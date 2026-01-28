from pathlib import Path

# === ルートディレクトリの解決 ===
PROJECT_ROOT = Path.cwd()

# === ディレクトリ定義 ===
CONFIG_DIR = PROJECT_ROOT / "configs"
LOG_DIR = PROJECT_ROOT / "logs"

PROTOCOLS_DIR = CONFIG_DIR / "protocols"  # HC用

# 必要なディレクトリの自動作成
if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir(parents=True)

if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

if not PROTOCOLS_DIR.exists():
    PROTOCOLS_DIR.mkdir(parents=True)

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
