"""
Specific Error Handling Decorators and Context Managers

This module provides targeted error handling mechanisms to replace overly broad
exception handling patterns throughout the application.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, Union
from contextlib import contextmanager
from pathlib import Path

from .error_categories import (
    ErrorContext,
    ErrorRecoveryStrategy,
    ErrorReport,
)
from .error_reporter import get_global_error_reporter


class SpecificErrorHandler:
    """
    Context manager and decorator for specific error handling.
    Replaces broad `except Exception` patterns with targeted handling.
    """

    def __init__(
        self,
        context: ErrorContext,
        expected_errors: Optional[Union[Type[Exception], tuple]] = None,
        recovery_strategy: Optional[ErrorRecoveryStrategy] = None,
        context_info: Optional[Dict[str, Any]] = None,
        reraise: bool = True,
    ):
        """
        Initialize specific error handler.

        Args:
            context: The context in which errors are handled
            expected_errors: Specific exception types to catch (None for all)
            recovery_strategy: How to handle caught errors
            context_info: Additional context information
            reraise: Whether to reraise handled errors
        """
        self.context = context
        self.expected_errors = expected_errors or Exception
        self.recovery_strategy = recovery_strategy
        self.context_info = context_info or {}
        self.reraise = reraise
        self.logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self) -> None:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager with specific error handling."""
        if exc_type is None:
            return False  # No exception occurred

        # Check if this is an expected error type
        if not issubclass(exc_type, self.expected_errors):
            return False  # Not an expected error, let it propagate

        # Handle the specific error
        return self._handle_error(exc_type, exc_val, exc_tb)

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            try:
                return func(*args, **kwargs)
            except self.expected_errors as e:
                return self._handle_error(type(e), e, None)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                # Re-raise unexpected exceptions
                raise

        return wrapper

    def _handle_error(self, exc_type: Type[Exception], exc_val: Exception, exc_tb) -> bool:
        """
        Handle the specific error with proper categorization and reporting.

        Returns:
            True if error was handled successfully, False if it should propagate
        """
        try:
            # Create comprehensive error report
            error_report = get_global_error_reporter().report_error(
                error=exc_val,
                context=self.context,
                context_info=self.context_info,
                recovery_callback=lambda: self._attempt_recovery(exc_val),
            )

            # Log the handling
            self.logger.info(
                "Specific error handled: %s in context %s",
                exc_type.__name__,
                self.context.value,
            )

            # Determine if we should reraise
            if self.reraise:
                # Re-raise with original traceback
                raise exc_val.with_traceback(exc_tb)

            return True

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as reporting_error:
            # If error reporting itself fails, log and continue
            self.logger.error("Error reporting failed: %s", reporting_error, exc_info=True)

            # In case of reporting failure, still attempt recovery
            try:
                self._attempt_recovery(exc_val)
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as recovery_error:
                self.logger.error("Recovery attempt failed: %s", recovery_error, exc_info=True)

            # Reraise original error if requested
            if self.reraise:
                raise exc_val.with_traceback(exc_tb)

            return False

    def _attempt_recovery(self, error: Exception) -> bool:
        """Attempt to recover from the error."""
        if not self.recovery_strategy:
            return False

        try:
            # Get recovery handler from global reporter
            reporter = get_global_error_reporter()
            recovery_handler = reporter.recovery_strategies.get(self.recovery_strategy)

            if recovery_handler:
                # Create a minimal error report for recovery
                error_report = ErrorReport.create_error_report(
                    error=error, context=self.context, context_info=self.context_info
                )

                # Attempt recovery
                return recovery_handler(error_report, lambda: None)

            return False

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as recovery_error:
            self.logger.error("Recovery strategy failed: %s", recovery_error, exc_info=True)
            return False


# Predefined handlers for common scenarios
class ShutdownErrorHandler(SpecificErrorHandler):
    """Specialized handler for shutdown operations."""

    def __init__(self, operation_name: str, context_info: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            context=ErrorContext.SHUTDOWN,
            expected_errors=(RuntimeError, OSError, IOError),
            recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN,
            context_info={"operation": operation_name, **(context_info or {})},
            reraise=False,  # Don't reraise during shutdown
        )


class VTKErrorHandler(SpecificErrorHandler):
    """Specialized handler for VTK operations."""

    def __init__(self, operation: str, context_info: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            context=ErrorContext.RENDERING,
            expected_errors=(RuntimeError, OSError),
            recovery_strategy=ErrorRecoveryStrategy.IGNORE_AND_CONTINUE,
            context_info={
                "vtk_operation": operation,
                "component": "vtk",
                **(context_info or {}),
            },
            reraise=False,  # VTK errors during shutdown are often expected
        )


class FileIOErrorHandler(SpecificErrorHandler):
    """Specialized handler for file I/O operations."""

    def __init__(
        self,
        operation: str,
        file_path: Optional[Path] = None,
        context_info: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            context=(
                ErrorContext.FILE_LOADING
                if "load" in operation.lower()
                else ErrorContext.FILE_SAVING
            ),
            expected_errors=(FileNotFoundError, PermissionError, OSError, IOError),
            recovery_strategy=ErrorRecoveryStrategy.USER_INTERVENTION,
            context_info={
                "file_operation": operation,
                "file_path": str(file_path) if file_path else None,
                **(context_info or {}),
            },
            reraise=True,  # File errors should be handled by caller
        )


class MemoryErrorHandler(SpecificErrorHandler):
    """Specialized handler for memory-related errors."""

    def __init__(self, operation: str, context_info: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            context=ErrorContext.NORMAL_OPERATION,
            expected_errors=(MemoryError,),
            recovery_strategy=ErrorRecoveryStrategy.IMMEDIATE_SHUTDOWN,
            context_info={
                "memory_operation": operation,
                "component": "memory_management",
                **(context_info or {}),
            },
            reraise=False,  # Memory errors require immediate attention
        )


# Context managers for specific operations
@contextmanager
def handle_shutdown_errors(
    operation_name: str, context_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Context manager for shutdown operations with specific error handling.

    Usage:
        with handle_shutdown_errors("vtk_cleanup"):
            # VTK cleanup code here
            pass
    """
    handler = ShutdownErrorHandler(operation_name, context_info)
    with handler:
        yield


@contextmanager
def handle_vtk_errors(operation: str, context_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Context manager for VTK operations with specific error handling.

    Usage:
        with handle_vtk_errors("render_cleanup"):
            # VTK cleanup code here
            pass
    """
    handler = VTKErrorHandler(operation, context_info)
    with handler:
        yield


@contextmanager
def handle_file_io_errors(
    operation: str,
    file_path: Optional[Path] = None,
    context_info: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for file I/O operations with specific error handling.

    Usage:
        with handle_file_io_errors("load_model", Path("model.stl")):
            # File loading code here
            pass
    """
    handler = FileIOErrorHandler(operation, file_path, context_info)
    with handler:
        yield


@contextmanager
def handle_memory_errors(operation: str, context_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Context manager for memory operations with specific error handling.

    Usage:
        with handle_memory_errors("allocate_buffers"):
            # Memory allocation code here
            pass
    """
    handler = MemoryErrorHandler(operation, context_info)
    with handler:
        yield


# Decorators for function-level error handling
def specific_error_handler(
    context: ErrorContext,
    expected_errors: Optional[Union[Type[Exception], tuple]] = None,
    recovery_strategy: Optional[ErrorRecoveryStrategy] = None,
    context_info: Optional[Dict[str, Any]] = None,
    reraise: bool = True,
):
    """
    Decorator for specific error handling on functions.

    Usage:
        @specific_error_handler(
            context=ErrorContext.SHUTDOWN,
            expected_errors=(RuntimeError, OSError),
            recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN
        )
        def cleanup_vtk_resources() -> None:
            # Cleanup code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        handler = SpecificErrorHandler(
            context=context,
            expected_errors=expected_errors,
            recovery_strategy=recovery_strategy,
            context_info=context_info,
            reraise=reraise,
        )
        return handler(func)

    return decorator


def shutdown_safe(func: Callable) -> Callable:
    """
    Decorator for shutdown-safe functions.

    Usage:
        @shutdown_safe
        def cleanup_vtk() -> None:
            # VTK cleanup code
            pass
    """
    return specific_error_handler(
        context=ErrorContext.SHUTDOWN,
        expected_errors=(RuntimeError, OSError, IOError),
        recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN,
        context_info={"function": func.__name__},
        reraise=False,
    )(func)


def vtk_safe(func: Callable) -> Callable:
    """
    Decorator for VTK-safe functions.

    Usage:
        @vtk_safe
        def render_scene() -> None:
            # VTK rendering code
            pass
    """
    return specific_error_handler(
        context=ErrorContext.RENDERING,
        expected_errors=(RuntimeError, OSError),
        recovery_strategy=ErrorRecoveryStrategy.IGNORE_AND_CONTINUE,
        context_info={"function": func.__name__, "component": "vtk"},
        reraise=False,
    )(func)


def file_io_safe(operation: str, file_path: Optional[Path] = None) -> None:
    """
    Decorator for file I/O safe functions.

    Usage:
        @file_io_safe("load_model", Path("model.stl"))
        def load_model_file() -> None:
            # File loading code
            pass
    """

    def decorator(func: Callable) -> Callable:
        return specific_error_handler(
            context=(
                ErrorContext.FILE_LOADING
                if "load" in operation.lower()
                else ErrorContext.FILE_SAVING
            ),
            expected_errors=(FileNotFoundError, PermissionError, OSError, IOError),
            recovery_strategy=ErrorRecoveryStrategy.USER_INTERVENTION,
            context_info={
                "function": func.__name__,
                "file_operation": operation,
                "file_path": str(file_path) if file_path else None,
            },
            reraise=True,
        )(func)

    return decorator


# Performance monitoring wrapper
def monitor_operation(
    operation_name: str, context: ErrorContext = ErrorContext.NORMAL_OPERATION
) -> None:
    """
    Decorator to monitor operation performance and handle errors.

    Usage:
        @monitor_operation("model_loading", ErrorContext.FILE_LOADING)
        def load_model() -> None:
            # Model loading code
            pass
    """

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            start_time = time.time()
            operation_id = f"{func.__name__}_{int(start_time * 1000)}"

            try:
                # Log operation start
                logging.getLogger("operation_monitor").info(
                    "Operation started: %s (%s)", operation_name, operation_id
                )

                # Execute operation with specific error handling
                with SpecificErrorHandler(
                    context=context,
                    context_info={
                        "operation_name": operation_name,
                        "operation_id": operation_id,
                        "function": func.__name__,
                    },
                ):
                    result = func(*args, **kwargs)

                # Log successful completion
                duration = time.time() - start_time
                logging.getLogger("operation_monitor").info(
                    "Operation completed: %s (%s) - Duration: %.3fs",
                    operation_name,
                    operation_id,
                    duration,
                )

                return result

            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                # Log failure with timing
                duration = time.time() - start_time
                logging.getLogger("operation_monitor").error(
                    "Operation failed: %s (%s) - Duration: %.3fs - Error: %s",
                    operation_name,
                    operation_id,
                    duration,
                    str(e),
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
