import datetime
import re
from pathlib import Path

from gan_controller.common.constants import LOG_DIR
from gan_controller.common.schemas.app_config import AppConfig

# ログファイル名の正規表現パターン: [Number]Protocol-yyyymmddHHMMSS.ext
LOGFILE_PATTERN = re.compile(r"^\[(\d+\.\d+)\]([A-Z0-9]+)\-(\d{14})\.dat$")


class LogFile:
    """個別のログファイルを操作するクラス"""

    def __init__(self, file_path: Path, encoding: str = "utf-8") -> None:
        self.path = file_path
        self.encoding = encoding

    @property
    def number(self) -> str:
        """ファイル名から連番を取得"""
        match = LOGFILE_PATTERN.match(self.path.name)
        return match[1] if match is not None else "0.0"

    @property
    def protocol(self) -> str:
        match = LOGFILE_PATTERN.match(self.path.name)
        return match[2] if match is not None else "ERROR"

    def write(self, content: str) -> None:
        """追記モードで書き込み"""
        try:
            with self.path.open("a", encoding=self.encoding, newline="") as f:
                f.write(content)

        except OSError as e:
            print(f"Error writing to log file {self.path}: {e}")


class DateLogDirectory:
    """日付ごとのディレクトリとファイル連番を管理するクラス"""

    def __init__(self, path: Path, tz: datetime.timezone, encoding: str) -> None:
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)

        self.tz = tz
        self.encoding = encoding

    def __str__(self) -> str:
        return f"DateLogDirectory(path={self.path})"

    def _find_current_version(self) -> tuple[int, int]:
        """最新の実験番号を取得

        Returns:
            tuple[int, int]: (current_major, current_minor)
                             ファイルが存在しない場合は (0, 0)

        """
        number_pattern = re.compile(r"(\d+)\.(\d+)")

        current_major = 0
        current_minor = 0

        try:
            for entry in self.path.iterdir():
                if not entry.is_file():
                    continue

                match = LOGFILE_PATTERN.match(entry.name)
                if match is None:
                    continue

                number = match.group(1)
                number_match = number_pattern.match(number)
                if number_match is None:
                    msg = f"Invalid number format in file name {entry.name}"
                    raise ValueError(msg)

                major = int(number_match.group(1))
                minor = int(number_match.group(2))

                # より大きい番号を探す
                if major > current_major:
                    current_major = major
                    current_minor = minor
                elif major == current_major and minor > current_minor:
                    current_minor = minor

        except OSError as e:
            print(f"Error scanning directory {self.path} for versions: {e}")

        return (current_major, current_minor)

    def _determine_next_version(self, major_update: bool) -> tuple[int, int]:
        """現在の実験番号に基づき、次の実験番号を決定"""
        current_major, current_minor = self._find_current_version()

        if current_major == 0 and current_minor == 0:
            # 初回 (0.1 開始)
            return (0, 1)

        if major_update:
            # メジャー番号更新
            return (current_major + 1, 1)

        # マイナー番号更新
        return (current_major, current_minor + 1)

    def create_logfile(self, protocol_name: str, major_update: bool = False) -> LogFile:
        """新しいログファイルを作成する"""
        # 実験番号
        new_major, new_minor = self._determine_next_version(major_update)

        # プロトコル名の正規化 (英数字のみ、大文字)
        protocol_formatted = re.sub(r"[^a-zA-Z0-9]", "", protocol_name).upper()
        if not protocol_formatted:
            protocol_formatted = "DEFAULT"

        # タイムスタンプ
        timestamp = datetime.datetime.now(self.tz).strftime("%Y%m%d%H%M%S")

        # ファイル名生成
        filename = f"[{new_major}.{new_minor}]{protocol_formatted}-{timestamp}.dat"
        file_path = self.path / filename

        return LogFile(file_path, self.encoding)


class LogManager:
    """ログシステムのルート管理クラス"""

    DATE_DIR_PATTERN = re.compile(r"^\d{6}$")  # YYMMDD

    def __init__(self, config: AppConfig) -> None:
        self.base_path = Path(LOG_DIR)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.tz = config.common.get_tz()
        self.encoding = config.common.encode

        self.base_path.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        return f"LogFileManager(path={self.base_path})"

    def _find_latest_date(self) -> datetime.date | None:
        """最新の日付ディレクトリを探す"""
        latest_date = None

        try:
            for entry in self.base_path.iterdir():
                if not entry.is_dir() or self.DATE_DIR_PATTERN.match(entry.name) is None:
                    continue

                try:
                    # ディレクトリ名を日付オブジェクトに変換
                    current_date = (
                        datetime.datetime.strptime(entry.name, "%y%m%d").astimezone(self.tz).date()
                    )

                    # latest_date が未設定、または見つかった日付の方が新しい場合
                    if latest_date is None or current_date > latest_date:
                        latest_date = current_date

                except ValueError:
                    # strptime が失敗した場合 (例: '999999' など不正な日付) は無視
                    continue

        except OSError as e:
            # ディレクトリのスキャンに失敗
            print(f"Error scanning log directory {self.base_path}: {e}")

        return latest_date

    def get_date_directory(self, update_date: bool = False) -> DateLogDirectory:
        """使用すべき日付ディレクトリを取得・生成する"""
        target_date: datetime.date

        if update_date:
            # 更新する場合は今日の日付
            target_date = datetime.datetime.now(self.tz).date()
        else:
            latest_date = self._find_latest_date()
            # 最新が見つかればそれを使い、なければ (logsが空なら) 今日の日付を使う
            target_date = (
                latest_date if latest_date is not None else datetime.datetime.now(self.tz).date()
            )

        dir_name = target_date.strftime("%y%m%d")
        dir_path = self.base_path / dir_name

        return DateLogDirectory(dir_path, self.tz, self.encoding)
