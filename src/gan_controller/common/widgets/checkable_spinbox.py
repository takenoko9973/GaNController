from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QGridLayout, QWidget


class CheckableSpinBox(QWidget):
    """チェックボックスに連動するSpinBox作成"""

    check_box: QCheckBox
    spin_box: QDoubleSpinBox

    def __init__(
        self,
        label_text: str,
        checked: bool = True,
        value: float = 0.0,
        prefix: str = "",  # 接頭辞
        suffix: str = "",  # 接尾辞
        decimals: int = 2,  # 小数点以下桁数
        minimum: float = 0.00,
        maximum: float = 99.99,
        single_step: float = 1.0,  # 1クリックあたりの変化量
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # 構成要素
        self.check_box = QCheckBox(label_text)
        self.check_box.setChecked(checked)
        self.spin_box = QDoubleSpinBox(
            value=value,
            prefix=prefix,
            suffix=suffix,
            decimals=decimals,
            minimum=minimum,
            maximum=maximum,
            singleStep=single_step,
        )

        # 配置
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check_box, 0, 0)
        layout.addWidget(self.spin_box, 0, 1)
        layout.setColumnStretch(0, 1)  # checkbox column stretch
        layout.setColumnStretch(1, 1)  # spin column stretch

        # チェックボックス操作で起動
        self.check_box.stateChanged.connect(self._update_state)
        self._update_state()

    def _update_state(self) -> None:
        """チェックボックスに連動して、入力欄の見た目を変化"""
        checked = self.check_box.isChecked()
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

        self.spin_box.setPalette(palette)

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        # ブロックシグナルで、無駄なイベント発火防止
        self.check_box.blockSignals(True)
        self.check_box.setChecked(checked)
        self.check_box.blockSignals(False)

        self._update_state()

    def setValue(self, value: float) -> None:  # noqa: N802
        self.spin_box.setValue(value)

    def setSuffix(self, suffix: str) -> None:  # noqa: N802
        self.spin_box.setSuffix(suffix)

    def value(self) -> float:
        return self.spin_box.value()

    def isChecked(self) -> bool:  # noqa: N802
        return self.check_box.isChecked()
