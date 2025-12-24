from PySide6.QtCore import QObject

from heater_amd_controller.controllers.heat_cleaning_controller import HeatCleaningController
from heater_amd_controller.controllers.nea_activation_controller import NEAController
from heater_amd_controller.logics.hardware_manager import HardwareManager
from heater_amd_controller.logics.protocol_manager import ProtocolManager
from heater_amd_controller.views.main_window import MainWindowView


class MainController(QObject):
    def __init__(self, main_window: MainWindowView) -> None:
        super().__init__()
        self.view = main_window

        # データ・ハードウェア管理クラスの生成
        self.protocol_manager = ProtocolManager()
        self.hw_manager = HardwareManager()

        # HC sub controller
        self.sequence_ctrl = HeatCleaningController(
            view=self.view.sequence_tab,
            manager=self.protocol_manager,
            hw_manager=self.hw_manager,
        )

        # NEA sub controller
        self.nea_ctrl = NEAController(
            view=self.view.nea_act_tab,
            hw_manager=self.hw_manager,  # 共有インスタンスを渡す
        )

        self.sequence_ctrl.status_message_requested.connect(self.view.show_status_message)
