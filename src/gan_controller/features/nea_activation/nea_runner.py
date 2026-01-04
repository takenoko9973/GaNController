import datetime
import queue
import time

from gan_controller.common.drivers.gm10 import GM10
from gan_controller.common.drivers.ibeam import IBeam
from gan_controller.common.drivers.pfr_100l50 import PFR100L50
from gan_controller.common.dtos.electricity import ElectricValuesDTO
from gan_controller.common.interfaces.runner import BaseRunner
from gan_controller.common.types.quantity import Quantity
from gan_controller.features.nea_activation.services.sensor_reader import NEASensorReader
from gan_controller.features.setting.model.app_config import AppConfig

from .device_manager import NEADeviceManager, NEADevices
from .dtos.nea_params import NEAConditionParams, NEAControlParams, NEALogParams
from .dtos.nea_result import NEAActivationResult


class NEAActivationRunner(BaseRunner):
    app_config: AppConfig  # 全体設定
    condition_params: NEAConditionParams  # 実験条件
    log_params: NEALogParams  # ログ設定
    control_params: NEAControlParams  # 動的制御設定

    _request_queue: queue.Queue

    def __init__(
        self,
        app_config: AppConfig,
        condition_params: NEAConditionParams,
        log_params: NEALogParams,
        init_control_params: NEAControlParams,
    ) -> None:
        super().__init__()
        self.app_config = app_config  # VISAアドレスなど
        self.condition_params = condition_params  # 実験条件
        self.log_params = log_params  # ログ設定
        self.control_params = init_control_params  # 動的制御設定

        self._request_queue = queue.Queue()  # スレッド通信用キュー

    def update_control_params(self, new_params: NEAControlParams) -> None:
        """実験中にパラメータを更新する"""
        self._request_queue.put(new_params)

    # =================================================================

    def run(self) -> None:
        """実験開始"""
        tz = self.app_config.common.get_tz()
        try:
            start_time = datetime.datetime.now(tz)
            print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

            with NEADeviceManager(self.app_config) as dev:
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

    def _setup_devices(self, devices: NEADevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        self._init_laser_static(devices.laser)
        self._init_aps_static(devices.aps)
        self._init_gm10_static(devices.logger)

        # 動的設定の適応
        self._apply_params_to_device(devices, self.control_params)

    def _init_laser_static(self, laser: IBeam) -> None:
        """レーザーの静的設定"""
        # チャンネルの有効化
        target_ch = self.app_config.devices.ibeam.beam_ch
        laser.set_channel_enable(target_ch, True)

    def _init_aps_static(self, aps: PFR100L50) -> None:
        """電源(AMD)の静的設定"""
        # 電圧リミットなどの安全設定
        v_limit = self.app_config.devices.amd.v_limit
        aps.set_voltage(v_limit)

        # 必要であればOCP(過電流保護)の設定などをここに追加

    def _init_gm10_static(self, gm10: GM10) -> None:
        """ロガー(GM10)の静的設定"""
        # 現状は読み込みのみなら特になくても良いが、
        # レンジ設定やフィルタ設定が必要ならここに記述する

    # =================================================================

    def _measurement_loop(self, devices: NEADevices) -> None:
        """計測ループ"""
        print("Start NEA activation measurement...")

        sensor_reader = NEASensorReader(devices.logger, self.app_config)

        start_perf = time.perf_counter()  # 開始時間 (高分解能)

        while not self._stop:
            elapsed_perf = time.perf_counter() - start_perf

            self._process_pending_requests(devices)  # デバイス設定更新

            # ===

            # 出力状態測定
            devices.laser.set_emission(True)  # レーザー出力開始
            time.sleep(self.condition_params.stabilization_time.value_as())  # 安定するまで待機

            bright_pc = sensor_reader.read_photocurrent_integrated(
                self.condition_params.shunt_resistance,
                int(self.condition_params.integration_count.value_as("")),
                self.condition_params.integration_interval.value_as(""),
            )

            # バックグラウンド測定
            devices.laser.set_emission(False)  # レーザー出力停止
            time.sleep(self.condition_params.stabilization_time.value_as())  # 安定するまで待機

            dark_pc = sensor_reader.read_photocurrent_integrated(
                self.condition_params.shunt_resistance,
                int(self.condition_params.integration_count.value_as("")),
                self.condition_params.integration_interval.value_as(""),
            )

            # ===

            wavelength = self.condition_params.laser_wavelength.value_as("n")
            laser_pv = self.control_params.laser_power_output.value_as("")

            pc = Quantity(bright_pc.value_as("") - dark_pc.value_as(""), "A")
            qe = Quantity(1240 * pc.value_as("") / (wavelength * laser_pv) * 100, "%")

            # 残りデータの測定
            ext_pressure = sensor_reader.read_ext()

            # 電源の値取得
            amd_i = devices.aps.measure_current()
            amd_v = devices.aps.measure_voltage()
            amd_w = devices.aps.measure_power()

            # === 結果オブジェクト作成 ===
            electricity = ElectricValuesDTO(voltage=amd_v, current=amd_i, power=amd_w)
            result = NEAActivationResult(
                ext_pressure=ext_pressure,
                photocurrent=pc,
                quantum_efficiency=qe,
                electricity=electricity,
                timestamp=elapsed_perf,
            )

            print("\033[32m" + f"{elapsed_perf:.1f}[s]\t" + "\033[0m")
            print(f"{qe:.3e}, {ext_pressure:.2e} (EXT)")

            # 結果をUIへ通知
            if self.emit_result:
                self.emit_result(result)

        # 終了処理
        devices.laser.set_emission(False)
        devices.aps.set_output(False)

    # =================================================================

    def _get_latest_params_from_queue(self) -> NEAControlParams | None:
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
        latest_params = self._get_latest_params_from_queue()

        # 変更があった場合のみデバイス操作を実行
        if latest_params is not None:
            self._apply_params_to_device(dev, latest_params)
            self.control_params = latest_params  # 現在値を更新

    def _apply_params_to_device(self, dev: NEADevices, params: NEAControlParams) -> None:
        """実際にデバイスにコマンドを送る処理"""
        print(
            f"Applying new params: AMD={params.amd_output_current}, Laser={params.laser_power_sv}"
        )

        # レーザー制御
        dev.laser.set_channel_power(
            self.app_config.devices.ibeam.beam_ch,
            params.laser_power_sv.value_as("m"),  # mW
        )

        # AMD電源の制御
        if params.amd_enable:
            dev.aps.set_current(params.amd_output_current.value_as(""))  # A
            dev.aps.set_output(True)
        else:
            dev.aps.set_output(False)
