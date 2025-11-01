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

NEA_log_path = Path("logs/251015/[2.2]NEA-20251028153023.dat")

log_events: list[dict] = event_data[NEA_log_path.parts[-2]][NEA_log_path.stem]["event_spans"]
event_spans = [EventSpan(**event) for event in log_events]

event_colors: list[EventColor] = [
    EventColor("Cs", "red"),
    EventColor("O2", "blue"),
    EventColor("Cs(3.0A)", "orange"),
    EventColor("LaserEngChange", "green"),
]

SAVE_FIG = True

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent


# ==================================================================


def main() -> None:
    logfile = LogFile(NEA_log_path)

    parts = list(logfile.path.parent.absolute().relative_to(root_path).parts)
    parts[0] = PLOT_DIR
    save_dir = root_path / Path(*parts)
    save_dir.mkdir(exist_ok=True, parents=True)

    plotter = NEAPlotter(logfile, save_dir, event_spans, event_colors, True)
    plotter.plot()


if __name__ == "__main__":
    main()
