from dataclasses import dataclass

from gan_controller.common.dtos.electricity import ElectricValuesDTO
from gan_controller.common.dtos.result import ExperimentResult
from gan_controller.common.types.quantity.quantity import Quantity
from gan_controller.common.types.quantity.unit_types import (
    Ampere,
    Dimensionless,
    Pascal,
    Second,
    Volt,
    Watt,
)


@dataclass
class NEAActivationResult(ExperimentResult):
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
    bright_photocurrent: Quantity[Ampere]  # レーザー照射時
    bright_voltage: Quantity[Volt]  # 電圧換算
    dark_photocurrent: Quantity[Ampere]  # レーザー未照射時
    dark_voltage: Quantity[Volt]
    # 量子効率
    quantum_efficiency: Quantity[Dimensionless]
    # AMDの電源情報
    amd_electricity: ElectricValuesDTO
