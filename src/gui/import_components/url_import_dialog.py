"""Dialog that downloads a model archive from a URL and imports it automatically."""

from __future__ import annotations

import http.cookiejar
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import (
    parse_qs,
    unquote,
    urljoin,
    urlencode,
    urlparse,
    urlsplit,
    urlunsplit,
)

from bs4 import BeautifulSoup
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
            helper = GoogleDriveHelper()
            if helper.can_handle(self.url):
                helper.download(self.url, self.destination, self.progress.emit)
            else:
                self._standard_download(self.url, self.destination)
            self.completed.emit(str(self.destination))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            self.failed.emit(str(exc))

    def _standard_download(self, url: str, destination: Path) -> None:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response:
            total = int(response.headers.get("Content-Length") or 0)
            downloaded = 0
            chunk_size = 1024 * 256

            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        percent = int((downloaded / total) * 100)
                        self.progress.emit(percent)


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
        self.status_label.setText("Downloading...")
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
                self,
                "Projects Folder Error",
                f"Unable to access Projects folder:\n\n{exc}",
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
        QMessageBox.information(
            self, "Import Complete", "The model was imported successfully."
        )
        self.accept()

    def _on_import_failed(self, error: str) -> None:
        self.logger.error("URL import failed: %s", error)
        QMessageBox.critical(self, "Import Failed", error)
        self.download_button.setEnabled(True)


class GoogleDriveHelper:
    """Utility to handle Google Drive share links that require confirmation tokens."""

    CONFIRM_PATTERN = re.compile(r"confirm=([0-9A-Za-z_]+)")

    def __init__(self) -> None:
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        # Defensive attributes to satisfy downstream callers
        self._source_url: Optional[str] = None
        self.logger = get_logger(__name__)
        self.import_result: Optional[ImportCoordinatorResult] = None

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if "googleusercontent" in host:
            return True
        if "google.com" in host and "drive" in host:
            return True
        if "facebook.com" in host:
            qs = parse_qs(parsed.query)
            if "u" in qs:
                return self.can_handle(unquote(qs["u"][0]))
        return False

    def download(
        self, url: str, destination: Path, progress_callback: Callable[[int], None]
    ) -> None:
        file_id = self._extract_file_id(url)
        if not file_id:
            raise ValueError(
                "Unable to determine Google Drive file ID from the provided link."
            )

        last_error: Optional[Exception] = None
        for candidate in self._candidate_urls(url, file_id):
            try:
                response = self._open(candidate)
                self._process_response(
                    file_id, response, destination, progress_callback
                )
                return
            except ValueError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise ValueError("Unable to download the Google Drive file.")

    def _process_response(
        self,
        file_id: str,
        response,
        destination: Path,
        progress_callback: Callable[[int], None],
    ) -> None:
        if self._is_binary_response(response):
            self._stream_response(response, destination, progress_callback)
            return

        page_content = response.read().decode("utf-8", errors="ignore")
        confirm_url = None
        try:
            confirm_url = self._extract_confirmation_url(
                page_content, response.geturl()
            )
        except ValueError as exc:
            raise ValueError(
                "Google Drive rejected the download request: " f"{exc}"
            ) from exc

        if not confirm_url:
            token = (
                self._extract_confirm_token(page_content)
                or self._extract_cookie_token()
            )
            if token:
                confirm_url = self._build_url(file_id, token)

        if not confirm_url:
            raise ValueError(
                "Google Drive requires confirmation for this file. "
                "Ensure the link is public or download it manually."
            )

        response = self._open(confirm_url)
        self._process_response(file_id, response, destination, progress_callback)

    def _candidate_urls(self, original_url: str, file_id: str):
        """Yield URLs to try, avoiding duplicates."""

        seen = set()
        for candidate in (original_url, self._build_url(file_id)):
            if candidate and candidate not in seen:
                seen.add(candidate)
                yield candidate

    def _extract_file_id(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "facebook.com" in host:
            qs = parse_qs(parsed.query)
            if "u" in qs:
                return self._extract_file_id(unquote(qs["u"][0]))

        qs = parse_qs(parsed.query)
        if "id" in qs:
            return qs["id"][0]

        match = re.search(r"/d/([^/]+)/", parsed.path)
        if match:
            return match.group(1)

        if "googleusercontent" in host and "id" in qs:
            return qs["id"][0]

        return None

    def _open(self, url: str):
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return self.opener.open(request)

    @staticmethod
    def _is_binary_response(response) -> bool:
        disposition = response.headers.get("Content-Disposition")
        content_type = (response.headers.get("Content-Type") or "").lower()
        return disposition is not None or not content_type.startswith("text/html")

    @classmethod
    def _extract_confirm_token(cls, page: str) -> Optional[str]:
        match = cls.CONFIRM_PATTERN.search(page)
        if match:
            return match.group(1)
        return None

    def _extract_cookie_token(self) -> Optional[str]:
        """Some downloads store the token in a download_warning cookie."""

        for cookie in self.cookie_jar:
            if cookie.name.startswith("download_warning"):
                return cookie.value
        return None

    def _extract_confirmation_url(
        self, page: str, response_url: Optional[str]
    ) -> Optional[str]:
        """Parse HTML confirmation pages to find the redirect download URL."""

        base = response_url or "https://docs.google.com"
        for line in page.splitlines():
            match = re.search(r'href="(\/uc\?export=download[^"]+)', line)
            if match:
                relative = match.group(1).replace("&amp;", "&")
                return urljoin(base, relative)

            soup = BeautifulSoup(line, "html.parser")
            form = soup.select_one("#download-form")
            if form is not None:
                action = (form.get("action") or "").replace("&amp;", "&")
                if not action:
                    continue
                action = urljoin(base, action)
                url_components = urlsplit(action)
                query_params = parse_qs(url_components.query)
                for param in form.find_all("input", attrs={"type": "hidden"}):
                    name = param.get("name")
                    if not name:
                        continue
                    query_params[name] = param.get("value")
                query = urlencode(query_params, doseq=True)
                return urlunsplit(url_components._replace(query=query))

            match = re.search('"downloadUrl":"([^"]+)', line)
            if match:
                url = match.group(1)
                url = url.replace("\\u003d", "=").replace("\\u0026", "&")
                return url

            match = re.search('<p class="uc-error-subcaption">(.*)</p>', line)
            if match:
                raise ValueError(match.group(1))

        return None

    def _stream_response(
        self, response, destination: Path, progress_callback: Callable[[int], None]
    ) -> None:

        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        chunk_size = 1024 * 256

        with destination.open("wb") as handle:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if total:
                    progress_callback(int((downloaded / total) * 100))

    @staticmethod
    def _build_url(file_id: str, token: Optional[str] = None) -> str:
        base = f"https://drive.google.com/uc?export=download&id={file_id}"
        if token:
            return f"{base}&confirm={token}"
        return base

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
                db_manager.update_model_keywords_tags(
                    model_id, add_tags=[TAG_DOWNLOADED]
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to tag downloaded model %s: %s", model_id, exc
                )

    def get_import_result(self) -> Optional[ImportCoordinatorResult]:
        """Expose the final import result to callers."""

        return self.import_result
