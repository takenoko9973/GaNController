from contextlib import ExitStack

import pyvisa

from gan_controller.core.domain.app_config import DevicesConfig
from gan_controller.core.domain.hardware import IHardwareBackend
from gan_controller.features.nea_activation.domain.interface import INEAHardwareFacade
from gan_controller.features.nea_activation.domain.models import NEADevices
from gan_controller.infrastructure.hardware.adapters.laser_adapter import (
    IBeamAdapter,
    MockLaserAdapter,
)
from gan_controller.infrastructure.hardware.adapters.logger_adapter import (
    GM10Adapter,
    MockLoggerAdapter,
)
from gan_controller.infrastructure.hardware.adapters.power_supply_adapter import (
    MockPowerSupplyAdapter,
    PFR100L50Adapter,
)
from gan_controller.infrastructure.hardware.drivers import GM10, PFR100L50, IBeam

from .facade import NEAHardwareFacade


class NEAHardwareBackend(IHardwareBackend[NEADevices, INEAHardwareFacade]):
    """ハードウェアの生成・接続・破棄を担う基底クラス"""

    def __init__(self, config: DevicesConfig) -> None:
        self._config = config

    def _disconnect_devices(self) -> None:
        """具体的な切断処理"""
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

    def get_facade(self) -> INEAHardwareFacade:
        """Facadeを構築して返す"""
        if not self._devices:
            msg = "Backend is not initialized. Use 'with' statement."
            raise RuntimeError(msg)

        return NEAHardwareFacade(devices=self._devices, config=self._config)


class RealNEAHardwareBackend(NEAHardwareBackend):
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager]:
        """具体的な接続処理"""
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

                devices = NEADevices(logger=logger_adapter, aps=aps_adapter, laser=laser_adapter)
                return devices, rm

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
