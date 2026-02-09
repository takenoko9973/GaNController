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

from gan_controller.common.domain.electricity import ElectricProperties
from gan_controller.common.domain.quantity import Pressure, Temperature
from gan_controller.common.ui.widgets import ValueLabel
from gan_controller.features.heat_cleaning.domain.models import HCExperimentResult


class HCMeasurePanel(QGroupBox):
    """実行制御およびモニタリング表示用ウィジェット"""

    # === 要素
    status_value_label: QLabel  # 動作状態

    step_time_label: ValueLabel  # シーケンスの経過時間
    total_time_label: ValueLabel  # 合計の経過時間

    hc_value_labels: dict[ElectricProperties, ValueLabel]
    amd_value_labels: dict[ElectricProperties, ValueLabel]

    temp_value_label: ValueLabel
    ext_pres_value_label: ValueLabel
    sip_pres_value_label: ValueLabel

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
        # 時間変換フォーマッタ
        def time_fmt(sec: float) -> str:
            m, s = divmod(int(sec), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        self.step_time_label = ValueLabel(0, formatter=time_fmt)
        self.total_time_label = ValueLabel(0, formatter=time_fmt)

        time_layout.addWidget(QLabel("状態 :"))
        time_layout.addWidget(self.status_value_label)
        time_layout.addStretch()
        time_layout.addWidget(QLabel("Step :"))
        time_layout.addWidget(self.step_time_label)
        time_layout.addSpacing(5)
        time_layout.addWidget(QLabel("Total :"))
        time_layout.addWidget(self.total_time_label)

        return time_layout

    def _create_monitor_section(self) -> QLayout:
        monitor_layout = QHBoxLayout()

        # --- 左側: 出力 (HC / AMD) ---
        output_grid = QGridLayout()
        output_grid.setHorizontalSpacing(10)

        # 一番左の行
        output_grid.addWidget(QLabel("HC :"), 1, 0)
        output_grid.addWidget(QLabel("AMD :"), 2, 0)

        # ヘッダーと要素
        self.hc_value_labels = {}
        self.amd_value_labels = {}
        for i, electric_prop in enumerate(ElectricProperties):
            header_text = f"{electric_prop.name} ({electric_prop.unit})"
            lbl = QLabel(header_text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 10.5px; color: #555;")

            self.hc_value_labels[electric_prop] = ValueLabel(0, ".2f")
            self.amd_value_labels[electric_prop] = ValueLabel(0, ".2f")

            output_grid.addWidget(lbl, 0, i + 1)
            output_grid.addWidget(self.hc_value_labels[electric_prop], 1, i + 1)
            output_grid.addWidget(self.amd_value_labels[electric_prop], 2, i + 1)

        # --- 右側: 環境 (Temp / Pressure) ---
        env_layout = QFormLayout()

        # 要素最小限幅
        env_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        # env_layout.setFormAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # 温度
        self.temp_value_label = ValueLabel(Temperature(25.0), ".1f")

        self.ext_pres_value_label = ValueLabel(Pressure(0.0), ".2e")
        self.sip_pres_value_label = ValueLabel(Pressure(0.0), ".2e")

        env_layout.addRow("温度 :", self.temp_value_label)
        env_layout.addRow("EXT :", self.ext_pres_value_label)
        env_layout.addRow("SIP :", self.sip_pres_value_label)

        monitor_layout.addLayout(output_grid)
        monitor_layout.addStretch()
        monitor_layout.addLayout(env_layout)

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

    def update_measure_values(self, result: HCExperimentResult) -> None:
        """測定結果で表示を更新"""
        text = f"{result.sequence_index}: {result.sequence_name}"
        self.set_status(text, True)

        self.step_time_label.setValue(result.timestamp_step.base_value)
        self.total_time_label.setValue(result.timestamp_total.base_value)

        self.temp_value_label.setValue(result.temperature_case)
        self.ext_pres_value_label.setValue(result.pressure_ext)
        self.sip_pres_value_label.setValue(result.pressure_sip)

        for electric_prop in ElectricProperties:
            self.hc_value_labels[electric_prop].setValue(
                result.electricity_hc.get_quantity(electric_prop).base_value
            )
            self.amd_value_labels[electric_prop].setValue(
                result.electricity_amd.get_quantity(electric_prop).base_value
            )
