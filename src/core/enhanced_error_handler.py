"""
Enhanced Error Handling Service for Candy-Cadence

This module provides a comprehensive error handling system that implements the IErrorHandler
interface and provides consistent error handling patterns across the application.

Key Features:
- Centralized error handling with detailed logging
- User-friendly error messages with recovery suggestions
- Automatic retry mechanisms for transient failures
- Security event logging for sensitive operations
- Error recovery workflows and fallback strategies
- Comprehensive exception hierarchies
- Performance monitoring integration
"""

import logging
import traceback
import uuid
import time
import functools
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import threading
from dataclasses import dataclass, field
from enum import Enum

from .interfaces.service_interfaces import IErrorHandler
from .logging_config import get_logger

# Optional performance monitor import
try:
    from .performance_monitor import get_performance_monitor
except ImportError:
    get_performance_monitor = lambda: None


class ErrorSeverity(Enum):
    """Error severity levels for categorization."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    PARSING_ERROR = "parsing_error"
    DATABASE_ERROR = "database_error"
    FILE_SYSTEM_ERROR = "file_system_error"
    NETWORK_ERROR = "network_error"
    MEMORY_ERROR = "memory_error"
    GPU_ERROR = "gpu_error"
    UI_ERROR = "ui_error"
    CONFIGURATION_ERROR = "configuration_error"
    SECURITY_ERROR = "security_error"
    PERFORMANCE_ERROR = "performance_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    USER_INTERVENTION = "user_intervention"
    SHUTDOWN = "shutdown"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    module_name: str = ""
    function_name: str = ""
    line_number: int = 0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    file_path: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None


@dataclass
class ErrorInfo:
    """Comprehensive error information container."""

    error: Exception
    context: ErrorContext
    severity: ErrorSeverity
    category: ErrorCategory
    recovery_strategy: RecoveryStrategy
    user_message: str
    developer_message: str
    recovery_suggestions: List[str]
    should_retry: bool
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    is_transient: bool = False
    is_recoverable: bool = True


class EnhancedErrorHandler(IErrorHandler):
    """
    Enhanced error handler implementing IErrorHandler interface.

    Provides comprehensive error handling with:
    - Detailed error logging and categorization
    - User-friendly error messages
    - Automatic retry mechanisms
    - Security event logging
    - Error recovery workflows
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the enhanced error handler.

        Args:
            config: Configuration dictionary for error handling settings
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.performance_monitor = get_performance_monitor()

        # Error tracking
        self._error_history: List[ErrorInfo] = []
        self._error_counts: Dict[str, int] = {}
        self._lock = threading.RLock()

        # Recovery callbacks
        self._recovery_callbacks: Dict[str, Callable] = {}

        # Security event logging
        self._security_logger = get_logger("security")

        # Configuration
        self.max_error_history = self.config.get("max_error_history", 1000)
        self.enable_detailed_logging = self.config.get("enable_detailed_logging", True)
        self.enable_security_logging = self.config.get("enable_security_logging", True)
        self.default_retry_count = self.config.get("default_retry_count", 3)
        self.default_retry_delay = self.config.get("default_retry_delay", 1.0)

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle an error with comprehensive processing.

        Args:
            error: Exception to handle
            context: Optional context information

        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            # Create error context
            error_context = self._create_error_context(error, context)

            # Categorize and analyze error
            error_info = self._analyze_error(error, error_context)

            # Log error with appropriate level
            self._log_error(error_info)

            # Store error in history
            self._store_error(error_info)

            # Attempt recovery if appropriate
            recovery_success = self._attempt_recovery(error_info)

            # Update error counts
            self._update_error_counts(error_info)

            return recovery_success

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as handling_error:
            self.logger.error("Error handler failed: %s", str(handling_error), exc_info=True)
            return False

    def log_error(self, error: Exception, level: str = "ERROR") -> None:
        """
        Log an error with enhanced details.

        Args:
            error: Exception to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            error_context = self._create_error_context(error)
            error_info = self._analyze_error(error, error_context)

            # Log with appropriate level
            log_level = getattr(logging, level.upper(), logging.ERROR)

            self.logger.log(
                log_level,
                f"Error: {error_info.user_message}",
                extra={
                    "error_category": error_info.category.value,
                    "error_severity": error_info.severity.value,
                    "error_id": error_info.context.error_id,
                    "developer_message": error_info.developer_message,
                    "recovery_suggestions": error_info.recovery_suggestions,
                    "should_retry": error_info.should_retry,
                    "is_transient": error_info.is_transient,
                    "is_recoverable": error_info.is_recoverable,
                },
                exc_info=True,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as log_error:
            self.logger.error("Failed to log error: %s", str(log_error), exc_info=True)

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if operation should be retried.

        Args:
            error: Exception to evaluate

        Returns:
            True if operation should be retried, False otherwise
        """
        try:
            error_context = self._create_error_context(error)
            error_info = self._analyze_error(error, error_context)

            return (
                error_info.should_retry
                and error_info.retry_count < error_info.max_retries
                and error_info.is_transient
            )

        except Exception:
            return False

    def register_recovery_callback(self, error_type: str, callback: Callable) -> None:
        """
        Register a recovery callback for specific error types.

        Args:
            error_type: Type of error to handle
            callback: Recovery callback function
        """
        with self._lock:
            self._recovery_callbacks[error_type] = callback
            self.logger.debug("Registered recovery callback for %s", error_type)

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics and metrics.

        Returns:
            Dictionary containing error statistics
        """
        with self._lock:
            recent_errors = [
                error
                for error in self._error_history
                if (datetime.now() - error.context.timestamp).seconds < 3600  # Last hour
            ]

            return {
                "total_errors": len(self._error_history),
                "recent_errors": len(recent_errors),
                "error_counts": self._error_counts.copy(),
                "categories": {
                    category.value: len([e for e in recent_errors if e.category == category])
                    for category in ErrorCategory
                },
                "severities": {
                    severity.value: len([e for e in recent_errors if e.severity == severity])
                    for severity in ErrorSeverity
                },
            }

    def clear_error_history(self) -> None:
        """Clear the error history."""
        with self._lock:
            self._error_history.clear()
            self._error_counts.clear()
            self.logger.info("Error history cleared")

    def _create_error_context(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Create error context from exception and optional context."""
        # Get stack trace information
        tb = traceback.extract_tb(error.__traceback__) if error.__traceback__ else []
        frame = tb[-1] if tb else None

        # Extract context information
        module_name = frame.filename if frame else ""
        function_name = frame.name if frame else ""
        line_number = frame.lineno if frame else 0

        # Create context
        error_context = ErrorContext(
            module_name=module_name,
            function_name=function_name,
            line_number=line_number,
            additional_data=context or {},
        )

        # Add correlation ID if available
        if context and "correlation_id" in context:
            error_context.correlation_id = context["correlation_id"]

        return error_context

    def _analyze_error(self, error: Exception, context: ErrorContext) -> ErrorInfo:
        """Analyze error and create comprehensive error information."""
        # Determine error category
        category = self._categorize_error(error)

        # Determine severity
        severity = self._determine_severity(error, category)

        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(error, category)

        # Generate messages
        user_message = self._generate_user_message(error, category)
        developer_message = self._generate_developer_message(error, context)

        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions(error, category)

        # Determine retry properties
        should_retry, is_transient = self._analyze_retry_properties(error, category)

        # Determine if recoverable
        is_recoverable = self._is_recoverable_error(error, category)

        return ErrorInfo(
            error=error,
            context=context,
            severity=severity,
            category=category,
            recovery_strategy=recovery_strategy,
            user_message=user_message,
            developer_message=developer_message,
            recovery_suggestions=recovery_suggestions,
            should_retry=should_retry,
            is_transient=is_transient,
            is_recoverable=is_recoverable,
            max_retries=self.default_retry_count,
            retry_delay=self.default_retry_delay,
        )

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and content."""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Database errors
        if any(
            keyword in error_message
            for keyword in ["database", "sql", "sqlite", "connection", "timeout"]
        ):
            return ErrorCategory.DATABASE_ERROR

        # File system errors
        if any(
            keyword in error_message
            for keyword in ["file", "directory", "path", "permission", "not found"]
        ):
            return ErrorCategory.FILE_SYSTEM_ERROR

        # Parsing errors
        if any(keyword in error_message for keyword in ["parse", "format", "invalid", "malformed"]):
            return ErrorCategory.PARSING_ERROR

        # Memory errors
        if any(keyword in error_message for keyword in ["memory", "out of memory", "allocation"]):
            return ErrorCategory.MEMORY_ERROR

        # GPU errors
        if any(
            keyword in error_message for keyword in ["gpu", "opengl", "vulkan", "cuda", "graphics"]
        ):
            return ErrorCategory.GPU_ERROR

        # Network errors
        if any(
            keyword in error_message
            for keyword in ["network", "connection", "timeout", "unreachable"]
        ):
            return ErrorCategory.NETWORK_ERROR

        # UI errors
        if any(keyword in error_message for keyword in ["ui", "widget", "qt", "gui", "window"]):
            return ErrorCategory.UI_ERROR

        # Configuration errors
        if any(keyword in error_message for keyword in ["config", "setting", "parameter"]):
            return ErrorCategory.CONFIGURATION_ERROR

        # Security errors
        if any(
            keyword in error_message
            for keyword in ["security", "permission", "unauthorized", "forbidden"]
        ):
            return ErrorCategory.SECURITY_ERROR

        # Performance errors
        if any(
            keyword in error_message for keyword in ["performance", "slow", "timeout", "deadlock"]
        ):
            return ErrorCategory.PERFORMANCE_ERROR

        return ErrorCategory.UNKNOWN_ERROR

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on type and category."""
        error_type = type(error).__name__

        # Critical errors
        if category in [ErrorCategory.SECURITY_ERROR, ErrorCategory.MEMORY_ERROR]:
            return ErrorSeverity.CRITICAL

        # High severity errors
        if category in [ErrorCategory.DATABASE_ERROR, ErrorCategory.GPU_ERROR]:
            return ErrorSeverity.HIGH

        # Medium severity errors
        if category in [ErrorCategory.PARSING_ERROR, ErrorCategory.FILE_SYSTEM_ERROR]:
            return ErrorSeverity.MEDIUM

        # Check specific error types
        if error_type in ["SystemExit", "KeyboardInterrupt", "MemoryError"]:
            return ErrorSeverity.CRITICAL
        elif error_type in ["IOError", "OSError", "ValueError", "TypeError"]:
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _determine_recovery_strategy(
        self, error: Exception, category: ErrorCategory
    ) -> RecoveryStrategy:
        """Determine appropriate recovery strategy."""
        if category == ErrorCategory.SECURITY_ERROR:
            return RecoveryStrategy.SHUTDOWN
        elif category == ErrorCategory.MEMORY_ERROR:
            return RecoveryStrategy.GRACEFUL_DEGRADATION
        elif category in [ErrorCategory.DATABASE_ERROR, ErrorCategory.NETWORK_ERROR]:
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.FILE_SYSTEM_ERROR:
            return RecoveryStrategy.FALLBACK
        else:
            return RecoveryStrategy.USER_INTERVENTION

    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message."""
        error_type = type(error).__name__

        # Category-specific messages
        category_messages = {
            ErrorCategory.PARSING_ERROR: "The file format is not supported or the file is corrupted.",
            ErrorCategory.DATABASE_ERROR: "A database operation failed. Your data may be temporarily unavailable.",
            ErrorCategory.FILE_SYSTEM_ERROR: "A file operation failed. Please check file permissions and paths.",
            ErrorCategory.NETWORK_ERROR: "A network connection failed. Please check your internet connection.",
            ErrorCategory.MEMORY_ERROR: "The application ran out of memory. Try closing other applications.",
            ErrorCategory.GPU_ERROR: "A graphics operation failed. Your GPU may not support this feature.",
            ErrorCategory.UI_ERROR: "A user interface error occurred. The application will continue to function.",
            ErrorCategory.CONFIGURATION_ERROR: "A configuration error occurred. Some features may not work correctly.",
            ErrorCategory.SECURITY_ERROR: "A security error occurred. The application will shut down for safety.",
            ErrorCategory.PERFORMANCE_ERROR: "A performance issue was detected. The operation may take longer than expected.",
        }

        if category in category_messages:
            return category_messages[category]

        # Generic error messages
        generic_messages = {
            "FileNotFoundError": "The requested file could not be found.",
            "PermissionError": "You don't have permission to perform this operation.",
            "ConnectionError": "Unable to establish a connection.",
            "TimeoutError": "The operation timed out.",
            "ValueError": "An invalid value was provided.",
            "TypeError": "An incorrect data type was used.",
        }

        if error_type in generic_messages:
            return generic_messages[error_type]

        return f"An error occurred: {str(error)}"

    def _generate_developer_message(self, error: Exception, context: ErrorContext) -> str:
        """Generate detailed developer message."""
        return (
            f"Error in {context.module_name}.{context.function_name} "
            f"at line {context.line_number}: {type(error).__name__}: {str(error)}"
        )

    def _generate_recovery_suggestions(
        self, error: Exception, category: ErrorCategory
    ) -> List[str]:
        """Generate recovery suggestions for the error."""
        suggestions = []

        # Category-specific suggestions
        category_suggestions = {
            ErrorCategory.PARSING_ERROR: [
                "Check if the file format is supported",
                "Verify the file is not corrupted",
                "Try converting the file to a supported format",
            ],
            ErrorCategory.DATABASE_ERROR: [
                "Check database connection",
                "Verify database file permissions",
                "Restart the application",
                "Check available disk space",
            ],
            ErrorCategory.FILE_SYSTEM_ERROR: [
                "Check file path and permissions",
                "Verify the file exists",
                "Try running as administrator",
                "Check available disk space",
            ],
            ErrorCategory.NETWORK_ERROR: [
                "Check internet connection",
                "Try again later",
                "Check firewall settings",
                "Verify network configuration",
            ],
            ErrorCategory.MEMORY_ERROR: [
                "Close other applications",
                "Restart the application",
                "Use smaller files",
                "Check available RAM",
            ],
            ErrorCategory.GPU_ERROR: [
                "Update graphics drivers",
                "Try software rendering mode",
                "Check GPU compatibility",
                "Restart the application",
            ],
            ErrorCategory.UI_ERROR: [
                "Restart the application",
                "Try different theme",
                "Check display settings",
                "Update graphics drivers",
            ],
            ErrorCategory.CONFIGURATION_ERROR: [
                "Reset to default settings",
                "Check configuration file",
                "Reinstall the application",
                "Contact support",
            ],
            ErrorCategory.SECURITY_ERROR: [
                "Run as administrator",
                "Check antivirus software",
                "Verify file permissions",
                "Contact system administrator",
            ],
            ErrorCategory.PERFORMANCE_ERROR: [
                "Close other applications",
                "Use smaller files",
                "Wait for operation to complete",
                "Restart the application",
            ],
        }

        if category in category_suggestions:
            suggestions.extend(category_suggestions[category])

        # Always add general suggestions
        suggestions.extend(
            [
                "Restart the application",
                "Check the application logs for more details",
                "Contact support if the problem persists",
            ]
        )

        return suggestions

    def _analyze_retry_properties(
        self, error: Exception, category: ErrorCategory
    ) -> tuple[bool, bool]:
        """Analyze if error should be retried and if it's transient."""
        # Transient errors that can be retried
        transient_errors = [
            "ConnectionError",
            "TimeoutError",
            "TemporaryFileNotFoundError",
            "DatabaseError",
            "NetworkError",
        ]

        error_type = type(error).__name__
        is_transient = error_type in transient_errors or category in [
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.DATABASE_ERROR,
        ]

        # Retryable categories
        retryable_categories = [
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.DATABASE_ERROR,
            ErrorCategory.FILE_SYSTEM_ERROR,
        ]

        should_retry = is_transient and category in retryable_categories

        return should_retry, is_transient

    def _is_recoverable_error(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if the error is recoverable."""
        # Non-recoverable errors
        non_recoverable = [ErrorCategory.SECURITY_ERROR, ErrorSeverity.CRITICAL]

        return category not in non_recoverable

    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error with appropriate level and details."""
        # Determine log level based on severity
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(error_info.severity, logging.ERROR)

        # Log the error
        self.logger.log(
            log_level,
            f"{error_info.category.value}: {error_info.user_message}",
            extra={
                "error_id": error_info.context.error_id,
                "error_category": error_info.category.value,
                "error_severity": error_info.severity.value,
                "recovery_strategy": error_info.recovery_strategy.value,
                "user_message": error_info.user_message,
                "developer_message": error_info.developer_message,
                "recovery_suggestions": error_info.recovery_suggestions,
                "should_retry": error_info.should_retry,
                "is_transient": error_info.is_transient,
                "is_recoverable": error_info.is_recoverable,
                "module": error_info.context.module_name,
                "function": error_info.context.function_name,
                "line": error_info.context.line_number,
                "correlation_id": error_info.context.correlation_id,
            },
            exc_info=True,
        )

        # Log security events separately
        if self.enable_security_logging and error_info.category == ErrorCategory.SECURITY_ERROR:
            self._security_logger.critical(
                f"SECURITY EVENT: {error_info.user_message}",
                extra={
                    "event_type": "security_error",
                    "error_id": error_info.context.error_id,
                    "severity": error_info.severity.value,
                    "module": error_info.context.module_name,
                    "function": error_info.context.function_name,
                    "user_id": error_info.context.user_id,
                    "session_id": error_info.context.session_id,
                },
            )

    def _store_error(self, error_info: ErrorInfo) -> None:
        """Store error in history with size management."""
        with self._lock:
            self._error_history.append(error_info)

            # Maintain history size limit
            if len(self._error_history) > self.max_error_history:
                self._error_history = self._error_history[-self.max_error_history :]

    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from the error."""
        try:
            # Check if recovery is possible
            if not error_info.is_recoverable:
                return False

            # Try registered recovery callbacks
            error_type = type(error_info.error).__name__
            if error_type in self._recovery_callbacks:
                callback = self._recovery_callbacks[error_type]
                return callback(error_info.error, error_info.context)

            # Handle specific recovery strategies
            if error_info.recovery_strategy == RecoveryStrategy.RETRY:
                return self._handle_retry_strategy(error_info)
            elif error_info.recovery_strategy == RecoveryStrategy.FALLBACK:
                return self._handle_fallback_strategy(error_info)
            elif error_info.recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return self._handle_graceful_degradation(error_info)

            return False

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as recovery_error:
            self.logger.error("Recovery attempt failed: %s", str(recovery_error), exc_info=True)
            return False

    def _handle_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """Handle retry-based recovery strategy."""
        if error_info.retry_count >= error_info.max_retries:
            return False

        # Increment retry count
        error_info.retry_count += 1

        # Log retry attempt
        self.logger.info(
            f"Retrying operation (attempt {error_info.retry_count}/{error_info.max_retries})",
            extra={
                "error_id": error_info.context.error_id,
                "retry_count": error_info.retry_count,
                "max_retries": error_info.max_retries,
            },
        )

        # Wait before retry
        time.sleep(error_info.retry_delay * error_info.retry_count)

        return True

    def _handle_fallback_strategy(self, error_info: ErrorInfo) -> bool:
        """Handle fallback-based recovery strategy."""
        self.logger.info(
            f"Attempting fallback recovery for {error_info.category.value}",
            extra={
                "error_id": error_info.context.error_id,
                "category": error_info.category.value,
            },
        )

        # Implement fallback logic based on category
        if error_info.category == ErrorCategory.FILE_SYSTEM_ERROR:
            # Try alternative file paths or locations
            return self._try_alternative_file_locations(error_info)

        return False

    def _handle_graceful_degradation(self, error_info: ErrorInfo) -> bool:
        """Handle graceful degradation strategy."""
        self.logger.info(
            f"Applying graceful degradation for {error_info.category.value}",
            extra={
                "error_id": error_info.context.error_id,
                "category": error_info.category.value,
            },
        )

        # Implement degradation logic
        if error_info.category == ErrorCategory.MEMORY_ERROR:
            # Reduce memory usage
            return self._reduce_memory_usage()

        return True

    def _try_alternative_file_locations(self, error_info: ErrorInfo) -> bool:
        """Try alternative file locations for file system errors."""
        # This would be implemented based on specific use cases
        return False

    def _reduce_memory_usage(self) -> bool:
        """Reduce memory usage for memory errors."""
        try:
            import gc

            gc.collect()
            return True
        except Exception:
            return False

    def _update_error_counts(self, error_info: ErrorInfo) -> None:
        """Update error count statistics."""
        with self._lock:
            error_key = f"{error_info.category.value}_{type(error_info.error).__name__}"
            self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1


# Decorator for automatic error handling
def handle_errors(operation_name: str = None, reraise: bool = True) -> None:
    """
    Decorator for automatic error handling.

    Args:
        operation_name: Name of the operation for logging
        reraise: Whether to re-raise the exception after handling
    """

    def decorator(func: Callable) -> Callable:
        """TODO: Add docstring."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            """TODO: Add docstring."""
            error_handler = EnhancedErrorHandler()
            operation = operation_name or f"{func.__module__}.{func.__name__}"

            try:
                return func(*args, **kwargs)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as error:
                context = {
                    "operation": operation,
                    "function": func.__name__,
                    "module": func.__module__,
                }

                handled = error_handler.handle_error(error, context)

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


# Global error handler instance
_global_error_handler: Optional[EnhancedErrorHandler] = None


def get_error_handler() -> EnhancedErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = EnhancedErrorHandler()
    return _global_error_handler


def set_error_handler(handler: EnhancedErrorHandler) -> None:
    """Set the global error handler instance."""
    global _global_error_handler
    _global_error_handler = handler
