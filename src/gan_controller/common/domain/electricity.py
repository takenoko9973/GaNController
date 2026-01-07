from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from gan_controller.common.domain.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import Ampere, Volt, Watt


class ElectricProperties(StrEnum):
    """電気特性"""

    CURRENT = "current"
    VOLTAGE = "voltage"
    POWER = "power"

    @classmethod
    def get_list(cls) -> list[str]:
        return list(cls)

    def get_name(self) -> str:
        if self == ElectricProperties.CURRENT:
            return "Current"
        if self == ElectricProperties.VOLTAGE:
            return "Voltage"
        if self == ElectricProperties.POWER:
            return "Power"

        msg = "Invalid enum value."
        raise ValueError(msg)

    def get_unit(self) -> str:
        if self == ElectricProperties.CURRENT:
            return "A"
        if self == ElectricProperties.VOLTAGE:
            return "V"
        if self == ElectricProperties.POWER:
            return "W"

        msg = "Invalid enum value."
        raise ValueError(msg)


class ElectricValuesDTO(BaseModel):
    """電力測定データDTO"""

    current: Quantity[Ampere]
    voltage: Quantity[Volt]
    power: Quantity[Watt]

    def get_value(self, enum: ElectricProperties) -> Quantity[Any]:
        if enum == ElectricProperties.CURRENT:
            return self.current
        if enum == ElectricProperties.VOLTAGE:
            return self.voltage
        if enum == ElectricProperties.POWER:
            return self.power

        msg = f"Invalid enum value: {enum}"
        raise ValueError(msg)
