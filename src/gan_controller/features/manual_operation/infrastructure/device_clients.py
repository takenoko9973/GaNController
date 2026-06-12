from typing import Protocol

from gan_controller.core.console_logger import get_logger
from gan_controller.core.domain.app_config import AppConfig
from gan_controller.core.domain.quantity import Celsius, Quantity, Watt
from gan_controller.features.manual_operation.infrastructure.visa_provider import (
    get_shared_resource_manager,
)
from gan_controller.infrastructure.hardware.adapters.laser_adapter import (
    IBeamAdapter,
    MockLaserAdapter,
)
from gan_controller.infrastructure.hardware.adapters.pyrometer_adapter import (
    MockPyrometerAdapter,
    PWUXAdapter,
)
from gan_controller.infrastructure.hardware.drivers import PWUX, IBeam

logger = get_logger(__name__)


class _Closable(Protocol):
    def close(self) -> None: ...


def _safe_close(name: str, resource: _Closable | None) -> None:
    # close() の失敗で他の後処理が止まらないようにする
    if resource is None:
        return
    try:
        resource.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("Error closing %s: %s", name, e, extra={"color": "yellow"})


class PwuxClient:
    def __init__(self) -> None:
        self._adapter: PWUXAdapter | MockPyrometerAdapter | None = None

    @property
    def is_connected(self) -> bool:
        return self._adapter is not None

    def connect(self, app_config: AppConfig) -> None:
        if self._adapter is not None:
            return

        if app_config.common.is_simulation_mode:
            self._adapter = MockPyrometerAdapter()
            return

        if app_config.devices.pwux.com_port <= 0:
            msg = "PWUX com_port が無効です。"
            raise ValueError(msg)

        resource_manager = get_shared_resource_manager()
        driver = PWUX(resource_manager, f"COM{app_config.devices.pwux.com_port}")
        self._adapter = PWUXAdapter(driver)

    def disconnect(self) -> None:
        if self._adapter is None:
            return

        try:
            self._adapter.set_pointer(False)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to disable PWUX pointer: %s", e, extra={"color": "yellow"})

        self._close_adapter()

    def read_temperature(self) -> Quantity[Celsius]:
        adapter = self._require_adapter()
        return adapter.read_temperature()

    def set_pointer(self, enable: bool) -> None:
        adapter = self._require_adapter()
        adapter.set_pointer(enable)

    def _close_adapter(self) -> None:
        if self._adapter:
            _safe_close("PWUX adapter", self._adapter)
        self._adapter = None

    def _require_adapter(self) -> PWUXAdapter | MockPyrometerAdapter:
        if self._adapter is None:
            msg = "PWUX is not connected."
            raise RuntimeError(msg)
        return self._adapter


class LaserClient:
    def __init__(self) -> None:
        self._adapter: IBeamAdapter | MockLaserAdapter | None = None
        self._beam_ch: int | None = None

    @property
    def is_connected(self) -> bool:
        return self._adapter is not None

    def connect(self, app_config: AppConfig) -> None:
        if self._adapter is not None:
            return

        if app_config.common.is_simulation_mode:
            self._adapter = MockLaserAdapter()
        else:
            if app_config.devices.ibeam.com_port <= 0:
                msg = "iBeam com_port が無効です。"
                raise ValueError(msg)

            resource_manager = get_shared_resource_manager()
            driver = IBeam(resource_manager, f"COM{app_config.devices.ibeam.com_port}")
            self._adapter = IBeamAdapter(driver)

        self._beam_ch = app_config.devices.ibeam.beam_ch
        self._adapter.set_channel_enable(self._beam_ch, True)
        self._adapter.set_emission(False)

    def disconnect(self) -> None:
        if self._adapter is None:
            return

        try:
            self._adapter.set_emission(False)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to stop laser emission: %s", e, extra={"color": "yellow"})

        if self._beam_ch is not None:
            try:
                self._adapter.set_channel_enable(self._beam_ch, False)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to disable laser channel: %s",
                    e,
                    extra={"color": "yellow"},
                )

        self._close_adapter()
        self._beam_ch = None

    def set_power(self, power: Quantity[Watt]) -> None:
        adapter = self._require_adapter()
        beam_ch = self._require_beam_channel()
        adapter.set_channel_power(beam_ch, power)

    def set_emission(self, enable: bool) -> None:
        adapter = self._require_adapter()
        adapter.set_emission(enable)

    def get_current_power(self) -> Quantity[Watt]:
        adapter = self._require_adapter()
        beam_ch = self._require_beam_channel()
        return adapter.get_channel_power(beam_ch)

    def _close_adapter(self) -> None:
        if self._adapter:
            _safe_close("Laser adapter", self._adapter)
        self._adapter = None

    def _require_adapter(self) -> IBeamAdapter | MockLaserAdapter:
        if self._adapter is None:
            msg = "Laser is not connected."
            raise RuntimeError(msg)
        return self._adapter

    def _require_beam_channel(self) -> int:
        if self._beam_ch is None:
            msg = "Laser is not connected."
            raise RuntimeError(msg)
        return self._beam_ch
