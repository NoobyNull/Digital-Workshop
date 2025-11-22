"""Folder scan worker for non-blocking model folder imports.

Scans a directory tree for supported model extensions in a background thread,
emitting progress and results so the UI remains responsive.
"""

from pathlib import Path
from typing import Iterable, List, Sequence

from PySide6.QtCore import Signal

from src.core.logging_config import get_logger
from src.gui.workers.base_worker import BaseWorker


class FolderScanWorker(BaseWorker):
    """Worker thread for scanning a folder for model files without blocking the GUI.

    Signals:
        progress_updated: Emitted with (files_found, current_path) periodically.
        scan_completed: Emitted with list[str] of discovered file paths on success.
        error_occurred: Emitted with error message on failure.
        cancelled: Emitted when the scan is cancelled before completion.
    """

    progress_updated = Signal(int, str)
    scan_completed = Signal(list)
    error_occurred = Signal(str)
    cancelled = Signal()

    def __init__(self, root_folder: str, extensions: Sequence[str]) -> None:
        super().__init__()
        self.logger = get_logger(__name__)
        self.root_folder = root_folder
        # Normalize extensions to lowercase with leading dot
        self.extensions = {ext.lower() for ext in extensions}
        # Bridge base progress to legacy signal for existing UI wiring.
        self.progress.connect(
            lambda current, _, path: self.progress_updated.emit(current, path)
        )

    def cancel(self) -> None:
        """Request cancellation of the scan."""

        self.request_cancel()
        self.logger.info("Folder scan cancelled by user for: %s", self.root_folder)

    def run(self) -> None:  # type: ignore[override]
        """Execute folder scan in background thread."""

        try:
            root_path = Path(self.root_folder)
            if not root_path.is_dir():
                msg = f"Folder does not exist or is not a directory: {root_path}"
                self.logger.warning(msg)
                self.error_occurred.emit(msg)
                return

            files: List[str] = []
            seen: set[str] = set()
            emit_interval = 100
            last_emit_count = 0

            for path in root_path.rglob("*"):
                if self.is_cancel_requested():
                    self.logger.info(
                        "Folder scan cancelled mid-run after %d files: %s",
                        len(files),
                        root_path,
                    )
                    self.cancelled.emit()
                    return

                if not path.is_file():
                    continue

                if path.suffix.lower() not in self.extensions:
                    continue

                str_path = str(path)
                if str_path in seen:
                    continue

                files.append(str_path)
                seen.add(str_path)

                if len(files) - last_emit_count >= emit_interval:
                    last_emit_count = len(files)
                    self.emit_progress(len(files), emit_interval, str(path.parent))

            self.logger.info(
                "Folder scan completed for %s: %d files found", root_path, len(files)
            )
            self.scan_completed.emit(files)

        except Exception as exc:  # pragma: no cover - defensive logging
            msg = f"Error scanning folder {self.root_folder}: {exc}"
            self.logger.error("%s", msg, exc_info=True)
            self.error_occurred.emit(msg)
