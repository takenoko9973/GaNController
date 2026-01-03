from PySide6.QtCore import Slot

from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.features.nea_activation.domain.nea_config import NEAConfig
from gan_controller.features.setting.model.app_config import AppConfig

from .dtos.nea_params import NEAActivationResult
from .nea_runner import NEAActivationRunner
from .state import NEAActivationState
from .view import NEAActivationTab


class NEAActivationController(ITabController):
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

        self._load_initial_config()

    def _load_initial_config(self) -> None:
        """起動時に設定ファイルを読み込んでUIにセットする"""
        config = NEAConfig.load()
        self._view.set_ui_from_config(config)

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
    # =================================================

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != NEAActivationState.IDLE:  # 二重起動防止
            return

        # 設定読み込み (ファイルを用いる)
        app_config = AppConfig.load()
        # 実験条件はウィンドウから所得
        condition_params = self._view.get_condition_params()
        log_params = self._view.get_log_params()
        init_control_params = self._view.get_control_params()

        self.set_state(NEAActivationState.RUNNING)

        self.runner = NEAActivationRunner(
            app_config, condition_params, log_params, init_control_params
        )
        self.worker = ExperimentWorker(self.runner)
        self._attach_worker(self.worker)

        self.worker.start()

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
        params = self._view.get_control_params()
        self.runner.update_params(params)

    # =================================================
    # Runner -> View
    # =================================================

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
