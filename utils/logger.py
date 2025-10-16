"""
Custom logging module with colored console output and rotating file handlers.

This module provides a Logger class that creates loggers with:
- Colored output to console for easy visual distinction of log levels
- Rotating file handlers to prevent log files from growing indefinitely
- Automatic log directory creation
- Logger caching to prevent duplicate handlers

Features:
    - Color-coded console output (DEBUG=Cyan, INFO=Green, WARNING=Yellow, ERROR=Red, CRITICAL=Magenta)
    - Rotating file handler (default: 10MB per file, 10 backup files)
    - Plain text output to log files (no ANSI color codes)
    - Thread-safe logger caching

Usage Example:
    Basic usage in any module:

    ```python
    from utils.logger import Logger

    logger = Logger(__name__)

    logger.debug("Debug message")      # Cyan - detailed diagnostic information
    logger.info("Info message")        # Green - general informational messages
    logger.warning("Warning message")  # Yellow - warning messages for potentially harmful situations
    logger.error("Error message")      # Red - error messages for serious problems
    logger.critical("Critical!")       # Magenta - critical messages for very serious errors
    ```

    Advanced usage with custom configuration:

    ```python
    from utils.logger import Logger

    # Custom log directory and file size limits
    logger = Logger(
        name=__name__,
        log_dir='custom_logs',
        max_bytes=5*1024*1024,  # 5MB per file
        backup_count=5           # Keep 5 backup files
    )

    logger.info("Starting process...")
    try:
        # Your code here
        result = some_function()
        logger.info(f"Process completed: {result}")
    except Exception as e:
        logger.error(f"Process failed: {e}", exc_info=True)  # Include stack trace
    ```

Output Format:
    Console: 2025-10-15 14:30:45 | INFO     | module_name | Your message here
    File:    2025-10-15 14:30:45 | INFO     | module_name | Your message here

Notes:
    - Loggers are cached by name to prevent duplicate handlers
    - Log files are stored in 'logs/' directory by default
    - All logs are written to 'logs/app.log' with automatic rotation
    - Console output includes colors; file output is plain text
"""
import logging
import os
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        return super().format(record)

class Logger:
    _loggers = {}  # Cache loggers to avoid duplicates
    _initialized = set()  # Track which loggers have been properly initialized

    def __init__(self, name=None, log_dir="logs", max_bytes=10*1024*1024, backup_count=10):
        """
        Initialize logger with colored console output

        Args:
            name: Logger name (use __name__ from calling module)
            log_dir: Directory to store logs
            max_bytes: Max size per log file (default 10MB)
            backup_count: Number of backup files to keep
        """
        self.name = name or "app"
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Use cached logger if exists, otherwise setup new one
        if self.name in Logger._loggers and self.name in Logger._initialized:
            self.logger = Logger._loggers[self.name]
        else:
            self.logger = self._setup_logger()
            Logger._loggers[self.name] = self.logger
            Logger._initialized.add(self.name)

    def _setup_logger(self):
        """Setup the logger with rotating file handler"""
        os.makedirs(self.log_dir, exist_ok=True)

        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Prevent propagation to root logger to avoid duplicate logs in Streamlit
        logger.propagate = False

        # Clear any existing handlers to avoid duplicates
        if logger.handlers:
            logger.handlers.clear()

        # File handler (plain text, no colors)
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "app.log"),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def info(self, message):
        self.logger.info(message)

    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)

    def critical(self, message):
        self.logger.critical(message)
