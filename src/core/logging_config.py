"""
JSON logging configuration with rotation for Digital Workshop application.

This module provides a centralized logging configuration with JSON formatting
and rotating file handlers to ensure efficient log management without memory leaks.
"""

import json
import logging
import logging.handlers
import sys
import traceback
from datetime import datetime
from pathlib import Path


class SimpleFormatter(logging.Formatter):
    """
    Simple text formatter for activity messages.

    Formats log records as simple text with timestamp and message only.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as simple text.

        Args:
            record: The log record to format

        Returns:
            Simple formatted log entry as string
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        return f"[{timestamp}] {record.getMessage()}"


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for logs.

    Formats log records as readable text with timestamp, level, logger, and message.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as human-readable text.

        Args:
            record: The log record to format

        Returns:
            Human-readable formatted log entry as string
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger = record.name.split(".")[-1]  # Get last part of logger name

        # Format the message
        msg = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            msg += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return f"[{timestamp}] {level} | {logger:20s} | {msg}"


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter that creates structured log entries.

    Formats log records as JSON with timestamp, level, logger, function, line, and message.
    Excludes taskname field to avoid null values.
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
            "process": record.process,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if present (excluding taskname and other standard fields)
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskname",
                "taskName",  # Exclude taskname variants
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class TimestampRotatingFileHandler(logging.Handler):
    """
    Custom file handler that creates new log files with timestamp-based naming.

    Creates new log files with format: "Log - MMDDYY-HH-MM-SS <Level>.txt"
    """

    def __init__(
        self,
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
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
        self.stream = open(self.current_file, "w", encoding="utf-8")

    def _cleanup_old_logs(self) -> None:
        """
        Remove old log files if we exceed the backup count.
        """
        log_files = list(self.log_dir.glob("Log - *.txt"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Keep only the most recent files
        for log_file in log_files[self.backup_count :]:
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
            self.stream.write(msg + "\n")
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
    enable_console: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    human_readable: bool = False,
) -> logging.Logger:
    """
    Set up logging with rotation for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_console: Whether to enable console logging (default: False, logs go to file only)
        max_bytes: Maximum bytes before rotation
        backup_count: Number of backup files to keep
        human_readable: Whether to use human-readable format instead of JSON (default: False)

    Returns:
        Configured logger instance
    """
    # Use installation-type aware log directory if default is used
    if log_dir == "logs":
        from .path_manager import get_log_directory

        log_dir = str(get_log_directory())

    # Create the application logger
    from .version_manager import get_logger_name

    logger = logging.getLogger(get_logger_name())
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create appropriate formatter
    if human_readable:
        formatter = HumanReadableFormatter()
    else:
        formatter = JSONFormatter()

    # Add timestamp rotating file handler
    file_handler = TimestampRotatingFileHandler(
        log_dir=log_dir, max_bytes=max_bytes, backup_count=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add console handler if requested
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
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
    from .version_manager import get_logger_name

    logger_name = get_logger_name()
    return logging.getLogger(f"{logger_name}.{name}")


def get_activity_logger(name: str) -> logging.Logger:
    """
    Get an activity logger that always logs to console with simple formatting.

    Used for user-visible activities like importing, rendering, analyzing models.
    These messages are always shown in the console regardless of --log-console flag.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Activity logger instance
    """
    from .version_manager import get_logger_name

    logger_name = get_logger_name()
    logger = logging.getLogger(f"{logger_name}.Activity.{name}")

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set to INFO level to show activity messages
    logger.setLevel(logging.INFO)

    # Add console handler with simple formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SimpleFormatter())
    logger.addHandler(console_handler)

    # Prevent propagation to parent logger to avoid duplicate messages
    logger.propagate = False

    return logger


def log_function_call(logger: logging.Logger, enable_logging: bool = False):
    """
    Decorator to automatically log function calls with parameters and return values.

    Args:
        logger: Logger instance to use for logging
        enable_logging: Whether to enable function call logging (default: False for less verbose output)

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Only log if explicitly enabled
            if enable_logging:
                try:
                    logger.debug(
                        f"Calling {func.__name__}",
                        extra={
                            "custom_function": func.__name__,
                            "custom_args": str(args),
                            "custom_kwargs": str(kwargs),
                        },
                    )
                except:
                    # If logging fails, continue with the function
                    pass

            try:
                result = func(*args, **kwargs)
                if enable_logging:
                    try:
                        logger.debug(
                            f"Completed {func.__name__}",
                            extra={
                                "custom_function": func.__name__,
                                "custom_result": str(result)[
                                    :100
                                ],  # Limit result length
                            },
                        )
                    except:
                        # If logging fails, continue with the function
                        pass
                return result
            except Exception as e:
                # Always log errors regardless of enable_logging setting
                try:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        extra={
                            "custom_function": func.__name__,
                            "custom_error_type": type(e).__name__,
                            "custom_error_message": str(e),
                        },
                    )
                except:
                    # If logging fails, continue with the exception
                    pass
                raise

        return wrapper

    return decorator
