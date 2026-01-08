from dataclasses import dataclass
from enum import Enum
from typing import Any

from gan_controller.common.domain.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import Ampere, Volt, Watt


class ElectricProperties(Enum):
    """電気特性定義 (表示名と単位を保持)"""

    # (フィールド名, 表示名, 単位)
    CURRENT = ("current", "Current", "A")
    VOLTAGE = ("voltage", "Voltage", "V")
    POWER = ("power", "Power", "W")

    def __init__(self, field_name: str, display_name: str, unit: str) -> None:
        self.field_name = field_name
        self.display_name = display_name
        self.unit_symbol = unit

    @property
    def name(self) -> str:
        return self.field_name

    @property
    def unit(self) -> str:
        return self.unit_symbol

    def __str__(self) -> str:
        return self.display_name


@dataclass(frozen=True)
class ElectricMeasurement:
    """電力測定データDTO"""

    current: Quantity[Ampere]
    voltage: Quantity[Volt]
    power: Quantity[Watt]

    def get_quantity(self, prop: ElectricProperties) -> Quantity[Any]:
        return getattr(self, prop.field_name)
