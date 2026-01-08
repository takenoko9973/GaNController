from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gan_controller.common.schemas.app_config import AppConfig, DevicesConfig
from gan_controller.features.setting.view.pages import (
    GeneralConfigPage,
    GM10ConfigPage,
    IBeamConfigPage,
    PFR100L50ConfigPage,
    PWUXConfigPage,
)


class SettingMainView(QWidget):
    """設定タブの見た目制御"""

    # === 要素
    _main_layout: QVBoxLayout

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

    # === シグナル
    load_requested = Signal()
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._init_ui()
        self._init_connect()

    def _init_ui(self) -> None:
        self._main_layout = QVBoxLayout(self)

        self._main_layout.addWidget(self._header_panel())
        self._main_layout.addWidget(self._main_panel())

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

    def _init_connect(self) -> None:
        self.btn_load.clicked.connect(self.load_requested.emit)
        self.btn_save.clicked.connect(self.save_requested.emit)
        # サイドとページの一致処理
        self.sidebar_widget.currentRowChanged.connect(self.stack_widget.setCurrentIndex)

    # =============================================================================

    def get_full_config(self) -> AppConfig:
        common_config = self.general_page.get_config()
        devices_config = DevicesConfig(
            gm10=self.gm10_page.get_config(),
            hps=self.hps_page.get_config(),
            aps=self.aps_page.get_config(),
            ibeam=self.ibeam_page.get_config(),
            pwux=self.pwux_page.get_config(),
        )

        return AppConfig(common=common_config, devices=devices_config)

    def set_full_config(self, config: AppConfig) -> None:
        self.general_page.set_config(config.common)

        self.gm10_page.set_config(config.devices.gm10)
        self.hps_page.set_config(config.devices.hps)
        self.aps_page.set_config(config.devices.aps)
        self.ibeam_page.set_config(config.devices.ibeam)
        self.pwux_page.set_config(config.devices.pwux)
