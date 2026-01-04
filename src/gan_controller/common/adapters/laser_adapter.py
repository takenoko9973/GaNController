from abc import ABC, abstractmethod

from gan_controller.common.drivers.ibeam import IBeam


# Interface
class ILaserAdapter(ABC):
    @abstractmethod
    def set_emission(self, on: bool) -> None:
        pass

    @abstractmethod
    def set_channel_enable(self, channel: int, enable: bool) -> None:
        pass

    @abstractmethod
    def set_channel_power(self, channel: int, power_mw: float) -> None:
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

    def set_channel_power(self, channel: int, power_mw: float) -> None:
        self._driver.set_channel_power(channel, power_mw)

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockLaserAdapter(ILaserAdapter):
    def __init__(self) -> None:
        self._emission = False

    def set_emission(self, on: bool) -> None:
        self._emission = on
        print(f"[Mock] Laser Emission: {on}")

    def set_channel_enable(self, channel: int, enable: bool) -> None:
        print(f"[Mock] Laser CH{channel} Enable: {enable}")

    def set_channel_power(self, channel: int, power_mw: float) -> None:
        print(f"[Mock] Laser CH{channel} Power: {power_mw}mW")

    def close(self) -> None:
        print("[Mock] Laser Closed")
