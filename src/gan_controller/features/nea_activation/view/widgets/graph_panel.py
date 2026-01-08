from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from gan_controller.common.ui.widgets import AxisScale, DualAxisGraph
from gan_controller.features.nea_activation.schemas import NEARunnerResult


class NEAGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # === 表示設定
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # グラフ表示幅
        self.time_window_spin = QSpinBox(minimum=0, maximum=99999, value=1800, suffix=" s")
        self.time_window_spin.setSpecialValueText("全期間")  # 0の時のテキスト
        setting_layout.addWidget(QLabel("表示範囲 (0s=全表示) :"))
        setting_layout.addWidget(self.time_window_spin)

        self.time_window_spin.valueChanged.connect(self._on_time_window_changed)  # 変更時、即時反映

        layout.addLayout(setting_layout)

        # === グラフ
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

        # 範囲初期化
        self._on_time_window_changed(self.time_window_spin.value())

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

    def update_graph(self, result: NEARunnerResult) -> None:
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

    @Slot(int)
    def _on_time_window_changed(self, window_sec: int) -> None:
        """グラフの表示幅を設定する (0以下の場合は全表示)"""
        val = float(window_sec) if window_sec > 0 else None

        self.graph_photocurrent.set_x_window(val)
        self.graph_qe.set_x_window(val)
