"""
JSON logging configuration with rotation for Digital Workshop application.

This module provides a centralized logging configuration with JSON formatting
and rotating file handlers to ensure efficient log management without memory leaks.
"""

import json
import logging
import logging.handlers
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter that creates structured log entries.

    Formats log records as JSON with timestamp, level, logger, function, line, and message.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log entry as string
        """
        # Create the base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "module": record.module,
            "thread": record.thread,
            "process": record.process
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'exc_info', 'exc_text', 'stack_info'
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class TimestampRotatingFileHandler(logging.Handler):
    """
    Custom file handler that creates new log files with timestamp-based naming.

    Creates new log files with format: "Log - MMDDYY-HH-MM-SS <Level>.txt"
    """

    def __init__(self, log_dir: str = "logs", max_bytes: int = 10*1024*1024,
                 backup_count: int = 5):
        """
        Initialize the timestamp rotating file handler.

        Args:
            log_dir: Directory to store log files
            max_bytes: Maximum bytes before rotation
            backup_count: Number of backup files to keep
        """
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.current_file = None
        self.current_level = "INFO"
        self.stream = None

    def _get_log_filename(self, level: str) -> str:
        """
        Generate a timestamp-based log filename.

        Args:
            level: Log level for the filename

        Returns:
            Formatted log filename
        """
        timestamp = datetime.now().strftime("%m%d%y-%H-%M-%S")
        return f"Log - {timestamp} {level}.txt"

    def _rotate_if_needed(self, level: str) -> None:
        """
        Rotate log file if needed based on size or level change.

        Args:
            level: Current log level
        """
        # Initialize stream if needed
        if not self.stream:
            self._rotate_file()
            return

        # Check if we need to rotate due to level change
        if self.current_level != level:
            self._rotate_file()
            self.current_level = level
            return

        # Check if we need to rotate due to size
        if self.stream.tell() >= self.max_bytes:
            self._rotate_file()

    def _rotate_file(self) -> None:
        """
        Close current file and create a new one with timestamp.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Clean up old log files if we have too many
        self._cleanup_old_logs()

        # Create new log file
        filename = self._get_log_filename(self.current_level)
        self.current_file = self.log_dir / filename
        self.stream = open(self.current_file, 'w', encoding='utf-8')

    def _cleanup_old_logs(self) -> None:
        """
        Remove old log files if we exceed the backup count.
        """
        log_files = list(self.log_dir.glob("Log - *.txt"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Keep only the most recent files
        for log_file in log_files[self.backup_count:]:
            try:
                log_file.unlink()
            except OSError:
                pass  # Ignore errors when removing files

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the file.

        Args:
            record: The log record to emit
        """
        try:
            # Rotate if needed
            self._rotate_if_needed(record.levelname)

            # Ensure we have an open file
            if not self.stream:
                self._rotate_file()

            # Format and write the log entry
            msg = self.format(record)
            self.stream.write(msg + '\n')
            self.stream.flush()

        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """
        Close the handler and any open files.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        super().close()


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_console: bool = True,
    max_bytes: int = 10*1024*1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up JSON logging with rotation for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_console: Whether to enable console logging
        max_bytes: Maximum bytes before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Create the application logger
    logger = logging.getLogger("Digital Workshop")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Add timestamp rotating file handler
    file_handler = TimestampRotatingFileHandler(
        log_dir=log_dir,
        max_bytes=max_bytes,
        backup_count=backup_count
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    # Add console handler if requested
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"Digital Workshop.{name}")


def log_function_call(logger: logging.Logger):
    """
    Decorator to automatically log function calls with parameters and return values.

    Args:
        logger: Logger instance to use for logging

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create a custom log record to avoid conflicts with reserved attributes
            try:
                logger.debug(
                    f"Calling {func.__name__}",
                    extra={
                        "custom_function": func.__name__,
                        "custom_args": str(args),
                        "custom_kwargs": str(kwargs)
                    }
                )
            except:
                # If logging fails, continue with the function
                pass

            try:
                result = func(*args, **kwargs)
                try:
                    logger.debug(
                        f"Completed {func.__name__}",
                        extra={
                            "custom_function": func.__name__,
                            "custom_result": str(result)[:100]  # Limit result length
                        }
                    )
                except:
                    # If logging fails, continue with the function
                    pass
                return result
            except Exception as e:
                try:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        extra={
                            "custom_function": func.__name__,
                            "custom_error_type": type(e).__name__,
                            "custom_error_message": str(e)
                        }
                    )
                except:
                    # If logging fails, continue with the exception
                    pass
                raise
        return wrapper
    return decorator
