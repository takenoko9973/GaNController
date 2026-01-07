from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pyvisa

# ドライバのインポート
from gan_controller.common.hardware.adapters.laser_adapter import (
    IBeamAdapter,
    ILaserAdapter,
    MockLaserAdapter,
)
from gan_controller.common.hardware.adapters.logger_adapter import (
    GM10Adapter,
    ILoggerAdapter,
    MockLoggerAdapter,
)
from gan_controller.common.hardware.adapters.power_supply_adapter import (
    IPowerSupplyAdapter,
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.common.hardware.drivers.gm10 import GM10
from gan_controller.common.hardware.drivers.ibeam import IBeam
from gan_controller.common.hardware.drivers.pfr_100l50 import PFR100L50
from gan_controller.common.schemas.app_config import AppConfig


@dataclass
class NEADevices:
    """NEA実験で使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    aps: IPowerSupplyAdapter
    laser: ILaserAdapter


# =================================================================
#  Factory Definitions (Abstract Factory Pattern)
# =================================================================


class AbstractDeviceFactory(ABC):
    """デバイス生成の抽象ファクトリー"""

    @abstractmethod
    def create_devices(self, config: AppConfig) -> tuple[NEADevices, Any]:
        """デバイス群を生成して返す。

        Returns:
            tuple[NEADevices, Any]:
                - 作成されたデバイスコンテナ
                - 管理が必要なリソースオブジェクト(例: pyvisa.ResourceManager)。不要ならNone。

        """


class SimulationDeviceFactory(AbstractDeviceFactory):
    """シミュレーション用 (Mock) デバイスファクトリー"""

    def create_devices(self, config: AppConfig) -> tuple[NEADevices, Any]:  # noqa: ARG002
        print("--- SIMULATION MODE ---")
        # Mockアダプタを生成
        devices = NEADevices(
            logger=MockLoggerAdapter(),
            aps=MockPowerSupplyAdapter(),
            laser=MockLaserAdapter(),
        )
        return devices, None  # リソースマネージャは不要


class RealDeviceFactory(AbstractDeviceFactory):
    """実機用デバイスファクトリー"""

    def create_devices(self, config: AppConfig) -> tuple[NEADevices, Any]:
        # 実機接続用のResourceManagerを作成
        rm = pyvisa.ResourceManager()

        try:
            # Logger (GM10)
            try:
                gm10 = GM10(rm, config.devices.gm10_visa)
                logger_adapter = GM10Adapter(gm10)
            except Exception as e:
                print(f"GM10 Connection Error: {e}")
                raise

            # Power Supply (AMD/PFR100L50)
            try:
                aps = PFR100L50(rm, config.devices.aps_visa)
                aps_adapter = PFR100L50Adapter(aps)
            except Exception as e:
                print(f"APS Connection Error: {e}")
                raise

            # Laser (IBeam)
            try:
                laser_port = f"COM{config.devices.ibeam_com_port}"
                laser = IBeam(port=laser_port)
                laser_adapter = IBeamAdapter(laser)
            except Exception as e:
                print(f"Laser Connection Error: {e}")
                raise

            return NEADevices(logger=logger_adapter, aps=aps_adapter, laser=laser_adapter), rm

        except Exception:
            # 生成途中で失敗した場合、作成したrmを閉じる必要がある
            rm.close()
            raise


# =================================================================
#  Device Manager (Context Manager)
# =================================================================


class NEADeviceManager:
    """デバイスの接続と終了を管理するコンテキストマネージャ"""

    def __init__(self, config: AppConfig, factory: AbstractDeviceFactory) -> None:
        self.config = config
        self._factory = factory

        self._devices: NEADevices | None = None
        self._resource_manager: pyvisa.ResourceManager | None = None

    def __enter__(self) -> NEADevices:
        """実験開始時の処理: Factoryを使用してデバイスを生成"""
        self._devices, self._resource_manager = self._factory.create_devices(self.config)
        return self._devices

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """実験終了時の処理: 各デバイスの切断とリソース解放"""
        if self._devices:
            # 各デバイスのクローズ (エラーがあっても続行)
            if self._devices.laser:
                try:
                    self._devices.laser.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing laser: {e}")

            if self._devices.aps:
                try:
                    self._devices.aps.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing APS: {e}")

            if self._devices.logger:
                try:
                    self._devices.logger.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing logger: {e}")

        # VISA ResourceManagerのクローズ
        if self._resource_manager:
            try:
                self._resource_manager.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing ResourceManager: {e}")
