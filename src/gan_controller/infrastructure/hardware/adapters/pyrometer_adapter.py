import random
from abc import ABC, abstractmethod

from gan_controller.core.models.quantity import Celsius, Quantity, Temperature
from gan_controller.infrastructure.hardware.drivers import PWUX


# Interface
class IPyrometerAdapter(ABC):
    @abstractmethod
    def read_temperature(self) -> Quantity[Celsius]:
        """温度計測"""

    @abstractmethod
    def set_pointer(self, enable: bool) -> None:
        """指定チャンネルを積算平均して読み取る"""

    # 必要であればクローズ処理など
    @abstractmethod
    def close(self) -> None:
        pass


class PWUXAdapter(IPyrometerAdapter):
    _driver: PWUX

    def __init__(self, driver: PWUX) -> None:
        self._driver = driver

    def read_temperature(self) -> Quantity[Celsius]:
        return Temperature(self._driver.get_temp())

    def set_pointer(self, enable: bool) -> None:
        self._driver.set_pointer(enable)

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockPyrometerAdapter(IPyrometerAdapter):
    def __init__(self, base_temp: float = 30.0, noise_level: float = 0.01) -> None:
        self.base_temp = base_temp
        self.noise_level = noise_level

        self._pointer = False

    def read_temperature(self) -> Quantity[Celsius]:
        noise = random.uniform(-self.noise_level, self.noise_level)  # noqa: S311
        val = self.base_temp + noise
        return Temperature(val)

    def set_pointer(self, enable: bool) -> None:
        self._pointer = enable
        print(f"[Mock pyrometer] Point: {enable}")

    def close(self) -> None:
        print("Mock pyrometer closed.")
