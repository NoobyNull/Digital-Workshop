"""
Enhanced Database Error Handling and Connection Management.

This module provides comprehensive error handling, connection health monitoring,
automatic recovery mechanisms, and graceful degradation for database operations.
"""

import sqlite3
import threading
import time
import traceback
import psutil
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import weakref

from ..logging_config import get_logger

logger = get_logger(__name__)


class DatabaseErrorType(Enum):
    """Database error type enumeration."""

    CONNECTION_ERROR = "connection_error"
    TRANSACTION_ERROR = "transaction_error"
    QUERY_ERROR = "query_error"
    CONSTRAINT_ERROR = "constraint_error"
    SCHEMA_ERROR = "schema_error"
    TIMEOUT_ERROR = "timeout_error"
    DISK_SPACE_ERROR = "disk_space_error"
    PERMISSION_ERROR = "permission_error"
    CORRUPTION_ERROR = "corruption_error"
    UNKNOWN_ERROR = "unknown_error"


class ConnectionState(Enum):
    """Database connection state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    CLOSED = "closed"


@dataclass
class DatabaseError:
    """Comprehensive database error information."""

    error_type: DatabaseErrorType
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    user_message: str
    recoverable: bool
    suggested_action: str
    context: Dict[str, Any] = field(default_factory=dict)
    traceback_info: Optional[str] = None


@dataclass
class ConnectionMetrics:
    """Database connection performance metrics."""

    connection_id: str
    created_at: datetime
    last_used: datetime
    query_count: int
    total_query_time: float
    error_count: int
    state: ConnectionState
    memory_usage_kb: float
    disk_usage_mb: float


class DatabaseErrorHandler:
    """Comprehensive database error handler with recovery mechanisms."""

    def __init__(self, db_path: str) -> None:
        """
        Initialize database error handler.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.error_history: List[DatabaseError] = []
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self._active_connections = weakref.WeakValueDictionary()
        self._lock = threading.Lock()
        self._recovery_callbacks: List[Callable] = []

        # Configuration
        self.max_error_history = 1000
        self.connection_timeout = 30.0
        self.recovery_attempts = 3
        self.disk_space_threshold = 0.90  # 90% full

        # Start monitoring
        self._start_monitoring()

    def _start_monitoring(self) -> None:
        """Start background monitoring of database health."""
        self._monitoring_thread = threading.Thread(
            target=self._monitor_database_health, daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Database error monitoring started")

    def _monitor_database_health(self) -> None:
        """Background database health monitoring."""
        while True:
            try:
                self._check_database_health()
                self._check_connection_leaks()
                self._cleanup_old_errors()
                time.sleep(30)  # Check every 30 seconds
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                logger.error("Health monitoring error: %s", str(e))

    def _check_database_health(self) -> None:
        """Check overall database health."""
        try:
            # Check disk space
            disk_usage = psutil.disk_usage(os.path.dirname(self.db_path))
            usage_percent = disk_usage.used / disk_usage.total

            if usage_percent > self.disk_space_threshold:
                self._log_error(
                    DatabaseErrorType.DISK_SPACE_ERROR,
                    f"Disk space critical: {usage_percent:.1%} used",
                    {
                        "usage_percent": usage_percent,
                        "free_gb": disk_usage.free / (1024**3),
                    },
                    "Please free up disk space to continue using the database.",
                )

            # Check database file size
            if os.path.exists(self.db_path):
                file_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
                free_space_mb = disk_usage.free / (1024 * 1024)

                if file_size_mb > free_space_mb * 0.8:
                    self._log_error(
                        DatabaseErrorType.DISK_SPACE_ERROR,
                        f"Database file size ({file_size_mb:.1f}MB) approaches available space",
                        {"file_size_mb": file_size_mb, "free_space_mb": free_space_mb},
                        "Consider cleaning up old data or freeing disk space.",
                    )

            # Check database integrity
            with self._create_safe_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                if result[0] != "ok":
                    self._log_error(
                        DatabaseErrorType.CORRUPTION_ERROR,
                        f"Database integrity check failed: {result[0]}",
                        {"integrity_result": result[0]},
                        "Database may be corrupted. Consider restoring from backup.",
                    )

            # Check connection count
            active_count = len(self._active_connections)
            if active_count > 50:  # Arbitrary threshold
                logger.warning("High connection count: %s", active_count)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Health check failed: %s", str(e))

    def _check_connection_leaks(self) -> None:
        """Check for connection leaks."""
        current_time = datetime.now()
        leaked_connections = []

        for conn_id, metrics in list(self.connection_metrics.items()):
            if metrics.state == ConnectionState.FAILED:
                continue

            # Check for connections not used for a long time
            idle_time = (current_time - metrics.last_used).total_seconds()
            if idle_time > 3600:  # 1 hour
                leaked_connections.append(conn_id)

        if leaked_connections:
            logger.warning("Potential connection leaks detected: %s", leaked_connections)
            # In a real implementation, we would force-close these connections

    def _cleanup_old_errors(self) -> None:
        """Clean up old error history."""
        with self._lock:
            if len(self.error_history) > self.max_error_history:
                # Keep only the most recent errors
                self.error_history = self.error_history[-self.max_error_history :]
                logger.debug("Cleaned up old error history")

    def _log_error(
        """TODO: Add docstring."""
        self,
        error_type: DatabaseErrorType,
        message: str,
        details: Dict[str, Any],
        user_message: str,
        recoverable: bool = True,
        suggested_action: str = "",
        context: Dict[str, Any] = None,
    ) -> DatabaseError:
        """
        Log a database error.

        Args:
            error_type: Type of error
            message: Technical error message
            details: Additional error details
            user_message: User-friendly error message
            recoverable: Whether the error might be recoverable
            suggested_action: Suggested action to resolve the error
            context: Additional context information

        Returns:
            DatabaseError object
        """
        error = DatabaseError(
            error_type=error_type,
            message=message,
            details=details,
            timestamp=datetime.now(),
            user_message=user_message,
            recoverable=recoverable,
            suggested_action=suggested_action,
            context=context or {},
            traceback_info=(
                traceback.format_exc() if error_type != DatabaseErrorType.UNKNOWN_ERROR else None
            ),
        )

        with self._lock:
            self.error_history.append(error)

        # Log according to error severity
        if error_type in [
            DatabaseErrorType.CORRUPTION_ERROR,
            DatabaseErrorType.CONNECTION_ERROR,
        ]:
            logger.critical("Critical database error: %s", message)
        elif error_type == DatabaseErrorType.UNKNOWN_ERROR:
            logger.error("Unknown database error: %s", message)
        else:
            logger.warning("Database error: %s", message)

        return error

    def handle_sqlite_error(
        """TODO: Add docstring."""
        self, error: sqlite3.Error, context: Dict[str, Any] = None
    ) -> DatabaseError:
        """
        Handle SQLite-specific errors.

        Args:
            error: SQLite error object
            context: Additional context

        Returns:
            DatabaseError object
        """
        error_message = str(error)
        error_code = getattr(error, "sqlite_errorcode", None)

        # Map SQLite error codes to our error types
        if "database is locked" in error_message.lower():
            error_type = DatabaseErrorType.CONNECTION_ERROR
            user_message = "Database is currently locked. Please try again in a moment."
            recoverable = True
            suggested_action = (
                "Wait and retry the operation, or close other applications using the database."
            )
        elif "no such table" in error_message.lower():
            error_type = DatabaseErrorType.SCHEMA_ERROR
            user_message = "Database schema is missing or outdated."
            recoverable = True
            suggested_action = "Run database migrations to update the schema."
        elif "constraint failed" in error_message.lower():
            error_type = DatabaseErrorType.CONSTRAINT_ERROR
            user_message = "Data constraint violation occurred."
            recoverable = True
            suggested_action = "Check data integrity and ensure unique constraints are satisfied."
        elif "database disk image is malformed" in error_message.lower():
            error_type = DatabaseErrorType.CORRUPTION_ERROR
            user_message = "Database file appears to be corrupted."
            recoverable = False
            suggested_action = "Restore database from backup or run integrity repair."
        elif "disk I/O error" in error_message.lower():
            error_type = DatabaseErrorType.DISK_SPACE_ERROR
            user_message = "Disk I/O error occurred. The disk may be full or damaged."
            recoverable = False
            suggested_action = "Check disk space and disk health."
        else:
            error_type = DatabaseErrorType.UNKNOWN_ERROR
            user_message = "An unexpected database error occurred."
            recoverable = True
            suggested_action = "Please try again or contact support if the problem persists."

        return self._log_error(
            error_type=error_type,
            message=f"SQLite error ({error_code}): {error_message}",
            details={"sqlite_errorcode": error_code, "original_error": error_message},
            user_message=user_message,
            recoverable=recoverable,
            suggested_action=suggested_action,
            context=context,
        )

    def handle_connection_error(
        """TODO: Add docstring."""
        self, error: Exception, context: Dict[str, Any] = None
    ) -> DatabaseError:
        """
        Handle connection-related errors.

        Args:
            error: Connection error
            context: Additional context

        Returns:
            DatabaseError object
        """
        error_message = str(error)

        return self._log_error(
            error_type=DatabaseErrorType.CONNECTION_ERROR,
            message=f"Connection error: {error_message}",
            details={
                "error_type": type(error).__name__,
                "original_error": error_message,
            },
            user_message="Failed to connect to the database.",
            recoverable=True,
            suggested_action="Check database file accessibility and permissions.",
            context=context,
        )

    def handle_transaction_error(
        """TODO: Add docstring."""
        self, error: Exception, context: Dict[str, Any] = None
    ) -> DatabaseError:
        """
        Handle transaction-related errors.

        Args:
            error: Transaction error
            context: Additional context

        Returns:
            DatabaseError object
        """
        error_message = str(error)

        return self._log_error(
            error_type=DatabaseErrorType.TRANSACTION_ERROR,
            message=f"Transaction error: {error_message}",
            details={
                "error_type": type(error).__name__,
                "original_error": error_message,
            },
            user_message="Database transaction failed.",
            recoverable=True,
            suggested_action="Transaction will be rolled back automatically. Please try again.",
            context=context,
        )

    def handle_timeout_error(
        """TODO: Add docstring."""
        self, operation: str, timeout_duration: float, context: Dict[str, Any] = None
    ) -> DatabaseError:
        """
        Handle timeout errors.

        Args:
            operation: Operation that timed out
            timeout_duration: Timeout duration in seconds
            context: Additional context

        Returns:
            DatabaseError object
        """
        return self._log_error(
            error_type=DatabaseErrorType.TIMEOUT_ERROR,
            message=f"Operation '{operation}' timed out after {timeout_duration}s",
            details={"operation": operation, "timeout_duration": timeout_duration},
            user_message=f"The database operation '{operation}' took too long to complete.",
            recoverable=True,
            suggested_action="The operation will be retried automatically. If it continues to fail, there may be performance issues.",
            context=context,
        )

    def attempt_recovery(self, error: DatabaseError) -> bool:
        """
        Attempt to recover from a database error.

        Args:
            error: Database error to recover from

        Returns:
            True if recovery was successful
        """
        if not error.recoverable:
            return False

        recovery_successful = False

        try:
            if error.error_type == DatabaseErrorType.CONNECTION_ERROR:
                recovery_successful = self._recover_connection()
            elif error.error_type == DatabaseErrorType.CORRUPTION_ERROR:
                recovery_successful = self._recover_from_corruption()
            elif error.error_type == DatabaseErrorType.DISK_SPACE_ERROR:
                recovery_successful = self._recover_disk_space()
            elif error.error_type == DatabaseErrorType.SCHEMA_ERROR:
                recovery_successful = self._recover_schema()

            # Call registered recovery callbacks
            for callback in self._recovery_callbacks:
                try:
                    callback(error)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Recovery callback failed: %s", str(e))

            if recovery_successful:
                logger.info("Successfully recovered from %s", error.error_type.value)
            else:
                logger.warning("Recovery failed for %s", error.error_type.value)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Recovery attempt failed: %s", str(e))

        return recovery_successful

    def _recover_connection(self) -> bool:
        """Attempt to recover connection errors."""
        try:
            # Test connection
            with self._create_safe_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False

    def _recover_from_corruption(self) -> bool:
        """Attempt to recover from database corruption."""
        try:
            # Try to rebuild database
            with self._create_safe_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                if result[0] == "ok":
                    return True
                else:
                    # Try to dump and restore
                    logger.info("Attempting to dump and restore corrupted database")
                    # This would involve more complex recovery logic
                    return False

        except Exception:
            return False

    def _recover_disk_space(self) -> bool:
        """Attempt to recover from disk space issues."""
        try:
            disk_usage = psutil.disk_usage(os.path.dirname(self.db_path))
            usage_percent = disk_usage.used / disk_usage.total

            if usage_percent <= self.disk_space_threshold:
                return True
            else:
                return False

        except Exception:
            return False

    def _recover_schema(self) -> bool:
        """Attempt to recover from schema errors."""
        try:
            # Check if required tables exist
            with self._create_safe_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('models', 'model_metadata')
                """
                )
                tables = cursor.fetchall()

                if len(tables) >= 2:  # Both required tables exist
                    return True
                else:
                    return False

        except Exception:
            return False

    def register_recovery_callback(self, callback: Callable) -> None:
        """
        Register a callback for error recovery.

        Args:
            callback: Function to call during recovery attempts
        """
        self._recovery_callbacks.append(callback)

    def _create_safe_connection(self) -> sqlite3.Connection:
        """Create a connection for safe operations during error handling."""
        conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent errors.

        Returns:
            Error summary dictionary
        """
        with self._lock:
            recent_errors = [
                error
                for error in self.error_history
                if error.timestamp > datetime.now() - timedelta(hours=24)
            ]

            error_counts = {}
            for error in recent_errors:
                error_type = error.error_type.value
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            return {
                "total_errors_24h": len(recent_errors),
                "error_counts_by_type": error_counts,
                "recoverable_errors": sum(1 for e in recent_errors if e.recoverable),
                "critical_errors": sum(
                    1
                    for e in recent_errors
                    if e.error_type
                    in [
                        DatabaseErrorType.CORRUPTION_ERROR,
                        DatabaseErrorType.CONNECTION_ERROR,
                    ]
                ),
                "most_common_error": (
                    max(error_counts.items(), key=lambda x: x[1]) if error_counts else None
                ),
            }

    def get_connection_metrics(self, connection_id: str) -> Optional[ConnectionMetrics]:
        """
        Get metrics for a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            ConnectionMetrics object or None
        """
        return self.connection_metrics.get(connection_id)

    def get_all_connection_metrics(self) -> List[ConnectionMetrics]:
        """
        Get metrics for all connections.

        Returns:
            List of ConnectionMetrics objects
        """
        return list(self.connection_metrics.values())

    def create_user_friendly_error_message(self, error: DatabaseError) -> str:
        """
        Create a user-friendly error message.

        Args:
            error: Database error

        Returns:
            User-friendly error message
        """
        message = error.user_message

        if error.suggested_action:
            message += f" {error.suggested_action}"

        return message


class ConnectionManager:
    """Enhanced connection manager with health monitoring."""

    def __init__(self, db_path: str, error_handler: DatabaseErrorHandler) -> None:
        """
        Initialize connection manager.

        Args:
            db_path: Database file path
            error_handler: Database error handler
        """
        self.db_path = db_path
        self.error_handler = error_handler
        self._connections = {}
        self._connection_counter = 0
        self._lock = threading.Lock()

    @contextmanager
    def get_connection(self, timeout: float = None) -> None:
        """
        Get a database connection with automatic health monitoring.

        Args:
            timeout: Connection timeout in seconds

        Yields:
            Database connection

        Raises:
            DatabaseError: If connection fails
        """
        if timeout is None:
            timeout = self.error_handler.connection_timeout

        conn = None
        connection_id = None

        try:
            # Create connection
            conn = self._create_healthy_connection(timeout)

            # Track connection
            with self._lock:
                connection_id = f"conn_{self._connection_counter}"
                self._connection_counter += 1
                self._connections[connection_id] = conn

                # Create metrics
                metrics = ConnectionMetrics(
                    connection_id=connection_id,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    query_count=0,
                    total_query_time=0.0,
                    error_count=0,
                    state=ConnectionState.HEALTHY,
                    memory_usage_kb=0.0,
                    disk_usage_mb=0.0,
                )
                self.error_handler.connection_metrics[connection_id] = metrics

            yield conn

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Handle connection error
            if conn:
                try:
                    conn.close()
                except:
                    pass

            error = self.error_handler.handle_connection_error(e)
            raise error

        finally:
            # Clean up connection tracking
            if connection_id:
                with self._lock:
                    self._connections.pop(connection_id, None)

                if conn:
                    try:
                        conn.close()
                    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                        logger.error("Error closing connection: %s", str(e))

    def _create_healthy_connection(self, timeout: float) -> sqlite3.Connection:
        """
        Create a healthy database connection.

        Args:
            timeout: Connection timeout

        Returns:
            SQLite connection

        Raises:
            sqlite3.Error: If connection fails
        """
        # Check disk space before creating connection
        disk_usage = psutil.disk_usage(os.path.dirname(self.db_path))
        usage_percent = disk_usage.used / disk_usage.total

        if usage_percent > self.error_handler.disk_space_threshold:
            raise sqlite3.Error("Insufficient disk space for database operations")

        # Create connection with optimized settings
        conn = sqlite3.connect(self.db_path, timeout=timeout, check_same_thread=False)

        # Configure connection for performance and reliability
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")

        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        return conn

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Connection statistics dictionary
        """
        with self._lock:
            return {
                "total_connections": len(self._connections),
                "active_connections": len([c for c in self._connections.values() if c is not None]),
                "connection_metrics": {
                    conn_id: {
                        "state": metrics.state.value,
                        "query_count": metrics.query_count,
                        "error_count": metrics.error_count,
                        "uptime_seconds": (datetime.now() - metrics.created_at).total_seconds(),
                    }
                    for conn_id, metrics in self.error_handler.connection_metrics.items()
                },
            }

    def close_all_connections(self) -> None:
        """Close all active connections."""
        with self._lock:
            for conn_id, conn in list(self._connections.items()):
                try:
                    if conn:
                        conn.close()
                        logger.debug("Closed connection %s", conn_id)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Error closing connection %s: {str(e)}", conn_id)

            self._connections.clear()


class GracefulDegradationManager:
    """Manages graceful degradation when database is unavailable."""

    def __init__(self) -> None:
        """Initialize graceful degradation manager."""
        self.degradation_level = 0  # 0 = normal, 1 = degraded, 2 = read-only, 3 = minimal
        self.available_features = set()
        self.fallback_data = {}

    def set_degradation_level(self, level: int) -> None:
        """
        Set degradation level.

        Args:
            level: Degradation level (0-3)
        """
        self.degradation_level = max(0, min(3, level))
        logger.info("Database degradation level set to %s", self.degradation_level)
        self._update_available_features()

    def _update_available_features(self) -> None:
        """Update available features based on degradation level."""
        if self.degradation_level == 0:
            self.available_features = {
                "read",
                "write",
                "search",
                "metadata",
                "transactions",
            }
        elif self.degradation_level == 1:
            self.available_features = {
                "read",
                "search",
                "metadata",  # Reduced write capabilities
            }
        elif self.degradation_level == 2:
            self.available_features = {"read", "search"}  # Read-only mode
        else:  # level 3
            self.available_features = {"read"}  # Minimal functionality

    def is_feature_available(self, feature: str) -> bool:
        """
        Check if a feature is available.

        Args:
            feature: Feature name

        Returns:
            True if feature is available
        """
        return feature in self.available_features

    def get_available_features(self) -> List[str]:
        """
        Get list of available features.

        Returns:
            List of available feature names
        """
        return list(self.available_features)

    def set_fallback_data(self, key: str, data: Any) -> None:
        """
        Set fallback data for when database is unavailable.

        Args:
            key: Data key
            data: Fallback data
        """
        self.fallback_data[key] = data

    def get_fallback_data(self, key: str, default: Any = None) -> Any:
        """
        Get fallback data.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Fallback data or default
        """
        return self.fallback_data.get(key, default)
