import sys
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt

from heater_amd_controller.config import Config
from heater_amd_controller.utils.log_file import DateLogDirectory, LogFile, LogManager

from .plot_util import PlotInfo, plot_twinx_multi_y

config_path = Path("config.toml")
config = Config.load_config(config_path)

PLOT_DIR = "plots"


def plot_neghd(logfile: LogFile, save_dir: Path) -> None:
    log_df = pd.read_csv(logfile.path, comment="#", sep="\t")

    time_h = log_df["Time[s]"] / 3600

    heater_plot_info = PlotInfo(
        log_df["Volt[V]"] * log_df["Current[A]"], "left", "NEG power", "chocolate"
    )
    pressure_ext_plot_info = PlotInfo(
        log_df["Pressure(EXT)[Pa]"], "right", "Pressure(EXT) (Pa)", "green"
    )

    plot_info_list = [heater_plot_info, pressure_ext_plot_info]

    # ==================================================================

    fig, ax1, ax2 = plot_twinx_multi_y(
        time_h,
        plot_info_list,
        (900, 500),
        "Time (h)",
        "Power (W)",
        "Pressure (Pa)",
        logfile.path.stem,
    )
    ax1.set_xlim(0, time_h.max())
    ax1.set_ylim(0, 100)
    if ax2:
        ax2.set_yscale("log")
        ax2.set_ylim(1e-9, 1e-3)
    fig.tight_layout()

    plt.savefig(save_dir / (logfile.path.stem + ".svg"), format="svg")
    plt.close(fig)  # メモリを解放
