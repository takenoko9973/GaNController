from enum import Enum


class ElectricProperties(Enum):
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
