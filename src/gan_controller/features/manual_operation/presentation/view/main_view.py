from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
        (
            header,
            self.gm10_connect_button,
            self.gm10_disconnect_button,
            self.gm10_status_label,
        ) = self._create_connection_header()

        # 設定チャンネルの表示
        rows = QVBoxLayout()
        rows.setSpacing(6)

        for key in ["ext", "sip", "hv", "pc", "tc"]:
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            value = ValueLabel("--", ".4g")
            value.setMinimumWidth(90)
            value.setMaximumWidth(120)

            self.gm10_label_widgets[key] = label
            self.gm10_value_labels[key] = value

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            row.addWidget(label)
            row.addWidget(value)
            row.addStretch()

            rows.addLayout(row)

        layout.addLayout(header)
        layout.addLayout(rows)

        return group

    def _create_pwux_group(self) -> QGroupBox:
        group = QGroupBox("PWUX (Pyrometer)")
        layout = QVBoxLayout(group)

        # 接続操作
        (
            header,
            self.pwux_connect_button,
            self.pwux_disconnect_button,
            self.pwux_status_label,
        ) = self._create_connection_header()

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
        (
            header,
            self.laser_connect_button,
            self.laser_disconnect_button,
            self.laser_status_label,
        ) = self._create_connection_header()

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
        self._apply_connection_state(
            self.gm10_connect_button,
            self.gm10_disconnect_button,
            self.gm10_status_label,
            connected,
        )

    def set_pwux_connected(self, connected: bool) -> None:
        # PWUXの接続状態をUIに反映
        self._apply_connection_state(
            self.pwux_connect_button,
            self.pwux_disconnect_button,
            self.pwux_status_label,
            connected,
            extra_enabled=[self.pwux_read_button, self.pwux_pointer_checkbox],
        )

    def set_laser_connected(self, connected: bool) -> None:
        # Laserの接続状態をUIに反映
        self._apply_connection_state(
            self.laser_connect_button,
            self.laser_disconnect_button,
            self.laser_status_label,
            connected,
            extra_enabled=[
                self.laser_set_button,
                self.laser_power_spin,
                self.laser_emission_checkbox,
            ],
        )
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
                self.gm10_value_labels[key].setText("--")

            self.gm10_label_widgets[key].setText(f"{text} :")

        self._fit_gm10_label_widths()

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

    def _fit_gm10_label_widths(self) -> None:
        max_width = 0
        for label in self.gm10_label_widgets.values():
            max_width = max(max_width, label.sizeHint().width())

        for label in self.gm10_label_widgets.values():
            label.setFixedWidth(max_width + 4)

    def _create_connection_header(
        self,
    ) -> tuple[QHBoxLayout, QPushButton, QPushButton, QLabel]:
        header = QHBoxLayout()
        connect_button = QPushButton("Connect")
        disconnect_button = QPushButton("Disconnect")
        status_label = QLabel("Disconnected")

        header.addWidget(connect_button)
        header.addWidget(disconnect_button)
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(status_label)

        return header, connect_button, disconnect_button, status_label

    def _apply_connection_state(
        self,
        connect_button: QPushButton,
        disconnect_button: QPushButton,
        status_label: QLabel,
        connected: bool,
        extra_enabled: list[QWidget] | None = None,
    ) -> None:
        connect_button.setEnabled(not connected)
        disconnect_button.setEnabled(connected)
        status_label.setText("Connected" if connected else "Disconnected")
        if extra_enabled:
            for widget in extra_enabled:
                widget.setEnabled(connected)
        self._apply_status_style(status_label, connected)

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
