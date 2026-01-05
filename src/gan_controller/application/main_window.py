from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QLayout, QMainWindow, QStatusBar, QTabWidget, QVBoxLayout, QWidget

from gan_controller.application.app_feature import AppFeature
from gan_controller.common.interfaces.tab_controller import ITabController
from gan_controller.common.services.global_messenger import GlobalMessenger


class MainWindow(QMainWindow):
    main_layout: QLayout
    tab_widget: QTabWidget
    status_bar: QStatusBar

    _last_tab_index: int
    controllers: dict[int, ITabController]

    def __init__(self, features: list[AppFeature]) -> None:
        super().__init__()

        self.setWindowTitle("GaN Controller")

        self._init_ui()
        self._init_connect()
        self._setup_services()
        self._setup_features(features)

    def _init_ui(self) -> None:
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
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.main_layout.addWidget(self.tab_widget)
        self._last_tab_index = 0

    def _setup_services(self) -> None:
        """アプリ全体に関わるサービスの接続"""
        # GlobalMessengerからの通知を表示
        messenger = GlobalMessenger()
        messenger.status_message_requested.connect(self.show_status_message)
        messenger.tab_lock_requested.connect(self.set_tabs_locked)

    def _setup_features(self, features: list[AppFeature]) -> None:
        """機能リストを受け取り、タブに追加する"""
        self.controllers = {}

        self.tab_widget.blockSignals(True)  # 追加によって、余計なシグナルを出さないように
        for feature in features:
            index = self.tab_widget.addTab(feature.view, feature.title)
            self.controllers[index] = feature.controller

        self.tab_widget.blockSignals(False)

    def _init_connect(self) -> None:
        self._last_tab_index = 0
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """アプリ終了時の処理"""
        # 全てのタブコントローラーの終了処理(保存など)を呼び出す
        for controller in self.controllers.values():
            controller.on_close()

        super().closeEvent(event)

    # =====================================================================================
    # シグナル
    # =====================================================================================

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

    @Slot(bool)
    def set_tabs_locked(self, locked: bool) -> None:
        """現在のタブ以外の有効/無効を切り替える (グレーアウト処理)"""
        current_index = self.tab_widget.currentIndex()

        for i in range(self.tab_widget.count()):
            # 現在表示中のタブ以外を操作する
            if i != current_index:
                self.tab_widget.setTabEnabled(i, not locked)
