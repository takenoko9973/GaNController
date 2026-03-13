from contextlib import ExitStack

import pyvisa

from gan_controller.core.domain.app_config import DevicesConfig
from gan_controller.core.domain.hardware import IHardwareBackend
from gan_controller.features.manual_operation.domain.interface import IManualHardwareFacade
from gan_controller.features.manual_operation.domain.models import ManualDevices
from gan_controller.infrastructure.hardware.adapters.laser_adapter import (
    IBeamAdapter,
    MockLaserAdapter,
)
from gan_controller.infrastructure.hardware.adapters.logger_adapter import (
    GM10Adapter,
    MockLoggerAdapter,
)
from gan_controller.infrastructure.hardware.adapters.pyrometer_adapter import (
    MockPyrometerAdapter,
    PWUXAdapter,
)
from gan_controller.infrastructure.hardware.drivers import GM10, PWUX, IBeam

from .facade import ManualHardwareFacade


class ManualHardwareBackend(IHardwareBackend[ManualDevices, IManualHardwareFacade]):
    """手動操作用: ハードウェアの生成・接続・破棄を担う基底クラス"""

    def __init__(self, config: DevicesConfig) -> None:
        self._config = config

    def _disconnect_devices(self) -> None:
        if self._devices:
            if self._devices.laser:
                try:
                    self._devices.laser.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing laser: {e}")

            if self._devices.pyrometer:
                try:
                    self._devices.pyrometer.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing pyrometer: {e}")

            if self._devices.logger:
                try:
                    self._devices.logger.close()
                except Exception as e:  # noqa: BLE001
                    print(f"Error closing logger: {e}")

    def get_facade(self) -> IManualHardwareFacade:
        if not self._devices:
            msg = "Backend is not initialized. Use 'with' statement."
            raise RuntimeError(msg)

        return ManualHardwareFacade(devices=self._devices, config=self._config)


class RealManualHardwareBackend(ManualHardwareBackend):
    """実機用バックエンド"""

    def _connect_devices(self) -> tuple[ManualDevices, pyvisa.ResourceManager]:
        rm = pyvisa.ResourceManager()

        with ExitStack() as stack:
            stack.callback(rm.close)

            if self._config.pwux.com_port <= 0:
                msg = "PWUX com_port is disabled (<=0)."
                raise ValueError(msg)

            if self._config.ibeam.com_port <= 0:
                msg = "iBeam com_port is disabled (<=0)."
                raise ValueError(msg)

            try:
                gm10 = GM10(rm, self._config.gm10.visa)
                logger_adapter = GM10Adapter(gm10)
                stack.callback(logger_adapter.close)

                pyrometer = PWUX(rm, f"COM{self._config.pwux.com_port}")
                pyrometer_adapter = PWUXAdapter(pyrometer)
                stack.callback(pyrometer_adapter.close)

                laser = IBeam(rm, f"COM{self._config.ibeam.com_port}")
                laser_adapter = IBeamAdapter(laser)
                stack.callback(laser_adapter.close)

                stack.pop_all()
                devices = ManualDevices(
                    logger=logger_adapter, pyrometer=pyrometer_adapter, laser=laser_adapter
                )
                return devices, rm

            except Exception as e:
                print(f"[CRITICAL] Device creation failed: {e}")
                raise


class SimulationManualHardwareBackend(ManualHardwareBackend):
    """シミュレーション用バックエンド"""

    def _connect_devices(self) -> tuple[ManualDevices, pyvisa.ResourceManager | None]:
        devices = ManualDevices(
            logger=MockLoggerAdapter(),
            pyrometer=MockPyrometerAdapter(),
            laser=MockLaserAdapter(),
        )
        return devices, None
