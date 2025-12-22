from PySide6.QtCore import QObject

from heater_amd_controller.controllers.heat_cleaning_controller import HeatCleaningController
from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.views.main_window import MainWindowView


class MainController(QObject):
    def __init__(self, main_window: MainWindowView) -> None:
        super().__init__()
        self.view = main_window

        self.protocol_manager = ProtocolManager()

        # HC sub controller
        self.sequence_ctrl = HeatCleaningController(
            view=self.view.sequence_tab,
            manager=self.protocol_manager,
        )

        self.sequence_ctrl.status_message_requested.connect(self.view.show_status_message)
