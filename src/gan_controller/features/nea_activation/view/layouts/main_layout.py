from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from .condition_setting_panel import NEAActConditionSettingsPanel
from .execution_panel import NEAActExecutionPanel
from .graph_panel import NEAActGraphPanel
from .log_setting_panel import NEAActLogSettingPanel
from .measure_panel import NEAActMeasurePanel


class NEAActMainLayout(QHBoxLayout):
    # 左側 (入力欄、装置表示)
    condition_setting_panel: NEAActConditionSettingsPanel
    log_setting_panel: NEAActLogSettingPanel
    measure_panel: NEAActMeasurePanel
    execution_panel: NEAActExecutionPanel
    # 右側 (グラフ)
    graph_panel: NEAActGraphPanel

    def __init__(self) -> None:
        super().__init__()

        self.addWidget(self._left_panel())
        self.addWidget(self._right_panel())

    def _left_panel(self) -> QFrame:
        """左側 (設定値、制御) レイアウト"""
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(400)

        left_layout = QVBoxLayout(left_panel)

        self.condition_setting_panel = NEAActConditionSettingsPanel()
        self.log_setting_panel = NEAActLogSettingPanel()
        self.execution_panel = NEAActExecutionPanel()
        self.measure_panel = NEAActMeasurePanel()

        left_layout.addWidget(self.condition_setting_panel)
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

        self.graph_panel = NEAActGraphPanel()

        right_layout.addWidget(self.graph_panel)

        return right_panel
