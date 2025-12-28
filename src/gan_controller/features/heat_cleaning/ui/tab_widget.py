from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

from .layouts import HCMainLayout


class HeatCleaningTab(QWidget):
    # model: HCModel
    # controller: HCController

    main_layout: HCMainLayout

    # ショートカット
    shortcut_save: QShortcut
    shortcut_save_as: QShortcut

    # シグナル
    save_overwrite_requested = Signal()  # 通常保存
    save_as_requested = Signal()  # 名前をつけて保存

    def __init__(self) -> None:
        super().__init__()

        # self.model = ExperimentAModel()
        # self.controller = ExperimentAController(self.model)

        self.main_layout = HCMainLayout()
        self.setLayout(self.main_layout)

        self._init_connect()

    def _init_connect(self) -> None:
        self._init_shortcuts()

    def _init_shortcuts(self) -> None:
        """ショートカットキーの設定"""
        # Ctrl+S -> 上書き保存
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_overwrite_requested.emit)

        # Ctrl+Shift+S -> 名前を付けて保存
        self.shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_as.activated.connect(self.save_as_requested.emit)
