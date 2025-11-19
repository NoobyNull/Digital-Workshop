"""First-launch dialog for library mode and root selection.

The dialog appears only once, the first time the application is run
(or until the user completes/skip the setup). It lets the user choose
between leaving files in place or consolidating into a managed library
root, with a default root under ``C:/Users/<user>/3D Objects``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QLineEdit,
    QFileDialog,
    QWidget,
)

from src.core.logging_config import get_logger
from src.core.services.library_settings import LibraryMode, LibrarySettings

logger = get_logger(__name__)


class LibrarySetupDialog(QDialog):
    """Simple first-launch dialog for library configuration."""

    def __init__(
        self, settings: LibrarySettings, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings

        self.setWindowTitle("Library Setup")
        self.setModal(True)

        self._leave_radio = QRadioButton("Leave files in place (use existing folders)")
        self._consolidate_radio = QRadioButton("Consolidate into a managed library")
        self._leave_radio.setChecked(True)

        warning_label = QLabel(
            "Warning: Leaving files in place on cloud or remote storage "
            "(OneDrive, Google Drive, Dropbox, UNC over DNS) can cause "
            "instability. A local or hard UNC path is recommended."
        )
        warning_label.setWordWrap(True)

        root_label = QLabel("Library root (for consolidated mode):")
        self._root_edit = QLineEdit(self)
        self._browse_button = QPushButton("Browse…", self)

        default_root = self._settings.get_default_projects_root()
        self._root_edit.setText(str(default_root))

        root_row = QHBoxLayout()
        root_row.addWidget(self._root_edit, 1)
        root_row.addWidget(self._browse_button)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self._skip_button = QPushButton("Skip", self)
        self._continue_button = QPushButton("Continue", self)
        buttons_row.addWidget(self._skip_button)
        buttons_row.addWidget(self._continue_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("How should Digital Workshop manage imported files?"))
        layout.addWidget(self._leave_radio)
        layout.addWidget(self._consolidate_radio)
        layout.addWidget(warning_label)
        layout.addSpacing(8)
        layout.addWidget(root_label)
        layout.addLayout(root_row)
        layout.addSpacing(12)
        layout.addLayout(buttons_row)

        self._browse_button.clicked.connect(self._on_browse_clicked)
        self._skip_button.clicked.connect(self._on_skip_clicked)
        self._continue_button.clicked.connect(self._on_continue_clicked)

        self._update_root_controls()
        self._leave_radio.toggled.connect(self._update_root_controls)
        self._consolidate_radio.toggled.connect(self._update_root_controls)

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def _update_root_controls(self) -> None:
        consolidate = self._consolidate_radio.isChecked()
        self._root_edit.setEnabled(consolidate)
        self._browse_button.setEnabled(consolidate)

    def _on_browse_clicked(self) -> None:
        current = self._root_edit.text().strip() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select library root",
            current,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if directory:
            self._root_edit.setText(directory)

    def _on_skip_clicked(self) -> None:
        """Skip explicit configuration and accept safe defaults."""

        logger.info("Library setup skipped; defaulting to LEAVE_IN_PLACE")
        self._settings.set_mode(LibraryMode.LEAVE_IN_PLACE)
        self._settings.set_base_root(None)
        self._settings.set_setup_completed(True)
        self.accept()

    def _on_continue_clicked(self) -> None:
        if self._leave_radio.isChecked():
            mode = LibraryMode.LEAVE_IN_PLACE
            base_root: Optional[Path] = None
        else:
            mode = LibraryMode.CONSOLIDATED
            text = self._root_edit.text().strip()
            if not text:
                text = str(self._settings.get_default_projects_root())
                self._root_edit.setText(text)
            base_root = Path(text)
            try:
                base_root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                logger.error("Failed to create library root %s: %s", base_root, exc)

        self._settings.set_mode(mode)
        self._settings.set_base_root(base_root)
        self._settings.set_setup_completed(True)
        self.accept()


def run_first_launch_setup(parent: Optional[QWidget] = None) -> None:
    """Run the first-launch library setup dialog if needed."""

    settings = LibrarySettings()
    if settings.is_setup_completed():
        return

    dialog = LibrarySetupDialog(settings, parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.exec()
