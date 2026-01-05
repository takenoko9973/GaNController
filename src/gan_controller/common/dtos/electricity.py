from typing import Any

from pydantic import BaseModel

from gan_controller.common.types.electricity import ElectricProperties
from gan_controller.common.types.quantity import Quantity
from gan_controller.common.types.quantity.unit_types import Ampere, Volt, Watt


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
