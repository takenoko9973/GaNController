from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox

from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.common.services.global_messenger import GlobalMessenger
from gan_controller.features.setting.model.app_config import AppConfig
from gan_controller.features.setting.view.tab_widget import SettingsTab


class SettingsController(ITabController):
    _view: SettingsTab
    _config: AppConfig

    def __init__(self, view: SettingsTab) -> None:
        super().__init__()

        self._view = view
        self._attach_view()

        # 初期ロード (通知なしで実行)
        self.load_config(show_notify=False)

    def _attach_view(self) -> None:
        self._view.load_requested.connect(self._on_load_clicked)
        self._view.save_requested.connect(self._on_save_clicked)

    def on_close(self) -> None:
        self.save_config(show_notify=False)

    # ==========================================================
    # ビジネスロジック
    # ==========================================================

    def load_config(self, show_notify: bool = True) -> bool:
        """設定をファイルから読み込んでViewに反映する。

        Args:
            show_notify: 完了時にステータス通知を出すかどうか
        Returns:
            bool: 成功したらTrue

        """
        try:
            # ロジック: 読み込み & 状態更新
            self._config = AppConfig.load()
            self._view.set_config(self._config)

        except Exception as e:  # noqa: BLE001
            # AppConfig.load がエラーを握りつぶさず raise するように変更した場合に備える
            QMessageBox.critical(
                self._view, "読み込みエラー", f"設定の読み込みに失敗しました:\n{e}"
            )
            return False

        else:
            if show_notify:
                GlobalMessenger().show_status("設定を読み込みました")

            return True

    def save_config(self, show_notify: bool = True) -> bool:
        """現在のViewの内容をファイルに保存する。

        Returns:
            bool: 保存に成功したらTrue

        """
        try:
            # ロジック: Viewからデータ取得 -> 保存 -> 状態更新
            new_config = self._view.create_config_from_ui()
            new_config.save()

        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self._view, "保存エラー", f"保存に失敗しました:\n{e}")
            return False

        else:
            self._config = new_config
            if show_notify:
                GlobalMessenger().show_status("設定を保存しました")

            return True

    # ==========================================================
    # インターフェース / ヘルパー
    # ==========================================================

    def get_config(self) -> AppConfig:
        """現在の設定(保存済み)のコピーを返す"""
        if self._config is None:
            return AppConfig()

        return self._config.model_copy(deep=True)

    def is_modified(self) -> bool:
        """UIの内容が、最後にロード/保存した内容と異なっているか判定"""
        if self._config is None:
            return False

        try:
            current_config = self._view.create_config_from_ui()
        except Exception:  # noqa: BLE001
            # 入力値エラーなどでConfig生成できない場合は「変更あり」とみなす
            return True
        else:
            return current_config != self._config  # 比較して変更があるか判定

    def try_switch_from(self) -> bool:
        """タブ移動時のチェック処理"""
        if not self.is_modified():
            return True  # 変更なしなら即移動

        title = "設定の保存"
        msg = "設定が変更されています。\n保存して切り替えますか？"  # noqa: RUF001
        buttons = (
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )

        # Viewを親にしてダイアログ表示
        ret = QMessageBox.question(self._view, title, msg, buttons, QMessageBox.StandardButton.Save)

        if ret == QMessageBox.StandardButton.Save:
            return self.save_config(show_notify=True)  # 保存できたらタブ移動

        if ret == QMessageBox.StandardButton.Discard:
            # 変更を破棄して移動
            self.load_config(show_notify=False)
            return True

        # キャンセル (移動しない)
        return False

    # ==========================================================
    # イベントハンドラ
    # ==========================================================

    @Slot()
    def _on_load_clicked(self) -> None:
        """読み込みボタン押下時"""
        self.load_config(show_notify=True)

    @Slot()
    def _on_save_clicked(self) -> None:
        """保存ボタン押下時"""
        self.save_config(show_notify=True)
