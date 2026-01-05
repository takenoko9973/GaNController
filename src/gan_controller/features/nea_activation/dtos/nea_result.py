from dataclasses import dataclass

from gan_controller.common.dtos.electricity import ElectricValuesDTO
from gan_controller.common.dtos.result import ExperimentResult
from gan_controller.common.types.quantity.quantity import Quantity


@dataclass
class NEAActivationResult(ExperimentResult):
    """NEA活性化の測定結果 (必要そうな設定値や観測値は全て入れとく)"""

    timestamp: Quantity
    # レーザー出力
    laser_power_sv: Quantity  # 設定値
    laser_power_pv: Quantity  # 実出力
    # 圧力
    ext_pressure: Quantity
    sip_pressure: Quantity
    # 引き出し電圧 (HV)
    extraction_voltage: Quantity
    # フォトカレント
    photocurrent: Quantity
    bright_photocurrent: Quantity  # レーザー照射時
    dark_photocurrent: Quantity  # レーザー未照射時
    # 量子効率
    quantum_efficiency: Quantity
    # AMDの電源情報
    amd_electricity: ElectricValuesDTO
