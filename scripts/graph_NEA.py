import sys
import tomllib
from pathlib import Path

from heater_amd_controller.utils.log_file import LogFile

sys.path.append(str(Path(__file__).parent.parent))
from scripts.data_plot.plot_nea import EventColor, EventSpan, NEAPlotter

event_data_path = Path(Path(__file__).parent / "NEA_graph_data.toml")
with event_data_path.open("rb") as f:
    event_data = tomllib.load(f)

# ======= Plot Setting =============================================

event_colors: list[EventColor] = [
    EventColor("Cs", "red"),
    EventColor("O2", "blue"),
    EventColor("Cs(3.0A)", "orange"),
    EventColor("Cs(3.8A)", "chocolate"),
    EventColor("LaserEngChange", "green"),
]

FORCE_SAVE_FIG = True

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent

# ==================================================================


def plot(path: Path) -> None:
    logfile = LogFile(path)

    parts = list(logfile.path.parent.absolute().relative_to(root_path).parts)
    parts[0] = PLOT_DIR
    save_dir = root_path / Path(*parts)
    save_dir.mkdir(exist_ok=True, parents=True)

    log_events: list[dict] = event_data[path.parts[-2]][path.stem]["event_spans"]
    event_spans = [EventSpan(**event) for event in log_events]

    plotter = NEAPlotter(logfile, save_dir, event_spans, event_colors, FORCE_SAVE_FIG)
    plotter.plot()


def main() -> None:
    for date in event_data:
        for file_name in event_data[date]:
            nea_log_path = Path("logs") / date / (file_name + ".dat")

            plot(nea_log_path)


if __name__ == "__main__":
    main()
