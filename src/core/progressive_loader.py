"""
Progressive File Loading System for Candy-Cadence.

This module provides high-performance file loading with:
- Progressive loading for large files
- Background processing with QThread
- Chunked file I/O operations
- Progress tracking and cancellation support
- Memory-efficient streaming
- Adaptive loading based on hardware capabilities
"""

import os
import time
import threading
import mmap
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

from PySide6.QtCore import QObject, Signal

from .logging_config import get_logger, log_function_call
from .memory_manager import memory_operation

logger = get_logger(__name__)


class LoadingState(Enum):
    """File loading states."""

    PENDING = "pending"
    LOADING = "loading"
    PROGRESS = "progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class LoadingPriority(Enum):
    """Loading priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class HardwareCapability(Enum):
    """Hardware capability levels."""

    MINIMAL = "minimal"  # 4GB RAM, 2-core CPU
    STANDARD = "standard"  # 8GB RAM, 4-core CPU
    HIGH = "high"  # 16GB RAM, 8-core CPU
    EXTREME = "extreme"  # 32GB+ RAM, 16+ core CPU


@dataclass
class LoadingProgress:
    """Loading progress information."""

    file_path: str
    bytes_loaded: int
    total_bytes: int
    percentage: float
    chunks_completed: int
    total_chunks: int
    estimated_time_remaining: float
    current_speed_mbps: float
    state: LoadingState
    error_message: Optional[str] = None


@dataclass
class ChunkInfo:
    """File chunk information."""

    chunk_id: int
    start_offset: int
    end_offset: int
    size_bytes: int
    data: Optional[bytes] = None
    processed: bool = False
    error: Optional[str] = None


@dataclass
class LoadingConfig:
    """Loading configuration."""

    chunk_size_mb: int = 10
    max_concurrent_chunks: int = 4
    buffer_size_mb: int = 50
    use_memory_mapping: bool = True
    enable_compression: bool = False
    priority: LoadingPriority = LoadingPriority.NORMAL
    hardware_capability: HardwareCapability = HardwareCapability.STANDARD
    max_memory_usage_mb: int = 512
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600


class HardwareDetector:
    """Detect system hardware capabilities for adaptive loading."""

    @staticmethod
    def detect_capability() -> HardwareCapability:
        """Detect system hardware capability level."""
        try:
            import psutil

            # Get system memory
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Get CPU count
            cpu_count = psutil.cpu_count()

            # Get CPU frequency (if available)
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_mhz = cpu_freq.max if cpu_freq else 2000
            except:
                cpu_mhz = 2000  # Default assumption

            # Determine capability level
            if memory_gb >= 32 and cpu_count >= 16 and cpu_mhz >= 3000:
                return HardwareCapability.EXTREME
            elif memory_gb >= 16 and cpu_count >= 8 and cpu_mhz >= 2500:
                return HardwareCapability.HIGH
            elif memory_gb >= 8 and cpu_count >= 4 and cpu_mhz >= 2000:
                return HardwareCapability.STANDARD
            else:
                return HardwareCapability.MINIMAL

        except Exception as e:
            logger.warning("Hardware detection failed: %s", str(e))
            return HardwareCapability.STANDARD

    @staticmethod
    def get_optimal_config(capability: HardwareCapability) -> LoadingConfig:
        """Get optimal loading configuration for hardware capability."""
        configs = {
            HardwareCapability.MINIMAL: LoadingConfig(
                chunk_size_mb=5,
                max_concurrent_chunks=2,
                buffer_size_mb=25,
                max_memory_usage_mb=128,
                use_memory_mapping=False,
            ),
            HardwareCapability.STANDARD: LoadingConfig(
                chunk_size_mb=10,
                max_concurrent_chunks=4,
                buffer_size_mb=50,
                max_memory_usage_mb=256,
            ),
            HardwareCapability.HIGH: LoadingConfig(
                chunk_size_mb=20,
                max_concurrent_chunks=8,
                buffer_size_mb=100,
                max_memory_usage_mb=512,
            ),
            HardwareCapability.EXTREME: LoadingConfig(
                chunk_size_mb=50,
                max_concurrent_chunks=16,
                buffer_size_mb=200,
                max_memory_usage_mb=1024,
            ),
        }

        return configs.get(capability, configs[HardwareCapability.STANDARD])


class FileChunker:
    """Efficient file chunking with multiple strategies."""

    def __init__(self, config: LoadingConfig):
        """
        Initialize file chunker.

        Args:
            config: Loading configuration
        """
        self.config = config
        self._lock = threading.Lock()

    def create_chunks(self, file_path: str, file_size: int) -> List[ChunkInfo]:
        """
        Create file chunks for progressive loading.

        Args:
            file_path: Path to file
            file_size: File size in bytes

        Returns:
            List of chunk information
        """
        chunks = []
        chunk_size = self.config.chunk_size_mb * 1024 * 1024
        chunk_id = 0

        for start_offset in range(0, file_size, chunk_size):
            end_offset = min(start_offset + chunk_size, file_size)
            chunk_size_bytes = end_offset - start_offset

            chunk = ChunkInfo(
                chunk_id=chunk_id,
                start_offset=start_offset,
                end_offset=end_offset,
                size_bytes=chunk_size_bytes,
            )
            chunks.append(chunk)
            chunk_id += 1

        logger.info("Created %s chunks for {file_path} ({file_size} bytes)", len(chunks))
        return chunks

    def read_chunk(self, file_path: str, chunk: ChunkInfo) -> bytes:
        """
        Read a specific chunk from file.

        Args:
            file_path: Path to file
            chunk: Chunk information

        Returns:
            Chunk data
        """
        try:
            if self.config.use_memory_mapping and os.path.getsize(file_path) > 100 * 1024 * 1024:
                # Use memory mapping for large files
                return self._read_chunk_mmap(file_path, chunk)
            else:
                # Use regular file reading
                return self._read_chunk_regular(file_path, chunk)
        except Exception as e:
            logger.error("Failed to read chunk %s: {str(e)}", chunk.chunk_id)
            raise

    def _read_chunk_regular(self, file_path: str, chunk: ChunkInfo) -> bytes:
        """Read chunk using regular file I/O."""
        with open(file_path, "rb") as f:
            f.seek(chunk.start_offset)
            return f.read(chunk.size_bytes)

    def _read_chunk_mmap(self, file_path: str, chunk: ChunkInfo) -> bytes:
        """Read chunk using memory mapping."""
        with open(file_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                return mmapped_file[chunk.start_offset : chunk.end_offset]


class ProgressTracker:
    """Track loading progress with detailed metrics."""

    def __init__(self):
        """Initialize progress tracker."""
        self._progress_callbacks: List[Callable[[LoadingProgress], None]] = []
        self._current_progress: Optional[LoadingProgress] = None
        self._start_time = 0.0
        self._lock = threading.Lock()

    def start_tracking(self, file_path: str, total_bytes: int) -> None:
        """Start tracking progress for a file."""
        with self._lock:
            self._start_time = time.time()
            self._current_progress = LoadingProgress(
                file_path=file_path,
                bytes_loaded=0,
                total_bytes=total_bytes,
                percentage=0.0,
                chunks_completed=0,
                total_chunks=0,
                estimated_time_remaining=0.0,
                current_speed_mbps=0.0,
                state=LoadingState.PENDING,
            )

    def update_progress(self, bytes_loaded: int, chunks_completed: int, total_chunks: int) -> None:
        """Update loading progress."""
        with self._lock:
            if not self._current_progress:
                return

            progress = self._current_progress
            progress.bytes_loaded = bytes_loaded
            progress.chunks_completed = chunks_completed
            progress.total_chunks = total_chunks
            progress.percentage = (
                (bytes_loaded / progress.total_bytes) * 100 if progress.total_bytes > 0 else 0
            )

            # Calculate speed and ETA
            elapsed_time = time.time() - self._start_time
            if elapsed_time > 0:
                progress.current_speed_mbps = (bytes_loaded / (1024 * 1024)) / elapsed_time

                if progress.current_speed_mbps > 0:
                    remaining_bytes = progress.total_bytes - bytes_loaded
                    remaining_time_seconds = remaining_bytes / (
                        progress.current_speed_mbps * 1024 * 1024
                    )
                    progress.estimated_time_remaining = remaining_time_seconds

            # Notify callbacks
            self._notify_progress_callbacks(progress)

    def set_state(self, state: LoadingState, error_message: Optional[str] = None) -> None:
        """Set loading state."""
        with self._lock:
            if self._current_progress:
                self._current_progress.state = state
                self._current_progress.error_message = error_message
                self._notify_progress_callbacks(self._current_progress)

    def register_progress_callback(self, callback: Callable[[LoadingProgress], None]) -> None:
        """Register progress callback."""
        self._progress_callbacks.append(callback)

    def _notify_progress_callbacks(self, progress: LoadingProgress) -> None:
        """Notify all progress callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error("Progress callback failed: %s", str(e))

    def get_current_progress(self) -> Optional[LoadingProgress]:
        """Get current progress."""
        with self._lock:
            return self._current_progress


class LoadingWorker(QObject):
    """Background worker for progressive file loading."""

    progress_updated = Signal(LoadingProgress)
    loading_completed = Signal(str, object)  # file_path, result
    loading_failed = Signal(str, str)  # file_path, error_message
    loading_cancelled = Signal(str)  # file_path

    def __init__(self, worker_id: int, config: LoadingConfig):
        """
        Initialize loading worker.

        Args:
            worker_id: Worker identifier
            config: Loading configuration
        """
        super().__init__()
        self.worker_id = worker_id
        self.config = config
        self.chunker = FileChunker(config)
        self._cancelled = False
        self._current_task = None

    def load_file_progressive(
        self, file_path: str, parser_func: Callable, progress_tracker: ProgressTracker
    ) -> Any:
        """
        Load file progressively.

        Args:
            file_path: Path to file
            parser_func: Function to parse file data
            progress_tracker: Progress tracker instance

        Returns:
            Parsed file data
        """
        try:
            self._cancelled = False
            file_size = os.path.getsize(file_path)

            # Start progress tracking
            progress_tracker.start_tracking(file_path, file_size)
            progress_tracker.set_state(LoadingState.LOADING)

            # Create chunks
            chunks = self.chunker.create_chunks(file_path, file_size)
            total_chunks = len(chunks)

            # Process chunks
            results = []
            bytes_loaded = 0

            for i, chunk in enumerate(chunks):
                if self._cancelled:
                    progress_tracker.set_state(LoadingState.CANCELLED)
                    return None

                try:
                    # Read chunk
                    chunk_data = self.chunker.read_chunk(file_path, chunk)
                    chunk.data = chunk_data
                    chunk.processed = True

                    # Parse chunk
                    chunk_result = parser_func(chunk_data, chunk)
                    if chunk_result:
                        results.append(chunk_result)

                    bytes_loaded += chunk.size_bytes
                    progress_tracker.update_progress(bytes_loaded, i + 1, total_chunks)

                except Exception as e:
                    logger.error("Failed to process chunk %s: {str(e)}", chunk.chunk_id)
                    chunk.error = str(e)
                    # Continue with other chunks

            # Combine results
            final_result = self._combine_results(results) if results else None

            progress_tracker.set_state(LoadingState.COMPLETED)
            return final_result

        except Exception as e:
            error_msg = f"Failed to load file {file_path}: {str(e)}"
            logger.error(error_msg)
            progress_tracker.set_state(LoadingState.FAILED, error_msg)
            raise

    def cancel(self) -> None:
        """Cancel current loading operation."""
        self._cancelled = True

    def _combine_results(self, results: List[Any]) -> Any:
        """
        Combine chunk results into final result.

        Args:
            results: List of chunk results

        Returns:
            Combined result
        """
        # This should be overridden by specific file type loaders
        # For now, return the first result or None
        return results[0] if results else None


class ProgressiveLoader(QObject):
    """Main progressive loading manager."""

    def __init__(self, max_workers: int = None):
        """
        Initialize progressive loader.

        Args:
            max_workers: Maximum number of worker threads
        """
        super().__init__()

        # Detect hardware capabilities
        self.hardware_capability = HardwareDetector.detect_capability()
        self.config = HardwareDetector.get_optimal_config(self.hardware_capability)

        # Override max_workers if specified
        if max_workers:
            self.config.max_concurrent_chunks = max_workers

        # Initialize components
        self.progress_tracker = ProgressTracker()
        self._active_loads: Dict[str, LoadingWorker] = {}
        self._load_queue: Queue = Queue()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_chunks)
        self._results_cache: Dict[str, Tuple[Any, float]] = {}  # (result, timestamp)
        self._lock = threading.Lock()

        logger.info(
            f"Progressive loader initialized with {self.hardware_capability.value} capability"
        )

    @log_function_call(logger)
    def load_file(
        self,
        file_path: str,
        parser_func: Callable,
        progress_callback: Optional[Callable[[LoadingProgress], None]] = None,
        priority: LoadingPriority = LoadingPriority.NORMAL,
    ) -> Future:
        """
        Load file progressively.

        Args:
            file_path: Path to file
            parser_func: Function to parse file data
            progress_callback: Progress callback function
            priority: Loading priority

        Returns:
            Future object for the loading operation
        """
        # Check cache first
        if self.config.enable_caching:
            cached_result = self._get_cached_result(file_path)
            if cached_result:
                future = Future()
                future.set_result(cached_result)
                return future

        # Register progress callback
        if progress_callback:
            self.progress_tracker.register_progress_callback(progress_callback)

        # Create worker
        worker = LoadingWorker(len(self._active_loads), self.config)

        with self._lock:
            self._active_loads[file_path] = worker

        # Submit to thread pool
        future = self._executor.submit(self._load_file_worker, file_path, parser_func, worker)

        return future

    def _load_file_worker(
        self, file_path: str, parser_func: Callable, worker: LoadingWorker
    ) -> Any:
        """Worker function for file loading."""
        try:
            with memory_operation(f"loading_{os.path.basename(file_path)}"):
                result = worker.load_file_progressive(file_path, parser_func, self.progress_tracker)

                # Cache result if successful
                if result and self.config.enable_caching:
                    self._cache_result(file_path, result)

                return result

        except Exception as e:
            logger.error("File loading failed for %s: {str(e)}", file_path)
            raise
        finally:
            with self._lock:
                self._active_loads.pop(file_path, None)

    def cancel_load(self, file_path: str) -> bool:
        """
        Cancel a loading operation.

        Args:
            file_path: Path to file being loaded

        Returns:
            True if cancelled successfully
        """
        with self._lock:
            worker = self._active_loads.get(file_path)
            if worker:
                worker.cancel()
                self._active_loads.pop(file_path, None)
                logger.info("Cancelled loading for %s", file_path)
                return True
        return False

    def get_load_status(self, file_path: str) -> Optional[LoadingProgress]:
        """
        Get loading status for a file.

        Args:
            file_path: Path to file

        Returns:
            Loading progress or None
        """
        with self._lock:
            if file_path in self._active_loads:
                return self.progress_tracker.get_current_progress()
        return None

    def _cache_result(self, file_path: str, result: Any) -> None:
        """Cache loading result."""
        try:
            current_time = time.time()
            self._results_cache[file_path] = (result, current_time)

            # Clean old cache entries
            self._clean_cache()

        except Exception as e:
            logger.warning("Failed to cache result for %s: {str(e)}", file_path)

    def _get_cached_result(self, file_path: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        try:
            if file_path not in self._results_cache:
                return None

            result, timestamp = self._results_cache[file_path]

            # Check if cache entry is still valid
            if time.time() - timestamp > self.config.cache_ttl_seconds:
                del self._results_cache[file_path]
                return None

            logger.debug("Using cached result for %s", file_path)
            return result

        except Exception as e:
            logger.warning("Failed to get cached result for %s: {str(e)}", file_path)
            return None

    def _clean_cache(self) -> None:
        """Clean expired cache entries."""
        try:
            current_time = time.time()
            expired_keys = []

            for file_path, (result, timestamp) in self._results_cache.items():
                if current_time - timestamp > self.config.cache_ttl_seconds:
                    expired_keys.append(file_path)

            for key in expired_keys:
                del self._results_cache[key]

            if expired_keys:
                logger.debug("Cleaned %s expired cache entries", len(expired_keys))

        except Exception as e:
            logger.warning("Failed to clean cache: %s", str(e))

    def clear_cache(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._results_cache.clear()
        logger.info("Loading cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "cached_entries": len(self._results_cache),
                "cache_size_mb": sum(len(str(result)) for result, _ in self._results_cache.values())
                / (1024 * 1024),
                "hardware_capability": self.hardware_capability.value,
                "config": {
                    "chunk_size_mb": self.config.chunk_size_mb,
                    "max_concurrent_chunks": self.config.max_concurrent_chunks,
                    "buffer_size_mb": self.config.buffer_size_mb,
                    "max_memory_usage_mb": self.config.max_memory_usage_mb,
                },
            }

    def shutdown(self) -> None:
        """Shutdown the progressive loader."""
        try:
            # Cancel all active loads
            with self._lock:
                for file_path in list(self._active_loads.keys()):
                    self.cancel_load(file_path)

            # Shutdown executor
            self._executor.shutdown(wait=True)

            logger.info("Progressive loader shutdown completed")

        except Exception as e:
            logger.error("Error during progressive loader shutdown: %s", str(e))


# Global progressive loader instance
_progressive_loader: Optional[ProgressiveLoader] = None


def get_progressive_loader() -> ProgressiveLoader:
    """Get global progressive loader instance."""
    global _progressive_loader
    if _progressive_loader is None:
        _progressive_loader = ProgressiveLoader()
    return _progressive_loader


def load_file_progressive(
    file_path: str,
    parser_func: Callable,
    progress_callback: Optional[Callable[[LoadingProgress], None]] = None,
) -> Future:
    """
    Load file progressively with global loader.

    Args:
        file_path: Path to file
        parser_func: Function to parse file data
        progress_callback: Progress callback function

    Returns:
        Future object for the loading operation
    """
    loader = get_progressive_loader()
    return loader.load_file(file_path, parser_func, progress_callback)


def cancel_file_load(file_path: str) -> bool:
    """Cancel file loading operation."""
    loader = get_progressive_loader()
    return loader.cancel_load(file_path)


def get_load_progress(file_path: str) -> Optional[LoadingProgress]:
    """Get loading progress for a file."""
    loader = get_progressive_loader()
    return loader.get_load_status(file_path)
