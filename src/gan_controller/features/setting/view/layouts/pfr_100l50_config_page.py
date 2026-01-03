from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget

from gan_controller.common.widgets import NoScrollDoubleSpinBox, NoScrollSpinBox


class PFR100L50ConfigPage(QWidget):
    """PFR-100L50 (Heater/AMD) 共通設定画面"""

    visa_address_edit: QLineEdit

    unit_spin: NoScrollSpinBox
    v_limit_spin: NoScrollDoubleSpinBox
    ovp_spin: NoScrollDoubleSpinBox
    ocp_spin: NoScrollDoubleSpinBox

    def __init__(self, title_suffix: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_connection_config_group())
        layout.addWidget(self._create_param_config_group(title_suffix))
        layout.addStretch()

    def _create_connection_config_group(self) -> QGroupBox:
        """接続アドレス設定"""
        connection_config_group = QGroupBox("接続設定")
        connection_config_form = QFormLayout(connection_config_group)

        self.visa_address_edit = QLineEdit()
        connection_config_form.addRow("VISA Address :", self.visa_address_edit)

        return connection_config_group

    def _create_param_config_group(self, title_suffix: str) -> QGroupBox:
        param_config_group = QGroupBox(f"詳細パラメータ {title_suffix}")
        param_config_form = QFormLayout(param_config_group)

        self.unit_spin = NoScrollSpinBox(minimum=-10, maximum=10)
        self.v_limit_spin = NoScrollDoubleSpinBox(suffix=" V", decimals=2)
        self.ovp_spin = NoScrollDoubleSpinBox(suffix=" V", decimals=2)
        self.ocp_spin = NoScrollDoubleSpinBox(suffix=" A", decimals=2)

        param_config_form.addRow("Unit ID :", self.unit_spin)
        param_config_form.addRow("Max Voltage :", self.v_limit_spin)
        param_config_form.addRow("OVP (過電圧保護) :", self.ovp_spin)
        param_config_form.addRow("OCP (過電流保護) :", self.ocp_spin)

        return param_config_group
