from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget

from gan_controller.ui.widgets.no_scroll_spinbox import NoScrollSpinBox


class GeneralConfigPage(QWidget):
    """共通設定画面"""

    log_dir_edit: QLineEdit
    encode_edit: QLineEdit
    tz_spin: NoScrollSpinBox

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(self._create_general_config())
        layout.addStretch()

    def _create_general_config(self) -> QGroupBox:
        common_config_group = QGroupBox("共通設定 (Logging / System)")
        common_config_form = QFormLayout(common_config_group)

        self.log_dir_edit = QLineEdit()
        self.encode_edit = QLineEdit()
        self.tz_spin = NoScrollSpinBox(minimum=-12, maximum=14)

        common_config_form.addRow("ログ保存先 :", self.log_dir_edit)
        common_config_form.addRow("ログエンコード :", self.encode_edit)
        common_config_form.addRow("タイムゾーン (JST=9) :", self.tz_spin)

        return common_config_group
