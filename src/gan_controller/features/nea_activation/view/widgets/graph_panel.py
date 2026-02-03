from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from gan_controller.common.ui.widgets import AxisScale, DualAxisGraph
from gan_controller.common.ui.widgets.graph import DisplayMode, GraphData
from gan_controller.features.nea_activation.schemas import NEARunnerResult


class NEAGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

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
        self.graph_pc = DualAxisGraph(
            "Photocurrent",
            "Time (s)",
            "Photocurrent (A)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
            left_display=DisplayMode.EXPONENTIAL,
            legend_location="upper left",
        )
        self.graph_pc.setMinimumWidth(500)
        self.graph_pc.setMinimumHeight(300)

        self.graph_qe = DualAxisGraph(
            "Quantum Efficiency",
            "Time (s)",
            "Quantum Efficiency (%)",
            "Pressure (Pa)",
            right_scale=AxisScale.LOG,
            left_display=DisplayMode.EXPONENTIAL,
            legend_location="upper left",
        )
        self.graph_qe.setMinimumWidth(500)
        self.graph_qe.setMinimumHeight(300)

        layout.addWidget(self.graph_pc)
        layout.addSpacing(10)
        layout.addWidget(self.graph_qe)

        self._init_lines()

        # 範囲初期化
        self._on_update_graph_settings()

    def _init_lines(self) -> None:
        """グラフにプロットする線を定義"""
        # PC Graph
        self.graph_pc.add_line(
            "pc", "Photocurrent", "blue", marker="o", line_style="None", is_right_axis=False
        )
        self.graph_pc.add_line("pres", "Pressure", "black", is_right_axis=True)

        # QE Graph
        self.graph_qe.add_line(
            "qe", "QE", "green", marker="o", line_style="None", is_right_axis=False
        )
        self.graph_qe.add_line("pres", "Pressure", "black", is_right_axis=True)

    def clear_graph(self) -> None:
        """グラフデータをクリアして再初期化"""
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
            x_val=t.base_value,
            values={
                "pc": pc_val,
                "pres": result.ext_pressure.base_value,
            },
        )
        self._history_qe.append_point(
            x_val=t.base_value,
            values={
                "qe": qe_val,
                "pres": result.ext_pressure.base_value,
            },
        )

        # グラフ更新
        self.graph_pc.set_data(self._history_pc)
        self.graph_qe.set_data(self._history_qe)

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

        self.graph_pc.set_x_window(val)
        self.graph_qe.set_x_window(val)
