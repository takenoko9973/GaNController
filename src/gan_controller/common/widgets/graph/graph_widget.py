from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .graph_data import GraphData

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


class AxisScale(Enum):
    """軸のスケール設定"""

    LINEAR = "linear"
    LOG = "log"


class DualAxisGraph(QWidget):
    """2軸データ(左・右) を表示するグラフウィジェット"""

    def __init__(
        self,
        title: str,
        x_label: str,
        left_label: str,
        right_label: str,
        left_scale: AxisScale = AxisScale.LINEAR,
        right_scale: AxisScale = AxisScale.LINEAR,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.model = GraphData()

        # Matplotlibの初期化
        self.fig = Figure(figsize=(5, 4), dpi=100, layout="constrained")  # constrainedで自動調整
        self.canvas = FigureCanvas(self.fig)

        self.ax_left = self.fig.add_subplot(111)
        self.ax_right = self.ax_left.twinx()

        self.ax_left.set_zorder(self.ax_right.get_zorder() + 1)
        self.ax_left.patch.set_visible(False)

        # レイアウト設定
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        # 軸ラベルとタイトルの設定
        self.ax_left.set_title(title, fontsize="x-small")
        self.ax_left.set_xlabel(x_label, fontsize="large")
        self.ax_left.set_ylabel(left_label, fontsize="large")
        self.ax_right.set_ylabel(right_label, fontsize="large")

        self.ax_left.yaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax_left.tick_params(which="major", labelsize="medium", direction="in", top=True)
        self.ax_left.tick_params(which="minor", labelsize="medium", direction="in", top=True)

        self.ax_right.yaxis.set_minor_locator(AutoMinorLocator(5))
        self.ax_right.tick_params(which="major", labelsize="medium", direction="in", top=True)
        self.ax_right.tick_params(which="minor", labelsize="medium", direction="in", top=True)

        self.ax_left.grid(True, linestyle="--", alpha=0.6)

        # スケール設定
        self.ax_left.set_yscale(left_scale.value)
        self.ax_right.set_yscale(right_scale.value)
        # 線形表示の場合、軸の上の方に指数が表示されるため、手動で指定
        if left_scale == AxisScale.LINEAR:
            self.ax_left.yaxis.set_major_formatter(FuncFormatter(self._sci_mathtext))
        if left_scale == AxisScale.LINEAR:
            self.ax_left.yaxis.set_major_formatter(FuncFormatter(self._sci_mathtext))

        # ラインオブジェクトの辞書 (再描画の高速化用)
        self.lines_left: dict[str, plt.Line2D] = {}
        self.lines_right: dict[str, plt.Line2D] = {}

    def _sci_mathtext(self, x, _) -> str:  # noqa: ANN001
        if x == 0:
            return r"$0$"
        exp = int(np.floor(np.log10(abs(x))))
        mant = x / 10**exp
        return rf"${mant:.1f} \times 10^{{{exp}}}$"

    # ---------- Controller ----------

    def set_title(self, title: str) -> None:
        """グラフのタイトルを再設定"""
        self.ax_left.set_title(title, fontsize="x-small")
        self.canvas.draw()

    def set_line_label(self, key_name: str, new_label: str) -> None:
        """凡例表示名を変更"""
        target_line = None

        if key_name in self.lines_left:
            target_line = self.lines_left[key_name]
        elif key_name in self.lines_right:
            target_line = self.lines_right[key_name]

        if target_line:
            target_line.set_label(new_label)
            self._update_legend()

    def add_line(
        self,
        name: str,
        label: str,
        color: str,
        marker: str | None = None,
        linestyle: str | None = None,
        is_right_axis: bool = False,
    ) -> None:
        """プロットするラインを登録"""
        axis = self.ax_right if is_right_axis else self.ax_left
        target = self.model.right if is_right_axis else self.model.left
        lines = self.lines_right if is_right_axis else self.lines_left

        target[name] = []

        # オプション引数
        plot_kwargs = {
            "label": label,
            "color": color,
            "linewidth": 1.5,
        }
        if marker is not None:
            plot_kwargs["marker"] = marker
        if linestyle is not None:
            plot_kwargs["linestyle"] = linestyle

        # kwargsを展開
        (line,) = axis.plot([], [], **plot_kwargs)

        lines[name] = line
        self._update_legend()

    def clear_data(self) -> None:
        self.model.clear()

        for line in self.lines_left.values():
            line.remove()
        for line in self.lines_right.values():
            line.remove()

        self.lines_left.clear()
        self.lines_right.clear()
        self.canvas.draw()

    def update_point(self, x_val: float, values: dict[str, float]) -> None:
        """新しいデータを一点追加して再描画"""
        self.model.append_point(x_val, values)
        self._render()

    # ---------- View ----------

    def _render(self) -> None:
        """データを更新して描画"""
        # 描画データの更新
        for name, line in self.lines_left.items():
            line.set_data(self.model.x, self.model.left[name])
        for name, line in self.lines_right.items():
            line.set_data(self.model.x, self.model.right[name])

        # 軸のスケール調整
        self.ax_left.relim()
        self.ax_left.autoscale_view()
        self.ax_right.relim()
        self.ax_right.autoscale_view()
        self.canvas.draw()

    def _update_legend(self) -> None:
        l1, lab1 = self.ax_left.get_legend_handles_labels()
        l2, lab2 = self.ax_right.get_legend_handles_labels()
        self.ax_left.legend(l1 + l2, lab1 + lab2, loc="upper right", fontsize="x-small")
