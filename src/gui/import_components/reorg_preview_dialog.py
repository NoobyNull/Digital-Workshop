"""
Stub dialog for reorganized import path preview.

Provides a lightweight UI to:
- Choose a source folder
- Detect files
- Preview proposed destinations side-by-side
- Select copy/move/dry-run modes (non-functional stub)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QMessageBox,
)

from src.core.logging_config import get_logger


@dataclass
class PreviewRow:
    """Represents a single file preview."""

    source: Path
    destination: Path
    relpath: Path


class ReorgPreviewDialog(QDialog):
    """Stub UI to preview import paths based on tags/templates."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.setWindowTitle("Import Path Preview (Stub)")
        self.resize(900, 600)

        self._source_root: Optional[Path] = None
        self._common_root: Optional[Path] = None
        self._preview_rows: List[PreviewRow] = []

        self._build_ui()

    def _build_ui(self) -> None:
        """Create the stub widgets."""
        root_layout = QVBoxLayout(self)

        # Folder selection
        picker_row = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        self.select_btn = QPushButton("Choose Folder")
        self.select_btn.clicked.connect(self._choose_folder)
        picker_row.addWidget(QLabel("Source Folder:"))
        picker_row.addWidget(self.folder_label, 1)
        picker_row.addWidget(self.select_btn)
        root_layout.addLayout(picker_row)

        # Template and tags
        template_row = QHBoxLayout()
        self.template_edit = QLineEdit("{collection}/{basename}.{ext}")
        self.template_edit.setPlaceholderText("Destination template")
        self.template_edit.textChanged.connect(self._refresh_preview)
        template_row.addWidget(QLabel("Template:"))
        template_row.addWidget(self.template_edit, 1)
        self.tags_hint = QLabel(
            "Tags: {collection}, {topdir}, {relpath}, {relparent}, {source_parent}, {basename}, {ext}, {filename}"
        )
        self.tags_hint.setStyleSheet("color: #666;")
        template_row.addWidget(self.tags_hint)
        root_layout.addLayout(template_row)

        # Detect button
        detect_row = QHBoxLayout()
        self.detect_btn = QPushButton("Detect & Preview")
        self.detect_btn.clicked.connect(self._detect)
        detect_row.addStretch()
        detect_row.addWidget(self.detect_btn)
        root_layout.addLayout(detect_row)

        # Preview table
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Source", "Proposed Destination"])
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        root_layout.addWidget(self.tree, 1)

        # Action buttons
        actions = QHBoxLayout()
        self.copy_btn = QPushButton("Copy (stub)")
        self.move_btn = QPushButton("Move (stub)")
        self.dry_run_btn = QPushButton("Dry run")
        self.cancel_btn = QPushButton("Cancel")
        self.copy_btn.clicked.connect(self._stub_action)
        self.move_btn.clicked.connect(self._stub_action)
        self.dry_run_btn.clicked.connect(self._stub_action)
        self.cancel_btn.clicked.connect(self.reject)
        actions.addStretch()
        actions.addWidget(self.dry_run_btn)
        actions.addWidget(self.copy_btn)
        actions.addWidget(self.move_btn)
        actions.addWidget(self.cancel_btn)
        root_layout.addLayout(actions)

    def _choose_folder(self) -> None:
        """Open folder picker."""
        selected = QFileDialog.getExistingDirectory(
            self, "Select source folder", os.path.expanduser("~")
        )
        if selected:
            self._source_root = Path(selected)
            self.folder_label.setText(str(self._source_root))
            self._detect()

    def _detect(self) -> None:
        """Best-effort detection stub."""
        if not self._source_root:
            QMessageBox.information(self, "Select folder", "Choose a folder first.")
            return

        files: List[Path] = []
        for root, _dirs, filenames in os.walk(self._source_root):
            for name in filenames:
                path = Path(root) / name
                files.append(path)
            if len(files) >= 200:
                break

        if not files:
            QMessageBox.information(self, "No files", "No files found in this folder.")
            self._preview_rows = []
            self._refresh_table()
            return

        # Compute common root across all files (up to their parent directories)
        parent_paths = [str(f.parent) for f in files]
        common = os.path.commonpath(parent_paths) if parent_paths else None
        self._common_root = Path(common) if common else self._source_root

        self._preview_rows = [self._build_preview_row(f) for f in files]
        self._refresh_table()

    def _build_preview_row(self, src: Path) -> PreviewRow:
        """Create a preview row using the template."""
        root = self._common_root or self._source_root or src.parent
        rel = src.relative_to(root)
        parts = rel.parts
        collection = parts[0] if parts else ""
        relparent = rel.parent.as_posix() if rel.parent != Path(".") else ""
        topdir = parts[0] if parts else ""
        source_parent = src.parent.name
        template = self.template_edit.text().strip() or "{basename}.{ext}"
        dest_str = self._safe_format_template(
            template=template,
            collection=collection,
            topdir=topdir,
            relpath=rel.as_posix(),
            relparent=relparent,
            source_parent=source_parent,
            basename=src.stem,
            ext=src.suffix.lstrip("."),
            filename=src.name,
        )
        dest = Path(dest_str)
        return PreviewRow(source=src, destination=dest, relpath=rel)

    def _safe_format_template(self, template: str, **tags) -> str:
        """Format the template; if invalid braces, return fallback literal."""
        try:
            return template.format(**tags)
        except Exception as exc:
            self.logger.warning("Invalid template '%s': %s", template, exc)
            # Fallback to simple basename.ext to avoid crashing the preview
            return f"{tags.get('basename', 'file')}.{tags.get('ext', '')}"

    def _refresh_preview(self) -> None:
        """Recompute destinations when template changes."""
        if not self._preview_rows:
            return
        self._preview_rows = [
            self._build_preview_row(r.source) for r in self._preview_rows
        ]
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Render the current preview rows."""
        self.tree.clear()
        node_lookup = {}
        for row in self._preview_rows:
            # Build directory hierarchy from common root
            rel_parts = list(row.relpath.parts)
            parent_item = None
            built_path: List[str] = []
            for part in rel_parts[:-1]:
                built_path.append(part)
                key = "/".join(built_path)
                if key not in node_lookup:
                    item = QTreeWidgetItem([part, ""])
                    node_lookup[key] = item
                    if parent_item:
                        parent_item.addChild(item)
                    else:
                        self.tree.addTopLevelItem(item)
                parent_item = node_lookup[key]
            # Leaf node for file
            leaf = QTreeWidgetItem([row.source.name, str(row.destination)])
            if parent_item:
                parent_item.addChild(leaf)
            else:
                self.tree.addTopLevelItem(leaf)
        self.tree.expandAll()

    def _stub_action(self) -> None:
        """Placeholder for copy/move/dry-run actions."""
        QMessageBox.information(
            self,
            "Stub",
            "This is a stub. Actions will be wired in a future step.",
        )
