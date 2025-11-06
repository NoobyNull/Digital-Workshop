"""
Coordinator for thumbnail generation with dedicated window.

This module manages the lifecycle of thumbnail generation, showing a dedicated
non-blocking window with progress tracking and live updates.

Usage:
    coordinator = ThumbnailGenerationCoordinator(parent_window)
    coordinator.generate_thumbnails(
        file_info_list=[(path, hash), ...],
        background=bg_color,
        material=material_name
    )
"""

from typing import List, Tuple, Optional

from PySide6.QtCore import QObject, Signal

from src.core.logging_config import get_logger
from src.gui.thumbnail_generation_worker import ThumbnailGenerationWorker
from src.gui.progress_window.thumbnail_generation_window import ThumbnailGenerationWindow


class ThumbnailGenerationCoordinator(QObject):
    """
    Coordinates thumbnail generation with dedicated window.

    Manages:
    - Worker thread lifecycle
    - Window creation and display
    - Signal connections
    - Progress tracking
    - Cancellation handling
    """

    # Signals
    generation_started = Signal()
    generation_completed = Signal()
    generation_cancelled = Signal()
    generation_failed = Signal(str)  # error_message

    def __init__(self, parent=None):
        """
        Initialize the coordinator.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.parent_widget = parent

        self.worker: Optional[ThumbnailGenerationWorker] = None
        self.window: Optional[ThumbnailGenerationWindow] = None

    def generate_thumbnails(
        self,
        file_info_list: List[Tuple[str, str]],
        background: Optional[str] = None,
        material: Optional[str] = None,
    ) -> None:
        """
        Generate thumbnails with dedicated window.

        Args:
            file_info_list: List of (model_path, file_hash) tuples
            background: Background color or image path
            material: Material name to apply
        """
        if not file_info_list:
            self.logger.warning("No files to process")
            return

        self.logger.info(
            "Starting thumbnail generation for %d files", len(file_info_list)
        )

        # Create window
        self.window = ThumbnailGenerationWindow(
            total_items=len(file_info_list), parent=self.parent_widget
        )

        # Create worker
        self.worker = ThumbnailGenerationWorker(
            file_info_list=file_info_list, background=background, material=material
        )

        # Connect worker signals to window
        self._connect_signals()

        # Show window
        self.window.show_and_raise()

        # Start worker
        self.worker.start()

        self.generation_started.emit()
        self.logger.info("Thumbnail generation window shown and worker started")

    def _connect_signals(self) -> None:
        """Connect worker signals to window and coordinator."""
        if not self.worker or not self.window:
            return

        # Batch progress
        self.worker.batch_progress_updated.connect(
            self.window.update_batch_progress
        )

        # Individual progress
        self.worker.individual_progress_updated.connect(
            self._on_individual_progress_updated
        )

        # File changes
        self.worker.current_file_changed.connect(
            self._on_current_file_changed
        )

        # Completion
        self.worker.finished_batch.connect(self._on_generation_completed)

        # Errors
        self.worker.error_occurred.connect(self._on_error_occurred)

        # Window signals
        self.window.operation_paused.connect(self._on_pause_requested)
        self.window.operation_resumed.connect(self._on_resume_requested)
        self.window.operation_cancelled.connect(self._on_cancel_requested)

        self.logger.debug("Worker and window signals connected")

    def _on_individual_progress_updated(self, percent: int, stage: str) -> None:
        """Handle individual progress update."""
        if self.window:
            # Get current file from window
            current_file = self.window.individual_label.text()
            if current_file.startswith("Current: "):
                current_file = current_file.replace("Current: ", "")
            self.window.update_individual_progress(current_file, percent, stage)

    def _on_current_file_changed(self, filename: str) -> None:
        """Handle current file change."""
        if self.window:
            # Reset individual progress for new file
            self.window.update_individual_progress(filename, 0, "Starting...")

    def _on_generation_completed(self) -> None:
        """Handle generation completion."""
        if self.window:
            self.window.mark_operation_completed()
        self.generation_completed.emit()
        self.logger.info("Thumbnail generation completed")

    def _on_error_occurred(self, file_path: str, error_message: str) -> None:
        """Handle error during generation."""
        self.logger.warning("Error generating thumbnail for %s: %s", file_path, error_message)

    def _on_pause_requested(self) -> None:
        """Handle pause request."""
        if self.worker:
            # TODO: Implement pause in worker
            self.logger.info("Pause requested (not yet implemented)")

    def _on_resume_requested(self) -> None:
        """Handle resume request."""
        if self.worker:
            # TODO: Implement resume in worker
            self.logger.info("Resume requested (not yet implemented)")

    def _on_cancel_requested(self) -> None:
        """Handle cancellation request."""
        if self.worker:
            self.worker.stop()
            self.generation_cancelled.emit()
            self.logger.info("Thumbnail generation cancelled by user")

    def wait_for_completion(self) -> None:
        """Wait for thumbnail generation to complete."""
        if self.worker:
            self.worker.wait()
            self.logger.debug("Thumbnail generation worker finished")

    def is_running(self) -> bool:
        """Check if generation is currently running."""
        return self.worker is not None and self.worker.isRunning()

    def stop(self) -> None:
        """Stop thumbnail generation."""
        if self.worker:
            self.worker.stop()
            self.logger.info("Thumbnail generation stopped")

