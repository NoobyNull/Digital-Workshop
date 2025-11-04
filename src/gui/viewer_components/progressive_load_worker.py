"""
Progressive model loading worker thread.

Handles background loading of 3D model geometry with progress reporting.
"""

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.model_cache import get_model_cache, CacheLevel


class ProgressiveLoadWorker(QThread):
    """
    Worker thread for progressive model loading.

    Handles loading of model geometry in background without blocking UI.
    """

    # Signals
    progress_updated = Signal(float, str)  # Progress percentage and message
    model_ready = Signal(object)  # Emitted when model is ready for display
    loading_complete = Signal()  # Emitted when loading is complete
    error_occurred = Signal(str)  # Emitted when an error occurs

    def __init__(self, file_path: str):
        """
        Initialize the progressive loading worker.

        Args:
            file_path: Path to the model file
        """
        super().__init__()
        self.file_path = file_path
        self.should_cancel = False
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Run the progressive loading process."""
        try:
            self.logger.info("Starting progressive loading: %s", self.file_path)

            # Get model cache
            model_cache = get_model_cache()

            # First, try to load metadata
            self.progress_updated.emit(10, "Loading model metadata...")
            metadata_model = model_cache.get(self.file_path, CacheLevel.METADATA)

            if metadata_model:
                self.progress_updated.emit(30, "Metadata loaded from cache")
                self.model_ready.emit(metadata_model)

            # Then load low-res geometry
            self.progress_updated.emit(40, "Loading low-resolution geometry...")
            low_res_model = model_cache.get(self.file_path, CacheLevel.GEOMETRY_LOW)

            if low_res_model:
                self.progress_updated.emit(70, "Low-resolution geometry loaded")
                self.model_ready.emit(low_res_model)

            # Finally load full geometry
            self.progress_updated.emit(80, "Loading full-resolution geometry...")
            full_model = model_cache.get(self.file_path, CacheLevel.GEOMETRY_FULL)

            if full_model:
                self.progress_updated.emit(100, "Full model loaded")
                self.model_ready.emit(full_model)
            else:
                # Full model not in cache, this shouldn't happen with proper lazy loading
                self.error_occurred.emit("Full model not available in cache")

            self.loading_complete.emit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Progressive loading failed: %s", str(e))
            self.error_occurred.emit(str(e))

    def cancel(self) -> None:
        """Cancel the loading process."""
        self.should_cancel = True
