from PySide6.QtCore import Slot

from gan_controller.core.constants import LOG_DIR
from gan_controller.core.domain.app_config import AppConfig
from gan_controller.features.heat_cleaning.application.protocol_manager import (
    ProtocolManager,
    SaveContext,
)
from gan_controller.features.heat_cleaning.application.workflow import HeatCleaningWorkflow
from gan_controller.features.heat_cleaning.domain.config import ProtocolConfig
from gan_controller.features.heat_cleaning.domain.constants import NEW_PROTOCOL_TEXT
from gan_controller.features.heat_cleaning.domain.models import (
    HCExperimentResult,
    HeatCleaningState,
)
from gan_controller.features.heat_cleaning.infrastructure.hardware import (
    RealHCHardwareBackend,
    SimulationHCHardwareBackend,
)
from gan_controller.features.heat_cleaning.infrastructure.persistence import (
    HCLogRecorder,
    ProtocolRepository,
)
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView
from gan_controller.infrastructure.persistence.log_manager import LogManager
from gan_controller.presentation.async_runners.manager import AsyncExperimentManager
from gan_controller.presentation.components.tab_controller import ITabController


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView
    _protocol_manager: ProtocolManager
    _state: HeatCleaningState

    _runner_manager: AsyncExperimentManager

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()
        self._view = view

        repository = ProtocolRepository()
        self._protocol_manager = ProtocolManager(repository)
        self._runner_manager = AsyncExperimentManager()

        self._connect_view_signals()
        self._connect_manager_signals()

        self.set_state(HeatCleaningState.IDLE)
        self._refresh_protocol_list()

    def _connect_view_signals(self) -> None:
        """Viewからのシグナル接続"""
        self._view.protocol_select_panel.protocol_changed.connect(self._on_protocol_changed)
        self._view.protocol_select_panel.protocol_saved.connect(self._on_save_action)

        self._view.save_action_requested.connect(self._on_save_action)
        self._view.save_as_requested.connect(self._on_save_as)

        self._view.execution_panel.start_requested.connect(self.experiment_start)
        self._view.execution_panel.stop_requested.connect(self.experiment_stop)

        # ログ設定変更時のプレビュー更新
        self._view.log_setting_panel.config_changed.connect(self._update_log_preview)

    def _connect_manager_signals(self) -> None:
        """実験ロジックからの通知を受け取るシグナルの接続"""
        self._runner_manager.step_result_observed.connect(self.on_result)
        self._runner_manager.error_occurred.connect(self.on_error)
        self._runner_manager.finished.connect(self.on_finished)
        self._runner_manager.message_logged.connect(self.on_message)

    def set_state(self, state: HeatCleaningState) -> None:
        """状態変更"""
        self._state = state
        self._view.set_running(self._state)

        # 待機中以外なら、タブをロック
        should_lock = state != HeatCleaningState.IDLE
        self.tab_lock_requested.emit(should_lock)

    def on_close(self) -> None:
        """アプリ終了時に設定を保存する"""
        # 現在のUIの状態からConfigオブジェクトを生成
        # current_config = self._view.get_full_config()

        # ファイルに保存
        # current_config.save(HC_CONFIG_PATH)

    # =================================================
    # Protocol Management
    # =================================================

    def _refresh_protocol_list(self) -> None:
        """プロトコルフォルダを走査してプルダウンを更新する"""
        names = self._protocol_manager.get_protocol_names()
        items = [*names, NEW_PROTOCOL_TEXT]  # 一番下に「新しいプロトコル...」を追加

        self._view.protocol_select_panel.set_protocol_items(items)

        # デフォルト選択
        default = items[0] if names else NEW_PROTOCOL_TEXT
        self._view.protocol_select_panel.set_current_selected_protocol(default)
        self._on_protocol_changed(default)

    @Slot(str)
    def _on_protocol_changed(self, protocol_name: str) -> None:
        """プルダウンの選択が変更されたときの処理"""
        if protocol_name == NEW_PROTOCOL_TEXT:
            # 新規作成時はデフォルト設定
            config = ProtocolConfig()
        else:
            try:
                config = self._protocol_manager.load_protocol(protocol_name)
            except Exception as e:  # noqa: BLE001
                print(f"Load failed: {e}")
                config = ProtocolConfig()

        self._view.set_full_config(config)
        self._update_log_preview()

    @Slot()
    def _on_save_action(self) -> None:
        """通常保存されたときの処理"""
        current_name = self._view.protocol_select_panel.current_selected_protocol()
        if current_name == NEW_PROTOCOL_TEXT:
            # 新規作成
            self._on_save_as()
        else:
            # 上書き保存
            current_name = current_name.strip().upper()  # 大文字化
            self._save_protocol(current_name)

    @Slot()
    def _on_save_as(self) -> None:
        """名前をつけて保存"""
        current_name = self._view.protocol_select_panel.current_selected_protocol()
        # 新規作成の場合はデフォルトの入力欄は空白に
        if current_name == NEW_PROTOCOL_TEXT:
            current_name = ""

        new_name = self._view.ask_new_name(current_name).strip().upper()
        if new_name != "":
            # 保存処理
            self._save_protocol(new_name)

    def _save_protocol(self, name: str) -> None:
        """保存処理を行い、通知する"""
        context = SaveContext(
            name,
            self._view.get_full_config(),
            self._view.confirm_overwrite,
        )
        success, msg = self._protocol_manager.save_protocol(context)

        if success:
            self._refresh_protocol_list()
            self._view.protocol_select_panel.set_current_selected_protocol(name)
            self.status_message_requested.emit(f"プロトコル {name} を保存しました", 5000)
        elif "キャンセル" not in msg:
            self._view.show_error(msg)

    # =================================================
    # Experiment Execution
    # =================================================

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != HeatCleaningState.IDLE:  # 二重起動防止
            return

        self.set_state(HeatCleaningState.RUNNING)
        self._view.clear_view()

        # 設定読み込み
        app_config = AppConfig.load()
        protocol_config = self._view.get_full_config()

        # 2. ハードウェアの接続 (Context Managerの手動制御)
        try:
            is_sim = getattr(app_config.common, "is_simulation_mode", False)
            if is_sim:
                backend = SimulationHCHardwareBackend(app_config.devices)
            else:
                backend = RealHCHardwareBackend(app_config.devices)

            recorder = self._create_recorder(app_config, protocol_config)

            # Runner作成
            workflow = HeatCleaningWorkflow(backend, recorder, protocol_config)
            self._runner_manager.start_workflow(workflow)

        except Exception as e:  # noqa: BLE001
            self._view.show_error(f"実験開始準備エラー: {e}")
            self.set_state(HeatCleaningState.IDLE)

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != HeatCleaningState.RUNNING or not self._runner_manager.is_running():
            return

        self.set_state(HeatCleaningState.STOPPING)
        self._runner_manager.stop_workflow()

    # =================================================
    # Runner -> View
    # =================================================

    @Slot(object)
    def on_result(self, result: HCExperimentResult) -> None:
        """結果表示"""
        self._view.update_view(result)

    @Slot(str)
    def on_error(self, message: str) -> None:
        """エラーメッセージ表示とログ出力処理"""
        self._view.show_error(f"Error occurred: {message}")

    @Slot()
    def on_finished(self) -> None:
        """実験終了処理"""
        self.set_state(HeatCleaningState.IDLE)

    @Slot(str)
    def on_message(self, message: str) -> None:
        """実験ロジックからの通知を受け取ったときの処理"""
        self.status_message_requested.emit(message, 10000)

    # =================================================
    # Log Helpers
    # =================================================

    def _create_recorder(
        self, app_config: AppConfig, protocol_config: ProtocolConfig
    ) -> HCLogRecorder:
        manager = LogManager(LOG_DIR, app_config.common.encode)

        # ログファイル準備
        update_date = protocol_config.log.update_date_folder
        major_update = protocol_config.log.update_major_number

        log_dir = manager.get_active_directory(update_date)
        log_file = log_dir.create_logfile(
            protocol_name=self._view.protocol_select_panel.current_selected_protocol(),
            major_update=major_update,
        )

        print(f"Log file created: {log_file.path}")
        return HCLogRecorder(log_file, protocol_config)

    def _update_log_preview(self) -> None:
        """現在の設定に基づいてログファイル名をプレビュー更新"""
        try:
            # マネージャー呼び出し
            app_config = AppConfig.load()
            manager = LogManager(LOG_DIR, app_config.common.encode)
            log_config = self._view.log_setting_panel.get_config()

            # 番号取得
            date_dir = manager.get_active_directory(log_config.update_date_folder)
            next_numbers = date_dir.get_next_number(major_update=log_config.update_major_number)

            number_text = f"{next_numbers[0]}.{next_numbers[1]}"
            self._view.log_setting_panel.set_preview_text(number_text)

        except Exception as e:  # noqa: BLE001
            print(f"Preview update failed: {e}")
            self._view.log_setting_panel.set_preview_text("Error")
