from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget

from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.models.protocol import ProtocolConfig


class ProtocolHandler(QObject):
    """プロトコルの読み書き、保存確認ダイアログなどのロジックを担当"""

    status_message = Signal(str, int)  # 保存完了やエラー時
    data_loaded = Signal(ProtocolConfig)  # データ読み込み完了時
    list_update_requested = Signal(str)  # リスト更新 (str: プロトコル選択)

    def __init__(self, view_widget: QWidget, manager: ProtocolManager) -> None:
        super().__init__()
        self.view_widget = view_widget  # ダイアログの親にするWidget
        self.manager = manager

        self._last_loaded_data: ProtocolConfig | None = None

    def load_protocol(self, name: str) -> None:
        """プロトコルをロード"""
        print(f"[ProtocolHandler] Load: {name}")
        data = self.manager.get_protocol(name)
        self._last_loaded_data = data
        self.data_loaded.emit(data)

    def save_protocol_flow(self, current_name: str, current_data: ProtocolConfig) -> None:
        """プロトコルの保存"""
        save_name = self._determine_save_name(current_name)
        if not save_name:
            return

        # 上書き確認
        if not self._confirm_overwrite(save_name, current_data):
            return

        # 保存実行
        success = self.manager.save_protocol(save_name, current_data)
        if success:
            self._last_loaded_data = current_data
            self.status_message.emit(f"保存完了: {save_name}", 5000)
            self.list_update_requested.emit(save_name)
        else:
            self.status_message.emit("エラー: 保存失敗", 10000)

    def _determine_save_name(self, current_name: str) -> str | None:
        if current_name == self.manager.NEW_PROTOCOL_NAME:
            text, ok = QInputDialog.getText(
                self.view_widget, "プロトコル保存", "新しいプロトコル名を入力:"
            )
            return text.strip() if ok and text else None
        return current_name

    def _confirm_overwrite(self, name: str, new_data: ProtocolConfig) -> bool:
        # 新規作成時は上書き確認しない
        if name == self.manager.NEW_PROTOCOL_NAME or name not in self.manager.get_protocol_names():
            return True

        # 差分チェック
        if self._last_loaded_data and new_data != self._last_loaded_data:
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
