from PySide6.QtWidgets import QWidget

from gan_controller.common.ui.widgets.log_setting_panel import CommonLogSettingPanel
from gan_controller.features.nea_activation.schemas import NEALogConfig


class NEALogSettingPanel(CommonLogSettingPanel):
    """ログ設定用ウィジェット"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Log Setting", parent)

    def get_config(self) -> NEALogConfig:
        values = self.get_values()
        return NEALogConfig(
            update_date_folder=values["update_date_folder"],
            update_major_number=values["update_major_number"],
            comment=values["comment"],
        )

    def set_config(self, config: NEALogConfig) -> None:
        self.set_values(
            update_date=config.update_date_folder,
            major_update=config.update_major_number,
            comment=config.comment,
        )
