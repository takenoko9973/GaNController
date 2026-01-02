from PySide6.QtCore import QObject, Slot

from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.features.nea_activation.dtos.nea_dto import NEAActivationResult

from .nea_runner import NEAActivationRunner
from .state import NEAActivationState
from .view import NEAActivationTab


class NEAActivationController(QObject):
    _view: NEAActivationTab

    _state: NEAActivationState

    runner: NEAActivationRunner
    worker: ExperimentWorker

    def __init__(self, view: NEAActivationTab) -> None:
        super().__init__()

        self._view = view
        self._attach_view()

        self._state = NEAActivationState.IDLE
        self._cleanup()

    def _attach_view(self) -> None:
        self._view.experiment_start.connect(self.experiment_start)
        self._view.experiment_stop.connect(self.experiment_stop)
        self._view.setting_apply.connect(self.setting_apply)

    def _attach_worker(self, worker: ExperimentWorker) -> None:
        worker.result_emitted.connect(self.on_result)
        worker.error_occurred.connect(self.on_error)
        worker.finished_ok.connect(self.on_finished)

    def _cleanup(self) -> None:
        self.worker = None
        self.runner = None

    def set_state(self, state: NEAActivationState) -> None:
        """状態変更"""
        self._state = state
        self._view.set_running(self._state)

    # =================================================
    # View -> Runner

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != NEAActivationState.IDLE:  # 二重起動防止
            return

        self.set_state(NEAActivationState.RUNNING)

        # params = self.view.get_parameters()
        # self.config_manager.experiments["experiment_a"].update(params)

        self.runner = NEAActivationRunner()
        self.worker = ExperimentWorker(self.runner)
        self._attach_worker(self.worker)

        self.worker.start()

        # self.view.set_running(True)

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != NEAActivationState.RUNNING:
            return

        self.set_state(NEAActivationState.STOPPING)
        self.runner.stop()

    @Slot()
    def setting_apply(self) -> None:
        """実験途中での値更新"""
        print("ex apply")

    # =================================================

    # Runner -> View

    @Slot(object)
    def on_result(self, result: NEAActivationResult) -> None:
        """結果表示とログ出力処理"""
        # self.view.update_values(result)
        # self.logger.log(result)

    @Slot(str)
    def on_error(self, message: str) -> None:
        """エラーメッセージ表示とログ出力処理"""

    @Slot()
    def on_finished(self) -> None:
        """実験終了処理"""
        print("ex finished")

        self._cleanup()
        self.set_state(NEAActivationState.IDLE)
