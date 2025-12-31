from PySide6.QtCore import QObject

from gan_controller.features.nea_activation.view.nea_tab_widget import NEAActivationTab


class NEAActivationController(QObject):
    def __init__(self, view: NEAActivationTab) -> None:
        super().__init__()

        self._view = view
        self._attach_view()

    def _attach_view(self) -> None:
        self._view.experiment_start.connect(self._experiment_start)
        self._view.experiment_stop.connect(self._experiment_stop)
        self._view.setting_apply.connect(self._setting_apply)

    def _experiment_start(self) -> None:
        """実験開始処理"""
        print("ex start")

    def _experiment_stop(self) -> None:
        """実験中断処理"""

    def _setting_apply(self) -> None:
        """実験途中での値更新"""
        print("ex apply")
