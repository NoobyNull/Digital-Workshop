"""
Progressive STL Loader with Level of Detail (LOD) Support.

This module provides progressive loading capabilities for large STL files,
enabling fast preview with increasing detail levels. It integrates with
the GPU-accelerated parser to provide smooth loading experiences.
"""

import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np  # type: ignore

from src.core.logging_config import get_logger, log_function_call
from src.parsers.base_parser import (
    Model,
    ModelFormat,
    Vector3D,
    ModelStats,
    ProgressCallback,
    LoadingState,
)
from src.parsers.stl_gpu_parser import STLGPUParser, GPUParseConfig


class LODLevel(Enum):
    """Level of Detail levels for progressive loading."""

    ULTRA_LOW = "ultra_low"  # ~1% of triangles
    LOW = "low"  # ~5% of triangles
    MEDIUM = "medium"  # ~25% of triangles
    HIGH = "high"  # ~50% of triangles
    FULL = "full"  # 100% of triangles


@dataclass
class LODConfig:
    """Configuration for Level of Detail processing."""

    levels: List[LODLevel] = None
    sampling_ratios: Dict[LODLevel, float] = None
    max_triangles_per_level: Dict[LODLevel, int] = None

    def __post_init__(self):
        if self.levels is None:
            self.levels = [
                LODLevel.ULTRA_LOW,
                LODLevel.LOW,
                LODLevel.MEDIUM,
                LODLevel.HIGH,
                LODLevel.FULL,
            ]

        if self.sampling_ratios is None:
            self.sampling_ratios = {
                LODLevel.ULTRA_LOW: 0.01,  # 1%
                LODLevel.LOW: 0.05,  # 5%
                LODLevel.MEDIUM: 0.25,  # 25%
                LODLevel.HIGH: 0.5,  # 50%
                LODLevel.FULL: 1.0,  # 100%
            }

        if self.max_triangles_per_level is None:
            self.max_triangles_per_level = {
                LODLevel.ULTRA_LOW: 10000,
                LODLevel.LOW: 50000,
                LODLevel.MEDIUM: 200000,
                LODLevel.HIGH: 1000000,
                LODLevel.FULL: float("inf"),
            }


@dataclass
class LODModel:
    """Model with multiple LOD levels."""

    base_model: Model
    lod_models: Dict[LODLevel, Model]
    current_lod: LODLevel = LODLevel.FULL
    lod_stats: Dict[LODLevel, Dict[str, Any]] = None

    def __post_init__(self):
        if self.lod_stats is None:
            self.lod_stats = {}

    @property
    def active_model(self) -> Model:
        """Get the currently active LOD model."""
        return self.lod_models.get(self.current_lod, self.base_model)

    def set_lod_level(self, level: LODLevel) -> None:
        """Set the active LOD level."""
        if level in self.lod_models:
            self.current_lod = level
        else:
            raise ValueError(f"LOD level {level} not available")

    def get_lod_info(self) -> Dict[str, Any]:
        """Get information about available LOD levels."""
        return {
            "current_level": self.current_lod.value,
            "available_levels": [level.value for level in self.lod_models.keys()],
            "level_stats": self.lod_stats,
        }


class ProgressiveSTLLoader:
    """
    Progressive loader for STL files with LOD support.

    Provides fast preview loading with increasing detail levels,
    enabling responsive UI during large file processing.
    """

    def __init__(
        self,
        config: Optional[LODConfig] = None,
        gpu_config: Optional[GPUParseConfig] = None,
    ):
        """Initialize progressive STL loader."""
        self.config = config or LODConfig()
        self.gpu_config = gpu_config or GPUParseConfig()
        self.logger = get_logger(__name__)

        # GPU parser instance
        self.gpu_parser = STLGPUParser(self.gpu_config)

        # Threading support
        self._lock = threading.RLock()
        self._cancel_event = threading.Event()

        # LOD cache
        self._lod_cache: Dict[str, LODModel] = {}

    @log_function_call
    def load_progressive(
        self,
        file_path: str,
        progress_callback: Optional[ProgressCallback] = None,
        lod_callback: Optional[Callable[[LODLevel, Model], None]] = None,
    ) -> LODModel:
        """
        Load STL file with progressive LOD levels.

        Args:
            file_path: Path to STL file
            progress_callback: Optional progress callback
            lod_callback: Optional callback for each LOD level completion

        Returns:
            LODModel with multiple detail levels
        """
        file_path_obj = Path(file_path)
        cache_key = str(file_path_obj.resolve())

        with self._lock:
            # Check cache first
            if cache_key in self._lod_cache:
                self.logger.info(f"Using cached LOD model for {file_path}")
                return self._lod_cache[cache_key]

        self._cancel_event.clear()
        start_time = time.time()

        try:
            # Phase 1: Quick metadata load
            if progress_callback:
                progress_callback.report(5.0, "Loading file metadata...")

            # Get basic file info
            triangle_count = self._get_triangle_count(file_path_obj)
            file_size = file_path_obj.stat().st_size

            self.logger.info(
                f"Progressive loading: {triangle_count} triangles ({file_size} bytes)"
            )

            # Phase 2: Load lowest LOD first for immediate preview
            lod_models = {}
            total_progress = 10.0

            for i, lod_level in enumerate(self.config.levels):
                if self._cancel_event.is_set():
                    raise Exception("Loading was cancelled")

                level_start = time.time()

                # Calculate target triangle count for this LOD level
                target_count = self._calculate_lod_triangle_count(
                    triangle_count, lod_level
                )

                if progress_callback:
                    progress_pct = total_progress + (i / len(self.config.levels)) * 80.0
                    progress_callback.report(
                        progress_pct,
                        f"Loading {lod_level.value} detail ({target_count:,} triangles)...",
                    )

                # Load this LOD level
                lod_model = self._load_lod_level(
                    file_path_obj, lod_level, target_count, triangle_count
                )

                lod_models[lod_level] = lod_model

                # Calculate stats for this level
                level_time = time.time() - level_start
                lod_stats = {
                    "triangle_count": lod_model.stats.triangle_count,
                    "load_time": level_time,
                    "compression_ratio": lod_model.stats.triangle_count
                    / triangle_count,
                    "file_size_mb": file_size / (1024 * 1024),
                }

                # Notify callback if provided
                if lod_callback:
                    lod_callback(lod_level, lod_model)

                self.logger.info(
                    f"Loaded {lod_level.value} LOD: {lod_model.stats.triangle_count:,} triangles "
                    f"in {level_time:.2f}s"
                )

            # Phase 3: Create full LOD model
            base_model = lod_models[LODLevel.FULL]

            lod_model = LODModel(
                base_model=base_model,
                lod_models=lod_models,
                current_lod=LODLevel.ULTRA_LOW,  # Start with lowest detail
                lod_stats={
                    level: {
                        "triangle_count": model.stats.triangle_count,
                        "load_time": 0.0,  # Would need to track individually
                        "compression_ratio": model.stats.triangle_count
                        / triangle_count,
                        "file_size_mb": file_size / (1024 * 1024),
                    }
                    for level, model in lod_models.items()
                },
            )

            # Cache the result
            with self._lock:
                self._lod_cache[cache_key] = lod_model

            total_time = time.time() - start_time

            if progress_callback:
                progress_callback.report(100.0, "Progressive loading completed")

            self.logger.info(
                f"Progressive loading completed: {len(lod_models)} LOD levels "
                f"in {total_time:.2f}s"
            )

            return lod_model

        except Exception as e:
            self.logger.error(f"Progressive loading failed: {e}")
            raise

    def _get_triangle_count(self, file_path: Path) -> int:
        """Get triangle count from STL file."""
        return self.gpu_parser._get_triangle_count(file_path)

    def _calculate_lod_triangle_count(
        self, total_count: int, lod_level: LODLevel
    ) -> int:
        """Calculate target triangle count for LOD level."""
        ratio = self.config.sampling_ratios[lod_level]
        max_count = self.config.max_triangles_per_level[lod_level]

        target_count = int(total_count * ratio)
        return min(target_count, max_count)

    def _load_lod_level(
        self, file_path: Path, lod_level: LODLevel, target_count: int, total_count: int
    ) -> Model:
        """Load a specific LOD level."""
        if lod_level == LODLevel.FULL:
            # Load full model
            return self.gpu_parser._parse_file_internal(str(file_path))
        else:
            # Load sampled model
            return self._load_sampled_model(file_path, target_count, total_count)

    def _load_sampled_model(
        self, file_path: Path, target_count: int, total_count: int
    ) -> Model:
        """Load a sampled version of the model for LOD."""
        # For now, use simple uniform sampling
        # In a full implementation, this would use more sophisticated sampling
        # like curvature-based or importance sampling

        # Load full model first (this could be optimized)
        full_model = self.gpu_parser._parse_file_internal(str(file_path))

        if full_model.vertex_array is None or full_model.normal_array is None:
            # Fallback for models without arrays
            return self._create_sampled_model_from_triangles(
                full_model, target_count, total_count
            )

        # Sample from vertex/normal arrays
        sample_indices = self._generate_sample_indices(total_count, target_count)

        sampled_vertices = full_model.vertex_array[sample_indices].copy()
        sampled_normals = full_model.normal_array[sample_indices].copy()

        # Update statistics
        sampled_stats = ModelStats(
            vertex_count=target_count * 3,
            triangle_count=target_count,
            min_bounds=full_model.stats.min_bounds,
            max_bounds=full_model.stats.max_bounds,
            file_size_bytes=full_model.stats.file_size_bytes,
            format_type=full_model.stats.format_type,
            parsing_time_seconds=full_model.stats.parsing_time_seconds,
        )

        # Create sampled model
        sampled_model = Model(
            header=f"{full_model.header} (LOD: {target_count}/{total_count} triangles)",
            triangles=[],
            stats=sampled_stats,
            format_type=full_model.format_type,
            loading_state=LoadingState.LOW_RES_GEOMETRY,
            file_path=full_model.file_path,
            vertex_array=sampled_vertices,
            normal_array=sampled_normals,
        )

        return sampled_model

    def _generate_sample_indices(
        self, total_count: int, target_count: int
    ) -> np.ndarray:
        """Generate sampling indices for LOD creation."""
        if target_count >= total_count:
            return np.arange(total_count, dtype=np.int32)

        # Simple uniform sampling
        step = total_count / target_count
        indices = np.arange(0, total_count, step, dtype=np.int32)
        return indices[:target_count]

    def _create_sampled_model_from_triangles(
        self, full_model: Model, target_count: int, total_count: int
    ) -> Model:
        """Create sampled model from Triangle objects (fallback)."""
        if not full_model.triangles:
            return full_model

        # Sample triangles
        sample_indices = self._generate_sample_indices(total_count, target_count)
        sampled_triangles = [full_model.triangles[i] for i in sample_indices]

        # Update statistics
        sampled_stats = ModelStats(
            vertex_count=target_count * 3,
            triangle_count=target_count,
            min_bounds=full_model.stats.min_bounds,
            max_bounds=full_model.stats.max_bounds,
            file_size_bytes=full_model.stats.file_size_bytes,
            format_type=full_model.stats.format_type,
            parsing_time_seconds=full_model.stats.parsing_time_seconds,
        )

        # Create sampled model
        sampled_model = Model(
            header=f"{full_model.header} (LOD: {target_count}/{total_count} triangles)",
            triangles=sampled_triangles,
            stats=sampled_stats,
            format_type=full_model.format_type,
            loading_state=LoadingState.LOW_RES_GEOMETRY,
            file_path=full_model.file_path,
        )

        return sampled_model

    @log_function_call
    def preload_lod_level(
        self,
        file_path: str,
        lod_level: LODLevel,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Model:
        """
        Preload a specific LOD level for a file.

        Args:
            file_path: Path to STL file
            lod_level: LOD level to preload
            progress_callback: Optional progress callback

        Returns:
            Model for the specified LOD level
        """
        file_path_obj = Path(file_path)
        cache_key = str(file_path_obj.resolve())

        with self._lock:
            # Check if already cached
            if cache_key in self._lod_cache:
                lod_model = self._lod_cache[cache_key]
                if lod_level in lod_model.lod_models:
                    return lod_model.lod_models[lod_level]

            # Load specific level
            triangle_count = self._get_triangle_count(file_path_obj)
            target_count = self._calculate_lod_triangle_count(triangle_count, lod_level)

            if progress_callback:
                progress_callback.report(0.0, f"Preloading {lod_level.value} detail...")

            model = self._load_lod_level(
                file_path_obj, lod_level, target_count, triangle_count
            )

            if progress_callback:
                progress_callback.report(
                    100.0, f"{lod_level.value.capitalize()} detail loaded"
                )

            return model

    def cancel_loading(self) -> None:
        """Cancel ongoing progressive loading."""
        self._cancel_event.set()
        self.gpu_parser.cancel_parsing()
        self.logger.info("Progressive loading cancelled")

    def clear_cache(self) -> None:
        """Clear the LOD cache."""
        with self._lock:
            self._lod_cache.clear()
            self.logger.info("LOD cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_models = len(self._lod_cache)
            total_lod_levels = sum(
                len(model.lod_models) for model in self._lod_cache.values()
            )

            return {
                "cached_models": total_models,
                "total_lod_levels": total_lod_levels,
                "cache_size_mb": self._estimate_cache_size_mb(),
            }

    def _estimate_cache_size_mb(self) -> float:
        """Estimate cache size in MB."""
        total_size = 0
        for lod_model in self._lod_cache.values():
            for model in lod_model.lod_models.values():
                # Rough estimate: 50 bytes per triangle
                total_size += model.stats.triangle_count * 50

        return total_size / (1024 * 1024)
