from abc import ABC, abstractmethod

from gan_controller.core.models.quantity import Power, Quantity, Watt
from gan_controller.infrastructure.hardware.drivers import IBeam


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
        print(f"[Mock] Laser Emission: {on}")

    def set_channel_enable(self, channel: int, enable: bool) -> None:
        print(f"[Mock] Laser CH{channel} Enable: {enable}")

    def set_channel_power(self, channel: int, power: Quantity[Watt]) -> None:
        self._power = power
        print(f"[Mock] Laser CH{channel} Power: {self._power.value_as('m')}mW")

    def get_channel_power(self, channel: int) -> Quantity[Watt]:  # noqa: ARG002
        return self._power

    def close(self) -> None:
        print("[Mock] Laser Closed")
