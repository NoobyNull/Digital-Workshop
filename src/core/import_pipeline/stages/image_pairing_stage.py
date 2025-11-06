"""
Image pairing stage for the import pipeline.

Handles finding and attaching matching image files to models.
"""

import os
import shutil
import time
from pathlib import Path
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
from src.core.services.image_pairing_service import (
    ImagePairingService,
    IMAGE_EXTENSIONS,
)


class ImagePairingStage(BaseStage):
    """
    Stage that finds and attaches matching images to models.

    This stage:
    1. Checks if image already attached (resume detection)
    2. Searches for matching image files
    3. Attaches image to model in database
    4. Updates task with paired_image_path
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        pairing_service: Optional[ImagePairingService] = None,
        thread_pool: Optional[QThreadPool] = None,
    ):
        """
        Initialize the image pairing stage.

        Args:
            db_manager: Database manager instance
            pairing_service: Optional image pairing service (creates one if None)
            thread_pool: Optional thread pool for async operations
        """
        super().__init__(thread_pool)
        self.db_manager = db_manager
        self.pairing_service = pairing_service or ImagePairingService()

    @property
    def stage_name(self) -> ImportStage:
        """Return the stage identifier."""
        return ImportStage.IMAGE_PAIRING

    @staticmethod
    def _get_thumbnail_directory() -> Path:
        """Get the thumbnail storage directory."""
        appdata = os.getenv("APPDATA") or os.path.expanduser("~/.config")
        return Path(appdata) / "3DModelManager" / "thumbnails"

    def should_process(self, task: ImportTask) -> bool:
        """
        Check if image already attached.

        Args:
            task: The import task to check

        Returns:
            True if image pairing needed, False if already done
        """
        # If task already has a paired image, it's been processed
        if task.paired_image_path is not None:
            return False

        # Check if model has image in database
        if task.model_id:
            try:
                # Check if model has associated image in metadata or separate table
                # For now, we'll always try to find images
                pass
            except Exception as e:
                self.logger.warning(
                    "Error checking for existing image for %s: %s", task.filename, e
                )

        return True

    def _find_matching_image(self, model_path: str) -> Optional[str]:
        """
        Find matching image file for a model.

        Args:
            model_path: Path to the model file

        Returns:
            Path to matching image file, or None if not found
        """
        model_path_obj = Path(model_path)
        model_dir = model_path_obj.parent
        model_stem = model_path_obj.stem

        # Search for images with matching base name
        for ext in IMAGE_EXTENSIONS:
            # Try exact match
            image_path = model_dir / f"{model_stem}{ext}"
            if image_path.exists():
                return str(image_path)

            # Try common suffixes
            for suffix in ["_preview", "_thumb", "_thumbnail", "_image"]:
                image_path = model_dir / f"{model_stem}{suffix}{ext}"
                if image_path.exists():
                    return str(image_path)

        return None

    def process(self, task: ImportTask) -> StageResult:
        """
        Find and attach matching image.

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """
        start_time = time.time()

        try:
            # Update task status
            task.current_stage = ImportStage.IMAGE_PAIRING
            task.status = ImportStatus.IN_PROGRESS

            # Find matching image
            image_path = self._find_matching_image(task.file_path)

            if image_path:
                # Update task
                task.paired_image_path = image_path

                # Copy image to thumbnail directory immediately for instant UI display
                if task.file_hash:
                    thumbnail_dir = self._get_thumbnail_directory()
                    thumbnail_dir.mkdir(parents=True, exist_ok=True)
                    thumbnail_path = thumbnail_dir / f"{task.file_hash[:16]}.png"

                    # Copy paired image to thumbnail location
                    shutil.copy2(image_path, thumbnail_path)
                    task.thumbnail_path = str(thumbnail_path)

                    self.logger.info(
                        "Paired image copied to thumbnail for %s: %s -> %s",
                        task.filename,
                        Path(image_path).name,
                        thumbnail_path.name,
                    )
                else:
                    self.logger.warning(
                        "Found image for %s but no hash available to create thumbnail",
                        task.filename,
                    )

                # Update database if model exists
                if task.model_id:
                    # Store image path in metadata or separate table
                    # For now, we'll add it to metadata
                    self.db_manager.update_model_metadata(
                        task.model_id, {"preview_image": image_path}
                    )

                self.logger.info(
                    "Found matching image for %s: %s",
                    task.filename,
                    Path(image_path).name,
                )
            else:
                self.logger.debug("No matching image found for %s", task.filename)

            task.status = ImportStatus.COMPLETED

            duration = time.time() - start_time

            return StageResult(
                stage=self.stage_name,
                success=True,
                task=task,
                duration_seconds=duration,
                metadata={
                    "image_found": image_path is not None,
                    "image_path": image_path,
                },
            )

        except Exception as e:
            error_msg = f"Image pairing failed: {e}"
            task.status = ImportStatus.FAILED
            task.failed_stage = ImportStage.IMAGE_PAIRING
            task.error_message = error_msg

            duration = time.time() - start_time

            self.logger.error(
                "Failed to pair image for %s: %s",
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
