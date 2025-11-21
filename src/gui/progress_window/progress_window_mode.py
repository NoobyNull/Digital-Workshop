"""
Progress Window Mode and Data Structures.

This module defines the operation modes and supporting data structures
for the UnifiedProgressWindow system.

The UnifiedProgressWindow adapts its UI based on the operation mode:
- IMPORT: Shows all import stages (validation, hashing, copying, thumbnails, analysis)
- THUMBNAIL_ONLY: Shows only thumbnail generation with prominent VTK preview
- ANALYSIS_ONLY: Shows only analysis stage (future)
- REGENERATE: Shows regeneration of existing items (future)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict
import time


class ProgressWindowMode(Enum):
    """Operation modes for the unified progress window."""

    IMPORT = "import"
    THUMBNAIL_ONLY = "thumbnail"
    ANALYSIS_ONLY = "analysis"
    REGENERATE = "regenerate"


class StageStatus(Enum):
    """Status of a progress stage."""

    WAITING = "waiting"  # ⏳
    IN_PROGRESS = "in_progress"  # ⚙
    COMPLETED = "completed"  # ✓
    FAILED = "failed"  # ✗
    PAUSED = "paused"  # ⏸
    CANCELLED = "cancelled"  # ✗


@dataclass
class StageProgress:
    """Progress information for a single stage."""

    name: str
    status: StageStatus = StageStatus.WAITING
    progress_percent: int = 0
    current_item: str = ""
    message: str = ""
    items_completed: int = 0
    items_total: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def get_elapsed_time(self) -> float:
        """Get elapsed time for this stage in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def get_status_icon(self) -> str:
        """Get the status icon for this stage."""
        icons = {
            StageStatus.WAITING: "⏳",
            StageStatus.IN_PROGRESS: "⚙",
            StageStatus.COMPLETED: "✓",
            StageStatus.FAILED: "✗",
            StageStatus.PAUSED: "⏸",
            StageStatus.CANCELLED: "✗",
        }
        return icons.get(self.status, "")


@dataclass
class ThumbnailProgress:
    """Progress information for thumbnail generation."""

    current_index: int = 0
    total_count: int = 0
    current_file: str = ""
    individual_percent: int = 0
    individual_stage: str = ""
    batch_percent: int = 0
    completed_count: int = 0
    failed_count: int = 0
    errors: Dict[str, str] = field(default_factory=dict)

    def get_batch_progress_text(self) -> str:
        """Get formatted batch progress text."""
        return f"{self.completed_count} of {self.total_count} ({self.batch_percent}%)"

    def get_individual_progress_text(self) -> str:
        """Get formatted individual progress text."""
        return f"{self.individual_percent}% - {self.individual_stage}"


@dataclass
class OverallProgress:
    """Overall progress information across all stages."""

    mode: ProgressWindowMode
    total_items: int
    current_item_index: int = 0
    overall_percent: int = 0
    current_stage: str = ""
    elapsed_time: float = 0.0
    estimated_remaining_time: float = 0.0
    items_completed: int = 0
    items_failed: int = 0
    items_skipped: int = 0
    is_paused: bool = False
    is_cancelled: bool = False

    def get_elapsed_time_formatted(self) -> str:
        """Get formatted elapsed time (e.g., '2m 15s')."""
        return self._format_time(self.elapsed_time)

    def get_remaining_time_formatted(self) -> str:
        """Get formatted remaining time (e.g., '3m 10s')."""
        return self._format_time(self.estimated_remaining_time)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in seconds to human-readable string."""
        if seconds < 0:
            return "Unknown"
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m"

    def calculate_remaining_time(self) -> None:
        """Calculate estimated remaining time based on current progress."""
        if self.items_completed > 0 and self.elapsed_time > 0:
            avg_time_per_item = self.elapsed_time / self.items_completed
            remaining_items = self.total_items - self.items_completed
            self.estimated_remaining_time = avg_time_per_item * remaining_items
        else:
            self.estimated_remaining_time = 0.0


@dataclass
class StageConfiguration:
    """Configuration for which stages are visible in each mode."""

    show_validation: bool = False
    show_hashing: bool = False
    show_copying: bool = False
    show_thumbnails: bool = False
    show_analysis: bool = False
    vtk_preview_height: int = 300
    window_title_prefix: str = "Progress"

    @staticmethod
    def for_mode(mode: ProgressWindowMode, total_items: int) -> "StageConfiguration":
        """Get stage configuration for a specific mode."""
        if mode == ProgressWindowMode.IMPORT:
            return StageConfiguration(
                show_validation=True,
                show_hashing=True,
                show_copying=True,
                show_thumbnails=True,
                show_analysis=True,
                vtk_preview_height=300,
                window_title_prefix=f"Import Progress - {total_items} Files",
            )
        elif mode == ProgressWindowMode.THUMBNAIL_ONLY:
            return StageConfiguration(
                show_validation=False,
                show_hashing=False,
                show_copying=False,
                show_thumbnails=True,
                show_analysis=False,
                vtk_preview_height=500,
                window_title_prefix=f"Thumbnail Generation - {total_items} Models",
            )
        elif mode == ProgressWindowMode.ANALYSIS_ONLY:
            return StageConfiguration(
                show_validation=False,
                show_hashing=False,
                show_copying=False,
                show_thumbnails=False,
                show_analysis=True,
                vtk_preview_height=0,
                window_title_prefix=f"Analysis - {total_items} Models",
            )
        else:  # REGENERATE or unknown
            return StageConfiguration(
                show_validation=False,
                show_hashing=False,
                show_copying=False,
                show_thumbnails=True,
                show_analysis=False,
                vtk_preview_height=400,
                window_title_prefix=f"Regenerate - {total_items} Items",
            )


@dataclass
class ProgressWeights:
    """Weight configuration for calculating overall progress in IMPORT mode."""

    validation_weight: int = 10  # 0-10%
    hashing_weight: int = 20  # 10-30%
    copying_weight: int = 20  # 30-50%
    thumbnail_weight: int = 30  # 50-80%
    analysis_weight: int = 20  # 80-100%

    def calculate_overall_progress(
        self, current_stage: str, stage_progress: int
    ) -> int:
        """
        Calculate overall progress percentage based on current stage and progress.

        Args:
            current_stage: Name of current stage
            stage_progress: Progress within current stage (0-100)

        Returns:
            Overall progress percentage (0-100)
        """
        stage_map = {
            "validation": 0,
            "hashing": self.validation_weight,
            "copying": self.validation_weight + self.hashing_weight,
            "thumbnails": self.validation_weight
            + self.hashing_weight
            + self.copying_weight,
            "analysis": self.validation_weight
            + self.hashing_weight
            + self.copying_weight
            + self.thumbnail_weight,
        }

        base_progress = stage_map.get(current_stage.lower(), 0)

        weight_map = {
            "validation": self.validation_weight,
            "hashing": self.hashing_weight,
            "copying": self.copying_weight,
            "thumbnails": self.thumbnail_weight,
            "analysis": self.analysis_weight,
        }

        current_weight = weight_map.get(current_stage.lower(), 0)
        stage_contribution = (stage_progress / 100.0) * current_weight

        return min(100, int(base_progress + stage_contribution))
