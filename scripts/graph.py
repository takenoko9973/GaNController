import sys
from pathlib import Path

from heater_amd_controller.config import Config
from heater_amd_controller.utils.log_file import DateLogDirectory, LogFile, LogManager

sys.path.append(str(Path(__file__).parent.parent))
from scripts.data_plot.plot_HC import plot_hc
from scripts.data_plot.plot_HD import plot_hd
from scripts.data_plot.plot_NEGHD import plot_neghd

config_path = Path("config.toml")
config = Config.load_config(config_path)

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent


def plots(logfile: LogFile) -> None:
    parts = list(logfile.path.parent.absolute().relative_to(root_path).parts)
    parts[0] = PLOT_DIR
    save_dir = root_path / Path(*parts)
    save_dir.mkdir(exist_ok=True, parents=True)

    if logfile.protocol == "HC":
        plot_hc(logfile, save_dir)
    elif logfile.protocol == "HD":
        plot_hd(logfile, save_dir)
    elif logfile.protocol == "NEGHD":
        plot_neghd(logfile, save_dir)


def main() -> None:
    log_manager = LogManager(config.common.log_dir)

    for date_dir_path in log_manager.get_date_dir_paths():
        date_dir = DateLogDirectory(date_dir_path)

        for logfile_path in date_dir.get_logfile_paths():
            logfile = LogFile(logfile_path)

            plots(logfile)


if __name__ == "__main__":
    main()
