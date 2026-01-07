from PySide6.QtWidgets import QFormLayout, QGroupBox, QVBoxLayout, QWidget

from gan_controller.common.schemas.app_config import PWUXConfig
from gan_controller.common.ui.widgets import NoScrollSpinBox


class PWUXConfigPage(QWidget):
    """PWUX (Temp Controller) 設定画面"""

    com_number_edit: NoScrollSpinBox

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_connection_config_group())
        layout.addStretch()

    def _create_connection_config_group(self) -> QGroupBox:
        connection_config_group = QGroupBox("接続設定")
        connection_config_form = QFormLayout(connection_config_group)

        self.com_number_edit = NoScrollSpinBox(minimum=0, maximum=99)
        connection_config_form.addRow("COM Port Number (0=disable) :", self.com_number_edit)

        return connection_config_group

    # =============================================================================

    def get_config(self) -> PWUXConfig:
        return PWUXConfig(
            com_port=self.com_number_edit.value(),
        )

    def set_config(self, config: PWUXConfig) -> None:
        self.com_number_edit.setValue(config.com_port)
