"""
JSON logging configuration with rotation for Digital Workshop application.

Provides standardized logging profiles, shared formatters/filters, and a singleton
LoggingManager that guarantees consistent handler configuration across the process.
"""

import json
import logging
import logging.handlers
import os
import sys
import threading
import traceback
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import functools

from .installation_detector import get_installation_type
from .path_manager import get_log_directory
from .version_manager import get_logger_name


@dataclass(frozen=True)
class LoggingProfile:
    """Immutable logging profile describing runtime logging preferences."""

    log_level: str = "INFO"
    enable_console: bool = False
    human_readable: bool = False
    log_dir: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5
    correlation_id: Optional[str] = None

    def merged(self, **overrides: Any) -> "LoggingProfile":
        """Return a copy of this profile with overrides applied."""
        cleaned = {k: v for k, v in overrides.items() if v is not None}
        if not cleaned:
            return self
        return replace(self, **cleaned)


class StructuredContextFilter(logging.Filter):
    """Injects shared structured metadata into every record."""

    def __init__(self, correlation_provider) -> None:
        super().__init__()
        self._correlation_provider = correlation_provider
        self._installation_type = get_installation_type().value
        self._app_version = None
        self._lock = threading.Lock()

    def _app_version_value(self) -> str:
        if self._app_version is None:
            with self._lock:
                if self._app_version is None:
                    try:
                        from .version_manager import get_display_version

                        self._app_version = get_display_version()
                    except Exception:
                        self._app_version = "unknown"
        return self._app_version

    def filter(self, record: logging.LogRecord) -> bool:
        record.app_version = self._app_version_value()
        record.installation_type = self._installation_type
        record.process_id = os.getpid()
        record.thread_id = threading.get_ident()
        correlation_id = self._correlation_provider()
        record.correlation_id = correlation_id if correlation_id else "-"
        return True


class SimpleFormatter(logging.Formatter):
    """Simple text formatter for activity messages."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        return f"[{timestamp}] {record.getMessage()}"


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for logs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger_name = record.name.split(".")[-1]
        message = record.getMessage()

        if record.exc_info:
            message += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return f"[{timestamp}] {level} | {logger_name:20s} | {message}"


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter that creates structured log entries."""

    def format(self, record: logging.LogRecord) -> str:
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
            "app_version": getattr(record, "app_version", "unknown"),
            "installation_type": getattr(record, "installation_type", "unknown"),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }

        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        for key, value in record.__dict__.items():
            if key in log_entry:
                continue
            if key.startswith("_"):
                continue
            if key in {
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
            }:
                continue
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
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.current_file = None
        self.current_level = "INFO"
        self.stream = None

    def _get_log_filename(self, level: str) -> str:
        timestamp = datetime.now().strftime("%m%d%y-%H-%M-%S")
        return f"Log - {timestamp} {level}.txt"

    def _rotate_if_needed(self, level: str) -> None:
        if not self.stream:
            self._rotate_file()
            return

        if self.current_level != level:
            self._rotate_file()
            self.current_level = level
            return

        if self.stream.tell() >= self.max_bytes:
            self._rotate_file()

    def _rotate_file(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None

        self._cleanup_old_logs()
        filename = self._get_log_filename(self.current_level)
        self.current_file = self.log_dir / filename
        self.stream = open(self.current_file, "w", encoding="utf-8")

    def _cleanup_old_logs(self) -> None:
        log_files = list(self.log_dir.glob("Log - *.txt"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for log_file in log_files[self.backup_count :]:
            try:
                log_file.unlink()
            except OSError:
                pass

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._rotate_if_needed(record.levelname)
            if not self.stream:
                self._rotate_file()

            msg = self.format(record)
            self.stream.write(msg + "\n")
            self.stream.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None
        super().close()


class LoggingManager:
    """Singleton manager that owns all logging handlers for the process."""

    _instance: Optional["LoggingManager"] = None
    _instance_lock = threading.RLock()

    _SPECIAL_LOGGERS: Dict[str, Dict[str, Any]] = {
        "security": {"filename": "security.log", "level": logging.WARNING},
        "performance": {"filename": "performance.log", "level": logging.INFO},
        "errors": {"filename": "errors.log", "level": logging.ERROR},
    }

    def __init__(self, profile: LoggingProfile) -> None:
        self._lock = threading.RLock()
        self._profile = profile
        self._thread_context = threading.local()
        self._base_logger_name = get_logger_name()
        self._base_logger = logging.getLogger(self._base_logger_name)
        self._structured_filter = StructuredContextFilter(self._current_correlation_id)
        self._formatter = self._create_formatter()
        self._handlers_initialized = False
        self._log_directory = self._resolve_log_directory()

    @classmethod
    def get_instance(cls, profile: Optional[LoggingProfile] = None) -> "LoggingManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = LoggingManager(profile or LoggingProfile())
            elif profile is not None:
                cls._instance.configure(profile)
        return cls._instance

    def configure(self, profile: Optional[LoggingProfile] = None) -> None:
        with self._lock:
            if profile is not None:
                self._profile = profile
            self._structured_filter = StructuredContextFilter(self._current_correlation_id)
            self._formatter = self._create_formatter()
            self._log_directory = self._resolve_log_directory()
            self._handlers_initialized = False

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        self._ensure_handlers()
        if name:
            return logging.getLogger(f"{self._base_logger_name}.{name}")
        return self._base_logger

    def get_activity_logger(self, name: str) -> logging.Logger:
        self._ensure_handlers()
        logger = logging.getLogger(f"{self._base_logger_name}.Activity.{name}")
        self._reset_handlers(logger)

        handler = logging.StreamHandler(sys.stdout)
        self._decorate_handler(handler)
        handler.setLevel(logging.INFO)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    def set_correlation_id(self, correlation_id: Optional[str]) -> None:
        if correlation_id:
            self._thread_context.correlation_id = correlation_id
        else:
            self.clear_correlation_id()

    def clear_correlation_id(self) -> None:
        if hasattr(self._thread_context, "correlation_id"):
            del self._thread_context.correlation_id

    def _current_correlation_id(self) -> Optional[str]:
        return getattr(self._thread_context, "correlation_id", self._profile.correlation_id)

    def _ensure_handlers(self) -> None:
        with self._lock:
            if self._handlers_initialized:
                return
            self._apply_base_logger_settings()
            self._install_application_handler()
            self._install_console_handler()
            self._install_special_handlers()
            self._handlers_initialized = True

    def _apply_base_logger_settings(self) -> None:
        self._base_logger.propagate = False
        self._base_logger.setLevel(self._level_value(self._profile.log_level))
        self._reset_handlers(self._base_logger)

    def _install_application_handler(self) -> None:
        handler = TimestampRotatingFileHandler(
            log_dir=str(self._log_directory),
            max_bytes=self._profile.max_bytes,
            backup_count=self._profile.backup_count,
        )
        self._decorate_handler(handler)
        self._base_logger.addHandler(handler)

    def _install_console_handler(self) -> None:
        if not self._profile.enable_console:
            return
        console_handler = logging.StreamHandler(sys.stdout)
        self._decorate_handler(console_handler)
        console_handler.setLevel(self._level_value(self._profile.log_level))
        self._base_logger.addHandler(console_handler)

    def _install_special_handlers(self) -> None:
        for key, config in self._SPECIAL_LOGGERS.items():
            logger = logging.getLogger(f"{self._base_logger_name}.{key}")
            self._reset_handlers(logger)

            log_path = self._log_directory / config["filename"]
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=self._profile.max_bytes,
                backupCount=self._profile.backup_count,
                encoding="utf-8",
            )
            self._decorate_handler(file_handler)
            file_handler.setLevel(config["level"])

            logger.addHandler(file_handler)
            logger.setLevel(config["level"])
            logger.propagate = False

    def _decorate_handler(self, handler: logging.Handler) -> None:
        handler.setFormatter(self._formatter)
        handler.addFilter(self._structured_filter)

    def _reset_handlers(self, logger: logging.Logger) -> None:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass

    def _level_value(self, level_name: str) -> int:
        return getattr(logging, str(level_name).upper(), logging.INFO)

    def _create_formatter(self) -> logging.Formatter:
        if self._profile.human_readable:
            return HumanReadableFormatter()
        return JSONFormatter()

    def _resolve_log_directory(self) -> Path:
        if not self._profile.log_dir or self._profile.log_dir == "logs":
            directory = get_log_directory()
        else:
            directory = Path(self._profile.log_dir)

        directory.mkdir(parents=True, exist_ok=True)
        return directory


def _coerce_profile(
    candidate: Optional[Union[LoggingProfile, Dict[str, Any]]],
    defaults: Dict[str, Any],
) -> LoggingProfile:
    """Coerce various profile inputs into a concrete :class:`LoggingProfile`.

    When a concrete :class:`LoggingProfile` instance is provided, we *respect it
    as-is* and do not merge in defaults. Callers that need to start from
    defaults and override individual fields should pass a ``dict`` instead.
    """

    defaults = {k: v for k, v in defaults.items() if k != "profile"}

    # Explicit profile: use it directly, do not overwrite fields like
    # ``log_level`` or ``enable_console`` with function defaults.
    if isinstance(candidate, LoggingProfile):
        return candidate

    # Dict profile: merge with defaults so callers can override specific keys.
    if isinstance(candidate, dict):
        combined = {**defaults, **candidate}
        return LoggingProfile(**combined)

    # No explicit profile: construct from defaults only.
    return LoggingProfile(**defaults)


def _prepare_profile_kwargs(**kwargs: Any) -> Dict[str, Any]:
    log_dir = kwargs.get("log_dir")
    if log_dir == "logs":
        kwargs["log_dir"] = None
    return kwargs


def setup_logging(
    log_level: Union[str, LoggingProfile, Dict[str, Any]] = "INFO",
    log_dir: Optional[str] = None,
    enable_console: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    human_readable: bool = False,
    profile: Optional[Union[LoggingProfile, Dict[str, Any]]] = None,
    **kwargs: Any,
) -> logging.Logger:
    """
    Configure logging according to the provided profile and return the base logger.

    Existing callers can continue to provide the original keyword arguments or pass
    an explicit LoggingProfile/dict via the profile argument.
    """
    profile_candidate = profile
    if isinstance(log_level, (LoggingProfile, dict)):
        profile_candidate = log_level
        log_level = "INFO"

    defaults = _prepare_profile_kwargs(
        log_level=log_level,
        log_dir=log_dir,
        enable_console=enable_console,
        max_bytes=max_bytes,
        backup_count=backup_count,
        human_readable=human_readable,
        **kwargs,
    )

    resolved_profile = _coerce_profile(profile_candidate, defaults)
    manager = LoggingManager.get_instance(resolved_profile)
    return manager.get_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a child logger instance with the specified name."""
    manager = LoggingManager.get_instance()
    return manager.get_logger(name)


def get_activity_logger(name: str) -> logging.Logger:
    """
    Get an activity logger that always logs to console with shared formatter/filter.

    These messages are always shown in the console regardless of --log-console flag.
    """
    manager = LoggingManager.get_instance()
    return manager.get_activity_logger(name)


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set the correlation identifier for the current thread."""
    LoggingManager.get_instance().set_correlation_id(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation identifier for the current thread."""
    LoggingManager.get_instance().clear_correlation_id()


def log_function_call(*decorator_args, **decorator_kwargs):
    """Flexible function-call logging decorator.

    This decorator intentionally supports multiple usage patterns so older
    call sites remain valid:

    - ``@log_function_call``                        -> derive logger from function's module
    - ``@log_function_call(enable_logging=True)``   -> same, with verbose logging
    - ``@log_function_call(logger)``                -> explicit logger instance
    - ``@log_function_call(logger, enable_logging=True)``

    Args:
        decorator_args: Positional arguments (either a logger or the function).
        decorator_kwargs: Keyword arguments, may include ``enable_logging``.
    """

    enable_logging = decorator_kwargs.get("enable_logging", False)

    def _make_wrapper(func, logger: logging.Logger):
        """Create the actual wrapper around *func* using *logger*."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if enable_logging:
                try:
                    logger.debug(
                        "Calling %s",
                        func.__name__,
                        extra={
                            "custom_function": func.__name__,
                            "custom_args": str(args),
                            "custom_kwargs": str(kwargs),
                        },
                    )
                except Exception:
                    # Logging must never break the wrapped function.
                    pass

            try:
                result = func(*args, **kwargs)
                if enable_logging:
                    try:
                        logger.debug(
                            "Completed %s",
                            func.__name__,
                            extra={
                                "custom_function": func.__name__,
                                "custom_result": str(result)[:100],
                            },
                        )
                    except Exception:
                        pass
                return result
            except Exception as exc:
                try:
                    logger.error(
                        "Error in %s: %s",
                        func.__name__,
                        str(exc),
                        extra={
                            "custom_function": func.__name__,
                            "custom_error_type": type(exc).__name__,
                            "custom_error_message": str(exc),
                        },
                    )
                except Exception:
                    pass
                raise

        return wrapper

    # Case 1: Used directly as ``@log_function_call`` (no parentheses).
    if decorator_args and callable(decorator_args[0]) and not isinstance(
        decorator_args[0], logging.Logger
    ):
        func = decorator_args[0]
        derived_logger = logging.getLogger(func.__module__)
        return _make_wrapper(func, derived_logger)

    # Case 2: Used as ``@log_function_call(logger, ...)`` or
    # ``@log_function_call()``. In these cases we return a classic decorator
    # that will receive *func* later.
    explicit_logger = None
    if decorator_args and isinstance(decorator_args[0], logging.Logger):
        explicit_logger = decorator_args[0]

    def decorator(func):
        logger_to_use = explicit_logger or logging.getLogger(func.__module__)
        return _make_wrapper(func, logger_to_use)

    return decorator
