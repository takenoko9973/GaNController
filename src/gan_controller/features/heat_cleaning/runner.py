import datetime
import queue
import time
import traceback

import pyvisa
import pyvisa.constants

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import Current, Quantity
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.adapters.power_supply_adapter import IPowerSupplyAdapter
from gan_controller.common.hardware.adapters.pyrometer_adapter import IPyrometerAdapter
from gan_controller.common.io.log_manager import LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.features.heat_cleaning.devices import (
    HCDeviceManager,
    HCDevices,
    RealHCDeviceFactory,
    SimulationHCDeviceFactory,
)
from gan_controller.features.heat_cleaning.domain import Sequence
from gan_controller.features.heat_cleaning.recorder import HCLogRecorder
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult
from gan_controller.features.heat_cleaning.sensor_reader import HCSensorReader


class HCActivationRunner(BaseRunner):
    app_config: AppConfig  # 全体設定
    protocol_config: ProtocolConfig  # 実験条件

    # _recorder: HCLogRecorder
    _request_queue: queue.Queue

    def __init__(self, app_config: AppConfig, protocol_config: ProtocolConfig) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.protocol_config = protocol_config  # 実験条件

        self._request_queue = queue.Queue()  # スレッド通信用キュー

    # =================================================================

    def run(self) -> None:
        """実験開始"""
        tz = self.app_config.common.get_tz()
        try:
            # 設定に基づいて適切なFactoryを選択する
            is_simulation = getattr(self.app_config.common, "is_simulation_mode", False)
            device_factory = SimulationHCDeviceFactory() if is_simulation else RealHCDeviceFactory()

            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")
            self._setup_recorder(start_time)

            with HCDeviceManager(self.app_config, factory=device_factory) as dev:
                self._setup_devices(dev)

                sensor_reader = HCSensorReader(dev.logger, self.app_config)
                self._measurement_loop(dev, sensor_reader)

        except Exception as e:
            # エラー発生時はログ出力などを行う
            print(f"Experiment Error: {e}")
            raise  # Workerスレッド側でキャッチさせるために再送出

        finally:
            finish_time = datetime.datetime.now(tz)
            print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")

    # =================================================================

    def _setup_recorder(self, start_time: datetime.datetime) -> None:
        """記録用ファイルの準備とヘッダー書き込み"""
        manager = LogManager(self.app_config)

        # ログファイル準備
        update_date = self.protocol_config.log.update_date_folder
        major_update = self.protocol_config.log.update_major_number

        log_dir = manager.get_date_directory(update_date)
        log_file = log_dir.create_logfile(protocol_name="NEA", major_update=major_update)
        print(f"Recording to: {log_file.path}")

        # レコーダー準備
        self._recorder = HCLogRecorder(log_file, self.protocol_config)
        self._recorder.record_header(start_time=start_time)

    def _setup_devices(self, devices: HCDevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        self._init_pyrometer_static(devices.pyrometer)
        self._init_power_supply_static(devices.hps, devices.aps)
        self._init_gm10_static(devices.logger)

    def _init_pyrometer_static(self, pyrometer: IPyrometerAdapter) -> None:
        """温度計(PWUX)の静的設定"""

    def _init_power_supply_static(self, hps: IPowerSupplyAdapter, aps: IPowerSupplyAdapter) -> None:
        """電源の静的設定"""
        hps_config = self.app_config.devices.hps
        hps.set_voltage(hps_config.v_limit)
        hps.set_ovp(hps_config.ovp)
        hps.set_ocp(hps_config.ocp)

        aps_config = self.app_config.devices.aps
        aps.set_voltage(aps_config.v_limit)
        aps.set_ovp(aps_config.ovp)
        aps.set_ocp(aps_config.ocp)

    def _init_gm10_static(self, gm10: ILoggerAdapter) -> None:
        """ロガー(GM10)の静的設定"""
        # 現状は読み込みのみなら特になくても良いが、
        # レンジ設定やフィルタ設定が必要ならここに記述する

    # =================================================================
    # Measurement Logic
    # =================================================================

    def _measurement_loop(self, devices: HCDevices, sensor_reader: HCSensorReader) -> None:
        """計測ループ"""
        sequences = self.protocol_config.get_sequences()
        if not sequences:
            print("No sequences found.")
            return

        print("Start Heat Cleaning measurement...")

        # 制御・ログ書き込み間隔
        monitor_interval = 1.0  # 測定間隔
        logging_interval = self.protocol_config.condition.logging_interval.base_value

        start_perf = time.perf_counter()  # 開始時間 (高分解能)
        next_log_time = 0.0

        try:
            # メインループ
            while not self._stop:
                try:
                    current_perf = time.perf_counter()
                    total_elapsed = current_perf - start_perf

                    is_logging_timing = total_elapsed >= next_log_time
                    if is_logging_timing:
                        next_log_time += logging_interval  # 次の更新時間を更新

                    # ===========================================================

                    current_seq, seq_elapsed = self._get_current_sequence_state(
                        sequences, total_elapsed
                    )
                    if current_seq is None:
                        print("All sequences finished.")
                        break

                    # 制御 (電流値適応)
                    if is_logging_timing:  # ログと同じ間隔
                        self._control_devices(devices, current_seq, seq_elapsed)

                    # 測定
                    result = self._measure(devices, sensor_reader, total_elapsed, seq_elapsed)

                    if self.emit_result is not None:
                        self.emit_result(result)

                    # ログ
                    if is_logging_timing and result is not None:
                        self._recorder.record_data(result)

                except pyvisa.errors.VisaIOError as e:
                    self._handle_visa_error(e)

                # 測定間隔調整
                elapsed_in_loop = time.perf_counter() - current_perf
                sleep_time = max(0.0, monitor_interval - elapsed_in_loop)
                time.sleep(sleep_time)

        except Exception as e:
            print(f"\033[31m[ERROR] Measurement loop failed: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            self._finalize_safety(devices)

    def _get_current_sequence_state(
        self, sequences: list[Sequence], total_elapsed: float
    ) -> tuple[Sequence | None, float]:
        """現在の経過時間から、該当するシーケンスとその中での経過時間を返す

        Returns:
            (Sequenceオブジェクト, シーケンス内経過時間[s])

        """
        # シーケンスごとの累積時間
        accumulated_time = 0.0

        for seq in sequences:
            duration = seq.duration_sec

            # まだこのシーケンスの範囲内か
            if total_elapsed < (accumulated_time + duration):
                seq_elapsed = total_elapsed - accumulated_time
                return seq, seq_elapsed

            accumulated_time += duration

        # 全シーケンス時間を超えている場合
        return None, 0.0

    def _control_devices(self, devices: HCDevices, seq: Sequence, seq_elapsed: float) -> None:
        """シーケンス定義に従ってデバイス(電源)を制御"""
        # HC電源の制御
        if self.protocol_config.condition.hc_enabled:
            # 現在の目標電流値を計算
            hc_max_current = self.protocol_config.condition.hc_current
            target_current = seq.current(hc_max_current.base_value, seq_elapsed)

            devices.hps.set_current(Current(target_current))

        # AMD電源の制御
        if self.protocol_config.condition.hc_enabled:
            amd_max_current = self.protocol_config.condition.amd_current
            target_current = seq.current(amd_max_current.base_value, seq_elapsed)

            devices.aps.set_current(Current(target_current))

    def _measure(
        self,
        devices: HCDevices,
        sensor_reader: HCSensorReader,
        total_elapsed: float,
        seq_elapsed: float,
    ) -> HCRunnerResult:
        # ケース温度
        case_temperature = devices.pyrometer.read_temperature()

        # 圧力
        ext_pressure = sensor_reader.read_ext()
        sip_pressure = sensor_reader.read_sip()

        # 電源の値取得
        hc_i = devices.aps.measure_current()
        hc_v = devices.aps.measure_voltage()
        hc_w = devices.aps.measure_power()
        hc_electricity = ElectricMeasurement(voltage=hc_v, current=hc_i, power=hc_w)

        amd_i = devices.aps.measure_current()
        amd_v = devices.aps.measure_voltage()
        amd_w = devices.aps.measure_power()
        amd_electricity = ElectricMeasurement(voltage=amd_v, current=amd_i, power=amd_w)

        return HCRunnerResult(
            sequence_timestamp=Quantity(seq_elapsed, "s"),
            total_timestamp=Quantity(total_elapsed, "s"),
            ext_pressure=ext_pressure,
            sip_pressure=sip_pressure,
            case_temperature=case_temperature,
            hc_electricity=hc_electricity,
            amd_electricity=amd_electricity,
        )

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e

    def _finalize_safety(self, devices: HCDevices) -> None:
        """終了処理"""
        print("Executing safety cleanup...")

        try:
            devices.hps.set_output(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop HPS: {cleanup_err}")

        try:
            devices.aps.set_output(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop APS: {cleanup_err}")
