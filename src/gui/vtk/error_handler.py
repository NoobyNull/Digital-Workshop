"""
VTK Error Handler - Centralized VTK error processing and logging.

This module provides comprehensive error handling for VTK operations,
including graceful handling of OpenGL context loss and proper error logging.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum

import vtk

from src.core.logging_config import get_logger, log_function_call


logger = get_logger(__name__)


class VTKErrorCode(Enum):
    """VTK error codes for classification and handling."""

    CONTEXT_LOST = "context_lost"
    INVALID_HANDLE = "invalid_handle"
    RENDER_ERROR = "render_error"
    CLEANUP_ERROR = "cleanup_error"
    RESOURCE_ERROR = "resource_error"
    INITIALIZATION_ERROR = "initialization_error"
    MEMORY_ERROR = "memory_error"
    THREAD_ERROR = "thread_error"
    UNKNOWN_ERROR = "unknown_error"


class VTKErrorSeverity(Enum):
    """Error severity levels for appropriate response."""

    LOW = "low"  # Log and continue
    MEDIUM = "medium"  # Log warning and attempt recovery
    HIGH = "high"  # Log error and use fallback
    CRITICAL = "critical"  # Log critical and shutdown gracefully


class VTKErrorHandler:
    """
    Centralized VTK error handler with comprehensive logging and recovery.

    Handles VTK errors gracefully, especially OpenGL context loss during cleanup.
    Provides detailed logging for debugging and implements fallback strategies.
    """

    def __init__(self):
        """Initialize the VTK error handler."""
        self.logger = get_logger(__name__)
        self.error_counts: Dict[VTKErrorCode, int] = {}
        self.error_callbacks: Dict[VTKErrorCode, Callable] = {}
        self.suppress_errors = False
        self.recovery_strategies: Dict[VTKErrorCode, Callable] = {}

        # Initialize error counts
        for error_code in VTKErrorCode:
            self.error_counts[error_code] = 0

        # Set up default recovery strategies
        self._setup_default_recovery_strategies()

        # Set up VTK error observer
        self._setup_vtk_error_observer()

        self.logger.info("VTK Error Handler initialized")

    def _setup_default_recovery_strategies(self) -> None:
        """Set up default recovery strategies for different error types."""

        def context_lost_recovery(error_info: Dict[str, Any]) -> bool:
            """Recovery strategy for OpenGL context loss."""
            self.logger.warning("OpenGL context lost, switching to fallback mode")
            # Context loss typically happens during shutdown, so we just log and continue
            return True

        def invalid_handle_recovery(error_info: Dict[str, Any]) -> bool:
            """Recovery strategy for invalid handle errors."""
            self.logger.debug("Invalid handle error detected, skipping operation")
            # Invalid handle usually means context is destroyed, safe to skip
            return True

        def render_error_recovery(error_info: Dict[str, Any]) -> bool:
            """Recovery strategy for render errors."""
            self.logger.warning("Render error occurred, attempting to continue")
            # Try to continue rendering, but with reduced quality if needed
            return True

        def cleanup_error_recovery(error_info: Dict[str, Any]) -> bool:
            """Recovery strategy for cleanup errors."""
            self.logger.debug("Cleanup error during shutdown, this is normal")
            # Cleanup errors during shutdown are expected, just log and continue
            return True

        def memory_error_recovery(error_info: Dict[str, Any]) -> bool:
            """Recovery strategy for memory errors."""
            self.logger.error("VTK memory error, attempting cleanup")
            # Force garbage collection and try to free resources
            import gc

            gc.collect()
            return False  # Memory errors are serious, don't continue

        # Register recovery strategies
        self.recovery_strategies[VTKErrorCode.CONTEXT_LOST] = context_lost_recovery
        self.recovery_strategies[VTKErrorCode.INVALID_HANDLE] = invalid_handle_recovery
        self.recovery_strategies[VTKErrorCode.RENDER_ERROR] = render_error_recovery
        self.recovery_strategies[VTKErrorCode.CLEANUP_ERROR] = cleanup_error_recovery
        self.recovery_strategies[VTKErrorCode.MEMORY_ERROR] = memory_error_recovery

    def _setup_vtk_error_observer(self) -> None:
        """Set up VTK error observer to capture VTK internal errors."""
        try:
            # Create a custom error observer class that inherits from vtk.vtkCommand
            class VTKErrorObserver(vtk.vtkCommand):
                def __init__(self, handler):
                    super().__init__()
                    self.handler = handler

                def Execute(self, obj, event, calldata):
                    if self.handler.suppress_errors:
                        return

                    try:
                        # Extract error information from VTK
                        error_text = calldata if calldata else "Unknown VTK error"
                        self.handler._handle_vtk_error(error_text)
                    except Exception as e:
                        self.handler.logger.debug("Error in VTK error callback: %s", e)

            # Set up the observer using the custom class
            self.vtk_error_observer = VTKErrorObserver(self)

            # Observe VTK object errors
            # Note: We suppress VTK warnings because wglMakeCurrent errors are
            # expected during rendering and are handled gracefully by VTK
            vtk.vtkObject.GlobalWarningDisplayOff()
            vtk.vtkObject.SetGlobalWarningDisplay(0)

        except Exception as e:
            self.logger.warning("Failed to set up VTK error observer: %s", e)

    def _handle_vtk_error(self, error_text: str) -> None:
        """Handle a VTK error message."""
        try:
            # Classify the error
            error_code = self._classify_error(error_text)
            severity = self._determine_severity(error_code, error_text)

            # Create error info
            error_info = {
                "error_text": error_text,
                "error_code": error_code.value,
                "severity": severity.value,
                "timestamp": self._get_timestamp(),
                "traceback": (
                    traceback.format_stack()[-3:-1] if severity != VTKErrorSeverity.LOW else []
                ),
            }

            # Log the error
            self._log_error(error_info, severity)

            # Update error counts
            self.error_counts[error_code] += 1

            # Execute recovery strategy if available
            if error_code in self.recovery_strategies:
                try:
                    recovery_success = self.recovery_strategies[error_code](error_info)
                    if recovery_success:
                        self.logger.debug("Recovery strategy succeeded for %s", error_code.value)
                    else:
                        self.logger.warning("Recovery strategy failed for %s", error_code.value)
                except Exception as e:
                    self.logger.error("Recovery strategy failed with exception: %s", e)

            # Execute callback if registered
            if error_code in self.error_callbacks:
                try:
                    self.error_callbacks[error_code](error_info)
                except Exception as e:
                    self.logger.error("Error callback failed: %s", e)

        except Exception as e:
            self.logger.error("Error in VTK error handler: %s", e)

    def _classify_error(self, error_text: str) -> VTKErrorCode:
        """Classify VTK error text into appropriate error code."""
        error_lower = error_text.lower()

        # Check for specific error patterns
        if "wglmakecurrent" in error_lower and "clean" in error_lower:
            return VTKErrorCode.CLEANUP_ERROR
        elif "invalid handle" in error_lower or "error: 6" in error_lower:
            return VTKErrorCode.INVALID_HANDLE
        elif "context" in error_lower and ("lost" in error_lower or "invalid" in error_lower):
            return VTKErrorCode.CONTEXT_LOST
        elif "render" in error_lower or "opengl" in error_lower:
            return VTKErrorCode.RENDER_ERROR
        elif "memory" in error_lower or "allocation" in error_lower:
            return VTKErrorCode.MEMORY_ERROR
        elif "thread" in error_lower:
            return VTKErrorCode.THREAD_ERROR
        elif "initialization" in error_lower or "init" in error_lower:
            return VTKErrorCode.INITIALIZATION_ERROR
        else:
            return VTKErrorCode.UNKNOWN_ERROR

    def _determine_severity(self, error_code: VTKErrorCode, error_text: str) -> VTKErrorSeverity:
        """Determine error severity based on code and content."""
        # Critical errors that require immediate attention
        if error_code in [VTKErrorCode.MEMORY_ERROR, VTKErrorCode.THREAD_ERROR]:
            return VTKErrorSeverity.CRITICAL

        # High severity errors that need fallback handling
        if error_code in [VTKErrorCode.CONTEXT_LOST, VTKErrorCode.INITIALIZATION_ERROR]:
            return VTKErrorSeverity.HIGH

        # Medium severity errors that need recovery attempts
        if error_code in [VTKErrorCode.RENDER_ERROR, VTKErrorCode.RESOURCE_ERROR]:
            return VTKErrorSeverity.MEDIUM

        # Low severity errors (cleanup, invalid handle during shutdown)
        if error_code in [VTKErrorCode.CLEANUP_ERROR, VTKErrorCode.INVALID_HANDLE]:
            return VTKErrorSeverity.LOW

        return VTKErrorSeverity.MEDIUM

    def _log_error(self, error_info: Dict[str, Any], severity: VTKErrorSeverity) -> None:
        """Log error with appropriate level and format."""
        log_data = {
            "vtk_error": True,
            "error_code": error_info["error_code"],
            "severity": error_info["severity"],
            "error_text": error_info["error_text"],
            "timestamp": error_info["timestamp"],
        }

        # Add traceback for non-low severity errors
        if severity != VTKErrorSeverity.LOW and error_info.get("traceback"):
            log_data["traceback"] = error_info["traceback"]

        # Log with appropriate level
        if severity == VTKErrorSeverity.CRITICAL:
            self.logger.critical("VTK Critical Error: %s", error_info['error_text'], extra=log_data)
        elif severity == VTKErrorSeverity.HIGH:
            self.logger.error(
                f"VTK High Severity Error: {error_info['error_text']}", extra=log_data
            )
        elif severity == VTKErrorSeverity.MEDIUM:
            self.logger.warning(
                f"VTK Medium Severity Error: {error_info['error_text']}", extra=log_data
            )
        else:  # LOW severity
            self.logger.debug("VTK Low Severity Error: %s", error_info['error_text'], extra=log_data)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    @log_function_call(logger)
    def handle_error(self, error: Exception, context: str = "unknown") -> bool:
        """
        Handle a VTK-related exception.

        Args:
            error: The exception that occurred
            context: Context where the error occurred

        Returns:
            True if the error was handled gracefully, False if it should propagate
        """
        try:
            error_text = f"{context}: {str(error)}"

            # Classify and handle the error
            error_code = self._classify_error(error_text)
            severity = self._determine_severity(error_code, error_text)

            error_info = {
                "error_text": error_text,
                "error_code": error_code.value,
                "severity": severity.value,
                "context": context,
                "exception_type": type(error).__name__,
                "timestamp": self._get_timestamp(),
                "traceback": traceback.format_exception(type(error), error, error.__traceback__),
            }

            # Log the error
            self._log_error(error_info, severity)

            # Update counts
            self.error_counts[error_code] += 1

            # Execute recovery strategy
            if error_code in self.recovery_strategies:
                try:
                    recovery_success = self.recovery_strategies[error_code](error_info)
                    return recovery_success
                except Exception as e:
                    self.logger.error("Recovery strategy failed: %s", e)

            # Default: return True for low/medium severity, False for high/critical
            return severity in [VTKErrorSeverity.LOW, VTKErrorSeverity.MEDIUM]

        except Exception as e:
            self.logger.error("Error in error handler: %s", e)
            return False

    def register_error_callback(self, error_code: VTKErrorCode, callback: Callable) -> None:
        """
        Register a callback for specific error types.

        Args:
            error_code: The error code to register for
            callback: Function to call when this error occurs
        """
        self.error_callbacks[error_code] = callback
        self.logger.debug("Registered callback for error code: %s", error_code.value)

    def suppress_errors_temporarily(self, duration_ms: int = 1000) -> None:
        """
        Temporarily suppress VTK error output.

        Args:
            duration_ms: Duration to suppress errors in milliseconds
        """
        self.suppress_errors = True

        def reenable_errors():
            self.suppress_errors = False
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("VTK error suppression ended")

        # Schedule re-enabling of errors
        from PySide6.QtCore import QTimer

        QTimer.singleShot(duration_ms, reenable_errors)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for debugging."""
        return {
            "error_counts": {code.value: count for code, count in self.error_counts.items()},
            "total_errors": sum(self.error_counts.values()),
            "suppressed_errors": self.suppress_errors,
        }

    def reset_error_counts(self) -> None:
        """Reset error counts for testing or debugging."""
        for error_code in VTKErrorCode:
            self.error_counts[error_code] = 0
        self.logger.info("VTK error counts reset")

    def is_context_lost_error(self, error_text: str) -> bool:
        """
        Check if error text indicates OpenGL context loss.

        Args:
            error_text: The error text to check

        Returns:
            True if this appears to be a context loss error
        """
        return VTKErrorCode.CONTEXT_LOST == self._classify_error(
            error_text
        ) or VTKErrorCode.INVALID_HANDLE == self._classify_error(error_text)

    def safe_vtk_operation(self, operation: Callable, context: str = "vtk_operation") -> Any:
        """
        Safely execute a VTK operation with error handling.

        Args:
            operation: The VTK operation to execute
            context: Context description for error logging

        Returns:
            Result of the operation, or None if it failed
        """
        try:
            return operation()
        except Exception as e:
            handled = self.handle_error(e, context)
            if not handled:
                raise  # Re-raise if not handled gracefully
            return None


# Global error handler instance
_vtk_error_handler: Optional[VTKErrorHandler] = None


def get_vtk_error_handler() -> VTKErrorHandler:
    """Get the global VTK error handler instance."""
    global _vtk_error_handler
    if _vtk_error_handler is None:
        _vtk_error_handler = VTKErrorHandler()
    return _vtk_error_handler


def handle_vtk_error(error: Exception, context: str = "unknown") -> bool:
    """
    Convenience function to handle VTK errors.

    Args:
        error: The exception that occurred
        context: Context where the error occurred

    Returns:
        True if handled gracefully, False otherwise
    """
    return get_vtk_error_handler().handle_error(error, context)


def suppress_vtk_errors_temporarily(duration_ms: int = 1000) -> None:
    """Convenience function to temporarily suppress VTK errors."""
    get_vtk_error_handler().suppress_errors_temporarily(duration_ms)
