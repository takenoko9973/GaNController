from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from gan_controller.features.nea_activation.view.widgets import (
    NEAActExecutionPanel,
    NEAActGraphPanel,
    NEAActLogSettingPanel,
    NEAActMeasurePanel,
)
from gan_controller.features.nea_activation.view.widgets.condition_setting_panel import (
    NEAActConditionSettingsPanel,
)


class NEAActivationWidget(QWidget):
    # 左パネル
    # sequences_panel: SequencesPanel
    log_setting_panel: NEAActLogSettingPanel
    execution_panel: NEAActExecutionPanel

    # 右パネル
    graph_panel: NEAActGraphPanel

    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

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
