"""
Resume detection for the import pipeline.

Detects partially imported models and determines which stages need to be completed.
"""

from pathlib import Path
from typing import List, Dict, Any

import os
from src.core.import_pipeline.pipeline_models import ImportTask, ImportStage
from src.core.database_manager import DatabaseManager
from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ResumeDetector:
    """
    Detects which stages of the import pipeline have been completed.

    This allows the pipeline to resume interrupted imports without
    redoing work that's already been completed.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the resume detector.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    @staticmethod
    def _get_thumbnail_directory() -> Path:
        """Get the thumbnail storage directory."""
        appdata = os.getenv("APPDATA") or os.path.expanduser("~/.config")
        return Path(appdata) / "3DModelManager" / "thumbnails"

    def detect_completed_stages(self, task: ImportTask) -> List[ImportStage]:
        """
        Detect which stages have been completed for a task.

        Args:
            task: The import task to check

        Returns:
            List of completed stages
        """
        completed = []

        # Check database stage
        if self._is_database_complete(task):
            completed.append(ImportStage.DATABASE_INSERT)

        # Check hashing stage
        if self._is_hashing_complete(task):
            completed.append(ImportStage.HASHING)

        # Check image pairing stage
        if self._is_image_pairing_complete(task):
            completed.append(ImportStage.IMAGE_PAIRING)

        # Check thumbnail stage
        if self._is_thumbnail_complete(task):
            completed.append(ImportStage.THUMBNAIL_GENERATION)

        return completed

    def _is_database_complete(self, task: ImportTask) -> bool:
        """Check if database insertion is complete."""
        # If task has model_id, it's in the database
        if task.model_id:
            return True

        # Check if model exists by file path
        try:
            model = self.db_manager.get_model_by_path(task.file_path)
            if model:
                task.model_id = model.get("id")
                return True
        except Exception as e:
            logger.warning("Error checking database for %s: %s", task.filename, e)

        return False

    def _is_hashing_complete(self, task: ImportTask) -> bool:
        """Check if file hashing is complete."""
        # If task has file_hash, it's complete
        if task.file_hash:
            return True

        # Check database if model exists
        if task.model_id:
            try:
                model = self.db_manager.get_model_by_id(task.model_id)
                if model and model.get("file_hash"):
                    task.file_hash = model["file_hash"]
                    return True
            except Exception as e:
                logger.warning("Error checking hash for %s: %s", task.filename, e)

        return False

    def _is_image_pairing_complete(self, task: ImportTask) -> bool:
        """Check if image pairing is complete."""
        # If task has paired_image_path, it's complete
        if task.paired_image_path:
            return True

        # Check database if model exists
        if task.model_id:
            try:
                metadata = self.db_manager.get_model_metadata(task.model_id)
                if metadata and metadata.get("preview_image"):
                    task.paired_image_path = metadata["preview_image"]
                    return True
            except Exception as e:
                logger.warning(
                    "Error checking image pairing for %s: %s", task.filename, e
                )

        # Image pairing is optional - if no image found, consider it "complete"
        # (i.e., we tried and there was no image to pair)
        return False

    def _is_thumbnail_complete(self, task: ImportTask) -> bool:
        """Check if thumbnail generation is complete."""
        # If task has thumbnail_path and file exists, it's complete
        if task.thumbnail_path and Path(task.thumbnail_path).exists():
            return True

        # Check if thumbnail exists based on file hash
        if task.file_hash:
            thumbnail_dir = self._get_thumbnail_directory()
            thumbnail_path = thumbnail_dir / f"{task.file_hash[:16]}.png"

            if thumbnail_path.exists():
                task.thumbnail_path = str(thumbnail_path)
                return True

        return False

    def get_resume_summary(self, tasks: List[ImportTask]) -> Dict[str, Any]:
        """
        Get a summary of resume status for multiple tasks.

        Args:
            tasks: List of import tasks

        Returns:
            Dictionary with resume statistics
        """
        total = len(tasks)
        fully_complete = 0
        partially_complete = 0
        not_started = 0

        stage_completion = {
            ImportStage.DATABASE_INSERT: 0,
            ImportStage.HASHING: 0,
            ImportStage.IMAGE_PAIRING: 0,
            ImportStage.THUMBNAIL_GENERATION: 0,
        }

        for task in tasks:
            completed_stages = self.detect_completed_stages(task)

            if len(completed_stages) == 4:
                fully_complete += 1
            elif len(completed_stages) > 0:
                partially_complete += 1
            else:
                not_started += 1

            for stage in completed_stages:
                if stage in stage_completion:
                    stage_completion[stage] += 1

        return {
            "total_tasks": total,
            "fully_complete": fully_complete,
            "partially_complete": partially_complete,
            "not_started": not_started,
            "stage_completion": stage_completion,
        }

