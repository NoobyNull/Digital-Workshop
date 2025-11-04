"""
Detailed progress tracker for model loading with stage-based progress calculation.

Provides precise progress percentage based on:
- File I/O time
- Parsing time
- Triangle count
- Rendering time
"""

from enum import Enum
from typing import Optional, Callable
import time


class LoadingStage(Enum):
    """Stages of model loading process."""

    IDLE = "idle"
    METADATA = "metadata"
    IO_READ = "io_read"
    PARSING = "parsing"
    RENDERING = "rendering"
    COMPLETE = "complete"


class DetailedProgressTracker:
    """Tracks detailed progress through model loading stages."""

    def __init__(self, triangle_count: int = 0, file_size_mb: float = 0.0):
        """
        Initialize progress tracker.

        Args:
            triangle_count: Number of triangles in model
            file_size_mb: File size in MB
        """
        self.triangle_count = triangle_count
        self.file_size_mb = file_size_mb
        self.current_stage = LoadingStage.IDLE
        self.stage_start_time = time.time()
        self.overall_start_time = time.time()

        # Stage progress ranges (percentage)
        self.stage_ranges = {
            LoadingStage.METADATA: (0, 5),
            LoadingStage.IO_READ: (5, 25),
            LoadingStage.PARSING: (25, 85),
            LoadingStage.RENDERING: (85, 100),
        }

        # Estimated times (in seconds) based on typical performance
        self.estimated_times = {
            LoadingStage.METADATA: 0.1,
            LoadingStage.IO_READ: self._estimate_io_time(),
            LoadingStage.PARSING: self._estimate_parse_time(),
            LoadingStage.RENDERING: self._estimate_render_time(),
        }

        self.progress_callback: Optional[Callable[[float, str], None]] = None

    def _estimate_io_time(self) -> float:
        """Estimate I/O time based on file size."""
        # Assume ~2500 MB/s read speed
        if self.file_size_mb > 0:
            return self.file_size_mb / 2500.0
        return 0.2

    def _estimate_parse_time(self) -> float:
        """Estimate parsing time based on triangle count."""
        # Assume ~7M triangles/second parsing speed
        if self.triangle_count > 0:
            return self.triangle_count / 7_000_000.0
        return 1.0

    def _estimate_render_time(self) -> float:
        """Estimate rendering time based on triangle count."""
        # Assume ~1M triangles/second rendering speed
        if self.triangle_count > 0:
            return self.triangle_count / 1_000_000.0
        return 2.0

    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """Set callback for progress updates."""
        self.progress_callback = callback

    def start_stage(self, stage: LoadingStage, message: str = "") -> None:
        """Start a new loading stage."""
        self.current_stage = stage
        self.stage_start_time = time.time()

        stage_range = self.stage_ranges.get(stage, (0, 100))
        progress = stage_range[0]

        if not message:
            message = f"Starting {stage.value}..."

        self._emit_progress(progress, message)

    def update_stage_progress(
        self, current: int, total: int, message: str = ""
    ) -> None:
        """
        Update progress within current stage.

        Args:
            current: Current item count
            total: Total items
            message: Progress message
        """
        if total == 0:
            return

        stage_range = self.stage_ranges.get(self.current_stage, (0, 100))
        stage_start, stage_end = stage_range
        stage_width = stage_end - stage_start

        # Calculate progress within stage
        stage_progress = (current / total) * stage_width
        overall_progress = stage_start + stage_progress

        if not message:
            message = f"{self.current_stage.value}: {current:,}/{total:,}"

        self._emit_progress(overall_progress, message)

    def complete_stage(self, message: str = "") -> None:
        """Complete current stage and move to next."""
        stage_range = self.stage_ranges.get(self.current_stage, (0, 100))
        progress = stage_range[1]

        if not message:
            elapsed = time.time() - self.stage_start_time
            message = f"{self.current_stage.value} completed in {elapsed:.2f}s"

        self._emit_progress(progress, message)

    def _emit_progress(self, progress: float, message: str) -> None:
        """Emit progress update."""
        progress = max(0.0, min(100.0, progress))
        if self.progress_callback:
            self.progress_callback(progress, message)

    def get_estimated_total_time(self) -> float:
        """Get estimated total loading time in seconds."""
        return sum(self.estimated_times.values())

    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.overall_start_time
