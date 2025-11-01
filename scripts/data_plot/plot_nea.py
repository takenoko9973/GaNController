import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from heater_amd_controller.utils.log_file import LogFile
from scripts.data_plot.base_plotter import BasePlotter

from .plot_util import AxisSide, PlotInfo, ScaleEnum


@dataclass
class EventSpan:
    def __init__(
        self,
        event_name: str,
        start_sec: float,
        end_sec: float,
        label: str | None = None,
        label_dx_sec: float = 0.0,  # ラベルの左右のずらし距離
        label_y: float = 0.95,  # ラベルの高さ (0.0, 1.0)
    ) -> None:
        self.event_name = event_name
        self.start = start_sec
        self.end = end_sec
        self.label = label
        self.label_dx_sec = label_dx_sec
        self.label_y = label_y

    @property
    def center(self) -> float:
        return (self.start + self.end) / 2.0


@dataclass
class EventColor:
    def __init__(self, event_name: str, color: str) -> None:
        self.event_name = event_name
        self.color = color


class NEAPlotter(BasePlotter):
    def __init__(
        self,
        logfile: LogFile,
        save_dir: Path,
        event_spans: list[EventSpan],
        event_colors: list[EventColor],
        overwrite: bool = False,
    ) -> None:
        super().__init__(logfile, save_dir, overwrite)
        self.event_spans = event_spans
        self.event_colors = event_colors

    @property
    def time_axis(self) -> pd.Series:
        return self.log_df["Time[s]"] / 60  # minute

    def plot(self) -> None:
        self.plot_photocurrent()

    def plot_photocurrent(self) -> None:
        df = self.log_df

        # nea_current = re.sub(r"[\[\]]", "", self.conditions["Condition"]["HC_CURRENT"])

        pc_plot_info = PlotInfo(
            df["PC[A]"], AxisSide.LEFT, "Photocurrent", "green", style="--", scale=ScaleEnum.LOG
        )
        pressure_plot_info = PlotInfo(
            df["Pressure(EXT)[Pa]"], AxisSide.RIGHT, "Pressure(EXT)", "black", scale=ScaleEnum.LOG
        )
        plot_info_list = [pc_plot_info, pressure_plot_info]

        min_expo, max_expo = math.log10(df["PC[A]"].min()), math.log10(df["PC[A]"].max())
        self._plot_save(
            f"{self.logfile.path.stem}.svg",
            plot_info_list,
            "Time (min)",
            "Photocurrent (A)",
            "Pressure (Pa)",
            ylim_left=(10 ** math.floor(min_expo), 10 ** math.ceil(max_expo)),
            ylim_right=(1e-9, 1e-5),
        )

    def _plot_save(
        self,
        filename: str,
        plot_info_list: list[PlotInfo],
        xlabel: str,
        ylabel_left: str,
        ylabel_right: str | None = None,
        ylim_left: tuple[float, float] | None = None,
        ylim_right: tuple[float, float] | None = None,
        plot_size: tuple[int, int] = (900, 500),
    ) -> None:
        if self._should_skip(filename):
            return

        fig, ax1, _ = self._plot_generate(
            plot_info_list, xlabel, ylabel_left, ylabel_right, ylim_left, ylim_right, plot_size
        )

        # イベント領域を追加
        for event_span in self.event_spans:
            match_color = next(
                filter(
                    lambda event_color: event_color.event_name == event_span.event_name,
                    self.event_colors,
                ),
                None,
            )

            if match_color is None:
                print(f"[Warning] No event_color exists for event_span ({event_span})")
                continue

            # 領域
            ax1.axvspan(
                event_span.start / 60, event_span.end / 60, color=match_color.color, alpha=0.1
            )

            # ラベル
            if event_span.label is not None:
                ax1.text(
                    (event_span.center + event_span.label_dx_sec) / 60,
                    event_span.label_y,
                    event_span.label,
                    color=match_color.color,
                    fontsize=16,
                    ha="center",
                    va="top",
                    transform=ax1.get_xaxis_transform(),  # xはデータ座標, yは軸比率(0〜1)
                )

        fig.tight_layout()
        self._save_figure(fig, filename)
