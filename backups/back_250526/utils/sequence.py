from abc import ABC, abstractmethod


class Sequence(ABC):
    time: float
    exponent: float

    def __init__(self, time: float, exponent: float) -> None:
        self.time = time
        self.exponent = exponent

    @abstractmethod
    def current_profile(self, elapsed_time: float) -> float:
        pass

    def current(self, target_current: float, elapsed_time: float) -> float:
        return target_current * self.current_profile(elapsed_time)


class Rising(Sequence):
    def current_profile(self, elapsed_time: float) -> float:
        return (elapsed_time / self.time) ** self.exponent


class HeatCleaning(Sequence):
    def current_profile(self, _: float) -> float:
        return 1


class Decrease(Sequence):
    def current_profile(self, elapsed_time: float) -> float:
        return (self.time - elapsed_time) / self.time


class Wait(Sequence):
    def current_profile(self, _: float) -> float:
        return 0
