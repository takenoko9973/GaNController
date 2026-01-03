from PySide6.QtCore import QObject


class ITabController(QObject):
    """各タブのコントローラーの基底クラス"""

    def try_switch_from(
        self,
    ) -> bool:
        """別のタブへ移動しようとした時に呼ばれる。

        Returns:
            bool: 退出判定 (Default: True)

        """
        return True
