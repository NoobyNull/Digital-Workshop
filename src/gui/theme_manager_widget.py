
"""
ThemeManagerWidget: Comprehensive theme editor with live preview.

- Left: Scrollable color controls grouped by category, with search filter.
- Right: Live preview window built from real Qt widgets.
- Bottom: Actions (Save, Load, Export, Import, Apply, Reset, Close).
- Real-time updates via ThemeManager set_colors + cached CSS processing.

Run standalone for testing:
    python -m src.gui.theme_manager_widget
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QGroupBox, QPushButton, QLabel, QColorDialog,
    QFileDialog, QLineEdit, QTextEdit, QComboBox, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox, QRadioButton, QSlider,
    QSpinBox, QFrame, QMenuBar, QMenu, QToolBar, QStatusBar,
    QDockWidget, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QMessageBox, QMainWindow, QTableWidget, QHeaderView, QApplication
)

from gui.theme import (
    ThemeManager, FALLBACK_COLOR, COLORS, SPACING_4, SPACING_8, SPACING_12, SPACING_16, SPACING_24,
    hex_to_rgb, ThemeDefaults
)
from core.logging_config import get_logger


def _contrasting_text_color(hex_color: str) -> str:
    """
    Choose black/white text for best contrast against a background color.
    Falls back to default theme text if parsing fails.
    """
    try:
        r, g, b = hex_to_rgb(hex_color)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)
        return "#000000" if brightness >= 128 else "#ffffff"
    except Exception:
        return COLORS.text


def _pretty_label(var_name: str) -> str:
    """Humanize variable name: button_default_bg -> Button Default Bg"""
    return " ".join([part.capitalize() for part in var_name.split("_")])


def _build_category_map() -> Dict[str, List[str]]:
    """
    Build category grouping for variables based on prefix heuristics.
    Any unknown keys fall into 'Other'.
    """
    tm = ThemeManager.instance()
    keys = sorted(tm.colors.keys())

    # Category definitions by prefixes
    categories: Dict[str, List[str]] = {
        "Window & UI": [],
        "Surfaces": [],
        "Toolbars": [],
        "Status Bar": [],
        "Dock Widgets": [],
        "Buttons": [],
        "Inputs": [],
        "Combobox": [],
        "Progress Bar": [],
        "Tabs": [],
        "Tables & Lists": [],
        "Scrollbars": [],
        "Splitters": [],
        "Group Boxes": [],
        "Checkboxes & Radios": [],
        "Spinbox & Slider": [],
        "Date/Time Edits": [],
        "Labels": [],
        "Status Indicators": [],
        "Accent / Brand": [],
        "Interactions": [],
        "Viewer / 3D": [],
        "Stars / Ratings": [],
        "Borders & Dividers": [],
        "Misc": [],
        "Other": [],
    }

    def add(cat: str, name: str) -> bool:
        categories[cat].append(name)
        return True

    for k in keys:
        if k in ("window_bg", "text", "text_inverse", "text_muted", "disabled_text", "menubar_bg", "menubar_text", "menubar_border", "menubar_item_hover_bg", "menubar_item_hover_text", "menubar_item_pressed_bg"):
            add("Window & UI", k)
        elif k.startswith("surface") or k in ("card_bg",):
            add("Surfaces", k)
        elif k.startswith("toolbar") or k.startswith("toolbutton"):
            add("Toolbars", k)
        elif k.startswith("statusbar_"):
            add("Status Bar", k)
        elif k.startswith("dock_"):
            add("Dock Widgets", k)
        elif k.startswith("button_"):
            add("Buttons", k)
        elif k.startswith("input_") or k.startswith("selection_"):
            add("Inputs", k)
        elif k.startswith("combobox_"):
            add("Combobox", k)
        elif k.startswith("progress_"):
            add("Progress Bar", k)
        elif k.startswith("tab_"):
            add("Tabs", k)
        elif k.startswith("table_") or k.startswith("header_"):
            add("Tables & Lists", k)
        elif k.startswith("scrollbar_"):
            add("Scrollbars", k)
        elif k.startswith("splitter_"):
            add("Splitters", k)
        elif k.startswith("groupbox_"):
            add("Group Boxes", k)
        elif k.startswith("checkbox_") or k.startswith("radio_"):
            add("Checkboxes & Radios", k)
        elif k.startswith("spinbox_") or k.startswith("slider_"):
            add("Spinbox & Slider", k)
        elif k.startswith("dateedit_"):
            add("Date/Time Edits", k)
        elif k.startswith("label_"):
            add("Labels", k)
        elif k in ("success", "warning", "error", "status_good_bg", "status_good_text", "status_good_border",
                   "status_warning_bg", "status_warning_text", "status_warning_border",
                   "status_error_bg", "status_error_text", "status_error_border"):
            add("Status Indicators", k)
        elif k in ("primary", "primary_hover", "primary_text"):
            add("Accent / Brand", k)
        elif k in ("hover", "pressed"):
            add("Interactions", k)
        elif k in ("canvas_bg", "model_surface", "model_ambient", "model_specular", "light_color", "edge_color"):
            add("Viewer / 3D", k)
        elif k.startswith("star_"):
            add("Stars / Ratings", k)
        elif k in ("border", "border_light", "focus_border"):
            add("Borders & Dividers", k)
        elif k.endswith("_rgba") or k.startswith("loading_overlay_"):
            add("Misc", k)
        else:
            add("Other", k)

    # Remove empty categories to keep UI compact
    categories = {c: vs for c, vs in categories.items() if len(vs) > 0}
    return categories


class ColorRow(QWidget):
    """
    One row for a single color variable:
    - label
    - color preview button (shows hex)
    - Pick Color
    - Reset
    """

    def __init__(
        self,
        var_name: str,
        default_hex: str,
        on_changed: Callable[[str, str], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.var_name = var_name
        self._default_hex = default_hex
        self._on_changed = on_changed

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_8)

        self.name_label = QLabel(_pretty_label(var_name))
        self.name_label.setMinimumWidth(160)

        self.color_btn = QPushButton("")
        self.color_btn.setObjectName("colorPreviewBtn")
        self.color_btn.setFixedWidth(120)

        self.pick_btn = QPushButton("Pick Color")
        self.reset_btn = QPushButton("Reset")

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.color_btn, 0)
        layout.addWidget(self.pick_btn, 0)
        layout.addWidget(self.reset_btn, 0)
        layout.addStretch(1)

        self.pick_btn.clicked.connect(self._on_pick)
        self.reset_btn.clicked.connect(self._on_reset)
        self.color_btn.clicked.connect(self._on_pick)

        self.update_from_theme()

    def update_from_theme(self) -> None:
        tm = ThemeManager.instance()
        hex_val = tm.get_color(self.var_name, context="ThemeManagerWidget.ColorRow")
        self._apply_button_style(hex_val)

    def _apply_button_style(self, hex_val: str) -> None:
        txt = _contrasting_text_color(hex_val)
        self.color_btn.setText(hex_val)
        self.color_btn.setStyleSheet(
            f"QPushButton#colorPreviewBtn {{ background-color: {hex_val}; color: {txt}; border: 1px solid {COLORS.border}; padding: 4px 8px; }}"
        )

    def _on_pick(self) -> None:
        current_hex = ThemeManager.instance().get_color(self.var_name, context="picker")
        try:
            r, g, b = hex_to_rgb(current_hex)
            initial = QColor(r, g, b)
        except Exception:
            initial = QColor(255, 0, 255)  # fallback visually noticeable

        color = QColorDialog.getColor(initial, self, f"Select color for {self.var_name}")
        if color.isValid():
            new_hex = f"#{color.red():02x}{color.green():02x}{color.blue():02x}"
            self._apply_button_style(new_hex)
            self._on_changed(self.var_name, new_hex)

    def _on_reset(self) -> None:
        self._apply_button_style(self._default_hex)
        self._on_changed(self.var_name, self._default_hex)


CSS_PREVIEW_TEMPLATE = """
/* Base window */
QMainWindow {{
    background-color: {{window_bg}};
    color: {{text}};
}}

/* Menubar */
QMenuBar {{
    background-color: {{menubar_bg}};
    color: {{menubar_text}};
    border-bottom: 1px solid {{menubar_border}};
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background: {{menubar_item_hover_bg}};
    color: {{menubar_item_hover_text}};
}}
QMenuBar::item:pressed {{
    background: {{menubar_item_pressed_bg}};
}}

/* Toolbar */
QToolBar {{
    background-color: {{toolbar_bg}};
    border-bottom: 1px solid {{toolbar_border}};
}}
QToolButton {{
    background: {{toolbutton_bg}};
    border: 1px solid {{toolbutton_border}};
    padding: 4px 8px;
}}
QToolButton:hover {{
    background: {{toolbutton_hover_bg}};
    border: 1px solid {{toolbutton_hover_border}};
}}
QToolButton:checked {{
    background: {{toolbutton_checked_bg}};
    color: {{toolbutton_checked_text}};
    border: 1px solid {{toolbutton_checked_border}};
}}

/* Status bar */
QStatusBar {{
    background-color: {{statusbar_bg}};
    color: {{statusbar_text}};
    border-top: 1px solid {{statusbar_border}};
}}

/* Dock */
QDockWidget {{
    background-color: {{dock_bg}};
    color: {{dock_text}};
    border: 1px solid {{dock_border}};
}}
QDockWidget::title {{
    background-color: {{dock_title_bg}};
    border-bottom: 1px solid {{dock_title_border}};
    padding: 4px 6px;
}}

/* Buttons */
QPushButton {{
    background-color: {{button_bg}};
    color: {{button_text}};
    border: 1px solid {{button_border}};
    padding: 6px 12px;
    border-radius: 2px;
}}
QPushButton:hover {{
    background-color: {{button_hover_bg}};
    border: 1px solid {{button_hover_border}};
}}
QPushButton:pressed {{
    background-color: {{button_pressed_bg}};
}}
QPushButton:checked {{
    background-color: {{button_checked_bg}};
    color: {{button_checked_text}};
    border: 1px solid {{button_checked_border}};
}}
QPushButton:default {{
    border: 1px solid {{button_default_border}};
    background-color: {{button_default_bg}};
    color: {{button_default_text}};
    font-weight: bold;
}}
QPushButton:disabled {{
    background-color: {{button_disabled_bg}};
    color: {{button_disabled_text}};
    border: 1px solid {{button_disabled_border}};
}}

/* Inputs */
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    border: 1px solid {{input_border}};
    border-radius: 2px;
    padding: 6px;
    background-color: {{input_bg}};
    color: {{input_text}};
    selection-background-color: {{selection_bg}};
    selection-color: {{selection_text}};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {{input_focus_border}};
}}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    background-color: {{input_disabled_bg}};
    color: {{input_disabled_text}};
}}

/* Progress bar */
QProgressBar {{
    border: 1px solid {{progress_border}};
    border-radius: 2px;
    text-align: center;
    background-color: {{progress_bg}};
    color: {{progress_text}};
}}
QProgressBar::chunk {{
    background-color: {{progress_chunk}};
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {{tab_pane_border}};
    background-color: {{tab_pane_bg}};
}}
QTabBar::tab {{
    background: {{tab_bg}};
    padding: 6px 10px;
    margin-right: 2px;
    border: 1px solid {{tab_border}};
    border-bottom: none;
    color: {{tab_text}};
}}
QTabBar::tab:selected {{
    background: {{tab_selected_bg}};
    border-bottom: 2px solid {{tab_selected_border}};
}}
QTabBar::tab:hover {{
    background: {{tab_hover_bg}};
}}

/* Tables & Lists */
QTableWidget {{
    background-color: {{table_bg}};
    color: {{table_text}};
    gridline-color: {{table_gridline}};
    border: 1px solid {{table_border}};
}}
QHeaderView::section {{
    background-color: {{header_bg}};
    color: {{header_text}};
    border: 1px solid {{header_border}};
}}
QListWidget {{
    background-color: {{table_bg}};
    color: {{table_text}};
    border: 1px solid {{table_border}};
    selection-background-color: {{selection_bg}};
    selection-color: {{selection_text}};
}}

/* GroupBox */
QGroupBox {{
    font-weight: bold;
    border: 2px solid {{groupbox_border}};
    border-radius: 4px;
    margin-top: 1ex;
    padding-top: 8px;
    background-color: {{groupbox_bg}};
    color: {{groupbox_text}};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px 0 4px;
    color: {{groupbox_title_text}};
}}

/* Checkboxes and radios (basic) */
QCheckBox, QRadioButton {{
    color: {{text}};
}}

/* Slider */
QSlider::groove:horizontal {{
    height: 6px;
    background: {{slider_groove_bg}};
    border: 1px solid {{slider_groove_border}};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 12px;
    background: {{slider_handle}};
    border: 1px solid {{slider_handle_border}};
    margin: -5px 0;
    border-radius: 6px;
}}

/* Spinbox */
QSpinBox {{
    background: {{spinbox_bg}};
    color: {{spinbox_text}};
    border: 1px solid {{spinbox_border}};
}}
QSpinBox:focus {{
    border: 2px solid {{spinbox_focus_border}};
}}

/* Status indicators (by objectName) */
QLabel#status-good {{
    background-color: {{status_good_bg}};
    color: {{status_good_text}};
    border: 1px solid {{status_good_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}
QLabel#status-warning {{
    background-color: {{status_warning_bg}};
    color: {{status_warning_text}};
    border: 1px solid {{status_warning_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}
QLabel#status-error {{
    background-color: {{status_error_bg}};
    color: {{status_error_text}};
    border: 1px solid {{status_error_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}

/* Generic labels */
QLabel {{
    color: {{label_text}};
}}
"""


class PreviewWindow(QMainWindow):
    """
    Mini QMainWindow with real widgets. Styles are applied via ThemeManager CSS processing.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview")
        self.resize(700, 520)

        # Menubar
        bar = self.menuBar()
        menu_file = bar.addMenu("File")
        menu_file.addAction("New")
        menu_file.addAction("Open")
        menu_file.addSeparator()
        menu_file.addAction("Exit")

        menu_edit = bar.addMenu("Edit")
        menu_edit.addAction("Copy")
        menu_edit.addAction("Paste")

        menu_view = bar.addMenu("View")
        menu_view.addAction("Reset Layout")

        # Toolbar
        tb = QToolBar("Main Toolbar")
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)
        tb.addAction("New")
        tb.addAction("Open")
        tb.addAction("Save")

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready", 2000)

        # Dock
        dock = QDockWidget("Sample Dock", self)
        dock_list = QListWidget()
        for i in range(5):
            dock_list.addItem(QListWidgetItem(f"Item {i+1}"))
        dock.setWidget(dock_list)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        cv = QVBoxLayout(central)
        cv.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        cv.setSpacing(SPACING_12)

        # Button row
        row_btns = QHBoxLayout()
        btn_normal = QPushButton("Normal")
        btn_hover_hint = QLabel("(Hover states preview on mouseover)")
        btn_pressed_hint = QLabel("(Press to see pressed state)")
        btn_checked = QPushButton("Checked"); btn_checked.setCheckable(True); btn_checked.setChecked(True)
        btn_disabled = QPushButton("Disabled"); btn_disabled.setEnabled(False)
        btn_default = QPushButton("Default"); btn_default.setDefault(True)

        row_btns.addWidget(btn_normal)
        row_btns.addWidget(btn_checked)
        row_btns.addWidget(btn_disabled)
        row_btns.addWidget(btn_default)
        row_btns.addStretch(1)
        cv.addLayout(row_btns)
        cv.addWidget(btn_hover_hint)
        cv.addWidget(btn_pressed_hint)

        # Inputs
        row_inputs = QHBoxLayout()
        le = QLineEdit(); le.setPlaceholderText("QLineEdit")
        te = QTextEdit(); te.setPlainText("QTextEdit\nmultiline")
        cb = QComboBox(); cb.addItems(["Option A", "Option B", "Option C"])
        sp = QSpinBox(); sp.setRange(0, 100); sp.setValue(42)
        sl = QSlider(Qt.Horizontal); sl.setRange(0, 100); sl.setValue(50)
        row_inputs.addWidget(le, 1)
        row_inputs.addWidget(te, 1)
        row_inputs.addWidget(cb, 0)
        row_inputs.addWidget(sp, 0)
        row_inputs.addWidget(sl, 1)
        cv.addLayout(row_inputs)

        # Progress
        pb = QProgressBar(); pb.setValue(45)
        cv.addWidget(pb)

        # Tabs with table and list
        tabs = QTabWidget()
        tab1 = QWidget(); tab1v = QVBoxLayout(tab1)
        table = QTableWidget(3, 3)
        table.setHorizontalHeaderLabels(["A", "B", "C"])
        for r in range(3):
            for c in range(3):
                table.setItem(r, c, QTableWidgetItem(f"{r},{c}"))
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        tab1v.addWidget(table)

        tab2 = QWidget(); tab2v = QVBoxLayout(tab2)
        l = QListWidget(); l.addItems([f"List {i+1}" for i in range(8)])
        tab2v.addWidget(l)

        tabs.addTab(tab1, "Table")
        tabs.addTab(tab2, "List")
        cv.addWidget(tabs)



        # Group box with checks/radios
        grp = QGroupBox("Group && State Indicators")
        gb_v = QVBoxLayout(grp)
        cb1 = QCheckBox("Enable feature")
        cb2 = QCheckBox("Disabled option"); cb2.setEnabled(False)
        rb1, rb2 = QRadioButton("Choice A"), QRadioButton("Choice B")
        rb1.setChecked(True)
        gb_v.addWidget(cb1)
        gb_v.addWidget(cb2)
        gb_v.addWidget(rb1)
        gb_v.addWidget(rb2)
        cv.addWidget(grp)

        # Status indicators
        status_row = QHBoxLayout()
        lbl_ok = QLabel("Success"); lbl_ok.setObjectName("status-good")
        lbl_warn = QLabel("Warning"); lbl_warn.setObjectName("status-warning")
        lbl_err = QLabel("Error"); lbl_err.setObjectName("status-error")
        status_row.addWidget(lbl_ok)
        status_row.addWidget(lbl_warn)
        status_row.addWidget(lbl_err)
        status_row.addStretch(1)
        cv.addLayout(status_row)

        # Register and apply preview stylesheet
        tm = ThemeManager.instance()
        tm.register_widget(self, css_text=CSS_PREVIEW_TEMPLATE)
        tm.apply_stylesheet(self)


class ThemeManagerWidget(QDialog):
    """
    ThemeManagerWidget: left-side scrollable color editor, right-side live preview,
    bottom action buttons. Integrates with ThemeManager singleton.

    Signals:
      - themeApplied(dict): emitted when 'Apply' is pressed with current colors dict
    """

    themeApplied = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Theme Manager")
        self.resize(1100, 730)

        self.logger = get_logger("gui.theme_manager")
        self.tm = ThemeManager.instance()
        self.defaults: Dict[str, str] = asdict(ThemeDefaults())
        self._rows: Dict[str, ColorRow] = {}
        self._category_groups: Dict[str, QGroupBox] = {}
        self._category_items: Dict[str, List[str]] = {}
        self._pending_overrides: Dict[str, str] = {}

        # Layout: Splitter (left controls, right preview)
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        root.setSpacing(SPACING_12)

        splitter = QSplitter(Qt.Horizontal, self)
        root.addWidget(splitter, 1)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(SPACING_8)

        # Search/filter
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search colors (name or label)...")
        self.search_edit.textChanged.connect(self._on_filter_text_changed)
        left_layout.addWidget(self.search_edit)

        # Scroll area for groups
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        left_layout.addWidget(self.scroll_area, 1)

        left_inner = QWidget()
        self.scroll_area.setWidget(left_inner)
        self.left_inner_layout = QVBoxLayout(left_inner)
        self.left_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.left_inner_layout.setSpacing(SPACING_8)

        # Build color groups and rows
        self._build_color_groups()

        self.left_inner_layout.addStretch(1)

        splitter.addWidget(left_panel)

        # Right panel: preview
        self.preview = PreviewWindow()
        splitter.addWidget(self.preview)

        # Bottom action buttons
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_load = QPushButton("Load")
        self.btn_export = QPushButton("Export")
        self.btn_import = QPushButton("Import")
        self.btn_apply = QPushButton("Apply")
        self.btn_reset = QPushButton("Reset to Default")
        self.btn_close = QPushButton("Close")

        # Mark Apply as default for Enter key in dialog context
        self.btn_apply.setDefault(True)

        for b in (self.btn_save, self.btn_load, self.btn_export, self.btn_import, self.btn_apply, self.btn_reset):
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_close)
        root.addLayout(btn_row)

        # Wire up actions
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_import.clicked.connect(self._on_import)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_reset.clicked.connect(self._on_reset_defaults)
        self.btn_close.clicked.connect(self.close)

        # Initial stylesheet application to preview
        self.refresh_preview()

    # ---------- UI builders ----------

    def _build_color_groups(self) -> None:
        cats = _build_category_map()
        # Persist category ordering by insertion
        for cat, names in cats.items():
            group = QGroupBox(cat)
            lay = QVBoxLayout(group)
            lay.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)
            lay.setSpacing(SPACING_8)

            for var_name in names:
                default_hex = self.defaults.get(var_name, FALLBACK_COLOR)
                row = ColorRow(var_name, default_hex, on_changed=self._on_color_changed, parent=group)
                self._rows[var_name] = row
                lay.addWidget(row)

            lay.addStretch(1)
            self.left_inner_layout.addWidget(group)
            self._category_groups[cat] = group
            self._category_items[cat] = list(names)

    # ---------- Actions ----------

    def _on_color_changed(self, var_name: str, hex_val: str) -> None:
        """
        Update ThemeManager with a single-color override and refresh preview live.
        """
        try:
            self._pending_overrides[var_name] = hex_val
            self.tm.set_colors({var_name: hex_val})
            self.refresh_preview()
        except Exception as exc:
            QMessageBox.warning(self, "Theme Update Error", f"Failed to apply color for {var_name}:\n{exc}")

    def _on_save(self) -> None:
        try:
            self.tm.save_to_settings()
            QMessageBox.information(self, "Theme", "Theme saved to AppData.")
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", f"Failed to save theme:\n{exc}")

    def _on_load(self) -> None:
        try:
            self.tm.load_from_settings()
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Theme loaded from AppData.")
        except Exception as exc:
            QMessageBox.warning(self, "Load Failed", f"Failed to load theme:\n{exc}")

    def _on_export(self) -> None:
        fn, _ = QFileDialog.getSaveFileName(self, "Export Theme", filter="JSON Files (*.json);;All Files (*.*)")
        if not fn:
            return
        try:
            p = Path(fn)
            if p.suffix.lower() != ".json":
                p = p.with_suffix(".json")
            self.tm.export_theme(p)
            QMessageBox.information(self, "Theme", f"Theme exported to:\n{p}")
        except Exception as exc:
            QMessageBox.warning(self, "Export Failed", f"Failed to export theme:\n{exc}")

    def _on_import(self) -> None:
        fn, _ = QFileDialog.getOpenFileName(self, "Import Theme", filter="JSON Files (*.json);;All Files (*.*)")
        if not fn:
            return
        try:
            self.tm.import_theme(fn)
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Theme imported successfully.")
        except Exception as exc:
            QMessageBox.warning(self, "Import Failed", f"Failed to import theme:\n{exc}")

    def _on_apply(self) -> None:
        try:
            # Re-apply to all registered widgets across the app
            self.tm.apply_to_registered()
            # Emit signal with current colors for external listeners
            self.themeApplied.emit(self.tm.colors)
            QMessageBox.information(self, "Theme", "Theme applied to application.")
        except Exception as exc:
            QMessageBox.warning(self, "Apply Failed", f"Failed to apply theme:\n{exc}")

    def _on_reset_defaults(self) -> None:
        try:
            self.tm.set_colors(self.defaults)
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Reset to default theme.")
        except Exception as exc:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset theme:\n{exc}")

    # ---------- Helpers ----------

    def refresh_preview(self) -> None:
        """
        Re-process and set stylesheet on preview window using ThemeManager.
        """
        try:
            self.tm.apply_stylesheet(self.preview)
        except Exception:
            # Fail-safe: don't break dialog if styling fails
            pass

    def _sync_rows_from_theme(self) -> None:
        """
        Reset each ColorRow's button to reflect current ThemeManager values.
        """
        for row in self._rows.values():
            row.update_from_theme()

    def _on_filter_text_changed(self, text: str) -> None:
        """
        Filter rows by substring in variable name or humanized label.
        Hide groups with no visible rows.
        """
        s = (text or "").strip().lower()
        for cat, group in self._category_groups.items():
            any_visible = False
            for var_name in self._category_items.get(cat, []):
                row = self._rows[var_name]
                target = f"{var_name} {_pretty_label(var_name)}".lower()
                visible = (s in target) if s else True
                row.setVisible(visible)
                any_visible = any_visible or visible
            group.setVisible(any_visible)

    # ---------- Integration Hooks ----------

    @classmethod
    def open_dialog(cls, parent: Optional[QWidget] = None) -> "ThemeManagerWidget":
        """
        Convenience helper to open as a dialog from main window menu.
        Returns the instance (already shown modally via exec).
        """
        dlg = cls(parent)
        dlg.setModal(True)
        dlg.exec()
        return dlg

    def closeEvent(self, event) -> None:
        """
        Cleanup preview if needed; ThemeManager keeps weak references so no explicit unregister required.
        """
        try:
            if self.preview:
                self.preview.deleteLater()
        except Exception:
            pass
        super().closeEvent(event)


# ---------- Standalone test harness ----------

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ThemeManagerWidget()
    w.show()
    sys.exit(app.exec())
