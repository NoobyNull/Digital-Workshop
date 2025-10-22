"""
Background Loading Manager for multi-threaded STL parsing.

This module provides the main coordinator for background loading operations,
managing the lifecycle of multi-threaded parsing jobs and coordinating
between UI and worker threads.
"""

import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Any, List
from enum import Enum

from src.core.logging_config import get_logger, log_function_call
from src.core.cancellation_token import CancellationToken
from src.core.memory_manager import get_memory_manager
from src.core.performance_profiler import get_performance_profiler, PerformanceMetric
from src.parsers.file_chunker import FileChunker
from src.parsers.adaptive_chunker import AdaptiveChunker
from src.parsers.thread_pool_coordinator import ThreadPoolCoordinator
from src.parsers.base_parser import Model, ProgressCallback


class LoadingState(Enum):
    """States for background loading operations."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    CHUNKING = "chunking"
    PARSING = "parsing"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class LoadingJob:
    """Represents a background loading job."""
    job_id: str
    file_path: Path
    state: LoadingState
    progress: float
    status_message: str
    start_time: float
    cancellation_token: CancellationToken
    future: Optional[Future] = None
    result: Optional[Model] = None
    error: Optional[Exception] = None


class BackgroundLoadingManager:
    """
    Main coordinator for background loading operations.

    This class manages the lifecycle of multi-threaded parsing jobs,
    coordinates between UI and worker threads, and handles cancellation
    requests from users.
    """

    def __init__(self, max_concurrent_jobs: int = 2):
        """
        Initialize the background loading manager.

        Args:
            max_concurrent_jobs: Maximum number of concurrent loading jobs
        """
        self.logger = get_logger(__name__)
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: Dict[str, LoadingJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs, thread_name_prefix="bg-loader")
        self._lock = threading.RLock()

        # Initialize components
        self.chunker = FileChunker()
        self.adaptive_chunker = AdaptiveChunker()
        self.coordinator = ThreadPoolCoordinator()

        # Initialize infrastructure components
        self.memory_manager = get_memory_manager()
        self.profiler = get_performance_profiler()

        self.logger.info(f"BackgroundLoadingManager initialized with max {max_concurrent_jobs} concurrent jobs")

    @log_function_call
    def load_file_async(
        self,
        file_path: str,
        progress_callback: Optional[ProgressCallback] = None,
        completion_callback: Optional[Callable[[str, Optional[Model], Optional[Exception]], None]] = None
    ) -> str:
        """
        Start an asynchronous file loading operation.

        Args:
            file_path: Path to the file to load
            progress_callback: Callback for progress updates
            completion_callback: Callback when loading completes

        Returns:
            Job ID for tracking the operation

        Raises:
            RuntimeError: If maximum concurrent jobs exceeded
        """
        file_path_obj = Path(file_path)

        with self._lock:
            # Check concurrent job limit
            active_jobs = [job for job in self.jobs.values() if job.state not in [LoadingState.COMPLETED, LoadingState.CANCELLED, LoadingState.FAILED]]
            if len(active_jobs) >= self.max_concurrent_jobs:
                raise RuntimeError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) exceeded")

            # Create job
            job_id = str(uuid.uuid4())
            cancellation_token = CancellationToken()

            job = LoadingJob(
                job_id=job_id,
                file_path=file_path_obj,
                state=LoadingState.INITIALIZING,
                progress=0.0,
                status_message="Initializing...",
                start_time=time.time(),
                cancellation_token=cancellation_token
            )

            self.jobs[job_id] = job

        # Submit job to executor
        future = self.executor.submit(self._execute_loading_job, job, progress_callback)
        job.future = future

        # Add completion callback
        def on_completion(fut: Future):
            try:
                result = fut.result()
                with self._lock:
                    job.result = result
                    job.state = LoadingState.COMPLETED
                    job.progress = 100.0
                    job.status_message = "Completed"
                self.logger.info(f"Loading job {job_id} completed successfully")
            except Exception as e:
                with self._lock:
                    job.error = e
                    job.state = LoadingState.FAILED
                    job.status_message = f"Failed: {str(e)}"
                self.logger.error(f"Loading job {job_id} failed: {e}")
            finally:
                if completion_callback:
                    completion_callback(job_id, job.result, job.error)

        future.add_done_callback(on_completion)

        self.logger.info(f"Started background loading job {job_id} for {file_path}")
        return job_id

    @log_function_call
    def cancel_loading(self, job_id: str) -> bool:
        """
        Cancel a loading operation.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if cancellation was initiated, False if job not found or already completed
        """
        start_time = time.time()

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                self.logger.warning(f"Attempted to cancel unknown job {job_id}")
                return False

            if job.state in [LoadingState.COMPLETED, LoadingState.CANCELLED, LoadingState.FAILED]:
                self.logger.info(f"Job {job_id} already in terminal state: {job.state.value}")
                return False

            # Initiate cancellation
            job.cancellation_token.cancel()
            job.state = LoadingState.CANCELLED
            job.status_message = "Cancelling..."

            # Cancel the future if it exists
            if job.future and not job.future.done():
                job.future.cancel()

            self.logger.info(f"Initiated cancellation for job {job_id}")

            # Ensure cancellation response time is under 500ms
            elapsed = time.time() - start_time
            if elapsed > 0.5:
                self.logger.warning(f"Cancellation response time exceeded 500ms: {elapsed:.3f}s")

            return True

    @log_function_call
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a loading job.

        Args:
            job_id: ID of the job to query

        Returns:
            Job status dictionary or None if job not found
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None

            return {
                "job_id": job.job_id,
                "file_path": str(job.file_path),
                "state": job.state.value,
                "progress": job.progress,
                "status_message": job.status_message,
                "elapsed_time": time.time() - job.start_time,
                "is_cancelled": job.cancellation_token.is_cancelled()
            }

    @log_function_call
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all loading jobs.

        Returns:
            Dictionary mapping job IDs to status dictionaries
        """
        with self._lock:
            return {job_id: self.get_job_status(job_id) for job_id in self.jobs.keys()}

    @log_function_call
    def cleanup_completed_jobs(self, max_age_seconds: int = 300) -> int:
        """
        Clean up old completed jobs.

        Args:
            max_age_seconds: Maximum age of completed jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        current_time = time.time()
        to_remove = []

        with self._lock:
            for job_id, job in self.jobs.items():
                if job.state in [LoadingState.COMPLETED, LoadingState.CANCELLED, LoadingState.FAILED]:
                    if current_time - job.start_time > max_age_seconds:
                        to_remove.append(job_id)

            for job_id in to_remove:
                del self.jobs[job_id]

        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old jobs")

        return len(to_remove)

    def _execute_loading_job(
        self,
        job: LoadingJob,
        progress_callback: Optional[ProgressCallback]
    ) -> Model:
        """
        Execute a loading job in the background with enhanced infrastructure.

        Args:
            job: The loading job to execute
            progress_callback: Progress callback from caller

        Returns:
            Parsed model

        Raises:
            Exception: If loading fails
        """
        with self.profiler.time_operation(f"load_{job.file_path.name}", PerformanceMetric.LOAD_TIME):
            try:
                # Update job state
                job.state = LoadingState.CHUNKING
                job.status_message = "Analyzing file structure..."

                # Use adaptive chunking for better performance
                file_size_gb = job.file_path.stat().st_size / (1024**3)
                if file_size_gb > 0.5:  # Use adaptive chunking for files > 500MB
                    chunks = self.adaptive_chunker.create_adaptive_chunks(job.file_path)
                    self.logger.info(f"Using adaptive chunking: created {len(chunks)} chunks")
                else:
                    chunks = self.chunker.create_chunks(job.file_path, target_chunk_size_mb=50)

                if job.cancellation_token.is_cancelled():
                    raise Exception("Loading was cancelled")

                # Update job state
                job.state = LoadingState.PARSING
                job.status_message = f"Processing {len(chunks)} chunks..."

                # Check memory limits before proceeding
                total_chunk_memory = sum(chunk.get_memory_estimate() for chunk in chunks)
                if not self.memory_manager.check_memory_limits(total_chunk_memory / (1024**3)):
                    raise Exception("Insufficient memory for loading operation")

                # Coordinate parsing with enhanced progress tracking
                def enhanced_progress_callback(progress: float, message: str):
                    self._update_job_progress(job, progress, message, progress_callback)

                    # Record performance metrics
                    self.profiler.record_sample(
                        PerformanceMetric.LOAD_TIME,
                        progress,
                        f"load_{job.file_path.name}",
                        {"phase": "parsing", "chunks": len(chunks)}
                    )

                result = self.coordinator.coordinate_parsing(
                    chunks=chunks,
                    cancellation_token=job.cancellation_token,
                    progress_callback=enhanced_progress_callback
                )

                if job.cancellation_token.is_cancelled():
                    raise Exception("Loading was cancelled")

                # Update final state
                job.state = LoadingState.AGGREGATING
                job.status_message = "Finalizing..."

                # Aggregation is handled by coordinator
                job.state = LoadingState.COMPLETED
                job.progress = 100.0
                job.status_message = "Completed"

                # Log performance metrics
                self.logger.info(
                    f"Loading completed: {job.file_path.name} "
                    f"({len(chunks)} chunks, {job.file_path.stat().st_size / (1024*1024):.1f}MB)"
                )

                return result

            except Exception as e:
                job.state = LoadingState.FAILED
                job.status_message = f"Failed: {str(e)}"

                # Log failure with context
                self.logger.error(
                    f"Loading failed: {job.file_path.name} - {str(e)}",
                    extra={
                        "file_path": str(job.file_path),
                        "file_size": job.file_path.stat().st_size,
                        "error_type": type(e).__name__
                    }
                )
                raise

    def _update_job_progress(
        self,
        job: LoadingJob,
        progress: float,
        message: str,
        callback: Optional[ProgressCallback]
    ) -> None:
        """
        Update job progress and notify callback.

        Args:
            job: The loading job
            progress: Progress percentage (0-100)
            message: Status message
            callback: Progress callback to notify
        """
        with self._lock:
            job.progress = progress
            job.status_message = message

        if callback:
            callback(progress, message)

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    def cleanup_on_error(self, job_id: str) -> None:
        """
        Clean up resources associated with a failed job.

        Args:
            job_id: Job ID to clean up
        """
        try:
            with self._lock:
                if job_id in self.jobs:
                    job = self.jobs[job_id]

                    # Cancel the future if it's still running
                    if job.future and not job.future.done():
                        job.future.cancel()

                    # Clean up job resources
                    job.cancellation_token = None
                    job.result = None
                    job.error = None

                    # Remove from active jobs
                    del self.jobs[job_id]

            self.logger.debug(f"Cleaned up resources for failed job {job_id}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup job {job_id}: {e}")

    def get_error_recovery_suggestions(self, error: Exception) -> List[str]:
        """
        Get recovery suggestions for a given error.

        Args:
            error: The exception that occurred

        Returns:
            List of recovery suggestions
        """
        suggestions = []
        error_message = str(error).lower()

        try:
            if "memory" in error_message:
                suggestions.extend([
                    "Reduce model complexity or use a smaller file",
                    "Close other applications to free up memory",
                    "Try loading the model synchronously instead"
                ])
            elif "thread" in error_message or "pool" in error_message:
                suggestions.extend([
                    "Wait for other background operations to complete",
                    "Try loading the model synchronously instead",
                    "Reduce concurrent background operations"
                ])
            elif "file" in error_message or "permission" in error_message:
                suggestions.extend([
                    "Check file permissions and accessibility",
                    "Ensure the file is not corrupted",
                    "Try copying the file to a different location"
                ])
            elif "timeout" in error_message:
                suggestions.extend([
                    "Try loading the model synchronously instead",
                    "Check system performance and available resources",
                    "Consider using a smaller or simpler model"
                ])
            else:
                suggestions.extend([
                    "Try loading the model using synchronous loading",
                    "Check application logs for more details",
                    "Restart the application and try again"
                ])

        except Exception as e:
            self.logger.warning(f"Failed to generate error recovery suggestions: {e}")
            suggestions = ["Check application logs for more details"]

        return suggestions