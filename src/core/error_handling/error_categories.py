"""
Error Categories and Classification System

This module defines a comprehensive error categorization system for the shutdown
and application error handling. It provides structured error classification,
severity levels, and recovery strategies.
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import platform
import sys


class ErrorSeverity(Enum):
    """Error severity levels for proper categorization and handling."""

    CRITICAL = "critical"  # Application cannot continue, immediate shutdown required
    HIGH = "high"  # Major functionality broken, user action required
    MEDIUM = "medium"  # Functionality degraded, workarounds available
    LOW = "low"  # Minor issues, cosmetic problems
    WARNING = "warning"  # Potential issues, preventive action recommended
    INFO = "info"  # Informational messages, not errors


class ErrorCategory(Enum):
    """Error categories for systematic classification."""

    # Shutdown and Cleanup Errors
    SHUTDOWN_CLEANUP = "shutdown_cleanup"
    VTK_CLEANUP = "vtk_cleanup"
    OPENGL_CLEANUP = "opengl_cleanup"
    RESOURCE_CLEANUP = "resource_cleanup"
    CONTEXT_MANAGEMENT = "context_management"

    # System and Platform Errors
    SYSTEM_RESOURCE = "system_resource"
    MEMORY_MANAGEMENT = "memory_management"
    PLATFORM_COMPATIBILITY = "platform_compatibility"
    HARDWARE_ACCELERATION = "hardware_acceleration"

    # Application Logic Errors
    PARSING_ERROR = "parsing_error"
    FILE_IO_ERROR = "file_io_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"

    # UI and Rendering Errors
    UI_RENDERING = "ui_rendering"
    THEME_ERROR = "theme_error"
    WIDGET_ERROR = "widget_error"
    VIEWER_ERROR = "viewer_error"

    # External Dependencies
    DEPENDENCY_ERROR = "dependency_error"
    LIBRARY_ERROR = "library_error"
    PLUGIN_ERROR = "plugin_error"

    # User Interaction
    USER_INPUT_ERROR = "user_input_error"
    PERMISSION_ERROR = "permission_error"
    VALIDATION_ERROR = "validation_error"


class ErrorRecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    IMMEDIATE_SHUTDOWN = "immediate_shutdown"  # Stop application immediately
    GRACEFUL_SHUTDOWN = "graceful_shutdown"  # Clean shutdown with error reporting
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry operation with exponential backoff
    FALLBACK_MODE = "fallback_mode"  # Switch to fallback implementation
    USER_INTERVENTION = "user_intervention"  # Request user action
    IGNORE_AND_CONTINUE = "ignore_and_continue"  # Log error and continue operation
    DEFER_PROCESSING = "defer_processing"  # Queue for later processing


class ErrorContext(Enum):
    """Context in which errors occur."""

    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    NORMAL_OPERATION = "normal_operation"
    USER_INTERACTION = "user_interaction"
    BACKGROUND_PROCESSING = "background_processing"
    FILE_LOADING = "file_loading"
    FILE_SAVING = "file_saving"
    RENDERING = "rendering"
    PARSING = "parsing"
    CLEANUP = "cleanup"


@dataclass
class ErrorClassification:
    """Complete error classification with all relevant metadata."""

    category: ErrorCategory
    severity: ErrorSeverity
    recovery_strategy: ErrorRecoveryStrategy
    context: ErrorContext
    is_recoverable: bool
    requires_user_action: bool
    can_be_retried: bool
    impact_assessment: str
    recommended_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert classification to dictionary for logging."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_strategy": self.recovery_strategy.value,
            "context": self.context.value,
            "is_recoverable": self.is_recoverable,
            "requires_user_action": self.requires_user_action,
            "can_be_retried": self.can_be_retried,
            "impact_assessment": self.impact_assessment,
            "recommended_actions": self.recommended_actions,
        }


class ErrorClassifier:
    """Intelligent error classification based on exception type and context."""

    # Classification rules mapping exception types to classifications
    _classification_rules: Dict[type, ErrorClassification] = {
        # Critical shutdown errors
        RuntimeError: ErrorClassification(
            category=ErrorCategory.SHUTDOWN_CLEANUP,
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN,
            context=ErrorContext.SHUTDOWN,
            is_recoverable=False,
            requires_user_action=False,
            can_be_retried=False,
            impact_assessment="Critical runtime error during shutdown - immediate attention required",
            recommended_actions=[
                "Check system resources",
                "Review recent changes",
                "Contact support if persistent",
            ],
        ),
        # Memory and resource errors
        MemoryError: ErrorClassification(
            category=ErrorCategory.MEMORY_MANAGEMENT,
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=ErrorRecoveryStrategy.IMMEDIATE_SHUTDOWN,
            context=ErrorContext.NORMAL_OPERATION,
            is_recoverable=False,
            requires_user_action=True,
            can_be_retried=False,
            impact_assessment="Out of memory - application cannot continue",
            recommended_actions=[
                "Close other applications",
                "Increase virtual memory",
                "Restart application",
            ],
        ),
        # File I/O errors
        FileNotFoundError: ErrorClassification(
            category=ErrorCategory.FILE_IO_ERROR,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=ErrorRecoveryStrategy.USER_INTERVENTION,
            context=ErrorContext.FILE_LOADING,
            is_recoverable=True,
            requires_user_action=True,
            can_be_retried=True,
            impact_assessment="Required file not found - user action needed",
            recommended_actions=[
                "Check file path",
                "Verify file exists",
                "Select alternative file",
            ],
        ),
        PermissionError: ErrorClassification(
            category=ErrorCategory.PERMISSION_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=ErrorRecoveryStrategy.USER_INTERVENTION,
            context=ErrorContext.FILE_IO_ERROR,
            is_recoverable=True,
            requires_user_action=True,
            can_be_retried=True,
            impact_assessment="Insufficient permissions - user action required",
            recommended_actions=[
                "Check file permissions",
                "Run as administrator",
                "Contact system administrator",
            ],
        ),
        # VTK and OpenGL errors
        Exception: ErrorClassification(  # Generic fallback
            category=ErrorCategory.VTK_CLEANUP,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=ErrorRecoveryStrategy.IGNORE_AND_CONTINUE,
            context=ErrorContext.SHUTDOWN,
            is_recoverable=True,
            requires_user_action=False,
            can_be_retried=False,
            impact_assessment="Generic error during VTK cleanup - may be expected during shutdown",
            recommended_actions=[
                "Monitor for patterns",
                "Check VTK version compatibility",
                "Review recent graphics driver updates",
            ],
        ),
    }

    @classmethod
    def classify_error(
        cls, error: Exception, context: ErrorContext = ErrorContext.NORMAL_OPERATION
    ) -> ErrorClassification:
        """
        Classify an error based on its type and context.

        Args:
            error: The exception to classify
            context: The context in which the error occurred

        Returns:
            ErrorClassification with complete error categorization
        """
        error_type = type(error)

        # Find the most specific classification rule
        classification = cls._classification_rules.get(error_type)

        if classification is None:
            # Try to find a parent class match
            for rule_type, rule_classification in cls._classification_rules.items():
                if isinstance(error, rule_type):
                    classification = rule_classification
                    break

        if classification is None:
            # Default classification for unknown errors
            classification = ErrorClassification(
                category=ErrorCategory.DEPENDENCY_ERROR,
                severity=ErrorSeverity.MEDIUM,
                recovery_strategy=ErrorRecoveryStrategy.IGNORE_AND_CONTINUE,
                context=context,
                is_recoverable=True,
                requires_user_action=False,
                can_be_retried=True,
                impact_assessment="Unknown error type - requires investigation",
                recommended_actions=[
                    "Check error details",
                    "Review logs for patterns",
                    "Report to development team",
                ],
            )

        # Update context if different
        if classification.context != context:
            classification.context = context

        return classification

    @classmethod
    def register_classification_rule(
        cls, error_type: type, classification: ErrorClassification
    ) -> None:
        """
        Register a new classification rule for a specific error type.

        Args:
            error_type: The exception type to classify
            classification: The classification to apply
        """
        cls._classification_rules[error_type] = classification

    @classmethod
    def get_classification_rules(cls) -> Dict[type, ErrorClassification]:
        """Get all registered classification rules."""
        return cls._classification_rules.copy()


@dataclass
class ErrorReport:
    """Comprehensive error report with all diagnostic information."""

    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    classification: ErrorClassification
    stack_trace: str
    context_info: Dict[str, Any]
    system_info: Dict[str, Any]
    user_context: Dict[str, Any]
    previous_errors: List[str]  # IDs of related previous errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary for logging."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "classification": self.classification.to_dict(),
            "stack_trace": self.stack_trace,
            "context_info": self.context_info,
            "system_info": self.system_info,
            "user_context": self.user_context,
            "previous_errors": self.previous_errors,
        }

    @classmethod
    def create_error_report(
        cls,
        error: Exception,
        context: ErrorContext,
        context_info: Dict[str, Any] = None,
        system_info: Dict[str, Any] = None,
        user_context: Dict[str, Any] = None,
    ) -> "ErrorReport":
        """
        Create a comprehensive error report.

        Args:
            error: The exception that occurred
            context: The context in which the error occurred
            context_info: Additional context information
            system_info: System information for debugging
            user_context: User context information

        Returns:
            ErrorReport with complete diagnostic information
        """
        import traceback

        classification = ErrorClassifier.classify_error(error, context)

        return cls(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            classification=classification,
            stack_trace="".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            ),
            context_info=context_info or {},
            system_info=system_info or cls._get_system_info(),
            user_context=user_context or {},
            previous_errors=[],
        )

    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """Get system information for error reporting."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node(),
        }
