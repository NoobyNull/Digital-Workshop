"""
Progress update throttler for model library operations.

Prevents UI from being overwhelmed by too many progress updates.
"""

import time
from typing import Callable, Optional

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ProgressThrottler:
    """
    Throttles progress updates to prevent UI overload.
    
    Only allows progress updates at a specified minimum interval,
    but always allows the first and last updates through.
    """
    
    def __init__(self, min_interval_ms: float = 100.0):
        """
        Initialize the progress throttler.
        
        Args:
            min_interval_ms: Minimum time between updates in milliseconds (default: 100ms)
        """
        self.min_interval_ms = min_interval_ms
        self.min_interval_sec = min_interval_ms / 1000.0
        self.last_update_time: Optional[float] = None
        self.pending_update: Optional[tuple] = None
        self.logger = get_logger(__name__)
        
        # Statistics
        self.total_updates = 0
        self.throttled_updates = 0
        self.emitted_updates = 0
    
    def should_update(self) -> bool:
        """
        Check if enough time has passed to allow an update.
        
        Returns:
            True if update should be allowed, False if throttled
        """
        current_time = time.time()
        
        # Always allow first update
        if self.last_update_time is None:
            self.last_update_time = current_time
            return True
        
        # Check if enough time has passed
        elapsed = current_time - self.last_update_time
        if elapsed >= self.min_interval_sec:
            self.last_update_time = current_time
            return True
        
        return False
    
    def update(
        self,
        callback: Callable,
        *args,
        force: bool = False,
        **kwargs
    ) -> bool:
        """
        Attempt to call the update callback with throttling.
        
        Args:
            callback: Function to call for the update
            *args: Positional arguments for the callback
            force: If True, bypass throttling and always update
            **kwargs: Keyword arguments for the callback
            
        Returns:
            True if update was emitted, False if throttled
        """
        self.total_updates += 1
        
        # Force update (e.g., for first/last updates)
        if force:
            callback(*args, **kwargs)
            self.emitted_updates += 1
            self.last_update_time = time.time()
            return True
        
        # Check throttling
        if self.should_update():
            callback(*args, **kwargs)
            self.emitted_updates += 1
            return True
        else:
            # Store pending update (will be lost if another comes before interval)
            self.pending_update = (callback, args, kwargs)
            self.throttled_updates += 1
            return False
    
    def flush_pending(self) -> bool:
        """
        Emit any pending update that was throttled.
        
        Returns:
            True if a pending update was emitted, False otherwise
        """
        if self.pending_update is not None:
            callback, args, kwargs = self.pending_update
            callback(*args, **kwargs)
            self.pending_update = None
            self.emitted_updates += 1
            self.last_update_time = time.time()
            return True
        return False
    
    def reset(self) -> None:
        """Reset the throttler state."""
        self.last_update_time = None
        self.pending_update = None
    
    def get_stats(self) -> dict:
        """
        Get throttling statistics.
        
        Returns:
            Dictionary with throttling statistics
        """
        return {
            "total_updates": self.total_updates,
            "emitted_updates": self.emitted_updates,
            "throttled_updates": self.throttled_updates,
            "throttle_rate": (
                self.throttled_updates / self.total_updates
                if self.total_updates > 0
                else 0.0
            ),
        }
    
    def log_stats(self) -> None:
        """Log throttling statistics."""
        stats = self.get_stats()
        self.logger.info(
            "Progress throttler stats: %d total, %d emitted, %d throttled (%.1f%% throttled)",
            stats["total_updates"],
            stats["emitted_updates"],
            stats["throttled_updates"],
            stats["throttle_rate"] * 100,
        )


class BatchProgressTracker:
    """
    Tracks progress for batch operations with throttling.
    
    Combines progress tracking with throttled updates to prevent UI overload.
    """
    
    def __init__(
        self,
        total_items: int,
        progress_callback: Optional[Callable] = None,
        throttle_ms: float = 100.0,
    ):
        """
        Initialize the batch progress tracker.
        
        Args:
            total_items: Total number of items to process
            progress_callback: Optional callback for progress updates (current, total, message)
            throttle_ms: Throttle interval in milliseconds
        """
        self.total_items = total_items
        self.completed_items = 0
        self.failed_items = 0
        self.progress_callback = progress_callback
        self.throttler = ProgressThrottler(min_interval_ms=throttle_ms)
        self.logger = get_logger(__name__)
    
    def increment(self, message: str = "", force: bool = False) -> None:
        """
        Increment the progress counter and emit update if not throttled.
        
        Args:
            message: Optional progress message
            force: If True, bypass throttling
        """
        self.completed_items += 1
        
        if self.progress_callback:
            self.throttler.update(
                self.progress_callback,
                self.completed_items,
                self.total_items,
                message,
                force=force,
            )
    
    def increment_failed(self, message: str = "") -> None:
        """
        Increment the failed counter.
        
        Args:
            message: Optional error message
        """
        self.failed_items += 1
        self.completed_items += 1
        
        if self.progress_callback:
            self.throttler.update(
                self.progress_callback,
                self.completed_items,
                self.total_items,
                f"Failed: {message}",
                force=False,
            )
    
    def finish(self, message: str = "Complete") -> None:
        """
        Mark the batch as finished and emit final update.
        
        Args:
            message: Completion message
        """
        # Flush any pending update
        self.throttler.flush_pending()
        
        # Emit final update
        if self.progress_callback:
            self.progress_callback(self.total_items, self.total_items, message)
        
        # Log statistics
        self.throttler.log_stats()
        self.logger.info(
            "Batch complete: %d/%d succeeded, %d failed",
            self.completed_items - self.failed_items,
            self.total_items,
            self.failed_items,
        )
    
    def get_progress_percent(self) -> float:
        """
        Get current progress as a percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.total_items == 0:
            return 100.0
        return (self.completed_items / self.total_items) * 100.0

