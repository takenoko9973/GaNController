from enum import Enum, auto


class HCActivationState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()
