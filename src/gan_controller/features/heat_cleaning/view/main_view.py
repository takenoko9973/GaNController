from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from gan_controller.features.heat_cleaning.schemas.config import ProtocolConfig
from gan_controller.features.heat_cleaning.schemas.result import HCRunnerResult
from gan_controller.features.heat_cleaning.view.widgets import (
    HCConditionPanel,
    HCExecutionPanel,
    HCGraphPanel,
    HCLogSettingPanel,
    HCMeasurePanel,
    HCProtocolSelectorPanel,
)


class HeatCleaningMainView(QWidget):
    # === 要素
    _main_layout: QHBoxLayout

    # 左側 (入力欄、装置表示)
    protocol_select_panel: HCProtocolSelectorPanel
    condition_panel: HCConditionPanel
    log_setting_panel: HCLogSettingPanel
    execution_panel: HCExecutionPanel
    measure_panel: HCMeasurePanel
    # 右側 (グラフ)
    graph_panel: HCGraphPanel

    # === シグナル系
    # ショートカット
    shortcut_save: QShortcut
    shortcut_save_as: QShortcut
    # シグナル
    save_action_requested = Signal()  # 通常保存
    save_as_requested = Signal()  # 名前をつけて保存

    def __init__(self) -> None:
        super().__init__()

        self._init_ui()
        self._init_shortcuts()

    def _init_ui(self) -> None:
        self._main_layout = QHBoxLayout(self)
        self.setLayout(self._main_layout)

        self._main_layout.addWidget(self._left_panel())
        self._main_layout.addWidget(self._right_panel())

    def _left_panel(self) -> QFrame:
        """左側 (設定値、制御) レイアウト"""
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(400)

        left_layout = QVBoxLayout(left_panel)

        self.protocol_select_panel = HCProtocolSelectorPanel()
        self.condition_panel = HCConditionPanel()
        self.log_setting_panel = HCLogSettingPanel()
        self.execution_panel = HCExecutionPanel()
        self.measure_panel = HCMeasurePanel()

        left_layout.addLayout(self.protocol_select_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.condition_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.log_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.execution_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.measure_panel)
        left_layout.addStretch()

        return left_panel

    def _right_panel(self) -> QFrame:
        """右側 (グラフ) レイアウト"""
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setMinimumWidth(540)

        right_layout = QVBoxLayout(right_panel)

        self.graph_panel = HCGraphPanel()

        right_layout.addWidget(self.graph_panel)

        return right_panel

    def _init_shortcuts(self) -> None:
        """ショートカットキーの設定"""
        # Ctrl+S -> 上書き保存
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_action_requested.emit)

        # Ctrl+Shift+S -> 名前を付けて保存
        self.shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_as.activated.connect(self.save_as_requested.emit)

    # =============================================================================

    def update_view(self, result: HCRunnerResult) -> None:
        self.measure_panel.update_measure_values(result)
        self.graph_panel.update_graph(result)

    # =============================================================================

    def get_full_config(self) -> ProtocolConfig:
        sequence, condition = self.condition_panel.get_config()
        return ProtocolConfig(
            sequence=sequence,
            condition=condition,
            log=self.log_setting_panel.get_config(),
        )

    def set_full_config(self, config: ProtocolConfig) -> None:
        self.condition_panel.set_config(config.sequence, config.condition)
        self.log_setting_panel.set_config(config.log)
