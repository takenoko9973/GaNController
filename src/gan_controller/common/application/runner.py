from PySide6.QtCore import QThread, Signal

from gan_controller.common.schemas.result import ExperimentResult


class ExperimentRunner(QThread):
    step_result_observed: Signal = Signal(ExperimentResult)
    error_occurred: Signal = Signal(str)
