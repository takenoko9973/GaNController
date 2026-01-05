from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from .execution_panel import HCExecutionPanel
from .graph_panel import HCGraphPanel
from .log_setting_panel import HCLogSettingPanel
from .protocol_select_panel import ProtocolSelectorPanel
from .sequence_panel import SequencesPanel


class HCMainLayout(QHBoxLayout):
    def __init__(self) -> None:
        super().__init__()

        self.addWidget(self._left_panel())
        self.addWidget(self._right_panel())

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
