"""
Base stage for the import pipeline.

Defines the abstract interface that all pipeline stages must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
from PySide6.QtCore import QThreadPool

from src.core.import_pipeline.pipeline_models import (
    ImportTask,
    StageResult,
    ImportStage,
)
from src.core.import_pipeline.signals import StageSignals
from src.core.logging_config import get_logger


class BaseStage(ABC):
    """
    Abstract base class for all pipeline stages.

    Each stage is responsible for:
    1. Checking if work needs to be done (resume detection)
    2. Executing the work (synchronously or asynchronously)
    3. Updating the ImportTask with results
    4. Emitting appropriate signals

    Stages should be lightweight and delegate heavy work to workers.
    """

    def __init__(self, thread_pool: Optional[QThreadPool] = None):
        """
        Initialize the stage.

        Args:
            thread_pool: Optional thread pool for async operations.
                        If None, operations run synchronously.
        """
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self.signals = StageSignals()
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def stage_name(self) -> ImportStage:
        """Return the stage identifier."""

    @abstractmethod
    def should_process(self, task: ImportTask) -> bool:
        """
        Check if this stage should process the task.

        This is used for resume detection - if the work is already done,
        return False to skip this stage.

        Args:
            task: The import task to check

        Returns:
            True if stage should process, False to skip
        """

    @abstractmethod
    def process(self, task: ImportTask) -> StageResult:
        """
        Process the import task.

        This method should:
        1. Perform the stage's work (or dispatch to a worker)
        2. Update the task with results
        3. Return a StageResult

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """

    def execute(self, task: ImportTask) -> StageResult:
        """
        Execute the stage with proper signal emission and error handling.

        This is the main entry point called by the coordinator.

        Args:
            task: The import task to process

        Returns:
            StageResult with success/failure information
        """
        try:
            # Check if we should skip this stage
            if not self.should_process(task):
                self.logger.debug(
                    "Skipping %s for %s (already complete)",
                    self.stage_name.value,
                    task.filename,
                )
                return StageResult(
                    stage=self.stage_name,
                    success=True,
                    task=task,
                    metadata={"skipped": True},
                )

            # Emit started signal
            self.signals.started.emit(task)
            self.logger.debug(
                "Starting %s for %s", self.stage_name.value, task.filename
            )

            # Process the task
            result = self.process(task)

            # Emit completion signal
            if result.success:
                self.signals.completed.emit(result)
                self.logger.debug(
                    "Completed %s for %s", self.stage_name.value, task.filename
                )
            else:
                self.signals.failed.emit(task, result.error_message or "Unknown error")
                self.logger.error(
                    "Failed %s for %s: %s",
                    self.stage_name.value,
                    task.filename,
                    result.error_message,
                )

            return result

        except Exception as e:
            error_msg = f"{self.stage_name.value} failed: {e}"
            self.logger.error(
                "Exception in %s for %s: %s",
                self.stage_name.value,
                task.filename,
                error_msg,
                exc_info=True,
            )

            self.signals.failed.emit(task, error_msg)

            return StageResult(
                stage=self.stage_name,
                success=False,
                task=task,
                error_message=error_msg,
            )
