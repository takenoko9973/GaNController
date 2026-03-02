import os
from pathlib import Path
from zoneinfo import ZoneInfo

# === アプリケーションディレクトリの解決 ===
APP_DIR_NAME = "GaNController"
APP_HOME_ENV_VAR = "GAN_CONTROLLER_HOME"


def _find_project_root(start: Path) -> Path | None:
    """開発実行時のプロジェクトルート(pyproject.tomlを含むディレクトリ)を探索する。"""
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def _resolve_platform_data_home() -> Path:
    if os.name == "nt":
        default_home = Path.home() / "AppData" / "Local"
        return Path(os.environ.get("LOCALAPPDATA", default_home))

    default_home = Path.home() / ".local" / "share"
    return Path(os.environ.get("XDG_DATA_HOME", default_home))


def resolve_app_home() -> Path:
    """
    設定/ログ保存先の基準ディレクトリを解決する。

    優先順位:
    1. 環境変数 GAN_CONTROLLER_HOME
    2. 開発実行時のプロジェクトルート (pyproject.toml 検出)
    3. OS標準のユーザーデータディレクトリ配下
    """
    env_home = os.environ.get(APP_HOME_ENV_VAR)
    if env_home:
        return Path(env_home).expanduser().resolve(strict=False)

    project_root = _find_project_root(Path.cwd())
    if project_root is not None:
        return project_root.resolve(strict=False)

    return (_resolve_platform_data_home() / APP_DIR_NAME).expanduser().resolve(strict=False)


APP_HOME = resolve_app_home()
PROJECT_ROOT = APP_HOME  # 互換性のため残す

# === ディレクトリ定義 ===
CONFIG_DIR = APP_HOME / "configs"
LOG_DIR = APP_HOME / "logs"
PROTOCOLS_DIR = CONFIG_DIR / "protocols"  # HC用


def ensure_runtime_dirs() -> None:
    """実行に必要なディレクトリを作成する。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)


# === ファイルパス定義 ===
# アプリケーション全体の設定 (デバイス接続など)
APP_CONFIG_PATH = CONFIG_DIR / "app_config.toml"

# 機能ごとの設定
HC_CONFIG_PATH = CONFIG_DIR / "hc_config.toml"
NEA_CONFIG_PATH = CONFIG_DIR / "nea_config.toml"

# === 物理定数 (SI定義) ===
# Planck constant [J s]
PLANCK_CONSTANT = 6.62607015e-34
# Speed of light in vacuum [m/s]
SPEED_OF_LIGHT = 299792458.0
# Elementary charge [C]
ELEMENTARY_CHARGE = 1.602176634e-19

# === その他
JST = ZoneInfo("Asia/Tokyo")
