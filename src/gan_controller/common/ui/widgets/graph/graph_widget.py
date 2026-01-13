from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .graph_data import GraphData

if TYPE_CHECKING:
    from matplotlib.lines import Line2D


class DebouncedFigureCanvas(FigureCanvas):
    """リサイズ時の再描画を遅延させ、ウィンドウ操作を軽量化するCanvas"""

    def __init__(self, figure: Figure) -> None:
        super().__init__(figure)

        # 遅延実行用のタイマー
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        # 100ms待機 (サイズ変更から規定の時間経ったら、グラフ再描画)
        self._resize_timer.setInterval(100)
        self._resize_timer.timeout.connect(self._perform_delayed_resize)

        # 最新の「サイズ」を保持
        self._pending_size: QSize | None = None

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """グラフ描画を即時実行せず、QWidgetのサイズ変更だけ先に行って描画を予約する"""
        # サイズ情報を保存
        self._pending_size = event.size()

        # QtのWidgetとしてのサイズ変更は即座に行う
        QWidget.resizeEvent(self, event)

        # タイマーをリセット (サイズ変更からの時間計測)
        self._resize_timer.start()

    def _perform_delayed_resize(self) -> None:
        """タイマー発火後に呼ばれる描画処理"""
        if self._pending_size:
            # 保存しておいたサイズから、新しいイベントオブジェクトを作成
            dummy_old_size = QSize()  # 空白で良い
            new_event = QResizeEvent(self._pending_size, dummy_old_size)

            # Matplotlibの親クラスのresizeEventを呼び出す
            super().resizeEvent(new_event)


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
        legend_location: str = "upper right",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.model = GraphData()

        # Matplotlibの初期化
        self.fig = Figure(figsize=(5, 4), dpi=100, layout="constrained")  # constrainedで自動調整
        self.canvas = DebouncedFigureCanvas(self.fig)

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
        self.lines_left: dict[str, Line2D] = {}
        self.lines_right: dict[str, Line2D] = {}

        # 凡例の場所
        self.legend_location = legend_location

    def _sci_mathtext(self, x, _) -> str:  # noqa: ANN001
        if x == 0:
            return r"$0$"
        exp = int(np.floor(np.log10(abs(x))))
        mant = x / 10**exp
        return rf"${mant:.1f} \times 10^{{{exp}}}$"

    # ---------- Controller ----------

    def set_x_window(self, x_window: float | None) -> None:
        """グラフのX軸の表示幅を設定する。

        parameter:
            x_window (float | None): x軸の表示幅。データが増えると自動でスライドする。
                                           Noneの場合は全範囲を表示する。
        """
        self._x_window = x_window
        self._render()  # 設定変更を即時反映

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
        line_style: str | None = None,
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
        if line_style is not None:
            plot_kwargs["linestyle"] = line_style

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

        # スライド表示 (Time Window) の適用
        if self._x_window is not None and len(self.model.x) > 0:
            latest_x = self.model.x[-1]

            # データが足りてない場合は自動拡大
            # 幅を超えている場合のみスライド
            min_x = max(latest_x - self._x_window, 0)
            max_x = latest_x

            self.ax_left.set_xlim(min_x, max_x)
            self.ax_right.set_xlim(min_x, max_x)
        elif self._x_window is None:
            max_x = max(self.model.x)
            min_x = 0

            self.ax_left.set_xlim(min_x, max_x)
            self.ax_right.set_xlim(min_x, max_x)

        self.canvas.draw()

    def _update_legend(self) -> None:
        l1, lab1 = self.ax_left.get_legend_handles_labels()
        l2, lab2 = self.ax_right.get_legend_handles_labels()
        self.ax_left.legend(l1 + l2, lab1 + lab2, loc=self.legend_location, fontsize="x-small")
