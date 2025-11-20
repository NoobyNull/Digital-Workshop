"""Interactive first-start walkthrough dialog.

This lightweight wizard appears only on the very first launch (unless
the user opts out). It guides the user through the key areas of the
product: project storage, project manager, model previewer, and G-code
previewer. The goal is to orient new users without forcing them to read
external docs.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedLayout,
    QWidget,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
)

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FirstRunWalkthrough(QDialog):
    """Three-step onboarding dialog with opt-out."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to Digital Workshop")
        self.setModal(True)
        self.setMinimumSize(540, 420)

        self._settings = QSettings("DigitalWorkshop", "DigitalWorkshop")
        self._stack = QStackedLayout()
        self._back_btn = QPushButton("Back")
        self._next_btn = QPushButton("Next")
        self._skip_btn = QPushButton("Skip")
        self._done_checkbox = QCheckBox("Don't show this guide again")
        self._done_checkbox.setChecked(True)

        container = QVBoxLayout(self)
        container.addLayout(self._stack)

        controls = QHBoxLayout()
        controls.addWidget(self._done_checkbox)
        controls.addStretch()
        controls.addWidget(self._skip_btn)
        controls.addWidget(self._back_btn)
        controls.addWidget(self._next_btn)
        container.addLayout(controls)

        self._build_pages()
        self._wire_signals()
        self._update_nav()

    def _build_pages(self) -> None:
        self._stack.addWidget(self._page_welcome())
        self._stack.addWidget(self._page_projects())
        self._stack.addWidget(self._page_tooling())

    def _page_welcome(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        title = QLabel("Let's get you oriented.")
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        body = QLabel(
            "We'll quickly show you where to create projects, view models, and preview G-code. "
            "You can revisit this from Help > Walkthrough anytime."
        )
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addStretch()
        return w

    def _page_projects(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        title = QLabel("Project Manager")
        font = title.font()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        desc = QLabel(
            "Create or import projects, organize them into groups, and add design/manufacturing files. "
            "Drag projects between groups to reorganize."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        checklist = QListWidget()
        for text in [
            "Create a project (Project Manager dock → New Project)",
            "Import existing files (Project Manager dock → Add Files)",
            "Organize with groups (right-click → Add Subgroup)",
        ]:
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemIsEnabled)
            checklist.addItem(item)
        layout.addWidget(checklist)
        layout.addStretch()
        return w

    def _page_tooling(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        title = QLabel("Model & G-code preview")
        font = title.font()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        desc = QLabel(
            "Double-click files in the Project Manager to open them in the right viewer:\n"
            " • Model Previewer: STL/OBJ/STEP with transform and measurements.\n"
            " • G-code Previewer: Timeline, layer filters, and 3D toolpath view."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        tips = QListWidget()
        for text in [
            "Use the camera toolbar to fit/rotate/pan the 3D view.",
            "Toggle layer filters (Not Cut / Cut / Rapids / Tool Change) to declutter toolpaths.",
            "Open the Metadata and Project Details tabs to annotate your jobs.",
        ]:
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemIsEnabled)
            tips.addItem(item)
        layout.addWidget(tips)
        layout.addStretch()
        return w

    def _wire_signals(self) -> None:
        self._back_btn.clicked.connect(self._on_back)
        self._next_btn.clicked.connect(self._on_next)
        self._skip_btn.clicked.connect(self._on_skip)

    def _on_back(self) -> None:
        idx = max(0, self._stack.currentIndex() - 1)
        self._stack.setCurrentIndex(idx)
        self._update_nav()

    def _on_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx >= self._stack.count() - 1:
            self._finish()
            return
        self._stack.setCurrentIndex(idx + 1)
        self._update_nav()

    def _on_skip(self) -> None:
        self._finish()

    def _finish(self) -> None:
        if self._done_checkbox.isChecked():
            self._settings.setValue("walkthrough/first_run_completed", True)
        self.accept()

    def _update_nav(self) -> None:
        idx = self._stack.currentIndex()
        count = self._stack.count()
        self._back_btn.setEnabled(idx > 0)
        if idx == count - 1:
            self._next_btn.setText("Done")
        else:
            self._next_btn.setText("Next")


def run_first_run_walkthrough(parent: Optional[QWidget] = None) -> None:
    """Show the first-run walkthrough if it hasn't been completed."""
    settings = QSettings("DigitalWorkshop", "DigitalWorkshop")
    if settings.value("walkthrough/first_run_completed", False, type=bool):
        return

    try:
        dlg = FirstRunWalkthrough(parent)
        dlg.exec()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("First-run walkthrough could not be shown: %s", exc)
