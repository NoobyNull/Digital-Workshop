"""
Batch screenshot generator worker for processing multiple models.

This module provides a background worker thread that generates screenshots
for all models in the library with applied materials.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.gui.screenshot_generator import ScreenshotGenerator


class BatchScreenshotWorker(QThread):
    """Background worker for generating screenshots of multiple models."""

    # Signals
    progress_updated = Signal(int, int)  # current, total
    screenshot_generated = Signal(int, str)  # model_id, screenshot_path
    error_occurred = Signal(str)  # error message
    finished_batch = Signal()  # All screenshots generated

    def __init__(
        self,
        material_manager=None,
        screenshot_size: int = 256,
        background_image: Optional[str] = None,
        material_name: Optional[str] = None,
    ):
        """
        Initialize the batch screenshot worker.

        Args:
            material_manager: MaterialManager instance for applying materials
            screenshot_size: Size of screenshots (width and height)
            background_image: Path to background image for thumbnails
            material_name: Material to apply to all thumbnails
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.db_manager = get_database_manager()
        self.material_manager = material_manager
        self.screenshot_size = screenshot_size
        self.screenshot_generator = ScreenshotGenerator(
            width=screenshot_size,
            height=screenshot_size,
            background_image=background_image,
            material_name=material_name,
        )
        self._stop_requested = False

    def run(self) -> None:
        """Generate screenshots for all models in the library."""
        try:
            self.logger.info("Starting batch screenshot generation")

            # Get all models from database
            models = self.db_manager.get_all_models()
            total = len(models)

            if total == 0:
                self.logger.info("No models to process")
                self.finished_batch.emit()
                return

            self.logger.info("Processing %s models", total)

            # Process each model
            for idx, model in enumerate(models):
                if self._stop_requested:
                    self.logger.info("Batch screenshot generation stopped by user")
                    break

                try:
                    model_id = model.get("id")
                    file_path = model.get("file_path")
                    file_hash = model.get("file_hash")

                    if not file_path or not Path(file_path).exists():
                        self.logger.warning("Model file not found: %s", file_path)
                        self.progress_updated.emit(idx + 1, total)
                        continue

                    # Generate screenshot
                    screenshot_path = self._generate_screenshot_for_model(
                        model_id, file_path, file_hash
                    )

                    if screenshot_path:
                        # Update database with thumbnail path
                        self.db_manager.update_model_thumbnail(model_id, screenshot_path)
                        self.screenshot_generated.emit(model_id, screenshot_path)
                        self.logger.info("Generated screenshot for model %s", model_id)
                    else:
                        self.logger.warning("Failed to generate screenshot for model %s", model_id)

                    # Emit progress
                    self.progress_updated.emit(idx + 1, total)

                except Exception as e:
                    self.logger.error("Error processing model %s: {e}", model.get('id'))
                    self.error_occurred.emit(f"Error processing model: {e}")

            self.logger.info("Batch screenshot generation completed")
            self.finished_batch.emit()

        except Exception as e:
            self.logger.error("Batch screenshot generation failed: %s", e, exc_info=True)
            self.error_occurred.emit(f"Batch generation failed: {e}")

    def _generate_screenshot_for_model(
        self, model_id: int, file_path: str, file_hash: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a screenshot for a single model.

        Args:
            model_id: ID of the model
            file_path: Path to the model file
            file_hash: xxHash128 of the model file (32 hex chars), or None to use model_id

        Returns:
            Path to the generated screenshot, or None if failed
        """
        try:
            # Determine output path in cache directory
            cache_dir = Path.home() / ".3dmm" / "thumbnails"
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Use file hash for naming if available, otherwise fall back to model_id
            if file_hash:
                # Use hash-based naming: {hash}_128x128.png
                output_path = str(cache_dir / f"{file_hash}_128x128.png")
            else:
                # Fallback to model_id-based naming
                output_path = str(cache_dir / f"model_{model_id}.png")

            # Generate screenshot
            screenshot_path = self.screenshot_generator.capture_model_screenshot(
                model_path=file_path,
                output_path=output_path,
                material_manager=self.material_manager,
                material_name=None,  # Use default material
            )

            return screenshot_path

        except Exception as e:
            self.logger.error("Failed to generate screenshot for model %s: {e}", model_id)
            return None

    def stop(self) -> None:
        """Request the worker to stop processing."""
        self._stop_requested = True
        self.logger.info("Stop requested for batch screenshot generation")
