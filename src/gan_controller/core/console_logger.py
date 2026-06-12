import logging
import sys
from typing import ClassVar

APP_LOGGER_NAME = "gan_controller"
APP_CONSOLE_HANDLER_NAME = "gan_controller_console"


class ColorConsoleFormatter(logging.Formatter):
    """コンソールログの色付けを行うFormatter。"""

    COLORS: ClassVar[dict[str, str]] = {
        "green": "\033[32m",
        "orange": "\033[38;5;208m",
        "red": "\033[31m",
        "yellow": "\033[33m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = getattr(record, "color", None)
        if not color:
            return message

        prefix = self.COLORS.get(color)
        if prefix is None:
            return message

        return f"{prefix}{message}{self.RESET}"


def get_logger(name: str) -> logging.Logger:
    """アプリ共通のloggerを返す。"""
    _configure_console_logger()
    return logging.getLogger(name)


def _configure_console_logger() -> None:
    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in logger.handlers:
        if handler.get_name() == APP_CONSOLE_HANDLER_NAME:
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(APP_CONSOLE_HANDLER_NAME)
    handler.setLevel(logging.INFO)
    handler.setFormatter(ColorConsoleFormatter("%(message)s"))
    logger.addHandler(handler)
