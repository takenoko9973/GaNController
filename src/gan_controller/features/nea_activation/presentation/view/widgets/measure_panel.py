from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from gan_controller.core.models.electricity import ElectricProperties
from gan_controller.core.models.quantity import Current, Pressure, Time, Value
from gan_controller.presentation.components.widgets import ValueLabel


class NEAMeasurePanel(QGroupBox):
    """モニタリング表示用ウィジェット"""

    # === 要素
    status_value_label: QLabel  # 動作状態

    sequence_time_label: ValueLabel  # シーケンスの経過時間
    elapsed_time_label: ValueLabel  # 合計の経過時間

    amd_value_labels: dict[ElectricProperties, ValueLabel]

    pc_value_label: ValueLabel
    qe_value_label: ValueLabel

    ext_pressure_value_label: ValueLabel

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("モニタリング", parent)

        layout = QVBoxLayout(self)

        layout.addLayout(self._create_status_section())  # 状態・時間
        layout.addSpacing(10)
        layout.addLayout(self._create_monitor_section())  # センサー値

    def _create_status_section(self) -> QLayout:
        time_layout = QHBoxLayout()

        # ====== 状態
        self.status_value_label = QLabel()
        self.set_status("待機中", False)
        # フォント
        status_font = QFont()
        status_font.setBold(True)
        self.status_value_label.setFont(status_font)

        # ====== 時間
        self.elapsed_time_label = ValueLabel(Time(0), ".1f")

        time_layout.addWidget(QLabel("状態 :"))
        time_layout.addWidget(self.status_value_label)
        time_layout.addStretch()
        time_layout.addWidget(QLabel("Time :"))
        time_layout.addWidget(self.elapsed_time_label)

        return time_layout

    def _create_monitor_section(self) -> QLayout:
        monitor_layout = QVBoxLayout()

        output_grid = QGridLayout()
        output_grid.setHorizontalSpacing(10)

        # === 環境値
        env_layout = QHBoxLayout()

        self.pc_value_label = ValueLabel(Current(0.0), ".2e")
        self.qe_value_label = ValueLabel(Value(0.0, "%"), ".2e")

        self.ext_pres_val = ValueLabel(Pressure(0.0), ".2e")

        form_layout1 = QFormLayout()
        form_layout1.addRow("Photocurrent :", self.pc_value_label)
        form_layout1.addRow("QE :", self.qe_value_label)

        form_layout2 = QFormLayout()
        form_layout2.addRow("Pressure(EXT) :", self.ext_pres_val)

        # === 電流値 (AMD)
        amd_group = QGroupBox("AMD")
        amd_layout = QGridLayout(amd_group)
        self.amd_value_labels = {}
        for i, electric_prop in enumerate(ElectricProperties):
            header_text = f"{electric_prop.name} ({electric_prop.unit})"
            lbl = QLabel(header_text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 10.5px; color: #555;")

            self.amd_value_labels[electric_prop] = ValueLabel(Value(0.0), ".2f")

            amd_layout.addWidget(lbl, 0, i)
            amd_layout.addWidget(self.amd_value_labels[electric_prop], 1, i)

        # 配置
        env_layout.addLayout(form_layout1)
        env_layout.addStretch()
        env_layout.addLayout(form_layout2)

        monitor_layout.addLayout(env_layout)
        monitor_layout.addWidget(amd_group)

        return monitor_layout

    # =============================================================================

    def set_status(self, status: str, is_running: bool) -> None:
        """ステータス表示を変更"""
        self.status_value_label.setText(status)

        pal = self.status_value_label.palette()
        if is_running:
            pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.green)
        else:
            pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.gray)

        self.status_value_label.setPalette(pal)
