import random
from abc import ABC, abstractmethod

from gan_controller.common.drivers.pfr_100l50 import PFR100L50
from gan_controller.common.types.quantity import Current, Power, Quantity, Voltage
from gan_controller.common.types.quantity.unit_types import Ampere, Volt, Watt


# Interface
class IPowerSupplyAdapter(ABC):
    @abstractmethod
    def set_output(self, on: bool) -> None:
        pass

    @abstractmethod
    def set_voltage(self, voltage: float) -> None:
        pass

    @abstractmethod
    def set_current(self, current: float) -> None:
        pass

    @abstractmethod
    def measure_voltage(self) -> Quantity[Volt]:
        pass

    @abstractmethod
    def measure_current(self) -> Quantity[Ampere]:
        pass

    @abstractmethod
    def measure_power(self) -> Quantity[Watt]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class PFR100L50Adapter(IPowerSupplyAdapter):
    def __init__(self, driver: PFR100L50) -> None:
        self._driver = driver

    def set_output(self, on: bool) -> None:
        self._driver.set_output(on)

    def set_voltage(self, voltage: float) -> None:
        self._driver.set_voltage(voltage)

    def set_current(self, current: float) -> None:
        self._driver.set_current(current)

    def measure_voltage(self) -> Quantity[Volt]:
        val = self._driver.measure_voltage()
        return Voltage(val)

    def measure_current(self) -> Quantity[Ampere]:
        val = self._driver.measure_current()
        return Current(val)

    def measure_power(self) -> Quantity[Watt]:
        val = self._driver.measure_power()
        return Power(val)

    def close(self) -> None:
        self._driver.close()


# ダミー用
class MockPowerSupplyAdapter(IPowerSupplyAdapter):
    def __init__(self) -> None:
        self._output_on = False
        self._setting_voltage = 0.0
        self._setting_current = 0.0

    def set_output(self, on: bool) -> None:
        self._output_on = on
        print(f"[Mock] Power Supply Output: {on}")

    def set_voltage(self, voltage: float) -> None:
        self._setting_voltage = voltage

    def set_current(self, current: float) -> None:
        self._setting_current = current

    def measure_voltage(self) -> Quantity[Volt]:
        # 出力ONなら設定値付近、OFFなら0
        val = self._setting_voltage if self._output_on else 0.0
        return Voltage(val)

    def measure_current(self) -> Quantity[Ampere]:
        # ダミーの負荷変動 (ONなら設定値付近)
        val = self._setting_current * random.uniform(0.95, 1.05) if self._output_on else 0.0  # noqa: S311
        return Current(val)

    def measure_power(self) -> Quantity[Watt]:
        v = self.measure_voltage().value_as()
        i = self.measure_current().value_as()
        return Power(v * i)

    def close(self) -> None:
        print("[Mock] Power Supply Closed")
