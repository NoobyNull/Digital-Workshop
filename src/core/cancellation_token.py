"""
Thread-safe cancellation token for background operations.

This module provides a mechanism for cancelling long-running operations
in a thread-safe manner, with support for cleanup callbacks.
"""

import threading
from typing import Callable, List
from src.core.logging_config import get_logger, log_function_call


class CancellationToken:
    """
    Thread-safe cancellation token for background operations.

    This class provides a way to signal cancellation across threads and
    execute cleanup callbacks when cancellation is requested.
    """

    def __init__(self) -> None:
        """Initialize the cancellation token."""
        self._cancelled = False
        self._lock = threading.RLock()
        self._cleanup_callbacks: List[Callable[[], None]] = []
        self.logger = get_logger(__name__)

    def __getstate__(self) -> None:
        """Support for pickling - exclude non-serializable objects."""
        state = self.__dict__.copy()
        # Remove the lock and logger as they can't be pickled
        state.pop("_lock", None)
        state.pop("logger", None)
        return state

    def __setstate__(self, state) -> None:
        """Support for unpickling - restore non-serializable objects."""
        self.__dict__.update(state)
        # Recreate the lock and logger
        self._lock = threading.RLock()
        self.logger = get_logger(__name__)

    @log_function_call
    def cancel(self) -> None:
        """
        Cancel the operation and run cleanup callbacks.

        This method is thread-safe and can be called multiple times.
        Cleanup callbacks are executed in the order they were registered.
        """
        with self._lock:
            if self._cancelled:
                return  # Already cancelled

            self._cancelled = True
            self.logger.debug("Cancellation requested, executing cleanup callbacks")

            # Execute cleanup callbacks
            callbacks_to_run = self._cleanup_callbacks.copy()

        # Run callbacks outside the lock to avoid deadlocks
        for callback in callbacks_to_run:
            try:
                callback()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.warning("Cleanup callback failed: %s", e)

        self.logger.debug("Cancellation completed")

    @log_function_call
    def is_cancelled(self) -> bool:
        """
        Check if the operation has been cancelled.

        Returns:
            True if cancelled, False otherwise
        """
        with self._lock:
            return self._cancelled

    @log_function_call
    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to run when cancellation is requested.

        Args:
            callback: Function to call during cancellation

        Note:
            Callbacks should be quick to execute to avoid blocking
            the cancellation process.
        """
        with self._lock:
            if self._cancelled:
                # If already cancelled, run callback immediately
                try:
                    callback()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.warning("Immediate cleanup callback failed: %s", e)
            else:
                self._cleanup_callbacks.append(callback)

    @log_function_call
    def unregister_cleanup_callback(self, callback: Callable[[], None]) -> bool:
        """
        Unregister a cleanup callback.

        Args:
            callback: The callback to remove

        Returns:
            True if callback was found and removed, False otherwise
        """
        with self._lock:
            try:
                self._cleanup_callbacks.remove(callback)
                return True
            except ValueError:
                return False

    def __bool__(self) -> bool:
        """Allow using token in boolean context (e.g., if token: ...)"""
        return self.is_cancelled()

    def __str__(self) -> str:
        """String representation of the token."""
        return f"CancellationToken(cancelled={self._cancelled})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"CancellationToken(cancelled={self._cancelled}, callbacks={len(self._cleanup_callbacks)})"
