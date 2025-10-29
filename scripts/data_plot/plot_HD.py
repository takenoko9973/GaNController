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


def plot_hd(logfile: LogFile, save_dir: Path) -> None:
    log_df = pd.read_csv(logfile.path, comment="#", sep="\t")

    time_h = log_df["Time[s]"] / 3600

    temp_plot_info = PlotInfo(log_df["Temp(TC)[deg.C]"], "left", "TC (℃)", "red")
    heater_plot_info = PlotInfo(
        log_df["Volt[V]"] * log_df["Current[A]"], "right", "Heater power", "orange"
    )

    plot_info_list = [temp_plot_info, heater_plot_info]

    if "Volt(AMD)[V]" in log_df and "Current(AMD)[A]" in log_df:
        amd_plot_info = PlotInfo(
            log_df["Volt(AMD)[V]"] * log_df["Current(AMD)[A]"], "right", "AMD power", "gold"
        )
        plot_info_list.append(amd_plot_info)

    # ==================================================================

    fig, ax1, ax2 = plot_twinx_multi_y(
        time_h,
        plot_info_list,
        (900, 500),
        "Time (h)",
        "Temperature (deg.C)",
        "Power (W)",
        logfile.path.stem,
    )
    ax1.set_xlim(0, time_h.max())
    ax1.set_ylim(0, 800)
    if ax2:
        ax2.set_ylim(0, 15)
    fig.tight_layout()

    plt.savefig(save_dir / (logfile.path.stem + "_power.svg"), format="svg")
    plt.close(fig)  # メモリを解放

    # ===================================================

    pressure_ext_plot_info = PlotInfo(
        log_df["Pressure(EXT)[Pa]"], "right", "Pressure(EXT) (Pa)", "green"
    )

    plot_info_list = [temp_plot_info, pressure_ext_plot_info]

    fig, ax1, ax2 = plot_twinx_multi_y(
        time_h,
        plot_info_list,
        (900, 500),
        "Time (h)",
        "Temperature (℃)",
        "Pressure (Pa)",
        logfile.path.stem,
    )
    ax1.set_xlim(0, time_h.max())
    ax1.set_ylim(0, 800)
    if ax2:
        ax2.set_yscale("log")
        ax2.set_ylim(1e-9, 1e-3)
    fig.tight_layout()

    plt.savefig(save_dir / (logfile.path.stem + "_pressure.svg"), format="svg")
    plt.close(fig)  # メモリを解放
