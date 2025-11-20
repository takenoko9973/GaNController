from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class ValueLabel(QLabel):
    """数値や時間を表示するための枠付きラベル (統一スタイル)"""

    def __init__(
        self,
        value: str | float = "0.00",
        suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._suffix = suffix

        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            padding: 2px 4px;
            font-family: Monospace;
        """)

        self.set_value(value)

    def set_value(self, value: str | float) -> None:
        self.setText(f"{value}{self._suffix}")
