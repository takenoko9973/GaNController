from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from heater_amd_controller.views.widgets.labeled_item import LabeledItem
from heater_amd_controller.views.widgets.value_label import ValueLabel


class HCExecutionControlGroup(QGroupBox):
    """実行制御およびモニタリング表示用ウィジェット"""

    execution_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("実行制御 / モニタリング", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 状態・時間
        layout.addLayout(self._create_status_section())
        layout.addSpacing(10)

        # センサー値
        layout.addLayout(self._create_monitor_section())
        layout.addSpacing(10)

        # 制御
        layout.addLayout(self._create_control_section())

    def _create_status_section(self) -> QLayout:
        time_layout = QHBoxLayout()

        # ====== 状態
        self.status_value_label = QLabel("待機中")
        # フォント
        status_font = QFont()
        status_font.setBold(True)
        self.status_value_label.setFont(status_font)

        status_pal = self.status_value_label.palette()
        status_pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.gray)
        self.status_value_label.setPalette(status_pal)

        # ====== 時間
        self.step_time_label = ValueLabel("00:00:00")
        self.total_time_label = ValueLabel("00:00:00")

        time_layout.addWidget(LabeledItem("状態:", self.status_value_label))
        time_layout.addStretch()
        time_layout.addWidget(LabeledItem("Sequence:", self.step_time_label))
        time_layout.addSpacing(5)
        time_layout.addWidget(LabeledItem("Total:", self.total_time_label))

        return time_layout

    def _create_monitor_section(self) -> QLayout:
        monitor_layout = QHBoxLayout()

        # --- 左側: 出力 (HC / AMD) ---
        output_grid = QGridLayout()
        output_grid.setHorizontalSpacing(15)

        # ヘッダー
        headers = ["Current (A)", "Voltage (V)", "Power (W)"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 11px; color: #555;")
            output_grid.addWidget(lbl, 0, col + 1)

        # HC 行
        output_grid.addWidget(QLabel("HC:"), 1, 0)
        self.hc_cur = ValueLabel("0.00")
        self.hc_vol = ValueLabel("0.00")
        self.hc_pow = ValueLabel("0.00")
        output_grid.addWidget(self.hc_cur, 1, 1)
        output_grid.addWidget(self.hc_vol, 1, 2)
        output_grid.addWidget(self.hc_pow, 1, 3)

        # AMD 行
        output_grid.addWidget(QLabel("AMD:"), 2, 0)
        self.amd_cur = ValueLabel("0.00")
        self.amd_vol = ValueLabel("0.00")
        self.amd_pow = ValueLabel("0.00")
        output_grid.addWidget(self.amd_cur, 2, 1)
        output_grid.addWidget(self.amd_vol, 2, 2)
        output_grid.addWidget(self.amd_pow, 2, 3)

        # --- 右側: 環境 (Temp / Pressure) ---
        env_grid = QVBoxLayout()

        # 温度
        self.temp_val = ValueLabel("25.0", suffix=" °C")
        self.ext_pres_val = ValueLabel("1.20e-8", suffix=" Pa")
        self.sip_pres_val = ValueLabel("3.50e-7", suffix=" Pa")

        env_grid.addWidget(LabeledItem("温度:", self.temp_val))
        env_grid.addWidget(LabeledItem("EXT:", self.ext_pres_val))
        env_grid.addWidget(LabeledItem("SIP:", self.sip_pres_val))

        monitor_layout.addLayout(output_grid, stretch=3)
        monitor_layout.addStretch(20)
        monitor_layout.addLayout(env_grid, stretch=2)

        return monitor_layout

    def _create_control_section(self) -> QLayout:
        control_layout = QHBoxLayout()

        self.start_button = QPushButton("開始")
        self.stop_button = QPushButton("停止")

        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)

        # 初期状態: 停止中なので「停止」ボタンは無効化
        self.stop_button.setEnabled(False)

        # クリック時のシグナル接続
        self.start_button.clicked.connect(self._on_start_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        return control_layout

    def _on_start_clicked(self) -> None:
        """開始ボタン押下時"""
        # 即座にUI反応
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # 開始 を通知
        self.execution_toggled.emit(True)

    def _on_stop_clicked(self) -> None:
        """停止ボタン押下時"""
        # 停止処理は時間がかかる場合があるため、ボタンを無効化して連打を防ぐ
        self.stop_button.setEnabled(False)
        # 停止 を通知
        self.execution_toggled.emit(False)

    # --- 更新用メソッド ---

    def update_status(
        self, status_text: str, step_time: str, total_time: str, is_running: bool
    ) -> None:
        """状態と時間を更新"""
        self.status_value_label.setText(status_text)
        self.step_time_label.setText(step_time)
        self.total_time_label.setText(total_time)

        pal = self.status_value_label.palette()
        if is_running:
            pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.green)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.gray)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

        self.status_value_label.setPalette(pal)

    def update_sensor_values(
        self,
        hc_vals: tuple[float, float, float],  # (A, V, W)
        amd_vals: tuple[float, float, float],  # (A, V, W)
        temp: float,
        ext_pres: float,
        sip_pres: float,
    ) -> None:
        """センサー値更新"""
        # HC
        self.hc_cur.set_value(f"{hc_vals[0]:.2f}")
        self.hc_vol.set_value(f"{hc_vals[1]:.2f}")
        self.hc_pow.set_value(f"{hc_vals[2]:.2f}")

        # AMD
        self.amd_cur.set_value(f"{amd_vals[0]:.2f}")
        self.amd_vol.set_value(f"{amd_vals[1]:.2f}")
        self.amd_pow.set_value(f"{amd_vals[2]:.2f}")

        # Environment
        self.temp_val.set_value(f"{temp:.1f}")
        self.ext_pres_val.set_value(f"{ext_pres:.2e}")
        self.sip_pres_val.set_value(f"{sip_pres:.2e}")
