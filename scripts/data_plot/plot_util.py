from dataclasses import dataclass

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import AutoMinorLocator


@dataclass
class PlotInfo:
    data: pd.Series
    axis: str = "left"
    label: str = ""
    color: str | None = None
    style: str = "-"


def plot_twinx_multi_y(
    x: pd.Series,
    plot_info_list: list[PlotInfo],
    size: tuple[int, int],
    xlabel: str,
    ylabel1: str,
    ylabel2: str = "",
    title: str = "",
) -> tuple[plt.Figure, plt.Axes, plt.Axes | None]:
    dpi = 100

    title_fontsize = 10
    label_fontsize = 18  # 軸ラベル (X, Y1, Y2 共通)
    tick_fontsize = 16  # 目盛り数値 (X, Y1, Y2 共通)
    legend_fontsize = 10

    # ==================================================

    fig, ax1 = plt.subplots(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)

    ax2 = None
    if ylabel2 != "":
        ax2 = ax1.twinx()

    # ==================================================

    ax1.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax1.set_xlabel(xlabel, fontsize=label_fontsize)

    ax1.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax1.set_ylabel(ylabel1, fontsize=label_fontsize)
    ax1.tick_params(
        axis="both", which="major", labelsize=tick_fontsize, direction="in", top=True, left=True
    )
    ax1.tick_params(axis="both", which="minor", direction="in", top=True, left=True)

    if ax2 is not None:
        ax2.yaxis.set_minor_locator(AutoMinorLocator(5))
        ax2.set_ylabel(ylabel2, fontsize=label_fontsize)
        ax2.tick_params(which="major", labelsize=tick_fontsize, direction="in", right=True)
        ax2.tick_params(which="minor", direction="in", right=True)

    # ==================================================

    lines = []
    labels = []
    for plot_info in plot_info_list:
        y_data = plot_info.data

        label = plot_info.label
        color = plot_info.color
        style = plot_info.style

        if plot_info.axis == "left":
            (line,) = ax1.plot(x, y_data, linestyle=style, color=color, label=label)
        elif plot_info.axis == "right" and ax2 is not None:
            (line,) = ax2.plot(x, y_data, linestyle=style, color=color, label=label)
        else:
            (line,) = ax1.plot(x, y_data, linestyle=style, color=color, label=label)

        # 凡例のために情報を保存
        lines.append(line)
        if label:
            labels.append(label)

    if len(labels) != 0:
        ax1.legend(lines, labels, loc="best", fontsize=legend_fontsize)

    ax1.set_title(title, fontsize=title_fontsize)
    fig.tight_layout()

    return fig, ax1, ax2
