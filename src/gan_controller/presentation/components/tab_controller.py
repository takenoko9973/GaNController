from PySide6.QtCore import QObject, Signal


class ITabController(QObject):
    """各タブのコントローラーの基底クラス"""

    status_message_requested = Signal(str, int)
    tab_lock_requested = Signal(bool)

    def try_switch_from(
        self,
    ) -> bool:
        """
        別のタブへ移動しようとした時に呼ばれる。

        Returns:
            bool: 退出判定 (Default: True)

        """
        return True

    def on_close(self) -> None:
        """アプリケーション終了時に呼ばれる。設定の保存やリソースの解放を行う。"""
