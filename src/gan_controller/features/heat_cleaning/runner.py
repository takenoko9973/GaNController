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
from gan_controller.common.schemas.app_config import AppConfig, PFR100l50Config
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

    _recorder: HCLogRecorder
    _request_queue: queue.Queue

    def __init__(
        self, app_config: AppConfig, protocol_config: ProtocolConfig, recorder: HCLogRecorder
    ) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.protocol_config = protocol_config  # 実験条件
        self._recorder = recorder

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
        print(f"Recording to: {self._recorder.file.path}")
        self._recorder.record_header(start_time=start_time)

    def _setup_devices(self, devices: HCDevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        self._init_pyrometer_static(devices.pyrometer)
        self._init_power_supply_static(
            devices.hps, self.app_config.devices.hps, self.protocol_config.condition.hc_enabled
        )
        self._init_power_supply_static(
            devices.aps, self.app_config.devices.aps, self.protocol_config.condition.amd_enabled
        )
        self._init_gm10_static(devices.logger)

    def _init_pyrometer_static(self, pyrometer: IPyrometerAdapter) -> None:
        """温度計(PWUX)の静的設定"""

    def _init_power_supply_static(
        self, power_supply: IPowerSupplyAdapter, config: PFR100l50Config, enable: bool
    ) -> None:
        """電源の静的設定"""
        power_supply.set_voltage(config.v_limit)
        power_supply.set_ovp(config.ovp)
        power_supply.set_ocp(config.ocp)
        power_supply.set_output(enable)

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
        interval = self.protocol_config.condition.logging_interval.base_value

        start_perf = time.perf_counter()  # 開始時間 (高分解能)
        next_target_perf = start_perf

        try:
            # メインループ
            while not self._stop:
                # タイミング調整
                current_perf = time.perf_counter()
                sleep_duration = next_target_perf - current_perf
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

                next_target_perf += interval  # 次の測定時間

                # =======================================================

                total_elapsed = time.perf_counter() - start_perf
                result = self._process_step(devices, sensor_reader, total_elapsed)

                if result is not None:
                    # 送信
                    if self.emit_result is not None:
                        self.emit_result(result)

                    # ログ書き込み
                    self._recorder.record_data(result)

        except Exception as e:
            print(f"\033[31m[ERROR] Measurement loop failed: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            self._finalize_safety(devices)

    def _process_step(
        self, devices: HCDevices, sensor_reader: HCSensorReader, total_elapsed: float
    ) -> HCRunnerResult | None:
        try:
            current_seq, seq_index, seq_elapsed = self._get_current_sequence_state(total_elapsed)
            if current_seq is not None:
                # 電流値設定
                self._control_devices(devices, current_seq, seq_elapsed)
            else:
                # 終了した場合
                print("All sequences finished.")
                self._stop = True

            time.sleep(0.1)  # 電流変化後の安定化用

            # 測定
            return self._measure_and_create_result(
                devices, sensor_reader, total_elapsed, seq_elapsed, current_seq, seq_index
            )

        except pyvisa.errors.VisaIOError as e:
            # 装置に関するエラー
            self._handle_visa_error(e)
            return None

    def _get_current_sequence_state(
        self, total_elapsed: float
    ) -> tuple[Sequence | None, int, float]:
        """現在の経過時間から、該当するシーケンスとその中での経過時間を返す

        Returns:
            (Sequenceオブジェクト, シーケンス番号, シーケンス内経過時間[s])

        """
        sequences = self.protocol_config.get_sequences()
        if not sequences:
            return None, -1, 0.0

        # シーケンスごとの累積時間
        accumulated_time = 0.0

        for i, seq in enumerate(sequences):
            duration = seq.duration_sec

            # まだこのシーケンスの範囲内か
            if total_elapsed < (accumulated_time + duration):
                seq_elapsed = total_elapsed - accumulated_time
                return seq, i, seq_elapsed

            accumulated_time += duration

        # 全シーケンス時間を超えている場合
        return None, -1, 0.0

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

    def _measure_and_create_result(
        self,
        devices: HCDevices,
        sensor_reader: HCSensorReader,
        total_elapsed: float,
        seq_elapsed: float,
        current_seq: Sequence | None,
        current_idx: int,
    ) -> HCRunnerResult:
        seq_name = current_seq.mode_name if current_seq else "Finish"

        # ケース温度
        case_temperature = devices.pyrometer.read_temperature()

        # 圧力
        ext_pressure = sensor_reader.read_ext()
        sip_pressure = sensor_reader.read_sip()

        # 電源の値取得
        hc_i = devices.hps.measure_current()
        hc_v = devices.hps.measure_voltage()
        hc_w = devices.hps.measure_power()
        hc_electricity = ElectricMeasurement(voltage=hc_v, current=hc_i, power=hc_w)

        amd_i = devices.aps.measure_current()
        amd_v = devices.aps.measure_voltage()
        amd_w = devices.aps.measure_power()
        amd_electricity = ElectricMeasurement(voltage=amd_v, current=amd_i, power=amd_w)

        return HCRunnerResult(
            current_sequence_index=current_idx + 1,
            current_sequence_name=seq_name,
            step_timestamp=Quantity(seq_elapsed, "s"),
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
