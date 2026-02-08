from PySide6.QtCore import Slot
from PySide6.QtWidgets import QInputDialog, QMessageBox

from gan_controller.common.application.global_messenger import GlobalMessenger
from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.io.log_manager import LogFile, LogManager
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.heat_cleaning.application.runner import HCActivationRunner
from gan_controller.features.heat_cleaning.application.validator import ProtocolValidator
from gan_controller.features.heat_cleaning.constants import NEW_PROTOCOL_TEXT
from gan_controller.features.heat_cleaning.infrastructure.persistence import FileProtocolRepository
from gan_controller.features.heat_cleaning.presentation.view import HeatCleaningMainView
from gan_controller.features.heat_cleaning.recorder import HCLogRecorder
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult
from gan_controller.features.heat_cleaning.state import HCActivationState


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView

    _repository: FileProtocolRepository
    _validator: ProtocolValidator

    _state: HCActivationState

    worker: ExperimentWorker | None
    runner: HCActivationRunner | None

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()

        self._view = view

        self._repository = FileProtocolRepository()
        self._validator = ProtocolValidator()

        self._attach_view()

        self._state = HCActivationState.IDLE
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

    def set_state(self, state: HCActivationState) -> None:
        """状態変更"""
        self._state = state
        self._view.set_running(self._state)

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

    def _refresh_protocol_list(self) -> None:
        """プロトコルフォルダを走査してプルダウンを更新する"""
        protocol_names = self._repository.list_names()

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
    # Protocol Save Helpers
    # =================================================

    def _should_overwrite(self, name: str) -> bool:
        """同名のプロトコルが存在するか確認し、存在する場合は上書きするか確認"""
        if self._repository.exists(name):
            ret = QMessageBox.question(
                self._view,
                "上書き確認",
                f"プロトコル '{name}' は既に存在します。\n上書きしますか？",  # noqa: RUF001
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            return ret == QMessageBox.StandardButton.Yes

        return True

    def _ask_save_name(self, default_text: str = "") -> str | None:
        """名前入力ダイアログを表示"""
        text, response = QInputDialog.getText(
            self._view,
            "プロトコル新規保存",
            "プロトコル名を入力してください\n(英大文字と数字のみ):",
            text=default_text,
        )

        return text.strip() if response and text else None

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
            config = self._repository.load(protocol_name)

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
            if not self._should_overwrite(current_name):  # 確認
                return

            self._repository.save(current_name, self._view.get_full_config())

    @Slot()
    def _on_save_as(self) -> None:
        """名前をつけて保存"""
        current_name = self._view.protocol_select_panel.current_selected_protocol()

        # 新規作成の場合はデフォルトの入力欄は空白に
        if current_name == NEW_PROTOCOL_TEXT:
            current_name = ""

        while True:
            new_name = self._ask_save_name(current_name)
            if new_name is None:
                break

            new_name = new_name.strip().upper()  # 大文字化

            # 名前形式確認
            is_valid, msg = self._validator.validate_name(new_name)
            if not is_valid:
                # 名前が不正なら再度入力
                QMessageBox.warning(self._view, "エラー", msg)
                continue

            # 上書き確認
            if not self._should_overwrite(new_name):
                current_name = new_name
                continue

            # 保存
            self._repository.save(new_name, self._view.get_full_config())

            # リストを更新、新しく名付けたものを選択
            self._refresh_protocol_list()
            self._view.protocol_select_panel.set_current_selected_protocol(new_name)

            # 保存完了ループ脱出
            break

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
        if self._state != HCActivationState.IDLE:  # 二重起動防止
            return

        # 前回のグラフ等をクリア
        self._view.clear_view()

        # 設定読み込み (ファイルを用いる)
        app_config = AppConfig.load()
        # 実験条件はウィンドウから所得
        config = self._view.get_full_config()

        log_file = self._create_recorder(app_config, config)
        recorder = HCLogRecorder(log_file, config)

        self.set_state(HCActivationState.RUNNING)

        self.runner = HCActivationRunner(app_config, config, recorder)
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
        self.set_state(HCActivationState.IDLE)
