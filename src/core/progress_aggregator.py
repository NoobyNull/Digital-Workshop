"""
Progress aggregation for multi-threaded operations.

This module provides functionality to aggregate progress from multiple
worker threads into unified progress reports for UI display.
"""

import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.core.logging_config import get_logger, log_function_call


@dataclass
class SubOperationProgress:
    """Progress information for a sub-operation within a chunk."""

    operation_id: str
    progress: float = 0.0  # 0-100
    status: str = "pending"
    weight: float = 1.0  # Relative weight in overall chunk progress
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def is_completed(self) -> bool:
        """Check if sub-operation is completed."""
        return self.progress >= 100.0

    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None


@dataclass
class ChunkProgress:
    """Progress information for a single chunk."""

    chunk_id: str
    progress: float = 0.0  # 0-100
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    sub_operations: Dict[str, SubOperationProgress] = None

    def __post_init__(self) -> None:
        """TODO: Add docstring."""
        if self.sub_operations is None:
            self.sub_operations = {}

    @property
    def is_completed(self) -> bool:
        """Check if chunk processing is completed."""
        return self.progress >= 100.0

    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None

    def calculate_weighted_progress(self) -> float:
        """Calculate progress based on weighted sub-operations."""
        if not self.sub_operations:
            return self.progress

        total_weight = sum(op.weight for op in self.sub_operations.values())
        if total_weight == 0:
            return self.progress

        weighted_progress = sum(
            (op.progress / 100.0) * op.weight for op in self.sub_operations.values()
        )
        return (weighted_progress / total_weight) * 100.0


class ProgressAggregator:
    """
    Aggregates progress from multiple worker threads.

    This class collects progress updates from individual chunks and
    calculates overall progress for display in the UI.
    """

    def __init__(self, total_chunks: int) -> None:
        """
        Initialize the progress aggregator.

        Args:
            total_chunks: Total number of chunks being processed
        """
        self.total_chunks = total_chunks
        self.chunks: Dict[str, ChunkProgress] = {}
        self._lock = threading.RLock()
        self.logger = get_logger(__name__)

        # Initialize chunk tracking
        for i in range(total_chunks):
            chunk_id = f"chunk_{i:03d}"
            self.chunks[chunk_id] = ChunkProgress(chunk_id=chunk_id)

        self.logger.debug("Initialized progress aggregator for %s chunks", total_chunks)

    @log_function_call
    def update_chunk_progress(
        self,
        chunk_id: str,
        progress: float,
        status: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update progress for a specific chunk.

        Args:
            chunk_id: ID of the chunk being updated
            progress: Progress percentage (0-100)
            status: Optional status message
            error: Optional error message
        """
        with self._lock:
            if chunk_id not in self.chunks:
                self.logger.warning("Unknown chunk ID: %s", chunk_id)
                return

            chunk = self.chunks[chunk_id]

            # Update start time on first progress
            if chunk.start_time is None and progress > 0:
                chunk.start_time = time.time()

            # Update end time when completed
            if progress >= 100.0 and chunk.end_time is None:
                chunk.end_time = time.time()

            chunk.progress = min(100.0, max(0.0, progress))
            if status:
                chunk.status = status
            if error:
                chunk.error = error

            self.logger.debug("Updated chunk %s: {progress:.1f}% - {status}", chunk_id)

    @log_function_call
    def update_sub_operation_progress(
        self,
        chunk_id: str,
        operation_id: str,
        progress: float,
        status: Optional[str] = None,
        weight: float = 1.0,
    ) -> None:
        """
        Update progress for a sub-operation within a chunk.

        Args:
            chunk_id: ID of the parent chunk
            operation_id: ID of the sub-operation
            progress: Progress percentage (0-100)
            status: Optional status message
            weight: Weight for this operation (default: 1.0)
        """
        with self._lock:
            if chunk_id not in self.chunks:
                self.logger.warning("Unknown chunk ID: %s", chunk_id)
                return

            chunk = self.chunks[chunk_id]

            # Get or create sub-operation
            if operation_id not in chunk.sub_operations:
                chunk.sub_operations[operation_id] = SubOperationProgress(
                    operation_id=operation_id, weight=weight
                )

            sub_op = chunk.sub_operations[operation_id]

            # Update start time on first progress
            if sub_op.start_time is None and progress > 0:
                sub_op.start_time = time.time()

            # Update end time when completed
            if progress >= 100.0 and sub_op.end_time is None:
                sub_op.end_time = time.time()

            sub_op.progress = min(100.0, max(0.0, progress))
            if status:
                sub_op.status = status

            # Update chunk progress based on weighted sub-operations
            chunk.progress = chunk.calculate_weighted_progress()

            self.logger.debug(
                f"Updated sub-operation {chunk_id}.{operation_id}: {progress:.1f}% - {status}"
            )

    @log_function_call
    def get_chunk_progress(self, chunk_id: str) -> Optional[ChunkProgress]:
        """
        Get progress information for a specific chunk.

        Args:
            chunk_id: ID of the chunk

        Returns:
            ChunkProgress object or None if not found
        """
        with self._lock:
            return self.chunks.get(chunk_id)

    @log_function_call
    def calculate_overall_progress(self) -> float:
        """
        Calculate overall progress across all chunks.

        Returns:
            Overall progress percentage (0-100)
        """
        with self._lock:
            if not self.chunks:
                return 0.0

            total_progress = sum(chunk.progress for chunk in self.chunks.values())
            return total_progress / len(self.chunks)

    @log_function_call
    def get_completed_chunks(self) -> int:
        """
        Get the number of completed chunks.

        Returns:
            Number of chunks with 100% progress
        """
        with self._lock:
            return sum(1 for chunk in self.chunks.values() if chunk.is_completed)

    @log_function_call
    def get_failed_chunks(self) -> List[str]:
        """
        Get list of chunk IDs that have errors.

        Returns:
            List of chunk IDs with errors
        """
        with self._lock:
            return [chunk_id for chunk_id, chunk in self.chunks.items() if chunk.error]

    @log_function_call
    def get_active_chunks(self) -> List[str]:
        """
        Get list of chunk IDs that are currently being processed.

        Returns:
            List of active chunk IDs
        """
        with self._lock:
            return [
                chunk_id
                for chunk_id, chunk in self.chunks.items()
                if chunk.start_time and not chunk.is_completed and not chunk.error
            ]

    @log_function_call
    def get_progress_summary(self) -> Dict:
        """
        Get a summary of current progress.

        Returns:
            Dictionary with progress summary
        """
        with self._lock:
            completed = self.get_completed_chunks()
            failed = len(self.get_failed_chunks())
            active = len(self.get_active_chunks())
            pending = self.total_chunks - completed - failed - active

            # Calculate sub-operation statistics
            total_sub_ops = sum(len(chunk.sub_operations) for chunk in self.chunks.values())
            active_sub_ops = sum(
                len(
                    [
                        op
                        for op in chunk.sub_operations.values()
                        if op.start_time and not op.is_completed
                    ]
                )
                for chunk in self.chunks.values()
            )

            return {
                "total_chunks": self.total_chunks,
                "completed": completed,
                "failed": failed,
                "active": active,
                "pending": pending,
                "overall_progress": self.calculate_overall_progress(),
                "failed_chunks": self.get_failed_chunks(),
                "total_sub_operations": total_sub_ops,
                "active_sub_operations": active_sub_ops,
            }

    @log_function_call
    def reset(self) -> None:
        """Reset all progress tracking."""
        with self._lock:
            self.chunks.clear()
            for i in range(self.total_chunks):
                chunk_id = f"chunk_{i:03d}"
                self.chunks[chunk_id] = ChunkProgress(chunk_id=chunk_id)
            self.logger.debug("Progress aggregator reset")

    def __str__(self) -> str:
        """String representation of progress."""
        summary = self.get_progress_summary()
        return (
            f"ProgressAggregator(total={summary['total_chunks']}, "
            f"completed={summary['completed']}, "
            f"active={summary['active']}, "
            f"failed={summary['failed']}, "
            f"progress={summary['overall_progress']:.1f}%)"
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ProgressAggregator(chunks={len(self.chunks)}, progress={self.calculate_overall_progress():.1f}%)"
