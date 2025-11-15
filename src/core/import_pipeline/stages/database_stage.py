"""
Database insertion stage for the import pipeline.

Handles inserting model data into the database.
"""

import time
from typing import Optional
from PySide6.QtCore import QThreadPool

from src.core.import_pipeline.stages.base_stage import BaseStage
from src.core.import_pipeline.pipeline_models import (
    ImportTask,
    StageResult,
    ImportStage,
    ImportStatus,
)
from src.core.database_manager import DatabaseManager


class DatabaseStage(BaseStage):
    """
    Stage that inserts model data into the database.

    This stage:
    1. Checks if model already exists (resume detection)
    2. Inserts model, metadata, and analysis data
    3. Updates task with model_id
    """

    def __init__(self, db_manager: DatabaseManager, thread_pool: Optional[QThreadPool] = None):
        """
        Initialize the database stage.

        Args:
            db_manager: Database manager instance
            thread_pool: Optional thread pool for async operations
        """
        super().__init__(thread_pool)
        self.db_manager = db_manager

    @property
    def stage_name(self) -> ImportStage:
        """Return the stage identifier."""
        return ImportStage.DATABASE_INSERT

    def should_process(self, task: ImportTask) -> bool:
        """
        Check if model already exists in database.

        Args:
            task: The import task to check

        Returns:
            True if model needs to be inserted, False if already exists
        """
        # If task already has a model_id, it's been processed
        if task.model_id is not None:
            return False

        # Check if model exists in database by file path
        try:
            existing_model = self.db_manager.get_model_by_path(task.file_path)
            if existing_model:
                # Model exists - update task with existing ID
                task.model_id = existing_model.get("id")
                self.logger.info(
                    "Model %s already exists in database (ID: %d)",
                    task.filename,
                    task.model_id,
                )
                return False
        except Exception as e:
            self.logger.warning("Error checking for existing model %s: %s", task.filename, e)

        return True

    def process(self, task: ImportTask) -> StageResult:
        """
        Insert model data into database.

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """
        start_time = time.time()

        try:
            # Update task status
            task.current_stage = ImportStage.DATABASE_INSERT
            task.status = ImportStatus.IN_PROGRESS

            # Insert model
            model_id = self.db_manager.add_model(
                filename=task.filename,
                format=task.format,
                file_path=task.file_path,
                file_size=task.file_size,
                file_hash=task.file_hash,  # May be None at this stage
            )

            # Insert metadata
            self.db_manager.add_model_metadata(
                model_id=model_id,
                title=task.filename,
                description="",
            )

            # Insert analysis data
            self.db_manager.add_model_analysis(
                model_id=model_id,
                triangle_count=task.triangle_count,
                vertex_count=task.vertex_count,
                min_bounds=task.min_bounds,
                max_bounds=task.max_bounds,
                analysis_time_seconds=task.parsing_time,
            )

            # Update task with model_id
            task.model_id = model_id
            task.status = ImportStatus.COMPLETED

            duration = time.time() - start_time

            self.logger.info(
                "Inserted model %s into database (ID: %d) in %.2fs",
                task.filename,
                model_id,
                duration,
            )

            return StageResult(
                stage=self.stage_name,
                success=True,
                task=task,
                duration_seconds=duration,
                metadata={"model_id": model_id},
            )

        except Exception as e:
            error_msg = f"Database insertion failed: {e}"
            task.status = ImportStatus.FAILED
            task.failed_stage = ImportStage.DATABASE_INSERT
            task.error_message = error_msg

            duration = time.time() - start_time

            self.logger.error(
                "Failed to insert model %s: %s", task.filename, error_msg, exc_info=True
            )

            return StageResult(
                stage=self.stage_name,
                success=False,
                task=task,
                error_message=error_msg,
                duration_seconds=duration,
            )
