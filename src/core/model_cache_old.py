"""
Simple model cache system for Digital Workshop.

This module provides a basic caching system for 3D models that relies on the OS
for memory management instead of implementing custom memory management.
"""

import sqlite3
import time
import xxhash
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any

from .logging_config import get_logger
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
    access_count: int
    last_access_time: float
    creation_time: float

    def update_access(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_access_time = time.time()


class ModelCache:
    """
    Simple model cache that lets the OS handle memory management.

    Features:
    - Basic caching with simple LRU-like behavior
    - Disk-based overflow caching
    - No memory limits or eviction logic
    """

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the model cache.

        Args:
            cache_dir: Directory for disk cache
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing simple model cache")

        # Cache configuration
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.disk_cache_db = str(self.cache_dir / "cache.db")

        # Initialize disk cache
        self._init_disk_cache()

        # Cache storage - simple dictionary, no memory management
        self.memory_cache: Dict[str, CacheEntry] = {}

        self.logger.info("Simple model cache initialized")

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

        except Exception as e:
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

        except Exception as e:
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

        except Exception as e:
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

        except Exception as e:
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
        sorted_entries = sorted(self.memory_cache.items(), key=lambda x: x[1].last_access_time)

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

            # Move to disk cache if not already there and disk cache is enabled
            if not entry.memory_only and self.use_disk_cache:
                self._store_to_disk_cache(key, entry)

            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)

            self.stats.eviction_count += 1

        if entries_to_evict:
            self.logger.debug("Evicted %s entries, freed {bytes_freed} bytes", len(entries_to_evict))

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

        except Exception as e:
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

        except Exception as e:
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
                self.logger.debug("Cache hit (memory): %s [{cache_level.value}]", file_path)
                return entry.data

            # Check disk cache if enabled
            if self.use_disk_cache:
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
                    self.logger.debug("Cache hit (disk): %s [{cache_level.value}]", file_path)
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

            # Create cache entry
            entry = self._create_cache_entry(
                file_path, file_hash, cache_level, data, data_size, memory_only
            )

            # Store in memory cache - let OS handle memory management
            self.memory_cache[key] = entry
            self.current_memory_bytes += data_size

            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            # Store to disk cache if not memory-only and disk cache is enabled
            if not memory_only and self.use_disk_cache:
                self._store_to_disk_cache(key, entry)

            # Update statistics
            self._update_stats()

            self.logger.debug("Cached: %s [{cache_level.value}] ({data_size} bytes)", file_path)
            return True

    def _create_cache_entry(
        self,
        file_path: str,
        file_hash: str,
        cache_level: CacheLevel,
        data: Any,
        data_size: int,
        memory_only: bool = False,
    ) -> CacheEntry:
        """Create a cache entry with the given parameters."""
        current_time = time.time()
        return CacheEntry(
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

    def _store_entry(
        self,
        file_path: str,
        cache_level: CacheLevel,
        data: Any,
        memory_only: bool = False,
    ) -> bool:
        """Store a cache entry using the standard path."""
        key = f"{file_path}:{cache_level.value}"
        file_hash = self._generate_file_hash(file_path)
        data_size = self._estimate_data_size(data)

        # Create cache entry
        entry = self._create_cache_entry(
            file_path, file_hash, cache_level, data, data_size, memory_only
        )

        # Store in memory cache
        if not memory_only or self._make_space_in_memory(data_size):
            self.memory_cache[key] = entry
            self.current_memory_bytes += data_size

            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

        # Store to disk cache if not memory-only and disk cache is enabled
        if not memory_only and self.use_disk_cache:
            self._store_to_disk_cache(key, entry)

        # Update statistics
        self._update_stats()

        self.logger.debug("Cached: %s [{cache_level.value}] ({data_size} bytes)", file_path)
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

                # Remove from disk cache if enabled
                if self.use_disk_cache:
                    try:
                        with sqlite3.connect(self.disk_cache_db) as conn:
                            cursor = conn.execute(
                                "DELETE FROM cache_entries WHERE file_path = ? AND cache_level = ?",
                                (file_path, level.value),
                            )
                            if cursor.rowcount > 0:
                                removed = True
                            conn.commit()

                    except Exception as e:
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

            # Clear disk cache if requested and enabled
            if not memory_only and self.use_disk_cache:
                try:
                    with sqlite3.connect(self.disk_cache_db) as conn:
                        conn.execute("DELETE FROM cache_entries")
                        conn.commit()

                except Exception as e:
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

        if self.use_disk_cache:
            try:
                with sqlite3.connect(self.disk_cache_db) as conn:
                    cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
                    row = cursor.fetchone()
                    if row:
                        self.stats.disk_entries = row[0] or 0
                        self.stats.disk_size_bytes = row[1] or 0

                    self.stats.total_entries = self.stats.memory_entries + self.stats.disk_entries

            except Exception as e:
                self.logger.error("Failed to update statistics: %s", str(e))
        else:
            # Disk cache disabled, only memory entries count
            self.stats.disk_entries = 0
            self.stats.disk_size_bytes = 0
            self.stats.total_entries = self.stats.memory_entries

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
                self.logger.info("High memory usage (%s), evicting entries", memory_usage_ratio:.1%)
                self._evict_memory_entries(int(self.current_memory_bytes * 0.2))

            # Clean up old disk cache entries if enabled
            if self.use_disk_cache:
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
                            self.logger.info("Cleaned up %s old disk cache entries", deleted_count)
                        conn.commit()

                except Exception as e:
                    self.logger.error("Failed to optimize disk cache: %s", str(e))

    def cleanup(self) -> None:
        """Clean up cache resources."""
        with self.lock:
            self.clear()

            # Close disk cache connection if needed
            # SQLite connections are automatically closed when out of scope

            self.logger.info("Model cache cleaned up")

    def get_or_load_progressive(
        self, file_path: str, parser, progress_callback=None
    ) -> Optional[Model]:
        """
        Get model from cache or load it with progressive loading.

        Args:
            file_path: Path to the model file
            parser: Parser instance to load the file if not cached
            progress_callback: Optional progress callback

        Returns:
            Model instance or None if loading failed
        """
        try:
            # First, try to get cached full geometry
            model = self.get(file_path, CacheLevel.GEOMETRY_FULL)
            if model:
                return model

            # Try cached low-res version
            model = self.get(file_path, CacheLevel.GEOMETRY_LOW)
            if model:
                self.logger.info("Using cached low-res version: %s", file_path)
                return model

            # Try cached metadata version
            model = self.get(file_path, CacheLevel.METADATA)
            if model:
                self.logger.info("Using cached metadata: %s", file_path)
                return model

            # Load full geometry - let OS handle memory management
            if progress_callback:
                progress_callback(10.0, "Loading model...")

            try:
                full_model = parser.parse_file(file_path, progress_callback)
                if full_model:
                    self.put(file_path, CacheLevel.GEOMETRY_FULL, full_model)
                    return full_model
            except Exception as e:
                self.logger.error("Failed to load full geometry: %s", e)

            # Fallback to metadata only
            if progress_callback:
                progress_callback(50.0, "Loading metadata...")

            try:
                metadata_model = parser._parse_metadata_only_internal(file_path)
                if metadata_model:
                    self.put(file_path, CacheLevel.METADATA, metadata_model)
                    return metadata_model
            except Exception as e:
                self.logger.error("Failed to load metadata: %s", e)

            return None

        except Exception as e:
            self.logger.error("Progressive loading failed for %s: {e}", file_path)
            return None

    def _load_full_geometry(
        self, file_path: str, parser, progress_callback=None
    ) -> Optional[Model]:
        """Load full geometry with caching."""
        # First, try to get cached version
        model = self.get(file_path, CacheLevel.GEOMETRY_FULL)
        if model:
            return model

        # Try low-res version as fallback
        model = self.get(file_path, CacheLevel.GEOMETRY_LOW)
        if model:
            self.logger.info("Using cached low-res version: %s", file_path)
            return model

        # Try metadata-only version as fallback
        model = self.get(file_path, CacheLevel.METADATA)
        if model:
            self.logger.info("Using cached metadata: %s", file_path)
            return model

        # Load full geometry
        if progress_callback:
            progress_callback(10.0, "Loading full geometry...")

        try:
            full_model = parser.parse_file(file_path, progress_callback)
            if full_model:
                self.put(file_path, CacheLevel.GEOMETRY_FULL, full_model)
                return full_model
        except Exception as e:
            self.logger.error("Failed to load full geometry: %s", e)

        # Fallback to low-res
        return self._load_low_res_geometry(file_path, parser, progress_callback)

    def _load_low_res_geometry(
        self, file_path: str, parser, progress_callback=None
    ) -> Optional[Model]:
        """Load low-resolution geometry with caching."""
        # Try cached versions first
        model = self.get(file_path, CacheLevel.GEOMETRY_LOW)
        if model:
            return model

        model = self.get(file_path, CacheLevel.METADATA)
        if model:
            return model

        # Load metadata first
        if progress_callback:
            progress_callback(10.0, "Loading file metadata...")

        try:
            metadata_model = parser._parse_metadata_only_internal(file_path)
            if metadata_model:
                self.put(file_path, CacheLevel.METADATA, metadata_model)
        except Exception as e:
            self.logger.error("Failed to load metadata: %s", e)

        # Load low-res geometry
        if progress_callback:
            progress_callback(40.0, "Loading low-resolution geometry...")

        try:
            low_res_model = parser._load_low_res_geometry(file_path, progress_callback)
            if low_res_model:
                self.put(file_path, CacheLevel.GEOMETRY_LOW, low_res_model)
                return low_res_model
        except Exception as e:
            self.logger.error("Failed to load low-res geometry: %s", e)

        # Fallback to metadata
        return metadata_model

    def _load_metadata_only(
        self, file_path: str, parser, progress_callback=None
    ) -> Optional[Model]:
        """Load metadata only with caching."""
        # Try cached version first
        model = self.get(file_path, CacheLevel.METADATA)
        if model:
            return model

        # Load metadata
        if progress_callback:
            progress_callback(20.0, "Loading file metadata...")

        try:
            metadata_model = parser._parse_metadata_only_internal(file_path)
            if metadata_model:
                self.put(file_path, CacheLevel.METADATA, metadata_model)
                return metadata_model
        except Exception as e:
            self.logger.error("Failed to load metadata: %s", e)

        return None


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
