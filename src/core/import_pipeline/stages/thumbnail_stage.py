"""
Thumbnail generation stage for the import pipeline.

Handles generating thumbnails for models.
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


class ThumbnailStage(BaseStage):
    """
    Stage that generates thumbnails for models.

    This stage:
    1. Checks if thumbnail already exists (resume detection)
    2. Generates thumbnail using thumbnail generator
    3. Updates task with thumbnail_path
    """

    def __init__(
        self,
        thumbnail_generator,
        thread_pool: Optional[QThreadPool] = None,
    ):
        """
        Initialize the thumbnail stage.

        Args:
            thumbnail_generator: ThumbnailGenerator instance
            thread_pool: Optional thread pool for async operations
        """
        super().__init__(thread_pool)
        self.thumbnail_generator = thumbnail_generator

    @staticmethod
    def _get_thumbnail_directory() -> Path:
        """Get the thumbnail storage directory."""
        appdata = os.getenv("APPDATA") or os.path.expanduser("~/.config")
        return Path(appdata) / "3DModelManager" / "thumbnails"

    @property
    def stage_name(self) -> ImportStage:
        """Return the stage identifier."""
        return ImportStage.THUMBNAIL_GENERATION

    def should_process(self, task: ImportTask) -> bool:
        """
        Check if thumbnail already exists.

        Args:
            task: The import task to check

        Returns:
            True if thumbnail needs to be generated, False if already exists
        """
        # If task already has a thumbnail path, check if file exists
        if task.thumbnail_path:
            if Path(task.thumbnail_path).exists():
                return False

        # Check if thumbnail file exists based on file hash
        if task.file_hash:
            thumbnail_dir = self._get_thumbnail_directory()
            thumbnail_path = thumbnail_dir / f"{task.file_hash[:16]}.png"

            if thumbnail_path.exists():
                task.thumbnail_path = str(thumbnail_path)
                self.logger.info(
                    "Thumbnail already exists for %s: %s",
                    task.filename,
                    thumbnail_path.name,
                )
                return False

        return True

    def process(self, task: ImportTask) -> StageResult:
        """
        Generate thumbnail or use paired image.

        If a paired image exists, use it as the thumbnail.
        Otherwise, generate a 3D rendered thumbnail.

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """
        start_time = time.time()

        try:
            # Update task status
            task.current_stage = ImportStage.THUMBNAIL_GENERATION
            task.status = ImportStatus.IN_PROGRESS

            thumbnail_generated = False
            used_paired_image = False

            # Check if we have a paired image to use as thumbnail
            if task.paired_image_path and Path(task.paired_image_path).exists():
                # Use paired image as thumbnail
                if task.file_hash:
                    thumbnail_dir = self._get_thumbnail_directory()
                    thumbnail_dir.mkdir(parents=True, exist_ok=True)
                    thumbnail_path = thumbnail_dir / f"{task.file_hash[:16]}.png"

                    # Copy paired image to thumbnail location
                    shutil.copy2(task.paired_image_path, thumbnail_path)
                    task.thumbnail_path = str(thumbnail_path)
                    used_paired_image = True

                    self.logger.info(
                        "Using paired image as thumbnail for %s: %s",
                        task.filename,
                        Path(task.paired_image_path).name,
                    )
                else:
                    self.logger.warning(
                        "Paired image found for %s but no hash available to save thumbnail",
                        task.filename,
                    )
            else:
                # No paired image - generate 3D rendered thumbnail
                model_info = task.to_dict()
                thumbnail = self.thumbnail_generator.generate_thumbnail(model_info)

                if thumbnail:
                    # Thumbnail generator returns QPixmap or path
                    # Store the path in task
                    if task.file_hash:
                        thumbnail_dir = self._get_thumbnail_directory()
                        thumbnail_path = thumbnail_dir / f"{task.file_hash[:16]}.png"
                        task.thumbnail_path = str(thumbnail_path)
                        thumbnail_generated = True
                        self.logger.info(
                            "Generated 3D thumbnail for %s: %s",
                            task.filename,
                            thumbnail_path.name,
                        )
                    else:
                        self.logger.warning(
                            "Generated thumbnail for %s but no hash available to save path",
                            task.filename,
                        )
                else:
                    self.logger.warning(
                        "Thumbnail generation returned None for %s", task.filename
                    )

            task.status = ImportStatus.COMPLETED

            duration = time.time() - start_time

            return StageResult(
                stage=self.stage_name,
                success=True,
                task=task,
                duration_seconds=duration,
                metadata={
                    "thumbnail_generated": thumbnail_generated,
                    "used_paired_image": used_paired_image,
                    "thumbnail_path": task.thumbnail_path,
                },
            )

        except Exception as e:
            error_msg = f"Thumbnail generation failed: {e}"
            task.status = ImportStatus.FAILED
            task.failed_stage = ImportStage.THUMBNAIL_GENERATION
            task.error_message = error_msg

            duration = time.time() - start_time

            self.logger.error(
                "Failed to generate thumbnail for %s: %s",
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
