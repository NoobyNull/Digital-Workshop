"""
Pipeline coordinator for the import pipeline.

Lightweight orchestrator that coordinates the execution of pipeline stages.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import List, Optional

from PySide6.QtCore import QObject, QThreadPool

from src.core.import_pipeline.pipeline_models import (
    ImportTask,
    ImportStage,
    ImportStatus,
    PipelineProgress,
    PipelineResult,
)
from src.core.import_pipeline.signals import PipelineSignals
from src.core.import_pipeline.stages.base_stage import BaseStage
from src.core.import_pipeline.resume_detector import ResumeDetector
from src.core.logging_config import get_logger


class PipelineCoordinator(QObject):
    """
    Coordinates the execution of import pipeline stages.

    This is a lightweight orchestrator that:
    1. Manages the list of stages
    2. Executes stages in order for each task
    3. Tracks progress
    4. Emits signals for GUI updates
    5. Handles errors and cancellation

    It does NOT contain business logic - that's in the stages.
    """

    def __init__(
        self,
        stages: List[BaseStage],
        resume_detector: Optional[ResumeDetector] = None,
        thread_pool: Optional[QThreadPool] = None,
        max_workers: int = 1,
    ):
        """
        Initialize the pipeline coordinator.

        Args:
            stages: List of pipeline stages to execute in order
            resume_detector: Optional resume detector for interrupted imports
            thread_pool: Optional thread pool for async operations
            max_workers: How many tasks to process concurrently
        """
        super().__init__()
        self.stages = stages
        self.resume_detector = resume_detector
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self.signals = PipelineSignals()
        self.logger = get_logger(__name__)

        self._is_cancelled = False
        self._tasks: List[ImportTask] = []
        self._completed_count = 0
        self._failed_count = 0
        self.max_workers = max(1, int(max_workers))
        self._stats_lock = Lock()

    def execute(self, tasks: List[ImportTask]) -> None:
        """
        Execute the pipeline for a list of tasks.

        Args:
            tasks: List of import tasks to process
        """
        self._tasks = tasks
        self._completed_count = 0
        self._failed_count = 0
        self._is_cancelled = False

        start_time = time.time()

        try:
            # Emit started signal
            self.signals.pipeline_started.emit(len(tasks))
            self.logger.info("Starting pipeline for %d tasks", len(tasks))

            # Detect resume status if detector available
            if self.resume_detector:
                resume_summary = self.resume_detector.get_resume_summary(tasks)
                self.logger.info("Resume summary: %s", resume_summary)

            # Process each task through all stages concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._run_task_wrapper, task) for task in tasks
                ]
                for future in as_completed(futures):
                    # Re-raise exceptions so pipeline_failed is triggered
                    future.result()

            if self._is_cancelled:
                self.logger.info("Pipeline cancelled")
                self.signals.pipeline_cancelled.emit()
                return

            # Calculate final results
            duration = time.time() - start_time
            result = PipelineResult(
                total_tasks=len(tasks),
                successful_tasks=self._completed_count,
                failed_tasks=self._failed_count,
                skipped_tasks=0,
                total_duration_seconds=duration,
            )

            # Emit completion signal
            self.signals.pipeline_completed.emit(result)
            self.logger.info(
                "Pipeline completed: %d/%d successful in %.2fs",
                self._completed_count,
                len(tasks),
                duration,
            )

        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            self.logger.error("Pipeline error: %s", error_msg, exc_info=True)
            self.signals.pipeline_failed.emit(error_msg)

    def _run_task_wrapper(self, task: ImportTask) -> None:
        """Wrapper for executor tasks to honor cancellation."""

        if self._is_cancelled:
            return
        self._process_task(task)

    def _process_task(self, task: ImportTask) -> None:
        """
        Process a single task through all stages.

        Args:
            task: The import task to process
        """
        try:
            self.signals.task_started.emit(task)

            # Detect completed stages if resume detector available
            completed_stages = []
            if self.resume_detector:
                completed_stages = self.resume_detector.detect_completed_stages(task)
                if completed_stages:
                    self.logger.info(
                        "Task %s has %d completed stages: %s",
                        task.filename,
                        len(completed_stages),
                        [stage.value for stage in completed_stages],
                    )

            # Execute each stage in order
            for stage in self.stages:
                if self._is_cancelled:
                    return

                # Skip stage if already completed
                stage_enum = self._get_stage_enum(stage)
                if stage_enum and stage_enum in completed_stages:
                    self.logger.info(
                        "Skipping completed stage %s for task %s",
                        stage_enum.value,
                        task.filename,
                    )
                    continue

                # Notify stage start for UI/telemetry
                try:
                    stage_name = stage.stage_name.value  # type: ignore[attr-defined]
                except Exception:
                    stage_name = None
                if stage_name:
                    self.signals.stage_started.emit(task, stage_name)

                # Execute stage
                result = stage.execute(task)

                # Check if stage failed
                if not result.success:
                    self._record_failure()
                    self.signals.stage_failed.emit(
                        task,
                        stage_name or "unknown_stage",
                        result.error_message or "Unknown error",
                    )
                    self.signals.task_failed.emit(
                        task, result.error_message or "Unknown error"
                    )
                    return
                else:
                    # Inform listeners of per-stage completion to update UI/logs.
                    self.signals.stage_completed.emit(result)

            # All stages completed successfully
            task.current_stage = ImportStage.COMPLETE
            task.status = ImportStatus.COMPLETED
            self._record_completion()
            self.signals.task_completed.emit(task)

        except Exception as e:
            error_msg = f"Task processing failed: {e}"
            self.logger.error(
                "Error processing task %s: %s", task.filename, error_msg, exc_info=True
            )
            self._record_failure()
            self.signals.task_failed.emit(task, error_msg)

    def _get_stage_enum(self, stage: BaseStage) -> Optional[ImportStage]:
        """
        Get the ImportStage enum for a stage instance.

        Args:
            stage: The stage instance

        Returns:
            The corresponding ImportStage enum or None
        """
        # Map stage class names to ImportStage enums
        stage_class_name = stage.__class__.__name__
        stage_map = {
            "DatabaseStage": ImportStage.DATABASE_INSERT,
            "HashingStage": ImportStage.HASHING,
            "ImagePairingStage": ImportStage.IMAGE_PAIRING,
            "ThumbnailStage": ImportStage.THUMBNAIL_GENERATION,
        }
        return stage_map.get(stage_class_name)

    def _record_completion(self) -> None:
        """Thread-safe helper for completion tracking."""

        with self._stats_lock:
            self._completed_count += 1
            progress = self._current_progress_locked()
        self.signals.progress_updated.emit(progress)

    def _record_failure(self) -> None:
        """Thread-safe helper for failure tracking."""

        with self._stats_lock:
            self._failed_count += 1
            progress = self._current_progress_locked()
        self.signals.progress_updated.emit(progress)

    def _current_progress_locked(self) -> PipelineProgress:
        """Build PipelineProgress assuming stats lock is held."""

        return PipelineProgress(
            total_tasks=len(self._tasks),
            completed_tasks=self._completed_count,
            failed_tasks=self._failed_count,
        )

    def cancel(self) -> None:
        """Cancel the pipeline execution."""
        self._is_cancelled = True
        self.logger.info("Pipeline cancellation requested")
