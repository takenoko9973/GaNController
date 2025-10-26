import datetime
import re
from pathlib import Path

from heater_amd_controller.config import Config

config_path = Path("config.toml")
config = Config.load_config(config_path)

LOG_DIR = config.common.log_dir
TZ = config.common.get_tz()


class LogFile:
    def __init__(self, file_path: Path, protocol: str, number: str) -> None:
        self.path = file_path
        self.protocol = protocol
        self.number = number

    def __str__(self) -> str:
        return str(self.path)

    def write(self, message: str) -> None:
        try:
            with self.path.open("a", encoding=config.common.encode) as f:
                f.write(message)

        except OSError as e:
            # 書き込みエラーのハンドリングを追加
            print(f"Error writing to log file {self.path}: {e}")


class DateLogDirectory:
    LOGFILE_PATTERN = re.compile(r"^\[(\d+)\.(\d+)\]([A-Z]+)\-(\d+)\.dat")

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.mkdir(exist_ok=True)

    def __str__(self) -> str:
        return f"DateLogDirectory(path={self.path})"

    def get_logfile_paths(self) -> list[Path]:
        """すべてのlogfileを取得"""
        logfile_paths = []

        for entry in self.path.iterdir():
            if not entry.is_file():
                continue

            match = self.LOGFILE_PATTERN.match(entry.name)
            if match is None:
                continue

            logfile_paths.append(entry)

        return logfile_paths

    def _find_current_version(self) -> tuple[int, int]:
        """最新のバージョン番号を取得

        Returns:
            tuple[int, int]: (current_major, current_minor)
                             ファイルが存在しない場合は (0, 0)

        """
        current_major = 0
        current_minor = 0

        try:
            for logfile_path in self.get_logfile_paths():
                match = self.LOGFILE_PATTERN.match(logfile_path.name)
                if match is None:
                    continue

                major = int(match.group(1))
                minor = int(match.group(2))

                # より大きいバージョンを探す
                if major > current_major:
                    current_major = major
                    current_minor = minor
                elif major == current_major and minor > current_minor:
                    current_minor = minor
        except OSError as e:
            print(f"Error scanning directory {self.path} for versions: {e}")

        return (current_major, current_minor)

    def _determine_next_version(self, major_update: bool) -> tuple[int, int]:
        """現在のバージョンに基づき、次のバージョン番号を決定"""
        current_major, current_minor = self._find_current_version()

        if current_major == 0 and current_minor == 0:
            # 最初のファイル (0.1 開始)
            new_major = 0
            new_minor = 1
        elif major_update:
            # メジャーアップデート
            new_major = current_major + 1
            new_minor = 1  # メジャーが上がったらマイナーは 0 にリセット
        else:
            # マイナーアップデート
            new_major = current_major
            new_minor = current_minor + 1

        return (new_major, new_minor)

    def create_logfile(self, protocol: str, major_update: bool = False) -> LogFile:
        # バージョン
        new_major, new_minor = self._determine_next_version(major_update)
        # プロトコル
        protocol_formatted = re.sub(r"[^a-zA-Z]", "", protocol).upper()
        if not protocol_formatted:
            protocol_formatted = "DEFAULT"
        # タイムスタンプ
        timestamp = datetime.datetime.now(TZ).strftime("%Y%m%d%H%M%S")

        number = f"{new_major}.{new_minor}"
        filename = f"[{number}]{protocol_formatted}-{timestamp}.dat"
        file_path = self.path / filename

        return LogFile(file_path, protocol_formatted, number)


class LogManager:
    date_dir_pattern = re.compile(r"^\d{6}$")

    def __init__(self, base_dir: str | Path = LOG_DIR) -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        return f"LogFileManager(path={self.base_path})"

    def get_date_dir_paths(self) -> list[Path]:
        """すべてのdate directoryを取得"""
        date_dir_paths = []

        for entry in self.base_path.iterdir():
            # ディレクトリ
            if not entry.is_dir():
                continue
            # 'yymmdd' 形式か
            if self.date_dir_pattern.match(entry.name) is None:
                continue

            date_dir_paths.append(entry)

        return date_dir_paths

    def _find_latest_date(self) -> datetime.date | None:
        latest_date = None

        try:
            for date_dir_path in self.get_date_dir_paths():
                try:
                    # ディレクトリ名を日付オブジェクトに変換
                    current_date = (
                        datetime.datetime.strptime(date_dir_path.name, "%y%m%d")
                        .astimezone(TZ)
                        .date()
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

    def get_date_directory(self, date_update: bool = False) -> DateLogDirectory:
        target_date: datetime.date

        if date_update:
            # 更新する場合は今日の日付
            target_date = datetime.datetime.now(TZ).date()
        else:
            # 最新を探す
            latest_date = self._find_latest_date()
            # 最新が見つかればそれを使い、なければ (logsが空なら) 今日の日付を使う
            target_date = (
                latest_date if latest_date is not None else datetime.datetime.now(TZ).date()
            )

        # 決定した日付で DateLogDirectory を返す
        dir_name = target_date.strftime("%y%m%d")
        dir_path = self.base_path / dir_name
        return DateLogDirectory(dir_path)
