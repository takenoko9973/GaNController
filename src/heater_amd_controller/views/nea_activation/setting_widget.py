from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QWidget,
)


class NEASettingsGroup(QGroupBox):
    """NEA活性化パラメータ設定"""

    apply_laser_requested = Signal(float, float)  # レーザー設定適用シグナル

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("パラメータ設定", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QGridLayout(self)

        # === レーザー出力設定 ===
        layout.addWidget(QLabel("レーザー設定出力:"), 0, 0)
        self.spin_laser_sv = QDoubleSpinBox(value=10)
        self.spin_laser_sv.setRange(0, 120)
        self.spin_laser_sv.setDecimals(1)
        self.spin_laser_sv.setSuffix(" mW")
        layout.addWidget(self.spin_laser_sv, 0, 1)

        layout.addWidget(QLabel("レーザー実出力:"), 1, 0)
        self.spin_laser_output = QDoubleSpinBox(value=3.01)
        self.spin_laser_output.setRange(0, 120)
        self.spin_laser_output.setDecimals(2)
        self.spin_laser_output.setSuffix(" mW")
        layout.addWidget(self.spin_laser_output, 1, 1)

        self.btn_apply_laser = QPushButton("Apply")
        self.btn_apply_laser.clicked.connect(self._on_apply_laser)
        layout.addWidget(self.btn_apply_laser, 1, 2)

        # 換算抵抗 (シャント抵抗)
        layout.addWidget(QLabel("換算抵抗:"), 2, 0)
        self.spin_shunt_r = QDoubleSpinBox(value=10)
        self.spin_shunt_r.setRange(1, 100)
        self.spin_shunt_r.setSuffix(" kΩ")
        layout.addWidget(self.spin_shunt_r, 2, 1)

    @Slot()
    def _on_apply_laser(self) -> None:
        laser_sv = self.spin_laser_sv.value()
        laser_output = self.spin_laser_output.value()
        self.apply_laser_requested.emit(laser_sv, laser_output)

    def get_config_subset(self) -> dict:
        """Config生成用データを返す"""
        return {
            "laser_sv": self.spin_laser_sv.value(),
            "laser_output": self.spin_laser_output.value(),
            "shunt_r": self.spin_shunt_r.value(),
        }
