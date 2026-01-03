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

        self._on_load_requested()

    def _attach_view(self) -> None:
        self._view.load_requested.connect(self._on_load_requested)
        self._view.save_requested.connect(self._on_save_requested)

    def get_config(self) -> AppConfig:
        return self._config.model_copy(deep=True)

    def is_modified(self) -> bool:
        """UIの内容が、最後にロード/保存した内容と異なっているか判定"""
        try:
            current_config = self._view.create_config_from_ui()
        except Exception:  # noqa: BLE001
            # 入力値エラーなどでConfig生成できない場合は「変更あり」とみなす
            return True
        else:
            return current_config != self._config  # 比較して変更があるか判定

    def try_switch_from(
        self,
    ) -> bool:
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
            # 保存して移動
            try:
                self._on_save_requested()
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self._view, "保存エラー", f"保存に失敗しました:\n{e}")
                return False  # 保存失敗時は移動しない
            else:
                return True

        elif ret == QMessageBox.StandardButton.Discard:
            # 変更を破棄して移動
            self._on_load_requested()
            return True

        else:
            # キャンセル (移動しない)
            return False

    @Slot()
    def _on_load_requested(self) -> None:
        """設定読み込み"""
        self._config = AppConfig.load()
        self._view.set_config(self._config)

        messenger = GlobalMessenger()
        messenger.show_status("設定を読み込みました", 5000)

    @Slot()
    def _on_save_requested(self) -> None:
        """設定を保存する"""
        config = self._view.create_config_from_ui()
        config.save()
        self._config = config

        messenger = GlobalMessenger()
        messenger.show_status("設定を保存しました", 5000)
