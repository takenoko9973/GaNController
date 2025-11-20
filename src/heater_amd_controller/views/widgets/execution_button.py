from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QWidget


class ExecutionControlButton(QPushButton):
    """開始・停止切り替えボタン"""

    toggled_state = Signal(bool)  # 開始・停止シグナル (True=開始、False=停止)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("開始", parent)
        self.setCheckable(True)  # トグルボタン
        self.setMinimumHeight(50)  # 大きめ

        # フォント設定
        font = self.font()
        font.setBold(True)
        font.setPointSize(12)
        self.setFont(font)

        self._update_style(False)  # noqa: FBT003

        self.clicked.connect(self._on_clicked)  # クリック時イベント

    def _on_clicked(self) -> None:
        is_running = self.isChecked()
        self.setText("停止" if is_running else "開始")
        self._update_style(is_running)

        self.toggled_state.emit(is_running)  # シグナル

    def _update_style(self, is_running: bool) -> None:
        if is_running:
            # 停止ボタン (赤系)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ffcccc;
                    color: #cc0000;
                    border: 1px solid #cc0000;
                    border-radius: 5px;
                }
                QPushButton:hover { background-color: #ff9999; }
                QPushButton:pressed { background-color: #e57373; }
            """)
        else:
            # 開始ボタン (青/緑系)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ccffcc;
                    color: #006600;
                    border: 1px solid #006600;
                    border-radius: 5px;
                }
                QPushButton:hover { background-color: #99ff99; }
                QPushButton:pressed { background-color: #81c784; }
            """)

    def force_stop(self) -> None:
        """外部から強制的に停止"""
        self.blockSignals(True)  # noqa: FBT003

        self.setChecked(False)
        self.setText("開始")
        self._update_style(False)  # noqa: FBT003

        self.blockSignals(False)  # noqa: FBT003
