"""
Modular import pipeline system.

This package provides a complete, modular import pipeline for processing
model files through multiple stages: database insertion, image pairing,
file hashing, and thumbnail generation.

Architecture:
- Each stage is a separate, focused module
- Stages implement the BaseStage interface
- Workers handle async operations
- Coordinator orchestrates stage execution
- Resume detector enables interrupted import recovery

Usage:
    from src.core.import_pipeline import create_pipeline, ImportTask

    # Create pipeline
    pipeline = create_pipeline(db_manager, thumbnail_generator)

    # Create tasks
    tasks = [ImportTask(file_path="model.stl", ...)]

    # Execute
    pipeline.execute(tasks)
"""

from src.core.import_pipeline.pipeline_models import (
    ImportTask,
    ImportStage,
    ImportStatus,
    StageResult,
    PipelineProgress,
    PipelineResult,
)
from src.core.import_pipeline.pipeline_coordinator import PipelineCoordinator
from src.core.import_pipeline.resume_detector import ResumeDetector
from src.core.import_pipeline.signals import (
    PipelineSignals,
    StageSignals,
    WorkerSignals,
)

# Stage imports
from src.core.import_pipeline.stages.database_stage import DatabaseStage
from src.core.import_pipeline.stages.hashing_stage import HashingStage
from src.core.import_pipeline.stages.image_pairing_stage import ImagePairingStage
from src.core.import_pipeline.stages.thumbnail_stage import ThumbnailStage


def create_pipeline(
    db_manager,
    thumbnail_generator,
    thread_pool=None,
    max_workers: int | None = None,
) -> PipelineCoordinator:
    """
    Factory function to create a complete import pipeline.

    Args:
        db_manager: DatabaseManager instance
        thumbnail_generator: ThumbnailGenerator instance
        thread_pool: Optional QThreadPool for async operations
        max_workers: Maximum number of tasks processed in parallel

    Returns:
        Configured PipelineCoordinator ready to execute
    """
    # Create stages in execution order
    stages = [
        DatabaseStage(db_manager, thread_pool),
        HashingStage(db_manager, thread_pool),
        ImagePairingStage(db_manager, thread_pool=thread_pool),
        ThumbnailStage(thumbnail_generator, thread_pool),
    ]

    # Create resume detector
    resume_detector = ResumeDetector(db_manager)

    # Create and return coordinator
    return PipelineCoordinator(
        stages=stages,
        resume_detector=resume_detector,
        thread_pool=thread_pool,
        max_workers=max_workers or 1,
    )


__all__ = [
    # Models
    "ImportTask",
    "ImportStage",
    "ImportStatus",
    "StageResult",
    "PipelineProgress",
    "PipelineResult",
    # Coordinator
    "PipelineCoordinator",
    "ResumeDetector",
    # Signals
    "PipelineSignals",
    "StageSignals",
    "WorkerSignals",
    # Stages
    "DatabaseStage",
    "HashingStage",
    "ImagePairingStage",
    "ThumbnailStage",
    # Factory
    "create_pipeline",
]
