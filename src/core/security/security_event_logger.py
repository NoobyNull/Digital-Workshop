"""
Security event logging for tracking security-related events.

Logs security events like failed authentication, path validation failures, etc.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityEventType(Enum):
    """Types of security events."""

    PATH_VALIDATION_FAILED = "path_validation_failed"
    INVALID_FILE_TYPE = "invalid_file_type"
    SYSTEM_FILE_BLOCKED = "system_file_blocked"
    CREDENTIAL_ACCESS = "credential_access"
    ENCRYPTION_FAILED = "encryption_failed"
    DECRYPTION_FAILED = "decryption_failed"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class SecurityEventLogger:
    """Logs security-related events for audit trail."""

    def __init__(self) -> None:
        """Initialize security event logger."""
        self.logger = get_logger("security")
        self.events = []

    def log_event(
        self,
        event_type: SecurityEventType,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
    ) -> None:
        """Log a security event.

        Args:
            event_type: Type of security event
            description: Human-readable description
            details: Additional event details
            severity: Log level (INFO, WARNING, ERROR, CRITICAL)
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type.value,
            "description": description,
            "details": details or {},
        }

        self.events.append(event)

        # Log to file
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(
            "Security Event: %s - %s",
            event_type.value,
            description,
            extra={"security_event": event},
        )

    def log_path_validation_failure(self, path: str, reason: str) -> None:
        """Log path validation failure.

        Args:
            path: Path that failed validation
            reason: Reason for failure
        """
        self.log_event(
            SecurityEventType.PATH_VALIDATION_FAILED,
            "Path validation failed",
            {"path": path, "reason": reason},
            "WARNING",
        )

    def log_invalid_file_type(self, file_path: str, file_type: str) -> None:
        """Log invalid file type attempt.

        Args:
            file_path: Path to file
            file_type: File type/extension
        """
        self.log_event(
            SecurityEventType.INVALID_FILE_TYPE,
            "Invalid file type attempted",
            {"file_path": file_path, "file_type": file_type},
            "WARNING",
        )

    def log_system_file_blocked(self, file_path: str) -> None:
        """Log system file block.

        Args:
            file_path: Path to system file
        """
        self.log_event(
            SecurityEventType.SYSTEM_FILE_BLOCKED,
            "System file blocked from import",
            {"file_path": file_path},
            "WARNING",
        )

    def log_credential_access(self, credential_type: str, success: bool) -> None:
        """Log credential access attempt.

        Args:
            credential_type: Type of credential accessed
            success: Whether access was successful
        """
        self.log_event(
            SecurityEventType.CREDENTIAL_ACCESS,
            "Credential access attempt",
            {"credential_type": credential_type, "success": success},
            "INFO",
        )

    def get_events(self, event_type: Optional[SecurityEventType] = None) -> list:
        """Get logged events, optionally filtered by type.

        Args:
            event_type: Optional event type to filter by

        Returns:
            List of events
        """
        if event_type is None:
            return self.events

        return [e for e in self.events if e["type"] == event_type.value]

    def clear_events(self) -> None:
        """Clear all logged events."""
        self.events.clear()
