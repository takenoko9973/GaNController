import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))
from heater_amd_controller.utils.log_file import LogFile
from scripts.data_plot.plot_util import PlotInfo, plot_twinx_multi_y


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


# ======= Plot Setting =============================================

NEA_log_path = Path("logs/250904/[2.1]NEA-20250917101546.dat")

event_spans: list[EventSpan] = [
    EventSpan("Cs", 97.1, 735.7, label="Cs (3.5A)"),
    EventSpan("O2", 735.7, 745.7),
    # =
    EventSpan("Cs", 880.3, 1374.6),
    EventSpan("O2", 1419.8, 1491.1, label="$\\mathrm{O_2}$"),
    # =
    EventSpan("Cs", 1607.6, 1758.6),
    EventSpan("O2", 1816.8, 1862.2),
    # =
    EventSpan("Cs", 1954.4, 2385.9),
    EventSpan("O2", 2539.8, 2645.6),
    # =
    EventSpan("Cs", 2693.0, 2829.1),
    # =
    # EventSpan("Cs(3.0A)", 4034.4, 4494.1, label="Cs (3.0A)", label_dx_sec=200.0),
    # =================================
    # EventSpan("LaserEngChange", 1191.4, 1415.9, label="Laser \n 3mW → 6mW → 25mW", label_y=0.7),
]

event_colors: list[EventColor] = [
    EventColor("Cs", "red"),
    EventColor("O2", "blue"),
    EventColor("Cs(3.0A)", "orange"),
    EventColor("LaserEngChange", "green"),
]

SAVE_FIG = False

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent


# ==================================================================


def main() -> None:
    log_file = LogFile(NEA_log_path)
    log_df = pd.read_csv(log_file.path, comment="#", sep="\t")

    time_min = log_df["Time[s]"] / 60

    pc_plot_info = PlotInfo(log_df["PC[A]"], "left", "Photocurrent (A)", "green", style="--")
    pressure_plot_info = PlotInfo(
        log_df["Pressure(EXT)[Pa]"], "right", "Pressure(EXT) (Pa)", "black"
    )

    plot_info_list = [pc_plot_info, pressure_plot_info]

    fig, ax1, ax2 = plot_twinx_multi_y(
        time_min,
        plot_info_list,
        (900, 500),
        "Time (min)",
        "Photocurrent (A)",
        "Pressure (Pa)",
        log_file.path.name,
    )
    ax1.set_xlim(0, time_min.max())

    ax1.set_yscale("log")
    ax1.set_ylim(1e-8, 1e-6)
    if ax2:
        ax2.set_yscale("log")
        ax2.set_ylim(1e-9, 1e-5)

    # イベント領域を追加
    for event_span in event_spans:
        match_color = next(
            filter(
                lambda event_color: event_color.event_name == event_span.event_name, event_colors
            ),
            None,
        )

        if match_color is None:
            print(f"[Warning] No event_color exists for event_span ({event_span})")
            continue

        # 領域
        ax1.axvspan(event_span.start / 60, event_span.end / 60, color=match_color.color, alpha=0.1)

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

    parts = list(log_file.path.parent.absolute().relative_to(root_path).parts)
    parts[0] = PLOT_DIR
    save_dir = root_path / Path(*parts)
    save_dir.mkdir(exist_ok=True, parents=True)

    fig.tight_layout()
    plt.show()

    if SAVE_FIG:
        save_path = save_dir / (log_file.path.stem + ".svg")
        plt.savefig(save_path, format="svg")
        print(f"Save graph (path: {save_path})")

    plt.close(fig)  # メモリを解放


if __name__ == "__main__":
    main()
