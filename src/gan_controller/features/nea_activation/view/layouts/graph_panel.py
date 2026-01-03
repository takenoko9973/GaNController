from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.widgets.graph import AxisScale, DualAxisGraph


class NEAActGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.graph_photocurrent = DualAxisGraph(
            "Photocurrent",
            "Time (s)",
            "Photocurrent (A)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_photocurrent.setMinimumWidth(500)
        self.graph_photocurrent.setMinimumHeight(300)

        self.graph_qe = DualAxisGraph(
            "Quantum Efficiency",
            "Time (s)",
            "QE (%)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
        )
        self.graph_qe.setMinimumWidth(500)
        self.graph_qe.setMinimumHeight(300)

        layout.addWidget(self.graph_photocurrent)
        layout.addSpacing(10)
        layout.addWidget(self.graph_qe)
