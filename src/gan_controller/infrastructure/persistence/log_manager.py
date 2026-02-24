import datetime
import re
from dataclasses import dataclass
from pathlib import Path

from gan_controller.core.constants import JST, LOG_DIR

# ---------------------------------------------------------------------------
# Helpers / Parsers (状態を持たない純粋なロジック群)
# ---------------------------------------------------------------------------

# ログファイル名の正規表現パターン: [Number]Protocol-yyyymmddHHMMSS.dat
LOGFILE_PATTERN = re.compile(r"^\[(\d+)\.(\d+)\]([A-Z0-9]+)\-(\d{14})\.dat$")
DATE_DIR_PATTERN = re.compile(r"^\d{6}$")  # YYMMDD


@dataclass(frozen=True)
class LogFileMetadata:
    """ログファイル名から抽出されるメタデータ"""

    major: int
    minor: int
    protocol: str


def parse_logfile_name(filename: str) -> LogFileMetadata:
    """ログファイル名からメタデータを抽出する"""
    match = LOGFILE_PATTERN.match(filename)
    if match:
        return LogFileMetadata(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            protocol=match.group(3),
        )
    return LogFileMetadata(major=0, minor=0, protocol="ERROR")


def parse_date_dirname(dirname: str) -> datetime.date | None:
    """ディレクトリ名 (YYMMDD) から日付を抽出する"""
    if not DATE_DIR_PATTERN.match(dirname):
        return None
    try:
        return datetime.datetime.strptime(dirname, "%y%m%d").astimezone(JST).date()
    except ValueError:
        return None


def normalize_protocol_name(protocol_name: str) -> str:
    """プロトコル名をファイル名用に正規化 (英数字大文字のみ) する"""
    formatted = re.sub(r"[^a-zA-Z0-9]", "", protocol_name).upper()
    return formatted if formatted else "DEFAULT"


def generate_timestamp() -> str:
    """現在時刻のタイムスタンプ文字列を生成する"""
    return datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S")


class LogFile:
    """個別のログファイルを操作するクラス"""

    def __init__(self, file_path: Path, encoding: str = "utf-8") -> None:
        self.path = file_path
        self.encoding = encoding
        self._metadata = parse_logfile_name(self.path.name)

    @property
    def major(self) -> int:
        return self._metadata.major

    @property
    def minor(self) -> int:
        return self._metadata.minor

    @property
    def number(self) -> str:
        """ファイル名から連番を取得"""
        return f"{self.major}.{self.minor}"

    @property
    def protocol(self) -> str:
        return self._metadata.protocol

    def write(self, content: str) -> None:
        """追記モードで書き込み"""
        try:
            with self.path.open("a", encoding=self.encoding, newline="") as f:
                f.write(content)

        except OSError as e:
            print(f"Error writing to log file {self.path}: {e}")


class DateLogDirectory:
    """日付ごとのディレクトリとファイル連番を管理するクラス"""

    def __init__(self, path: Path, target_date: datetime.date, encoding: str = "utf-8") -> None:
        self.path: Path = path
        self.date: datetime.date = target_date
        self.encoding: str = encoding

    def __str__(self) -> str:
        return f"DateLogDirectory(path={self.path})"

    def get_log_files(self) -> list[LogFile]:
        """このディレクトリ内のすべての有効なログファイルを取得する"""
        if not self.path.exists():
            return []

        log_files = []
        try:
            for entry in self.path.iterdir():
                if entry.is_file() and LOGFILE_PATTERN.match(entry.name):
                    log_files.append(LogFile(entry, self.encoding))  # noqa: PERF401

        except OSError as e:
            print(f"Error reading directory {self.path}: {e}")

        # 必要に応じてファイル名や作成日時でソートして返す
        return sorted(log_files, key=lambda log: log.path.name)

    def _find_current_version(self) -> tuple[int, int]:
        """
        最新の実験番号を取得

        Returns:
            tuple[int, int]: (current_major, current_minor)
                             ファイルが存在しない場合は (0, 0)

        """
        if not self.path.exists():
            return (0, 0)

        versions = []
        try:
            for entry in self.path.iterdir():
                if not entry.is_file():
                    continue

                metadata = parse_logfile_name(entry.name)
                versions.append((metadata.major, metadata.minor))

        except OSError as e:
            print(f"Error scanning directory {self.path} for versions: {e}")

        # タプルの比較を利用して最大値を一括取得
        return max(versions) if versions else (0, 0)

    def get_next_number(self, major_update: bool) -> tuple[int, int]:
        """現在の実験番号に基づき、次の実験番号を決定"""
        current_major, current_minor = self._find_current_version()

        if current_major == 0 and current_minor == 0:
            # 初回
            return (1, 1) if major_update else (0, 1)

        if major_update:
            # メジャー番号更新
            return (current_major + 1, 1)

        # マイナー番号更新
        return (current_major, current_minor + 1)

    def _create_logfile_name(self, protocol_name: str, major_update: bool = False) -> str:
        # 実験番号
        new_major, new_minor = self.get_next_number(major_update)

        # プロトコル名の正規化 (英数字のみ、大文字)
        protocol_formatted = re.sub(r"[^a-zA-Z0-9]", "", protocol_name).upper()
        if not protocol_formatted:
            protocol_formatted = "DEFAULT"

        # タイムスタンプ
        timestamp = datetime.datetime.now(JST).strftime("%Y%m%d%H%M%S")

        return f"[{new_major}.{new_minor}]{protocol_formatted}-{timestamp}.dat"

    def create_logfile(self, protocol_name: str, major_update: bool = False) -> LogFile:
        """新しいログファイルを作成する"""
        # 作成先
        new_major, new_minor = self.get_next_number(major_update)

        protocol_formatted = normalize_protocol_name(protocol_name)
        timestamp = generate_timestamp()

        filename = f"[{new_major}.{new_minor}]{protocol_formatted}-{timestamp}.dat"
        file_path = self.path / filename

        # フォルダ・ファイル作成
        self.path.mkdir(parents=True, exist_ok=True)
        return LogFile(file_path, self.encoding)


class LogManager:
    """ログシステムのルート管理クラス"""

    DATE_DIR_PATTERN = re.compile(r"^\d{6}$")  # YYMMDD

    def __init__(self, base_path: str | Path = LOG_DIR, encoding: str = "utf-8") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding

    def __str__(self) -> str:
        return f"LogFileManager(path={self.base_path})"

    def _get_valid_date_directories(self) -> list[DateLogDirectory]:
        """有効な日付ディレクトリのリストをタプル (日付, パス) で取得する"""
        if not self.base_path.exists():
            return []

        directories = []
        try:
            for entry in self.base_path.iterdir():
                if not entry.is_dir():
                    continue

                parsed_date = parse_date_dirname(entry.name)
                if parsed_date:
                    directories.append(DateLogDirectory(entry, parsed_date, self.encoding))
        except OSError as e:
            print(f"Error scanning log directory {self.base_path}: {e}")

        return directories

    def get_active_directory(self, update_date: bool = False) -> DateLogDirectory:
        """使用すべき日付ディレクトリを取得・生成する"""
        if update_date:
            # 更新する場合は今日の日付
            target_date = datetime.datetime.now(JST).date()
        else:
            valid_dirs = self._get_valid_date_directories()
            # 最新が見つかればそれを使い、なければ (logsが空なら) 今日の日付を使う
            if valid_dirs:
                latest_dir = max(valid_dirs, key=lambda d: d.date)
                target_date = latest_dir.date
            else:
                target_date = datetime.datetime.now(JST).date()

        dir_name = target_date.strftime("%y%m%d")
        dir_path = self.base_path / dir_name

        return DateLogDirectory(dir_path, target_date, self.encoding)

    def get_directory_by_date(
        self, target_date: datetime.date | None = None
    ) -> DateLogDirectory | None:
        """指定された日付 (指定がない場合は最新) のディレクトリを取得する"""
        if target_date is None:
            valid_dirs = self._get_valid_date_directories()
            if not valid_dirs:
                return None

            latest_dir = max(valid_dirs, key=lambda d: d.date)
            target_date = latest_dir.date

        dir_name = target_date.strftime("%y%m%d")
        dir_path = self.base_path / dir_name

        if not dir_path.exists() or not dir_path.is_dir():
            return None

        return DateLogDirectory(dir_path, target_date, self.encoding)

    def get_all_log_files(self) -> list[LogFile]:
        """すべての日付ディレクトリを走査し、全ログファイルを時系列順に取得する"""
        valid_dirs = self._get_valid_date_directories()
        valid_dirs.sort(key=lambda d: d.date)

        all_logs: list[LogFile] = []
        for date_dir in valid_dirs:
            all_logs.extend(date_dir.get_log_files())

        return all_logs
