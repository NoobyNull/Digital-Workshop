"""
Data models for the import pipeline.

Defines the data structures used throughout the import pipeline stages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime


class ImportStage(Enum):
    """Stages of the import pipeline."""

    PENDING = "pending"
    DATABASE_INSERT = "database_insert"
    IMAGE_PAIRING = "image_pairing"
    HASHING = "hashing"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    COMPLETE = "complete"
    FAILED = "failed"


class ImportStatus(Enum):
    """Status of an import task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ImportTask:
    """
    Represents a single model import task.

    This is the core data structure that flows through the pipeline stages.
    Each stage adds its results to this task.
    """

    # File information
    file_path: str
    filename: str
    format: str
    file_size: int

    # Model information (from parsing)
    triangle_count: Optional[int] = None
    vertex_count: Optional[int] = None
    min_bounds: Optional[tuple] = None
    max_bounds: Optional[tuple] = None
    parsing_time: Optional[float] = None

    # Pipeline tracking
    current_stage: ImportStage = ImportStage.PENDING
    status: ImportStatus = ImportStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    # Stage results
    model_id: Optional[int] = None  # From database stage
    file_hash: Optional[str] = None  # From hashing stage
    paired_image_path: Optional[str] = None  # From image pairing stage
    thumbnail_path: Optional[str] = None  # From thumbnail stage

    # Error tracking
    error_message: Optional[str] = None
    failed_stage: Optional[ImportStage] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "format": self.format,
            "file_size": self.file_size,
            "triangle_count": self.triangle_count,
            "vertex_count": self.vertex_count,
            "min_bounds": self.min_bounds,
            "max_bounds": self.max_bounds,
            "parsing_time": self.parsing_time,
            "current_stage": self.current_stage.value,
            "status": self.status.value,
            "model_id": self.model_id,
            "file_hash": self.file_hash,
            "paired_image_path": self.paired_image_path,
            "thumbnail_path": self.thumbnail_path,
            "error_message": self.error_message,
            "failed_stage": self.failed_stage.value if self.failed_stage else None,
            "metadata": self.metadata,
        }


@dataclass
class StageResult:
    """Result from a pipeline stage execution."""

    stage: ImportStage
    success: bool
    task: ImportTask
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineProgress:
    """Progress information for the entire pipeline."""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    current_stage_counts: Dict[ImportStage, int] = field(default_factory=dict)

    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100.0

    @property
    def in_progress_tasks(self) -> int:
        """Calculate number of tasks in progress."""
        return self.total_tasks - self.completed_tasks - self.failed_tasks


@dataclass
class PipelineResult:
    """Final result of the import pipeline."""

    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    skipped_tasks: int
    total_duration_seconds: float
    failed_task_details: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100.0
