from enum import Enum, auto


class HeatCleaningState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()
