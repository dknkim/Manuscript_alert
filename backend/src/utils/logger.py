"""
Custom logging module with colored console output and rotating file handlers.

Features:
    - Color-coded console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Rotating file handler (default: 10 MB per file, 10 backup files)
    - Plain text output to log files (no ANSI color codes)
    - Thread-safe logger caching

Usage:
    from utils.logger import Logger
    logger = Logger(__name__)
    logger.info("Hello world")
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import ClassVar


class ColoredFormatter(logging.Formatter):
    """Custom formatter with ANSI colors for console output."""

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET: str = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        levelname: str = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class Logger:
    """Wrapper around logging.Logger with rotating file + coloured console."""

    _loggers: ClassVar[dict[str, logging.Logger]] = {}
    _initialized: ClassVar[set[str]] = set()

    def __init__(
        self,
        name: str | None = None,
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 10,
    ) -> None:
        self.name: str = name or "app"
        self.log_dir: str = log_dir
        self.max_bytes: int = max_bytes
        self.backup_count: int = backup_count

        if self.name in Logger._loggers and self.name in Logger._initialized:
            self.logger: logging.Logger = Logger._loggers[self.name]
            if not self.logger.handlers:
                self.logger = self._setup_logger()
                Logger._loggers[self.name] = self.logger
        else:
            self.logger = self._setup_logger()
            Logger._loggers[self.name] = self.logger
            Logger._initialized.add(self.name)

    def _setup_logger(self) -> logging.Logger:
        """Create and configure a new :class:`logging.Logger`."""
        os.makedirs(self.log_dir, exist_ok=True)

        logger: logging.Logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if logger.handlers:
            logger.handlers.clear()

        fmt: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        datefmt: str = "%Y-%m-%d %H:%M:%S"

        file_handler: RotatingFileHandler = RotatingFileHandler(
            os.path.join(self.log_dir, "app.log"),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        logger.addHandler(file_handler)

        console_handler: logging.StreamHandler = logging.StreamHandler()  # type: ignore[type-arg]
        console_handler.setFormatter(ColoredFormatter(fmt, datefmt=datefmt))
        logger.addHandler(console_handler)

        return logger

    # Convenience methods ---------------------------------------------------

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)
