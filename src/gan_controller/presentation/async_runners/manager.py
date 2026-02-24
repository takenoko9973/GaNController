from PySide6.QtCore import QObject, QThread, Signal, Slot

from gan_controller.core.domain.result import ExperimentResult

from .interfaces import IExperimentObserver, IExperimentWorkflow


class _WorkerObserver(IExperimentObserver):
    """Workflowからの通知をQtシグナルに変換するブリッジ"""

    def __init__(self, worker: "_ExperimentWorker") -> None:
        self._worker = worker

    def on_step_completed(self, result: ExperimentResult) -> None:
        self._worker.result_observed.emit(result)

    def on_error(self, message: str) -> None:
        self._worker.error_occurred.emit(message)

    def on_finished(self) -> None:
        self._worker.finished.emit()

    def is_interruption_requested(self) -> bool:
        return self._worker.interruption_requested

    def on_message(self, message: str) -> None:
        self._worker.message_logged.emit(message)


class _ExperimentWorker(QObject):
    """実際にQThread上で動くWorker"""

    finished = Signal()
    result_observed = Signal(object)
    error_occurred = Signal(str)
    message_logged = Signal(str)

    def __init__(self, workflow: IExperimentWorkflow) -> None:
        super().__init__()
        self._workflow = workflow
        self.interruption_requested = False

    @Slot()
    def run(self) -> None:
        self.interruption_requested = False
        observer = _WorkerObserver(self)
        try:
            self._workflow.execute(observer)
        except Exception as e:  # noqa: BLE001
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def stop(self) -> None:
        self.interruption_requested = True


class AsyncExperimentManager(QObject):
    """
    外部(Controller)から利用するFacadeクラス
    QThreadのライフサイクルを管理
    """

    step_result_observed = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()
    message_logged = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _ExperimentWorker | None = None

    def start_workflow(self, workflow: IExperimentWorkflow) -> None:
        """実験を開始する"""
        if self.is_running():
            return

        self._thread = QThread()
        self._worker = _ExperimentWorker(workflow)
        self._worker.moveToThread(self._thread)

        # シグナル接続
        self._thread.started.connect(self._worker.run)
        self._worker.result_observed.connect(self.step_result_observed)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.message_logged.connect(self.message_logged)

        # 終了処理のチェーン
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self.finished)
        self._thread.finished.connect(self._cleanup)

        self._thread.start()

    def stop_workflow(self) -> None:
        """実験を中断する"""
        if self._worker:
            self._worker.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _cleanup(self) -> None:
        self._thread = None
        self._worker = None
