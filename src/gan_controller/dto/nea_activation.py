from dataclasses import dataclass

from gan_controller.domain.quantity import Quantity

from .base import ExperimentResult


@dataclass
class NEAActivationResult(ExperimentResult):
    ext_pressure: Quantity
    hv: Quantity
    photocurrent: Quantity
    timestamp: float
