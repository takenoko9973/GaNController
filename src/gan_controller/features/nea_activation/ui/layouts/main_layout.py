from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from .condition_setting_panel import NEAActConditionSettingsPanel
from .execution_panel import NEAActExecutionPanel
from .graph_panel import NEAActGraphPanel
from .log_setting_panel import NEAActLogSettingPanel
from .measure_panel import NEAActMeasurePanel


class NEAMainLayout(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()

        self.addWidget(self._left_panel())
        self.addWidget(self._right_panel())

    def _left_panel(self) -> QFrame:
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(400)

        left_layout = QVBoxLayout(left_panel)

        self.condition_setting_panel = NEAActConditionSettingsPanel()
        self.log_setting_panel = NEAActLogSettingPanel()
        self.measure_panel = NEAActMeasurePanel()
        self.execution_panel = NEAActExecutionPanel()

        left_layout.addWidget(self.condition_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.log_setting_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.measure_panel)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.execution_panel)
        left_layout.addStretch()

        return left_panel

    def _right_panel(self) -> QFrame:
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setMinimumWidth(540)

        right_layout = QVBoxLayout(right_panel)

        self.graph_panel = NEAActGraphPanel()

        right_layout.addWidget(self.graph_panel)

        return right_panel
