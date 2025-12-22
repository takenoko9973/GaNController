import sys
from pathlib import Path
from typing import TYPE_CHECKING

from heater_amd_controller.models.app_config import AppConfig
from heater_amd_controller.utils.log_file import DateLogDirectory, LogFile, LogManager

sys.path.append(str(Path(__file__).parent.parent))
from scripts.data_plot import HCPlotter, HDPlotter, NEGHDPlotter

if TYPE_CHECKING:
    from scripts.data_plot.base_plotter import BasePlotter

config_path = Path("config.toml")
config = AppConfig.load()

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent


def plots(logfile: LogFile) -> None:
    parts = list(logfile.path.parent.absolute().relative_to(root_path).parts)
    parts[0] = PLOT_DIR
    save_dir = root_path / Path(*parts)
    save_dir.mkdir(exist_ok=True, parents=True)

    plotters = {
        "TEST": HCPlotter,
        "HD": HDPlotter,
        "NEGHD": NEGHDPlotter,
    }

    cls = plotters.get(logfile.protocol)
    if cls:
        plotter: BasePlotter = cls(logfile, save_dir)
        plotter.plot()


def main() -> None:
    log_manager = LogManager(config.common.log_dir)

    for date_dir_path in log_manager.get_date_dir_paths():
        date_dir = DateLogDirectory(date_dir_path)

        for logfile_path in date_dir.get_logfile_paths():
            logfile = LogFile(logfile_path)

            plots(logfile)


if __name__ == "__main__":
    main()
