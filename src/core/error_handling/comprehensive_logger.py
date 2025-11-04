"""
Comprehensive Logging System

This module provides structured JSON logging with performance monitoring,
context-aware logging, and integration with the error reporting system.
"""

import json
import logging
import logging.handlers
import time
import threading
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import psutil
import traceback

from .error_categories import ErrorSeverity


@dataclass
class LogContext:
    """Context information for structured logging."""

    operation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    function: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    timestamp: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize timestamp and system info if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.thread_id is None:
            self.thread_id = threading.get_ident()
        if self.process_id is None:
            self.process_id = os.getpid()
        if self.custom_fields is None:
            self.custom_fields = {}


@dataclass
class PerformanceMetrics:
    """Performance metrics for logging."""

    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    operation_count: int = 0
    error_count: int = 0

    def finalize(self):
        """Calculate final metrics."""
        if self.end_time is None:
            self.end_time = time.time()
        if self.duration_ms is None:
            self.duration_ms = (self.end_time - self.start_time) * 1000

        # Get current system metrics
        process = psutil.Process()
        self.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        self.cpu_percent = process.cpu_percent()


class ComprehensiveLogger:
    """
    Comprehensive logger with structured JSON output, performance monitoring,
    and context-aware logging.
    """

    def __init__(
        self,
        log_dir: Path,
        max_log_size: int = 50 * 1024 * 1024,  # 50MB
        backup_count: int = 5,
        enable_performance_logging: bool = True,
        enable_system_metrics: bool = True,
    ):
        """
        Initialize comprehensive logger.

        Args:
            log_dir: Directory for log files
            max_log_size: Maximum size of individual log files
            backup_count: Number of backup files to keep
            enable_performance_logging: Whether to log performance metrics
            enable_system_metrics: Whether to include system metrics
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.enable_performance_logging = enable_performance_logging
        self.enable_system_metrics = enable_system_metrics

        # Thread safety
        self._lock = threading.RLock()

        # Performance tracking
        self.active_operations: Dict[str, PerformanceMetrics] = {}
        self.operation_stats: Dict[str, Dict[str, Any]] = {}

        # Setup loggers
        self._setup_loggers()

        # System info cache
        self._system_info = self._get_system_info() if enable_system_metrics else {}

    def _setup_loggers(self):
        """Setup structured loggers for different purposes."""
        # Main application logger
        self.app_logger = logging.getLogger("app")
        self.app_logger.setLevel(logging.DEBUG)

        # Error logger (for error reports)
        self.error_logger = logging.getLogger("error")
        self.error_logger.setLevel(logging.ERROR)

        # Performance logger
        self.performance_logger = logging.getLogger("performance")
        self.performance_logger.setLevel(logging.INFO)

        # Security logger
        self.security_logger = logging.getLogger("security")
        self.security_logger.setLevel(logging.WARNING)

        # Remove existing handlers
        for logger in [
            self.app_logger,
            self.error_logger,
            self.performance_logger,
            self.security_logger,
        ]:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        # Setup JSON file handlers
        self._setup_json_file_handler(self.app_logger, "app.log")
        self._setup_json_file_handler(self.error_logger, "errors.log")
        self._setup_json_file_handler(self.performance_logger, "performance.log")
        self._setup_json_file_handler(self.security_logger, "security.log")

        # Setup console handlers for critical errors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.error_logger.addHandler(console_handler)

    def _setup_json_file_handler(self, logger: logging.Logger, filename: str):
        """Setup JSON file handler with rotation."""
        log_file = self.log_dir / filename

        # Rotating file handler with JSON formatting
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )

        handler.setLevel(logging.DEBUG)

        # JSON formatter
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for logging."""
        try:
            return {
                "platform": sys.platform,
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "disk_usage": {
                    "total_gb": psutil.disk_usage("/").total / 1024 / 1024 / 1024,
                    "free_gb": psutil.disk_usage("/").free / 1024 / 1024 / 1024,
                },
            }
        except Exception:
            return {}

    def _create_log_entry(
        self,
        level: str,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception_info: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Create structured log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": "comprehensive_logger",
            "thread_id": threading.get_ident(),
            "process_id": os.getpid(),
        }

        # Add context information
        if context:
            entry["context"] = asdict(context)

        # Add system info if enabled
        if self.enable_system_metrics and self._system_info:
            entry["system_info"] = self._system_info

        # Add extra data
        if extra_data:
            entry["extra"] = extra_data

        # Add exception info if provided
        if exception_info:
            entry["exception"] = {
                "type": exception_info[0].__name__ if exception_info[0] else None,
                "message": str(exception_info[1]) if exception_info[1] else None,
                "traceback": (
                    traceback.format_exception(*exception_info)
                    if exception_info[0]
                    else None
                ),
            }

        return entry

    def _log_structured(
        self,
        logger: logging.Logger,
        level: str,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception_info: Optional[Any] = None,
    ):
        """Log structured JSON entry."""
        try:
            log_entry = self._create_log_entry(
                level, message, context, extra_data, exception_info
            )
            log_line = json.dumps(log_entry, default=str)

            # Log to appropriate logger
            if level == "CRITICAL":
                logger.critical(log_line)
            elif level == "ERROR":
                logger.error(log_line)
            elif level == "WARNING":
                logger.warning(log_line)
            elif level == "INFO":
                logger.info(log_line)
            else:  # DEBUG
                logger.debug(log_line)

        except Exception as e:
            # Fallback to basic logging if structured logging fails
            logger.error(f"Structured logging failed: {e}")
            logger.error(f"Original message: {message}")

    def log_info(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Log info message."""
        with self._lock:
            self._log_structured(self.app_logger, "INFO", message, context, extra_data)

    def log_warning(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Log warning message."""
        with self._lock:
            self._log_structured(
                self.app_logger, "WARNING", message, context, extra_data
            )

    def log_error(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception_info: Optional[Any] = None,
    ):
        """Log error message."""
        with self._lock:
            self._log_structured(
                self.error_logger, "ERROR", message, context, extra_data, exception_info
            )

    def log_critical(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception_info: Optional[Any] = None,
    ):
        """Log critical message."""
        with self._lock:
            self._log_structured(
                self.error_logger,
                "CRITICAL",
                message,
                context,
                extra_data,
                exception_info,
            )

    def log_debug(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Log debug message."""
        with self._lock:
            self._log_structured(self.app_logger, "DEBUG", message, context, extra_data)

    def log_security(
        self,
        message: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Log security-related message."""
        with self._lock:
            self._log_structured(
                self.security_logger, "WARNING", message, context, extra_data
            )

    def start_operation(
        self,
        operation_id: str,
        operation_name: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Start tracking an operation for performance monitoring."""
        with self._lock:
            metrics = PerformanceMetrics(start_time=time.time())
            self.active_operations[operation_id] = metrics

            # Log operation start
            log_context = context or LogContext()
            log_context.operation_id = operation_id
            log_context.function = operation_name

            self.log_info(
                f"Operation started: {operation_name}", log_context, extra_data
            )

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """End tracking an operation and log performance metrics."""
        with self._lock:
            if operation_id not in self.active_operations:
                self.log_warning(
                    f"Operation {operation_id} not found in active operations"
                )
                return

            metrics = self.active_operations.pop(operation_id)
            metrics.finalize()

            # Update statistics
            if operation_id not in self.operation_stats:
                self.operation_stats[operation_id] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "avg_duration_ms": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "min_duration_ms": float("inf"),
                    "max_duration_ms": 0,
                }

            stats = self.operation_stats[operation_id]
            stats["count"] += 1
            stats["total_duration_ms"] += metrics.duration_ms
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
            stats["min_duration_ms"] = min(
                stats["min_duration_ms"], metrics.duration_ms
            )
            stats["max_duration_ms"] = max(
                stats["max_duration_ms"], metrics.duration_ms
            )

            if success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
                metrics.error_count += 1

            # Log operation completion
            log_context = context or LogContext()
            log_context.operation_id = operation_id

            performance_data = {
                "duration_ms": metrics.duration_ms,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_percent": metrics.cpu_percent,
                "success": success,
                "statistics": stats,
            }

            if extra_data:
                performance_data.update(extra_data)

            if success:
                self.log_info(
                    f"Operation completed: {operation_id}",
                    log_context,
                    performance_data,
                )
            else:
                self.log_error(
                    f"Operation failed: {operation_id}", log_context, performance_data
                )

            # Log performance metrics if enabled
            if self.enable_performance_logging:
                self._log_structured(
                    self.performance_logger,
                    "INFO",
                    f"Performance metrics for {operation_id}",
                    log_context,
                    performance_data,
                )

    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get operation performance statistics."""
        with self._lock:
            return {
                "active_operations": len(self.active_operations),
                "operation_statistics": self.operation_stats.copy(),
                "system_info": self._system_info,
            }

    def log_error_report(self, error_report, context: Optional[LogContext] = None):
        """Log error report from error reporter."""
        log_context = context or LogContext()
        log_context.component = "error_reporter"

        error_data = {
            "error_type": error_report.error_type,
            "error_message": error_report.error_message,
            "severity": error_report.classification.severity.value,
            "category": error_report.classification.category.value,
            "context": error_report.context.value,
            "stack_trace": error_report.stack_trace,
            "system_info": error_report.system_info,
            "recovery_strategy": (
                error_report.classification.recovery_strategy.value
                if error_report.classification.recovery_strategy
                else None
            ),
        }

        if error_report.classification.severity == ErrorSeverity.CRITICAL:
            self.log_critical(
                f"Critical error reported: {error_report.error_type}",
                log_context,
                error_data,
            )
        else:
            self.log_error(
                f"Error reported: {error_report.error_type}", log_context, error_data
            )

    @contextmanager
    def operation_context(
        self,
        operation_name: str,
        context: Optional[LogContext] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for operation tracking."""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"

        try:
            self.start_operation(operation_id, operation_name, context, extra_data)
            yield operation_id
        except Exception as e:
            self.end_operation(
                operation_id,
                success=False,
                context=context,
                extra_data={"error": str(e), "exception_type": type(e).__name__},
            )
            raise
        else:
            self.end_operation(
                operation_id, success=True, context=context, extra_data=extra_data
            )


# Global logger instance
_global_logger: Optional[ComprehensiveLogger] = None


def get_global_logger() -> ComprehensiveLogger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        log_dir = Path("logs")
        _global_logger = ComprehensiveLogger(log_dir)
    return _global_logger


def set_global_logger(logger: ComprehensiveLogger) -> None:
    """Set the global logger instance."""
    global _global_logger
    _global_logger = logger


# Convenience functions
def log_info(
    message: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """Log info message using global logger."""
    get_global_logger().log_info(message, context, extra_data)


def log_warning(
    message: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """Log warning message using global logger."""
    get_global_logger().log_warning(message, context, extra_data)


def log_error(
    message: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    exception_info: Optional[Any] = None,
):
    """Log error message using global logger."""
    get_global_logger().log_error(message, context, extra_data, exception_info)


def log_critical(
    message: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    exception_info: Optional[Any] = None,
):
    """Log critical message using global logger."""
    get_global_logger().log_critical(message, context, extra_data, exception_info)


def log_debug(
    message: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """Log debug message using global logger."""
    get_global_logger().log_debug(message, context, extra_data)


@contextmanager
def operation_context(
    operation_name: str,
    context: Optional[LogContext] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    """Context manager for operation tracking using global logger."""
    with get_global_logger().operation_context(
        operation_name, context, extra_data
    ) as operation_id:
        yield operation_id
