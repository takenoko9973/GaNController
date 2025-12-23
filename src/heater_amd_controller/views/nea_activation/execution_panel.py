from PySide6.QtCore import Qt, Signal, Slot
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


class NEAExecutionPanel(QGroupBox):
    """NEA Activation 実行制御およびモニタリング表示用パネル"""

    # シグナル
    start_requested = Signal()
    stop_requested = Signal()

    # UI要素
    status_value_label: QLabel
    time_label: ValueLabel

    qe_val: ValueLabel
    current_val: ValueLabel

    temp_val: ValueLabel
    ext_pres_val: ValueLabel
    sip_pres_val: ValueLabel

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("実行制御 / モニタリング", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. 状態・時間
        layout.addLayout(self._create_status_section())
        layout.addSpacing(10)

        # 2. センサー値 (QE, Current, Pressure, Temp)
        layout.addLayout(self._create_monitor_section())
        layout.addSpacing(10)

        # 3. 制御ボタン
        layout.addLayout(self._create_control_section())

    def _create_status_section(self) -> QLayout:
        layout = QHBoxLayout()

        # ====== 状態
        self.status_value_label = QLabel("待機中")
        status_font = QFont()
        status_font.setBold(True)
        self.status_value_label.setFont(status_font)

        # 初期色
        pal = self.status_value_label.palette()
        pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.gray)
        self.status_value_label.setPalette(pal)

        # ====== 時間 (秒表示)
        self.time_label = ValueLabel("0.0", suffix=" s")

        layout.addWidget(LabeledItem("状態:", self.status_value_label))
        layout.addStretch()
        layout.addWidget(LabeledItem("Time:", self.time_label))

        return layout

    def _create_monitor_section(self) -> QLayout:
        # グリッドレイアウトで整理
        layout = QGridLayout()
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(10)

        # --- Row 0: 主要測定値 (QE, Photocurrent) ---
        self.qe_val = ValueLabel("0.000", suffix=" %")
        self.current_val = ValueLabel("0.00e-00", suffix=" A")

        # 少し強調
        font = QFont()
        font.setBold(True)
        self.qe_val.setFont(font)

        layout.addWidget(LabeledItem("QE:", self.qe_val), 0, 0)
        layout.addWidget(LabeledItem("Photocurrent:", self.current_val), 0, 1)

        # --- Row 1: 環境値 (Pressure, Temp) ---
        self.ext_pres_val = ValueLabel("0.00e-00", suffix=" Pa")
        self.sip_pres_val = ValueLabel("0.00e-00", suffix=" Pa")
        self.temp_val = ValueLabel("25.0", suffix=" °C")

        layout.addWidget(LabeledItem("EXT:", self.ext_pres_val), 1, 0)
        layout.addWidget(LabeledItem("SIP:", self.sip_pres_val), 1, 1)
        layout.addWidget(LabeledItem("Temp:", self.temp_val), 2, 0)

        return layout

    def _create_control_section(self) -> QLayout:
        layout = QHBoxLayout()

        self.start_button = QPushButton("開始")
        self.stop_button = QPushButton("停止")

        self.start_button.setMinimumHeight(40)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.on_start_clicked)
        self.stop_button.clicked.connect(self.on_stop_clicked)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        return layout

    # === Slots ===

    @Slot()
    def on_start_clicked(self) -> None:
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.start_requested.emit()

    @Slot()
    def on_stop_clicked(self) -> None:
        self.stop_button.setEnabled(False)
        self.stop_requested.emit()

    @Slot(str, float, bool)
    def update_status(self, status_text: str, time_sec: float, is_running: bool) -> None:
        """状態と時間を更新 (秒単位)"""
        self.status_value_label.setText(status_text)
        self.time_label.set_value(f"{time_sec:.1f}")

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

    @Slot(float, float, float, float, float)
    def update_monitor_values(
        self, qe: float, current: float, ext: float, sip: float, temp: float
    ) -> None:
        """モニタリング値の更新"""
        self.qe_val.set_value(f"{qe:.4f}")
        self.current_val.set_value(f"{current:.4e}")
        self.ext_pres_val.set_value(f"{ext:.2e}")
        self.sip_pres_val.set_value(f"{sip:.2e}")
        self.temp_val.set_value(f"{temp:.1f}")
