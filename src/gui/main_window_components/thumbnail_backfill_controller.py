"""
Controller to manage thumbnail backfill from the main window.

Moves worker orchestration and UI messaging out of main_window.py to shrink
the monolith while keeping behavior identical.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger
from src.gui.workers.thumbnail_backfill_worker import ThumbnailBackfillWorker


class ThumbnailBackfillController(QObject):
    """Orchestrates thumbnail backfill lifecycle for the main window."""

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self.logger = get_logger(__name__)
        self.main_window = main_window
        self._worker: Optional[ThumbnailBackfillWorker] = None

    def start(self) -> None:
        """Start a thumbnail backfill run unless one is already running."""
        if self._worker and self._worker.isRunning():
            QMessageBox.information(
                self.main_window,
                "Thumbnails",
                "Thumbnail backfill is already running.",
            )
            return

        self._worker = ThumbnailBackfillWorker(self.logger)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._cleanup)
        self._worker.failed.connect(self._cleanup)
        self._worker.start()

        self._set_status("Starting thumbnail backfill...", enable_button=False)

    @Slot(int, int)
    def _on_progress(self, processed: int, total: int) -> None:
        """Update status as thumbnails are backfilled."""
        self._set_status(f"Backfilling thumbnails ({processed}/{total})")

    @Slot(int, int)
    def _on_finished(self, completed: int, total: int) -> None:
        """Report completion and refresh UI."""
        self._set_status("Thumbnail backfill complete")

        if total == 0:
            QMessageBox.information(
                self.main_window, "Thumbnails", "All models already have thumbnails."
            )
        else:
            QMessageBox.information(
                self.main_window,
                "Thumbnails",
                f"Backfilled thumbnails for {completed} of {total} model(s).",
            )

        if hasattr(self.main_window, "model_library_widget"):
            try:
                self.main_window.model_library_widget._refresh_model_display()
            except Exception:  # pragma: no cover - UI best effort
                self.logger.debug("Failed to refresh model library after backfill")

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        """Surface backfill failure without crashing the UI."""
        QMessageBox.critical(
            self.main_window, "Thumbnails", f"Backfill failed:\n{message}"
        )
        self.logger.error("Thumbnail backfill failed: %s", message)

    def _cleanup(self) -> None:
        """Release worker and re-enable status bar controls."""
        if self._worker:
            if self._worker.isRunning():
                self._worker.request_cancel()
                self._worker.wait(500)
            self._worker.deleteLater()
        self._worker = None
        self._set_status("", enable_button=True)

    def _set_status(self, message: str, enable_button: Optional[bool] = None) -> None:
        """Helper to update status bar and optional toolbar button."""
        try:
            if message:
                self.main_window.statusBar().showMessage(message, 2000)
        except Exception:
            pass

        if enable_button is not None:
            if hasattr(self.main_window, "status_bar_manager") and getattr(
                self.main_window, "status_bar_manager"
            ):
                try:
                    self.main_window.status_bar_manager.thumb_button.setEnabled(
                        enable_button
                    )
                except Exception:
                    pass
