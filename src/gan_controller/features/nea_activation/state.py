from enum import Enum, auto


class NEAActivationState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()
