"""Status-bar monitor for background imports."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QTimer

from src.core.logging_config import get_logger


class ImportBackgroundMonitor(QObject):
    """Relay import worker progress to the main window status bar."""

    def __init__(self, main_window, worker) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.worker = worker
        self.logger = get_logger(__name__)

        self._current = 0
        self._total = 0
        self._percent = 0
        self._stage: str = "Preparing"
        self._last_message: str = ""

        worker.stage_changed.connect(self._on_stage_changed)
        worker.file_progress.connect(self._on_file_progress)
        worker.overall_progress.connect(self._on_overall_progress)
        worker.import_completed.connect(self._on_import_completed)
        worker.import_cancelled.connect(self._on_import_cancelled)
        worker.import_failed.connect(self._on_import_failed)

        self._show_status("Import running in background...")

    # ------------------------------------------------------------------ helpers
    def _status_bar(self):
        if hasattr(self.main_window, "statusBar"):
            return self.main_window.statusBar()
        return None

    def _show_status(self, text: str, timeout: int = 0) -> None:
        """Update both the status label and status bar."""

        if hasattr(self.main_window, "status_label"):
            self.main_window.status_label.setText(text)

        bar = self._status_bar()
        if bar:
            bar.showMessage(text, timeout)

    def _update_status(self) -> None:
        """Render the latest background import status."""

        total = self._total or "?"
        current = self._current if self._total else "?"
        stage = self._stage
        percent = self._percent

        detail = self._last_message or stage
        text = f"Importing models ({detail}) - {current}/{total} ({percent}%)"
        self._show_status(text)

    # ------------------------------------------------------------------ slots
    def _on_stage_changed(self, stage: str, message: str) -> None:
        self._stage = stage.replace("_", " ").title()
        self._last_message = message
        self._update_status()

    def _on_file_progress(self, filename: str, percent: int, message: str) -> None:
        self._last_message = f"{filename}: {message}"
        self._update_status()

    def _on_overall_progress(self, current: int, total: int, percent: int) -> None:
        self._current = current
        self._total = total
        self._percent = percent
        self._update_status()

    def _on_import_completed(self, result) -> None:
        processed = result.processed_files if result else 0
        failed = result.failed_files if result else 0
        message = f"Import complete: {processed} file(s) – {failed} failed."
        self._show_status(message, 5000)
        QTimer.singleShot(5000, lambda: self._show_status("Ready"))
        self._cleanup()

    def _on_import_cancelled(self, result, reason: str) -> None:
        processed = result.processed_files if result else 0
        message = f"Import cancelled after {processed} file(s): {reason}"
        self._show_status(message, 5000)
        QTimer.singleShot(5000, lambda: self._show_status("Ready"))
        self._cleanup()

    def _on_import_failed(self, error: str) -> None:
        self._show_status(f"Import failed: {error}", 8000)
        self.logger.error("Background import failed: %s", error)
        self._cleanup()

    def _cleanup(self) -> None:
        """Disconnect worker signals once finished."""

        try:
            self.worker.stage_changed.disconnect(self._on_stage_changed)
        except TypeError:
            pass
        try:
            self.worker.file_progress.disconnect(self._on_file_progress)
        except TypeError:
            pass
        try:
            self.worker.overall_progress.disconnect(self._on_overall_progress)
        except TypeError:
            pass
        try:
            self.worker.import_completed.disconnect(self._on_import_completed)
        except TypeError:
            pass
        try:
            self.worker.import_cancelled.disconnect(self._on_import_cancelled)
        except TypeError:
            pass
        try:
            self.worker.import_failed.disconnect(self._on_import_failed)
        except TypeError:
            pass

        self.worker = None
        self.deleteLater()
