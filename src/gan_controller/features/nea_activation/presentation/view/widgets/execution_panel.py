from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gan_controller.common.domain.quantity.factory import Current, Power
from gan_controller.common.ui.widgets import CheckableSpinBox
from gan_controller.features.nea_activation.schemas import NEAControlConfig


class NEAExecutionPanel(QGroupBox):
    """実行制御ウィジェット"""

    # === 要素
    amd_output_current_spin: CheckableSpinBox
    laser_sv_spin: QDoubleSpinBox
    laser_pv_spin: QDoubleSpinBox

    start_button: QPushButton
    stop_button: QPushButton
    apply_button: QPushButton

    # === シグナル
    start_requested = Signal()
    stop_requested = Signal()
    apply_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("実行制御", parent)

        layout = QVBoxLayout(self)
        layout.addWidget(self._create_control_section())
        layout.addLayout(self._create_execution_section())  # 制御

        self._connect_signal()

    def _create_control_section(self) -> QGroupBox:
        control_group = QGroupBox()
        control_layout = QVBoxLayout(control_group)

        # ====== 設定値入力
        value_set_layout = QHBoxLayout()

        # === AMD
        amd_control_layout = QVBoxLayout()
        amd_control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.amd_output_current_spin = CheckableSpinBox(
            "AMD出力 :", checked=False, value=3.5, suffix=" A", maximum=10, single_step=0.1
        )
        amd_control_layout.addWidget(self.amd_output_current_spin)

        # === Laser
        laser_layout = QGridLayout()
        laser_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.laser_sv_spin = QDoubleSpinBox(value=10, suffix=" mW", decimals=1, maximum=120)
        self.laser_pv_spin = QDoubleSpinBox(value=3.01, suffix=" mW", decimals=2, maximum=120)
        laser_layout.addWidget(QLabel("レーザー出力 :"), 0, 0)
        laser_layout.addWidget(self.laser_sv_spin, 0, 1)
        laser_layout.addWidget(QLabel("レーザー実出力 :"), 1, 0)
        laser_layout.addWidget(self.laser_pv_spin, 1, 1)

        value_set_layout.addLayout(amd_control_layout, stretch=1)
        value_set_layout.addSpacing(10)
        value_set_layout.addLayout(laser_layout, stretch=1)

        # ====== 適応
        self.apply_button = QPushButton("Apply")

        control_layout.addLayout(value_set_layout)
        control_layout.addWidget(self.apply_button)

        return control_group

    def _create_execution_section(self) -> QLayout:
        execution_layout = QHBoxLayout()

        self.start_button = QPushButton("開始")
        self.stop_button = QPushButton("停止")

        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)

        # 初期状態: 停止中なので「停止」ボタンは無効化
        self.stop_button.setEnabled(False)

        execution_layout.addWidget(self.start_button)
        execution_layout.addWidget(self.stop_button)

        return execution_layout

    def _connect_signal(self) -> None:
        self.start_button.clicked.connect(self.start_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.apply_button.clicked.connect(self.apply_requested)

    # =============================================================================

    def get_config(self) -> NEAControlConfig:
        return NEAControlConfig(
            amd_enable=self.amd_output_current_spin.isChecked(),
            amd_output_current=Current(self.amd_output_current_spin.value()),
            laser_power_sv=Power(self.laser_sv_spin.value(), "m"),
            laser_power_pv=Power(self.laser_pv_spin.value(), "m"),
        )

    def set_config(self, config: NEAControlConfig) -> None:
        self.amd_output_current_spin.setChecked(config.amd_enable)
        self.amd_output_current_spin.setValue(config.amd_output_current.base_value)
        self.laser_sv_spin.setValue(config.laser_power_sv.value_as("m"))
        self.laser_pv_spin.setValue(config.laser_power_pv.value_as("m"))
