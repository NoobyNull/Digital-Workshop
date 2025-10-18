"""
Performance tracking for 3D viewer.

Monitors FPS and performance metrics.
"""

import time
from typing import Callable, Optional

from PySide6.QtCore import QTimer

from src.core.logging_config import get_logger, log_function_call


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
        self.performance_timer.stop()
        logger.debug("Performance monitoring stopped")

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
                self.update_callback(self.current_fps)

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()

