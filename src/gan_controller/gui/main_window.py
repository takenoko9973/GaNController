from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLayout, QMainWindow, QStatusBar, QTabWidget, QVBoxLayout, QWidget

from gan_controller.features.heat_cleaning.view import HeatCleaningWidget
from gan_controller.features.nea_activation.view import NEAActivationWidget
from gan_controller.features.setting.view import SettingsWidget


class MainWindow(QMainWindow):
    main_layout: QLayout

    # タブウィンドウの各要素を定義
    tabs: QTabWidget
    heat_cleaning_tab: HeatCleaningWidget
    nea_activation_tab: NEAActivationWidget
    settings_tab: SettingsWidget

    status_bar: QStatusBar

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
        self.setup_tabs(self.main_layout)

    def setup_tabs(self, layout: QLayout) -> None:
        """タブウィンドウの各要素を設定"""
        self.tabs = QTabWidget()

        self.heat_cleaning_tab = HeatCleaningWidget()
        self.nea_activation_tab = NEAActivationWidget()
        self.settings_tab = SettingsWidget()

        self.tabs.addTab(self.heat_cleaning_tab, "Heat Cleaning")
        self.tabs.addTab(self.nea_activation_tab, "NEA Activation")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)

    @Slot(str, int)
    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        """ステータスバーにメッセージを表示する (デフォルト5秒で消える)"""
        self.status_bar.showMessage(message, timeout)
