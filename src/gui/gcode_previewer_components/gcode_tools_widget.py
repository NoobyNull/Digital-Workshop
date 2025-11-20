"""G-code tools panel widget with timeline, statistics, editor, and snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QComboBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QAbstractItemView,
    QColorDialog,
)

from src.core.logging_config import get_logger
from .gcode_editor import GcodeEditorWidget
from .gcode_interactive_loader import InteractiveGcodeLoader
from .gcode_renderer import GcodeRenderer
from .gcode_timeline import GcodeTimeline


class ToolSnapshotsWidget(QWidget):
    """Structured table widget for viewing and exchanging tool snapshots."""

    add_from_editor_requested = Signal()
    snapshots_imported = Signal(list)
    delete_requested = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._current_rows: List[Dict[str, Any]] = []
        self._row_id_map: Dict[int, Optional[int]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.status_label = QLabel("No snapshots captured yet.")
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Tool #", "Diameter", "Material", "Feed", "Plunge", "Notes"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        layout.addWidget(self.table)

        button_row = QHBoxLayout()
        self.add_from_editor_button = QPushButton("Add from Editor")
        self.delete_button = QPushButton("Delete Selected")
        self.import_button = QPushButton("Import CSV")
        self.export_button = QPushButton("Export CSV")
        button_row.addWidget(self.add_from_editor_button)
        button_row.addWidget(self.delete_button)
        button_row.addStretch()
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.export_button)
        layout.addLayout(button_row)

        self.add_from_editor_button.clicked.connect(self.add_from_editor_requested.emit)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.import_button.clicked.connect(self._import_csv)
        self.export_button.clicked.connect(self._export_csv)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_snapshots(self, rows: List[Dict[str, Any]]) -> None:
        """Replace the displayed rows with canonical snapshot data."""
        self._current_rows = list(rows)
        self.table.setRowCount(len(rows))
        self._row_id_map.clear()

        for row_index, snapshot in enumerate(rows):
            tool_number = snapshot.get("tool_number") or snapshot.get("tool")
            diameter = snapshot.get("diameter")
            material = snapshot.get("material") or snapshot.get("provider") or ""
            feed_rate = snapshot.get("feed_rate")
            plunge_rate = snapshot.get("plunge_rate")
            notes = snapshot.get("notes") or ""

            def _make_item(text: str) -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                return item

            tool_item = _make_item(self._format_value(tool_number))
            tool_item.setData(Qt.UserRole, snapshot.get("id"))
            self.table.setItem(row_index, 0, tool_item)
            self.table.setItem(row_index, 1, _make_item(self._format_numeric(diameter)))
            self.table.setItem(row_index, 2, _make_item(self._format_value(material)))
            self.table.setItem(row_index, 3, _make_item(self._format_numeric(feed_rate)))
            self.table.setItem(row_index, 4, _make_item(self._format_numeric(plunge_rate)))
            self.table.setItem(row_index, 5, _make_item(notes.strip()))

            self._row_id_map[row_index] = snapshot.get("id")

        if rows:
            self.status_label.setText(f"{len(rows)} snapshot(s) captured.")
        else:
            self.status_label.setText("No snapshots captured yet.")

    def set_version_available(self, available: bool) -> None:
        """Enable or disable editing controls depending on context."""
        for button in (
            self.add_from_editor_button,
            self.delete_button,
            self.import_button,
            self.export_button,
        ):
            button.setEnabled(available)

        if not available:
            self.status_label.setText("Select a project G-code to capture tool snapshots.")
            self.table.setRowCount(0)
            self._current_rows.clear()
            self._row_id_map.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _format_value(self, value: Optional[Any]) -> str:
        if value is None:
            return "-"
        text = str(value).strip()
        return text or "-"

    def _format_numeric(self, value: Optional[Any]) -> str:
        try:
            if value is None:
                return "-"
            if isinstance(value, str) and not value.strip():
                return "-"
            return f"{float(value):.3f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            return self._format_value(value)

    def _selected_snapshot_ids(self) -> List[int]:
        ids: List[int] = []
        for row in set(index.row() for index in self.table.selectedIndexes()):
            snapshot_id = self._row_id_map.get(row)
            if snapshot_id is not None:
                ids.append(int(snapshot_id))
        return ids

    def _on_delete_clicked(self) -> None:
        ids = self._selected_snapshot_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Select at least one snapshot to delete.")
            return
        self.delete_requested.emit(ids)

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Tool Snapshots", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
            if not lines:
                QMessageBox.warning(self, "Empty File", "The selected CSV has no data.")
                return
            headers = [h.strip().lower() for h in lines[0].split(",")]
            rows: List[Dict[str, Any]] = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                values = [v.strip() for v in line.split(",")]
                row_dict = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
                rows.append(
                    {
                        "tool_number": row_dict.get("tool #") or row_dict.get("tool"),
                        "diameter": row_dict.get("diameter"),
                        "material": row_dict.get("material"),
                        "feed_rate": row_dict.get("feed") or row_dict.get("feed_rate"),
                        "plunge_rate": row_dict.get("plunge"),
                        "notes": row_dict.get("notes"),
                    }
                )
            if not rows:
                QMessageBox.information(self, "No Rows", "No snapshot rows were found in the CSV.")
                return
            self.snapshots_imported.emit(rows)
            QMessageBox.information(
                self,
                "Import Queued",
                f"Parsed {len(rows)} snapshot row(s). They will appear once saved to the project.",
            )
        except Exception as exc:  # pragma: no cover - UI feedback
            QMessageBox.warning(self, "Import Failed", f"Could not import CSV:\n{exc}")

    def _export_csv(self) -> None:
        if not self._current_rows:
            QMessageBox.information(self, "No Data", "Add a snapshot before exporting.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tool Snapshots", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            lines: List[str] = ["Tool #,Diameter,Material,Feed,Plunge,Notes"]
            for snapshot in self._current_rows:
                values = [
                    self._format_value(snapshot.get("tool_number")),
                    self._format_numeric(snapshot.get("diameter")),
                    self._format_value(snapshot.get("material")),
                    self._format_numeric(snapshot.get("feed_rate")),
                    self._format_numeric(snapshot.get("plunge_rate")),
                    (snapshot.get("notes") or "").replace(",", " "),
                ]
                lines.append(",".join(values))
            Path(path).write_text("\n".join(lines), encoding="utf-8")
            self.logger.info("Exported %s tool snapshot(s) to %s", len(self._current_rows), path)
            QMessageBox.information(self, "Export Complete", "Snapshots exported successfully.")
        except Exception as exc:  # pragma: no cover - UI feedback
            QMessageBox.warning(self, "Export Failed", f"Could not export CSV:\n{exc}")


class GcodeToolsWidget(QWidget):
    """Composite tools widget used on the right-hand side of the previewer."""

    reload_file_requested = Signal()
    open_folder_requested = Signal(str)
    file_saved = Signal(str)
    material_changed = Signal(str)
    cut_color_changed = Signal(tuple)
    ahead_color_changed = Signal(tuple)

    def __init__(self, renderer: Optional[GcodeRenderer], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.renderer = renderer

        self.timeline: Optional[GcodeTimeline] = None
        self.interactive_loader: Optional[InteractiveGcodeLoader] = None
        self.editor: Optional[GcodeEditorWidget] = None
        self.snapshots_panel: Optional[ToolSnapshotsWidget] = None
        self.project_base_directory: Optional[Path] = None

        self.stats_label: Optional[QLabel] = None
        self.tool_label: Optional[QLabel] = None
        self.moves_table: Optional[QTableWidget] = None
        self.material_combo: Optional[QComboBox] = None

        self.viz_mode_combo: Optional[QComboBox] = None
        self.camera_controls_checkbox: Optional[QCheckBox] = None
        self.layer_combo: Optional[QComboBox] = None
        self.show_all_layers_btn: Optional[QPushButton] = None
        self.layer_filters: Dict[str, QCheckBox] = {}
        self.cut_color_btn: Optional[QPushButton] = None
        self.ahead_color_btn: Optional[QPushButton] = None

        self.progress_bar: Optional[QProgressBar] = None
        self.file_name_label: Optional[QLabel] = None
        self.project_name_label: Optional[QLabel] = None
        self.runtime_label: Optional[QLabel] = None
        self.distance_label: Optional[QLabel] = None
        self.feed_override_label: Optional[QLabel] = None
        self.open_folder_btn: Optional[QPushButton] = None
        self.reload_button: Optional[QPushButton] = None
        self._current_file_path: Optional[str] = None

        self._init_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_timeline_tab(), "Timeline & Loader")
        tabs.addTab(self._build_statistics_tab(), "Statistics")
        tabs.addTab(self._build_editor_tab(), "Editor")
        tabs.addTab(self._build_snapshots_tab(), "Tool Snapshots")

        layout.addWidget(tabs)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Wire material combo change
        if self.material_combo:
            self.material_combo.currentTextChanged.connect(self.material_changed.emit)

    def _build_timeline_tab(self) -> QWidget:
        widget = QWidget()
        tab_layout = QVBoxLayout(widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(8)

        self.timeline = GcodeTimeline()
        tab_layout.addWidget(self.timeline)

        if self.renderer is not None:
            self.interactive_loader = InteractiveGcodeLoader(self.renderer)
            tab_layout.addWidget(self.interactive_loader)
        else:
            tab_layout.addWidget(QLabel("Interactive loader unavailable"))

        self._init_loader_summary(tab_layout)
        self._init_visualization_controls(tab_layout)
        return widget

    def _build_statistics_tab(self) -> QWidget:
        widget = QWidget()
        stats_layout = QVBoxLayout(widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)

        tool_group = QGroupBox("Active Tool")
        tool_layout = QVBoxLayout(tool_group)
        self.tool_label = QLabel("No tool selected")
        self.tool_label.setWordWrap(True)
        tool_layout.addWidget(self.tool_label)
        self.select_tool_button = QPushButton("Select Tool")
        tool_layout.addWidget(self.select_tool_button)

        # Material selector for current part/toolpath
        material_row = QHBoxLayout()
        material_row.addWidget(QLabel("Material:"))
        self.material_combo = QComboBox()
        self.material_combo.setEditable(True)
        material_row.addWidget(self.material_combo, 1)
        tool_layout.addLayout(material_row)
        stats_layout.addWidget(tool_group)

        stats_group = QGroupBox("Toolpath Statistics")
        stats_group_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Load a G-code file to see statistics")
        self.stats_label.setWordWrap(True)
        stats_group_layout.addWidget(self.stats_label)
        stats_layout.addWidget(stats_group)

        moves_group = QGroupBox("G-code Moves")
        moves_layout = QVBoxLayout(moves_group)
        self.moves_table = QTableWidget()
        self.moves_table.setColumnCount(7)
        self.moves_table.setHorizontalHeaderLabels(
            ["Line", "Type", "X", "Y", "Z", "Feed", "Speed"]
        )
        self.moves_table.setMaximumHeight(200)
        moves_layout.addWidget(self.moves_table)
        stats_layout.addWidget(moves_group)
        stats_layout.addStretch()
        return widget

    def _build_editor_tab(self) -> QWidget:
        self.editor = GcodeEditorWidget()
        self.editor.save_requested.connect(self._save_editor_contents)
        return self.editor

    def _build_snapshots_tab(self) -> QWidget:
        self.snapshots_panel = ToolSnapshotsWidget()
        self.snapshots_panel.set_version_available(False)
        return self.snapshots_panel

    def _init_loader_summary(self, parent_layout: QVBoxLayout) -> None:
        """Create summary card showing current file context."""
        summary_group = QGroupBox("Current G-code")
        summary_layout = QGridLayout(summary_group)

        summary_layout.addWidget(QLabel("File:"), 0, 0)
        self.file_name_label = QLabel("No file loaded")
        summary_layout.addWidget(self.file_name_label, 0, 1)

        summary_layout.addWidget(QLabel("Project:"), 1, 0)
        self.project_name_label = QLabel("No project selected")
        summary_layout.addWidget(self.project_name_label, 1, 1)

        summary_layout.addWidget(QLabel("Runtime:"), 2, 0)
        self.runtime_label = QLabel("-")
        summary_layout.addWidget(self.runtime_label, 2, 1)

        summary_layout.addWidget(QLabel("Path Length:"), 3, 0)
        self.distance_label = QLabel("-")
        summary_layout.addWidget(self.distance_label, 3, 1)

        summary_layout.addWidget(QLabel("Feed Override:"), 4, 0)
        self.feed_override_label = QLabel("-")
        summary_layout.addWidget(self.feed_override_label, 4, 1)

        button_row = QHBoxLayout()
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self._emit_open_folder)
        button_row.addWidget(self.open_folder_btn)

        self.reload_button = QPushButton("Reload File")
        self.reload_button.setEnabled(False)
        self.reload_button.clicked.connect(self.reload_file_requested.emit)
        button_row.addWidget(self.reload_button)
        button_row.addStretch()
        summary_layout.addLayout(button_row, 5, 0, 1, 2)

        parent_layout.addWidget(summary_group)

    def _init_visualization_controls(self, parent_layout: QVBoxLayout) -> None:
        viz_group = QGroupBox("Visualization")
        viz_layout = QGridLayout(viz_group)

        viz_layout.addWidget(QLabel("Visualization:"), 0, 0)
        self.viz_mode_combo = QComboBox()
        self.viz_mode_combo.addItems(["Default", "Feed Rate", "Spindle Speed"])
        viz_layout.addWidget(self.viz_mode_combo, 0, 1)

        self.camera_controls_checkbox = QCheckBox("View Controls")
        self.camera_controls_checkbox.setChecked(True)
        viz_layout.addWidget(self.camera_controls_checkbox, 0, 2)

        # Path colors
        viz_layout.addWidget(QLabel("Path Colors:"), 1, 0)
        color_row = QHBoxLayout()
        self.cut_color_btn = QPushButton("Cut Color")
        self.ahead_color_btn = QPushButton("Ahead Color")
        self._set_button_color(self.cut_color_btn, (0.0, 0.8, 0.4))
        self._set_button_color(self.ahead_color_btn, (0.35, 0.35, 0.7))
        self.cut_color_btn.clicked.connect(lambda: self._pick_color(self.cut_color_btn, self.cut_color_changed))
        self.ahead_color_btn.clicked.connect(
            lambda: self._pick_color(self.ahead_color_btn, self.ahead_color_changed)
        )
        color_row.addWidget(self.cut_color_btn)
        color_row.addWidget(self.ahead_color_btn)
        color_row.addStretch()
        viz_layout.addLayout(color_row, 1, 1, 1, 2)

        # Layer visibility as toggleable move-type filters
        viz_layout.addWidget(QLabel("Layers:"), 2, 0)
        filters_layout = QHBoxLayout()
        self.layer_filters = {
            "not_cut": QCheckBox("Not Cut"),
            "cut": QCheckBox("Cut"),
            "rapids": QCheckBox("Rapids"),
            "tool_change": QCheckBox("Tool Change"),
        }
        for key, cb in self.layer_filters.items():
            cb.setChecked(True)
            filters_layout.addWidget(cb)
        filters_layout.addStretch()
        viz_layout.addLayout(filters_layout, 2, 1, 1, 2)

        viz_layout.setColumnStretch(1, 1)
        parent_layout.addWidget(viz_group)

    # ------------------------------------------------------------------
    # Integration helpers
    # ------------------------------------------------------------------
    def set_material_choices(self, materials: list[str]) -> None:
        """Populate material choices while preserving current selection."""
        if not self.material_combo:
            return
        current = self.material_combo.currentText()
        block = self.material_combo.blockSignals(True)
        self.material_combo.clear()
        for name in materials:
            self.material_combo.addItem(name)
        if current:
            idx = self.material_combo.findText(current)
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)
            else:
                self.material_combo.setEditText(current)
        self.material_combo.blockSignals(block)

    def set_material_value(self, value: str) -> None:
        """Set the material field without emitting change."""
        if not self.material_combo:
            return
        block = self.material_combo.blockSignals(True)
        self.material_combo.setEditText(value or "")
        self.material_combo.blockSignals(block)

    def current_material_value(self) -> str:
        """Return current material text."""
        if not self.material_combo:
            return ""
        return self.material_combo.currentText().strip()

    def set_project_directory(self, base_path: Optional[str]) -> None:
        """Set the base directory for saving edited G-code."""
        if not base_path:
            self.project_base_directory = None
            return
        try:
            self.project_base_directory = Path(base_path)
            self.project_base_directory.mkdir(parents=True, exist_ok=True)
        except Exception:  # pragma: no cover - best effort
            self.project_base_directory = None

    def _save_editor_contents(self, text: str) -> None:
        default_dir = self.project_base_directory or Path.home()
        suggested = str(default_dir / "edited_gcode.nc")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Edited G-code",
            suggested,
            "G-code Files (*.nc *.gcode *.tap);;All Files (*)",
        )
        if not path:
            return
        try:
            Path(path).write_text(text, encoding="utf-8")
            self.logger.info("Saved edited G-code to %s", path)
            self.file_saved.emit(path)
            QMessageBox.information(self, "G-code Saved", f"Edited file saved to:\n{path}")
        except Exception as exc:  # pragma: no cover - UI feedback
            self.logger.warning("Failed to save edited G-code to %s: %s", path, exc)
            QMessageBox.warning(self, "Save Failed", f"Could not save file:\n{exc}")

    # ------------------------------------------------------------------
    # Color helpers
    # ------------------------------------------------------------------
    def _set_button_color(self, button: QPushButton, color: tuple[float, float, float]) -> None:
        r, g, b = [int(c * 255) for c in color]
        button.setStyleSheet(f"QPushButton {{ background-color: rgb({r},{g},{b}); color: #fff; }}")

    def _pick_color(self, button: QPushButton, signal: Signal) -> None:
        current_style = button.palette().button().color()
        initial = QColorDialog.getColor(current_style, self, "Select Color")
        if not initial.isValid():
            return
        r, g, b, _ = initial.getRgb()
        color_tuple = (r / 255.0, g / 255.0, b / 255.0)
        self._set_button_color(button, color_tuple)
        signal.emit(color_tuple)

    def update_loader_summary(
        self,
        *,
        file_path: Optional[str],
        project_name: Optional[str],
        runtime_text: str,
        distance_text: str,
        feed_override_text: str,
    ) -> None:
        """Update the loader summary card with the latest metrics."""
        self._current_file_path = file_path

        if self.file_name_label is not None:
            file_name = Path(file_path).name if file_path else "No file loaded"
            self.file_name_label.setText(file_name)
        if self.project_name_label is not None:
            self.project_name_label.setText(project_name or "No project selected")
        if self.runtime_label is not None:
            self.runtime_label.setText(runtime_text or "-")
        if self.distance_label is not None:
            self.distance_label.setText(distance_text or "-")
        if self.feed_override_label is not None:
            self.feed_override_label.setText(feed_override_text or "-")

        enabled = bool(file_path)
        if self.open_folder_btn is not None:
            self.open_folder_btn.setEnabled(enabled)
        if self.reload_button is not None:
            self.reload_button.setEnabled(enabled)

    def _emit_open_folder(self) -> None:
        """Emit the open-folder request when a file is available."""
        if self._current_file_path:
            self.open_folder_requested.emit(self._current_file_path)
