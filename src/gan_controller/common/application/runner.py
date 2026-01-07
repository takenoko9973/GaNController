from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from gan_controller.common.dtos.result import ExperimentResult


class BaseRunner(ABC):
    def __init__(self) -> None:
        self.emit_result: Callable[[ExperimentResult], None] | None = None
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    @abstractmethod
    def run(self) -> None: ...
