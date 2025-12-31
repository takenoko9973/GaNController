from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLayout, QMainWindow, QStatusBar, QTabWidget, QVBoxLayout, QWidget

from gan_controller.features.heat_cleaning.ui import HeatCleaningTab
from gan_controller.features.nea_activation.nea_controller import NEAActivationController
from gan_controller.features.nea_activation.view import NEAActivationTab
from gan_controller.features.setting.ui import SettingsTab


class MainWindow(QMainWindow):
    main_layout: QLayout
    tabs: QTabWidget
    status_bar: QStatusBar

    # タブウィンドウの各要素を定義
    heat_cleaning_tab: HeatCleaningTab
    nea_activation_tab: NEAActivationTab
    settings_tab: SettingsTab

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("GaN Controller")

        # ウィンドウ全体のメインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # タブウィジェット設定
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self._init_heat_cleaning()
        self._init_nea_activation()
        self._init_settings()

    def _add_tab[T: QWidget](self, tab_name: str, tab: T) -> T:
        self.tabs.addTab(tab, tab_name)
        return tab

    def _init_heat_cleaning(self) -> None:
        self.heat_cleaning_tab = self._add_tab("Heat Cleaning", HeatCleaningTab())
        # self.heat_cleaning_controller

    def _init_nea_activation(self) -> None:
        self.nea_activation_tab = self._add_tab("NEA Activation", NEAActivationTab())
        self.nea_activation_controller = NEAActivationController(self.nea_activation_tab)

    def _init_settings(self) -> None:
        self.settings_tab = self._add_tab("Settings", SettingsTab())

    @Slot(str, int)
    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        """ステータスバーにメッセージを表示する (デフォルト5秒で消える)"""
        self.status_bar.showMessage(message, timeout)
