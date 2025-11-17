"""
Async task classes for non-blocking model library operations.

Uses QRunnable with QThreadPool for truly parallel execution without blocking the UI.
"""

from typing import Any, Dict

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from src.core.logging_config import get_logger
from src.core.database.database_manager import DatabaseManager


logger = get_logger(__name__)


class TaskSignals(QObject):
    """
    Signals for QRunnable tasks.

    QRunnable itself cannot emit signals, so we use a separate QObject.
    """

    # Database task signals
    database_completed = Signal(dict)  # model_info with database IDs
    database_failed = Signal(str, str)  # model_path, error_message

    # Thumbnail task signals
    thumbnail_completed = Signal(dict)  # model_info with thumbnail
    thumbnail_failed = Signal(str, str)  # model_path, error_message

    # Progress signals
    progress_updated = Signal(int, int, str)  # current, total, message


class DatabaseInsertTask(QRunnable):
    """
    QRunnable task for inserting model data into the database.

    Performs all database operations (add_model, add_model_metadata, add_model_analysis)
    in a thread pool worker, preventing UI blocking.
    """

    def __init__(
        self,
        model_info: Dict[str, Any],
        db_manager: DatabaseManager,
        task_index: int = 0,
        total_tasks: int = 1,
    ):
        """
        Initialize the database insert task.

        Args:
            model_info: Dictionary containing model information
            db_manager: Database manager instance
            task_index: Index of this task in the batch
            total_tasks: Total number of tasks in the batch
        """
        super().__init__()
        self.model_info = model_info
        self.db_manager = db_manager
        self.task_index = task_index
        self.total_tasks = total_tasks
        self.signals = TaskSignals()
        self.logger = get_logger(__name__)

        # Enable auto-deletion when task completes
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        """Execute the database insert operations."""
        try:
            filename = self.model_info.get("filename", "unknown")
            self.logger.debug(
                "DatabaseInsertTask [%d/%d]: Starting for %s",
                self.task_index + 1,
                self.total_tasks,
                filename,
            )

            # Insert model record
            model_id = self.db_manager.add_model(
                filename=self.model_info["filename"],
                format=self.model_info["format"],
                file_path=self.model_info["file_path"],
                file_size=self.model_info.get("file_size"),
                file_hash=self.model_info.get("file_hash"),
            )

            # Insert metadata
            self.db_manager.add_model_metadata(
                model_id=model_id,
                title=self.model_info["filename"],
                description="",
            )

            # Insert analysis data
            self.db_manager.add_model_analysis(
                model_id=model_id,
                triangle_count=self.model_info.get("triangle_count"),
                vertex_count=self.model_info.get("vertex_count"),
                min_bounds=self.model_info.get("min_bounds"),
                max_bounds=self.model_info.get("max_bounds"),
                analysis_time_seconds=self.model_info.get("parsing_time"),
            )

            # Add model_id to model_info
            self.model_info["id"] = model_id

            self.logger.debug(
                "DatabaseInsertTask [%d/%d]: Completed for %s (ID: %d)",
                self.task_index + 1,
                self.total_tasks,
                filename,
                model_id,
            )

            # Emit success signal
            self.signals.database_completed.emit(self.model_info)

        except Exception as e:
            error_msg = f"Database insert failed: {e}"
            self.logger.error(
                "DatabaseInsertTask [%d/%d]: Failed for %s - %s",
                self.task_index + 1,
                self.total_tasks,
                self.model_info.get("file_path", "unknown"),
                error_msg,
                exc_info=True,
            )
            self.signals.database_failed.emit(
                self.model_info.get("file_path", "unknown"), error_msg
            )


class ThumbnailGenerationTask(QRunnable):
    """
    QRunnable task for generating model thumbnails.

    Generates thumbnails in a thread pool worker to prevent UI blocking.
    """

    def __init__(
        self,
        model_info: Dict[str, Any],
        thumbnail_generator,
        task_index: int = 0,
        total_tasks: int = 1,
    ):
        """
        Initialize the thumbnail generation task.

        Args:
            model_info: Dictionary containing model information (must have 'id')
            thumbnail_generator: ThumbnailGenerator instance
            task_index: Index of this task in the batch
            total_tasks: Total number of tasks in the batch
        """
        super().__init__()
        self.model_info = model_info
        self.thumbnail_generator = thumbnail_generator
        self.task_index = task_index
        self.total_tasks = total_tasks
        self.signals = TaskSignals()
        self.logger = get_logger(__name__)

        # Enable auto-deletion when task completes
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        """Execute the thumbnail generation."""
        try:
            filename = self.model_info.get("filename", "unknown")
            self.logger.debug(
                "ThumbnailGenerationTask [%d/%d]: Starting for %s",
                self.task_index + 1,
                self.total_tasks,
                filename,
            )

            # Generate thumbnail
            thumbnail = self.thumbnail_generator.generate_thumbnail(self.model_info)

            # Add thumbnail to model_info
            self.model_info["thumbnail"] = thumbnail

            self.logger.debug(
                "ThumbnailGenerationTask [%d/%d]: Completed for %s",
                self.task_index + 1,
                self.total_tasks,
                filename,
            )

            # Emit success signal
            self.signals.thumbnail_completed.emit(self.model_info)

        except Exception as e:
            error_msg = f"Thumbnail generation failed: {e}"
            self.logger.error(
                "ThumbnailGenerationTask [%d/%d]: Failed for %s - %s",
                self.task_index + 1,
                self.total_tasks,
                self.model_info.get("file_path", "unknown"),
                error_msg,
                exc_info=True,
            )
            self.signals.thumbnail_failed.emit(
                self.model_info.get("file_path", "unknown"), error_msg
            )


class CombinedModelProcessingTask(QRunnable):
    """
    QRunnable task that combines database insert and thumbnail generation.

    This is more efficient than separate tasks as it reduces signal overhead
    and ensures proper ordering of operations.
    """

    def __init__(
        self,
        model_info: Dict[str, Any],
        db_manager: DatabaseManager,
        thumbnail_generator,
        task_index: int = 0,
        total_tasks: int = 1,
    ):
        """
        Initialize the combined processing task.

        Args:
            model_info: Dictionary containing model information
            db_manager: Database manager instance
            thumbnail_generator: ThumbnailGenerator instance
            task_index: Index of this task in the batch
            total_tasks: Total number of tasks in the batch
        """
        super().__init__()
        self.model_info = model_info
        self.db_manager = db_manager
        self.thumbnail_generator = thumbnail_generator
        self.task_index = task_index
        self.total_tasks = total_tasks
        self.signals = TaskSignals()
        self.logger = get_logger(__name__)

        # Enable auto-deletion when task completes
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        """Execute both database insert and thumbnail generation."""
        try:
            filename = self.model_info.get("filename", "unknown")
            self.logger.debug(
                "CombinedTask [%d/%d]: Starting for %s",
                self.task_index + 1,
                self.total_tasks,
                filename,
            )

            # Step 1: Database operations
            model_id = self.db_manager.add_model(
                filename=self.model_info["filename"],
                format=self.model_info["format"],
                file_path=self.model_info["file_path"],
                file_size=self.model_info.get("file_size"),
                file_hash=self.model_info.get("file_hash"),
            )

            self.db_manager.add_model_metadata(
                model_id=model_id,
                title=self.model_info["filename"],
                description="",
            )

            self.db_manager.add_model_analysis(
                model_id=model_id,
                triangle_count=self.model_info.get("triangle_count"),
                vertex_count=self.model_info.get("vertex_count"),
                min_bounds=self.model_info.get("min_bounds"),
                max_bounds=self.model_info.get("max_bounds"),
                analysis_time_seconds=self.model_info.get("parsing_time"),
            )

            self.model_info["id"] = model_id

            # Step 2: Generate thumbnail
            thumbnail = self.thumbnail_generator.generate_thumbnail(self.model_info)
            self.model_info["thumbnail"] = thumbnail

            self.logger.debug(
                "CombinedTask [%d/%d]: Completed for %s (ID: %d)",
                self.task_index + 1,
                self.total_tasks,
                filename,
                model_id,
            )

            # Emit completion signal with all data
            self.signals.database_completed.emit(self.model_info)

        except Exception as e:
            error_msg = f"Model processing failed: {e}"
            self.logger.error(
                "CombinedTask [%d/%d]: Failed for %s - %s",
                self.task_index + 1,
                self.total_tasks,
                self.model_info.get("file_path", "unknown"),
                error_msg,
                exc_info=True,
            )
            self.signals.database_failed.emit(
                self.model_info.get("file_path", "unknown"), error_msg
            )
