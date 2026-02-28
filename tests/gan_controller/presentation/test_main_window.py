from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from gan_controller.presentation.app_feature import AppFeature
from gan_controller.presentation.components.tab_controller import ITabController
from gan_controller.presentation.main_window import MainWindow


class _CountingTabController(ITabController):
    def __init__(self) -> None:
        super().__init__()
        self.switch_attempts = 0

    def try_switch_from(self) -> bool:
        self.switch_attempts += 1
        return True


def test_tab_change_calls_try_switch_from_once(qtbot: QtBot) -> None:
    first_ctrl = _CountingTabController()
    second_ctrl = _CountingTabController()

    features = [
        AppFeature("Tab1", QWidget(), first_ctrl),
        AppFeature("Tab2", QWidget(), second_ctrl),
    ]
    window = MainWindow(features)
    qtbot.addWidget(window)
    window.show()

    window.tab_widget.setCurrentIndex(1)
    qtbot.waitUntil(lambda: window.tab_widget.currentIndex() == 1)

    assert first_ctrl.switch_attempts == 1
