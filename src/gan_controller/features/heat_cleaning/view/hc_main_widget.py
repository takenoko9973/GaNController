from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from gan_controller.features.heat_cleaning.view.widgets import (
    HCExecutionPanel,
    HCGraphPanel,
    HCLogSettingPanel,
    ProtocolSelectorPanel,
    SequencesPanel,
)


class HeatCleaningWidget(QWidget):
    # 左パネル
    protocol_select_panel: ProtocolSelectorPanel
    sequences_panel: SequencesPanel
    log_setting_panel: HCLogSettingPanel
    execution_panel: HCExecutionPanel

    # 右パネル
    graph_panel: HCGraphPanel

    # ============================================================

    # ショートカット
    shortcut_save: QShortcut
    shortcut_save_as: QShortcut

    # シグナル
    save_overwrite_requested = Signal()  # 通常保存
    save_as_requested = Signal()  # 名前をつけて保存

    def __init__(self) -> None:
        super().__init__()
        self.init_shortcuts()
        self.init_ui()

    def init_shortcuts(self) -> None:
        """ショートカットキーの設定"""
        # Ctrl+S -> 上書き保存
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_overwrite_requested.emit)

        # Ctrl+Shift+S -> 名前を付けて保存
        self.shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_as.activated.connect(self.save_as_requested.emit)

    def init_ui(self) -> None:
        # メインのレイアウト (左右分割)
        main_layout = QHBoxLayout(self)

        main_layout.addWidget(self._left_panel())
        main_layout.addWidget(self._right_panel())

    def _left_panel(self) -> QFrame:
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(400)

        left_layout = QVBoxLayout(left_panel)

        self.protocol_select_panel = ProtocolSelectorPanel()
        self.sequences_panel = SequencesPanel()
        self.log_setting_panel = HCLogSettingPanel()
        self.execution_panel = HCExecutionPanel()

        left_layout.addLayout(self.protocol_select_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.sequences_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.log_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.execution_panel)
        left_layout.addStretch()

        return left_panel

    def _right_panel(self) -> QFrame:
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setMinimumWidth(540)

        right_layout = QVBoxLayout(right_panel)

        self.graph_panel = HCGraphPanel()

        right_layout.addWidget(self.graph_panel)

        return right_panel
