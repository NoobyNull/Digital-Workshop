"""
Base worker for async pipeline operations.

Defines the abstract interface for all async workers (QRunnable).
"""

from abc import ABC, abstractmethod
from PySide6.QtCore import QRunnable, Slot

from src.core.import_pipeline.pipeline_models import ImportTask
from src.core.import_pipeline.signals import WorkerSignals
from src.core.logging_config import get_logger


class BaseWorker(QRunnable, ABC):
    """
    Abstract base class for all async workers.

    Workers are QRunnable objects that execute in a thread pool.
    They perform the actual heavy lifting for each pipeline stage.

    Each worker:
    1. Takes an ImportTask as input
    2. Performs its specific operation
    3. Emits signals to report progress and results
    4. Returns results via signals (not return values)
    """

    def __init__(self, task: ImportTask):
        """
        Initialize the worker.

        Args:
            task: The import task to process
        """
        super().__init__()
        self.task = task
        self.signals = WorkerSignals()
        self.logger = get_logger(self.__class__.__name__)

        # Enable auto-deletion when task completes
        self.setAutoDelete(True)

    @abstractmethod
    def do_work(self) -> None:
        """
        Perform the actual work.

        This method should:
        1. Do the heavy lifting
        2. Update self.task with results
        3. Emit progress signals as needed
        4. Raise exceptions on failure (will be caught by run())

        Subclasses must implement this method.
        """

    @Slot()
    def run(self) -> None:
        """
        Execute the worker (called by QThreadPool).

        This method handles signal emission and error handling.
        Subclasses should NOT override this - override do_work() instead.
        """
        try:
            # Emit started signal
            self.signals.started.emit(self.task.file_path)
            self.logger.debug("Worker started for %s", self.task.filename)

            # Do the actual work
            self.do_work()

            # Emit completion signal with the updated task
            self.signals.completed.emit(self.task)
            self.logger.debug("Worker completed for %s", self.task.filename)

        except Exception as e:
            error_msg = f"Worker failed: {e}"
            self.logger.error(
                "Worker exception for %s: %s",
                self.task.filename,
                error_msg,
                exc_info=True,
            )

            # Emit failure signal
            self.signals.failed.emit(self.task.file_path, error_msg)
