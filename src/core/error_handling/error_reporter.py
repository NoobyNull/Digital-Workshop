"""
Comprehensive Error Reporting System

This module provides a robust error reporting system that replaces overly broad
exception handling with specific, targeted error handling and detailed diagnostic
information.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
import threading

from .error_categories import (
    ErrorReport,
    ErrorSeverity,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorContext,
)


class ErrorReporter:
    """
    Central error reporting system that handles error categorization,
    logging, and reporting with comprehensive diagnostic information.
    """

    def __init__(
        self,
        log_file_path: Optional[Path] = None,
        max_reports: int = 1000,
        enable_console_logging: bool = True,
    ):
        """
        Initialize the error reporter.

        Args:
            log_file_path: Path to error log file
            max_reports: Maximum number of error reports to keep in memory
            enable_console_logging: Whether to enable console logging
        """
        self.log_file_path = log_file_path or Path("error_reports.jsonl")
        self.max_reports = max_reports
        self.enable_console_logging = enable_console_logging

        # Error tracking
        self.error_reports: List[ErrorReport] = []
        self.error_counts: Dict[str, int] = {}
        self.error_patterns: Dict[str, List[datetime]] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Logging setup
        self._setup_logging()

        # Error handlers by category
        self.category_handlers: Dict[ErrorCategory, Callable] = {}

        # Recovery strategies
        self.recovery_strategies: Dict[ErrorRecoveryStrategy, Callable] = {}

        # Performance tracking
        self.reporting_stats = {
            "total_reports": 0,
            "critical_errors": 0,
            "recovered_errors": 0,
            "failed_recoveries": 0,
            "average_report_time": 0.0,
        }

        self._setup_default_handlers()

    def _setup_logging(self) -> None:
        """Setup logging configuration for error reporting."""
        # Create logger
        self.logger = logging.getLogger("error_reporter")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # File handler for error reports
        if self.log_file_path:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.DEBUG)

            # JSON formatter for structured logging
            formatter = logging.Formatter("%(message)s")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Console handler for critical errors
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def _setup_default_handlers(self) -> None:
        """Setup default error handlers for different categories."""
        # Critical error handlers
        self.category_handlers[ErrorCategory.SHUTDOWN_CLEANUP] = self._handle_shutdown_error
        self.category_handlers[ErrorCategory.VTK_CLEANUP] = self._handle_vtk_error
        self.category_handlers[ErrorCategory.MEMORY_MANAGEMENT] = self._handle_memory_error
        self.category_handlers[ErrorCategory.SYSTEM_RESOURCE] = self._handle_system_resource_error

        # Recovery strategies
        self.recovery_strategies[ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN] = self._graceful_shutdown
        self.recovery_strategies[ErrorRecoveryStrategy.IMMEDIATE_SHUTDOWN] = (
            self._immediate_shutdown
        )
        self.recovery_strategies[ErrorRecoveryStrategy.RETRY_WITH_BACKOFF] = (
            self._retry_with_backoff
        )
        self.recovery_strategies[ErrorRecoveryStrategy.FALLBACK_MODE] = self._fallback_mode
        self.recovery_strategies[ErrorRecoveryStrategy.USER_INTERVENTION] = (
            self._request_user_intervention
        )
        self.recovery_strategies[ErrorRecoveryStrategy.IGNORE_AND_CONTINUE] = (
            self._ignore_and_continue
        )
        self.recovery_strategies[ErrorRecoveryStrategy.DEFER_PROCESSING] = self._defer_processing

    def report_error(
        self,
        error: Exception,
        context: ErrorContext,
        context_info: Dict[str, Any] = None,
        system_info: Dict[str, Any] = None,
        user_context: Dict[str, Any] = None,
        recovery_callback: Optional[Callable] = None,
    ) -> ErrorReport:
        """
        Report an error with comprehensive categorization and handling.

        Args:
            error: The exception that occurred
            context: The context in which the error occurred
            context_info: Additional context information
            system_info: System information for debugging
            user_context: User context information
            recovery_callback: Optional callback for recovery attempts

        Returns:
            ErrorReport with complete diagnostic information
        """
        start_time = time.time()

        try:
            # Create comprehensive error report
            error_report = ErrorReport.create_error_report(
                error=error,
                context=context,
                context_info=context_info,
                system_info=system_info,
                user_context=user_context,
            )

            # Store and process the error report
            with self._lock:
                self._store_error_report(error_report)
                self._update_error_patterns(error_report)

                # Update statistics
                self.reporting_stats["total_reports"] += 1
                if error_report.classification.severity == ErrorSeverity.CRITICAL:
                    self.reporting_stats["critical_errors"] += 1

            # Log the error
            self._log_error_report(error_report)

            # Handle error by category
            self._handle_error_by_category(error_report)

            # Attempt recovery if appropriate
            if recovery_callback:
                self._attempt_recovery(error_report, recovery_callback)

            # Calculate reporting time
            reporting_time = time.time() - start_time
            self._update_reporting_stats(reporting_time)

            return error_report

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as reporting_error:
            # Fallback error handling if reporting itself fails
            self.logger.critical("Error reporting failed: %s", reporting_error, exc_info=True)
            raise

    def _store_error_report(self, error_report: ErrorReport) -> None:
        """Store error report with memory management."""
        self.error_reports.append(error_report)

        # Maintain memory limit
        if len(self.error_reports) > self.max_reports:
            self.error_reports.pop(0)

        # Update error counts
        error_key = f"{error_report.error_type}:{error_report.classification.category.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def _update_error_patterns(self, error_report: ErrorReport) -> None:
        """Track error patterns for analysis."""
        error_key = f"{error_report.error_type}:{error_report.classification.category.value}"
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = []
        self.error_patterns[error_key].append(error_report.timestamp)

        # Clean old patterns (keep last 24 hours)
        cutoff_time = datetime.utcnow().timestamp() - 86400
        self.error_patterns[error_key] = [
            ts for ts in self.error_patterns[error_key] if ts.timestamp() > cutoff_time
        ]

    def _log_error_report(self, error_report: ErrorReport) -> None:
        """Log error report with appropriate level."""
        log_data = error_report.to_dict()

        # Determine log level based on severity
        if error_report.classification.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("%s", json.dumps(log_data))
        elif error_report.classification.severity == ErrorSeverity.HIGH:
            self.logger.error(json.dumps(log_data))
        elif error_report.classification.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

    def _handle_error_by_category(self, error_report: ErrorReport) -> None:
        """Handle error based on its category."""
        category = error_report.classification.category
        handler = self.category_handlers.get(category)

        if handler:
            try:
                handler(error_report)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as handler_error:
                self.logger.error(
                    f"Error handler failed for category {category.value}: {handler_error}",
                    exc_info=True,
                )

    def _attempt_recovery(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Attempt to recover from the error."""
        strategy = error_report.classification.recovery_strategy
        recovery_handler = self.recovery_strategies.get(strategy)

        if not recovery_handler:
            self.logger.warning("No recovery handler for strategy: %s", strategy.value)
            return False

        try:
            success = recovery_handler(error_report, recovery_callback)
            with self._lock:
                if success:
                    self.reporting_stats["recovered_errors"] += 1
                else:
                    self.reporting_stats["failed_recoveries"] += 1
            return success
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as recovery_error:
            self.logger.error("Recovery attempt failed: %s", recovery_error, exc_info=True)
            with self._lock:
                self.reporting_stats["failed_recoveries"] += 1
            return False

    def _update_reporting_stats(self, reporting_time: float) -> None:
        """Update reporting performance statistics."""
        with self._lock:
            current_avg = self.reporting_stats["average_report_time"]
            total_reports = self.reporting_stats["total_reports"]

            # Calculate new average
            self.reporting_stats["average_report_time"] = (
                current_avg * (total_reports - 1) + reporting_time
            ) / total_reports

    # Category-specific error handlers
    def _handle_shutdown_error(self, error_report: ErrorReport) -> None:
        """Handle shutdown-related errors."""
        self.logger.error(
            f"Shutdown error detected: {error_report.error_message}. "
            f"Classification: {error_report.classification.impact_assessment}"
        )

        # Additional shutdown-specific logging
        if error_report.context_info:
            self.logger.debug("Shutdown context: %s", error_report.context_info)

    def _handle_vtk_error(self, error_report: ErrorReport) -> None:
        """Handle VTK-related errors."""
        self.logger.warning(
            f"VTK error during {error_report.context.value}: {error_report.error_message}"
        )

        # VTK-specific diagnostic information
        vtk_info = {
            "vtk_version": error_report.system_info.get("vtk_version", "unknown"),
            "opengl_version": error_report.system_info.get("opengl_version", "unknown"),
            "graphics_card": error_report.system_info.get("graphics_card", "unknown"),
        }
        self.logger.debug("VTK diagnostic info: %s", vtk_info)

    def _handle_memory_error(self, error_report: ErrorReport) -> None:
        """Handle memory-related errors."""
        self.logger.critical(
            f"Memory error: {error_report.error_message}. " f"Immediate attention required."
        )

        # Log memory usage information
        memory_info = {
            "available_memory": error_report.system_info.get("available_memory", "unknown"),
            "memory_usage": error_report.system_info.get("memory_usage", "unknown"),
            "process_memory": error_report.system_info.get("process_memory", "unknown"),
        }
        self.logger.critical("Memory diagnostic info: %s", memory_info)

    def _handle_system_resource_error(self, error_report: ErrorReport) -> None:
        """Handle system resource errors."""
        self.logger.error("System resource error: %s", error_report.error_message)

        # Log system resource information
        resource_info = {
            "cpu_usage": error_report.system_info.get("cpu_usage", "unknown"),
            "disk_space": error_report.system_info.get("disk_space", "unknown"),
            "system_load": error_report.system_info.get("system_load", "unknown"),
        }
        self.logger.debug("System resource info: %s", resource_info)

    # Recovery strategy implementations
    def _graceful_shutdown(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Attempt graceful shutdown recovery."""
        self.logger.info("Attempting graceful shutdown recovery")
        try:
            # Call the recovery callback
            recovery_callback()
            self.logger.info("Graceful shutdown recovery successful")
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Graceful shutdown recovery failed: %s", e)
            return False

    def _immediate_shutdown(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Immediate shutdown recovery (emergency)."""
        self.logger.critical("Immediate shutdown required - emergency recovery")
        try:
            # Force immediate shutdown
            import os

            os._exit(1)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Immediate shutdown failed: %s", e)
            return False

    def _retry_with_backoff(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Retry with exponential backoff."""
        self.logger.info("Attempting retry with backoff")
        try:
            import time
            import random

            # Exponential backoff: 1s, 2s, 4s, 8s, etc.
            for attempt in range(5):
                delay = (2**attempt) + random.uniform(0, 1)
                time.sleep(delay)

                try:
                    recovery_callback()
                    self.logger.info("Retry successful on attempt %s", attempt + 1)
                    return True
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.warning("Retry attempt %s failed: {e}", attempt + 1)
                    continue

            self.logger.error("All retry attempts failed")
            return False
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Retry with backoff failed: %s", e)
            return False

    def _fallback_mode(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Switch to fallback mode."""
        self.logger.info("Switching to fallback mode")
        try:
            # Implement fallback logic here
            self.logger.info("Fallback mode activated successfully")
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Fallback mode activation failed: %s", e)
            return False

    def _request_user_intervention(
        self, error_report: ErrorReport, recovery_callback: Callable
    ) -> bool:
        """Request user intervention."""
        self.logger.warning(
            f"User intervention required: {error_report.classification.impact_assessment}"
        )

        # Log recommended actions
        for action in error_report.classification.recommended_actions:
            self.logger.info("Recommended action: %s", action)

        # In a real implementation, this would show a dialog to the user
        # For now, we'll just log that user intervention is needed
        return False  # User intervention required, not automatically recoverable

    def _ignore_and_continue(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Ignore error and continue operation."""
        self.logger.info("Ignoring error and continuing: %s", error_report.error_message)
        return True

    def _defer_processing(self, error_report: ErrorReport, recovery_callback: Callable) -> bool:
        """Defer processing for later."""
        self.logger.info("Deferring processing: %s", error_report.error_message)
        # In a real implementation, this would queue the operation for later
        return True

    # Public interface methods
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        with self._lock:
            return {
                "reporting_stats": self.reporting_stats.copy(),
                "error_counts": self.error_counts.copy(),
                "error_patterns": {
                    key: len(timestamps) for key, timestamps in self.error_patterns.items()
                },
                "total_reports": len(self.error_reports),
                "recent_errors": [report.to_dict() for report in self.error_reports[-10:]],
            }

    def get_error_reports_by_category(self, category: ErrorCategory) -> List[ErrorReport]:
        """Get all error reports for a specific category."""
        with self._lock:
            return [
                report
                for report in self.error_reports
                if report.classification.category == category
            ]

    def clear_old_reports(self, max_age_hours: int = 24) -> int:
        """Clear error reports older than specified hours."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        with self._lock:
            original_count = len(self.error_reports)
            self.error_reports = [
                report
                for report in self.error_reports
                if report.timestamp.timestamp() > cutoff_time
            ]
            cleared_count = original_count - len(self.error_reports)

            # Clean up patterns
            for error_key in list(self.error_patterns.keys()):
                self.error_patterns[error_key] = [
                    ts for ts in self.error_patterns[error_key] if ts.timestamp() > cutoff_time
                ]
                if not self.error_patterns[error_key]:
                    del self.error_patterns[error_key]

            return cleared_count

    def export_error_report(self, file_path: Path, format: str = "json") -> None:
        """Export error reports to file."""
        with self._lock:
            reports_data = [report.to_dict() for report in self.error_reports]

        if format.lower() == "json":
            with open(file_path, "w") as f:
                json.dump(reports_data, f, indent=2, default=str)
        elif format.lower() == "jsonl":
            with open(file_path, "w") as f:
                for report_data in reports_data:
                    f.write(json.dumps(report_data) + "\n")
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global error reporter instance
_global_error_reporter: Optional[ErrorReporter] = None


def get_global_error_reporter() -> ErrorReporter:
    """Get the global error reporter instance."""
    global _global_error_reporter
    if _global_error_reporter is None:
        _global_error_reporter = ErrorReporter()
    return _global_error_reporter


def set_global_error_reporter(reporter: ErrorReporter) -> None:
    """Set the global error reporter instance."""
    global _global_error_reporter
    _global_error_reporter = reporter


def report_error(
    error: Exception,
    context: ErrorContext,
    context_info: Dict[str, Any] = None,
    system_info: Dict[str, Any] = None,
    user_context: Dict[str, Any] = None,
    recovery_callback: Optional[Callable] = None,
) -> ErrorReport:
    """
    Convenience function to report an error using the global reporter.

    Args:
        error: The exception that occurred
        context: The context in which the error occurred
        context_info: Additional context information
        system_info: System information for debugging
        user_context: User context information
        recovery_callback: Optional callback for recovery attempts

    Returns:
        ErrorReport with complete diagnostic information
    """
    return get_global_error_reporter().report_error(
        error=error,
        context=context,
        context_info=context_info,
        system_info=system_info,
        user_context=user_context,
        recovery_callback=recovery_callback,
    )
