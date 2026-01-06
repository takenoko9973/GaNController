from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gan_controller.common.types.quantity.factory import Length, Resistance, Time, Value
from gan_controller.features.nea_activation.schemas import NEAConditionConfig


class NEAConditionSettingsPanel(QGroupBox):
    """実験条件ウィジェット"""

    # === 要素
    shunt_r_spin: QDoubleSpinBox
    laser_wavelength_spin: QDoubleSpinBox

    stabilization_time_spin: QDoubleSpinBox
    integrated_interval_spin: QDoubleSpinBox
    integrated_count_spin: QSpinBox

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Condition Settings", parent)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        setting_layout = self._create_settings_layout()

        main_layout.addLayout(setting_layout)

    def _create_settings_layout(self) -> QHBoxLayout:
        """その他シーケンス設定"""
        setting_layout = QHBoxLayout()

        # ====================

        config_layout1 = QGridLayout()
        config_layout1.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.shunt_r_spin = QDoubleSpinBox(
            value=10, minimum=1, maximum=10000, decimals=0, suffix=" kΩ"
        )
        self.laser_wavelength_spin = QDoubleSpinBox(
            value=406, minimum=1, maximum=2000, decimals=0, suffix=" nm"
        )
        config_layout1.addWidget(QLabel("換算抵抗 :"), 0, 0)
        config_layout1.addWidget(self.shunt_r_spin, 0, 1)
        config_layout1.addWidget(QLabel("レーザー波長 :"), 2, 0)
        config_layout1.addWidget(self.laser_wavelength_spin, 2, 1)

        # ====================

        config_layout2 = QGridLayout()
        config_layout2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stabilization_time_spin = QDoubleSpinBox(
            value=1, minimum=0, maximum=10, decimals=1, singleStep=0.1, suffix=" s"
        )
        self.integrated_interval_spin = QDoubleSpinBox(
            value=0.1, minimum=0.1, maximum=10, decimals=1, singleStep=0.1, suffix=" s"
        )
        self.integrated_count_spin = QSpinBox(value=1, minimum=1, maximum=1000)
        config_layout2.addWidget(QLabel("安定化時間 :"), 0, 0)
        config_layout2.addWidget(self.stabilization_time_spin, 0, 1)
        config_layout2.addWidget(QLabel("積算間隔 :"), 1, 0)
        config_layout2.addWidget(self.integrated_interval_spin, 1, 1)
        config_layout2.addWidget(QLabel("積算回数 :"), 2, 0)
        config_layout2.addWidget(self.integrated_count_spin, 2, 1)

        # ====================

        setting_layout.addLayout(config_layout1, stretch=1)
        setting_layout.addSpacing(20)
        setting_layout.addLayout(config_layout2, stretch=1)

        return setting_layout

    # =============================================================================

    def get_config(self) -> NEAConditionConfig:
        return NEAConditionConfig(
            shunt_resistance=Resistance(self.shunt_r_spin.value(), "k"),
            laser_wavelength=Length(self.laser_wavelength_spin.value(), "n"),
            stabilization_time=Time(self.stabilization_time_spin.value()),
            integration_count=Value(self.integrated_count_spin.value()),
            integration_interval=Time(self.integrated_interval_spin.value()),
        )

    def set_config(self, config: NEAConditionConfig) -> None:
        self.shunt_r_spin.setValue(config.shunt_resistance.value_as("k"))
        self.laser_wavelength_spin.setValue(config.laser_wavelength.value_as("n"))
        self.stabilization_time_spin.setValue(config.stabilization_time.si_value)
        self.integrated_count_spin.setValue(int(config.integration_count.si_value))
        self.integrated_interval_spin.setValue(config.integration_interval.si_value)
