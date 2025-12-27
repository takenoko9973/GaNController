from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget


class ProtocolSelectorPanel(QHBoxLayout):
    protocol_combo: QComboBox
    save_button: QPushButton

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.protocol_combo = QComboBox()
        self.save_button = QPushButton("保存")

        self.addWidget(QLabel("プロトコル"))
        self.addWidget(self.protocol_combo)
        self.addStretch()
        self.addWidget(self.save_button)

    def add_item(self, text: str) -> None:
        self.protocol_combo.addItem(text)

    def add_items(self, texts: list[str]) -> None:
        self.protocol_combo.addItems(texts)
