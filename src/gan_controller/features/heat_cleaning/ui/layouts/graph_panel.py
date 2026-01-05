from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.widgets.graph import AxisScale, DualAxisGraph


class HCGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.graph_power = DualAxisGraph(
            "Power",
            "Time (h)",
            "Temperature (°C)",
            "Power (W)",
        )
        self.graph_power.setMinimumWidth(500)
        self.graph_power.setMinimumHeight(300)

        self.graph_pressure = DualAxisGraph(
            "Pressure",
            "Time (h)",
            "Temperature (°C)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_pressure.setMinimumWidth(500)
        self.graph_pressure.setMinimumHeight(300)

        layout.addWidget(self.graph_power)
        layout.addSpacing(10)
        layout.addWidget(self.graph_pressure)
