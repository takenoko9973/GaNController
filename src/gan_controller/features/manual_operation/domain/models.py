from dataclasses import dataclass, field

from gan_controller.core.domain.quantity import Celsius, Quantity, Volt
from gan_controller.core.domain.result import ExperimentResult


@dataclass
class ManualResult(ExperimentResult):
    gm10_values: dict[str, Quantity[Volt]] = field(default_factory=dict)
    pwux_temperature: Quantity[Celsius] | None = None
