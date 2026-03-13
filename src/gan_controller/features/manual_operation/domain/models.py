from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from gan_controller.core.domain.quantity import Celsius, Quantity, Volt
from gan_controller.core.domain.result import ExperimentResult
from gan_controller.infrastructure.hardware.adapters.laser_adapter import ILaserAdapter
from gan_controller.infrastructure.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.infrastructure.hardware.adapters.pyrometer_adapter import IPyrometerAdapter


@dataclass
class ManualDevices:
    """Manual Operation で使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    pyrometer: IPyrometerAdapter
    laser: ILaserAdapter


class ManualState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()


class ManualCommandType(Enum):
    READ_PWUX_TEMP = auto()
    SET_PWUX_POINTER = auto()
    SET_LASER_POWER = auto()
    SET_LASER_EMISSION = auto()


@dataclass
class ManualCommand:
    command_type: ManualCommandType
    payload: Any | None = None


@dataclass
class ManualResult(ExperimentResult):
    gm10_values: dict[str, Quantity[Volt]] = field(default_factory=dict)
    pwux_temperature: Quantity[Celsius] | None = None
