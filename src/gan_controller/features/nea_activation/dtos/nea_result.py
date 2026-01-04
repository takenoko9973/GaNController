from dataclasses import dataclass

from gan_controller.common.dtos.electricity import ElectricValuesDTO
from gan_controller.common.dtos.result import ExperimentResult
from gan_controller.common.types.quantity.quantity import Quantity


@dataclass
class NEAActivationResult(ExperimentResult):
    laser_power_pv: Quantity
    ext_pressure: Quantity
    sip_pressure: Quantity
    photocurrent: Quantity
    bright_pc: Quantity
    dark_pc: Quantity
    quantum_efficiency: Quantity
    electricity: ElectricValuesDTO
    timestamp: Quantity
