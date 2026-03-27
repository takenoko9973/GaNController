import math

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from gan_controller.features.nea_activation.domain.models import NEAExperimentResult
from gan_controller.presentation.components.widgets import (
    DualAxisGraph,
    GraphData,
    SignificantFigureSpinBox,
)


class NEAGraphPanel(QWidget):
    """実行制御およびモニタリング表示用ウィジェット"""

    QE_AXIS_MODE_NORMAL = "normal"
    QE_AXIS_MODE_VISIBLE_MAX = "visible_max"
    QE_AXIS_MODE_FIXED_MAX = "fixed_max"

    QE_SAFE_FALLBACK_MAX = 1.0

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
        self.time_window_spin = QSpinBox(minimum=0, maximum=180, value=10, suffix=" min")
        self.time_window_spin.setSpecialValueText("全期間")  # 0の時のテキスト
        # タイピング中は値を更新せず、Enterキー押下かフォーカス外れ時のみ更新
        self.time_window_spin.setKeyboardTracking(False)
        self.time_window_spin.valueChanged.connect(self._on_update_graph_settings)

        setting_layout.addWidget(QLabel("表示範囲 (0 min=全期間) :"))
        setting_layout.addWidget(self.time_window_spin)

        self.qe_axis_mode_combo = QComboBox()
        self.qe_axis_mode_combo.addItem("通常", self.QE_AXIS_MODE_NORMAL)
        self.qe_axis_mode_combo.addItem("表示範囲最大", self.QE_AXIS_MODE_VISIBLE_MAX)
        self.qe_axis_mode_combo.addItem("固定最大", self.QE_AXIS_MODE_FIXED_MAX)
        self.qe_axis_mode_combo.currentIndexChanged.connect(self._on_update_graph_settings)

        self.qe_fixed_max_spin = SignificantFigureSpinBox(sig_figs=3)
        self.qe_fixed_max_spin.setSuffix(" %")
        self.qe_fixed_max_spin.setRange(1e-9, 1e6)
        self.qe_fixed_max_spin.setValue(self.QE_SAFE_FALLBACK_MAX)
        self.qe_fixed_max_spin.setEnabled(False)
        self.qe_fixed_max_spin.valueChanged.connect(self._on_qe_fixed_max_changed)

        setting_layout.addSpacing(12)
        setting_layout.addWidget(QLabel("QE左軸 :"))
        setting_layout.addWidget(self.qe_axis_mode_combo)
        setting_layout.addWidget(QLabel("固定最大 :"))
        setting_layout.addWidget(self.qe_fixed_max_spin)

        layout.addLayout(setting_layout)

        # === グラフ
        self.graph_pc = DualAxisGraph()
        self.graph_pc.setMinimumSize(500, 300)
        self.graph_pc.set_title("Photocurrent")
        self.graph_pc.set_axis_labels(
            x_label="Time (min)", left_label="Photocurrent (A)", right_label="Pressure (Pa)"
        )
        self.graph_pc.set_axis_scale("right", "log")
        self.graph_pc.set_axis_formatter("left", True)
        self.graph_pc.set_legend_location("upper left")

        self.graph_qe = DualAxisGraph()
        self.graph_qe.setMinimumSize(500, 300)
        self.graph_qe.set_title("Quantum Efficiency")
        self.graph_qe.set_axis_labels(
            x_label="Time (min)", left_label="Quantum Efficiency (%)", right_label="Pressure (Pa)"
        )
        self.graph_qe.set_axis_scale("right", "log")
        self.graph_qe.set_axis_formatter("left", True)
        self.graph_qe.set_legend_location("upper left")

        layout.addWidget(self.graph_pc)
        layout.addSpacing(10)
        layout.addWidget(self.graph_qe)

        self._init_lines()

        self._last_qe_axis_mode = self._current_qe_axis_mode()

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
        self._apply_qe_axis_mode()

    def append_data(self, result: NEAExperimentResult) -> None:
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
            x_value=t.value_as("min"),
            y_values={
                "pc": pc_val,
                "pres": result.ext_pressure.base_value,
            },
        )
        self._history_qe.append_point(
            x_value=t.value_as("min"),
            y_values={
                "qe": qe_val,
                "pres": result.ext_pressure.base_value,
            },
        )

        # グラフ更新
        self.graph_pc.update_plot(self._history_pc)
        self.graph_qe.update_plot(self._history_qe)
        self._apply_qe_axis_mode()

    # =============================================================

    @Slot(int)
    def _on_update_graph_settings(self, _value: int = 0) -> None:
        """グラフ表示設定の変更"""
        # 表示幅変更
        window_min = self.time_window_spin.value()
        self._change_time_window(window_min)

        mode = self._current_qe_axis_mode()
        if mode == self.QE_AXIS_MODE_FIXED_MAX and self._last_qe_axis_mode != mode:
            self._initialize_qe_fixed_max()

        self._last_qe_axis_mode = mode
        self._sync_qe_fixed_max_enabled()
        self._apply_qe_axis_mode()

    @Slot(float)
    def _on_qe_fixed_max_changed(self, _value: float) -> None:
        if self._current_qe_axis_mode() == self.QE_AXIS_MODE_FIXED_MAX:
            self._apply_qe_axis_mode()

    def _change_time_window(self, window_min: float) -> None:
        """グラフの表示幅を設定 (0以下の場合は全表示)"""
        val = float(window_min) if window_min > 0 else None

        self.graph_pc.set_visible_x_span(val)
        self.graph_qe.set_visible_x_span(val)

    def _current_qe_axis_mode(self) -> str:
        mode = self.qe_axis_mode_combo.currentData()
        return mode if isinstance(mode, str) else self.QE_AXIS_MODE_NORMAL

    def _sync_qe_fixed_max_enabled(self) -> None:
        self.qe_fixed_max_spin.setEnabled(
            self._current_qe_axis_mode() == self.QE_AXIS_MODE_FIXED_MAX
        )

    def _initialize_qe_fixed_max(self) -> None:
        max_val = self._visible_qe_max()
        safe_max = self._safe_qe_max(max_val)

        self.qe_fixed_max_spin.blockSignals(True)
        self.qe_fixed_max_spin.setValue(safe_max)
        self.qe_fixed_max_spin.blockSignals(False)

    def _apply_qe_axis_mode(self) -> None:
        mode = self._current_qe_axis_mode()

        if mode == self.QE_AXIS_MODE_NORMAL:
            self.graph_qe.ax_left.set_autoscaley_on(True)
            if not self._history_qe.get_data().empty:
                self.graph_qe.update_plot(self._history_qe)
            return

        self.graph_qe.ax_left.set_autoscaley_on(False)
        if mode == self.QE_AXIS_MODE_VISIBLE_MAX:
            y_max = self._visible_qe_max()
        else:
            y_max = self.qe_fixed_max_spin.value()

        self.graph_qe.ax_left.set_ylim(0.0, self._safe_qe_max(y_max))
        self.graph_qe.canvas.draw_idle()

    def _visible_qe_max(self) -> float | None:
        df = self._history_qe.get_data()
        if df.empty or "x" not in df.columns or "qe" not in df.columns:
            return None

        view_df = df
        window_min = self.time_window_spin.value()
        if window_min > 0:
            max_x = float(df["x"].iloc[-1])
            min_x = max_x - float(window_min)
            view_df = df[df["x"] >= min_x]

        values: list[float] = []
        for raw in view_df["qe"].to_list():
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if math.isfinite(val) and val > 0:
                values.append(val)

        if not values:
            return None

        return max(values)

    def _safe_qe_max(self, value: float | None) -> float:
        if value is None or not math.isfinite(value) or value <= 0:
            return self.QE_SAFE_FALLBACK_MAX
        return value
