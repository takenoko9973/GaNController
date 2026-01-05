from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.features.heat_cleaning.ui.tab_widget import HeatCleaningTab


class HeatCleaningController(ITabController):
    _view: HeatCleaningTab

    def __init__(self, view: HeatCleaningTab) -> None:
        super().__init__()

        self._view = view
