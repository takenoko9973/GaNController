from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QGridLayout, QLabel, QStyle, QWidget


class CheckableSpinBox(QWidget):
    """チェックボックスに連動するSpinBox作成"""

    def __init__(
        self,
        label_text: str,
        checked: bool = True,
        suffix: str = "",
        decimals: int | None = None,
        minimum: float | None = None,
        value: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # 構成要素
        self.checkbox = QCheckBox()
        self.label = QLabel(label_text)
        self.spinbox = QDoubleSpinBox(
            suffix=suffix, decimals=decimals, minimum=minimum, value=value
        )

        # チェックボックスの削れ防止
        indicator_w = self.checkbox.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        indicator_h = self.checkbox.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorHeight)
        self.checkbox.setMinimumWidth(indicator_w + 4)
        self.checkbox.setMinimumHeight(indicator_h + 4)

        self.checkbox.setChecked(checked)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.checkbox, 0, 0)
        layout.addWidget(self.label, 0, 1)
        layout.addWidget(self.spinbox, 0, 2)

        # 列幅を適切に調整したい場合は以下を利用
        layout.setColumnStretch(1, 1)  # label column stretch
        layout.setColumnStretch(2, 1)  # spin column stretch

        self.setLayout(layout)

        self.checkbox.stateChanged.connect(self._update_state)
        self._update_state()

    # 内部ロジック完全カプセル化
    def _update_state(self) -> None:
        checked = self.checkbox.isChecked()
        palette = self.palette()

        group = QPalette.ColorGroup.Normal if checked else QPalette.ColorGroup.Disabled
        palette.setColor(
            QPalette.ColorGroup.Normal,
            QPalette.ColorRole.Base,
            palette.color(group, QPalette.ColorRole.Base),
        )
        palette.setColor(
            QPalette.ColorGroup.Normal,
            QPalette.ColorRole.Text,
            palette.color(group, QPalette.ColorRole.Text),
        )

        self.spinbox.setPalette(palette)

    def set_data(self, checked: bool, value: float) -> None:
        """外部からデータをセット"""
        # ブロックシグナルで、無駄なイベント発火防止
        self.checkbox.blockSignals(True)  # noqa: FBT003

        self.checkbox.setChecked(checked)
        self.spinbox.setValue(value)
        self._update_state()

        self.checkbox.blockSignals(False)  # noqa: FBT003

    def value(self) -> float:
        return self.spinbox.value()

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()
