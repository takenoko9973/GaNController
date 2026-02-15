from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from gan_controller.features.nea_activation.domain.models import NEARunnerResult
from gan_controller.presentation.components.widgets import DualAxisGraph, GraphData


class NEAGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    _history_pc: GraphData
    _history_qe: GraphData

    graph_pc: DualAxisGraph
    graph_qe: DualAxisGraph

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # 履歴データ (全データ) をここに保持
        self._history_pc = GraphData()
        self._history_qe = GraphData()

        layout = QVBoxLayout(self)

        # === 表示設定
        setting_layout = QHBoxLayout()
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # グラフ表示幅
        self.time_window_spin = QSpinBox(minimum=0, maximum=99999, value=600, suffix=" s")
        self.time_window_spin.setSpecialValueText("全期間")  # 0の時のテキスト
        self.update_window_button = QPushButton("更新")
        setting_layout.addWidget(QLabel("表示範囲 (0s=全表示) :"))
        setting_layout.addWidget(self.time_window_spin)
        setting_layout.addWidget(self.update_window_button)

        # ボタンを押すと反映
        self.update_window_button.clicked.connect(self._on_update_graph_settings)

        layout.addLayout(setting_layout)

        # === グラフ
        self.graph_pc = DualAxisGraph()
        self.graph_pc.setMinimumSize(500, 300)
        self.graph_pc.set_title("Photocurrent")
        self.graph_pc.set_axis_labels(
            x_label="Time (s)", left_label="Photocurrent (A)", right_label="Pressure (Pa)"
        )
        self.graph_pc.set_axis_scale("right", "log")
        self.graph_pc.set_axis_formatter("left", True)
        self.graph_pc.set_legend_location("upper left")

        self.graph_qe = DualAxisGraph()
        self.graph_qe.setMinimumSize(500, 300)
        self.graph_qe.set_title("Quantum Efficiency")
        self.graph_qe.set_axis_labels(
            x_label="Time (s)", left_label="Quantum Efficiency (%)", right_label="Pressure (Pa)"
        )
        self.graph_qe.set_axis_scale("right", "log")
        self.graph_qe.set_axis_formatter("left", True)
        self.graph_qe.set_legend_location("upper left")

        layout.addWidget(self.graph_pc)
        layout.addSpacing(10)
        layout.addWidget(self.graph_qe)

        self._init_lines()

        # 範囲初期化
        self._on_update_graph_settings()

    def _init_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # PC Graph
        self.graph_pc.add_series(
            "pc", "left", "blue", marker="o", linestyle="None", legend_label="Photocurrent"
        )
        self.graph_pc.add_series("pres", "right", "black", legend_label="Pressure")

        # QE Graph
        self.graph_qe.add_series(
            "qe", "left", "green", marker="o", linestyle="None", legend_label="QE"
        )
        self.graph_qe.add_series("pres", "right", "black", legend_label="Pressure")

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
        self._history_pc = GraphData()
        self._history_qe = GraphData()

        self.graph_pc.clear_view()
        self.graph_qe.clear_view()

        self._init_lines()  # ライン再設定

    def append_data(self, result: NEARunnerResult) -> None:
        t = result.timestamp

        # PC, QE が負の場合は描画しない
        pc_val = result.photocurrent.base_value
        if pc_val <= 0:
            pc_val = float("nan")

        qe_val = result.quantum_efficiency.value_as("%")
        if qe_val <= 0:
            qe_val = float("nan")

        #  データ追加
        self._history_pc.append_point(
            x_value=t.base_value,
            y_values={
                "pc": pc_val,
                "pres": result.ext_pressure.base_value,
            },
        )
        self._history_qe.append_point(
            x_value=t.base_value,
            y_values={
                "qe": qe_val,
                "pres": result.ext_pressure.base_value,
            },
        )

        # グラフ更新
        self.graph_pc.update_plot(self._history_pc)
        self.graph_qe.update_plot(self._history_qe)

    # =============================================================

    @Slot(int)
    def _on_update_graph_settings(self) -> None:
        """グラフ表示設定の変更"""
        # 表示幅変更
        window_sec = self.time_window_spin.value()
        self._change_time_window(window_sec)

    def _change_time_window(self, window_sec: float) -> None:
        """グラフの表示幅を設定 (0以下の場合は全表示)"""
        val = float(window_sec) if window_sec > 0 else None

        self.graph_pc.set_visible_x_span(val)
        self.graph_qe.set_visible_x_span(val)
