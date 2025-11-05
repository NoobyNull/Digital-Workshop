"""
Thumbnail generation worker for background processing.

This module provides a background worker thread that generates thumbnails
for imported models without blocking the main UI thread.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.import_thumbnail_service import ImportThumbnailService


class ThumbnailGenerationWorker(QThread):
    """Background worker for generating thumbnails during import."""

    # Signals
    progress_updated = Signal(int, int, str)  # current, total, current_file
    thumbnail_generated = Signal(str, str)  # file_path, thumbnail_path
    error_occurred = Signal(str, str)  # file_path, error_message
    finished_batch = Signal()  # All thumbnails generated

    def __init__(
        self,
        file_info_list: List[Tuple[str, str]],
        background: Optional[str] = None,
        material: Optional[str] = None,
    ):
        """
        Initialize the thumbnail generation worker.

        Args:
            file_info_list: List of (model_path, file_hash) tuples
            background: Background color or image path for thumbnails
            material: Material name to apply to thumbnails
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.file_info_list = file_info_list
        self.background = background
        self.material = material
        self.thumbnail_service = ImportThumbnailService()
        self._stop_requested = False

    def run(self) -> None:
        """Generate thumbnails for all files in the list."""
        try:
            self.logger.info("Starting thumbnail generation for %s files", len(self.file_info_list))
            self.logger.info("Background: %s, Material: {self.material}", self.background)

            total = len(self.file_info_list)

            # Process each file
            for idx, (model_path, file_hash) in enumerate(self.file_info_list):
                if self._stop_requested:
                    self.logger.info("Thumbnail generation stopped by user")
                    break

                try:
                    file_name = Path(model_path).name
                    self.logger.debug("Generating thumbnail for: %s", file_name)

                    # Generate thumbnail
                    result = self.thumbnail_service.generate_thumbnail(
                        model_path=model_path,
                        file_hash=file_hash,
                        background=self.background,
                        material=self.material,
                    )

                    if result.success and result.thumbnail_path:
                        self.logger.info("✓ Thumbnail generated: %s", file_name)
                        self.thumbnail_generated.emit(model_path, str(result.thumbnail_path))

                        # Save camera parameters to database if available
                        if result.camera_params:
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
                                        f"Saved camera view '{result.camera_params.view_name}' for model {model_id}"
                                    )
                            except Exception as e:
                                self.logger.warning(f"Failed to save camera parameters: {e}")
                    else:
                        error_msg = result.error or "Unknown error"
                        self.logger.warning(
                            f"✗ Failed to generate thumbnail for {file_name}: {error_msg}"
                        )
                        self.error_occurred.emit(model_path, error_msg)

                    # Emit progress
                    self.progress_updated.emit(idx + 1, total, file_name)

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.error(
                        f"Error generating thumbnail for {model_path}: {e}",
                        exc_info=True,
                    )
                    self.error_occurred.emit(model_path, str(e))
                    self.progress_updated.emit(idx + 1, total, Path(model_path).name)

            self.logger.info("Thumbnail generation batch completed")
            self.finished_batch.emit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Fatal error in thumbnail generation worker: %s", e, exc_info=True)
            self.error_occurred.emit("", str(e))

    def stop(self) -> None:
        """Request the worker to stop processing."""
        self.logger.info("Stop requested for thumbnail generation worker")
        self._stop_requested = True
        self.wait()
