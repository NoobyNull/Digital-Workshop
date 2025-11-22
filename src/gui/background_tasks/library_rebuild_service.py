"""Service that re-imports files already inside the managed Projects folder."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from src.core.logging_config import get_logger
from src.core.import_file_manager import ImportFileManager, FileManagementMode
from src.core.services.library_settings import LibrarySettings, LibraryMode
from src.gui.background_tasks.import_background_monitor import ImportBackgroundMonitor

logger = get_logger(__name__)


class LibraryRebuildService(QObject):
    """Trigger a headless import of files already located in the managed Projects folder."""

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.settings = LibrarySettings()
        self.worker = None
        self.monitor: Optional[ImportBackgroundMonitor] = None
        self.allowed_extensions = {
            ext.lower()
            for ext in ImportFileManager.ORGANIZED_SUBDIRS
            if ext not in {"other"}
        }

    def start(self) -> None:
        """Begin rebuilding the managed library."""

        if self.worker and self.worker.isRunning():
            QMessageBox.information(
                self.main_window,
                "Rebuild In Progress",
                "A managed library rebuild is already running.",
            )
            return

        if self.settings.get_mode() != LibraryMode.CONSOLIDATED:
            QMessageBox.warning(
                self.main_window,
                "Managed Library Required",
                "Rebuilding is only available when the Projects folder is managed by the app.",
            )
            return

        base_root = self.settings.get_base_root()
        if base_root is None or not base_root.exists():
            QMessageBox.warning(
                self.main_window,
                "Projects Folder Missing",
                "The configured Projects folder could not be found. Please verify it exists.",
            )
            return

        files = self._collect_files(base_root)
        if not files:
            QMessageBox.information(
                self.main_window,
                "Nothing To Rebuild",
                "No supported model files were found in the Projects folder.",
            )
            return

        confirm = QMessageBox.question(
            self.main_window,
            "Rebuild Managed Library",
            f"Re-import {len(files)} file(s) found in the Projects folder? "
            "Existing database entries will be replaced as needed.",
        )
        if confirm != QMessageBox.Yes:
            return

        from src.gui.import_components.import_workers import (
            ImportJobConfig,
            PipelineImportWorker,
        )

        config = ImportJobConfig(
            generate_thumbnails=True,
            run_analysis=True,
            concurrency_mode="concurrent",
        )
        worker = PipelineImportWorker(
            file_paths=files,
            mode=FileManagementMode.LEAVE_IN_PLACE,
            root_directory=None,
            config=config,
        )
        self.worker = worker
        self.monitor = ImportBackgroundMonitor(self.main_window, worker)

        worker.import_completed.connect(self._on_completed)
        worker.import_cancelled.connect(self._on_cancelled)
        worker.import_failed.connect(self._on_failed)
        worker.start()

    def _collect_files(self, root: Path) -> List[str]:
        """Return all supported files within the managed root."""

        files: List[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower().lstrip(".")
            if suffix in self.allowed_extensions:
                files.append(str(path))
        return files

    def _on_completed(self, result) -> None:
        self._cleanup_worker()
        processed = result.processed_files if result else 0
        failed = result.failed_files if result else 0
        QMessageBox.information(
            self.main_window,
            "Library Rebuild Complete",
            f"Processed {processed} file(s).\nFailed: {failed}",
        )

    def _on_cancelled(self, result, reason: str) -> None:
        self._cleanup_worker()
        QMessageBox.information(
            self.main_window,
            "Library Rebuild Cancelled",
            f"The rebuild was cancelled.\n{reason}",
        )

    def _on_failed(self, error: str) -> None:
        self._cleanup_worker()
        QMessageBox.critical(
            self.main_window,
            "Library Rebuild Failed",
            f"The rebuild failed:\n{error}",
        )

    def _cleanup_worker(self) -> None:
        """Reset worker references after completion."""

        self.monitor = None
        self.worker = None
