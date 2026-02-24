from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget


class LabeledItem(QWidget):
    """文字列と任意のウィジェットを横並び"""

    def __init__(
        self,
        label_text: str,
        item_widget: QWidget,
        label_width: int | None = None,
        label_align: Qt.AlignmentFlag | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.label = QLabel(label_text)
        if label_width:
            self.label.setFixedWidth(label_width)
        if label_align:
            self.label.setAlignment(label_align)

        self.item_widget = item_widget

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.item_widget, 0, 1)

    @property
    def label_widget(self) -> QLabel:
        return self.label

    @property
    def widget(self) -> QWidget:
        return self.item_widget
