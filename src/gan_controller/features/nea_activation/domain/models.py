from dataclasses import dataclass
from enum import Enum, auto

from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity.quantity import Quantity
from gan_controller.common.domain.quantity.unit_types import (
    Ampere,
    Dimensionless,
    Pascal,
    Second,
    Volt,
    Watt,
)
from gan_controller.common.hardware.adapters.laser_adapter import ILaserAdapter
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.adapters.power_supply_adapter import IPowerSupplyAdapter
from gan_controller.common.schemas.result import ExperimentResult


# =============================================================================
# Devices
# =============================================================================
@dataclass
class NEADevices:
    """NEA実験で使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    aps: IPowerSupplyAdapter
    laser: ILaserAdapter


# =============================================================================
# States
# =============================================================================
class NEAActivationState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()


# =============================================================================
# Result Data
# =============================================================================
@dataclass
class NEARunnerResult(ExperimentResult):
    """NEA活性化の測定結果 (必要そうな設定値や観測値は全て入れとく)"""

    timestamp: Quantity[Second]
    # レーザー出力
    laser_power_sv: Quantity[Watt]  # 設定値
    laser_power_pv: Quantity[Watt]  # 実出力
    # 圧力
    ext_pressure: Quantity[Pascal]
    sip_pressure: Quantity[Pascal]
    # 引き出し電圧 (HV)
    extraction_voltage: Quantity[Volt]
    # フォトカレント
    photocurrent: Quantity[Ampere]
    photocurrent_voltage: Quantity[Volt]
    bright_pc: Quantity[Ampere]  # レーザー照射時
    bright_pc_voltage: Quantity[Volt]  # 電圧換算
    dark_pc: Quantity[Ampere]  # レーザー未照射時
    dark_pc_voltage: Quantity[Volt]
    # 量子効率
    quantum_efficiency: Quantity[Dimensionless]
    # AMDの電源情報
    amd_electricity: ElectricMeasurement
