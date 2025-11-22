"""
Thumbnail generation worker for background processing.

This module provides a background worker thread that generates thumbnails
for imported models without blocking the main UI thread.

Features:
- Non-blocking background processing
- Granular progress tracking (batch + individual)
- Stage-based progress (loading, material, rendering, saving)
- Cancellation support
- Comprehensive error handling
"""

from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import Signal

from src.core.logging_config import get_logger
from src.core.import_thumbnail_service import ImportThumbnailService
from src.gui.workers.base_worker import BaseWorker


class ThumbnailGenerationWorker(BaseWorker):
    """Background worker for generating thumbnails during import."""

    # Signals - Batch level
    progress_updated = Signal(int, int, str)  # current, total, current_file
    batch_progress_updated = Signal(int, int)  # current, total

    # Signals - Individual level
    individual_progress_updated = Signal(int, str)  # percent, stage
    current_file_changed = Signal(str)  # current_file_name

    # Signals - Results
    thumbnail_generated = Signal(str, str)  # file_path, thumbnail_path
    error_occurred = Signal(str, str)  # file_path, error_message
    finished_batch = Signal()  # All thumbnails generated

    def __init__(
        self,
        file_info_list: List[Tuple[str, str]],
        background: Optional[str] = None,
        material: Optional[str] = None,
        force_regenerate: bool = False,
    ):
        """Initialize the thumbnail generation worker.

        Args:
            file_info_list: List of (model_path, file_hash) tuples
            background: Background color or image path for thumbnails
            material: Material name to apply to thumbnails
            force_regenerate: If True, always regenerate thumbnails even when a cached one exists
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.file_info_list = file_info_list
        self.background = background
        self.material = material
        self.force_regenerate = force_regenerate
        self.thumbnail_service = ImportThumbnailService()

    def run(self) -> None:
        """Generate thumbnails for all files in the list."""
        try:
            self.logger.info(
                "Starting thumbnail generation for %s files", len(self.file_info_list)
            )
            self.logger.info(
                "Background: %s, Material: %s", self.background, self.material
            )

            total = len(self.file_info_list)

            # Process each file
            for idx, (model_path, file_hash) in enumerate(self.file_info_list):
                if self.is_cancel_requested():
                    self.logger.info("Thumbnail generation stopped by user")
                    break

                self._process_single_thumbnail(idx, model_path, file_hash, total)

            self.logger.info("Thumbnail generation batch completed")
            self.finished_batch.emit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Fatal error in thumbnail generation worker: %s", e, exc_info=True
            )
            self.error_occurred.emit("", str(e))

    def _process_single_thumbnail(
        self, idx: int, model_path: str, file_hash: str, total: int
    ) -> None:
        """
        Process a single thumbnail generation.

        Args:
            idx: Current index (0-based)
            model_path: Path to model file
            file_hash: Hash of model file
            total: Total number of files
        """
        try:
            file_name = Path(model_path).name
            self.logger.debug("Generating thumbnail for: %s", file_name)

            # Emit file change signal
            self.current_file_changed.emit(file_name)

            # Emit individual progress - loading stage
            self.individual_progress_updated.emit(10, "Loading model...")

            # Generate thumbnail
            result = self.thumbnail_service.generate_thumbnail(
                model_path=model_path,
                file_hash=file_hash,
                background=self.background,
                material=self.material,
                force_regenerate=self.force_regenerate,
            )

            # Emit individual progress - rendering stage
            self.individual_progress_updated.emit(80, "Rendering...")

            if result.success and result.thumbnail_path:
                self.logger.info("✓ Thumbnail generated: %s", file_name)
                self.thumbnail_generated.emit(model_path, str(result.thumbnail_path))

                # Emit individual progress - saving stage
                self.individual_progress_updated.emit(95, "Saving...")

                # Save camera parameters to database if available
                self._save_camera_parameters(file_hash, result)

                # Emit individual progress - complete
                self.individual_progress_updated.emit(100, "Complete")
            else:
                error_msg = result.error or "Unknown error"
                self.logger.warning(
                    "✗ Failed to generate thumbnail for %s: %s",
                    file_name,
                    error_msg,
                )
                self.error_occurred.emit(model_path, error_msg)

            # Emit batch progress
            self.batch_progress_updated.emit(idx + 1, total)
            self.progress_updated.emit(idx + 1, total, file_name)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Error generating thumbnail for %s: %s",
                model_path,
                e,
                exc_info=True,
            )
            self.error_occurred.emit(model_path, str(e))
            self.batch_progress_updated.emit(idx + 1, total)
            self.progress_updated.emit(idx + 1, total, Path(model_path).name)

    def _save_camera_parameters(self, file_hash: str, result) -> None:
        """
        Save camera parameters to database.

        Args:
            file_hash: Hash of model file
            result: ThumbnailGenerationResult with camera_params
        """
        if not result.camera_params:
            return

        try:
            from src.core.database_manager import get_database_manager

            db_manager = get_database_manager()

            # Find model by hash
            model = db_manager.find_model_by_hash(file_hash)
            if model:
                model_id = model.get("id")
                db_manager.update_model_camera_view(
                    model_id=model_id,
                    camera_position=result.camera_params.position,
                    camera_focal_point=result.camera_params.focal_point,
                    camera_view_up=result.camera_params.view_up,
                    camera_view_name=result.camera_params.view_name,
                )
                self.logger.debug(
                    "Saved camera view '%s' for model %d",
                    result.camera_params.view_name,
                    model_id,
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to save camera parameters: %s", e)

    def stop(self) -> None:
        """Request the worker to stop processing."""
        self.logger.info("Stop requested for thumbnail generation worker")
        self._stop_requested = True
        self.wait()
