from PySide6.QtCore import Slot

from gan_controller.common.application.global_messenger import GlobalMessenger
from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.heat_cleaning.runner import HCActivationRunner
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult
from gan_controller.features.heat_cleaning.state import HCActivationState
from gan_controller.features.heat_cleaning.view.main_view import HeatCleaningMainView


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView

    _state: HCActivationState

    worker: ExperimentWorker | None

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()

        self._view = view

        self._attach_view()

        self._state = HCActivationState.IDLE
        self._cleanup()

        self._load_initial_config()

    def _load_initial_config(self) -> None:
        """起動時に設定ファイルを読み込んでUIにセットする"""
        # config = HCConfig.load(HC_CONFIG_PATH)
        # self._view.set_full_config(config)

    def _attach_view(self) -> None:
        self._view.execution_panel.start_requested.connect(self.experiment_start)
        self._view.execution_panel.stop_requested.connect(self.experiment_stop)

    def _attach_worker(self, worker: ExperimentWorker) -> None:
        worker.result_emitted.connect(self.on_result)
        worker.error_occurred.connect(self.on_error)
        worker.finished.connect(self.on_finished)

    def _cleanup(self) -> None:
        self.worker = None
        self.runner = None

    def set_state(self, state: HCActivationState) -> None:
        """状態変更"""
        self._state = state
        # self._view.set_running(self._state)

        # 待機中以外なら、タブをロック
        should_lock = state != HCActivationState.IDLE
        GlobalMessenger().tab_lock_requested.emit(should_lock)

    def on_close(self) -> None:
        """アプリ終了時に設定を保存する"""
        # 現在のUIの状態からConfigオブジェクトを生成
        # current_config = self._view.get_full_config()

        # ファイルに保存
        # current_config.save(HC_CONFIG_PATH)

    # =================================================
    # View -> Runner
    # =================================================

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != HCActivationState.IDLE:  # 二重起動防止
            return

        # 前回のグラフ等をクリア
        # self._view.clear_view()

        # 設定読み込み (ファイルを用いる)
        app_config = AppConfig.load()
        # 実験条件はウィンドウから所得
        config = self._view.get_full_config()

        self.set_state(HCActivationState.RUNNING)

        self.runner = HCActivationRunner(app_config, config)
        self.worker = ExperimentWorker(self.runner)
        self._attach_worker(self.worker)

        self.worker.start()

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != HCActivationState.RUNNING or self.runner is None:
            return

        self.set_state(HCActivationState.STOPPING)
        self.runner.stop()

    # =================================================
    # Runner -> View
    # =================================================

    @Slot(object)
    def on_result(self, result: HCRunnerResult) -> None:
        """結果表示とログ出力処理"""
        self._view.update_view(result)
        # self.logger.log(result)

    @Slot(str)
    def on_error(self, message: str) -> None:
        """エラーメッセージ表示とログ出力処理"""

    @Slot()
    def on_finished(self) -> None:
        """実験終了処理"""
        print("ex finished")

        self._cleanup()
        self.set_state(HCActivationState.IDLE)
