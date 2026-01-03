import time

from gan_controller.common.dtos.electricity import ElectricValuesDTO
from gan_controller.common.interfaces.runner import BaseRunner
from gan_controller.common.types.quantity import Quantity
from gan_controller.features.nea_activation.device_manager import NEADeviceManager, NEADevices
from gan_controller.features.nea_activation.dtos.nea_params import (
    NEAActivationResult,
    NEAConditionParams,
    NEAControlParams,
    NEALogParams,
)
from gan_controller.features.setting.model.app_config import AppConfig


class NEAActivationRunner(BaseRunner):
    config: AppConfig  # 全体設定
    condition_params: NEAConditionParams  # 実験条件
    log_params: NEALogParams  # ログ設定
    control_params: NEAControlParams  # 動的制御設定

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

    def update_params(self, new_params: NEAControlParams) -> None:
        """実験中にパラメータを更新する"""
        self.control_params = new_params

    def run(self) -> None:
        try:
            with NEADeviceManager(self.config) as dev:
                self._setup_devices(dev)
                self._measurement_loop(dev)

        except Exception as e:
            # エラー発生時はログ出力などを行う
            print(f"Experiment Error: {e}")
            raise  # Workerスレッド側でキャッチさせるために再送出

    def _setup_devices(self, devices: NEADevices) -> None:
        """実験前の初期設定"""
        print("Setting up devices...")

        # レーザー設定
        devices.laser.set_channel_enable(self.config.devices.ibeam.beam_ch, True)
        devices.laser.set_channel_power(
            self.config.devices.ibeam.beam_ch, self.control_params.laser_power_sv
        )

        # 電源設定 (AMD)
        devices.aps.set_voltage(self.config.devices.amd.v_limit)
        devices.aps.set_output(True)

        # 安定待ち
        time.sleep(1.0)

    def _measurement_loop(self, devices: NEADevices) -> None:
        """計測ループ"""
        start_time = time.time()

        while not self._stop:
            print(self.control_params)
            time.sleep(1.0)
            continue

            current_time = time.time()
            elapsed = current_time - start_time

            # === 計測処理 ===
            # GM10から全データ取得
            # 設定ファイルのチャンネル定義を使用
            gm10_cfg = self.config.devices.gm10

            # まとめて取得する場合は read_channels を使うのが効率的
            # ここでは例として単一取得メソッドを使用
            pc_val = devices.gm10.read_channel(gm10_cfg.pc_ch)
            ext_val = devices.gm10.read_channel(gm10_cfg.ext_ch)
            hv_val = devices.gm10.read_channel(gm10_cfg.hv_ch)  # 実際のHV電圧など

            # 電源の値取得
            amd_i = devices.aps.measure_current()
            amd_v = devices.aps.measure_voltage()
            amd_w = devices.aps.measure_power()

            # === 結果オブジェクト作成 ===
            # NOTE: DTOの構造に合わせて値を詰める
            result = NEAActivationResult(
                ext_pressure=Quantity(value=ext_val, unit="Pa"),
                hv=Quantity(value=hv_val, unit="V"),
                photocurrent=Quantity(value=pc_val, unit="A"),
                electricity=ElectricValuesDTO(
                    voltage=amd_v,
                    current=amd_i,
                    power=amd_w,
                    resistance=0.0,  # 必要なら計算
                ),
                timestamp=elapsed,
            )

            # 結果をUIへ通知
            if self.emit_result:
                self.emit_result(result)

            # 周期調整 (1秒待機など)
            time.sleep(1.0)

        # ループを抜けたら終了処理 (デバイスOFFなど)
        # NOTE: withブロックを抜ける際にcloseは呼ばれるが、
        # 安全のために出力をOFFにする処理はここに書くと良い
        devices.laser.set_emission(False)
        devices.amd.set_output(False)
