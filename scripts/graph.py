import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gan_controller.core.constants import LOG_DIR
from gan_controller.core.domain.app_config import AppConfig
from gan_controller.infrastructure.persistence.log_manager import LogFile, LogManager

sys.path.append(str(Path(__file__).parent.parent))
from scripts.data_plot import HCPlotter, HDPlotter, NEGHDPlotter

if TYPE_CHECKING:
    from scripts.data_plot.base_plotter import BasePlotter

config = AppConfig.load()

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent


def plots(logfile: LogFile) -> None:
    # ログディレクトリからの相対パスを取得
    rel_dir = logfile.path.parent.relative_to(Path(LOG_DIR))
    save_dir = root_path / PLOT_DIR / rel_dir
    save_dir.mkdir(exist_ok=True, parents=True)

    plotters = {
        "HC": HCPlotter,
        "HD": HDPlotter,
        "NEGHD": NEGHDPlotter,
    }

    cls = plotters.get(logfile.protocol)
    if cls:
        print(f"Plotting: {logfile.path.name} (Protocol: {logfile.protocol})")
        plotter: BasePlotter = cls(logfile, save_dir)
        plotter.plot()
    else:
        print(f"Skipping: {logfile.path.name} (Unknown Protocol: {logfile.protocol})")


def main() -> None:
    log_manager = LogManager()
    all_log_files = log_manager.get_all_log_files()

    for logfile in all_log_files:
        plots(logfile)


if __name__ == "__main__":
    main()
