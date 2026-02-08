from PySide6.QtCore import Slot

from gan_controller.common.application.global_messenger import GlobalMessenger
from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.constants import NEA_CONFIG_PATH
from gan_controller.common.io.log_manager import LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.nea_activation.presentation.view import NEAActivationMainView
from gan_controller.features.nea_activation.runner import NEAActivationRunner
from gan_controller.features.nea_activation.schemas import NEAConfig
from gan_controller.features.nea_activation.schemas.result import NEARunnerResult
from gan_controller.features.nea_activation.state import NEAActivationState


class NEAActivationController(ITabController):
    _view: NEAActivationMainView

    _state: NEAActivationState

    runner: NEAActivationRunner | None
    worker: ExperimentWorker | None

    def __init__(self, view: NEAActivationMainView) -> None:
        super().__init__()

        self._view = view
        self._attach_view()

        self._state = NEAActivationState.IDLE
        self._cleanup()

        self._load_initial_config()

    def _load_initial_config(self) -> None:
        """起動時に設定ファイルを読み込んでUIにセットする"""
        config = NEAConfig.load(NEA_CONFIG_PATH)
        self._view.set_full_config(config)

    def _attach_view(self) -> None:
        self._view.execution_panel.start_requested.connect(self.experiment_start)
        self._view.execution_panel.stop_requested.connect(self.experiment_stop)
        self._view.execution_panel.apply_requested.connect(self.setting_apply)

        # ログ設定変更時のプレビュー更新
        self._view.log_setting_panel.config_changed.connect(self._update_log_preview)

    def _attach_worker(self, worker: ExperimentWorker) -> None:
        worker.result_emitted.connect(self.on_result)
        worker.error_occurred.connect(self.on_error)
        worker.finished.connect(self.on_finished)

    def _cleanup(self) -> None:
        self.worker = None
        self.runner = None

    def set_state(self, state: NEAActivationState) -> None:
        """状態変更"""
        self._state = state
        self._view.set_running(self._state)

        # 待機中以外なら、タブをロック
        should_lock = state != NEAActivationState.IDLE
        GlobalMessenger().tab_lock_requested.emit(should_lock)

    def on_close(self) -> None:
        """アプリ終了時に設定を保存する"""
        # 現在のUIの状態からConfigオブジェクトを生成
        current_config = self._view.get_full_config()

        # ファイルに保存
        current_config.save(NEA_CONFIG_PATH)

    def _update_log_preview(self) -> None:
        """現在の設定に基づいてログファイル名をプレビュー更新"""
        try:
            # マネージャー呼び出し
            app_config = AppConfig.load()
            manager = LogManager(app_config.common.get_tz(), app_config.common.encode)

            # 番号取得
            log_config = self._view.log_setting_panel.get_config()
            date_dir = manager.get_date_directory(log_config.update_date_folder)
            next_numbers = date_dir.get_next_number(major_update=log_config.update_major_number)

            number_text = f"{next_numbers[0]}.{next_numbers[1]}"
            self._view.log_setting_panel.set_preview_text(number_text)

        except Exception as e:  # noqa: BLE001
            print(f"Preview update failed: {e}")
            self._view.log_setting_panel.set_preview_text("Error")

    # =================================================
    # View -> Runner
    # =================================================

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != NEAActivationState.IDLE:  # 二重起動防止
            return

        # 前回のグラフ等をクリア
        self._view.clear_view()

        # 設定読み込み (ファイルを用いる)
        app_config = AppConfig.load()
        # 実験条件はウィンドウから所得
        config = self._view.get_full_config()

        self.set_state(NEAActivationState.RUNNING)

        self.runner = NEAActivationRunner(app_config, config)
        self.worker = ExperimentWorker(self.runner)
        self._attach_worker(self.worker)

        self.worker.start()

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != NEAActivationState.RUNNING or self.runner is None:
            return

        self.set_state(NEAActivationState.STOPPING)
        self.runner.stop()

    @Slot()
    def setting_apply(self) -> None:
        """実験途中での値更新"""
        config = self._view.execution_panel.get_config()

        if self._state == NEAActivationState.RUNNING and self.runner is not None:
            self.runner.update_control_params(config)

    # =================================================
    # Runner -> View
    # =================================================

    @Slot(object)
    def on_result(self, result: NEARunnerResult) -> None:
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
        self.set_state(NEAActivationState.IDLE)
