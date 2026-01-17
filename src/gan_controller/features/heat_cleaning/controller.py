import re
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QInputDialog, QMessageBox

from gan_controller.common.application.global_messenger import GlobalMessenger
from gan_controller.common.concurrency.experiment_worker import ExperimentWorker
from gan_controller.common.constants import PROTOCOLS_DIR
from gan_controller.common.schemas.app_config import AppConfig
from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.heat_cleaning.constants import NEW_PROTOCOL_TEXT
from gan_controller.features.heat_cleaning.runner import HCActivationRunner
from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult
from gan_controller.features.heat_cleaning.state import HCActivationState
from gan_controller.features.heat_cleaning.view import HeatCleaningMainView


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView

    _state: HCActivationState

    worker: ExperimentWorker | None
    runner: HCActivationRunner | None

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()

        self._view = view

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

    def _fetch_protocol_names(self, protocols_dir: Path = PROTOCOLS_DIR) -> list[str]:
        """プロトコル設定ファイルの名前一覧を取得"""
        if not (protocols_dir.exists() and protocols_dir.is_dir()):
            return []

        return [p.stem for p in protocols_dir.glob("*.toml")]

    def _refresh_protocol_list(self) -> None:
        """プロトコルフォルダを走査してプルダウンを更新する"""
        protocol_names = self._fetch_protocol_names()

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

    def _load_config_from_file(self, name: str) -> ProtocolConfig:
        """ファイルから設定を読み込む"""
        try:
            return ProtocolConfig.load(f"{name}.toml")
        except Exception as e:  # noqa: BLE001
            print(f"Failed to load protocol {name}: {e}")  # 読み込みに失敗したら、初期値を返す
            return ProtocolConfig()

    # =================================================
    # Protocol Save Helpers
    # =================================================

    def _validate_protocol_name(self, name: str) -> bool:
        """プロトコル名の形式を検証し、不正なら警告を表示する"""
        if not re.fullmatch(r"[A-Z0-9]+", name):
            QMessageBox.warning(
                self._view,
                "入力エラー",
                "プロトコル名は英大文字(A-Z)と数字(0-9)のみ使用可能です。",
            )
            return False

        return True

    def _should_overwrite(self, name: str) -> bool:
        """同名のプロトコルが存在するか確認し、存在する場合は上書きするか確認"""
        existing_names = self._fetch_protocol_names()

        if name in existing_names:
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

    def _save_protocol_config(self, name: str) -> None:
        """プロトコル設定を保存"""
        protocol_config = self._view.get_full_config()
        protocol_config.save(f"{name}.toml")

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
            config = self._load_config_from_file(protocol_name)

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

            self._save_protocol_config(current_name)

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
            if not self._validate_protocol_name(new_name):
                # 名前が不正なら再度入力
                current_name = new_name
                continue

            # 上書き確認
            if not self._should_overwrite(new_name):
                current_name = new_name
                continue

            # 保存
            self._save_protocol_config(new_name)

            # リストを更新、新しく名付けたものを選択
            self._refresh_protocol_list()
            self._view.protocol_select_panel.set_current_selected_protocol(new_name)

            # 保存完了ループ脱出
            break

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
