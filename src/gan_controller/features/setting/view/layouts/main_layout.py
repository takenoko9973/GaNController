from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .general_config_page import GeneralConfigPage
from .gm10_config_page import GM10ConfigPage
from .ibeam_config_page import IBeamConfigPage
from .pfr_100l50_config_page import PFR100L50ConfigPage
from .pwux_config_page import PWUXConfigPage


class SettingLayout(QVBoxLayout):
    """設定タブ見た目"""

    # 操作ボタン
    btn_load: QPushButton
    btn_save: QPushButton

    # サイドバーとページスタック
    sidebar_widget: QListWidget
    stack_widget: QStackedWidget

    # ページ
    gm10_page: GM10ConfigPage
    hps_page: PFR100L50ConfigPage
    aps_page: PFR100L50ConfigPage
    ibeam_page: IBeamConfigPage
    pwux_page: PWUXConfigPage
    general_page: GeneralConfigPage

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(10)

        self.addWidget(self._header_panel())
        self.addWidget(self._main_panel())

        self._connect_signal()

    def _header_panel(self) -> QFrame:
        header_panel = QFrame()
        header_layout = QHBoxLayout(header_panel)

        self.btn_load = QPushButton("設定読み込み")
        self.btn_save = QPushButton("設定保存")

        header_layout.addStretch()
        header_layout.addWidget(self.btn_load)
        header_layout.addWidget(self.btn_save)

        return header_panel

    def _main_panel(self) -> QFrame:
        main_panel = QFrame()
        main_layout = QHBoxLayout(main_panel)

        self.sidebar_widget = QListWidget()
        self.sidebar_widget.setFixedWidth(200)

        self.stack_widget = QStackedWidget()
        self.stack_widget.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(self.stack_widget)

        self.gm10_page = self._add_page("GM10 (Logger)", GM10ConfigPage())
        self.hps_page = self._add_page("PFR100L50 (Heater)", PFR100L50ConfigPage("(Heater)"))
        self.aps_page = self._add_page("PFR100L50 (AMD)", PFR100L50ConfigPage("(AMD)"))
        self.ibeam_page = self._add_page("iBeam (Laser)", IBeamConfigPage())
        self.pwux_page = self._add_page("PWUX (Pyrometer)", PWUXConfigPage())
        self.general_page = self._add_page("その他設定 (General)", GeneralConfigPage())

        self.sidebar_widget.setCurrentRow(0)

        return main_panel

    def _add_page[T: QWidget](self, title: str, widget: T) -> T:
        """ページの追加"""
        self.sidebar_widget.addItem(title)
        self.stack_widget.addWidget(widget)
        return widget

    def _connect_signal(self) -> None:
        # サイドとページの一致処理
        self.sidebar_widget.currentRowChanged.connect(self.stack_widget.setCurrentIndex)
