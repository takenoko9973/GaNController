from abc import ABC, abstractmethod
from enum import StrEnum


class SequenceMode(StrEnum):
    RISING = "Rising"
    HEAT_CLEANING = "HeatCleaning"
    DECREASE = "Decrease"
    WAIT = "Wait"


class Sequence(ABC):
    mode_init: str
    mode_type: SequenceMode

    def __init__(self, duration_second: float, exponent: float) -> None:
        self.duration_second = duration_second
        self.exponent = exponent
        self.mode_name = self.mode_type.value

    def __str__(self) -> str:
        return f"[{self.duration_second}, '{self.mode_init}', {self.exponent}]"

    @abstractmethod
    def current_profile(self, elapsed_time: float) -> float:
        pass

    def current(self, target_current: float, elapsed_time: float) -> float:
        profile = self.current_profile(elapsed_time)
        return target_current * max(0, min(profile, 1))

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

    def __init__(self, duration_second: int, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "r"

    def current_profile(self, elapsed_time: float) -> float:
        # 昇温 I = [hc_c] * t^[Exponent] (+ StartCurrent)
        return (elapsed_time / self.duration_second) ** self.exponent


class HeatCleaning(Sequence):
    mode_type = SequenceMode.HEAT_CLEANING

    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "c"

    def current_profile(self, _: float) -> float:
        return 1


class Decrease(Sequence):
    mode_type = SequenceMode.DECREASE

    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "d"

    def current_profile(self, elapsed_time: float) -> float:
        # 降温 I = -[hc_c] * t (+ StartCurrent)
        return (self.duration_second - elapsed_time) / self.duration_second


class Wait(Sequence):
    mode_type = SequenceMode.WAIT

    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "w"

    def current_profile(self, _: float) -> float:
        return 0
