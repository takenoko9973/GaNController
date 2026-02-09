from PySide6.QtWidgets import QCheckBox, QWidget

from gan_controller.common.ui.widgets.log_setting_panel import CommonLogSettingPanel
from gan_controller.features.heat_cleaning.domain.config import HCLogConfig


class HCLogSettingPanel(CommonLogSettingPanel):
    """シーケンス設定用ウィジェット"""

    chk_record_pyro: QCheckBox

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Log Setting", parent)
        self._add_custom_widgets()

    def _add_custom_widgets(self) -> None:
        """固有のUI要素を追加する"""
        self.chk_record_pyro = QCheckBox("放射温度計記録")
        self.chk_record_pyro.setChecked(True)

        # コメント欄の上に挿入
        self.insert_widget(1, self.chk_record_pyro)

    # 特定のConfig型への変換のみを担当する
    def get_config(self) -> HCLogConfig:
        values = self.get_values()
        return HCLogConfig(
            update_date_folder=values["update_date_folder"],
            update_major_number=values["update_major_number"],
            comment=values["comment"],
            record_pyrometer=self.chk_record_pyro.isChecked(),
        )

    def set_config(self, config: HCLogConfig) -> None:
        self.set_values(
            update_date=config.update_date_folder,
            major_update=config.update_major_number,
            comment=config.comment,
        )
        self.chk_record_pyro.setChecked(config.record_pyrometer)
