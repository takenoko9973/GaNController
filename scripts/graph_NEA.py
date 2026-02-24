import sys
import tomllib
from pathlib import Path

from gan_controller.infrastructure.persistence.log_manager import LogFile, LogManager

sys.path.append(str(Path(__file__).parent.parent))
from scripts.data_plot.plot_nea import NEAPlotConfig, NEAPlotter

PLOT_DIR = "plots"
root_path = Path(__file__).parent.parent
TOML_PATH = root_path / "scripts" / "NEA_graph_data.toml"


def load_nea_config() -> dict:
    if not TOML_PATH.exists():
        return {"colors": {}, "plots": {}}

    with TOML_PATH.open("rb") as f:
        return tomllib.load(f)


def plots_nea(logfile: LogFile, config_data: dict) -> None:
    # 日付と実験番号のキーを作成
    # LogFile の path.parent.name が "250904" などの日付ディレクトリであることを前提
    date_str = logfile.path.parent.name
    major, minor = logfile.major, logfile.minor
    plot_key = f"{date_str}_{major}.{minor}"

    # このログに対する設定が存在するかチェック
    plot_config = config_data.get("plots", {}).get(plot_key)
    if not plot_config:
        # 設定がなければスキップ
        return

    # 保存先ディレクトリの作成
    try:
        rel_dir = logfile.path.parent.relative_to(Path("logs").absolute())
        save_dir = root_path / PLOT_DIR / rel_dir
    except ValueError:
        save_dir = root_path / PLOT_DIR / logfile.path.parent.name
    save_dir.mkdir(exist_ok=True, parents=True)

    # 抽出した設定をデータクラスにまとめる
    nea_config = NEAPlotConfig(
        colors=config_data.get("colors", {}),
        spans=plot_config.get("spans", []),
        points=plot_config.get("points", []),
    )

    print(f"Plotting NEA: {logfile.path.name}")
    plotter = NEAPlotter(logfile, save_dir, nea_config)
    plotter.plot()


def main() -> None:
    log_manager = LogManager()
    config_data = load_nea_config()

    for logfile in log_manager.get_all_log_files():
        # プロトコル名が "NEA" を含むものだけを処理対象とする
        if logfile.protocol == "NEA":
            plots_nea(logfile, config_data)


if __name__ == "__main__":
    main()
