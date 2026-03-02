import queue

from PySide6.QtCore import Slot

from gan_controller.core.constants import LOG_DIR, NEA_CONFIG_PATH
from gan_controller.core.domain.app_config import AppConfig
from gan_controller.features.nea_activation.application.workflow import NEAActivationWorkflow
from gan_controller.features.nea_activation.domain.config import NEAConfig
from gan_controller.features.nea_activation.domain.models import (
    NEAActivationState,
    NEAExperimentResult,
)
from gan_controller.features.nea_activation.infrastructure.hardware.backend import (
    RealNEAHardwareBackend,
    SimulationNEAHardwareBackend,
)
from gan_controller.features.nea_activation.infrastructure.persistence.recorder import (
    NEALogRecorder,
)
from gan_controller.features.nea_activation.presentation.view import NEAActivationMainView
from gan_controller.infrastructure.persistence.log_manager import LogManager
from gan_controller.presentation.async_runners.manager import AsyncExperimentManager
from gan_controller.presentation.components.tab_controller import ITabController


class NEAActivationController(ITabController):
    _view: NEAActivationMainView

    _state: NEAActivationState

    _runner_manager: AsyncExperimentManager

    def __init__(self, view: NEAActivationMainView) -> None:
        super().__init__()

        self._view = view

        self._runner_manager = AsyncExperimentManager()
        self._request_queue = queue.Queue()

        self._connect_view_signals()
        self._connect_manager_signals()

        self.set_state(NEAActivationState.IDLE)
        self._load_initial_config()

    def _connect_view_signals(self) -> None:
        """UI操作を受け取るシグナルの接続"""
        self._view.execution_panel.start_requested.connect(self.experiment_start)
        self._view.execution_panel.stop_requested.connect(self.experiment_stop)
        self._view.execution_panel.apply_requested.connect(self.setting_apply)

        # ログ設定変更時のプレビュー更新
        self._view.log_setting_panel.config_changed.connect(self._update_log_preview)

    def _connect_manager_signals(self) -> None:
        """実験ロジックからの通知を受け取るシグナルの接続"""
        self._runner_manager.step_result_observed.connect(self.on_result)
        self._runner_manager.error_occurred.connect(self.on_error)
        self._runner_manager.finished.connect(self.on_finished)
        self._runner_manager.message_logged.connect(self.on_message)

    def _load_initial_config(self) -> None:
        """起動時に設定ファイルを読み込んでUIにセットする"""
        config = NEAConfig.load(NEA_CONFIG_PATH)
        self._view.set_full_config(config)

    def set_state(self, state: NEAActivationState) -> None:
        """状態変更"""
        self._state = state
        self._view.set_running(self._state)

        # 待機中以外なら、タブをロック
        should_lock = state != NEAActivationState.IDLE
        self.tab_lock_requested.emit(should_lock)

    def on_close(self) -> None:
        """アプリ終了時に設定を保存する"""
        # 現在のUIの状態からConfigオブジェクトを生成
        current_config = self._view.get_full_config()

        # ファイルに保存
        current_config.save(NEA_CONFIG_PATH)

    # =================================================
    # View -> Runner
    # =================================================

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != NEAActivationState.IDLE:  # 二重起動防止
            return

        self.set_state(NEAActivationState.RUNNING)
        self._view.clear_view()  # 前回のグラフ等をクリア

        # 設定読み込み
        app_config = AppConfig.load()
        nea_config = self._view.get_full_config()

        try:
            is_sim = getattr(app_config.common, "is_simulation_mode", False)
            if is_sim:
                backend = SimulationNEAHardwareBackend(app_config.devices)
            else:
                backend = RealNEAHardwareBackend(app_config.devices)

            recorder = self._create_recorder(app_config, nea_config)

            workflow = NEAActivationWorkflow(backend, recorder, nea_config, self._request_queue)
            self._runner_manager.start_workflow(workflow)

        except Exception as e:  # noqa: BLE001
            message = f"実験開始準備エラー: {e}"
            self._view.show_error(message)
            self.status_message_requested.emit(message, 10000)
            self.set_state(NEAActivationState.IDLE)

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != NEAActivationState.RUNNING or not self._runner_manager.is_running():
            return

        self.set_state(NEAActivationState.STOPPING)
        self._runner_manager.stop_workflow()

    @Slot()
    def setting_apply(self) -> None:
        """実験途中での値更新"""
        config = self._view.execution_panel.get_config()

        if self._state == NEAActivationState.RUNNING and self._runner_manager.is_running():
            self._request_queue.put(config)

    # =================================================
    # Runner -> View
    # =================================================

    @Slot(object)
    def on_result(self, result: NEAExperimentResult) -> None:
        """結果表示とログ出力処理"""
        self._view.update_view(result)

    @Slot(str)
    def on_error(self, message: str) -> None:
        """エラーメッセージ表示とログ出力処理"""
        self._view.show_error(f"Error occurred: {message}")
        self.status_message_requested.emit(message, 10000)

    @Slot()
    def on_finished(self) -> None:
        """実験終了処理"""
        self.set_state(NEAActivationState.IDLE)

    @Slot(str)
    def on_message(self, message: str) -> None:
        """実験ロジックからの通知を受け取ったときの処理"""
        self.status_message_requested.emit(message, 10000)

    # =================================================
    # Log Helpers
    # =================================================

    def _create_recorder(self, app_config: AppConfig, nea_config: NEAConfig) -> NEALogRecorder:
        manager = LogManager(LOG_DIR, app_config.common.encode)

        # ログファイル準備
        update_date = nea_config.log.update_date_folder
        major_update = nea_config.log.update_major_number

        log_dir = manager.get_active_directory(update_date)
        log_file = log_dir.create_logfile(
            protocol_name="NEA",
            major_update=major_update,
        )

        print(f"Log file created: {log_file.path}")
        return NEALogRecorder(log_file, nea_config)

    def _update_log_preview(self) -> None:
        """現在の設定に基づいてログファイル名をプレビュー更新"""
        try:
            # マネージャー呼び出し
            app_config = AppConfig.load()
            manager = LogManager(LOG_DIR, app_config.common.encode)

            # 番号取得
            log_config = self._view.log_setting_panel.get_config()
            date_dir = manager.get_active_directory(log_config.update_date_folder)
            next_numbers = date_dir.get_next_number(major_update=log_config.update_major_number)

            number_text = f"{next_numbers[0]}.{next_numbers[1]}"
            self._view.log_setting_panel.set_preview_text(number_text)

        except Exception as e:  # noqa: BLE001
            print(f"Preview update failed: {e}")
            self._view.log_setting_panel.set_preview_text("Error")
