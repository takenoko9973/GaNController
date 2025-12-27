from enum import Enum
from typing import TYPE_CHECKING

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator
from PySide6.QtWidgets import QVBoxLayout, QWidget

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

        # データの保持用
        self.x_data: list[float] = []
        self.left_data: dict[str, list[float]] = {}
        self.right_data: dict[str, list[float]] = {}

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

        # ラインオブジェクトの辞書 (再描画の高速化用)
        self.lines_left: dict[str, plt.Line2D] = {}
        self.lines_right: dict[str, plt.Line2D] = {}

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

    def add_line(self, name: str, label_name: str, color: str, is_right_axis: bool = False) -> None:
        """プロットするラインを登録"""
        axis = self.ax_right if is_right_axis else self.ax_left
        lines_dict = self.lines_right if is_right_axis else self.lines_left
        data_dict = self.right_data if is_right_axis else self.left_data

        # ラインを作成して保持
        data_dict[name] = []
        (line,) = axis.plot([], [], label=label_name, color=color, linewidth=1.5)
        lines_dict[name] = line

        # 凡例を統合して表示
        self._update_legend()

    def _update_legend(self) -> None:
        """左右の軸の凡例をまとめて表示"""
        lines1, labels1 = self.ax_left.get_legend_handles_labels()
        lines2, labels2 = self.ax_right.get_legend_handles_labels()
        # 凡例
        self.ax_left.legend(
            lines1 + lines2, labels1 + labels2, loc="upper right", fontsize="x-small"
        )

    def clear_data(self) -> None:
        """ラインを削除し、初期状態に戻す"""
        # x軸データ
        self.x_data.clear()

        # 左軸ライン
        for line in self.lines_left.values():
            line.remove()
        self.lines_left.clear()
        self.left_data.clear()

        # 右軸ライン
        for line in self.lines_right.values():
            line.remove()
        self.lines_right.clear()
        self.right_data.clear()

        self.canvas.draw()

    def update_point(self, x_val: float, values: dict[str, float]) -> None:
        """新しいデータを一点追加して再描画"""
        self.x_data.append(x_val)

        # データの追加
        for name, val in values.items():
            if name in self.left_data:
                self.left_data[name].append(val)
            elif name in self.right_data:
                self.right_data[name].append(val)

        # 描画データの更新 (set_dataは高速)
        for name, line in self.lines_left.items():
            line.set_data(self.x_data, self.left_data[name])

        for name, line in self.lines_right.items():
            line.set_data(self.x_data, self.right_data[name])

        # 軸のスケール調整
        self.ax_left.relim()
        self.ax_left.autoscale_view()
        self.ax_right.relim()
        self.ax_right.autoscale_view()

        self.canvas.draw()
