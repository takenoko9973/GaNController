from abc import ABC, abstractmethod

from gan_controller.core.console_logger import get_logger
from gan_controller.core.domain.quantity import Power, Quantity, Watt
from gan_controller.infrastructure.hardware.drivers import IBeam

logger = get_logger(__name__)


# Interface
class ILaserAdapter(ABC):
    @abstractmethod
    def set_emission(self, on: bool) -> None:
        pass

    @abstractmethod
    def set_channel_enable(self, channel: int, enable: bool) -> None:
        pass

    @abstractmethod
    def set_channel_power(self, channel: int, power: Quantity[Watt]) -> None:
        pass

    @abstractmethod
    def get_channel_power(self, channel: int) -> Quantity[Watt]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class IBeamAdapter(ILaserAdapter):
    def __init__(self, driver: IBeam) -> None:
        self._driver = driver

    def set_emission(self, on: bool) -> None:
        self._driver.set_emission(on)

    def set_channel_enable(self, channel: int, enable: bool) -> None:
        self._driver.set_channel_enable(channel, enable)

    def set_channel_power(self, channel: int, power: Quantity[Watt]) -> None:
        self._driver.set_channel_power(channel, power.value_as("m"))

    def get_channel_power(self, channel: int) -> Quantity[Watt]:
        return Power(self._driver.get_channel_power(channel), "m")

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockLaserAdapter(ILaserAdapter):
    def __init__(self) -> None:
        self._emission = False
        self._power = Power(0.0)

    def set_emission(self, on: bool) -> None:
        self._emission = on
        logger.info("[Mock] Laser Emission: %s", on)

    def set_channel_enable(self, channel: int, enable: bool) -> None:
        logger.info("[Mock] Laser CH%s Enable: %s", channel, enable)

    def set_channel_power(self, channel: int, power: Quantity[Watt]) -> None:
        self._power = power
        logger.info("[Mock] Laser CH%s Power: %smW", channel, self._power.value_as("m"))

    def get_channel_power(self, channel: int) -> Quantity[Watt]:  # noqa: ARG002
        return self._power

    def close(self) -> None:
        logger.info("[Mock] Laser Closed")
