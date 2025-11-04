"""
Database Caching Layer with Multi-Level Cache Management.

This module provides comprehensive caching for database operations including
query results, model metadata, search results, and thumbnails with intelligent
invalidation and performance optimization.
"""

import os
import pickle
import gzip
import hashlib
import threading
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict, defaultdict
from contextlib import contextmanager

from ..logging_config import get_logger

logger = get_logger(__name__)


class CacheLevel(Enum):
    """Cache level enumeration."""

    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"


class CacheStrategy(Enum):
    """Cache strategy enumeration."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on usage patterns


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    compressed: bool = False
    cache_level: CacheLevel = CacheLevel.MEMORY
    ttl_seconds: Optional[float] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    avg_access_time: float = 0.0
    memory_usage_mb: float = 0.0
    disk_usage_mb: float = 0.0
    entries_count: int = 0


class MemoryCache:
    """High-performance in-memory cache with LRU eviction."""

    def __init__(self, max_size_mb: int = 100, strategy: CacheStrategy = CacheStrategy.LRU):
        """
        Initialize memory cache.

        Args:
            max_size_mb: Maximum cache size in megabytes
            strategy: Cache eviction strategy
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.strategy = strategy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_size = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._access_times = defaultdict(float)
        self._access_counts = defaultdict(int)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check TTL
                if entry.ttl_seconds:
                    age = (datetime.now() - entry.created_at).total_seconds()
                    if age > entry.ttl_seconds:
                        self._remove_entry(key)
                        return None

                # Update access statistics
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                self._access_times[key] = time.time()
                self._access_counts[key] += 1

                # Move to end for LRU
                if self.strategy == CacheStrategy.LRU:
                    self._cache.move_to_end(key)

                # Decompress if needed
                if entry.compressed:
                    return gzip.decompress(entry.value)
                else:
                    return entry.value

            return None

    def put(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[float] = None,
        tags: List[str] = None,
        compress: bool = False,
    ) -> bool:
        """
        Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            tags: Cache tags for invalidation
            compress: Whether to compress the value

        Returns:
            True if cached successfully
        """
        if tags is None:
            tags = []

        with self._lock:
            # Calculate size
            if compress:
                serialized = gzip.compress(pickle.dumps(value))
                size = len(serialized)
            else:
                serialized = pickle.dumps(value)
                size = len(serialized)

            # Check if we need to evict
            while self._current_size + size > self.max_size_bytes and self._cache:
                self._evict_one()

            # Remove existing entry
            if key in self._cache:
                self._remove_entry(key)

            # Add new entry
            entry = CacheEntry(
                key=key,
                value=serialized,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                size_bytes=size,
                compressed=compress,
                cache_level=CacheLevel.MEMORY,
                ttl_seconds=ttl_seconds,
                tags=tags,
            )

            self._cache[key] = entry
            self._current_size += size

            return True

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size -= entry.size_bytes

    def _evict_one(self) -> None:
        """Evict one entry based on strategy."""
        if not self._cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used
            key = next(iter(self._cache))
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
        elif self.strategy == CacheStrategy.FIFO:
            # Remove first inserted
            key = next(iter(self._cache))
        else:
            # Default to LRU
            key = next(iter(self._cache))

        self._remove_entry(key)

    def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags.

        Args:
            tags: Tags to match

        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_entry(key)
                invalidated += 1

        return invalidated

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                total_requests=total_requests,
                hit_rate=hit_rate,
                memory_usage_mb=self._current_size / (1024 * 1024),
                entries_count=len(self._cache),
            )

    def __len__(self) -> int:
        """Get number of entries."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache


class DiskCache:
    """Persistent disk-based cache with compression."""

    def __init__(self, cache_dir: str, max_size_mb: int = 500):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size = 0
        self._lock = threading.Lock()

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Load existing cache info
        self._load_cache_info()

    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def _get_info_path(self) -> str:
        """Get cache info file path."""
        return os.path.join(self.cache_dir, "cache_info.json")

    def _load_cache_info(self) -> None:
        """Load cache information from disk."""
        info_path = self._get_info_path()
        if os.path.exists(info_path):
            try:
                with open(info_path, "r") as f:
                    info = json.load(f)
                    self._current_size = info.get("total_size", 0)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning("Failed to load cache info: %s", str(e))

    def _save_cache_info(self) -> None:
        """Save cache information to disk."""
        info_path = self._get_info_path()
        try:
            info = {
                "total_size": self._current_size,
                "last_updated": datetime.now().isoformat(),
            }
            with open(info_path, "w") as f:
                json.dump(info, f)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save cache info: %s", str(e))

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "rb") as f:
                # Read metadata
                metadata_size = int.from_bytes(f.read(4), "big")
                metadata_bytes = f.read(metadata_size)
                metadata = pickle.loads(metadata_bytes)

                # Check TTL
                if metadata.get("ttl_seconds"):
                    age = (
                        datetime.now() - datetime.fromisoformat(metadata["created_at"])
                    ).total_seconds()
                    if age > metadata["ttl_seconds"]:
                        self._remove_cache_file(cache_path)
                        return None

                # Read compressed data
                data_size = int.from_bytes(f.read(8), "big")
                data = f.read(data_size)

                # Decompress and deserialize
                if metadata.get("compressed", False):
                    data = gzip.decompress(data)

                return pickle.loads(data)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to read cache file %s: {str(e)}", cache_path)
            # Remove corrupted file
            try:
                os.remove(cache_path)
            except:
                pass
            return None

    def put(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[float] = None,
        tags: List[str] = None,
        compress: bool = True,
    ) -> bool:
        """
        Put value in disk cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            tags: Cache tags for invalidation
            compress: Whether to compress the value

        Returns:
            True if cached successfully
        """
        if tags is None:
            tags = []

        cache_path = self._get_cache_path(key)

        try:
            # Serialize and optionally compress data
            data = pickle.dumps(value)
            if compress:
                data = gzip.compress(data)

            # Create metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "ttl_seconds": ttl_seconds,
                "tags": tags,
                "compressed": compress,
                "original_size": len(pickle.dumps(value)),
                "cached_size": len(data),
            }

            metadata_bytes = pickle.dumps(metadata)

            # Check size limit
            total_size = 4 + len(metadata_bytes) + 8 + len(data)
            if self._current_size + total_size > self.max_size_bytes:
                self._evict_cache_files(total_size)

            # Write to disk
            with open(cache_path, "wb") as f:
                # Write metadata size and data
                f.write(len(metadata_bytes).to_bytes(4, "big"))
                f.write(metadata_bytes)

                # Write data size and data
                f.write(len(data).to_bytes(8, "big"))
                f.write(data)

            # Update cache info
            with self._lock:
                self._current_size += total_size
                self._save_cache_info()

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to write cache file %s: {str(e)}", cache_path)
            return False

    def _remove_cache_file(self, cache_path: str) -> None:
        """Remove cache file and update size."""
        try:
            file_size = os.path.getsize(cache_path)
            os.remove(cache_path)
            with self._lock:
                self._current_size -= file_size
                self._save_cache_info()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to remove cache file %s: {str(e)}", cache_path)

    def _evict_cache_files(self, needed_size: int) -> None:
        """Evict cache files to make space."""
        # Get all cache files with their modification times
        cache_files = []
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".cache"):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    size = os.path.getsize(filepath)
                    cache_files.append((filepath, mtime, size))
                except:
                    continue

        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda x: x[1])

        # Remove oldest files until we have enough space
        freed_size = 0
        for filepath, _, size in cache_files:
            if freed_size >= needed_size:
                break
            self._remove_cache_file(filepath)
            freed_size += size

    def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags.

        Args:
            tags: Tags to match

        Returns:
            Number of entries invalidated
        """
        invalidated = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".cache"):
                filepath = os.path.join(self.cache_dir, filename)

                try:
                    # Read metadata to check tags
                    with open(filepath, "rb") as f:
                        metadata_size = int.from_bytes(f.read(4), "big")
                        metadata_bytes = f.read(metadata_size)
                        metadata = pickle.loads(metadata_bytes)

                        if any(tag in metadata.get("tags", []) for tag in tags):
                            self._remove_cache_file(filepath)
                            invalidated += 1

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning("Failed to check cache file %s: {str(e)}", filepath)
                    # Remove corrupted file
                    try:
                        self._remove_cache_file(filepath)
                    except:
                        pass

        return invalidated

    def clear(self) -> None:
        """Clear all cache files."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(filepath)
                    except:
                        pass

            with self._lock:
                self._current_size = 0
                self._save_cache_info()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to clear disk cache: %s", str(e))

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            # Count cache files
            file_count = sum(1 for f in os.listdir(self.cache_dir) if f.endswith(".cache"))

            return CacheStats(
                hits=0,  # Disk cache doesn't track hits/misses separately
                misses=0,
                evictions=0,
                total_requests=0,
                hit_rate=0.0,
                disk_usage_mb=self._current_size / (1024 * 1024),
                entries_count=file_count,
            )


class DatabaseCacheManager:
    """Comprehensive database cache manager with multi-level caching."""

    def __init__(self, db_path: str, memory_cache_mb: int = 100, disk_cache_mb: int = 500):
        """
        Initialize database cache manager.

        Args:
            db_path: Database file path
            memory_cache_mb: Memory cache size in MB
            disk_cache_mb: Disk cache size in MB
        """
        self.db_path = db_path
        self.cache_dir = os.path.join(os.path.dirname(db_path), "cache")

        # Initialize caches
        self.memory_cache = MemoryCache(memory_cache_mb)
        self.disk_cache = DiskCache(self.cache_dir, disk_cache_mb)

        # Cache configuration
        self.default_ttl = {
            "model_metadata": 3600,  # 1 hour
            "search_results": 1800,  # 30 minutes
            "query_results": 900,  # 15 minutes
            "thumbnails": 7200,  # 2 hours
            "file_hashes": 86400,  # 24 hours
        }

        # Statistics
        self._stats = CacheStats()
        self._lock = threading.Lock()

        # Start background cleanup
        self._start_background_cleanup()

    def _start_background_cleanup(self) -> None:
        """Start background cache cleanup thread."""

        def cleanup_worker():
            while True:
                try:
                    self._cleanup_expired_entries()
                    time.sleep(300)  # Run every 5 minutes
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Cache cleanup error: %s", str(e))

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        # Memory cache cleanup is handled automatically on access
        # Disk cache cleanup is handled during put operations

        # Log cache statistics periodically
        if int(time.time()) % 3600 == 0:  # Every hour
            self._log_cache_stats()

    def _log_cache_stats(self) -> None:
        """Log cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()

        logger.info(
            f"Cache stats - Memory: {memory_stats.entries_count} entries, "
            f"{memory_stats.memory_usage_mb:.1f}MB, Hit rate: {memory_stats.hit_rate:.2%}"
        )
        logger.info(
            f"Cache stats - Disk: {disk_stats.entries_count} entries, "
            f"{disk_stats.disk_usage_mb:.1f}MB"
        )

    def _generate_cache_key(self, category: str, *args, **kwargs) -> str:
        """
        Generate cache key from category and parameters.

        Args:
            category: Cache category
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create a deterministic key
        key_parts = [category]

        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency)
        for key in sorted(kwargs.keys()):
            key_parts.append(f"{key}={kwargs[key]}")

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached model metadata.

        Args:
            model_id: Model identifier

        Returns:
            Model metadata or None
        """
        cache_key = self._generate_cache_key("model_metadata", model_id)

        # Try memory cache first
        result = self.memory_cache.get(cache_key)
        if result is not None:
            return result

        # Try disk cache
        result = self.disk_cache.get(cache_key)
        if result is not None:
            # Promote to memory cache
            self.memory_cache.put(cache_key, result, ttl_seconds=self.default_ttl["model_metadata"])
            return result

        return None

    def cache_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> None:
        """
        Cache model metadata.

        Args:
            model_id: Model identifier
            metadata: Model metadata
        """
        cache_key = self._generate_cache_key("model_metadata", model_id)

        # Cache in both memory and disk
        self.memory_cache.put(cache_key, metadata, ttl_seconds=self.default_ttl["model_metadata"])
        self.disk_cache.put(cache_key, metadata, ttl_seconds=self.default_ttl["model_metadata"])

    def get_search_results(self, query: str, filters: Dict[str, Any] = None) -> Optional[List[str]]:
        """
        Get cached search results.

        Args:
            query: Search query
            filters: Search filters

        Returns:
            List of model IDs or None
        """
        if filters is None:
            filters = {}

        cache_key = self._generate_cache_key("search_results", query, **filters)

        # Try memory cache first
        result = self.memory_cache.get(cache_key)
        if result is not None:
            return result

        # Try disk cache
        result = self.disk_cache.get(cache_key)
        if result is not None:
            # Promote to memory cache
            self.memory_cache.put(cache_key, result, ttl_seconds=self.default_ttl["search_results"])
            return result

        return None

    def cache_search_results(
        self, query: str, results: List[str], filters: Dict[str, Any] = None
    ) -> None:
        """
        Cache search results.

        Args:
            query: Search query
            results: List of model IDs
            filters: Search filters
        """
        if filters is None:
            filters = {}

        cache_key = self._generate_cache_key("search_results", query, **filters)

        # Cache in both memory and disk
        self.memory_cache.put(cache_key, results, ttl_seconds=self.default_ttl["search_results"])
        self.disk_cache.put(cache_key, results, ttl_seconds=self.default_ttl["search_results"])

    def get_query_results(self, query: str, params: Tuple = None) -> Optional[List[tuple]]:
        """
        Get cached query results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results or None
        """
        cache_key = self._generate_cache_key("query_results", query, params)

        # Try memory cache first
        result = self.memory_cache.get(cache_key)
        if result is not None:
            return result

        # Try disk cache
        result = self.disk_cache.get(cache_key)
        if result is not None:
            # Promote to memory cache
            self.memory_cache.put(cache_key, result, ttl_seconds=self.default_ttl["query_results"])
            return result

        return None

    def cache_query_results(self, query: str, results: List[tuple], params: Tuple = None) -> None:
        """
        Cache query results.

        Args:
            query: SQL query
            results: Query results
            params: Query parameters
        """
        cache_key = self._generate_cache_key("query_results", query, params)

        # Cache in both memory and disk
        self.memory_cache.put(cache_key, results, ttl_seconds=self.default_ttl["query_results"])
        self.disk_cache.put(cache_key, results, ttl_seconds=self.default_ttl["query_results"])

    def get_thumbnail(self, model_id: str, size: str = "medium") -> Optional[bytes]:
        """
        Get cached thumbnail.

        Args:
            model_id: Model identifier
            size: Thumbnail size

        Returns:
            Thumbnail image data or None
        """
        cache_key = self._generate_cache_key("thumbnail", model_id, size)

        # Try memory cache first
        result = self.memory_cache.get(cache_key)
        if result is not None:
            return result

        # Try disk cache
        result = self.disk_cache.get(cache_key)
        if result is not None:
            # Promote to memory cache
            self.memory_cache.put(cache_key, result, ttl_seconds=self.default_ttl["thumbnails"])
            return result

        return None

    def cache_thumbnail(self, model_id: str, thumbnail_data: bytes, size: str = "medium") -> None:
        """
        Cache thumbnail.

        Args:
            model_id: Model identifier
            thumbnail_data: Thumbnail image data
            size: Thumbnail size
        """
        cache_key = self._generate_cache_key("thumbnail", model_id, size)

        # Cache in both memory and disk
        self.memory_cache.put(cache_key, thumbnail_data, ttl_seconds=self.default_ttl["thumbnails"])
        self.disk_cache.put(cache_key, thumbnail_data, ttl_seconds=self.default_ttl["thumbnails"])

    def invalidate_model_cache(self, model_id: str) -> int:
        """
        Invalidate all cache entries for a specific model.

        Args:
            model_id: Model identifier

        Returns:
            Number of cache entries invalidated
        """
        invalidated = 0

        # Invalidate by model-specific tags
        tags = [f"model:{model_id}"]

        invalidated += self.memory_cache.invalidate_by_tags(tags)
        invalidated += self.disk_cache.invalidate_by_tags(tags)

        return invalidated

    def invalidate_by_category(self, category: str) -> int:
        """
        Invalidate cache entries by category.

        Args:
            category: Cache category

        Returns:
            Number of cache entries invalidated
        """
        invalidated = 0

        # Invalidate by category tags
        tags = [f"category:{category}"]

        invalidated += self.memory_cache.invalidate_by_tags(tags)
        invalidated += self.disk_cache.invalidate_by_tags(tags)

        return invalidated

    def clear_all_cache(self) -> None:
        """Clear all cache entries."""
        self.memory_cache.clear()
        self.disk_cache.clear()
        logger.info("All cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()

        return {
            "memory_cache": {
                "entries": memory_stats.entries_count,
                "memory_usage_mb": memory_stats.memory_usage_mb,
                "hit_rate": memory_stats.hit_rate,
                "total_requests": memory_stats.total_requests,
            },
            "disk_cache": {
                "entries": disk_stats.entries_count,
                "disk_usage_mb": disk_stats.disk_usage_mb,
            },
            "total_memory_usage_mb": memory_stats.memory_usage_mb + disk_stats.disk_usage_mb,
            "overall_hit_rate": memory_stats.hit_rate,  # Memory cache hit rate as overall indicator
        }

    @contextmanager
    def cached_query(self, query: str, params: Tuple = None, ttl_seconds: float = None):
        """
        Context manager for cached query execution.

        Args:
            query: SQL query
            params: Query parameters
            ttl_seconds: Cache TTL

        Yields:
            Query results
        """
        # Try to get from cache first
        cached_results = self.get_query_results(query, params)

        if cached_results is not None:
            yield cached_results
            return

        # If not in cache, we need to execute the query
        # This would typically be handled by the calling code
        yield None

        # After execution, cache the results
        # This would be called by the repository after getting results
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl["query_results"]

    def warm_up_cache(self, repository) -> None:
        """
        Warm up cache with frequently accessed data.

        Args:
            repository: Repository instance to get data from
        """
        try:
            logger.info("Starting cache warm-up")

            # Get popular models (this would be implemented in the repository)
            popular_models = repository.get_popular_models(limit=100)

            for model_id in popular_models:
                # Cache model metadata
                metadata = repository.get_metadata(model_id)
                if metadata:
                    self.cache_model_metadata(model_id, metadata)

                # Cache thumbnails
                thumbnail = repository.get_thumbnail(model_id)
                if thumbnail:
                    self.cache_thumbnail(model_id, thumbnail)

            logger.info("Cache warm-up completed for %s models", len(popular_models))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Cache warm-up failed: %s", str(e))

    def optimize_cache_performance(self) -> Dict[str, Any]:
        """
        Optimize cache performance based on usage patterns.

        Returns:
            Optimization results
        """
        results = {
            "memory_cache_optimized": False,
            "disk_cache_optimized": False,
            "recommendations": [],
        }

        # Analyze memory cache usage
        memory_stats = self.memory_cache.get_stats()
        if memory_stats.hit_rate < 0.7:
            results["recommendations"].append("Consider increasing memory cache size")
            results["memory_cache_optimized"] = True

        # Analyze disk cache usage
        disk_stats = self.disk_cache.get_stats()
        if disk_stats.entries_count == 0:
            results["recommendations"].append(
                "Disk cache appears empty - check cache configuration"
            )

        # Check cache sizes
        total_memory_mb = memory_stats.memory_usage_mb + disk_stats.disk_usage_mb
        if total_memory_mb > 1000:  # 1GB
            results["recommendations"].append("Consider cleaning up old cache entries")

        return results
