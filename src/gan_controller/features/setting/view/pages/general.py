from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QVBoxLayout, QWidget

from gan_controller.common.schemas.app_config import CommonConfig


class GeneralConfigPage(QWidget):
    """共通設定画面"""

    log_dir_edit: QLineEdit
    encode_edit: QLineEdit

    is_simulation: bool  # デバック用の値を一応保持

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

        common_config_form.addRow("ログエンコード :", self.encode_edit)

        return common_config_group

    # =============================================================================

    def get_config(self) -> CommonConfig:
        return CommonConfig(
            encode=self.encode_edit.text(),
            is_simulation_mode=self.is_simulation,
        )

    def set_config(self, config: CommonConfig) -> None:
        self.encode_edit.setText(config.encode)
        self.is_simulation = config.is_simulation_mode  # 操作はできないが一応
