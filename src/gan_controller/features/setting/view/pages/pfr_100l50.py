from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget

from gan_controller.common.domain.quantity.factory import Current, Voltage
from gan_controller.common.schemas.app_config import PFR100l50Config
from gan_controller.common.ui.widgets import NoScrollDoubleSpinBox, NoScrollSpinBox


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

    # =============================================================================

    def get_config(self) -> PFR100l50Config:
        return PFR100l50Config(
            visa=self.visa_address_edit.text(),
            unit=self.unit_spin.value(),
            v_limit=Voltage(self.v_limit_spin.value()),
            ovp=Voltage(self.ovp_spin.value()),
            ocp=Current(self.ocp_spin.value()),
        )

    def set_config(self, config: PFR100l50Config) -> None:
        self.visa_address_edit.setText(config.visa)
        self.unit_spin.setValue(config.unit)
        self.v_limit_spin.setValue(config.v_limit.base_value)
        self.ovp_spin.setValue(config.ovp.base_value)
        self.ocp_spin.setValue(config.ocp.base_value)
