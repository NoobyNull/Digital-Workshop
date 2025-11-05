"""
Background model loading worker for library.

Loads models in a separate thread with progress reporting.
"""

import gc
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.model_cache import CacheLevel, get_model_cache
from src.core.performance_monitor import get_performance_monitor
from src.parsers.format_detector import FormatDetector, ModelFormat
from src.parsers.obj_parser import OBJParser
from src.parsers.step_parser import STEPParser
from src.parsers.stl_parser import STLParser
from src.parsers.threemf_parser import ThreeMFParser
from src.gui.components.detailed_progress_tracker import (
    DetailedProgressTracker,
    LoadingStage,
)


logger = get_logger(__name__)


class ModelLoadWorker(QThread):
    """Worker thread for loading models in the background."""

    model_loaded = Signal(dict)
    progress_updated = Signal(float, str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, file_paths: List[str]) -> None:
        """
        Initialize the worker.

        Args:
            file_paths: List of file paths to load
        """
        super().__init__()
        self.file_paths = file_paths
        self._is_cancelled = False
        self.logger = get_logger(__name__)
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()

    def cancel(self) -> None:
        """Cancel the loading operation."""
        self._is_cancelled = True

    def run(self) -> None:
        """Load models in background thread with detailed progress tracking."""
        self.logger.info("Starting to load %s models", len(self.file_paths))
        for i, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                self.logger.info("Model loading cancelled")
                break

            try:
                filename = Path(file_path).name
                file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

                # Create detailed progress tracker for this file
                tracker = DetailedProgressTracker(
                    triangle_count=0, file_size_mb=file_size_mb
                )

                # Set callback to emit progress
                # Use default arguments to capture loop variables (avoids cell-var-from-loop)
                def emit_progress(
                    progress: float,
                    message: str,
                    idx: int = i,
                    fname: str = filename
                ) -> None:
                    """
                    Emit progress updates for the current file being loaded.

                    Calculates overall progress across all files and emits a signal
                    with the progress percentage and status message.

                    Args:
                        progress: Progress percentage for current file (0-100)
                        message: Status message describing current operation
                        idx: File index (captured from loop)
                        fname: Filename (captured from loop)
                    """
                    # Adjust for multiple files
                    file_progress = (idx / max(1, len(self.file_paths))) * 100.0
                    overall_progress = file_progress + (progress / len(self.file_paths))
                    self.progress_updated.emit(overall_progress, f"{fname}: {message}")

                tracker.set_progress_callback(emit_progress)

                operation_id = self.performance_monitor.start_operation(
                    "load_model_to_library",
                    {"file_path": file_path, "filename": filename},
                )

                # Check cache first
                tracker.start_stage(
                    LoadingStage.METADATA, f"Checking cache for {filename}"
                )
                cached_model = self.model_cache.get(file_path, CacheLevel.METADATA)
                if cached_model:
                    model = cached_model
                    tracker.complete_stage("Loaded from cache")
                else:
                    # Try Trimesh first for fast background loading
                    from src.parsers.trimesh_loader import get_trimesh_loader  # pylint: disable=import-outside-toplevel

                    trimesh_loader = get_trimesh_loader()
                    model = None

                    if trimesh_loader.is_trimesh_available():
                        tracker.start_stage(
                            LoadingStage.PARSING,
                            f"Loading {filename} with Trimesh (fast)...",
                        )
                        model = trimesh_loader.load_model(file_path, tracker)

                    # Fallback to standard parsers if Trimesh failed or unavailable
                    if model is None:
                        # Detect format
                        fmt = FormatDetector().detect_format(Path(file_path))
                        # pylint: disable=abstract-class-instantiated
                        if fmt == ModelFormat.STL:
                            parser = STLParser()
                        elif fmt == ModelFormat.OBJ:
                            parser = OBJParser()
                        elif fmt == ModelFormat.THREE_MF:
                            parser = ThreeMFParser()
                        elif fmt == ModelFormat.STEP:
                            parser = STEPParser()
                        else:
                            raise ValueError(f"Unsupported model format: {fmt}")

                        # Parse with progress tracking
                        tracker.start_stage(LoadingStage.PARSING, f"Parsing {filename}")
                        model = parser.parse_metadata_only(file_path)
                        tracker.complete_stage(
                            f"Parsed {model.stats.triangle_count:,} triangles"
                        )

                    # Cache the model
                    self.model_cache.put(file_path, CacheLevel.METADATA, model)

                model_info = {
                    "file_path": file_path,
                    "filename": filename,
                    "format": model.format_type.value,
                    "file_size": model.stats.file_size_bytes,
                    "file_hash": None,
                    "triangle_count": model.stats.triangle_count,
                    "vertex_count": model.stats.vertex_count,
                    "dimensions": model.stats.get_dimensions(),
                    "parsing_time": model.stats.parsing_time_seconds,
                    "min_bounds": (
                        model.stats.min_bounds.x,
                        model.stats.min_bounds.y,
                        model.stats.min_bounds.z,
                    ),
                    "max_bounds": (
                        model.stats.max_bounds.x,
                        model.stats.max_bounds.y,
                        model.stats.max_bounds.z,
                    ),
                }

                self.model_loaded.emit(model_info)
                self.performance_monitor.end_operation(operation_id, success=True)

                if i % 10 == 0:
                    gc.collect()

            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                msg = f"Failed to load {file_path}: {e}"
                self.logger.error(msg)
                self.error_occurred.emit(msg)

        self.finished.emit()
        self.logger.info("Model loading completed")
