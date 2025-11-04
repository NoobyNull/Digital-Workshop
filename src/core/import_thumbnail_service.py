"""
Import Thumbnail Service for 3D Model Import Process.

Provides hash-based thumbnail generation with configurable storage locations,
cache management, and progress tracking for the import workflow.

Features:
- Integration with existing ThumbnailGenerator
- Hash-based thumbnail naming using FastHasher
- Configurable storage locations (AppData or custom)
- Thumbnail cache management and cleanup
- Progress tracking for batch operations
- Comprehensive JSON logging
- Memory-efficient processing
- Cancellation support
"""

import json
import logging
import time
import gc
from pathlib import Path
from typing import Optional, Callable, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.logging_config import get_logger
from src.core.thumbnail_components import ThumbnailGenerator
from src.core.thumbnail_components.thumbnail_resizer import ThumbnailResizer
from src.core.fast_hasher import FastHasher
from src.core.cancellation_token import CancellationToken


class StorageLocation(Enum):
    """Thumbnail storage location options."""

    APPDATA = "appdata"
    CUSTOM = "custom"


@dataclass
class ThumbnailGenerationResult:
    """Result of a thumbnail generation operation."""

    file_path: str
    file_hash: str
    thumbnail_path: Optional[Path]
    generation_time: float
    success: bool
    error: Optional[str] = None
    cached: bool = False


@dataclass
class ThumbnailBatchResult:
    """Result of a batch thumbnail generation operation."""

    total_files: int
    successful: int
    failed: int
    cached: int
    total_time: float
    results: List[ThumbnailGenerationResult]


class ImportThumbnailService:
    """
    Service for generating thumbnails during the 3D model import process.

    Integrates with the existing ThumbnailGenerator to provide:
    - Hash-based thumbnail naming for deduplication
    - Configurable storage locations (AppData or custom directory)
    - Thumbnail cache management to avoid redundant generation
    - Progress tracking for batch operations
    - Cancellation support for long operations
    - Comprehensive JSON logging for quality standards

    Performance targets:
    - Thumbnail generation: < 2 seconds per model
    - Cache lookup: < 10ms per file
    - Memory usage: Stable during batch operations

    Example:
        >>> service = ImportThumbnailService()
        >>> result = service.generate_thumbnail("model.stl", "abc123hash")
        >>> if result.success:
        ...     print(f"Thumbnail: {result.thumbnail_path}")
    """

    # Default thumbnail specifications
    DEFAULT_THUMBNAIL_SIZE = (1280, 1280)
    DEFAULT_THUMBNAIL_SIZES = {
        "small": (128, 128),
        "medium": (256, 256),
        "large": (512, 512),
        "xlarge": (1280, 1280),
    }

    def __init__(
        self,
        storage_location: StorageLocation = StorageLocation.APPDATA,
        custom_storage_path: Optional[str] = None,
        settings_manager=None,
    ):
        """
        Initialize the import thumbnail service.

        Args:
            storage_location: Where to store thumbnails (APPDATA or CUSTOM)
            custom_storage_path: Custom directory path if storage_location is CUSTOM
            settings_manager: Optional settings manager for thumbnail preferences
        """
        self.logger = get_logger(__name__)
        self.storage_location = storage_location
        self.custom_storage_path = custom_storage_path
        self.settings_manager = settings_manager

        # Initialize core components
        self.thumbnail_generator = ThumbnailGenerator(settings_manager=settings_manager)
        self.thumbnail_resizer = ThumbnailResizer()
        self.hasher = FastHasher()

        # Thumbnail cache: hash -> thumbnail_path
        self._thumbnail_cache: Dict[str, Path] = {}

        # Determine storage directory
        self._storage_dir = self._initialize_storage_directory()

        # Statistics
        self._stats = {
            "thumbnails_generated": 0,
            "thumbnails_cached": 0,
            "total_generation_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        self._log_json(
            "service_initialized",
            {
                "storage_location": storage_location.value,
                "storage_dir": str(self._storage_dir),
                "thumbnail_size": self.DEFAULT_THUMBNAIL_SIZE,
            },
        )

    def _log_json(self, event: str, data: dict) -> None:
        """Log event in JSON format as required by quality standards."""
        # Only log if DEBUG level is enabled to reduce verbosity
        if not self.logger.isEnabledFor(logging.DEBUG):
            return

        log_entry = {"event": event, "timestamp": time.time(), **data}
        self.logger.debug(json.dumps(log_entry))

    def _initialize_storage_directory(self) -> Path:
        """
        Initialize and validate the thumbnail storage directory.

        Returns:
            Path to thumbnail storage directory
        """
        if self.storage_location == StorageLocation.CUSTOM:
            if not self.custom_storage_path:
                raise ValueError("Custom storage path required when storage_location is CUSTOM")
            storage_dir = Path(self.custom_storage_path)
        else:
            # Use AppData for default storage
            import os

            appdata = os.getenv("APPDATA") or os.path.expanduser("~/.config")
            storage_dir = Path(appdata) / "3DModelManager" / "thumbnails"

        # Create directory if it doesn't exist
        storage_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Thumbnail storage initialized: {storage_dir}")
        return storage_dir

    def get_thumbnail_path(self, file_hash: str) -> Path:
        """
        Get the expected thumbnail path for a given file hash.

        Args:
            file_hash: Hash of the model file

        Returns:
            Path where the thumbnail should be stored
        """
        return self._storage_dir / f"{file_hash}.png"

    def is_thumbnail_cached(self, file_hash: str) -> bool:
        """
        Check if a thumbnail already exists for the given hash.

        Args:
            file_hash: Hash of the model file

        Returns:
            True if thumbnail exists in cache or on disk
        """
        # Check memory cache first
        if file_hash in self._thumbnail_cache:
            cached_path = self._thumbnail_cache[file_hash]
            if cached_path.exists():
                self._stats["cache_hits"] += 1
                return True
            else:
                # Remove stale cache entry
                del self._thumbnail_cache[file_hash]

        # Check disk
        thumbnail_path = self.get_thumbnail_path(file_hash)
        if thumbnail_path.exists():
            # Add to memory cache
            self._thumbnail_cache[file_hash] = thumbnail_path
            self._stats["cache_hits"] += 1
            return True

        self._stats["cache_misses"] += 1
        return False

    def generate_thumbnail(
        self,
        model_path: str,
        file_hash: str,
        background: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None,
        material: Optional[str] = None,
        force_regenerate: bool = False,
    ) -> ThumbnailGenerationResult:
        """
        Generate a thumbnail for a 3D model with hash-based naming.

        Args:
            model_path: Path to the 3D model file
            file_hash: Hash of the model (from FastHasher)
            background: Optional background color or image path
            size: Optional thumbnail size (width, height)
            material: Optional material name to apply
            force_regenerate: If True, regenerate even if cached

        Returns:
            ThumbnailGenerationResult with generation details
        """
        start_time = time.time()
        model_name = Path(model_path).name

        try:
            # Check if thumbnail already exists (unless forced)
            if not force_regenerate and self.is_thumbnail_cached(file_hash):
                cached_path = self.get_thumbnail_path(file_hash)
                generation_time = time.time() - start_time

                self._log_json(
                    "thumbnail_cached",
                    {
                        "file": model_name,
                        "hash": file_hash[:16] + "...",
                        "path": str(cached_path),
                        "lookup_time_ms": round(generation_time * 1000, 2),
                    },
                )

                self._stats["thumbnails_cached"] += 1

                return ThumbnailGenerationResult(
                    file_path=model_path,
                    file_hash=file_hash,
                    thumbnail_path=cached_path,
                    generation_time=generation_time,
                    success=True,
                    cached=True,
                )

            # Generate new thumbnail
            self._log_json(
                "thumbnail_generation_started",
                {
                    "file": model_name,
                    "hash": file_hash[:16] + "...",
                    "force_regenerate": force_regenerate,
                },
            )

            # Always generate at 1280x1280 (high quality)
            # Then resize to other sizes using Pillow
            thumbnail_path = self.thumbnail_generator.generate_thumbnail(
                model_path=model_path,
                file_hash=file_hash,
                output_dir=self._storage_dir,
                background=background,
                size=self.DEFAULT_THUMBNAIL_SIZE,  # Always 1280x1280
                material=material,
                force_regenerate=force_regenerate,
            )

            generation_time = time.time() - start_time

            if thumbnail_path:
                # Resize to other sizes using Pillow (fast, efficient)
                resized_paths = self.thumbnail_resizer.resize_and_save(
                    source_image_path=thumbnail_path,
                    file_hash=file_hash,
                    output_dir=self._storage_dir,
                )

                # Add to cache (store the xlarge/1280 version)
                self._thumbnail_cache[file_hash] = thumbnail_path
                self._stats["thumbnails_generated"] += 1
                self._stats["total_generation_time"] += generation_time

                self._log_json(
                    "thumbnail_generated",
                    {
                        "file": model_name,
                        "hash": file_hash[:16] + "...",
                        "path": str(thumbnail_path),
                        "size": self.DEFAULT_THUMBNAIL_SIZE,
                        "resized_sizes": list(resized_paths.keys()),
                        "generation_time_seconds": round(generation_time, 3),
                    },
                )

                return ThumbnailGenerationResult(
                    file_path=model_path,
                    file_hash=file_hash,
                    thumbnail_path=thumbnail_path,
                    generation_time=generation_time,
                    success=True,
                    cached=False,
                )
            else:
                error_msg = "Thumbnail generation returned None"
                self.logger.error(f"{error_msg} for {model_name}")

                return ThumbnailGenerationResult(
                    file_path=model_path,
                    file_hash=file_hash,
                    thumbnail_path=None,
                    generation_time=generation_time,
                    success=False,
                    error=error_msg,
                )

        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Thumbnail generation failed: {e}"

            self.logger.error(f"{error_msg} for {model_name}", exc_info=True)
            self._log_json(
                "thumbnail_generation_failed",
                {
                    "file": model_name,
                    "hash": file_hash[:16] + "...",
                    "error": str(e),
                    "generation_time_seconds": round(generation_time, 3),
                },
            )

            return ThumbnailGenerationResult(
                file_path=model_path,
                file_hash=file_hash,
                thumbnail_path=None,
                generation_time=generation_time,
                success=False,
                error=error_msg,
            )
        finally:
            # Force garbage collection to free VTK resources
            gc.collect()

    def generate_thumbnails_batch(
        self,
        file_info_list: List[Tuple[str, str]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
        background: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None,
        material: Optional[str] = None,
    ) -> ThumbnailBatchResult:
        """
        Generate thumbnails for multiple files with progress tracking.

        Args:
            file_info_list: List of (model_path, file_hash) tuples
            progress_callback: Optional callback(completed, total, current_file)
            cancellation_token: Optional token to check for cancellation
            background: Optional background color or image path
            size: Optional thumbnail size
            material: Optional material name

        Returns:
            ThumbnailBatchResult with batch generation details
        """
        start_time = time.time()
        total_files = len(file_info_list)
        results = []

        self._log_json(
            "batch_generation_started",
            {"total_files": total_files, "storage_dir": str(self._storage_dir)},
        )

        for idx, (model_path, file_hash) in enumerate(file_info_list):
            # Check for cancellation
            if cancellation_token is not None and cancellation_token.is_cancelled():
                self._log_json(
                    "batch_generation_cancelled",
                    {
                        "completed": idx,
                        "total": total_files,
                        "percent_complete": round((idx / total_files) * 100, 1),
                    },
                )
                break

            # Report progress
            if progress_callback:
                progress_callback(idx, total_files, Path(model_path).name)

            # Generate thumbnail
            result = self.generate_thumbnail(
                model_path=model_path,
                file_hash=file_hash,
                background=background,
                size=size,
                material=material,
            )
            results.append(result)

        # Final progress report
        if progress_callback:
            progress_callback(len(results), total_files, "Batch complete")

        batch_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        cached = sum(1 for r in results if r.cached)

        self._log_json(
            "batch_generation_completed",
            {
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "cached": cached,
                "generated": successful - cached,
                "time_seconds": round(batch_time, 3),
                "avg_time_per_file": (round(batch_time / total_files, 3) if total_files > 0 else 0),
            },
        )

        return ThumbnailBatchResult(
            total_files=total_files,
            successful=successful,
            failed=failed,
            cached=cached,
            total_time=batch_time,
            results=results,
        )

    def cleanup_orphaned_thumbnails(self, valid_hashes: List[str]) -> Dict[str, int]:
        """
        Remove thumbnails that no longer have corresponding model files.

        Args:
            valid_hashes: List of hashes for models that should have thumbnails

        Returns:
            Dictionary with cleanup statistics
        """
        start_time = time.time()
        valid_hash_set = set(valid_hashes)

        removed_count = 0
        kept_count = 0
        error_count = 0

        self._log_json(
            "cleanup_started",
            {
                "storage_dir": str(self._storage_dir),
                "valid_hashes": len(valid_hash_set),
            },
        )

        try:
            # Iterate through all PNG files in storage directory
            for thumbnail_path in self._storage_dir.glob("*.png"):
                try:
                    # Extract hash from filename
                    file_hash = thumbnail_path.stem

                    if file_hash not in valid_hash_set:
                        # Orphaned thumbnail - remove it
                        thumbnail_path.unlink()
                        removed_count += 1

                        # Remove from cache if present
                        self._thumbnail_cache.pop(file_hash, None)
                    else:
                        kept_count += 1

                except Exception as e:
                    self.logger.warning(f"Error processing {thumbnail_path}: {e}")
                    error_count += 1

            cleanup_time = time.time() - start_time

            self._log_json(
                "cleanup_completed",
                {
                    "removed": removed_count,
                    "kept": kept_count,
                    "errors": error_count,
                    "time_seconds": round(cleanup_time, 3),
                },
            )

            return {
                "removed": removed_count,
                "kept": kept_count,
                "errors": error_count,
                "time_seconds": cleanup_time,
            }

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}", exc_info=True)
            return {
                "removed": removed_count,
                "kept": kept_count,
                "errors": error_count + 1,
                "time_seconds": time.time() - start_time,
            }

    def clear_cache(self) -> None:
        """Clear the in-memory thumbnail cache."""
        cache_size = len(self._thumbnail_cache)
        self._thumbnail_cache.clear()

        self._log_json("cache_cleared", {"entries_cleared": cache_size})

    def get_cache_statistics(self) -> Dict[str, any]:
        """
        Get current cache and service statistics.

        Returns:
            Dictionary with cache and generation statistics
        """
        stats = {
            "cache_size": len(self._thumbnail_cache),
            "storage_dir": str(self._storage_dir),
            "thumbnails_generated": self._stats["thumbnails_generated"],
            "thumbnails_cached": self._stats["thumbnails_cached"],
            "total_generation_time": round(self._stats["total_generation_time"], 3),
            "avg_generation_time": round(
                self._stats["total_generation_time"] / max(1, self._stats["thumbnails_generated"]),
                3,
            ),
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "cache_hit_rate": round(
                self._stats["cache_hits"]
                / max(1, self._stats["cache_hits"] + self._stats["cache_misses"])
                * 100,
                2,
            ),
        }

        self._log_json("cache_statistics", stats)
        return stats

    def get_storage_directory(self) -> Path:
        """
        Get the current thumbnail storage directory.

        Returns:
            Path to thumbnail storage directory
        """
        return self._storage_dir

    def set_storage_directory(
        self, storage_location: StorageLocation, custom_path: Optional[str] = None
    ) -> None:
        """
        Change the thumbnail storage directory.

        Args:
            storage_location: New storage location type
            custom_path: Custom directory path if storage_location is CUSTOM
        """
        old_dir = self._storage_dir
        self.storage_location = storage_location
        self.custom_storage_path = custom_path

        self._storage_dir = self._initialize_storage_directory()

        # Clear cache since paths have changed
        self.clear_cache()

        self._log_json(
            "storage_directory_changed",
            {
                "old_dir": str(old_dir),
                "new_dir": str(self._storage_dir),
                "storage_location": storage_location.value,
            },
        )

    def verify_thumbnail(self, file_hash: str) -> bool:
        """
        Verify that a thumbnail exists and is valid.

        Args:
            file_hash: Hash of the model file

        Returns:
            True if thumbnail exists and is valid
        """
        thumbnail_path = self.get_thumbnail_path(file_hash)

        if not thumbnail_path.exists():
            return False

        try:
            # Check if file is readable and not empty
            if thumbnail_path.stat().st_size == 0:
                self.logger.warning(f"Thumbnail is empty: {thumbnail_path}")
                return False

            # Basic PNG header validation
            with open(thumbnail_path, "rb") as f:
                header = f.read(8)
                if header != b"\x89PNG\r\n\x1a\n":
                    self.logger.warning(f"Invalid PNG header: {thumbnail_path}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error verifying thumbnail {thumbnail_path}: {e}")
            return False

    def get_thumbnail_by_size(self, file_hash: str, size: str = "xlarge") -> Optional[Path]:
        """
        Get thumbnail path for a specific size.

        Args:
            file_hash: Hash of the model file
            size: Size name ('xlarge', 'large', 'small')

        Returns:
            Path to the thumbnail file, or None if not found
        """
        path = self.thumbnail_resizer.get_thumbnail_path(
            file_hash=file_hash, output_dir=self._storage_dir, size=size
        )

        if path.exists():
            return path

        return None
