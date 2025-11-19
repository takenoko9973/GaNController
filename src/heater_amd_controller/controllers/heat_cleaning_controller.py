from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.views.tabs.heat_cleaning_tab import HeatCleaningTab

if TYPE_CHECKING:
    from heater_amd_controller.models.protocol import ProtocolConfig


class HeatCleaningController(QObject):
    status_message_requested = Signal(str, int)  # メッセージシグナル (メッセージ内容, 表示時間ms)

    def __init__(self, view: HeatCleaningTab, manager: ProtocolManager) -> None:
        super().__init__()
        self.view = view
        self.manager = manager

        # 読み込み直後、保存直後のデータ
        self._last_loaded_data: ProtocolConfig | None = None

        # --- シグナル接続 ---
        self.view.protocol_changed.connect(self.on_protocol_selected)
        self.view.save_requested.connect(self.on_save_requested)

        # 初期化処理
        self.initialize_view()

    def initialize_view(self) -> None:
        self.refresh_list()

    def refresh_list(self, select_name: str | None = None) -> None:
        """リストを更新し、指定があればそれを選択する"""
        names = self.manager.get_protocol_names()
        self.view.set_protocol_list(names)

        if select_name and select_name in names:
            target_name = select_name
        elif names:
            target_name = names[0]

        if target_name:
            self.view.select_protocol(target_name)
            self.on_protocol_selected(target_name)  # 更新

    def on_protocol_selected(self, protocol_name: str) -> None:
        """プロトコル変更"""
        print(f"[HC_Ctrl] プロトコル変更: {protocol_name}")

        data = self.manager.get_protocol(protocol_name)
        self._last_loaded_data = data  # 読み込み直後のデータを取得

        self.view.update_ui_from_data(data)

    def on_save_requested(self) -> None:
        """プロトコル保存時"""
        # データ読み込み
        current_data = self.view.get_current_ui_data()
        current_combo_name = self.view.get_current_protocol_name()

        # 「新しいプロトコル...」の場合、名前入力
        if current_combo_name == self.manager.NEW_PROTOCOL_NAME:
            text, ok = QInputDialog.getText(
                self.view, "プロトコル保存", "新しいプロトコル名を入力してください:"
            )
            if ok and text:
                save_name = text.strip()
            else:
                return  # キャンセル

        elif current_combo_name != self.manager.NEW_PROTOCOL_NAME:
            # 既存ファイルは上書き
            save_name = current_combo_name

        # Managerに保存
        if save_name:
            success = self.manager.save_protocol(save_name, current_data)
            if success:
                print(f"[HC_Ctrl] 保存: {save_name}")

                msg = f"保存完了: {save_name} を保存しました。"
                self.status_message_requested.emit(msg, 5000)

                self._last_loaded_data = current_data  # 保存直後のデータに更新

                self.refresh_list(select_name=save_name)
            else:
                self.status_message_requested.emit("エラー: 保存に失敗しました。", 10000)
