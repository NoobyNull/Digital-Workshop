"""Centralized Logging Service for Candy-Cadence

This module provides a unified logging service that integrates all logging components
including JSON formatting, error handling, security logging, and performance monitoring.
"""

import logging
import logging.handlers
import time
import threading
import functools
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .logging_config import (
    get_logger,
    setup_logging,
    JSONFormatter,
    TimestampRotatingFileHandler,
)
from .enhanced_error_handler import (
    EnhancedErrorHandler,
)


class LogLevel(Enum):
    """Standardized log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityEventType(Enum):
    """Types of security events for logging."""

    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_DENIED = "authorization_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_ACCESS = "system_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class SecurityEvent:
    """Security event data structure."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: SecurityEventType = SecurityEventType.SUSPICIOUS_ACTIVITY
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: str = "unknown"
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"
    correlation_id: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""
    duration: float = 0.0
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CentralizedLoggingService:
    """
    Centralized logging service that provides unified logging across the application.

    Features:
    - JSON-formatted logging with structured data
    - Security event logging with audit trails
    - Performance monitoring and metrics
    - Error handling integration
    - Configurable log levels and outputs
    - Log rotation and retention
    - Correlation ID tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the centralized logging service.

        Args:
            config: Configuration dictionary for logging settings
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.error_handler = EnhancedErrorHandler(self.config.get("error_handler", {}))

        # Thread safety
        self._lock = threading.RLock()

        # Security event tracking
        self._security_logger = get_logger("security")
        self._security_events: List[SecurityEvent] = []

        # Performance metrics
        self._performance_logger = get_logger("performance")
        self._performance_metrics: List[PerformanceMetric] = []

        # Correlation ID tracking
        self._correlation_context: Dict[str, Any] = {}

        # Configuration
        self.max_security_events = self.config.get("max_security_events", 10000)
        self.max_performance_metrics = self.config.get("max_performance_metrics", 10000)
        self.enable_correlation_tracking = self.config.get("enable_correlation_tracking", True)
        self.enable_performance_logging = self.config.get("enable_performance_logging", True)
        self.enable_security_logging = self.config.get("enable_security_logging", True)

        # Setup security and performance loggers
        self._setup_security_logging()
        self._setup_performance_logging()

        self.logger.info("Centralized logging service initialized")

    def _setup_security_logging(self) -> None:
        """Setup dedicated security logging."""
        if not self.enable_security_logging:
            return

        # Configure security logger
        security_handler = TimestampRotatingFileHandler(
            "logs/security.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        security_handler.setFormatter(JSONFormatter())
        security_handler.setLevel(logging.WARNING)

        self._security_logger.addHandler(security_handler)
        self._security_logger.setLevel(logging.WARNING)
        self._security_logger.propagate = False

    def _setup_performance_logging(self) -> None:
        """Setup dedicated performance logging."""
        if not self.enable_performance_logging:
            return

        # Configure performance logger
        performance_handler = TimestampRotatingFileHandler(
            "logs/performance.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        performance_handler.setFormatter(JSONFormatter())
        performance_handler.setLevel(logging.INFO)

        self._performance_logger.addHandler(performance_handler)
        self._performance_logger.setLevel(logging.INFO)
        self._performance_logger.propagate = False

    def log_info(self, message: str, **kwargs) -> None:
        """Log an info message with structured data."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message with structured data."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def log_error(
        self,
        error: Union[Exception, str],
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> bool:
        """Log an error with comprehensive handling.

        Args:
            error: Exception or error message
            context: Optional context information
            **kwargs: Additional structured data

        Returns:
            True if error was handled successfully
        """
        try:
            if isinstance(error, Exception):
                return self.error_handler.handle_error(error, context)
            else:
                # Log as regular error message
                self._log_with_context(logging.ERROR, str(error), **kwargs)
                return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as handling_error:
            self.logger.error("Error logging failed: %s", str(handling_error), exc_info=True)
            return False

    def log_critical(self, message: str, **kwargs) -> None:
        """Log a critical message with structured data."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)

    def log_debug(self, message: str, **kwargs) -> None:
        """Log a debug message with structured data."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event with audit trail."""
        if not self.enable_security_logging:
            return

        try:
            with self._lock:
                self._security_events.append(event)

                # Maintain event history size
                if len(self._security_events) > self.max_security_events:
                    self._security_events = self._security_events[-self.max_security_events :]

            # Log the security event
            log_level = {
                "low": logging.DEBUG,
                "medium": logging.INFO,
                "high": logging.WARNING,
                "critical": logging.CRITICAL,
            }.get(event.severity.lower(), logging.WARNING)

            self._security_logger.log(
                log_level,
                f"Security Event: {event.event_type.value}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "session_id": event.session_id,
                    "source_ip": event.source_ip,
                    "resource": event.resource,
                    "action": event.action,
                    "result": event.result,
                    "severity": event.severity,
                    "correlation_id": event.correlation_id,
                    **event.details,
                },
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Security event logging failed: %s", str(e), exc_info=True)

    def log_performance_metric(self, metric: PerformanceMetric) -> None:
        """Log a performance metric."""
        if not self.enable_performance_logging:
            return

        try:
            with self._lock:
                self._performance_metrics.append(metric)

                # Maintain metrics history size
                if len(self._performance_metrics) > self.max_performance_metrics:
                    self._performance_metrics = self._performance_metrics[
                        -self.max_performance_metrics :
                    ]

            # Log the performance metric
            self._performance_logger.info(
                f"Performance Metric: {metric.operation}",
                extra={
                    "metric_id": metric.metric_id,
                    "operation": metric.operation,
                    "duration": metric.duration,
                    "memory_usage": metric.memory_usage,
                    "cpu_usage": metric.cpu_usage,
                    "success": metric.success,
                    "error_message": metric.error_message,
                    **metric.metadata,
                },
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Performance metric logging failed: %s", str(e), exc_info=True)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current context."""
        if self.enable_correlation_tracking:
            with self._lock:
                self._correlation_context["correlation_id"] = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        if self.enable_correlation_tracking:
            with self._lock:
                return self._correlation_context.get("correlation_id")
        return None

    def clear_correlation_id(self) -> None:
        """Clear correlation ID for current context."""
        if self.enable_correlation_tracking:
            with self._lock:
                self._correlation_context.pop("correlation_id", None)

    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log message with correlation context."""
        try:
            # Add correlation ID if available
            if self.enable_correlation_tracking:
                correlation_id = self.get_correlation_id()
                if correlation_id:
                    kwargs["correlation_id"] = correlation_id

            # Add timestamp
            kwargs["timestamp"] = datetime.now().isoformat()

            # Log with structured data
            self.logger.log(level, message, extra=kwargs)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Fallback to basic logging if structured logging fails
            self.logger.log(level, f"{message}: {str(e)}")

    def get_security_events(
        self, limit: int = 100, event_type: Optional[SecurityEventType] = None
    ) -> List[SecurityEvent]:
        """Get security events with optional filtering.

        Args:
            limit: Maximum number of events to return
            event_type: Optional event type filter

        Returns:
            List of security events
        """
        with self._lock:
            events = self._security_events.copy()

            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]

            # Return most recent events
            return events[-limit:]

    def get_performance_metrics(
        self, limit: int = 100, operation: Optional[str] = None
    ) -> List[PerformanceMetric]:
        """Get performance metrics with optional filtering.

        Args:
            limit: Maximum number of metrics to return
            operation: Optional operation filter

        Returns:
            List of performance metrics
        """
        with self._lock:
            metrics = self._performance_metrics.copy()

            # Apply filters
            if operation:
                metrics = [m for m in metrics if m.operation == operation]

            # Return most recent metrics
            return metrics[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive logging statistics.

        Returns:
            Dictionary containing logging statistics
        """
        with self._lock:
            now = datetime.now()
            hour_ago = now.timestamp() - 3600

            # Recent security events
            recent_security_events = [
                e for e in self._security_events if e.timestamp.timestamp() > hour_ago
            ]

            # Recent performance metrics
            recent_performance_metrics = [
                m for m in self._performance_metrics if m.timestamp.timestamp() > hour_ago
            ]

            return {
                "security_events": {
                    "total": len(self._security_events),
                    "recent": len(recent_security_events),
                    "by_type": {
                        event_type.value: len(
                            [e for e in recent_security_events if e.event_type == event_type]
                        )
                        for event_type in SecurityEventType
                    },
                    "by_severity": {
                        severity: len(
                            [e for e in recent_security_events if e.severity.lower() == severity]
                        )
                        for severity in ["low", "medium", "high", "critical"]
                    },
                },
                "performance_metrics": {
                    "total": len(self._performance_metrics),
                    "recent": len(recent_performance_metrics),
                    "average_duration": (
                        sum(m.duration for m in recent_performance_metrics)
                        / len(recent_performance_metrics)
                        if recent_performance_metrics
                        else 0
                    ),
                    "success_rate": (
                        len([m for m in recent_performance_metrics if m.success])
                        / len(recent_performance_metrics)
                        if recent_performance_metrics
                        else 0
                    ),
                },
                "error_handling": self.error_handler.get_error_statistics(),
            }

    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files and events.

        Args:
            days_to_keep: Number of days of logs to keep
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)

            with self._lock:
                # Clean up old security events
                self._security_events = [
                    e for e in self._security_events if e.timestamp.timestamp() > cutoff_time
                ]

                # Clean up old performance metrics
                self._performance_metrics = [
                    m for m in self._performance_metrics if m.timestamp.timestamp() > cutoff_time
                ]

            self.logger.info("Cleaned up logs older than %s days", days_to_keep)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Log cleanup failed: %s", str(e), exc_info=True)


# Decorator for automatic performance and error logging
def log_operation(operation_name: str = None, log_level: LogLevel = LogLevel.INFO) -> None:
    """
    Decorator for automatic operation logging with performance and error tracking.

    Args:
        operation_name: Name of the operation for logging
        log_level: Log level for the operation
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            # Get logging service
            logging_service = get_logging_service()

            try:
                # Set correlation ID if available in kwargs
                correlation_id = kwargs.get("correlation_id")
                if correlation_id:
                    logging_service.set_correlation_id(correlation_id)

                # Log operation start
                logging_service.log_info(
                    f"Starting operation: {operation}",
                    operation=operation,
                    function=func.__name__,
                    module=func.__module__,
                )

                # Execute function
                result = func(*args, **kwargs)

                # Calculate duration
                duration = time.time() - start_time

                # Log performance metric
                metric = PerformanceMetric(
                    operation=operation,
                    duration=duration,
                    success=True,
                    metadata={"function": func.__name__, "module": func.__module__},
                )
                logging_service.log_performance_metric(metric)

                # Log success
                logging_service.log_info(
                    f"Operation completed: {operation}",
                    operation=operation,
                    duration=duration,
                    success=True,
                )

                return result

            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as error:
                # Calculate duration
                duration = time.time() - start_time

                # Log performance metric with error
                metric = PerformanceMetric(
                    operation=operation,
                    duration=duration,
                    success=False,
                    error_message=str(error),
                    metadata={"function": func.__name__, "module": func.__module__},
                )
                logging_service.log_performance_metric(metric)

                # Log error
                context = {
                    "operation": operation,
                    "function": func.__name__,
                    "module": func.__module__,
                    "duration": duration,
                }
                logging_service.log_error(error, context)

                # Re-raise the exception
                raise

            finally:
                # Clear correlation ID
                logging_service.clear_correlation_id()

        return wrapper

    return decorator


# Global logging service instance
_global_logging_service: Optional[CentralizedLoggingService] = None


def get_logging_service() -> CentralizedLoggingService:
    """Get the global logging service instance."""
    global _global_logging_service
    if _global_logging_service is None:
        _global_logging_service = CentralizedLoggingService()
    return _global_logging_service


def set_logging_service(service: CentralizedLoggingService) -> None:
    """Set the global logging service instance."""
    global _global_logging_service
    _global_logging_service = service


def initialize_logging(
    config: Optional[Dict[str, Any]] = None,
) -> CentralizedLoggingService:
    """Initialize the centralized logging system.

    Args:
        config: Configuration for logging system

    Returns:
        Initialized logging service
    """
    # Setup basic logging
    setup_logging(config)

    # Create centralized service
    service = CentralizedLoggingService(config)
    set_logging_service(service)

    return service
