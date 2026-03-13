from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gan_controller.core.domain.app_config import GM10Config
from gan_controller.core.domain.quantity import Power, Quantity, Temperature, Volt, Watt
from gan_controller.presentation.components.widgets import ValueLabel


class ManualOperationMainView(QWidget):
    gm10_connect_requested = Signal()
    gm10_disconnect_requested = Signal()
    pwux_connect_requested = Signal()
    pwux_disconnect_requested = Signal()
    laser_connect_requested = Signal()
    laser_disconnect_requested = Signal()
    pwux_read_requested = Signal()
    pwux_pointer_toggled = Signal(bool)
    laser_set_requested = Signal()
    laser_emission_toggled = Signal(bool)

    gm10_connect_button: QPushButton
    gm10_disconnect_button: QPushButton
    gm10_status_label: QLabel

    pwux_connect_button: QPushButton
    pwux_disconnect_button: QPushButton
    pwux_status_label: QLabel

    laser_connect_button: QPushButton
    laser_disconnect_button: QPushButton
    laser_status_label: QLabel

    gm10_label_widgets: dict[str, QLabel]
    gm10_value_labels: dict[str, ValueLabel]
    gm10_enabled: dict[str, bool]

    pwux_temp_label: ValueLabel
    pwux_read_button: QPushButton
    pwux_pointer_checkbox: QCheckBox

    laser_power_spin: QDoubleSpinBox
    laser_set_button: QPushButton
    laser_emission_checkbox: QCheckBox
    laser_power_pv_label: ValueLabel

    def __init__(self) -> None:
        super().__init__()
        self.gm10_label_widgets = {}
        self.gm10_value_labels = {}
        self.gm10_enabled = {}

        self._init_ui()
        self._connect_signals()
        self.set_gm10_connected(False)
        self.set_pwux_connected(False)
        self.set_laser_connected(False)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 装置ごとの接続/操作パネル
        layout.addWidget(self._create_gm10_group())
        layout.addWidget(self._create_pwux_group())
        layout.addWidget(self._create_laser_group())
        layout.addStretch()

    def _create_gm10_group(self) -> QGroupBox:
        group = QGroupBox("Logger (GM10)")
        layout = QVBoxLayout(group)

        # 接続操作
        header = QHBoxLayout()
        self.gm10_connect_button = QPushButton("Connect")
        self.gm10_disconnect_button = QPushButton("Disconnect")
        self.gm10_status_label = QLabel("Disconnected")

        header.addWidget(self.gm10_connect_button)
        header.addWidget(self.gm10_disconnect_button)
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(self.gm10_status_label)

        # 設定チャンネルの表示
        form = QFormLayout()

        for key in ["ext", "sip", "hv", "pc", "tc"]:
            label = QLabel()
            value = ValueLabel("-", ".4g")
            self.gm10_label_widgets[key] = label
            self.gm10_value_labels[key] = value
            form.addRow(label, value)

        layout.addLayout(header)
        layout.addLayout(form)

        return group

    def _create_pwux_group(self) -> QGroupBox:
        group = QGroupBox("PWUX (Pyrometer)")
        layout = QVBoxLayout(group)

        # 接続操作
        header = QHBoxLayout()
        self.pwux_connect_button = QPushButton("Connect")
        self.pwux_disconnect_button = QPushButton("Disconnect")
        self.pwux_status_label = QLabel("Disconnected")

        header.addWidget(self.pwux_connect_button)
        header.addWidget(self.pwux_disconnect_button)
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(self.pwux_status_label)

        self.pwux_temp_label = ValueLabel(Temperature(float("nan")), ".2f")
        self.pwux_read_button = QPushButton("温度取得")
        self.pwux_pointer_checkbox = QCheckBox("照準表示")

        # 温度表示・照準切替
        body = QHBoxLayout()
        body.addWidget(QLabel("Temperature:"))
        body.addWidget(self.pwux_temp_label)
        body.addSpacing(10)
        body.addWidget(self.pwux_read_button)
        body.addWidget(self.pwux_pointer_checkbox)
        body.addStretch()

        layout.addLayout(header)
        layout.addLayout(body)

        return group

    def _create_laser_group(self) -> QGroupBox:
        group = QGroupBox("Toptica Laser")
        layout = QVBoxLayout(group)

        # 接続操作
        header = QHBoxLayout()
        self.laser_connect_button = QPushButton("Connect")
        self.laser_disconnect_button = QPushButton("Disconnect")
        self.laser_status_label = QLabel("Disconnected")

        header.addWidget(self.laser_connect_button)
        header.addWidget(self.laser_disconnect_button)
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(self.laser_status_label)

        self.laser_power_spin = QDoubleSpinBox()
        self.laser_power_spin.setRange(0.0, 120.0)
        self.laser_power_spin.setDecimals(1)
        self.laser_power_spin.setValue(10.0)
        self.laser_power_spin.setSuffix(" mW")

        self.laser_set_button = QPushButton("Set")
        self.laser_emission_checkbox = QCheckBox("Emission ON")
        self.laser_power_pv_label = ValueLabel(Power(0.0, "m"), ".2f")

        # 出力設定・Emission切替
        body = QHBoxLayout()
        body.addWidget(QLabel("Power:"))
        body.addWidget(self.laser_power_spin)
        body.addWidget(self.laser_set_button)
        body.addSpacing(10)
        body.addWidget(QLabel("Current:"))
        body.addWidget(self.laser_power_pv_label)
        body.addSpacing(10)
        body.addWidget(self.laser_emission_checkbox)
        body.addStretch()

        layout.addLayout(header)
        layout.addLayout(body)

        return group

    def _connect_signals(self) -> None:
        self.gm10_connect_button.clicked.connect(self.gm10_connect_requested.emit)
        self.gm10_disconnect_button.clicked.connect(self.gm10_disconnect_requested.emit)
        self.pwux_connect_button.clicked.connect(self.pwux_connect_requested.emit)
        self.pwux_disconnect_button.clicked.connect(self.pwux_disconnect_requested.emit)
        self.laser_connect_button.clicked.connect(self.laser_connect_requested.emit)
        self.laser_disconnect_button.clicked.connect(self.laser_disconnect_requested.emit)
        self.pwux_read_button.clicked.connect(self.pwux_read_requested.emit)
        self.pwux_pointer_checkbox.toggled.connect(self.pwux_pointer_toggled.emit)
        self.laser_set_button.clicked.connect(self.laser_set_requested.emit)
        self.laser_emission_checkbox.toggled.connect(self.laser_emission_toggled.emit)

    # =============================================================================

    def set_gm10_connected(self, connected: bool) -> None:
        # GM10の接続状態をUIに反映
        self.gm10_connect_button.setEnabled(not connected)
        self.gm10_disconnect_button.setEnabled(connected)
        self.gm10_status_label.setText("Connected" if connected else "Disconnected")
        self._apply_status_style(self.gm10_status_label, connected)

    def set_pwux_connected(self, connected: bool) -> None:
        # PWUXの接続状態をUIに反映
        self.pwux_connect_button.setEnabled(not connected)
        self.pwux_disconnect_button.setEnabled(connected)
        self.pwux_status_label.setText("Connected" if connected else "Disconnected")
        self.pwux_read_button.setEnabled(connected)
        self.pwux_pointer_checkbox.setEnabled(connected)
        self._apply_status_style(self.pwux_status_label, connected)

    def set_laser_connected(self, connected: bool) -> None:
        # Laserの接続状態をUIに反映
        self.laser_connect_button.setEnabled(not connected)
        self.laser_disconnect_button.setEnabled(connected)
        self.laser_status_label.setText("Connected" if connected else "Disconnected")
        self.laser_set_button.setEnabled(connected)
        self.laser_power_spin.setEnabled(connected)
        self.laser_emission_checkbox.setEnabled(connected)
        self._apply_status_style(self.laser_status_label, connected)
        if not connected:
            self.laser_power_pv_label.setText("--")

    def set_gm10_channel_config(self, config: GM10Config) -> None:
        mapping = {
            "ext": ("真空度(EXT)", config.ext_ch),
            "sip": ("真空度(SIP)", config.sip_ch),
            "hv": ("HV Control", config.hv_ch),
            "pc": ("Photo Current", config.pc_ch),
            "tc": ("TC Measure", config.tc_ch),
        }

        for key, (label, ch) in mapping.items():
            if ch <= 0:
                text = f"{label} (Disabled)"
                self.gm10_enabled[key] = False
                self.gm10_value_labels[key].setText("--")
            else:
                text = f"{label} (Ch {ch})"
                self.gm10_enabled[key] = True

            self.gm10_label_widgets[key].setText(f"{text} :")

    def update_gm10_values(self, values: dict[str, Quantity[Volt]]) -> None:
        for key, val in values.items():
            if not self.gm10_enabled.get(key, False):
                continue
            self.gm10_value_labels[key].setValue(val)

    def set_pwux_temperature(self, temperature) -> None:  # noqa: ANN001
        self.pwux_temp_label.setValue(temperature)

    def set_pwux_pointer_checked(self, checked: bool) -> None:
        self.pwux_pointer_checkbox.blockSignals(True)
        self.pwux_pointer_checkbox.setChecked(checked)
        self.pwux_pointer_checkbox.blockSignals(False)

    def set_laser_emission_checked(self, checked: bool) -> None:
        self.laser_emission_checkbox.blockSignals(True)
        self.laser_emission_checkbox.setChecked(checked)
        self.laser_emission_checkbox.blockSignals(False)

    def set_laser_current_power(self, power: Quantity[Watt] | None) -> None:
        if power is None:
            self.laser_power_pv_label.setText("--")
            return
        self.laser_power_pv_label.setValue(power)

    def _apply_status_style(self, label: QLabel, connected: bool) -> None:
        font = QFont(label.font())
        font.setBold(connected)
        label.setFont(font)

        palette = label.palette()
        if connected:
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.green)
        else:
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.gray)
        label.setPalette(palette)

    def confirm_disconnect_all(self) -> bool:
        # タブ移動時の切断確認
        ret = QMessageBox.question(
            self,
            "切断確認",
            "接続中の機器があります。切断してタブを切り替えますか？",  # noqa: RUF001
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return ret == QMessageBox.StandardButton.Ok

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "エラー", message)
