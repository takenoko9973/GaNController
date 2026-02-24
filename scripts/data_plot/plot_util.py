from dataclasses import dataclass
from enum import Enum

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import AutoMinorLocator


@dataclass
class PlotStyleConfig:
    """グラフのスタイル設定を保持するデータクラス"""

    size: tuple[int, int] = (900, 500)
    dpi: int = 100
    title_fontsize: int = 10
    label_fontsize: int = 18
    tick_fontsize: int = 16
    legend_fontsize: int = 10


class AxisSide(Enum):
    LEFT = "left"
    RIGHT = "right"


class ScaleEnum(Enum):
    LINEAR = "linear"
    LOG = "log"


@dataclass
class PlotInfo:
    data: pd.Series
    axis: AxisSide = AxisSide.LEFT
    label: str = ""
    color: str | None = None
    style: str = "-"
    scale: ScaleEnum = ScaleEnum.LINEAR


class GraphBuilder:
    def __init__(self, style_config: PlotStyleConfig | None = None) -> None:
        self.style = style_config or PlotStyleConfig()

        self.fig, self.ax1 = plt.subplots(
            figsize=(self.style.size[0] / self.style.dpi, self.style.size[1] / self.style.dpi),
            dpi=self.style.dpi,
        )
        self.ax2: plt.Axes | None = None

        # 1軸目 (左) の初期設定
        self._setup_axis(self.ax1)
        self.ax1.tick_params(
            axis="both",
            which="major",
            labelsize=self.style.tick_fontsize,
            direction="in",
            top=True,
            left=True,
        )
        self.ax1.tick_params(axis="both", which="minor", direction="in", top=True, left=True)

        # 凡例用の保持リスト
        self.lines = []
        self.labels = []

        self._base_ylim: dict[AxisSide, tuple[float, float] | None] = {
            AxisSide.LEFT: None,
            AxisSide.RIGHT: None,
        }

    def _setup_axis(self, ax: plt.Axes) -> None:
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))

    def get_ax2(self) -> plt.Axes:
        """右軸を遅延生成"""
        if self.ax2 is None:
            self.ax2 = self.ax1.twinx()
            self._setup_axis(self.ax2)
            self.ax2.tick_params(
                which="major", labelsize=self.style.tick_fontsize, direction="in", right=True
            )
            self.ax2.tick_params(which="minor", direction="in", right=True)
        return self.ax2

    def set_labels(self, xlabel: str, ylabel_left: str, ylabel_right: str = "") -> None:
        self.ax1.set_xlabel(xlabel, fontsize=self.style.label_fontsize)
        self.ax1.set_ylabel(ylabel_left, fontsize=self.style.label_fontsize)
        if ylabel_right:
            ax2 = self.get_ax2()
            ax2.set_ylabel(ylabel_right, fontsize=self.style.label_fontsize)

    def set_title(self, title: str) -> None:
        self.ax1.set_title(title, fontsize=self.style.title_fontsize)

    def set_xlim(self, xmin: float, xmax: float) -> None:
        self.ax1.set_xlim(xmin, xmax)

    def set_base_ylim(self, side: AxisSide, ymin: float, ymax: float) -> None:
        """最低限確保する描画範囲のベースラインを設定する"""
        self._base_ylim[side] = (ymin, ymax)

    def set_yscale(self, side: AxisSide, scale: str) -> None:
        target_ax = self.ax1 if side == AxisSide.LEFT else self.get_ax2()
        target_ax.set_yscale(scale)

    def add_plot(self, x_data: pd.Series, plot_info: PlotInfo) -> None:
        """1系列分のデータをプロットする"""
        target_ax = self.ax1 if plot_info.axis == AxisSide.LEFT else self.get_ax2()

        (line,) = target_ax.plot(
            x_data,
            plot_info.data,
            plot_info.style,
            color=plot_info.color,
            label=plot_info.label,
        )

        self.lines.append(line)
        if plot_info.label:
            self.labels.append(plot_info.label)

    def adjust_axes_limits(self) -> None:
        """Y軸の最終的な描画範囲を計算して確定させる"""
        for side in [AxisSide.LEFT, AxisSide.RIGHT]:
            ax = self.ax1 if side == AxisSide.LEFT else self.ax2
            if ax is None or self._base_ylim[side] is None:
                continue

            ymin_base, ymax_base = self._base_ylim[side]  # ty:ignore[not-iterable]
            ymin_auto, ymax_auto = ax.get_ylim()

            final_ymin = min(ymin_base, ymin_auto)
            final_ymax = max(ymax_base, ymax_auto)

            ax.set_ylim(final_ymin, final_ymax)

    def finalize(self) -> plt.Figure:
        """すべての要素を合成し、Figureを完成させる"""
        self.adjust_axes_limits()  # 軸の確定をここでも呼ぶ (複数回呼んでも問題ない設計)

        if self.labels:
            self.ax1.legend(
                self.lines, self.labels, loc="best", fontsize=self.style.legend_fontsize
            )
        self.fig.tight_layout()

        return self.fig
