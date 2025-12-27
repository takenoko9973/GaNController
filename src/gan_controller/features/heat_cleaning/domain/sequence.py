from abc import ABC, abstractmethod
from enum import StrEnum


class SequenceMode(StrEnum):
    RISING = "Rising"
    HEAT_CLEANING = "HeatCleaning"
    DECREASE = "Decrease"
    WAIT = "Wait"


class Sequence(ABC):
    mode_char: str
    mode_type: SequenceMode

    def __init__(self, duration_sec: float, exponent: float) -> None:
        self.duration_sec = duration_sec
        self.exponent = exponent

    def __str__(self) -> str:
        return f"[{self.duration_sec}, '{self.mode_char}', {self.exponent}]"

    @property
    def mode_name(self) -> str:
        return self.mode_type.value

    # ====================================================================

    @abstractmethod
    def _current_profile(self, elapsed_time: float) -> float:
        pass

    def current(self, target_current: float, elapsed_time: float) -> float:
        profile = self._current_profile(elapsed_time)
        return target_current * max(0, min(profile, 1))

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
    mode_init = "r"
    mode_type = SequenceMode.RISING

    def _current_profile(self, elapsed_time: float) -> float:
        # 昇温 I = [hc_c] * (t / total_t)^[Exponent]
        return (elapsed_time / self.duration_sec) ** self.exponent


class HeatCleaning(Sequence):
    mode_init = "c"
    mode_type = SequenceMode.HEAT_CLEANING

    def _current_profile(self, _: float) -> float:
        return 1


class Decrease(Sequence):
    mode_init = "d"
    mode_type = SequenceMode.DECREASE

    def _current_profile(self, elapsed_time: float) -> float:
        # 降温 I = [hc_c] * (total_t - t) / total_t
        return (self.duration_sec - elapsed_time) / self.duration_sec


class Wait(Sequence):
    mode_init = "w"
    mode_type = SequenceMode.WAIT

    def _current_profile(self, _: float) -> float:
        return 0
