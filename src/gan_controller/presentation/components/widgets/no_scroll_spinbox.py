from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QWidget


class NoScrollSpinBox(QSpinBox):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        suffix: str | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            suffix=suffix,
            minimum=minimum,
            maximum=maximum,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        suffix: str | None = None,
        decimals: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            suffix=suffix,
            decimals=decimals,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        event.ignore()
