from PySide6.QtCore import Slot

from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.io.log_manager import LogFile, LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.heat_cleaning.application.protocol_service import (
    ProtocolService,
    SaveContext,
)
from gan_controller.features.heat_cleaning.application.runner import HeatCleaningRunner
from gan_controller.features.heat_cleaning.application.validator import ProtocolValidator
from gan_controller.features.heat_cleaning.constants import NEW_PROTOCOL_TEXT
from gan_controller.features.heat_cleaning.domain.state import HeatCleaningState
from gan_controller.features.heat_cleaning.infrastructure.persistence import (
    FileProtocolRepository,
    HCLogRecorder,
)
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView

    _protocol_service: ProtocolService
    _validator: ProtocolValidator

    _state: HeatCleaningState

    worker: ExperimentWorker | None
    runner: HeatCleaningRunner | None

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()

        self._view = view

        repository = FileProtocolRepository()
        validator = ProtocolValidator()
        self._protocol_service = ProtocolService(repository, validator)

        self._attach_view()

        self._state = HeatCleaningState.IDLE
        self._cleanup()

        self._refresh_protocol_list()

    def _attach_view(self) -> None:
        self._view.protocol_select_panel.protocol_changed.connect(self._on_protocol_changed)
        self._view.protocol_select_panel.protocol_saved.connect(self._on_save_action)

        self._view.save_action_requested.connect(self._on_save_action)
        self._view.save_as_requested.connect(self._on_save_as)

        self._view.execution_panel.start_requested.connect(self.experiment_start)
        self._view.execution_panel.stop_requested.connect(self.experiment_stop)

        # ログ設定変更時のプレビュー更新
        self._view.log_setting_panel.config_changed.connect(self._update_log_preview)

    def _attach_worker(self, worker: ExperimentWorker) -> None:
        worker.result_emitted.connect(self.on_result)
        worker.error_occurred.connect(self.on_error)
        worker.finished.connect(self.on_finished)

    def _cleanup(self) -> None:
        self.worker = None
        self.runner = None

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

    def _refresh_protocol_list(self) -> None:
        """プロトコルフォルダを走査してプルダウンを更新する"""
        protocol_names = self._protocol_service.get_protocol_names()

        # 一番下に「新しいプロトコル...」を追加
        items = protocol_names
        items.append(NEW_PROTOCOL_TEXT)
        self._view.protocol_select_panel.set_protocol_items(items)

        # デフォルト選択
        self._view.protocol_select_panel.protocol_combo.blockSignals(True)  # 無駄なシグナル停止
        default_selection = items[0] if protocol_names else NEW_PROTOCOL_TEXT
        self._view.protocol_select_panel.set_current_selected_protocol(default_selection)
        self._view.protocol_select_panel.protocol_combo.blockSignals(False)

        # 初期選択状態の内容をロード
        self._on_protocol_changed(default_selection)

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
    # View Events
    # =================================================

    @Slot(str)
    def _on_protocol_changed(self, protocol_name: str) -> None:
        """プルダウンの選択が変更されたときの処理"""
        if protocol_name == NEW_PROTOCOL_TEXT:
            # 新規作成時はデフォルト設定
            config = ProtocolConfig()
        else:
            try:
                config = self._protocol_service.load_protocol(protocol_name)
            except Exception:  # noqa: BLE001
                config = ProtocolConfig()

        self._view.set_full_config(config)

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

        new_name = self._view.ask_new_name(current_name).upper()
        if new_name == "":
            return

        # 保存処理
        self._save_protocol(new_name)

    def _save_protocol(self, name: str) -> None:
        """保存処理を行い、通知する"""
        context = SaveContext(
            name,
            self._view.get_full_config(),
            self._view.confirm_overwrite,
        )
        success, msg = self._protocol_service.save_protocol(context)

        if success:
            self._refresh_protocol_list()
            self._view.protocol_select_panel.set_current_selected_protocol(name)
            self.status_message_requested.emit(f"プロトコル {name} を保存しました", 5000)
        elif "キャンセル" not in msg:
            self._view.show_error(msg)

    # =================================================
    # View -> Runner
    # =================================================

    def _create_recorder(self, app_config: AppConfig, protocol_config: ProtocolConfig) -> LogFile:
        manager = LogManager(app_config.common.get_tz(), app_config.common.encode)

        # ログファイル準備
        update_date = protocol_config.log.update_date_folder
        major_update = protocol_config.log.update_major_number

        log_dir = manager.get_date_directory(update_date)
        return log_dir.create_logfile(
            protocol_name=self._view.protocol_select_panel.current_selected_protocol(),
            major_update=major_update,
        )

    @Slot()
    def experiment_start(self) -> None:
        """実験開始処理"""
        if self._state != HeatCleaningState.IDLE:  # 二重起動防止
            return

        # 前回のグラフ等をクリア
        self._view.clear_view()

        # 設定読み込み (ファイルを用いる)
        app_config = AppConfig.load()
        # 実験条件はウィンドウから所得
        config = self._view.get_full_config()

        log_file = self._create_recorder(app_config, config)
        recorder = HCLogRecorder(log_file, config)

        self.set_state(HeatCleaningState.RUNNING)

        self.runner = HeatCleaningRunner(app_config, config, recorder)
        self.worker = ExperimentWorker(self.runner)
        self._attach_worker(self.worker)

        self.worker.start()

    @Slot()
    def experiment_stop(self) -> None:
        """実験中断処理"""
        if self._state != HeatCleaningState.RUNNING or self.runner is None:
            return

        self.set_state(HeatCleaningState.STOPPING)
        self.runner.stop()

    # =================================================
    # Runner -> View
    # =================================================

    @Slot(object)
    def on_result(self, result: HCRunnerResult) -> None:
        """結果表示"""
        self._view.update_view(result)

    @Slot(str)
    def on_error(self, message: str) -> None:
        """エラーメッセージ表示とログ出力処理"""

    @Slot()
    def on_finished(self) -> None:
        """実験終了処理"""
        print("ex finished")

        self._cleanup()
        self.set_state(HeatCleaningState.IDLE)
