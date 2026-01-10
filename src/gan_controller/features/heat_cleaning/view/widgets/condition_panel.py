from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from gan_controller.common.ui.widgets import CheckableSpinBox
from gan_controller.features.heat_cleaning.domain.sequence import SequenceMode


class HCConditionPanel(QGroupBox):
    """シーケンス設定用ウィジェット"""

    sequence_time_spins: dict[str, QDoubleSpinBox]  # シーケンス要素

    sequence_repeat_spin: QDoubleSpinBox  # シーケンス繰り返し回数
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
        layout.setColumnStretch(1, 1)

        layout.addWidget(QLabel("時間 (hour)"), 0, 1)
        for i, section_mode in enumerate(SequenceMode):
            col = 1 + i
            label = QLabel(section_mode.display_name)
            double_spin_box = QDoubleSpinBox(minimum=0, decimals=3, singleStep=0.5)

            layout.addWidget(label, col, 0)
            layout.addWidget(double_spin_box, col, 1)

            self.sequence_time_spins[section_mode.display_name] = double_spin_box

        return layout

    def _create_settings_layout(self) -> QHBoxLayout:
        """その他シーケンス設定"""
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        config_layout1 = QGridLayout()
        self.sequence_repeat_spin = QDoubleSpinBox(value=1, minimum=1, decimals=0)
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
