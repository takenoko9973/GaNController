from dataclasses import dataclass

import pyvisa

# ドライバのインポート
from gan_controller.common.adapters.laser_adapter import (
    IBeamAdapter,
    ILaserAdapter,
    MockLaserAdapter,
)
from gan_controller.common.adapters.logger_adapter import (
    GM10Adapter,
    ILoggerAdapter,
    MockLoggerAdapter,
)
from gan_controller.common.adapters.power_supply_adapter import (
    IPowerSupplyAdapter,
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.common.drivers.gm10 import GM10
from gan_controller.common.drivers.ibeam import IBeam
from gan_controller.common.drivers.pfr_100l50 import PFR100L50
from gan_controller.features.setting.model.app_config import AppConfig


@dataclass
class NEADevices:
    """NEA実験で使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    aps: IPowerSupplyAdapter
    laser: ILaserAdapter


class NEADeviceManager:
    """デバイスの接続と終了を管理するコンテキストマネージャ"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._rm: pyvisa.ResourceManager | None = None
        self._devices: NEADevices | None = None

    def __enter__(self) -> NEADevices:
        """実験開始時の処理: 全デバイスへの接続"""
        # シミュレーションか判定
        is_simulation = getattr(self.config.common, "is_simulation_mode", True)

        if is_simulation:
            print("--- SIMULATION MODE ---")
            # ダミーアダプタを使用
            self._rm = None  # MockならVISA不要
            logger_adapter = MockLoggerAdapter()
            aps_adapter = MockPowerSupplyAdapter()
            laser_adapter = MockLaserAdapter()
        else:
            # 実機接続
            self._rm = pyvisa.ResourceManager()
            # Logger (GM10)
            try:
                gm10 = GM10(self._rm, self.config.devices.gm10_visa)
                logger_adapter = GM10Adapter(gm10)
            except Exception as e:
                print(f"GM10 Connection Error: {e}")
                raise

            # Power Supply (AMD/PFR100L50)
            try:
                aps = PFR100L50(self._rm, self.config.devices.aps_visa)
                aps_adapter = PFR100L50Adapter(aps)
            except Exception as e:
                print(f"APS Connection Error: {e}")
                # 必要に応じてclose処理を入れる
                raise

            # Laser (IBeam)
            try:
                # COM ポート番号から作成 (3 -> COM3)
                laser_port = f"COM{self.config.devices.ibeam_com_port}"
                laser = IBeam(port=laser_port)
                laser_adapter = IBeamAdapter(laser)
            except Exception as e:
                print(f"Laser Connection Error: {e}")
                raise

        self._devices = NEADevices(logger=logger_adapter, aps=aps_adapter, laser=laser_adapter)
        return self._devices

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """実験終了時の処理: 各デバイスの切断"""
        if self._devices:
            # 個別のcloseメソッドを呼び出す (エラーがあっても次へ進むように実装推奨)
            if self._devices.laser:
                self._devices.laser.close()
            if self._devices.aps:
                self._devices.aps.close()
            if self._devices.logger:
                self._devices.logger.close()

        if self._rm:
            self._rm.close()
