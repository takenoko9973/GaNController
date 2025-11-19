import datetime
import re as regex
from pathlib import Path

LOG_DIR = "logs"


class LogFile:
    pattern = regex.compile(r"^\[(\d+)\.(\d+)\]([A-Z]+)\-(\d+)\.dat")

    def __init__(
        self,
        major_num: int,
        minor_num: int,
        protocol: str,
        date: str,
        log_dir: str | Path = LOG_DIR,
    ) -> None:
        self.major_num = major_num
        self.minor_num = minor_num
        self.protocol = protocol
        self.date = date

        self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.get_file_path().open("a", encoding="utf-8")

    @classmethod
    def from_file_name(cls, file_name: str, log_dir: str | Path = LOG_DIR) -> "LogFile":
        match = cls.pattern.match(file_name)
        if match is None:
            msg = f"Invalid file name format: {file_name}"
            raise ValueError(msg)

        return cls(
            major_num=int(match.group(1)),
            minor_num=int(match.group(2)),
            protocol=match.group(3),
            date=match.group(4),
            log_dir=log_dir,
        )

    @classmethod
    def from_file_path(cls, file_path: str | Path) -> "LogFile":
        file_name = Path(file_path).name
        log_dir = Path(file_path).parent

        return cls.from_file_name(file_name, log_dir)

    def __del__(self) -> None:
        if hasattr(self, "file") and self.file is not None:
            self.file.close()

    def __str__(self) -> str:
        return self.get_file_name()

    @property
    def number(self) -> str:
        return f"{self.major_num}.{self.minor_num}"

    def write(self, message: str) -> None:
        if hasattr(self, "file") and self.file is not None:
            self.file.write(message)
            self.file.flush()

    def get_file_name(self) -> str:
        return f"[{self.number}]{self.protocol}-{self.date}.dat"

    def get_file_path(self) -> Path:
        return self.log_dir / self.get_file_name()


class LogFileManager:
    def __init__(self, log_dir: str | Path = LOG_DIR) -> None:
        self.log_dir = Path(log_dir)

    def __str__(self) -> str:
        return f"LogFileManager[dir={self.log_dir}]"

    def get_log_files(self) -> list[LogFile]:
        files = self.log_dir.glob("*.dat")

        log_files = []
        for file in files:
            try:
                log_files.append(LogFile.from_file_path(file))
            except Exception as e:  # noqa: BLE001
                print(f"{e}")

        return sorted(log_files, key=lambda x: x.date)

    def get_latest_log_file(self) -> LogFile | None:
        log_files = self.get_log_files()

        if len(log_files) == 0:
            return None

        return log_files[-1]

    def create_log_file(self, protocol: str, update_major: bool = False) -> LogFile:
        latest_log_file = self.get_latest_log_file()

        if latest_log_file is None:
            major_num = 1
            minor_num = 1
        elif update_major:
            major_num = latest_log_file.major_num + 1
            minor_num = 1
        else:
            major_num = latest_log_file.major_num
            minor_num = latest_log_file.minor_num + 1

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        date = now.strftime("%Y%m%d%H%M%S")

        return LogFile(
            major_num=major_num,
            minor_num=minor_num,
            protocol=protocol,
            date=date,
            log_dir=self.log_dir,
        )
