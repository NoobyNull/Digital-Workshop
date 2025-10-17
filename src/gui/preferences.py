from __future__ import annotations

"""
Preferences dialog with tabbed interface:
- Display
- System
- Files
- Theming (live-apply + persist to AppData)

The Theming tab edits central color variables in gui.theme.COLORS and applies
changes live across the running app. On Save, the current theme is persisted
to AppData and loaded on next startup.
"""

from dataclasses import asdict
from typing import Dict, List, Callable

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QDialog, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QCheckBox
)

from src.gui.theme import (
    COLORS,
    set_theme, save_theme_to_settings, theme_to_dict, color as color_hex, hex_to_rgb
)
from src.gui.files_tab import FilesTab


class PreferencesDialog(QDialog):
    """
    Application preferences dialog with multiple tabs.
    Emits theme_changed whenever the Theming tab applies updates.
    """
    theme_changed = Signal()

    def __init__(self, parent=None, on_reset_layout=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.on_reset_layout = on_reset_layout
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Placeholder tabs for scope expansion
        self.display_tab = DisplayTab(on_reset_layout=self.on_reset_layout)
        self.system_tab = PlaceholderTab("System settings (coming soon)")
        self.files_tab = FilesTab()

        self.theming_tab = ThemingTab(on_live_apply=self._on_theme_live_applied)

        self.tabs.addTab(self.display_tab, "Display")
        self.tabs.addTab(self.system_tab, "System")
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.theming_tab, "Theming")

        # Dialog action buttons
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_save = QPushButton("Save")
        self.btn_close = QPushButton("Close")

        buttons_row.addWidget(self.btn_reset)
        buttons_row.addWidget(self.btn_save)
        buttons_row.addWidget(self.btn_close)

        layout.addLayout(buttons_row)

        # Wire actions
        self.btn_close.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save_and_notify)
        self.btn_reset.clicked.connect(self._reset_to_defaults)

    def _on_theme_live_applied(self):
        # Bubble up to MainWindow so it can re-render stylesheets on key widgets
        self.theme_changed.emit()

    def _save_and_notify(self):
        try:
            save_theme_to_settings()
            QMessageBox.information(self, "Saved", "Theme settings saved.")
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save theme settings:\n{e}")

    def _reset_to_defaults(self):
        # Build defaults from the dataclass defaults
        try:
            # Get default values from the ThemeDefaults dataclass
            from src.gui.theme import ThemeDefaults
            default_map = asdict(ThemeDefaults())
        except Exception:
            # Fallback: if introspection doesn't work cross-runtime, use initial theme_to_dict()
            default_map = theme_to_dict()
        set_theme(default_map)
        self.theming_tab.reload_from_current()
        self._on_theme_live_applied()


class ThemingTab(QWidget):
    """
    Theming editor that lists all color variables with editable hex values
    and a color picker per row. Applies live changes via on_live_apply callback.
    """

    def __init__(self, on_live_apply=None, parent=None):
        super().__init__(parent)
        self.on_live_apply = on_live_apply
        self._setup_ui()

    def _normalize_hex(self, val: str) -> str:
        """
        Normalize user-entered hex to #rrggbb; returns original value for CSS keywords.
        Returns empty string on invalid hex.
        """
        if not val:
            return ""
        s = val.strip()
        lower = s.lower()
        
        # Pass through CSS color functions and keywords without modification
        css_keywords = {"transparent", "inherit", "initial", "unset", "currentcolor"}
        if lower.startswith("rgba(") or lower.startswith("rgb(") or lower in css_keywords:
            return s
        
        # Handle hex colors
        if not s.startswith("#"):
            s = "#" + s
        # Accept #rgb and #rrggbb
        if len(s) == 4:
            r, g, b = s[1], s[2], s[3]
            s = f"#{r}{r}{g}{g}{b}{b}"
        if len(s) != 7:
            return ""
        try:
            int(s[1:], 16)
            return s.lower()
        except Exception:
            return ""

    def _update_pick_button_color(self, btn: QPushButton, val: str) -> None:
        """Update the 'Pick…' button swatch to match the given hex value using theme variables."""
        hex_val = self._normalize_hex(val)
        # For CSS keywords, show neutral style
        if not hex_val or not hex_val.startswith("#"):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color_hex('surface')}; color: {color_hex('text')}; border: 1px solid {color_hex('border')}; }}"
            )
            return
        try:
            r, g, b = hex_to_rgb(hex_val)
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            text_color = color_hex('text') if brightness >= 0.6 else color_hex('text_inverse')
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_val}; color: {text_color}; border: 1px solid {color_hex('border')}; }}"
            )
        except Exception:
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color_hex('surface')}; color: {color_hex('text')}; border: 1px solid {color_hex('border')}; }}"
            )

    def _update_pick_button_color(self, btn: QPushButton, val: str) -> None:
        """Update the pick button's background to match the given hex value using theme variables."""
        hex_val = self._normalize_hex(val)
        if not hex_val:
            # fallback neutral styling when invalid (using theme variables)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color_hex('surface')}; color: {color_hex('text')}; border: 1px solid {color_hex('border')}; }}"
            )
            return
        try:
            r, g, b = hex_to_rgb(hex_val)
            # Perceived brightness to choose legible text color
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            text_color = color_hex('text') if brightness >= 0.6 else color_hex('text_inverse')
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_val}; color: {text_color}; border: 1px solid {color_hex('border')}; }}"
            )
        except Exception:
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color_hex('surface')}; color: {color_hex('text')}; border: 1px solid {color_hex('border')}; }}"
            )

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        hdr = QLabel("Adjust UI colors. Changes apply immediately. Click 'Save' in Preferences to persist.")
        hdr.setWordWrap(True)
        layout.addWidget(hdr)

        # Live apply toggle
        self.live_apply_checkbox = QCheckBox("Apply changes live")
        self.live_apply_checkbox.setChecked(True)
        layout.addWidget(self.live_apply_checkbox)

        # Table for colors
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Hex", "Pick"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        layout.addWidget(self.table)

        # Buttons row
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_apply_all = QPushButton("Apply Now")
        row.addWidget(self.btn_apply_all)
        layout.addLayout(row)

        self.btn_apply_all.clicked.connect(self._apply_from_table)

        self.reload_from_current()

    def _color_keys(self) -> List[str]:
        # keep ordering stable and user-friendly
        keys = list(theme_to_dict().keys())
        # Optional: promote common ones to top
        preferred = [
            "window_bg", "surface", "canvas_bg",
            "text", "text_muted", "text_inverse",
            "primary", "primary_hover", "primary_text",
            "border", "border_light",
            "hover", "pressed",
            "selection_bg", "selection_text",
        ]
        ordered = preferred + [k for k in keys if k not in preferred]
        # Deduplicate while preserving order
        seen = set()
        result = []
        for k in ordered:
            if k not in seen:
                result.append(k)
                seen.add(k)
        return result

    def reload_from_current(self):
        data = theme_to_dict()
        keys = self._color_keys()

        self.table.setRowCount(0)
        for key in keys:
            self._add_color_row(key, data.get(key, ""))

    def _add_color_row(self, key: str, hex_value: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(key)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, 0, name_item)

        hex_edit = QLineEdit(hex_value)
        hex_edit.setObjectName(f"hex_{key}")
        self.table.setCellWidget(row, 1, hex_edit)

        pick_btn = QPushButton("Pick…")
        pick_btn.setObjectName(f"pick_{key}")
        self.table.setCellWidget(row, 2, pick_btn)

        # Initialize picker button color
        self._update_pick_button_color(pick_btn, hex_value)

        # Connect changes
        # Update button swatch while typing
        hex_edit.textChanged.connect(lambda text, btn=pick_btn: self._update_pick_button_color(btn, text))
        hex_edit.editingFinished.connect(self._maybe_apply_live)
        # Pass pick button so we can update its color after selection
        pick_btn.clicked.connect(lambda: self._pick_color_for_row(key, hex_edit, pick_btn))

    def _pick_color_for_row(self, key: str, hex_edit: QLineEdit, pick_btn: QPushButton):
        initial = QColor(hex_edit.text() or color_hex(key))
        c = QColorDialog.getColor(initial, self, f"Pick color for {key}")
        if c and c.isValid():
            hex_edit.setText(c.name())  # #rrggbb
            # Update the button swatch immediately
            self._update_pick_button_color(pick_btn, c.name())
            self._maybe_apply_live()

    def _collect_overrides(self) -> Dict[str, str]:
        overrides: Dict[str, str] = {}
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text()
            hex_widget = self.table.cellWidget(row, 1)
            if isinstance(hex_widget, QLineEdit):
                val = hex_widget.text().strip()
                if val:
                    if not val.startswith("#"):
                        val = f"#{val}"
                    overrides[key] = val
        return overrides

    def _apply_overrides(self):
        overrides = self._collect_overrides()
        if overrides:
            set_theme(overrides)

    def _maybe_apply_live(self):
        if self.live_apply_checkbox.isChecked():
            self._apply_overrides()
            if callable(self.on_live_apply):
                self.on_live_apply()

    def _apply_from_table(self):
        self._apply_overrides()
        if callable(self.on_live_apply):
            self.on_live_apply()


class DisplayTab(QWidget):
    """Display settings tab: reset window/dock layout."""
    def __init__(self, on_reset_layout: Callable | None = None, parent=None):
        super().__init__(parent)
        self.on_reset_layout = on_reset_layout
        layout = QVBoxLayout(self)

        header = QLabel("Window layout and docking")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel("Layout auto-saves when you move or dock panels. Use 'Reset Window Layout' to restore defaults.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Actions row
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_reset_layout = QPushButton("Reset Window Layout")
        row.addWidget(self.btn_reset_layout)
        layout.addLayout(row)

        self.btn_reset_layout.clicked.connect(self._handle_reset)

        layout.addStretch(1)

    def _handle_reset(self):
        try:
            if callable(self.on_reset_layout):
                self.on_reset_layout()
                QMessageBox.information(self, "Layout Reset", "Window layout has been reset to defaults.")
        except Exception as e:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset layout:\n{e}")

class PlaceholderTab(QWidget):
    """Simple placeholder content for non-implemented tabs."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch(1)