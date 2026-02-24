from abc import ABC, abstractmethod


class Sequence(ABC):
    mode_init: str

    def __init__(self, duration_second: float, exponent: float) -> None:
        self.duration_second = duration_second
        self.exponent = exponent
        self.mode_name = self.__class__.__name__

    def __str__(self) -> str:
        return f"[{self.duration_second}, '{self.mode_init}', {self.exponent}]"

    @abstractmethod
    def current_profile(self, elapsed_time: float) -> float:
        pass

    def current(self, target_current: float, elapsed_time: float) -> float:
        profile = self.current_profile(elapsed_time)
        return target_current * max(0, min(profile, 1))


class Rising(Sequence):
    def __init__(self, duration_second: int, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "r"

    def current_profile(self, elapsed_time: float) -> float:
        # 昇温 I = [hc_c] * t^[Exponent] (+ StartCurrent)
        return (elapsed_time / self.duration_second) ** self.exponent


class HeatCleaning(Sequence):
    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "c"

    def current_profile(self, _: float) -> float:
        return 1


class Decrease(Sequence):
    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "d"

    def current_profile(self, elapsed_time: float) -> float:
        # 降温 I = -[hc_c] * t (+ StartCurrent)
        return (self.duration_second - elapsed_time) / self.duration_second


class Wait(Sequence):
    def __init__(self, duration_second: float, exponent: float) -> None:
        super().__init__(duration_second, exponent)
        self.mode_init = "w"

    def current_profile(self, _: float) -> float:
        return 0
