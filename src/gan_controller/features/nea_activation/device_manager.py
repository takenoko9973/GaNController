from dataclasses import dataclass

import pyvisa

# ドライバのインポート
from gan_controller.common.drivers.gm10 import GM10
from gan_controller.common.drivers.ibeam import IBeam
from gan_controller.common.drivers.pfr_100l50 import PFR100L50
from gan_controller.features.setting.model.app_config import AppConfig


@dataclass
class NEADevices:
    """NEA実験で使用するデバイス群を保持するコンテナ"""

    gm10: GM10
    aps: PFR100L50
    laser: IBeam


class NEADeviceManager:
    """デバイスの接続と終了を管理するコンテキストマネージャ"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._rm: pyvisa.ResourceManager | None = None
        self._devices: NEADevices | None = None

    def __enter__(self) -> NEADevices:
        """実験開始時の処理: 全デバイスへの接続"""
        self._rm = pyvisa.ResourceManager()

        # GM10 (Logger)
        gm10 = GM10(self._rm, self.config.devices.gm10_visa)

        # AMD Power Supply (PFR100L50)
        aps = PFR100L50(self._rm, self.config.devices.aps_visa)

        # Laser (IBeam)
        # COMポート番号からポート名を作成 (例: 3 -> COM3)
        laser_port = f"COM{self.config.devices.ibeam_com_port}"
        laser = IBeam(port=laser_port)

        self._devices = NEADevices(gm10=gm10, aps=aps, laser=laser)
        return self._devices

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """実験終了時の処理: 各デバイスの切断"""
        if self._devices:
            # 個別のcloseメソッドを呼び出す (エラーがあっても次へ進むように実装推奨)
            if self._devices.laser:
                self._devices.laser.close()
            if self._devices.aps:
                self._devices.aps.close()
            if self._devices.gm10:
                self._devices.gm10.close()

        if self._rm:
            self._rm.close()
