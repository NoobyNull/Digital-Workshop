"""
Model cache system for Digital Workshop.

This module provides an intelligent caching system for 3D models with adaptive
memory management, LRU eviction, and progressive loading capabilities.
"""

import gc
import pickle
import sqlite3
import threading
import time
import xxhash
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any

from .logging_config import get_logger
from .performance_monitor import get_performance_monitor, PerformanceLevel
from .data_structures import Model


class CacheLevel(Enum):
    """Cache levels for different model representations."""

    METADATA = "metadata"  # Just file metadata and statistics
    GEOMETRY_LOW = "geometry_low"  # Low-resolution geometry
    GEOMETRY_FULL = "geometry_full"  # Full-resolution geometry


@dataclass
class CacheEntry:
    """Entry in the model cache."""

    file_path: str
    file_hash: str
    cache_level: CacheLevel
    data: Any
    size_bytes: int
    access_count: int
    last_access_time: float
    creation_time: float
    memory_only: bool = False

    def update_access(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_access_time = time.time()


@dataclass
class CacheStats:
    """Cache statistics."""

    total_entries: int = 0
    total_size_bytes: int = 0
    memory_entries: int = 0
    memory_size_bytes: int = 0
    disk_entries: int = 0
    disk_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0


class ModelCache:
    """
    Intelligent model cache with adaptive memory management.

    Features:
    - Multi-level caching (metadata, low-res, full-res)
    - LRU eviction policy
    - Adaptive cache sizing based on system capabilities
    - Disk-based overflow caching
    - Progressive loading support
    - Thread-safe operations
    """

    def __init__(
        self, cache_dir: str = "cache", max_memory_mb: Optional[float] = None
    ) -> None:
        """
        Initialize the model cache.

        Args:
            cache_dir: Directory for disk cache
            max_memory_mb: Maximum memory usage in MB (auto-detected if None)
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing model cache")

        # Get performance profile for adaptive settings
        self.perf_monitor = get_performance_monitor()
        perf_profile = self.perf_monitor.get_performance_profile()

        # Cache configuration - use user-specific directory for installed app
        if cache_dir == "cache":
            # Default to user local app data directory
            import os

            app_data = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
            )
            from .path_manager import get_cache_directory

            self.cache_dir = get_cache_directory()
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Memory limits - check for user override first
        if max_memory_mb is None:
            # Check if user has set a manual override in config
            try:
                import psutil
                from .application_config import ApplicationConfig

                config = ApplicationConfig.get_default()

                if config.use_manual_memory_override:
                    # Calculate cache limit as percentage of total system RAM
                    total_system_memory_mb = int(
                        psutil.virtual_memory().total / (1024**2)
                    )
                    cache_limit_mb = int(
                        total_system_memory_mb
                        * (config.manual_cache_limit_percent / 100)
                    )
                    self.max_memory_bytes = cache_limit_mb * 1024 * 1024
                    self.logger.info(
                        f"Using manual cache limit: {config.manual_cache_limit_percent}% of "
                        f"{total_system_memory_mb}MB system RAM = {cache_limit_mb}MB"
                    )
                else:
                    # Use adaptive cache size from performance profile
                    self.max_memory_bytes = (
                        perf_profile.recommended_cache_size_mb * 1024 * 1024
                    )
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                self.logger.warning(
                    "Failed to check config override, using adaptive: %s", e
                )
                self.max_memory_bytes = (
                    perf_profile.recommended_cache_size_mb * 1024 * 1024
                )
        else:
            self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # Cache storage
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache_db = str(self.cache_dir / "cache.db")
        self._init_disk_cache()

        # Cache state
        self.current_memory_bytes = 0
        self.access_order = []  # For LRU tracking
        self.lock = threading.RLock()

        # Statistics
        self.stats = CacheStats()

        # Adaptive settings based on performance level
        # Disk cache is 2x the memory cache size
        self.max_disk_cache_mb = (self.max_memory_bytes / (1024 * 1024)) * 2
        self.compression_enabled = (
            perf_profile.performance_level != PerformanceLevel.ULTRA
        )
        self.aggressive_eviction = (
            perf_profile.performance_level == PerformanceLevel.MINIMAL
        )

        self.logger.info(
            f"Model cache initialized: {self.max_memory_bytes / (1024*1024):.1f}MB memory limit, "
            f"{self.max_disk_cache_mb:.1f}MB disk limit, "
            f"compression: {self.compression_enabled}"
        )

    def _init_disk_cache(self) -> None:
        """Initialize the disk cache database."""
        try:
            with sqlite3.connect(self.disk_cache_db) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        file_path TEXT PRIMARY KEY,
                        file_hash TEXT NOT NULL,
                        cache_level TEXT NOT NULL,
                        data BLOB NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        access_count INTEGER DEFAULT 1,
                        last_access_time REAL NOT NULL,
                        creation_time REAL NOT NULL
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_file_hash ON cache_entries(file_hash)
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_cache_level ON cache_entries(cache_level)
                """
                )

                conn.commit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize disk cache: %s", str(e))
            raise

    def _generate_file_hash(self, file_path: str) -> str:
        """
        Generate xxHash128 for file path and modification time (cache key).

        Args:
            file_path: Path to the file

        Returns:
            Hash string (32 hex characters)
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                hasher = xxhash.xxh128()
                hasher.update(file_path.encode())
                return hasher.hexdigest()

            # Use file path, size, and modification time for hash
            stat = path_obj.stat()
            hash_input = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
            hasher = xxhash.xxh128()
            hasher.update(hash_input.encode())
            return hasher.hexdigest()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to generate file hash: %s", str(e))
            hasher = xxhash.xxh128()
            hasher.update(file_path.encode())
            return hasher.hexdigest()

    def _estimate_data_size(self, data: Any) -> int:
        """
        Estimate the size of data in bytes.

        Args:
            data: Data to estimate size for

        Returns:
            Estimated size in bytes
        """
        try:
            if isinstance(data, Model):
                # Base estimate for Triangle objects
                size = len(data.triangles) * 50 + 100  # Rough estimate

                # Account for array-based geometry if present
                va = getattr(data, "vertex_array", None)
                na = getattr(data, "normal_array", None)
                for arr in (va, na):
                    if arr is not None:
                        nbytes = getattr(arr, "nbytes", None)
                        if isinstance(nbytes, (int, float)):
                            size += int(nbytes)
                        else:
                            # Fallback: approximate via size * itemsize if available
                            try:
                                size += int(getattr(arr, "size", 0)) * int(
                                    getattr(arr, "itemsize", 4)
                                )
                            except Exception:
                                pass
                return size
            else:
                # Use pickle size as estimate
                return len(pickle.dumps(data))

        except Exception:
            return 1024  # Default 1KB estimate

    def _serialize_data(self, data: Any) -> bytes:
        """
        Serialize data for storage.

        Args:
            data: Data to serialize

        Returns:
            Serialized data
        """
        try:
            if self.compression_enabled:
                # Use pickle with highest protocol for efficiency
                return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to serialize data: %s", str(e))
            raise

    def _deserialize_data(self, data: bytes) -> Any:
        """
        Deserialize data from storage.

        Args:
            data: Serialized data

        Returns:
            Deserialized data
        """
        try:
            return pickle.loads(data)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to deserialize data: %s", str(e))
            raise

    def _evict_memory_entries(self, required_bytes: int) -> None:
        """
        Evict entries from memory cache to make room.

        Args:
            required_bytes: Number of bytes needed
        """
        bytes_freed = 0
        entries_to_evict = []

        # Sort by last access time (LRU)
        sorted_entries = sorted(
            self.memory_cache.items(), key=lambda x: x[1].last_access_time
        )

        for key, entry in sorted_entries:
            if bytes_freed >= required_bytes:
                break

            # Don't evict if recently accessed (unless aggressive mode)
            if not self.aggressive_eviction:
                time_since_access = time.time() - entry.last_access_time
                if time_since_access < 300:  # 5 minutes
                    continue

            entries_to_evict.append(key)
            bytes_freed += entry.size_bytes

        # Evict entries
        for key in entries_to_evict:
            entry = self.memory_cache.pop(key)
            self.current_memory_bytes -= entry.size_bytes

            # Move to disk cache if not already there
            if not entry.memory_only:
                self._store_to_disk_cache(key, entry)

            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)

            self.stats.eviction_count += 1

        if entries_to_evict:
            self.logger.debug(
                "Evicted %s entries, freed {bytes_freed} bytes", len(entries_to_evict)
            )

    def _store_to_disk_cache(self, key: str, entry: CacheEntry) -> None:
        """
        Store entry to disk cache.

        Args:
            key: Cache key
            entry: Cache entry
        """
        try:
            serialized_data = self._serialize_data(entry.data)

            with sqlite3.connect(self.disk_cache_db) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                    (file_path, file_hash, cache_level, data, size_bytes,
                     access_count, last_access_time, creation_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.file_path,
                        entry.file_hash,
                        entry.cache_level.value,
                        serialized_data,
                        entry.size_bytes,
                        entry.access_count,
                        entry.last_access_time,
                        entry.creation_time,
                    ),
                )
                conn.commit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to store to disk cache: %s", str(e))

    def _load_from_disk_cache(
        self, file_path: str, cache_level: CacheLevel
    ) -> Optional[CacheEntry]:
        """
        Load entry from disk cache.

        Args:
            file_path: File path
            cache_level: Cache level

        Returns:
            Cache entry if found, None otherwise
        """
        try:
            with sqlite3.connect(self.disk_cache_db) as conn:
                cursor = conn.execute(
                    """
                    SELECT file_hash, data, size_bytes, access_count,
                           last_access_time, creation_time
                    FROM cache_entries
                    WHERE file_path = ? AND cache_level = ?
                    """,
                    (file_path, cache_level.value),
                )

                row = cursor.fetchone()
                if row:
                    (
                        file_hash,
                        data,
                        size_bytes,
                        access_count,
                        last_access_time,
                        creation_time,
                    ) = row

                    deserialized_data = self._deserialize_data(data)

                    return CacheEntry(
                        file_path=file_path,
                        file_hash=file_hash,
                        cache_level=cache_level,
                        data=deserialized_data,
                        size_bytes=size_bytes,
                        access_count=access_count,
                        last_access_time=last_access_time,
                        creation_time=creation_time,
                        memory_only=False,
                    )

                return None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load from disk cache: %s", str(e))
            return None

    def _make_space_in_memory(self, required_bytes: int) -> bool:
        """
        Make space in memory cache for new entry.

        Args:
            required_bytes: Number of bytes needed

        Returns:
            True if space was made, False if not possible
        """
        # Check if we need to evict
        if self.current_memory_bytes + required_bytes <= self.max_memory_bytes:
            return True

        # Evict entries to make space
        self._evict_memory_entries(required_bytes)

        # Check if we have enough space now
        return self.current_memory_bytes + required_bytes <= self.max_memory_bytes

    def get(self, file_path: str, cache_level: CacheLevel) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            file_path: File path
            cache_level: Cache level

        Returns:
            Cached data or None if not found
        """
        with self.lock:
            key = f"{file_path}:{cache_level.value}"

            # Check memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                entry.update_access()

                # Update access order for LRU
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

                self.stats.hit_count += 1
                self.logger.debug(
                    "Cache hit (memory): %s [{cache_level.value}]", file_path
                )
                return entry.data

            # Check disk cache
            entry = self._load_from_disk_cache(file_path, cache_level)
            if entry:
                entry.update_access()

                # Try to store in memory cache
                data_size = entry.size_bytes
                if self._make_space_in_memory(data_size):
                    self.memory_cache[key] = entry
                    self.current_memory_bytes += data_size

                    # Update access order
                    self.access_order.append(key)

                self.stats.hit_count += 1
                self.logger.debug(
                    "Cache hit (disk): %s [{cache_level.value}]", file_path
                )
                return entry.data

            # Cache miss
            self.stats.miss_count += 1
            self.logger.debug("Cache miss: %s [{cache_level.value}]", file_path)
            return None

    def put(
        self,
        file_path: str,
        cache_level: CacheLevel,
        data: Any,
        memory_only: bool = False,
    ) -> bool:
        """
        Store data in cache.

        Args:
            file_path: File path
            cache_level: Cache level
            data: Data to cache
            memory_only: If True, only store in memory

        Returns:
            True if successfully stored, False otherwise
        """
        with self.lock:
            key = f"{file_path}:{cache_level.value}"

            # Generate file hash
            file_hash = self._generate_file_hash(file_path)

            # Estimate data size
            data_size = self._estimate_data_size(data)

            # Check if item is larger than total cache limit
            if data_size > self.max_memory_bytes and not memory_only:
                self.logger.warning(
                    f"Data too large for cache ({data_size} bytes > {self.max_memory_bytes} bytes): {file_path}"
                )
                return False

            # Create cache entry
            current_time = time.time()
            entry = CacheEntry(
                file_path=file_path,
                file_hash=file_hash,
                cache_level=cache_level,
                data=data,
                size_bytes=data_size,
                access_count=1,
                last_access_time=current_time,
                creation_time=current_time,
                memory_only=memory_only,
            )

            # Store in memory cache
            if not memory_only or self._make_space_in_memory(data_size):
                self.memory_cache[key] = entry
                self.current_memory_bytes += data_size

                # Update access order
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

            # Store to disk cache if not memory-only
            if not memory_only:
                self._store_to_disk_cache(key, entry)

            # Update statistics
            self._update_stats()

            self.logger.debug(
                "Cached: %s [{cache_level.value}] ({data_size} bytes)", file_path
            )
            return True

    def remove(self, file_path: str, cache_level: Optional[CacheLevel] = None) -> bool:
        """
        Remove data from cache.

        Args:
            file_path: File path
            cache_level: Specific cache level to remove (all levels if None)

        Returns:
            True if successfully removed, False otherwise
        """
        with self.lock:
            removed = False

            # Determine which levels to remove
            levels_to_remove = [cache_level] if cache_level else list(CacheLevel)

            for level in levels_to_remove:
                key = f"{file_path}:{level.value}"

                # Remove from memory cache
                if key in self.memory_cache:
                    entry = self.memory_cache.pop(key)
                    self.current_memory_bytes -= entry.size_bytes
                    removed = True

                    # Update access order
                    if key in self.access_order:
                        self.access_order.remove(key)

                # Remove from disk cache
                try:
                    with sqlite3.connect(self.disk_cache_db) as conn:
                        cursor = conn.execute(
                            "DELETE FROM cache_entries WHERE file_path = ? AND cache_level = ?",
                            (file_path, level.value),
                        )
                        if cursor.rowcount > 0:
                            removed = True
                        conn.commit()

                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.error("Failed to remove from disk cache: %s", str(e))

            if removed:
                self._update_stats()
                self.logger.debug("Removed from cache: %s", file_path)

            return removed

    def clear(self, memory_only: bool = False) -> None:
        """
        Clear cache.

        Args:
            memory_only: If True, only clear memory cache
        """
        with self.lock:
            # Clear memory cache
            self.memory_cache.clear()
            self.current_memory_bytes = 0
            self.access_order.clear()

            # Clear disk cache if requested
            if not memory_only:
                try:
                    with sqlite3.connect(self.disk_cache_db) as conn:
                        conn.execute("DELETE FROM cache_entries")
                        conn.commit()

                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.error("Failed to clear disk cache: %s", str(e))

            # Reset statistics
            self.stats = CacheStats()

            # Force garbage collection
            gc.collect()

            self.logger.info("Cache cleared (memory_only=%s)", memory_only)

    def _update_stats(self) -> None:
        """Update cache statistics."""
        self.stats.total_entries = len(self.memory_cache)
        self.stats.memory_entries = len(self.memory_cache)
        self.stats.memory_size_bytes = self.current_memory_bytes

        try:
            with sqlite3.connect(self.disk_cache_db) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*), SUM(size_bytes) FROM cache_entries"
                )
                row = cursor.fetchone()
                if row:
                    self.stats.disk_entries = row[0] or 0
                    self.stats.disk_size_bytes = row[1] or 0

                self.stats.total_entries = (
                    self.stats.memory_entries + self.stats.disk_entries
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update statistics: %s", str(e))

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            Current cache statistics
        """
        with self.lock:
            self._update_stats()
            return self.stats

    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.

        Returns:
            Memory usage in MB
        """
        return self.current_memory_bytes / (1024 * 1024)

    def get_hit_ratio(self) -> float:
        """
        Get cache hit ratio.

        Returns:
            Hit ratio (0.0 to 1.0)
        """
        total = self.stats.hit_count + self.stats.miss_count
        if total == 0:
            return 0.0
        return self.stats.hit_count / total

    def optimize_cache(self) -> None:
        """Optimize cache performance."""
        with self.lock:
            # Update statistics
            self._update_stats()

            # Check if we're using too much memory
            memory_usage_ratio = self.current_memory_bytes / self.max_memory_bytes
            if memory_usage_ratio > 0.9:
                self.logger.info(
                    "High memory usage (%.1f%%), evicting entries",
                    memory_usage_ratio * 100,
                )
                self._evict_memory_entries(int(self.current_memory_bytes * 0.2))

            # Clean up old disk cache entries
            try:
                with sqlite3.connect(self.disk_cache_db) as conn:
                    # Remove entries older than 30 days with low access count
                    cutoff_time = time.time() - (30 * 24 * 60 * 60)
                    cursor = conn.execute(
                        """
                        DELETE FROM cache_entries
                        WHERE last_access_time < ? AND access_count < 3
                        """,
                        (cutoff_time,),
                    )
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        self.logger.info(
                            "Cleaned up %s old disk cache entries", deleted_count
                        )
                    conn.commit()

            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                self.logger.error("Failed to optimize disk cache: %s", str(e))

    def cleanup(self) -> None:
        """Clean up cache resources."""
        with self.lock:
            self.clear()

            # Close disk cache connection if needed
            # SQLite connections are automatically closed when out of scope

            self.logger.info("Model cache cleaned up")


# Global model cache instance
_model_cache = None


def get_model_cache() -> ModelCache:
    """
    Get the global model cache instance.

    Returns:
        Global model cache instance
    """
    global _model_cache
    if _model_cache is None:
        _model_cache = ModelCache()
    return _model_cache
