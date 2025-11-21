"""Background watcher that auto-imports files dropped into the Projects inbox."""

from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional, Set

from PySide6.QtCore import QObject, QTimer

from src.core.logging_config import get_logger
from src.core.import_coordinator import ImportCoordinator, ImportCoordinatorResult
from src.core.import_file_manager import FileManagementMode
from src.core.services.library_settings import LibraryMode, LibrarySettings


class ImportWatchService(QObject):
    """Monitor the managed Projects inbox and automatically import payloads."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.settings = LibrarySettings()
        self.watch_path: Optional[Path] = None
        self._queue: Deque[Path] = deque()
        self._queued_entries: Set[str] = set()
        self._current_entry: Optional[Path] = None
        self._current_payload: List[str] = []
        self._import_running = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(5000)  # 5 seconds
        self._poll_timer.timeout.connect(self._scan_for_new_entries)

        self._coordinator = ImportCoordinator(self)
        self._coordinator.import_completed.connect(self._on_import_completed)
        self._coordinator.import_failed.connect(self._on_import_failed)

    def start(self) -> None:
        """Begin watching the inbox directory."""

        if self.settings.get_mode() != LibraryMode.CONSOLIDATED:
            self.logger.info("Import watch service disabled outside Projects mode.")
            return

        try:
            self.watch_path = self.settings.get_watch_folder()
        except OSError as exc:
            self.logger.error("Unable to initialize watch folder: %s", exc)
            return

        self.logger.info("Watching %s for new imports", self.watch_path)
        self._poll_timer.start()
        self._scan_for_new_entries()

    def stop(self) -> None:
        """Stop watching the inbox."""

        self._poll_timer.stop()
        self._queue.clear()
        self._queued_entries.clear()

    def _scan_for_new_entries(self) -> None:
        """Detect new files dropped into the watch folder."""

        if self.watch_path is None or not self.watch_path.exists():
            return

        for entry in self.watch_path.iterdir():
            if entry.name.startswith("_"):
                continue

            key = str(entry.resolve())
            if key in self._queued_entries:
                continue
            try:
                current_match = self._current_entry and entry.samefile(
                    self._current_entry
                )
            except FileNotFoundError:
                current_match = False

            if current_match:
                continue

            self._queue.append(entry)
            self._queued_entries.add(key)

        self._process_queue()

    def _process_queue(self) -> None:
        """Start importing the next queued entry if idle."""

        if self._import_running or not self._queue:
            return

        entry = self._queue.popleft()
        key = str(entry.resolve())
        self._queued_entries.discard(key)

        payload = self._collect_payload(entry)
        if not payload:
            self._cleanup_entry(entry, success=True)
            return

        try:
            projects_root = str(self.settings.ensure_projects_root())
        except OSError as exc:
            self.logger.error(
                "Cannot determine Projects folder for watch import: %s", exc
            )
            return

        started = self._coordinator.start_import(
            file_paths=payload,
            mode=FileManagementMode.KEEP_ORGANIZED,
            root_directory=projects_root,
        )

        if not started:
            self.logger.warning("Failed to start watch import for %s", entry)
            self._queue.appendleft(entry)
            self._queued_entries.add(key)
            return

        self._import_running = True
        self._current_entry = entry
        self._current_payload = payload

    def _collect_payload(self, entry: Path) -> List[str]:
        """Collect files contained in the queued entry."""

        if entry.is_dir():
            return [str(path) for path in entry.rglob("*") if path.is_file()]
        if entry.is_file():
            return [str(entry)]
        return []

    def _on_import_completed(self, result: ImportCoordinatorResult) -> None:
        """Handle successful import and clean up the source."""

        if self._current_entry:
            self.logger.info(
                "Auto-imported %s item(s) from %s",
                result.import_result.processed_files if result.import_result else 0,
                self._current_entry,
            )
        self._finalize_current_entry(success=True)

    def _on_import_failed(self, error: str) -> None:
        """Handle failed auto import."""

        self.logger.error("Auto import failed: %s", error)
        self._finalize_current_entry(success=False)

    def _finalize_current_entry(self, success: bool) -> None:
        """Cleanup state after an import completes."""

        if self._current_entry:
            self._cleanup_entry(self._current_entry, success)

        self._current_entry = None
        self._current_payload = []
        self._import_running = False
        QTimer.singleShot(1000, self._process_queue)

    def _cleanup_entry(self, entry: Path, success: bool) -> None:
        """Remove or quarantine processed files."""

        try:
            if success:
                if entry.is_dir():
                    shutil.rmtree(entry, ignore_errors=True)
                elif entry.exists():
                    entry.unlink()
            else:
                failed_dir = (self.watch_path or entry.parent) / "_failed"
                failed_dir.mkdir(parents=True, exist_ok=True)
                target = failed_dir / entry.name
                if target.exists():
                    target = failed_dir / f"{entry.stem}_failed{entry.suffix}"
                entry.replace(target)
        except (OSError, IOError) as exc:
            self.logger.warning("Failed to tidy watch entry %s: %s", entry, exc)
