from PySide6.QtCore import QThread, Signal

from gan_controller.dto.base import ExperimentResult
from gan_controller.runners.base import BaseRunner


class ExperimentWorker(QThread):
    result_emitted = Signal(object)  # object: ExperimentResult
    error_occurred = Signal(str)
    finished_ok = Signal()

    def __init__(self, runner: BaseRunner) -> None:
        super().__init__()
        self.runner = runner
        self.runner.emit_result = self._on_result

    def _on_result(self, result: ExperimentResult) -> None:
        self.result_emitted.emit(result)

    def run(self) -> None:
        try:
            self.runner.run()
            self.finished_ok.emit()
        except Exception as e:  # noqa: BLE001
            self.error_occurred.emit(str(e))
