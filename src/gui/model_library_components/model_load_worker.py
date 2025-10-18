"""
Background model loading worker for library.

Loads models in a separate thread with progress reporting.
"""

import gc
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.model_cache import CacheLevel, get_model_cache
from src.core.performance_monitor import get_performance_monitor
from src.parsers.format_detector import FormatDetector, ModelFormat
from src.parsers.obj_parser import OBJParser
from src.parsers.step_parser import STEPParser
from src.parsers.stl_parser import STLParser
from src.parsers.threemf_parser import ThreeMFParser


logger = get_logger(__name__)


class ModelLoadWorker(QThread):
    """Worker thread for loading models in the background."""

    model_loaded = Signal(dict)
    progress_updated = Signal(float, str)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, file_paths: List[str]):
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
        """Load models in background thread."""
        self.logger.info(f"Starting to load {len(self.file_paths)} models")
        for i, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                self.logger.info("Model loading cancelled")
                break

            try:
                progress = (i / max(1, len(self.file_paths))) * 100.0
                filename = Path(file_path).name
                self.progress_updated.emit(progress, f"Loading {filename}")

                operation_id = self.performance_monitor.start_operation(
                    "load_model_to_library", {"file_path": file_path, "filename": filename}
                )

                cached_model = self.model_cache.get(file_path, CacheLevel.METADATA)
                if cached_model:
                    model = cached_model
                else:
                    fmt = FormatDetector().detect_format(Path(file_path))
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

                    model = parser.parse_metadata_only(file_path)
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
                    "min_bounds": (model.stats.min_bounds.x, model.stats.min_bounds.y, model.stats.min_bounds.z),
                    "max_bounds": (model.stats.max_bounds.x, model.stats.max_bounds.y, model.stats.max_bounds.z),
                }

                self.model_loaded.emit(model_info)
                self.performance_monitor.end_operation(operation_id, success=True)

                if i % 10 == 0:
                    gc.collect()

            except Exception as e:
                msg = f"Failed to load {file_path}: {e}"
                self.logger.error(msg)
                self.error_occurred.emit(msg)

        self.finished.emit()
        self.logger.info("Model loading completed")

