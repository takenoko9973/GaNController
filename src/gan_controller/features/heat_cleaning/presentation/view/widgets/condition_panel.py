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

from gan_controller.common.domain.quantity.factory import Current, Time, Value
from gan_controller.common.ui.widgets import CheckableSpinBox
from gan_controller.features.heat_cleaning.domain.config import HCConditionConfig, HCSequenceConfig
from gan_controller.features.heat_cleaning.domain.models import SequenceMode


class HCConditionPanel(QGroupBox):
    """シーケンス設定用ウィジェット"""

    sequence_time_spins: dict[SequenceMode, QDoubleSpinBox]  # シーケンス要素

    sequence_repeat_spin: QSpinBox  # シーケンス繰り返し回数
    logging_interval_spin: QDoubleSpinBox  # ログ間隔

    hc_checked_spin: CheckableSpinBox  # HC 電流値
    amd_checked_spin: CheckableSpinBox  # AMD 電流値

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Protocol Sequences", parent)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        sequence_layout = self._create_sequences_layout()
        setting_layout = self._create_settings_layout()

        main_layout.addLayout(sequence_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(setting_layout)

    def _create_sequences_layout(self) -> QGridLayout:
        """シーケンス時間設定"""
        self.sequence_time_spins = {}

        # 2列
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(QLabel("時間 (hour)"), 1, 0)
        for i, section_mode in enumerate(SequenceMode):
            col = 1 + i
            label = QLabel(section_mode.display_name)
            label.setStyleSheet("font-size: 10.5px;")
            double_spin_box = QDoubleSpinBox(minimum=0, decimals=2, singleStep=0.5)

            layout.addWidget(label, 0, col)
            layout.addWidget(double_spin_box, 1, col)

            self.sequence_time_spins[section_mode] = double_spin_box

        return layout

    def _create_settings_layout(self) -> QHBoxLayout:
        """その他シーケンス設定"""
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_layout1 = QGridLayout()
        self.sequence_repeat_spin = QSpinBox(value=1, minimum=1)
        self.logging_interval_spin = QDoubleSpinBox(value=10, minimum=1, decimals=0, suffix=" s")
        config_layout1.addWidget(QLabel("繰り返し回数"), 0, 0)
        config_layout1.addWidget(self.sequence_repeat_spin, 0, 1)
        config_layout1.addWidget(QLabel("ログ間隔"), 1, 0)
        config_layout1.addWidget(self.logging_interval_spin, 1, 1)

        config_layout2 = QGridLayout()
        self.hc_checked_spin = CheckableSpinBox("HC 電流", minimum=0, decimals=1, suffix=" A")
        self.amd_checked_spin = CheckableSpinBox("AMD 電流", minimum=0, decimals=1, suffix=" A")
        config_layout2.addWidget(self.hc_checked_spin, 0, 0, 1, 2)
        config_layout2.addWidget(self.amd_checked_spin, 1, 0, 1, 2)

        setting_layout.addLayout(config_layout1)
        setting_layout.addSpacing(20)
        setting_layout.addLayout(config_layout2)

        return setting_layout

    # =============================================================================

    def get_config(self) -> tuple[HCSequenceConfig, HCConditionConfig]:
        sequence_config = HCSequenceConfig(
            rising_time=Time(self.sequence_time_spins[SequenceMode.RISING].value(), "hour"),
            heating_time=Time(self.sequence_time_spins[SequenceMode.HEAT_CLEANING].value(), "hour"),
            decrease_time=Time(self.sequence_time_spins[SequenceMode.DECREASE].value(), "hour"),
            wait_time=Time(self.sequence_time_spins[SequenceMode.WAIT].value(), "hour"),
        )
        condition_config = HCConditionConfig(
            repeat_count=Value(self.sequence_repeat_spin.value()),
            logging_interval=Time(self.logging_interval_spin.value()),
            # ===
            hc_enabled=self.hc_checked_spin.isChecked(),
            hc_current=Current(self.hc_checked_spin.value()),
            # ===
            amd_enabled=self.amd_checked_spin.isChecked(),
            amd_current=Current(self.amd_checked_spin.value()),
        )
        return sequence_config, condition_config

    def set_config(
        self, sequence_config: HCSequenceConfig, condition_config: HCConditionConfig
    ) -> None:
        # === Sequence
        self.sequence_time_spins[SequenceMode.RISING].setValue(
            sequence_config.rising_time.value_as("hour")
        )
        self.sequence_time_spins[SequenceMode.HEAT_CLEANING].setValue(
            sequence_config.heating_time.value_as("hour")
        )
        self.sequence_time_spins[SequenceMode.DECREASE].setValue(
            sequence_config.decrease_time.value_as("hour")
        )
        self.sequence_time_spins[SequenceMode.WAIT].setValue(
            sequence_config.wait_time.value_as("hour")
        )

        # === Condition
        self.sequence_repeat_spin.setValue(int(condition_config.repeat_count.base_value))
        self.logging_interval_spin.setValue(condition_config.logging_interval.base_value)
        # HC
        self.hc_checked_spin.setChecked(condition_config.hc_enabled)
        self.hc_checked_spin.setValue(condition_config.hc_current.base_value)
        # AMD
        self.amd_checked_spin.setChecked(condition_config.amd_enabled)
        self.amd_checked_spin.setValue(condition_config.amd_current.base_value)
