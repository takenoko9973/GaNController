from collections.abc import Callable
from contextlib import ExitStack

import pyvisa

from gan_controller.core.console_logger import get_logger
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

logger = get_logger(__name__)


class NEAHardwareBackend(IHardwareBackend[NEADevices, INEAHardwareFacade]):
    """ハードウェアの生成・接続・破棄を担う基底クラス"""

    def __init__(self, config: DevicesConfig, *, connect_laser: bool = True) -> None:
        self._config = config
        self._connect_laser = connect_laser

    def _close_device_with_log(self, label: str, close_action: Callable[[], None]) -> None:
        try:
            close_action()
            logger.info("[DISCONNECT][%s] success", label)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "[DISCONNECT][%s] failed: %s",
                label,
                e,
                extra={"color": "yellow"},
            )

    def _disconnect_devices(self) -> None:
        """具体的な切断処理"""
        if self._devices:
            if self._devices.laser:
                self._close_device_with_log("laser", self._devices.laser.close)
            if self._devices.aps:
                self._close_device_with_log("APS", self._devices.aps.close)
            if self._devices.logger:
                self._close_device_with_log("logger", self._devices.logger.close)

    def get_facade(self) -> INEAHardwareFacade:
        """Facadeを構築して返す"""
        if not self._devices:
            msg = "Backend is not initialized. Use 'with' statement."
            raise RuntimeError(msg)

        return NEAHardwareFacade(
            devices=self._devices,
            config=self._config,
            connect_laser=self._connect_laser,
        )


class RealNEAHardwareBackend(NEAHardwareBackend):
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager]:
        """具体的な接続処理"""
        logger.info("Connecting to Real Hardware...")
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

                if self._connect_laser:
                    laser_port = f"COM{self._config.ibeam.com_port}"
                    laser = IBeam(rm, laser_port)
                    laser_adapter = IBeamAdapter(laser)
                    stack.callback(laser_adapter.close)
                else:
                    logger.info("Laser connection skipped (fixed background mode).")
                    laser_adapter = MockLaserAdapter()

                stack.pop_all()

                devices = NEADevices(logger=logger_adapter, aps=aps_adapter, laser=laser_adapter)
                return devices, rm

            except Exception as e:
                logger.critical(
                    "[CRITICAL] Device creation failed: %s",
                    e,
                    extra={"color": "red"},
                )
                raise


class SimulationNEAHardwareBackend(NEAHardwareBackend):
    def _connect_devices(self) -> tuple[NEADevices, pyvisa.ResourceManager | None]:
        logger.info("Initializing Simulation Hardware...")
        devices = NEADevices(
            logger=MockLoggerAdapter(),
            aps=MockPowerSupplyAdapter(),
            laser=MockLaserAdapter(),
        )
        return devices, None
