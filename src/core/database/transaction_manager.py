"""
Comprehensive Transaction Management System.

This module provides robust transaction management with connection pooling,
retry mechanisms, rollback support, and comprehensive error handling.
"""

import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
from enum import Enum

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class TransactionState(Enum):
    """Transaction state enumeration."""

    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DatabaseError(Exception):
    """Custom database exception for better error handling."""


class TransactionError(DatabaseError):
    """Transaction-specific exception."""


class ConnectionPool:
    """Thread-safe connection pool for database connections."""

    def __init__(self, db_path: str, max_connections: int = 10, timeout: float = 30.0):
        """
        Initialize connection pool.

        Args:
            db_path: Path to the SQLite database file
            max_connections: Maximum number of connections in pool
            timeout: Connection timeout in seconds
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = []
        self._active_connections = 0
        self._lock = threading.Lock()
        self._connection_counter = 0

    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection from the pool.

        Returns:
            Database connection

        Raises:
            DatabaseError: If unable to get connection
        """
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            with self._lock:
                # Try to reuse an existing connection
                if self._pool:
                    conn = self._pool.pop()
                    try:
                        # Test if connection is still valid
                        conn.execute("SELECT 1")
                        return conn
                    except sqlite3.Error:
                        # Connection is broken, discard it
                        continue

                # Create new connection if under limit
                if self._active_connections < self.max_connections:
                    self._active_connections += 1
                    try:
                        conn = self._create_connection()
                        return conn
                    except sqlite3.Error:
                        self._active_connections -= 1
                        raise DatabaseError(
                            f"Failed to create database connection to {self.db_path}"
                        )

            # Wait a bit before retrying
            time.sleep(0.1)

        raise DatabaseError(f"Timeout waiting for database connection after {self.timeout}s")

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """
        Return a connection to the pool.

        Args:
            conn: Database connection to return
        """
        with self._lock:
            try:
                # Test if connection is still valid
                conn.execute("SELECT 1")

                # Return to pool if under limit
                if len(self._pool) < self.max_connections:
                    self._pool.append(conn)
                else:
                    # Pool is full, close the connection
                    conn.close()
                    self._active_connections -= 1
            except sqlite3.Error:
                # Connection is broken, close it
                try:
                    conn.close()
                except:
                    pass
                self._active_connections -= 1

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Set WAL mode for better performance
        conn.execute("PRAGMA journal_mode = WAL")

        # Optimize for performance
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")

        # Enable auto-vacuum
        conn.execute("PRAGMA auto_vacuum = INCREMENTAL")

        return conn

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except:
                    pass
            self._pool.clear()
            self._active_connections = 0


class Transaction:
    """Represents a database transaction with state tracking."""

    def __init__(self, connection: sqlite3.Connection, transaction_id: str = None):
        """
        Initialize transaction.

        Args:
            connection: Database connection
            transaction_id: Unique transaction identifier
        """
        self.connection = connection
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.state = TransactionState.PENDING
        self.start_time = time.time()
        self.operations = []
        self._savepoint_name = f"sp_{self.transaction_id.replace('-', '_')}"

    def begin(self) -> None:
        """Begin the transaction."""
        try:
            self.connection.execute(f"SAVEPOINT {self._savepoint_name}")
            self.state = TransactionState.ACTIVE
            logger.debug("Transaction %s started", self.transaction_id)
        except sqlite3.Error as e:
            self.state = TransactionState.FAILED
            raise TransactionError(f"Failed to begin transaction: {str(e)}")

    def commit(self) -> None:
        """Commit the transaction."""
        try:
            self.connection.execute(f"RELEASE SAVEPOINT {self._savepoint_name}")
            self.state = TransactionState.COMMITTED
            duration = time.time() - self.start_time
            logger.info("Transaction %s committed in {duration:.3f}s", self.transaction_id)
        except sqlite3.Error as e:
            self.state = TransactionState.FAILED
            raise TransactionError(f"Failed to commit transaction: {str(e)}")

    def rollback(self) -> None:
        """Rollback the transaction."""
        try:
            self.connection.execute(f"ROLLBACK TO SAVEPOINT {self._savepoint_name}")
            self.connection.execute(f"RELEASE SAVEPOINT {self._savepoint_name}")
            self.state = TransactionState.ROLLED_BACK
            duration = time.time() - self.start_time
            logger.info("Transaction %s rolled back after {duration:.3f}s", self.transaction_id)
        except sqlite3.Error as e:
            self.state = TransactionState.FAILED
            logger.error("Failed to rollback transaction %s: {str(e)}", self.transaction_id)

    def add_operation(self, operation: str, params: tuple = None) -> None:
        """Add an operation to the transaction log."""
        self.operations.append({"operation": operation, "params": params, "timestamp": time.time()})

    def get_duration(self) -> float:
        """Get transaction duration in seconds."""
        return time.time() - self.start_time


class TransactionManager:
    """Comprehensive transaction management system."""

    def __init__(self, db_path: str, max_retries: int = 3, retry_delay: float = 0.1):
        """
        Initialize transaction manager.

        Args:
            db_path: Path to the SQLite database file
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_pool = ConnectionPool(db_path)
        self.active_transactions = {}
        self._lock = threading.Lock()

    @log_function_call(logger)
    def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation with automatic retry on failure.

        Args:
            operation: Function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            TransactionError: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (sqlite3.Error, TransactionError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}"
                    )
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries + 1} attempts: {str(e)}"
                    )

        raise TransactionError(
            f"Operation failed after {self.max_retries + 1} attempts: {str(last_exception)}"
        )

    @contextmanager
    def transaction(self, transaction_id: str = None):
        """
        Context manager for database transactions.

        Args:
            transaction_id: Optional transaction identifier

        Yields:
            Transaction object

        Raises:
            TransactionError: If transaction fails
        """
        transaction = None
        conn = None

        try:
            # Get connection from pool
            conn = self.connection_pool.get_connection()

            # Create transaction
            transaction = Transaction(conn, transaction_id)
            transaction.begin()

            # Register active transaction
            with self._lock:
                self.active_transactions[transaction.transaction_id] = transaction

            yield transaction

            # Commit transaction
            transaction.commit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Rollback transaction
            if transaction:
                try:
                    transaction.rollback()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as rollback_error:
                    logger.error(
                        f"Failed to rollback transaction {transaction.transaction_id}: {str(rollback_error)}"
                    )

            # Log transaction failure
            if transaction:
                logger.error("Transaction %s failed: {str(e)}", transaction.transaction_id)

            raise TransactionError(f"Transaction failed: {str(e)}")

        finally:
            # Unregister transaction
            if transaction:
                with self._lock:
                    self.active_transactions.pop(transaction.transaction_id, None)

            # Return connection to pool
            if conn:
                self.connection_pool.return_connection(conn)

    def execute_transaction(
        self, operations: List[Dict[str, Any]], transaction_id: str = None
    ) -> List[Any]:
        """
        Execute multiple operations in a single transaction.

        Args:
            operations: List of operation dictionaries with 'function' and 'args' keys
            transaction_id: Optional transaction identifier

        Returns:
            List of operation results

        Raises:
            TransactionError: If transaction fails
        """
        results = []

        with self.transaction(transaction_id) as transaction:
            for op in operations:
                try:
                    func = op["function"]
                    args = op.get("args", ())
                    kwargs = op.get("kwargs", {})

                    # Add operation to transaction log
                    transaction.add_operation(func.__name__, args)

                    # Execute operation
                    result = func(*args, **kwargs)
                    results.append(result)

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error(
                        f"Operation {op} failed in transaction {transaction.transaction_id}: {str(e)}"
                    )
                    raise TransactionError(f"Operation failed: {str(e)}")

        return results

    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific transaction.

        Args:
            transaction_id: Transaction identifier

        Returns:
            Transaction status dictionary or None if not found
        """
        with self._lock:
            transaction = self.active_transactions.get(transaction_id)
            if transaction:
                return {
                    "transaction_id": transaction.transaction_id,
                    "state": transaction.state.value,
                    "start_time": transaction.start_time,
                    "duration": transaction.get_duration(),
                    "operations_count": len(transaction.operations),
                }
        return None

    def get_all_transaction_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all active transactions.

        Returns:
            List of transaction status dictionaries
        """
        with self._lock:
            return [
                {
                    "transaction_id": tid,
                    "state": tx.state.value,
                    "start_time": tx.start_time,
                    "duration": tx.get_duration(),
                    "operations_count": len(tx.operations),
                }
                for tid, tx in self.active_transactions.items()
            ]

    def cleanup_stale_transactions(self, max_age: float = 3600.0) -> int:
        """
        Clean up stale transactions.

        Args:
            max_age: Maximum age of transaction in seconds

        Returns:
            Number of transactions cleaned up
        """
        current_time = time.time()
        cleaned_count = 0

        with self._lock:
            stale_transactions = []

            for tid, transaction in self.active_transactions.items():
                if current_time - transaction.start_time > max_age:
                    stale_transactions.append(tid)

            for tid in stale_transactions:
                transaction = self.active_transactions.pop(tid, None)
                if transaction:
                    try:
                        transaction.rollback()
                        cleaned_count += 1
                        logger.warning("Cleaned up stale transaction %s", tid)
                    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                        logger.error("Failed to cleanup stale transaction %s: {str(e)}", tid)

        return cleaned_count

    def close(self) -> None:
        """Close the transaction manager and all connections."""
        # Rollback all active transactions
        with self._lock:
            for transaction in list(self.active_transactions.values()):
                try:
                    transaction.rollback()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Failed to rollback transaction during cleanup: %s", str(e))
            self.active_transactions.clear()

        # Close connection pool
        self.connection_pool.close_all()
        logger.info("Transaction manager closed")


def transactional(max_retries: int = 3, retry_delay: float = 0.1):
    """
    Decorator for automatic transaction management.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would need to be integrated with the transaction manager
            # For now, just execute the function with basic error handling
            try:
                return func(*args, **kwargs)
            except sqlite3.Error as e:
                logger.error("Database error in %s: {str(e)}", func.__name__)
                raise DatabaseError(f"Database operation failed: {str(e)}")

        return wrapper

    return decorator


class DatabaseHealthMonitor:
    """Monitor database health and performance."""

    def __init__(self, connection_pool: ConnectionPool):
        """
        Initialize health monitor.

        Args:
            connection_pool: Connection pool to monitor
        """
        self.connection_pool = connection_pool
        self._metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time": 0.0,
            "connection_pool_size": 0,
            "active_connections": 0,
        }
        self._lock = threading.Lock()

    def record_operation(self, success: bool, response_time: float) -> None:
        """
        Record operation metrics.

        Args:
            success: Whether operation was successful
            response_time: Operation response time in seconds
        """
        with self._lock:
            self._metrics["total_operations"] += 1

            if success:
                self._metrics["successful_operations"] += 1
            else:
                self._metrics["failed_operations"] += 1

            # Update average response time
            total_ops = self._metrics["total_operations"]
            current_avg = self._metrics["average_response_time"]
            self._metrics["average_response_time"] = (
                current_avg * (total_ops - 1) + response_time
            ) / total_ops

            # Update connection metrics
            self._metrics["connection_pool_size"] = len(self.connection_pool._pool)
            self._metrics["active_connections"] = self.connection_pool._active_connections

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current database health status.

        Returns:
            Health status dictionary
        """
        with self._lock:
            metrics = self._metrics.copy()

            # Calculate success rate
            if metrics["total_operations"] > 0:
                metrics["success_rate"] = (
                    metrics["successful_operations"] / metrics["total_operations"]
                )
            else:
                metrics["success_rate"] = 0.0

            # Determine health status
            if metrics["success_rate"] >= 0.95 and metrics["average_response_time"] < 1.0:
                status = "healthy"
            elif metrics["success_rate"] >= 0.80:
                status = "degraded"
            else:
                status = "unhealthy"

            metrics["status"] = status
            return metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "average_response_time": 0.0,
                "connection_pool_size": 0,
                "active_connections": 0,
            }
