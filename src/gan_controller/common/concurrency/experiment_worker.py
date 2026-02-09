from PySide6.QtCore import QThread, Signal

from gan_controller.common.application.runner import BaseRunner
from gan_controller.common.schemas.result import ExperimentResult


class ExperimentWorker(QThread):
    result_emitted = Signal(object)  # object: ExperimentResult
    error_occurred = Signal(str)

    def __init__(self, runner: BaseRunner) -> None:
        super().__init__()
        self.runner = runner
        self.runner.emit_result = self._on_result

    def _on_result(self, result: ExperimentResult) -> None:
        self.result_emitted.emit(result)

    def run(self) -> None:
        try:
            self.runner.run()
        except Exception as e:  # noqa: BLE001
            self.error_occurred.emit(str(e))
