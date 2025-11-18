"""Dialog for handling extra/unknown file types during consolidation.

This dialog presents grouped extra files by extension and lets the user choose
how to handle them (move to Misc, leave in place), with options to apply the
choice to all files of a given type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
)

from src.core.logging_config import get_logger
from src.core.services.extra_files_policy import ExtraFilesPolicy, ExtraFileDecision


logger = get_logger(__name__)


@dataclass
class ExtraFileGroup:
    """Represents a group of extra files with the same extension."""

    extension: str
    files: List[str]


class ExtraFilesDialog(QDialog):
    """Windows-style dialog for deciding how to handle extra file types.

    The dialog exposes the user's choices for this session via
    :attr:`session_decisions` while also updating :class:`ExtraFilesPolicy`
    when "all of this type" options are used.
    """

    def __init__(
        self,
        groups: List[ExtraFileGroup],
        policy: Optional[ExtraFilesPolicy] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Extra Files Detected")
        self.setModal(True)

        self._groups = groups
        self._policy = policy or ExtraFilesPolicy()

        self._current_group: Optional[ExtraFileGroup] = None
        self.session_decisions: Dict[str, ExtraFileDecision] = {}

        self._setup_ui()
        self._populate_groups()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()

        description = QTextEdit()
        description.setReadOnly(True)
        description.setMaximumHeight(90)
        description.setText(
            "Some files were found that are not part of the normal model/document "
            "set. You can choose whether to move them into the project (Misc) or "
            "leave them in their current folders."
        )
        layout.addWidget(description)

        content_layout = QHBoxLayout()

        self.group_list = QListWidget()
        self.group_list.currentItemChanged.connect(self._on_group_changed)
        content_layout.addWidget(self.group_list, 1)

        self.details_label = QLabel("Select a file type to see details.")
        self.details_label.setWordWrap(True)
        content_layout.addWidget(self.details_label, 2)

        layout.addLayout(content_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.move_btn = QPushButton("Move")
        self.move_btn.clicked.connect(self._on_move_clicked)
        button_layout.addWidget(self.move_btn)

        self.move_all_btn = QPushButton("Move all of this type")
        self.move_all_btn.clicked.connect(self._on_move_all_clicked)
        button_layout.addWidget(self.move_all_btn)

        self.leave_btn = QPushButton("Leave")
        self.leave_btn.clicked.connect(self._on_leave_clicked)
        button_layout.addWidget(self.leave_btn)

        self.leave_all_btn = QPushButton("Leave all of this type")
        self.leave_all_btn.clicked.connect(self._on_leave_all_clicked)
        button_layout.addWidget(self.leave_all_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.resize(700, 400)

    def _populate_groups(self) -> None:
        """Populate the list of extensions, applying existing policies."""

        self.group_list.clear()

        for group in self._groups:
            item_text = f"{group.extension}  ({len(group.files)} files)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, group)
            self.group_list.addItem(item)

        if self.group_list.count() > 0:
            self.group_list.setCurrentRow(0)

    def _on_group_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        group = current.data(Qt.UserRole) if current is not None else None
        self._current_group = group

        if not group:
            self.details_label.setText("Select a file type to see details.")
            return

        examples = group.files[:5]
        details = [
            f"Extension: {group.extension}",
            f"Total files: {len(group.files)}",
            "Examples:",
            *[f"  • {path}" for path in examples],
        ]

        self.details_label.setText("\n".join(details))

    # === Button handlers ===

    def _apply_decision(self, decision: ExtraFileDecision, remember: bool) -> None:
        """Apply a decision to the current group and optionally persist it."""

        if not self._current_group:
            return

        ext = self._current_group.extension
        self.session_decisions[ext] = decision

        if remember:
            self._policy.set_policy(ext, decision)

        logger.info(
            "Extra files decision: %s -> %s (remember=%s)",
            ext,
            decision.value,
            remember,
        )

    def _on_move_clicked(self) -> None:
        self._apply_decision(ExtraFileDecision.MOVE_TO_MISC, remember=False)
        self.accept()

    def _on_move_all_clicked(self) -> None:
        self._apply_decision(ExtraFileDecision.MOVE_TO_MISC, remember=True)
        self.accept()

    def _on_leave_clicked(self) -> None:
        self._apply_decision(ExtraFileDecision.LEAVE_IN_PLACE, remember=False)
        self.accept()

    def _on_leave_all_clicked(self) -> None:
        self._apply_decision(ExtraFileDecision.LEAVE_IN_PLACE, remember=True)
        self.accept()

