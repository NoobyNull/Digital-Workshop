"""
Enhanced progressive model loading worker with accurate parsing progress.

This worker integrates detailed parsing progress (including "decoding floats")
with viewer loading to ensure the loading indicator reaches 100% exactly when
the model becomes available for display.
"""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.format_detector import FormatDetector, ModelFormat
from src.parsers.obj_parser import OBJParser
from src.parsers.step_parser import STEPParser
from src.parsers.stl_parser import STLParser
from src.parsers.threemf_parser import ThreeMFParser
from src.gui.components.detailed_progress_tracker import (
    DetailedProgressTracker,
    LoadingStage,
)


class EnhancedProgressiveLoadWorker(QThread):
    """
    Enhanced worker thread for progressive model loading with accurate parsing progress.

    This worker provides detailed progress tracking during actual parsing operations,
    ensuring the loading indicator reflects the true state of model loading including
    the "decoding floats" phase and other parsing stages.
    """

    # Signals
    progress_updated = Signal(float, str)  # Progress percentage and message
    model_ready = Signal(object)  # Emitted when model is ready for display
    loading_complete = Signal()  # Emitted when loading is complete
    error_occurred = Signal(str)  # Emitted when an error occurs

    def __init__(self, file_path: str) -> None:
        """
        Initialize the enhanced progressive loading worker.

        Args:
            file_path: Path to the model file
        """
        super().__init__()
        self.file_path = file_path
        self.should_cancel = False
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Run the enhanced progressive loading process with accurate progress tracking."""
        try:
            self.logger.info("Starting enhanced progressive loading: %s", self.file_path)

            # Get model cache
            model_cache = get_model_cache()
            file_path_obj = Path(self.file_path)

            # Check if we need to actually parse the file
            full_model = model_cache.get(self.file_path, CacheLevel.GEOMETRY_FULL)

            if full_model:
                # Model is already in cache, loading is instant
                self.logger.info("Model found in cache - loading instantly")
                self.progress_updated.emit(100, "Model loaded from cache")
                self.model_ready.emit(full_model)
                self.loading_complete.emit()
                return

            # Model not in cache, need to parse it with detailed progress tracking
            self.logger.info("Model not in cache - parsing with detailed progress tracking")
            self._parse_model_with_progress(file_path_obj, model_cache)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Enhanced progressive loading failed: %s", str(e))
            self.error_occurred.emit(str(e))

    def _parse_model_with_progress(self, file_path: Path, model_cache) -> None:
        """
        Parse model with detailed progress tracking including "decoding floats".

        Args:
            file_path: Path to the model file
            model_cache: Model cache instance
        """
        try:
            # Create detailed progress tracker
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            tracker = DetailedProgressTracker(triangle_count=0, file_size_mb=file_size_mb)

            # Set callback to emit progress updates
            def emit_progress(progress: float, message: str) -> None:
                self.progress_updated.emit(progress, message)

            tracker.set_progress_callback(emit_progress)

            # Detect format and get appropriate parser
            tracker.start_stage(LoadingStage.METADATA, "Detecting file format...")
            fmt = FormatDetector().detect_format(file_path)

            if fmt == ModelFormat.STL:
                parser = STLParser()
            elif fmt == ModelFormat.OBJ:
                parser = OBJParser()
            elif fmt == ModelFormat.THREE_MF:
                parser = ThreeMFParser()
            elif fmt == ModelFormat.STEP:
                parser = STEPParser()
            else:
                raise Exception(f"Unsupported model format: {fmt}")

            tracker.complete_stage(f"Format detected: {fmt.value}")

            # Parse the model with progress tracking
            tracker.start_stage(LoadingStage.PARSING, f"Parsing {file_path.name}...")

            # Create progress callback for the parser
            class ParserProgressCallback:

                def __init__(self, tracker) -> None:
                    self.tracker = tracker

                def report(self, progress: float, message: str) -> None:
                    # Map parser progress to our tracking system
                    if self.tracker.progress_callback:
                        self.tracker.progress_callback(progress, message)

            progress_callback = ParserProgressCallback(tracker)

            # Perform the actual parsing
            model = parser.parse_file(str(file_path), progress_callback)

            tracker.complete_stage(f"Parsed {model.stats.triangle_count:,} triangles")

            # Cache the model for future use
            model_cache.put(str(file_path), CacheLevel.GEOMETRY_FULL, model)

            # Model is now ready for display
            self.logger.info("Model parsing completed: %s triangles", model.stats.triangle_count)
            self.progress_updated.emit(
                100, f"Model ready: {model.stats.triangle_count:,} triangles"
            )

            # Emit model ready signal
            self.model_ready.emit(model)

            # Signal completion
            self.loading_complete.emit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Model parsing failed: %s", str(e))
            raise

    def cancel(self) -> None:
        """Cancel the loading process."""
        self.should_cancel = True
        self.logger.info("Enhanced progressive loading cancelled")
