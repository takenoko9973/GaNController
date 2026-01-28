from dataclasses import dataclass

from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import Celsius, Pascal, Quantity, Second
from gan_controller.common.schemas.result import ExperimentResult


@dataclass
class HCRunnerResult(ExperimentResult):
    """NEA活性化の測定結果 (必要そうな設定値や観測値は全て入れとく)"""

    current_sequence_index: int  # 現在のシーケンス番号 (1開始)
    current_sequence_name: str  # 現在のシーケンス名

    step_timestamp: Quantity[Second]  # シーケンス内の経過時間
    total_timestamp: Quantity[Second]  # 合計の経過時間
    # 圧力
    ext_pressure: Quantity[Pascal]
    sip_pressure: Quantity[Pascal]
    # 温度
    case_temperature: Quantity[Celsius]
    # HCの電源情報
    hc_electricity: ElectricMeasurement
    # AMDの電源情報
    amd_electricity: ElectricMeasurement
