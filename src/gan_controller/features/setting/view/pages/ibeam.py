from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from gan_controller.core.domain.app_config import IBeamConfig
from gan_controller.presentation.components.widgets import NoScrollSpinBox


class IBeamConfigPage(QWidget):
    """iBeam (Laser) 設定画面"""

    com_number_edit: NoScrollSpinBox

    beam_channel_spin: NoScrollSpinBox

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_connection_config_group())
        layout.addWidget(self._create_param_config_group())
        layout.addStretch()

    def _create_connection_config_group(self) -> QGroupBox:
        connection_config_group = QGroupBox("接続設定")
        connection_config_form = QFormLayout(connection_config_group)

        self.com_number_edit = NoScrollSpinBox(minimum=0, maximum=99)
        connection_config_form.addRow("COM Port Number (0=disable) :", self.com_number_edit)

        return connection_config_group

    def _create_param_config_group(self) -> QGroupBox:
        param_config_group = QGroupBox("詳細パラメータ")
        param_config_form = QFormLayout(param_config_group)

        self.beam_channel_spin = NoScrollSpinBox(minimum=1, maximum=2)
        param_config_form.addRow("Beam Channel :", self.beam_channel_spin)

        return param_config_group

    # =============================================================================

    def get_config(self) -> IBeamConfig:
        return IBeamConfig(
            com_port=self.com_number_edit.value(),
            beam_ch=self.beam_channel_spin.value(),
        )

    def set_config(self, config: IBeamConfig) -> None:
        self.com_number_edit.setValue(config.com_port)
        self.beam_channel_spin.setValue(config.beam_ch)
