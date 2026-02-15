from abc import ABC, abstractmethod
from contextlib import ExitStack
from types import TracebackType

import pyvisa

from gan_controller.common.hardware.adapters.laser_adapter import IBeamAdapter, MockLaserAdapter
from gan_controller.common.hardware.adapters.logger_adapter import GM10Adapter, MockLoggerAdapter
from gan_controller.common.hardware.adapters.power_supply_adapter import (
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.common.hardware.drivers.gm10 import GM10
from gan_controller.common.hardware.drivers.ibeam import IBeam
from gan_controller.common.hardware.drivers.pfr_100l50 import PFR100L50
from gan_controller.common.schemas.app_config import DevicesConfig
from gan_controller.features.nea_activation.domain.models import NEADevices

from .facade import NEAHardwareFacade


class NEAHardwareBackend(ABC):
    """ハードウェアの生成・接続・破棄を担う基底クラス"""

    def __init__(self, config: DevicesConfig) -> None:
        self._config = config
        self._devices: NEADevices | None = None
        self._rm: pyvisa.ResourceManager | None = None

    @abstractmethod
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager | None]:
        """具体的な接続処理 (サブクラスで実装)"""

    def __enter__(self) -> NEAHardwareFacade:
        """デバイスと接続してFacadeを返す"""
        self._devices, self._rm = self._connect_devices()
        return NEAHardwareFacade(self._devices, self._config)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """コンテキスト出口: 切断処理"""
        if self._devices:
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

        if self._rm:
            try:
                self._rm.close()
            except Exception as e:  # noqa: BLE001
                print(f"Error closing ResourceManager: {e}")


class RealNEAHardwareBackend(NEAHardwareBackend):
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager]:
        print("Connecting to Real Hardware...")
        rm = pyvisa.ResourceManager()

        with ExitStack() as stack:
            stack.callback(rm.close)

            try:
                gm10 = GM10(rm, self._config.gm10.visa)
                logger_adapter = GM10Adapter(gm10)
                stack.callback(logger_adapter.close)

                aps = PFR100L50(rm, self._config.aps.visa)
                aps_adapter = PFR100L50Adapter(aps)
                stack.callback(aps_adapter.close)

                laser_port = f"COM{self._config.ibeam.com_port}"
                laser = IBeam(rm, laser_port)
                laser_adapter = IBeamAdapter(laser)
                stack.callback(laser_adapter.close)

                stack.pop_all()
                return NEADevices(logger=logger_adapter, aps=aps_adapter, laser=laser_adapter), rm

            except Exception as e:
                print(f"[CRITICAL] Device creation failed: {e}")
                raise


class SimulationNEAHardwareBackend(NEAHardwareBackend):
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager | None]:
        print("Initializing Simulation Hardware...")
        devices = NEADevices(
            logger=MockLoggerAdapter(),
            aps=MockPowerSupplyAdapter(),
            laser=MockLaserAdapter(),
        )
        return devices, None
