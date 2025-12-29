from PySide6.QtWidgets import QWidget

from gan_controller.features.setting.controller import SettingController
from gan_controller.features.setting.ui.layouts import SettingLayout


class SettingsTab(QWidget):
    main_layout: SettingLayout
    controller: SettingController

    def __init__(self) -> None:
        super().__init__()

        self.main_layout = SettingLayout()
        self.setLayout(self.main_layout)
