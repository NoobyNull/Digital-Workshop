"""
Memory management system for GPU-accelerated 3D model loading.

This module provides comprehensive memory monitoring, allocation tracking,
and cleanup mechanisms to ensure stable memory usage during large file processing.
"""

import gc
import psutil
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.core.logging_config import get_logger, log_function_call


class MemoryPressure(Enum):
    """Memory pressure levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    total_memory_gb: float
    available_memory_gb: float
    used_memory_gb: float
    memory_percent: float
    gpu_memory_used_gb: float = 0.0
    gpu_memory_total_gb: float = 0.0
    pressure_level: MemoryPressure = MemoryPressure.LOW

    @property
    def available_ratio(self) -> float:
        """Get ratio of available to total memory."""
        return self.available_memory_gb / self.total_memory_gb if self.total_memory_gb > 0 else 0

    @property
    def is_memory_constrained(self) -> bool:
        """Check if system is memory constrained."""
        return self.pressure_level in [MemoryPressure.HIGH, MemoryPressure.CRITICAL]


class MemoryPool:
    """
    Memory pool for efficient allocation and reuse.

    Provides a pool-based memory allocation system to reduce allocation overhead
    and improve memory locality.
    """

    def __init__(self, block_size_mb: int = 64, max_blocks: int = 10):
        """
        Initialize memory pool.

        Args:
            block_size_mb: Size of each memory block in MB
            max_blocks: Maximum number of blocks to allocate
        """
        self.block_size_bytes = block_size_mb * 1024 * 1024
        self.max_blocks = max_blocks
        self.allocated_blocks: List[bytearray] = []
        self.available_blocks: List[bytearray] = []
        self._lock = threading.RLock()

    def allocate(self, size_bytes: int) -> Optional[bytearray]:
        """
        Allocate memory from the pool.

        Args:
            size_bytes: Size of memory to allocate

        Returns:
            Allocated memory block or None if allocation failed
        """
        with self._lock:
            # Check if we can satisfy from available blocks
            for block in self.available_blocks:
                if len(block) >= size_bytes:
                    self.available_blocks.remove(block)
                    return block

            # Allocate new block if under limit
            if len(self.allocated_blocks) < self.max_blocks:
                block = bytearray(max(size_bytes, self.block_size_bytes))
                self.allocated_blocks.append(block)
                return block

            return None

    def free(self, block: bytearray) -> None:
        """
        Return memory block to the pool.

        Args:
            block: Memory block to return
        """
        with self._lock:
            if block in self.allocated_blocks and block not in self.available_blocks:
                # Clear the block for reuse
                block[:] = b"\x00"
                self.available_blocks.append(block)

    def cleanup(self) -> None:
        """Clean up all allocated memory."""
        with self._lock:
            self.allocated_blocks.clear()
            self.available_blocks.clear()


class MemoryMonitor:
    """
    System memory monitoring and pressure detection.

    Monitors system memory usage and provides pressure level assessment
    for adaptive resource management.
    """

    def __init__(self, update_interval_seconds: float = 1.0):
        """
        Initialize memory monitor.

        Args:
            update_interval_seconds: How often to update memory stats
        """
        self.logger = get_logger(__name__)
        self.update_interval = update_interval_seconds
        self._stats = MemoryStats(0, 0, 0, 0)
        self._lock = threading.RLock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[MemoryStats], None]] = []

    def start_monitoring(self) -> None:
        """Start memory monitoring thread."""
        with self._lock:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, name="MemoryMonitor", daemon=True
            )
            self._monitor_thread.start()
            self.logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        with self._lock:
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2.0)

            self.logger.info("Memory monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._update_stats()
                self._check_pressure_levels()

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(self._stats)
                    except Exception as e:
                        self.logger.warning(f"Memory monitor callback failed: {e}")

            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")

            time.sleep(self.update_interval)

    def _update_stats(self) -> None:
        """Update current memory statistics."""
        try:
            mem = psutil.virtual_memory()

            with self._lock:
                self._stats.total_memory_gb = mem.total / (1024**3)
                self._stats.available_memory_gb = mem.available / (1024**3)
                self._stats.used_memory_gb = mem.used / (1024**3)
                self._stats.memory_percent = mem.percent

                # Update pressure level based on usage
                if mem.percent > 90:
                    self._stats.pressure_level = MemoryPressure.CRITICAL
                elif mem.percent > 75:
                    self._stats.pressure_level = MemoryPressure.HIGH
                elif mem.percent > 50:
                    self._stats.pressure_level = MemoryPressure.MEDIUM
                else:
                    self._stats.pressure_level = MemoryPressure.LOW

        except Exception as e:
            self.logger.warning(f"Failed to update memory stats: {e}")

    def _check_pressure_levels(self) -> None:
        """Check and log memory pressure levels."""
        stats = self._stats

        if stats.pressure_level == MemoryPressure.CRITICAL:
            self.logger.warning(
                f"Critical memory pressure: {stats.memory_percent:.1f}% used "
                f"({stats.used_memory_gb:.1f}GB/{stats.total_memory_gb:.1f}GB)"
            )
        elif stats.pressure_level == MemoryPressure.HIGH:
            self.logger.info(
                f"High memory pressure: {stats.memory_percent:.1f}% used "
                f"({stats.used_memory_gb:.1f}GB/{stats.total_memory_gb:.1f}GB)"
            )

    @log_function_call
    def get_memory_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            Current memory stats
        """
        with self._lock:
            return MemoryStats(
                total_memory_gb=self._stats.total_memory_gb,
                available_memory_gb=self._stats.available_memory_gb,
                used_memory_gb=self._stats.used_memory_gb,
                memory_percent=self._stats.memory_percent,
                gpu_memory_used_gb=self._stats.gpu_memory_used_gb,
                gpu_memory_total_gb=self._stats.gpu_memory_total_gb,
                pressure_level=self._stats.pressure_level,
            )

    def add_pressure_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """
        Add callback for memory pressure notifications.

        Args:
            callback: Function to call when memory stats update
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_pressure_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """
        Remove memory pressure callback.

        Args:
            callback: Callback to remove
        """
        with self._lock:
            try:
                self._callbacks.remove(callback)
            except ValueError:
                pass


class MemoryManager:
    """
    Comprehensive memory management system.

    Coordinates memory allocation, monitoring, and cleanup across the application.
    Provides adaptive memory management based on system resources and usage patterns.
    """

    def __init__(self, max_memory_gb: float = 2.0):
        """
        Initialize memory manager.

        Args:
            max_memory_gb: Maximum memory usage limit
        """
        self.logger = get_logger(__name__)
        self.max_memory_gb = max_memory_gb

        # Core components
        self.monitor = MemoryMonitor()
        self.memory_pool = MemoryPool(block_size_mb=64, max_blocks=8)

        # Tracking
        self.allocation_tracking: Dict[str, List[int]] = defaultdict(list)
        self._lock = threading.RLock()

        # Start monitoring
        self.monitor.start_monitoring()

        # Register cleanup callback
        self.monitor.add_pressure_callback(self._on_memory_pressure)

        self.logger.info(f"MemoryManager initialized with {max_memory_gb}GB limit")

    def _on_memory_pressure(self, stats: MemoryStats) -> None:
        """
        Handle memory pressure events.

        Args:
            stats: Current memory statistics
        """
        if stats.pressure_level == MemoryPressure.CRITICAL:
            self.logger.warning("Critical memory pressure detected - triggering cleanup")
            self.force_cleanup()
        elif stats.pressure_level == MemoryPressure.HIGH:
            self.logger.info("High memory pressure detected - performing maintenance cleanup")
            self.maintenance_cleanup()

    @log_function_call
    def allocate_memory(self, size_bytes: int, owner: str = "unknown") -> Optional[bytearray]:
        """
        Allocate memory with tracking and limits.

        Args:
            size_bytes: Size of memory to allocate in bytes
            owner: Identifier for the allocation owner

        Returns:
            Allocated memory block or None if allocation failed
        """
        size_gb = size_bytes / (1024**3)
        stats = self.monitor.get_memory_stats()

        with self._lock:
            # Check memory limits
            if stats.used_memory_gb + size_gb > self.max_memory_gb:
                self.logger.warning(
                    f"Memory allocation denied: would exceed {self.max_memory_gb}GB limit "
                    f"(current: {stats.used_memory_gb:.2f}GB, requested: {size_gb:.2f}GB)"
                )
                return None

            # Try pool allocation first
            block = self.memory_pool.allocate(size_bytes)
            if block:
                self.allocation_tracking[owner].append(len(block))
                self.logger.debug(f"Allocated {len(block)} bytes from pool for {owner}")
                return block

            # Fallback to direct allocation if pool fails
            try:
                block = bytearray(size_bytes)
                self.allocation_tracking[owner].append(len(block))
                self.logger.debug(f"Direct allocated {len(block)} bytes for {owner}")
                return block
            except MemoryError:
                self.logger.error(f"Memory allocation failed for {owner}: {size_bytes} bytes")
                return None

    @log_function_call
    def free_memory(self, block: bytearray, owner: str = "unknown") -> None:
        """
        Free allocated memory.

        Args:
            block: Memory block to free
            owner: Identifier for the allocation owner
        """
        with self._lock:
            try:
                # Try to return to pool
                self.memory_pool.free(block)
                self.logger.debug(f"Returned {len(block)} bytes to pool for {owner}")
            except Exception as e:
                self.logger.warning(f"Failed to return block to pool: {e}")

            # Remove from tracking
            if owner in self.allocation_tracking:
                try:
                    self.allocation_tracking[owner].remove(len(block))
                except ValueError:
                    pass

    @log_function_call
    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        Get summary of current memory allocations.

        Returns:
            Dictionary with allocation summary
        """
        with self._lock:
            total_allocated = sum(sum(sizes) for sizes in self.allocation_tracking.values())

            return {
                "total_allocated_bytes": total_allocated,
                "total_allocated_gb": total_allocated / (1024**3),
                "allocation_count": sum(len(sizes) for sizes in self.allocation_tracking.values()),
                "owners": dict(self.allocation_tracking),
                "memory_stats": self.monitor.get_memory_stats().__dict__,
            }

    @log_function_call
    def maintenance_cleanup(self) -> int:
        """
        Perform maintenance cleanup of unused resources.

        Returns:
            Number of cleanup operations performed
        """
        cleanup_count = 0

        # Force garbage collection
        collected = gc.collect()
        if collected > 0:
            self.logger.debug(f"Garbage collection freed {collected} objects")
            cleanup_count += 1

        # Clean up memory pool
        # Note: Pool cleanup is conservative to avoid disrupting active operations

        return cleanup_count

    @log_function_call
    def force_cleanup(self) -> int:
        """
        Perform aggressive cleanup when memory pressure is critical.

        Returns:
            Number of cleanup operations performed
        """
        self.logger.warning("Performing force cleanup due to critical memory pressure")

        cleanup_count = 0

        # Aggressive garbage collection
        for _ in range(3):
            collected = gc.collect()
            if collected > 0:
                cleanup_count += 1

        # Clean memory pool more aggressively
        # Note: In a real implementation, this might involve clearing caches,
        # releasing GPU memory, etc.

        if cleanup_count > 0:
            self.logger.info(f"Force cleanup completed: {cleanup_count} operations")

        return cleanup_count

    @log_function_call
    def check_memory_limits(self, requested_gb: float) -> bool:
        """
        Check if a memory allocation would exceed limits.

        Args:
            requested_gb: Amount of memory requested in GB

        Returns:
            True if allocation is allowed, False otherwise
        """
        stats = self.monitor.get_memory_stats()
        projected_usage = stats.used_memory_gb + requested_gb

        return projected_usage <= self.max_memory_gb

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.monitor.stop_monitoring()
            self.memory_pool.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None
_memory_manager_lock = threading.RLock()


def get_memory_manager() -> MemoryManager:
    """
    Get the global memory manager instance.

    Returns:
        MemoryManager instance
    """
    global _memory_manager

    with _memory_manager_lock:
        if _memory_manager is None:
            _memory_manager = MemoryManager()

        return _memory_manager
