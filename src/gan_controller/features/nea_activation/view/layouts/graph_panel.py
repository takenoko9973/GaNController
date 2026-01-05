from PySide6.QtWidgets import QVBoxLayout, QWidget

from gan_controller.common.widgets.graph import AxisScale, DualAxisGraph
from gan_controller.features.nea_activation.dtos.nea_result import NEAActivationResult


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

        self._setup_lines()

    def _setup_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # PC Graph
        self.graph_photocurrent.add_line(
            "pc", "Photocurrent", "blue", marker="o", linestyle="None", is_right_axis=False
        )
        self.graph_photocurrent.add_line("pres", "Pressure", "black", is_right_axis=True)

        # QE Graph
        self.graph_qe.add_line(
            "qe", "QE", "green", marker="o", linestyle="None", is_right_axis=False
        )
        self.graph_qe.add_line("pres", "Pressure", "black", is_right_axis=True)

    def update_graph(self, result: NEAActivationResult) -> None:
        t = result.timestamp

        # PC, QE が負の場合は描画しない
        pc_val = result.quantum_efficiency.si_value
        if pc_val <= 0:
            pc_val = float("nan")

        qe_val = result.quantum_efficiency.value_as("%")
        if qe_val <= 0:
            qe_val = float("nan")

        # --- Photocurrent Graph の更新 ---
        # Resultオブジェクトから値を取り出し、辞書形式でグラフに渡す
        self.graph_photocurrent.update_point(
            x_val=t.si_value,
            values={
                "pc": pc_val,
                "pres": result.ext_pressure.si_value,
            },
        )

        # --- QE Graph の更新 ---
        self.graph_qe.update_point(
            x_val=t.si_value,
            values={
                "qe": qe_val,
                "pres": result.ext_pressure.si_value,
            },
        )

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
        self.graph_photocurrent.clear_data()
        self.graph_qe.clear_data()

        self._setup_lines()  # ライン再設定
