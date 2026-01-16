import tomllib
from pathlib import Path

from PySide6.QtCore import Slot

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
        self._view.protocol_select_panel.set_items(items)

        # デフォルト選択
        self._view.protocol_select_panel.protocol_combo.blockSignals(True)  # 無駄なシグナル停止
        default_selection = items[0] if protocol_names else NEW_PROTOCOL_TEXT
        self._view.protocol_select_panel.set_current_text(default_selection)
        self._view.protocol_select_panel.protocol_combo.blockSignals(False)

        # 初期選択状態の内容をロード
        self._on_protocol_changed(default_selection)

    def _load_config_from_file(self, name: str) -> ProtocolConfig:
        """ファイルから設定を読み込む"""
        file_path = PROTOCOLS_DIR / f"{name}.toml"

        if not file_path.exists():
            # ファイルが見つからない場合はデフォルト値を返すなどのエラー処理
            print(f"Warning: Protocol file not found: {file_path}")
            return ProtocolConfig()

        try:
            with file_path.open("rb") as f:
                data = tomllib.load(f)
            return ProtocolConfig(**data)
        except Exception as e:  # noqa: BLE001
            print(f"Failed to load protocol {name}: {e}")  # 読み込みに失敗したら、初期値を返す
            return ProtocolConfig()

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
