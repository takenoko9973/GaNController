from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget


class PWUXConfigPage(QWidget):
    """PWUX (Temp Controller) 設定画面"""

    com_number_edit: QLineEdit

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_connection_config_group())
        layout.addStretch()

    def _create_connection_config_group(self) -> QGroupBox:
        connection_config_group = QGroupBox("接続設定")
        connection_config_form = QFormLayout(connection_config_group)

        self.com_number_edit = QLineEdit()
        connection_config_form.addRow("COM Port Number :", self.com_number_edit)

        return connection_config_group
