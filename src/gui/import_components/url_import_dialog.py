"""Dialog that downloads a model archive from a URL and imports it automatically."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QMessageBox,
)

from src.core.logging_config import get_logger
from src.core.import_coordinator import ImportCoordinator, ImportCoordinatorResult
from src.core.import_file_manager import FileManagementMode
from src.core.services.library_settings import LibrarySettings
from src.core.database_manager import get_database_manager
from src.core.model_tags import TAG_DOWNLOADED


class UrlDownloadWorker(QThread):
    """Background worker that streams a URL to disk."""

    progress = Signal(int)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, destination: Path) -> None:
        super().__init__()
        self.url = url
        self.destination = destination

    def run(self) -> None:
        try:
            self.destination.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(self.url) as response:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                chunk_size = 1024 * 256

                with self.destination.open("wb") as handle:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = int((downloaded / total) * 100)
                            self.progress.emit(percent)

            self.completed.emit(str(self.destination))
        except (urllib.error.URLError, OSError) as exc:
            self.failed.emit(str(exc))


class UrlImportDialog(QDialog):
    """Download a remote archive and import it into the managed Projects folder."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import From URL")
        self.setModal(True)

        self.logger = get_logger(__name__)
        self.settings = LibrarySettings()
        self.download_worker: Optional[UrlDownloadWorker] = None
        self.import_coordinator: Optional[ImportCoordinator] = None
        self.import_result: Optional[ImportCoordinatorResult] = None
        self._download_path: Optional[Path] = None
        self._source_url: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(
            QLabel(
                "Paste a direct download link (ZIP or STL/OBJ file). "
                "The file will be downloaded, extracted if needed, and added to your library."
            )
        )

        url_row = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com/model.zip")
        url_row.addWidget(url_label)
        url_row.addWidget(self.url_edit, 1)
        layout.addLayout(url_row)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.download_button = QPushButton("Download && Import")
        self.cancel_button = QPushButton("Cancel")
        button_row.addWidget(self.download_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

        self.download_button.clicked.connect(self._start_download)
        self.cancel_button.clicked.connect(self.reject)

    def _start_download(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL Required", "Please enter a download URL.")
            return

        destination = self._derive_destination(url)
        self._source_url = url

        self.download_worker = UrlDownloadWorker(url, destination)
        self.download_worker.progress.connect(self.progress_bar.setValue)
        self.download_worker.completed.connect(self._on_download_completed)
        self.download_worker.failed.connect(self._on_download_failed)
        self.download_button.setEnabled(False)
        self.status_label.setText("Downloading…")
        self.progress_bar.setValue(0)
        self.download_worker.start()

    def _derive_destination(self, url: str) -> Path:
        downloads_dir = self.settings.get_downloads_cache()
        parsed = urlparse(url)
        filename = Path(parsed.path).name or "downloaded_model"
        if "." not in filename:
            filename = f"{filename}.zip"
        sanitized = "".join(ch for ch in filename if ch not in r"<>:\"/\\|?*")
        return downloads_dir / sanitized

    def _on_download_completed(self, path_str: str) -> None:
        self._download_path = Path(path_str)
        self.status_label.setText("Download complete. Importing…")
        self.progress_bar.setValue(0)
        self._begin_import()

    def _on_download_failed(self, error: str) -> None:
        self.logger.error("Download failed: %s", error)
        QMessageBox.critical(self, "Download Failed", error)
        self.download_button.setEnabled(True)
        self.status_label.setText("Download failed.")

    def _begin_import(self) -> None:
        if not self._download_path:
            QMessageBox.critical(self, "Import Error", "No downloaded file to import.")
            self.download_button.setEnabled(True)
            return

        try:
            projects_root = str(self.settings.ensure_projects_root())
        except OSError as exc:
            QMessageBox.critical(
                self, "Projects Folder Error", f"Unable to access Projects folder:\n\n{exc}"
            )
            self.download_button.setEnabled(True)
            return

        self.import_coordinator = ImportCoordinator(self)
        self.import_coordinator.import_completed.connect(self._on_import_completed)
        self.import_coordinator.import_failed.connect(self._on_import_failed)

        started = self.import_coordinator.start_import(
            file_paths=[str(self._download_path)],
            mode=FileManagementMode.KEEP_ORGANIZED,
            root_directory=projects_root,
        )

        if not started:
            QMessageBox.critical(
                self,
                "Import Error",
                "Unable to start the import process. Please try again.",
            )
            self.download_button.setEnabled(True)

    def _on_import_completed(self, result: ImportCoordinatorResult) -> None:
        self.import_result = result
        self.status_label.setText("Import completed.")
        self._tag_downloaded_models(result)
        QMessageBox.information(self, "Import Complete", "The model was imported successfully.")
        self.accept()

    def _on_import_failed(self, error: str) -> None:
        self.logger.error("URL import failed: %s", error)
        QMessageBox.critical(self, "Import Failed", error)
        self.download_button.setEnabled(True)
        self.status_label.setText("Import failed.")

    def _tag_downloaded_models(self, result: ImportCoordinatorResult) -> None:
        if not result.import_result or not self._source_url:
            return

        db_manager = get_database_manager()
        for file_info in result.import_result.session.files:
            if file_info.import_status != "completed":
                continue
            model_path = file_info.managed_path or file_info.original_path
            record = db_manager.get_model_by_path(model_path)
            if not record:
                continue

            model_id = record.get("id")
            if model_id is None:
                continue

            try:
                db_manager.update_model_metadata(model_id, source=self._source_url)
                db_manager.update_model_keywords_tags(model_id, add_tags=[TAG_DOWNLOADED])
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to tag downloaded model %s: %s", model_id, exc)

    def get_import_result(self) -> Optional[ImportCoordinatorResult]:
        """Expose the final import result to callers."""

        return self.import_result
