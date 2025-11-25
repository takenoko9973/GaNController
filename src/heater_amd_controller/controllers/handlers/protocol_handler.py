from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget

from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.models.protocol_config import ProtocolConfig


class ProtocolHandler(QObject):
    """プロトコルの読み書き、保存確認ダイアログなどのロジックを担当"""

    status_message = Signal(str, int)  # 保存完了やエラー時
    data_loaded = Signal(ProtocolConfig)  # データ読み込み完了時
    list_update_requested = Signal(str)  # リスト更新 (str: プロトコル選択)

    def __init__(self, view_widget: QWidget, manager: ProtocolManager) -> None:
        super().__init__()
        self.view_widget = view_widget  # ダイアログの親にするWidget
        self.manager = manager

        self._last_loaded_config: ProtocolConfig | None = None

    def load_protocol(self, name: str) -> None:
        """プロトコルをロード"""
        print(f"[ProtocolHandler] Load: {name}")
        data = self.manager.get_protocol(name)
        self._last_loaded_config = data
        self.data_loaded.emit(data)

    # ==================================================
    # 公開メソッド
    # ==================================================

    def save_overwrite(self, current_name: str, protocol_config: ProtocolConfig) -> None:
        """プロトコルの保存 (is_save_as=True なら強制名前を付けて保存)"""
        # 保存名決定
        save_name = self._determine_save_name(current_name)
        if not save_name:
            return

        # 上書き確認
        if not self._confirm_overwrite(save_name, protocol_config):
            return

        # 保存実行
        self._perform_save(save_name, protocol_config)

    def save_as(self, current_name: str, protocol_config: ProtocolConfig) -> None:
        """名前を付けて保存フロー (Ctrl+Shift+S)"""
        # 保存名決定
        default_text = current_name if current_name != self.manager.NEW_PROTOCOL_NAME else ""
        save_name = self._ask_save_name(default_text=default_text)
        if not save_name:
            return

        # 保存実行
        if self._confirm_overwrite(save_name, protocol_config):  # 重複チェック
            self._perform_save(save_name, protocol_config)

    # ==================================================
    # 内部フロー & チェックメソッド
    # ==================================================
    def _save_as_flow(self, default_text: str, protocol_config: ProtocolConfig) -> None:
        # 保存名決定
        save_name = self._ask_save_name(default_text=default_text)
        if not save_name:
            return

        # 保存実行
        if self._confirm_overwrite(save_name, protocol_config):  # 重複チェック
            self._perform_save(save_name, protocol_config)

    def _determine_save_name(self, current_name: str) -> str | None:
        if current_name == self.manager.NEW_PROTOCOL_NAME:
            return self._ask_save_name()

        return current_name

    def _ask_save_name(self, default_text: str = "") -> str | None:
        """名前入力ダイアログを表示"""
        text, ok = QInputDialog.getText(
            self.view_widget,
            "プロトコル新規保存",
            "プロトコル名を入力してください:",
            text=default_text,
        )
        return text.strip() if ok and text else None

    def _confirm_overwrite(self, name: str, new_config: ProtocolConfig) -> bool:
        # 新規作成時は上書き確認しない
        if name == self.manager.NEW_PROTOCOL_NAME or name not in self.manager.get_protocol_names():
            return True

        # 差分チェック
        if self._last_loaded_config and new_config != self._last_loaded_config:
            reply = QMessageBox.question(
                self.view_widget,
                "変更確認",
                f"'{name}' に変更があります。\n上書きしますか？",  # noqa: RUF001
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False

        return True

    def _perform_save(self, name: str, save_protocol_config: ProtocolConfig) -> None:
        """実際に保存を実行し、結果を通知する"""
        success = self.manager.save_protocol(name, save_protocol_config)
        if success:
            self._last_loaded_config = save_protocol_config
            self.status_message.emit(f"保存完了: {name}", 5000)
            self.list_update_requested.emit(name)
        else:
            self.status_message.emit("エラー: 保存失敗", 10000)
