from abc import ABC, abstractmethod
from typing import Protocol

from gan_controller.core.domain.result import ExperimentResult


class IExperimentObserver(Protocol):
    """実験の進捗や結果を受け取るためのインターフェース"""

    def on_step_completed(self, result: ExperimentResult) -> None: ...
    def on_error(self, message: str) -> None: ...
    def on_finished(self) -> None: ...
    def is_interruption_requested(self) -> bool: ...

    def on_message(self, message: str) -> None: ...


class IExperimentWorkflow(ABC):
    """実験ロジック本体の基底クラス"""

    @abstractmethod
    def execute(self, observer: IExperimentObserver) -> None:
        """
        実験のメイン処理
        このメソッドは別スレッド(Worker)内で実行される
        """
