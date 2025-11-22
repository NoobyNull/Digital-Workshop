"""
Shared worker base for background tasks that need progress, cancellation, and error reporting.

Subclasses should override ``run`` and use ``emit_progress`` plus ``is_cancel_requested``
to keep UI updates consistent.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    """Lightweight base around QThread with common signals and cancellation."""

    progress = Signal(int, int, str)  # current, total, message
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._cancel_requested = False

    def request_cancel(self) -> None:
        """Signal that work should stop."""
        if not self._cancel_requested:
            self._cancel_requested = True
            self.cancelled.emit()

    def is_cancel_requested(self) -> bool:
        """Return True if cancellation has been requested."""
        return self._cancel_requested

    def emit_progress(self, current: int, total: int, message: str = "") -> None:
        """Helper to emit progress without repeating the tuple packing."""
        self.progress.emit(current, total, message or "")
