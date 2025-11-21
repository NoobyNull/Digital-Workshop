"""
File hashing stage for the import pipeline.

Handles calculating file hashes for integrity verification.
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
from src.utils.file_hash import calculate_file_hash


class HashingStage(BaseStage):
    """
    Stage that calculates file hashes.

    This stage:
    1. Checks if hash already exists (resume detection)
    2. Calculates xxHash128 of the file
    3. Updates database with hash
    4. Updates task with file_hash
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        thread_pool: Optional[QThreadPool] = None,
    ):
        """
        Initialize the hashing stage.

        Args:
            db_manager: Database manager instance
            thread_pool: Optional thread pool for async operations
        """
        super().__init__(thread_pool)
        self.db_manager = db_manager

    @property
    def stage_name(self) -> ImportStage:
        """Return the stage identifier."""
        return ImportStage.HASHING

    def should_process(self, task: ImportTask) -> bool:
        """
        Check if file hash already exists.

        Args:
            task: The import task to check

        Returns:
            True if hash needs to be calculated, False if already exists
        """
        # If task already has a hash, it's been processed
        if task.file_hash is not None:
            return False

        # Check if model has hash in database
        if task.model_id:
            try:
                model = self.db_manager.get_model_by_id(task.model_id)
                if model and model.get("file_hash"):
                    task.file_hash = model["file_hash"]
                    self.logger.info(
                        "Model %s already has hash: %s",
                        task.filename,
                        task.file_hash[:16],
                    )
                    return False
            except Exception as e:
                self.logger.warning(
                    "Error checking for existing hash for %s: %s", task.filename, e
                )

        return True

    def process(self, task: ImportTask) -> StageResult:
        """
        Calculate file hash.

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """
        start_time = time.time()

        try:
            # Update task status
            task.current_stage = ImportStage.HASHING
            task.status = ImportStatus.IN_PROGRESS

            # Calculate hash
            file_hash = calculate_file_hash(task.file_path)

            if not file_hash:
                raise ValueError("Hash calculation returned None")

            # Update task
            task.file_hash = file_hash

            # Update database if model exists
            if task.model_id:
                self.db_manager.update_model_hash(task.model_id, file_hash)

            task.status = ImportStatus.COMPLETED

            duration = time.time() - start_time

            self.logger.info(
                "Calculated hash for %s: %s in %.2fs",
                task.filename,
                file_hash[:16],
                duration,
            )

            return StageResult(
                stage=self.stage_name,
                success=True,
                task=task,
                duration_seconds=duration,
                metadata={"file_hash": file_hash},
            )

        except Exception as e:
            error_msg = f"Hash calculation failed: {e}"
            task.status = ImportStatus.FAILED
            task.failed_stage = ImportStage.HASHING
            task.error_message = error_msg

            duration = time.time() - start_time

            self.logger.error(
                "Failed to calculate hash for %s: %s",
                task.filename,
                error_msg,
                exc_info=True,
            )

            return StageResult(
                stage=self.stage_name,
                success=False,
                task=task,
                error_message=error_msg,
                duration_seconds=duration,
            )
