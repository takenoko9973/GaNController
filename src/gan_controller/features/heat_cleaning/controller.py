from gan_controller.common.ui.tab_controller import ITabController
from gan_controller.features.heat_cleaning.view.main_view import HeatCleaningMainView


class HeatCleaningController(ITabController):
    _view: HeatCleaningMainView

    def __init__(self, view: HeatCleaningMainView) -> None:
        super().__init__()

        self._view = view
