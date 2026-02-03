import datetime
import queue
import time
import traceback

import pyvisa
import pyvisa.constants

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.calculations.physics import calculate_quantum_efficiency
from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import Ampere, Current, Quantity, Time, Value
from gan_controller.common.domain.quantity.factory import Voltage
from gan_controller.common.domain.quantity.unit_types import Volt
from gan_controller.common.hardware.adapters.laser_adapter import ILaserAdapter
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.adapters.power_supply_adapter import IPowerSupplyAdapter
from gan_controller.common.io.log_manager import LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.features.nea_activation.recorder import NEALogRecorder
from gan_controller.features.nea_activation.schemas import NEAConfig, NEAControlConfig
from gan_controller.features.nea_activation.sensor_reader import NEASensorReader

from .devices import NEADeviceManager, NEADevices, RealDeviceFactory, SimulationDeviceFactory
from .schemas.result import NEARunnerResult


class NEAActivationRunner(BaseRunner):
    app_config: AppConfig  # 全体設定
    nea_config: NEAConfig  # 実験条件

    _recorder: NEALogRecorder
    _request_queue: queue.Queue

    def __init__(self, app_config: AppConfig, nea_config: NEAConfig) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.nea_config = nea_config  # 実験条件

        self._request_queue = queue.Queue()  # スレッド通信用キュー

    def update_control_params(self, new_params: NEAControlConfig) -> None:
        """実験中にパラメータを更新する"""
        self._request_queue.put(new_params)

    # =================================================================

    def run(self) -> None:
        """実験開始"""
        tz = self.app_config.common.get_tz()
        try:
            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

            self._setup_recorder(start_time)

            # 設定に基づいて適切なFactoryを選択する
            is_simulation = getattr(self.app_config.common, "is_simulation_mode", False)
            device_factory = SimulationDeviceFactory() if is_simulation else RealDeviceFactory()

            with NEADeviceManager(self.app_config, factory=device_factory) as dev:
                self._setup_devices(dev)
                self._measurement_loop(dev)

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
        manager = LogManager(self.app_config.common.get_tz(), self.app_config.common.encode)

        log_dir = manager.get_date_directory(update_date=self.nea_config.log.update_date_folder)

        log_file = log_dir.create_logfile(
            protocol_name="NEA", major_update=self.nea_config.log.update_major_number
        )
        print(f"Recording to: {log_file.path}")

        self._recorder = NEALogRecorder(log_file)

        # ヘッダー書き込み (リファレンスと完全一致させるため start_time を渡す)
        self._recorder.record_header(
            start_time=start_time,
            init_nea_config=self.nea_config,
        )

    def _setup_devices(self, devices: NEADevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        self._init_laser_static(devices.laser)
        self._init_aps_static(devices.aps)
        self._init_gm10_static(devices.logger)

        # 動的設定の適応
        self._apply_params_to_device(devices, self.nea_config.control)

    def _init_laser_static(self, laser: ILaserAdapter) -> None:
        """レーザーの静的設定"""
        # チャンネルの有効化
        target_ch = self.app_config.devices.ibeam.beam_ch
        laser.set_channel_enable(target_ch, True)

    def _init_aps_static(self, aps: IPowerSupplyAdapter) -> None:
        """電源(AMD)の静的設定"""
        # 電圧リミットなどの安全設定
        aps_config = self.app_config.devices.aps
        aps.set_voltage(aps_config.v_limit)
        aps.set_ovp(aps_config.ovp)
        aps.set_ocp(aps_config.ocp)

        # 必要であればOCP(過電流保護)の設定などをここに追加

    def _init_gm10_static(self, gm10: ILoggerAdapter) -> None:
        """ロガー(GM10)の静的設定"""
        # 現状は読み込みのみなら特になくても良いが、
        # レンジ設定やフィルタ設定が必要ならここに記述する

    # =================================================================

    def _wait_interruptable(self, duration_sec: float) -> bool:
        """指定時間待機する。中断フラグが立ったら即座に終了する。

        Args:
            duration_sec (float): 待機する秒数

        Returns:
            bool: 待機が完了した場合はTrue、中断された場合はFalse

        """
        check_interval = 0.1  # チェック間隔 [s]
        start_perf = time.perf_counter()

        while True:
            # 経過時間をチェック
            elapsed = time.perf_counter() - start_perf
            remaining = duration_sec - elapsed

            if remaining <= 0:
                return True  # 待機完了

            # 中断フラグチェック
            if self._stop:
                return False  # 中断された

            # 次のチェックまでのスリープ (残り時間とインターバルの短い方)
            time.sleep(min(check_interval, remaining))

    def _measurement_loop(self, devices: NEADevices) -> None:
        """計測ループ"""
        print("Start NEA activation measurement...")

        sensor_reader = NEASensorReader(devices.logger, self.app_config)

        start_perf = time.perf_counter()  # 開始時間 (高分解能)

        try:
            # メインループ
            while not self._stop:
                try:
                    # 1ステップ分実行
                    if not self._execute_single_measurement(devices, sensor_reader, start_perf):
                        break
                except pyvisa.errors.VisaIOError as e:
                    self._handle_visa_error(e)

        except Exception as e:
            print(f"\033[31m[ERROR] Measurement loop failed: {e}\033[0m")
            print(traceback.format_exc())
            raise

        finally:
            self._finalize_safety(devices)

    def _execute_single_measurement(
        self, devices: NEADevices, sensor_reader: NEASensorReader, start_perf: float
    ) -> bool:
        """1回分の測定サイクルを実行

        Returns:
            bool: 測定が完了したらTrue, 中断されたらFalse

        """
        elapsed_perf = time.perf_counter() - start_perf
        self._process_pending_requests(devices)  # 設定に変更があるか確認

        stabilization_time = self.nea_config.condition.stabilization_time.base_value

        # 出力状態測定 (Bright)
        devices.laser.set_emission(True)  # レーザー出力開始
        # 安定するまで待機
        if not self._wait_interruptable(stabilization_time):
            return False  # 待機中に中断されたら終了

        bright_pc_volt, bright_pc = sensor_reader.read_photocurrent_integrated(
            self.nea_config.condition.shunt_resistance,
            int(self.nea_config.condition.integration_count.base_value),
            self.nea_config.condition.integration_interval.base_value,
        )

        # バックグラウンド測定 (Dark)
        devices.laser.set_emission(False)
        if not self._wait_interruptable(stabilization_time):
            return False

        dark_pc_volt, dark_pc = sensor_reader.read_photocurrent_integrated(
            self.nea_config.condition.shunt_resistance,
            int(self.nea_config.condition.integration_count.base_value),
            self.nea_config.condition.integration_interval.base_value,
        )

        # 4. データ集計と通知
        self._process_and_emit_result(
            devices,
            sensor_reader,
            elapsed_perf,
            bright_pc,
            bright_pc_volt,
            dark_pc,
            dark_pc_volt,
        )

        return True

    def _process_and_emit_result(
        self,
        devices: NEADevices,
        sensor_reader: NEASensorReader,
        timestamp: float,
        bright_pc: Quantity[Ampere],
        bright_pc_voltage: Quantity[Volt],
        dark_pc: Quantity[Ampere],
        dark_pc_voltage: Quantity[Volt],
    ) -> None:
        """測定値の計算、Result生成、通知を行う"""
        # --- 計算 ---
        wavelength_nm = self.nea_config.condition.laser_wavelength.value_as("n")
        laser_pv_watt = self.nea_config.control.laser_power_pv.base_value

        pc_val = bright_pc.base_value - dark_pc.base_value
        pc_v_val = bright_pc_voltage.base_value - dark_pc_voltage.base_value

        qe_val = calculate_quantum_efficiency(
            current_amp=pc_val, laser_power_watt=laser_pv_watt, wavelength_nm=wavelength_nm
        )

        pc = Current(pc_val)
        pc_voltage = Voltage(pc_v_val)
        qe = Value(qe_val, "%")

        # --- 読み取り ---
        ext_pressure = sensor_reader.read_ext()
        sip_pressure = sensor_reader.read_sip()
        extraction_voltage = sensor_reader.read_hv()

        # 電源の値取得
        amd_i = devices.aps.measure_current()
        amd_v = devices.aps.measure_voltage()
        amd_w = devices.aps.measure_power()

        electricity = ElectricMeasurement(voltage=amd_v, current=amd_i, power=amd_w)

        # --- Result生成 ---

        result = NEARunnerResult(
            timestamp=Time(timestamp),
            # LP
            laser_power_sv=self.nea_config.control.laser_power_sv,
            laser_power_pv=self.nea_config.control.laser_power_pv,
            # Pressure
            ext_pressure=ext_pressure,
            sip_pressure=sip_pressure,
            # HV
            extraction_voltage=extraction_voltage,
            # PC
            photocurrent=pc,
            photocurrent_voltage=pc_voltage,
            bright_pc=bright_pc,
            bright_pc_voltage=bright_pc_voltage,
            dark_pc=dark_pc,
            dark_pc_voltage=dark_pc_voltage,
            # QE
            quantum_efficiency=qe,
            # AMD power supply
            amd_electricity=electricity,
        )
        event = ""

        # --- 出力 ---
        print("\033[32m" + f"{timestamp:.1f}[s]\t" + "\033[0m")
        print(f"{qe:.3e}, {pc:.3e}, {ext_pressure:.2e} (EXT)")

        if self._recorder:
            self._recorder.record_data(result, event)

        if self.emit_result:
            self.emit_result(result)

    def _handle_visa_error(self, e: pyvisa.errors.VisaIOError) -> None:
        """VISAエラーのハンドリング"""
        if e.error_code == pyvisa.constants.VI_ERROR_TMO:
            print(f"\033[33m[WARNING] Device Timeout occurred. Retrying... ({e})\033[0m")
            # タイムアウト時は続行 (呼び出し元のループが継続する)
        else:
            # それ以外は再送出
            raise e

    def _finalize_safety(self, devices: NEADevices) -> None:
        """終了処理"""
        print("Executing safety cleanup...")

        try:
            devices.laser.set_emission(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop laser: {cleanup_err}")

        try:
            devices.aps.set_output(False)
        except Exception as cleanup_err:  # noqa: BLE001
            print(f"Failed to stop APS: {cleanup_err}")

    # =================================================================

    def _get_latest_config_from_queue(self) -> NEAControlConfig | None:
        """キューから最新の設定を取り出す"""
        if self._request_queue.empty():
            return None

        latest_params = None
        while not self._request_queue.empty():
            try:
                latest_params = self._request_queue.get_nowait()
            except queue.Empty:
                break

        return latest_params

    def _process_pending_requests(self, dev: NEADevices) -> None:
        """キューから最新の設定を取り出してデバイスに適用する"""
        latest_config = self._get_latest_config_from_queue()

        # 変更があった場合のみデバイス操作を実行
        if latest_config is not None:
            self._apply_params_to_device(dev, latest_config)
            self.nea_config.control = latest_config  # 現在値を更新

    def _apply_params_to_device(self, dev: NEADevices, params: NEAControlConfig) -> None:
        """実際にデバイスにコマンドを送る処理"""
        print(
            f"Applying new params: AMD={params.amd_output_current}, Laser={params.laser_power_sv}"
        )

        # レーザー制御
        dev.laser.set_channel_power(self.app_config.devices.ibeam.beam_ch, params.laser_power_sv)
        print(f"Set power: {dev.laser.get_channel_power(2).value_as('m')} mW")

        # AMD電源の制御
        if params.amd_enable:
            dev.aps.set_current(params.amd_output_current)  # A
            dev.aps.set_output(True)
        else:
            dev.aps.set_output(False)
