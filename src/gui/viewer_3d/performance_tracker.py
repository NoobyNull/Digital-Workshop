"""
Performance tracking for 3D viewer.

Monitors FPS and performance metrics.
"""

import time
from typing import Callable, Optional

from PySide6.QtCore import QTimer

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class PerformanceTracker:
    """Tracks performance metrics like FPS."""

    def __init__(self, update_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize performance tracker.

        Args:
            update_callback: Optional callback for performance updates
        """
        self.update_callback = update_callback
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance)

    def start(self) -> None:
        """Start performance monitoring."""
        self.performance_timer.start(1000)  # Update every second
        logger.debug("Performance monitoring started")

    def stop(self) -> None:
        """Stop performance monitoring."""
        try:
            if hasattr(self, "performance_timer") and self.performance_timer:
                self.performance_timer.stop()
                logger.debug("Performance monitoring stopped")
        except (RuntimeError, AttributeError) as e:
            # Timer may already be deleted
            logger.debug("Performance monitoring stop failed (timer deleted): %s", e)

    def frame_rendered(self) -> None:
        """Call this when a frame is rendered."""
        self.frame_count += 1

    def _update_performance(self) -> None:
        """Update performance metrics."""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed > 0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time

            if self.update_callback:
                try:
                    self.update_callback(self.current_fps)
                except RuntimeError as e:
                    # Widget has been deleted, stop the timer
                    if "already deleted" in str(e):
                        logger.debug(
                            "Performance tracker callback failed - widget deleted, stopping timer"
                        )
                        self.stop()
                    else:
                        logger.warning("Performance tracker callback failed: %s", e)

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, "performance_timer") and self.performance_timer:
                self.stop()
                # Disconnect the signal to prevent callbacks after cleanup
                try:
                    self.performance_timer.timeout.disconnect(self._update_performance)
                except (TypeError, RuntimeError):
                    # Signal may already be disconnected or timer deleted
                    pass
        except Exception as e:
            logger.debug("Error during performance tracker cleanup: %s", e)
