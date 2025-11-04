"""
Base parser interface for Digital Workshop.

This module provides the common interface and data structures that all 3D format parsers
must implement. It ensures consistent behavior across different format parsers.
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Union
import gc

from src.core.logging_config import get_logger
from src.core.performance_monitor import get_performance_monitor
from src.core.data_structures import (
    Model,
    ModelFormat,
    Triangle,
    Vector3D,
    ModelStats,
    LoadingState,
)

# Import model_cache lazily to avoid circular imports


class ParseError(Exception):
    """Custom exception for parsing errors."""


class ProgressCallback:
    """Callback interface for progress reporting during parsing."""

    def __init__(self, callback_func=None):
        """
        Initialize progress callback.

        Args:
            callback_func: Optional function to call with progress updates
                          signature: callback_func(progress_percent: float, message: str)
        """
        self.callback_func = callback_func
        self.last_report_time = 0
        self.report_interval = 0.1  # Report at most every 0.1 seconds

    def report(self, progress_percent: float, message: str = "") -> None:
        """
        Report progress if enough time has passed.

        Args:
            progress_percent: Progress percentage (0-100)
            message: Optional progress message
        """
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            if self.callback_func:
                self.callback_func(progress_percent, message)
            self.last_report_time = current_time


class BaseParser(ABC):
    """
    Abstract base class for all 3D format parsers.

    All format parsers must inherit from this class and implement the required methods.
    This ensures consistent behavior and interface across all parsers.
    """

    def __init__(self):
        """Initialize the parser."""
        self.logger = get_logger(self.__class__.__name__)
        self._cancel_parsing = False
        self.performance_monitor = get_performance_monitor()
        self._model_cache = None  # Lazy initialization

    @property
    def model_cache(self):
        """Lazy initialization of model_cache to avoid circular imports."""
        if self._model_cache is None:
            from src.core.model_cache import get_model_cache

            self._model_cache = get_model_cache()
        return self._model_cache

    def parse_file(
        self,
        file_path: Union[str, Path],
        progress_callback: Optional[ProgressCallback] = None,
        lazy_loading: bool = True,
    ) -> Model:
        """
        Parse a 3D model file with optional lazy loading.

        Args:
            file_path: Path to the 3D model file
            progress_callback: Optional progress callback
            lazy_loading: Enable lazy loading for better performance

        Returns:
            Parsed 3D model

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        file_path = str(file_path)

        # Start performance monitoring
        operation_id = self.performance_monitor.start_operation(
            f"parse_{self.__class__.__name__}",
            {"file_path": file_path, "lazy_loading": lazy_loading},
        )

        try:
            # Check cache first if lazy loading is enabled
            if lazy_loading:
                # Try to get cached model
                # Import CacheLevel lazily to avoid circular imports
                from src.core.model_cache import CacheLevel

                cached_model = self.model_cache.get(file_path, CacheLevel.GEOMETRY_FULL)
                if cached_model:
                    self.logger.info(f"Loaded model from cache: {file_path}")
                    self.performance_monitor.end_operation(operation_id, success=True)
                    return cached_model

                # Try to get cached metadata
                cached_metadata = self.model_cache.get(file_path, CacheLevel.METADATA)
                if cached_metadata:
                    self.logger.info(f"Loaded metadata from cache: {file_path}")
                    # Load full geometry in background if needed
                    if cached_metadata.needs_geometry_loading():
                        self._load_geometry_async(cached_metadata, progress_callback)
                    self.performance_monitor.end_operation(operation_id, success=True)
                    return cached_metadata

            # Parse the file
            model = self._parse_file_internal(file_path, progress_callback)

            # Cache the model if lazy loading is enabled
            if lazy_loading:
                self.model_cache.put(file_path, CacheLevel.GEOMETRY_FULL, model)
                # Also cache metadata separately
                metadata_model = self._create_metadata_model(model)
                self.model_cache.put(file_path, CacheLevel.METADATA, metadata_model)

            self.performance_monitor.end_operation(operation_id, success=True)
            return model

        except Exception as e:
            self.performance_monitor.end_operation(
                operation_id, success=False, error_message=str(e)
            )
            raise

    @abstractmethod
    def _parse_file_internal(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> Model:
        """
        Internal method to parse a 3D model file.

        Args:
            file_path: Path to the 3D model file
            progress_callback: Optional progress callback

        Returns:
            Parsed 3D model

        Raises:
            ParseError: If parsing fails
        """

    def parse_metadata_only(self, file_path: Union[str, Path]) -> Model:
        """
        Parse only metadata from a 3D model file.

        Args:
            file_path: Path to the 3D model file

        Returns:
            Model with metadata only
        """
        file_path = str(file_path)

        # Check cache first
        # Import CacheLevel lazily to avoid circular imports
        from src.core.model_cache import CacheLevel

        cached_metadata = self.model_cache.get(file_path, CacheLevel.METADATA)
        if cached_metadata:
            return cached_metadata

        # Parse metadata
        metadata_model = self._parse_metadata_only_internal(file_path)

        # Cache metadata
        self.model_cache.put(file_path, CacheLevel.METADATA, metadata_model)

        return metadata_model

    @abstractmethod
    def _parse_metadata_only_internal(self, file_path: str) -> Model:
        """
        Internal method to parse only metadata from a 3D model file.

        Args:
            file_path: Path to the 3D model file

        Returns:
            Model with metadata only
        """

    def _create_metadata_model(self, model: Model) -> Model:
        """
        Create a metadata-only model from a full model.

        Args:
            model: Full model

        Returns:
            Metadata-only model
        """
        return Model(
            header=model.header,
            triangles=[],  # Empty geometry
            stats=model.stats,
            format_type=model.format_type,
            loading_state=LoadingState.METADATA_ONLY,
            file_path=model.file_path,
        )

    def _load_geometry_async(
        self,
        metadata_model: Model,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """
        Load geometry asynchronously for a metadata-only model.

        Args:
            metadata_model: Model with metadata only
            progress_callback: Optional progress callback
        """
        # This method should be overridden by subclasses to implement async loading
        # For now, we'll load synchronously
        if metadata_model.file_path:
            try:
                # Lazy import to avoid NameError during async geometry load
                from src.core.model_cache import CacheLevel

                full_model = self._parse_file_internal(metadata_model.file_path, progress_callback)

                # Merge geometry into the metadata model
                try:
                    # Prefer array-based path if available
                    is_array_based = False
                    if hasattr(full_model, "is_array_based") and callable(
                        getattr(full_model, "is_array_based")
                    ):
                        is_array_based = bool(full_model.is_array_based())  # type: ignore[attr-defined]

                    if is_array_based:
                        # Copy arrays and mark state
                        setattr(
                            metadata_model,
                            "vertex_array",
                            getattr(full_model, "vertex_array", None),
                        )
                        setattr(
                            metadata_model,
                            "normal_array",
                            getattr(full_model, "normal_array", None),
                        )
                        metadata_model.triangles = []  # ensure no legacy triangles
                        metadata_model.loading_state = LoadingState.ARRAY_GEOMETRY
                    else:
                        # Legacy triangles path
                        metadata_model.triangles = full_model.triangles
                        metadata_model.loading_state = LoadingState.FULL_GEOMETRY

                    # Always copy stats and format (in case improved precision)
                    metadata_model.stats = full_model.stats
                    metadata_model.format_type = full_model.format_type
                except Exception as merge_err:
                    # Fallback to legacy triangles only to avoid blank view
                    self.logger.warning(
                        f"Geometry merge fallback (triangles only) due to: {merge_err}"
                    )
                    metadata_model.triangles = full_model.triangles
                    metadata_model.loading_state = LoadingState.FULL_GEOMETRY

                # Cache the full model (may be skipped if too large per cache limits)
                self.model_cache.put(metadata_model.file_path, CacheLevel.GEOMETRY_FULL, full_model)

            except Exception as e:
                self.logger.error(
                    f"Failed to load geometry for {metadata_model.file_path}: {str(e)}"
                )

    @abstractmethod
    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate a 3D model file without fully parsing it.

        Args:
            file_path: Path to the 3D model file

        Returns:
            Tuple of (is_valid, error_message)
        """

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of supported file extensions (including the dot)
        """

    def cancel_parsing(self) -> None:
        """Cancel the current parsing operation."""
        self._cancel_parsing = True
        self.logger.info("Parsing cancellation requested")

    def reset_cancel_state(self) -> None:
        """Reset the cancellation state for a new parsing operation."""
        self._cancel_parsing = False

    def _calculate_bounds(self, triangles: List[Triangle]) -> Tuple[Vector3D, Vector3D]:
        """
        Calculate the bounding box of a list of triangles.

        Args:
            triangles: List of triangles

        Returns:
            Tuple of (min_bounds, max_bounds)
        """
        if not triangles:
            return Vector3D(0, 0, 0), Vector3D(0, 0, 0)

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        for triangle in triangles:
            for vertex in triangle.get_vertices():
                min_x = min(min_x, vertex.x)
                min_y = min(min_y, vertex.y)
                min_z = min(min_z, vertex.z)
                max_x = max(max_x, vertex.x)
                max_y = max(max_y, vertex.y)
                max_z = max(max_z, vertex.z)

        return Vector3D(min_x, min_y, min_z), Vector3D(max_x, max_y, max_z)

    def _periodic_gc(self, count: int, interval: int = 10000) -> None:
        """
        Perform periodic garbage collection for large files.

        Args:
            count: Current count of processed items
            interval: Interval between garbage collections
        """
        if count % interval == 0 and count > 0:
            gc.collect()

    def _check_file_exists(self, file_path: Union[str, Path]) -> Path:
        """
        Check if a file exists and return Path object.

        Args:
            file_path: Path to the file

        Returns:
            Path object

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If file is empty
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.stat().st_size == 0:
            raise ParseError("File is empty")

        return file_path

    def _create_model_stats(
        self,
        triangles: List[Triangle],
        file_size: int,
        format_type: ModelFormat,
        start_time: float,
    ) -> ModelStats:
        """
        Create model statistics.

        Args:
            triangles: List of triangles
            file_size: File size in bytes
            format_type: Model format type
            start_time: Parsing start time

        Returns:
            ModelStats object
        """
        min_bounds, max_bounds = self._calculate_bounds(triangles)
        parsing_time = time.time() - start_time

        return ModelStats(
            vertex_count=len(triangles) * 3,
            triangle_count=len(triangles),
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=file_size,
            format_type=format_type,
            parsing_time_seconds=parsing_time,
        )
