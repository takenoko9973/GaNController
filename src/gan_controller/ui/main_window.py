from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLayout, QMainWindow, QStatusBar, QTabWidget, QVBoxLayout, QWidget

from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.common.services.global_messenger import GlobalMessenger
from gan_controller.features.heat_cleaning.hc_controller import HeatCleaningController
from gan_controller.features.heat_cleaning.ui import HeatCleaningTab
from gan_controller.features.nea_activation.nea_controller import NEAActivationController
from gan_controller.features.nea_activation.view import NEAActivationTab
from gan_controller.features.setting.setting_controller import SettingsController
from gan_controller.features.setting.view import SettingsTab


class MainWindow(QMainWindow):
    main_layout: QLayout
    tab_widget: QTabWidget
    status_bar: QStatusBar

    # タブウィンドウの各要素を定義
    heat_cleaning_tab: HeatCleaningTab
    nea_activation_tab: NEAActivationTab
    settings_tab: SettingsTab

    # 各タブのコントローラー
    heat_cleaning_controller: HeatCleaningController
    nea_activation_controller: NEAActivationController
    settings_controller: SettingsController

    _last_tab_index: int
    controllers: list[ITabController]

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
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        self.controllers: dict[int, object] = {}

        self._init_heat_cleaning_tab()
        self._init_nea_activation_tab()
        self._init_settings_tab()

        self._init_connect()

        # メッセンジャーとステータスバーとの接続
        messenger = GlobalMessenger()
        messenger.status_message_requested.connect(self.show_status_message)

    def _add_tab[T: QWidget, U: ITabController](self, tab_name: str, tab: T, controller: U) -> None:
        index = self.tab_widget.addTab(tab, tab_name)
        self.controllers[index] = controller

    def _init_heat_cleaning_tab(self) -> None:
        self.heat_cleaning_tab = HeatCleaningTab()
        self.heat_cleaning_controller = HeatCleaningController(self.heat_cleaning_tab)
        self._add_tab("Heat Cleaning", self.heat_cleaning_tab, self.heat_cleaning_controller)

    def _init_nea_activation_tab(self) -> None:
        self.nea_activation_tab = NEAActivationTab()
        self.nea_activation_controller = NEAActivationController(self.nea_activation_tab)
        self._add_tab("NEA Activation", self.nea_activation_tab, self.nea_activation_controller)

    def _init_settings_tab(self) -> None:
        self.settings_tab = SettingsTab()
        self.settings_controller = SettingsController(self.settings_tab)
        self._add_tab("Settings", self.settings_tab, self.settings_controller)

    def _init_connect(self) -> None:
        # --- イベント監視 ---
        self._last_tab_index = 0
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    @Slot(int)
    def _on_tab_changed(self, new_index: int) -> None:
        """タブ切り替え時のイベントハンドラ"""
        old_index = self._last_tab_index

        self.tab_widget.blockSignals(True)  # タブのシグナル無効化
        self.tab_widget.setCurrentIndex(old_index)  # 一旦戻す

        # 移動元のコントローラーを取得
        controller: ITabController = self.controllers.get(old_index)

        is_allowed = controller.try_switch_from()  # 移動していいか確認
        if is_allowed:
            # 移動を行う
            self.tab_widget.setCurrentIndex(new_index)
            self._last_tab_index = new_index

        self.tab_widget.blockSignals(False)  # 再有効化

    @Slot(str, int)
    def show_status_message(self, message: str, timeout_ms: int = 5000) -> None:
        """ステータスバーにメッセージを表示する (デフォルト5秒で消える)"""
        self.status_bar.showMessage(message, timeout_ms)
