"""
GPU Memory Manager for STL Parsing Operations.

This module provides memory-efficient GPU buffer management for large STL files,
with adaptive allocation, memory monitoring, and automatic cleanup.
"""

import threading
from dataclasses import dataclass
from typing import Dict, Optional, Any
from enum import Enum

from src.core.logging_config import get_logger, log_function_call
from src.core.gpu_acceleration import get_gpu_accelerator, GPUBuffer


class MemoryStrategy(Enum):
    """Memory allocation strategies for different file sizes."""

    CONSERVATIVE = "conservative"  # Small chunks, frequent sync
    BALANCED = "balanced"  # Medium chunks, balanced throughput
    AGGRESSIVE = "aggressive"  # Large chunks, maximum throughput


@dataclass
class MemoryStats:
    """GPU memory usage statistics."""

    allocated_bytes: int = 0
    peak_usage_bytes: int = 0
    available_bytes: int = 0
    fragmentation_ratio: float = 0.0
    allocation_count: int = 0


class GPUMemoryManager:
    """
    Manages GPU memory allocation and deallocation for STL parsing operations.

    Provides:
    - Adaptive memory allocation based on file size and GPU capabilities
    - Memory usage monitoring and leak detection
    - Automatic cleanup and resource management
    - Memory-efficient data streaming for large files
    """

    def __init__(self):
        """Initialize GPU memory manager."""
        self.logger = get_logger(__name__)
        self.gpu_accelerator = get_gpu_accelerator()
        self._lock = threading.RLock()

        # Memory tracking
        self.active_buffers: Dict[str, GPUBuffer] = {}
        self.memory_stats = MemoryStats()
        self.allocation_strategy = MemoryStrategy.BALANCED

        # Configuration based on GPU capabilities
        self._configure_for_gpu()

    @log_function_call
    def _configure_for_gpu(self) -> None:
        """Configure memory manager based on GPU capabilities."""
        device_info = self.gpu_accelerator.get_device_info()

        if device_info.get("available", False):
            memory_gb = device_info.get("memory_gb", 0)
            if memory_gb >= 16:
                self.allocation_strategy = MemoryStrategy.AGGRESSIVE
            elif memory_gb >= 8:
                self.allocation_strategy = MemoryStrategy.BALANCED
            else:
                self.allocation_strategy = MemoryStrategy.CONSERVATIVE

            self.memory_stats.available_bytes = int(memory_gb * 1024 * 1024 * 1024)
            self.logger.info(
                f"GPU memory manager configured for {memory_gb}GB GPU (strategy: {self.allocation_strategy.value})"
            )
        else:
            self.allocation_strategy = MemoryStrategy.CONSERVATIVE
            self.memory_stats.available_bytes = 2 * 1024 * 1024 * 1024  # 2GB CPU fallback
            self.logger.info("GPU memory manager configured for CPU fallback")

    @log_function_call
    def allocate_stl_buffer(self, triangle_count: int, buffer_type: str) -> Optional[GPUBuffer]:
        """
        Allocate GPU buffer optimized for STL triangle data.

        Args:
            triangle_count: Number of triangles to allocate for
            buffer_type: Type of buffer ('vertices', 'normals', 'raw_data')

        Returns:
            GPUBuffer instance or None if allocation failed
        """
        with self._lock:
            try:
                # Calculate buffer size based on type
                size_bytes = self._calculate_buffer_size(triangle_count, buffer_type)

                # Check memory limits
                if not self._can_allocate(size_bytes):
                    self.logger.warning(
                        f"Cannot allocate {size_bytes} bytes, would exceed memory limits"
                    )
                    return None

                # Allocate buffer
                buffer = self.gpu_accelerator.allocate_buffer(size_bytes)
                if buffer:
                    buffer_id = f"stl_{buffer_type}_{triangle_count}_{id(buffer)}"
                    self.active_buffers[buffer_id] = buffer
                    self.memory_stats.allocated_bytes += size_bytes
                    self.memory_stats.allocation_count += 1
                    self.memory_stats.peak_usage_bytes = max(
                        self.memory_stats.peak_usage_bytes,
                        self.memory_stats.allocated_bytes,
                    )

                    self.logger.debug("Allocated STL buffer: %s ({size_bytes} bytes)", buffer_id)
                    return buffer
                else:
                    self.logger.error("GPU buffer allocation failed for %s bytes", size_bytes)
                    return None

            except Exception as e:
                self.logger.error("Error allocating STL buffer: %s", e)
                return None

    def _calculate_buffer_size(self, triangle_count: int, buffer_type: str) -> int:
        """Calculate buffer size in bytes for given triangle count and type."""
        if buffer_type == "vertices":
            # 9 floats per triangle (3 vertices × 3 coordinates)
            return triangle_count * 9 * 4  # 4 bytes per float
        elif buffer_type == "normals":
            # 9 floats per triangle (3 normals × 3 coordinates)
            return triangle_count * 9 * 4
        elif buffer_type == "raw_data":
            # Raw STL data: 50 bytes per triangle
            return triangle_count * 50
        elif buffer_type == "validation_flags":
            # 1 byte per triangle for validation flags
            return triangle_count
        else:
            raise ValueError(f"Unknown buffer type: {buffer_type}")

    def _can_allocate(self, size_bytes: int) -> bool:
        """Check if allocation would exceed memory limits."""
        # Reserve 20% of GPU memory for other operations
        reserve_bytes = int(self.memory_stats.available_bytes * 0.2)
        available_for_allocation = self.memory_stats.available_bytes - reserve_bytes

        projected_usage = self.memory_stats.allocated_bytes + size_bytes
        return projected_usage <= available_for_allocation

    @log_function_call
    def get_optimal_chunk_size(self, file_size_bytes: int, triangle_count: int) -> int:
        """
        Calculate optimal chunk size for processing based on memory strategy.

        Args:
            file_size_bytes: Total file size in bytes
            triangle_count: Total number of triangles

        Returns:
            Optimal triangle count per chunk
        """
        # Base calculations
        avg_triangle_bytes = file_size_bytes / max(triangle_count, 1)
        memory_per_triangle = avg_triangle_bytes * 3  # vertices + normals + raw data

        if self.allocation_strategy == MemoryStrategy.CONSERVATIVE:
            # Small chunks: use 10% of available memory
            max_chunk_memory = int(self.memory_stats.available_bytes * 0.1)
            chunk_triangles = int(max_chunk_memory / memory_per_triangle)
            return max(1000, min(chunk_triangles, 50000))  # 1K to 50K triangles

        elif self.allocation_strategy == MemoryStrategy.BALANCED:
            # Medium chunks: use 25% of available memory
            max_chunk_memory = int(self.memory_stats.available_bytes * 0.25)
            chunk_triangles = int(max_chunk_memory / memory_per_triangle)
            return max(10000, min(chunk_triangles, 200000))  # 10K to 200K triangles

        else:  # AGGRESSIVE
            # Large chunks: use 50% of available memory
            max_chunk_memory = int(self.memory_stats.available_bytes * 0.5)
            chunk_triangles = int(max_chunk_memory / memory_per_triangle)
            return max(50000, min(chunk_triangles, 1000000))  # 50K to 1M triangles

    @log_function_call
    def stream_file_to_gpu(
        self,
        file_path: str,
        triangle_count: int,
        progress_callback: Optional[Any] = None,
    ) -> Optional[GPUBuffer]:
        """
        Stream large STL file to GPU memory in chunks.

        Args:
            file_path: Path to STL file
            triangle_count: Total triangles in file
            progress_callback: Optional progress callback

        Returns:
            GPU buffer containing file data or None if failed
        """
        try:
            chunk_size = self.get_optimal_chunk_size(
                triangle_count * 50, triangle_count  # Estimate file size
            )

            # Allocate output buffer
            output_buffer = self.allocate_stl_buffer(triangle_count, "raw_data")
            if not output_buffer:
                return None

            # Process file in chunks
            with open(file_path, "rb") as file:
                # Skip header (80 bytes)
                file.seek(80)

                # Skip triangle count (4 bytes)
                file.seek(4, 1)

                total_processed = 0
                chunk_idx = 0

                while total_processed < triangle_count:
                    current_chunk_size = min(chunk_size, triangle_count - total_processed)

                    # Read chunk data
                    chunk_bytes = file.read(current_chunk_size * 50)
                    if len(chunk_bytes) != current_chunk_size * 50:
                        self.logger.error("Incomplete read at chunk %s", chunk_idx)
                        self.free_buffer(output_buffer)
                        return None

                    # Upload to GPU
                    offset = total_processed * 50
                    if not output_buffer.copy_to_device(chunk_bytes, offset):
                        self.logger.error("GPU upload failed at chunk %s", chunk_idx)
                        self.free_buffer(output_buffer)
                        return None

                    total_processed += current_chunk_size
                    chunk_idx += 1

                    # Progress reporting
                    if progress_callback:
                        progress = total_processed / triangle_count
                        progress_callback.report(progress * 100, f"Streaming chunk {chunk_idx}")

            self.logger.info("Successfully streamed %s triangles to GPU", triangle_count)
            return output_buffer

        except Exception as e:
            self.logger.error("Error streaming file to GPU: %s", e)
            return None

    @log_function_call
    def free_buffer(self, buffer: GPUBuffer) -> None:
        """
        Free a GPU buffer and update memory statistics.

        Args:
            buffer: Buffer to free
        """
        with self._lock:
            try:
                # Find and remove from active buffers
                buffer_id = None
                for bid, buf in self.active_buffers.items():
                    if buf is buffer:
                        buffer_id = bid
                        break

                if buffer_id:
                    del self.active_buffers[buffer_id]

                # Update memory stats
                self.memory_stats.allocated_bytes -= buffer.size_bytes
                self.memory_stats.allocation_count -= 1

                # Free GPU memory
                buffer.free()

                self.logger.debug("Freed GPU buffer: %s ({buffer.size_bytes} bytes)", buffer_id)

            except Exception as e:
                self.logger.error("Error freeing GPU buffer: %s", e)

    @log_function_call
    def get_memory_stats(self) -> MemoryStats:
        """
        Get current memory usage statistics.

        Returns:
            MemoryStats object with current usage information
        """
        with self._lock:
            # Calculate fragmentation (simplified)
            if self.memory_stats.allocation_count > 0:
                avg_allocation = (
                    self.memory_stats.allocated_bytes / self.memory_stats.allocation_count
                )
                # Fragmentation estimate based on allocation variance
                self.memory_stats.fragmentation_ratio = min(
                    1.0, avg_allocation / (1024 * 1024)
                )  # Rough estimate

            return MemoryStats(
                allocated_bytes=self.memory_stats.allocated_bytes,
                peak_usage_bytes=self.memory_stats.peak_usage_bytes,
                available_bytes=self.memory_stats.available_bytes,
                fragmentation_ratio=self.memory_stats.fragmentation_ratio,
                allocation_count=self.memory_stats.allocation_count,
            )

    @log_function_call
    def cleanup(self) -> None:
        """Clean up all GPU memory resources."""
        with self._lock:
            buffers_to_free = list(self.active_buffers.values())
            for buffer in buffers_to_free:
                self.free_buffer(buffer)

            self.memory_stats = MemoryStats()
            self.logger.info("GPU memory manager cleanup completed")

    def __del__(self):
        """Destructor - ensure cleanup."""
        self.cleanup()


# Global memory manager instance
_gpu_memory_manager: Optional[GPUMemoryManager] = None
_memory_manager_lock = threading.RLock()


def get_gpu_memory_manager() -> GPUMemoryManager:
    """
    Get the global GPU memory manager instance.

    Returns:
        GPUMemoryManager instance
    """
    global _gpu_memory_manager

    with _memory_manager_lock:
        if _gpu_memory_manager is None:
            _gpu_memory_manager = GPUMemoryManager()

        return _gpu_memory_manager
