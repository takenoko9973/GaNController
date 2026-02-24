from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget


class HCProtocolSelectorPanel(QWidget):
    # === 要素
    protocol_combo: QComboBox
    save_button: QPushButton

    # === シグナル
    protocol_changed = Signal(str)
    protocol_saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        self.protocol_combo = QComboBox()
        self.save_button = QPushButton("保存")

        main_layout.addWidget(QLabel("プロトコル"))
        main_layout.addWidget(self.protocol_combo)
        main_layout.addStretch()
        main_layout.addWidget(self.save_button)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.protocol_combo.currentTextChanged.connect(self.protocol_changed.emit)
        self.save_button.clicked.connect(self.protocol_saved.emit)

    def set_protocol_items(self, texts: list[str]) -> None:
        """プルダウンの項目をリセットして設定する"""
        self.protocol_combo.blockSignals(True)  # 無駄なシグナルを出さないように
        self.protocol_combo.clear()
        self.protocol_combo.addItems(texts)
        self.protocol_combo.blockSignals(False)

    def current_selected_protocol(self) -> str:
        """現在選択されているテキストを取得"""
        return self.protocol_combo.currentText()

    def set_current_selected_protocol(self, text: str) -> None:
        """テキストを指定して選択を変更"""
        self.protocol_combo.setCurrentText(text)
