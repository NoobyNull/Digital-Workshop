"""
Thumbnail Regeneration Worker for Non-Blocking UI Operations.

Provides a QThread-based worker for regenerating thumbnails in the background
without blocking the main GUI thread.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal

from src.core.logging_config import get_logger
from src.core.import_thumbnail_service import (
    ImportThumbnailService,
    ThumbnailGenerationResult,
)
from src.gui.workers.base_worker import BaseWorker


class ThumbnailRegenerationWorker(BaseWorker):
    """
    Worker thread for regenerating thumbnails without blocking the GUI.

    Signals:
        progress_updated: Emitted with (current, total, message) during generation
        thumbnail_generated: Emitted with ThumbnailGenerationResult on success
        error_occurred: Emitted with error message on failure
        finished: Emitted when work is complete (success or failure)
    """

    progress_updated = Signal(int, int, str)  # current, total, message
    thumbnail_generated = Signal(object)  # ThumbnailGenerationResult
    error_occurred = Signal(str)  # error_message
    finished = Signal()

    def __init__(
        self,
        model_path: str,
        file_hash: str,
        material: Optional[str] = None,
        background: Optional[str] = None,
    ) -> None:
        """
        Initialize the thumbnail regeneration worker.

        Args:
            model_path: Path to the 3D model file
            file_hash: Hash of the model file
            material: Optional material name to apply
            background: Optional background color or image path
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.model_path = model_path
        self.file_hash = file_hash
        self.material = material
        self.background = background
        # Bridge base signals to legacy names for existing UI wiring.
        self.progress.connect(self.progress_updated)
        self.error.connect(self.error_occurred)

    def cancel(self) -> None:
        """Request cancellation of the thumbnail generation."""
        self.request_cancel()
        self.logger.info("Thumbnail regeneration cancelled by user")

    def run(self) -> None:
        """Execute thumbnail regeneration in background thread."""
        try:
            model_name = Path(self.model_path).name
            self.logger.info(
                "Starting thumbnail regeneration for: %s (hash: %s)",
                model_name,
                self.file_hash[:16],
            )

            # Emit initial progress
            self.emit_progress(0, 100, f"Loading {model_name}...")

            # Check for cancellation
            if self.is_cancel_requested():
                self.logger.info("Thumbnail regeneration cancelled before start")
                self.finished.emit()
                return

            # Create thumbnail service
            thumbnail_service = ImportThumbnailService()

            # Emit progress
            self.emit_progress(25, 100, f"Rendering {model_name}...")

            # Generate thumbnail with force_regenerate=True
            result: ThumbnailGenerationResult = thumbnail_service.generate_thumbnail(
                model_path=self.model_path,
                file_hash=self.file_hash,
                material=self.material,
                background=self.background,
                force_regenerate=True,
            )

            # Check for cancellation after generation
            if self.is_cancel_requested():
                self.logger.info("Thumbnail regeneration cancelled after generation")
                self.finished.emit()
                return

            # Emit progress
            self.emit_progress(90, 100, "Finalizing...")

            # Check result
            if result.success:
                self.logger.info(
                    "Thumbnail regenerated successfully: %s", result.thumbnail_path
                )
                self.emit_progress(100, 100, "Complete!")
                self.thumbnail_generated.emit(result)
            else:
                error_msg = result.error or "Unknown error during thumbnail generation"
                self.logger.error("Thumbnail regeneration failed: %s", error_msg)
                self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Thumbnail regeneration failed: {str(e)}"
            self.logger.error("%s", error_msg, exc_info=True)
            self.error.emit(error_msg)

        finally:
            self.finished.emit()


class BatchThumbnailRegenerationWorker(BaseWorker):
    """
    Worker thread for regenerating multiple thumbnails in batch.

    Signals:
        progress_updated: Emitted with (current, total, message) during generation
        thumbnail_generated: Emitted with (model_id, ThumbnailGenerationResult) for each success
        error_occurred: Emitted with (model_id, error_message) for each failure
        batch_complete: Emitted with (success_count, failure_count) when batch is done
        finished: Emitted when work is complete
    """

    progress_updated = Signal(int, int, str)  # current, total, message
    thumbnail_generated = Signal(int, object)  # model_id, ThumbnailGenerationResult
    error_occurred = Signal(int, str)  # model_id, error_message
    batch_complete = Signal(int, int)  # success_count, failure_count
    finished = Signal()

    def __init__(
        self,
        models_data: list,  # List of dicts with model_id, file_path, file_hash
        material: Optional[str] = None,
        background: Optional[str] = None,
    ) -> None:
        """
        Initialize the batch thumbnail regeneration worker.

        Args:
            models_data: List of model data dicts with keys: model_id, file_path, file_hash
            material: Optional material name to apply
            background: Optional background color or image path
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.models_data = models_data
        self.material = material
        self.background = background
        # Bridge base signals for existing slots.
        self.progress.connect(self.progress_updated)
        self.error.connect(lambda msg: None)  # errors are per-model below

    def cancel(self) -> None:
        """Request cancellation of the batch thumbnail generation."""
        self.request_cancel()
        self.logger.info("Batch thumbnail regeneration cancelled by user")

    def run(self) -> None:
        """Execute batch thumbnail regeneration in background thread."""
        success_count = 0
        failure_count = 0
        total = len(self.models_data)

        try:
            self.logger.info(
                "Starting batch thumbnail regeneration for %d models", total
            )

            # Create thumbnail service
            thumbnail_service = ImportThumbnailService()

            for idx, model_data in enumerate(self.models_data):
                # Check for cancellation
                if self.is_cancel_requested():
                    self.logger.info(
                        "Batch thumbnail regeneration cancelled at %d/%d", idx, total
                    )
                    break

                model_id = model_data["model_id"]
                file_path = model_data["file_path"]
                file_hash = model_data["file_hash"]
                model_name = Path(file_path).name

                # Emit progress
                self.emit_progress(
                    idx + 1, total, f"Regenerating {model_name} ({idx + 1}/{total})..."
                )

                try:
                    # Generate thumbnail
                    result: ThumbnailGenerationResult = (
                        thumbnail_service.generate_thumbnail(
                            model_path=file_path,
                            file_hash=file_hash,
                            material=self.material,
                            background=self.background,
                            force_regenerate=True,
                        )
                    )

                    if result.success:
                        success_count += 1
                        self.thumbnail_generated.emit(model_id, result)
                    else:
                        failure_count += 1
                        error_msg = result.error or "Unknown error"
                        self.error_occurred.emit(model_id, error_msg)

                except Exception as e:
                    failure_count += 1
                    error_msg = f"Failed to regenerate thumbnail: {str(e)}"
                    self.logger.error(
                        "Error regenerating thumbnail for model %d: %s",
                        model_id,
                        error_msg,
                    )
                    self.error_occurred.emit(model_id, error_msg)

            self.logger.info(
                "Batch thumbnail regeneration complete: %d success, %d failed",
                success_count,
                failure_count,
            )
            self.batch_complete.emit(success_count, failure_count)

        except Exception as e:
            self.logger.error(
                "Batch thumbnail regeneration failed: %s", e, exc_info=True
            )

        finally:
            self.finished.emit()
