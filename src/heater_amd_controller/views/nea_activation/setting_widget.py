from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.models.nea_config import NEAConfig
from heater_amd_controller.views.widgets.checkable_spinbox import CheckableSpinBox  # 便宜上使用


class NEASettingsGroup(QGroupBox):
    """NEA活性化パラメータ設定"""

    apply_laser_requested = Signal(float)  # レーザー設定適用シグナル

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("パラメータ設定", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QGridLayout(self)

        # === レーザー出力設定 ===
        layout.addWidget(QLabel("Laser Setpoint:"), 0, 0)
        self.spin_laser_set = QDoubleSpinBox()
        self.spin_laser_set.setRange(0, 1000)  # 適切に調整
        self.spin_laser_set.setDecimals(2)
        self.spin_laser_set.setSuffix(" (Cmd)")
        layout.addWidget(self.spin_laser_set, 0, 1)

        self.btn_apply_laser = QPushButton("Apply")
        self.btn_apply_laser.clicked.connect(self._on_apply_laser)
        layout.addWidget(self.btn_apply_laser, 0, 2)

        # === 計算用パラメータ ===
        layout.addWidget(QLabel("Laser Energy (Calc):"), 1, 0)
        self.spin_laser_energy = QDoubleSpinBox()
        self.spin_laser_energy.setRange(0, 1)
        self.spin_laser_energy.setDecimals(6)  # 微小値対応
        self.spin_laser_energy.setSingleStep(1e-6)
        self.spin_laser_energy.setSuffix(" W")
        self.spin_laser_energy.setValue(164e-6)  # デフォルト
        layout.addWidget(self.spin_laser_energy, 1, 1)

        layout.addWidget(QLabel("Resistance:"), 2, 0)
        self.spin_resistance = QDoubleSpinBox()
        self.spin_resistance.setRange(1, 1e9)
        self.spin_resistance.setSuffix(" Ω")
        self.spin_resistance.setValue(1e6)  # デフォルト
        layout.addWidget(self.spin_resistance, 2, 1)

        layout.addWidget(QLabel("HV:"), 3, 0)
        self.spin_hv = QDoubleSpinBox()
        self.spin_hv.setRange(0, 1000)
        self.spin_hv.setValue(100)
        self.spin_hv.setSuffix(" V")
        layout.addWidget(self.spin_hv, 3, 1)

    @Slot()
    def _on_apply_laser(self) -> None:
        val = self.spin_laser_set.value()
        self.apply_laser_requested.emit(val)

    def get_config_subset(self) -> dict:
        """Config生成用データを返す"""
        return {
            "laser_setpoint": self.spin_laser_set.value(),
            "laser_power_energy": self.spin_laser_energy.value(),
            "resistance": self.spin_resistance.value(),
            "hv_value": self.spin_hv.value(),
        }
