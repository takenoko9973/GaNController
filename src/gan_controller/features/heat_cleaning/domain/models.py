from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from gan_controller.common.domain.electricity import ElectricMeasurement
from gan_controller.common.domain.quantity import Celsius, Pascal, Quantity, Second
from gan_controller.common.hardware.adapters.logger_adapter import ILoggerAdapter
from gan_controller.common.hardware.adapters.power_supply_adapter import IPowerSupplyAdapter
from gan_controller.common.hardware.adapters.pyrometer_adapter import IPyrometerAdapter
from gan_controller.common.schemas.result import ExperimentResult


# =============================================================================
# Devices
# =============================================================================
@dataclass
class HCDevices:
    """HeatCleaningで使用するデバイス群を保持するコンテナ"""

    logger: ILoggerAdapter
    hps: IPowerSupplyAdapter
    aps: IPowerSupplyAdapter
    pyrometer: IPyrometerAdapter


# =============================================================================
# States
# =============================================================================
class HeatCleaningState(Enum):
    """実験の進行状態"""

    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()


# =============================================================================
# Sequence Logic
# =============================================================================
class SequenceMode(Enum):
    RISING = ("Rising", "r")
    HEAT_CLEANING = ("HeatCleaning", "c")
    DECREASE = ("Decrease", "d")
    WAIT = ("Wait", "w")

    def __init__(self, display_name: str, initial: str) -> None:
        self.display_name = display_name  # 表示用シーケンス名
        self.initial = initial  # シーケンスイニシャル


class Sequence(ABC):
    mode_type: SequenceMode

    def __init__(self, duration_sec: float, exponent: float) -> None:
        self.duration_sec = duration_sec
        self.exponent = exponent

    def __str__(self) -> str:
        return f"[{self.duration_sec}, '{self.mode_type.initial}', {self.exponent}]"

    @property
    def mode_name(self) -> str:
        return self.mode_type.display_name

    # ====================================================================

    @abstractmethod
    def _current_profile_ratio(self, elapsed_time: float) -> float:
        """経過時間における出力比率 (0.0 - 1.0) を計算して返す"""

    def calculate_current(self, target_max_current: float, elapsed_time: float) -> float:
        """指定された最大電流値と経過時間から、現在の電流値を計算する"""
        if target_max_current <= 0:
            return 0.0

        ratio = self._current_profile_ratio(elapsed_time)
        # 0.0~1.0の範囲に収め、最大電流を掛ける
        return target_max_current * max(0, min(ratio, 1))

    # ====================================================================

    @classmethod
    def create(cls, mode: SequenceMode, duration: float, exponent: float) -> "Sequence | None":
        """指定されたモードに対応するサブクラスを探し、インスタンス化"""
        # 全サブクラスを走査 (Rising, HeatCleaning, ...)
        for subclass in cls.__subclasses__():
            # クラス側で定義している mode_type と一致するか確認
            if subclass.mode_type == mode:
                return subclass(duration, exponent)

        return None


class Rising(Sequence):
    mode_type = SequenceMode.RISING

    def _current_profile_ratio(self, elapsed_time: float) -> float:
        # 昇温 : I = [hc_c] * (t / total_t)^[Exponent]
        return (elapsed_time / self.duration_sec) ** self.exponent


class HeatCleaning(Sequence):
    mode_type = SequenceMode.HEAT_CLEANING

    def _current_profile_ratio(self, elapsed_time: float) -> float:  # noqa: ARG002
        # 一定
        return 1


class Decrease(Sequence):
    mode_type = SequenceMode.DECREASE

    def _current_profile_ratio(self, elapsed_time: float) -> float:
        # 降温 : I = [hc_c] * (total_t - t) / total_t
        return (self.duration_sec - elapsed_time) / self.duration_sec


class Wait(Sequence):
    mode_type = SequenceMode.WAIT

    def _current_profile_ratio(self, elapsed_time: float) -> float:  # noqa: ARG002
        # 待機 (電流ゼロ)
        return 0


# =============================================================================
# Result Data
# =============================================================================
@dataclass
class HCExperimentResult(ExperimentResult):
    """HeatCleaningの1ステップごとの結果データ"""

    # シーケンス情報
    sequence_index: int  # シーケンス番号 (1開始)
    sequence_name: str  # シーケンス名

    # 時間情報
    timestamp_step: Quantity[Second]  # シーケンス内の経過時間
    timestamp_total: Quantity[Second]  # 合計の経過時間

    # 圧力
    pressure_ext: Quantity[Pascal]
    pressure_sip: Quantity[Pascal]

    # 温度
    temperature_case: Quantity[Celsius]

    # 電源出力値
    electricity_hc: ElectricMeasurement
    electricity_amd: ElectricMeasurement
