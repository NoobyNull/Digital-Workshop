"""
ThemeManagerWidget - Main theme editor dialog.

Comprehensive theme editor with left-side color controls, right-side live preview,
and bottom action buttons. Integrates with ThemeManager singleton.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QScrollArea,
    QGroupBox,
    QPushButton,
    QLabel,
    QColorDialog,
    QFileDialog,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QApplication,
)

from src.gui.theme import (
    ThemeManager,
    FALLBACK_COLOR,
    ThemeDefaults,
    SPACING_8,
    SPACING_12,
    hex_to_rgb,
)
from src.core.logging_config import get_logger

from .color_row import ColorRow
from .preview_window import PreviewWindow
from .theme_manager_helpers import build_category_map, pretty_label


class ThemeManagerWidget(QDialog):
    """
    ThemeManagerWidget: left-side scrollable color editor, right-side live preview,
    bottom action buttons. Integrates with ThemeManager singleton.

    Signals:
      - themeApplied(dict): emitted when 'Apply' is pressed with current colors dict
    """

    themeApplied = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """TODO: Add docstring."""
        super().__init__(parent)
        self.setWindowTitle("Theme Manager")
        self.resize(1100, 730)

        self.logger = get_logger("gui.theme_manager")
        self.tm = ThemeManager.instance()
        self.defaults: Dict[str, str] = asdict(ThemeDefaults())
        self._rows: Dict[str, ColorRow] = {}
        self._category_groups: Dict[str, QGroupBox] = {}
        self._category_items: Dict[str, list] = {}
        self._pending_overrides: Dict[str, str] = {}

        # Preset UI state
        self._preset_key_by_label = {
            "Modern": "modern",
            "High Contrast": "high_contrast",
            "Custom": "custom",
        }
        self._custom_mode_key_by_label = {
            "Auto": "auto",
            "Light": "light",
            "Dark": "dark",
        }
        self._custom_seed_hex = self.tm.get_color("primary", context="ThemeManagerWidget.init")

        # Layout: Splitter (left controls, right preview)
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        root.setSpacing(SPACING_12)

        splitter = QSplitter(1, self)  # Qt.Horizontal = 1
        root.addWidget(splitter, 1)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(SPACING_8)

        # Preset controls
        preset_row = QHBoxLayout()
        preset_label = QLabel("Preset")
        self.preset_combo = QComboBox()
        for lbl in self._preset_key_by_label.keys():
            self.preset_combo.addItem(lbl)
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.preset_combo, 1)
        left_layout.addLayout(preset_row)

        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("Custom mode"))
        self.custom_mode_combo = QComboBox()
        for lbl in self._custom_mode_key_by_label.keys():
            self.custom_mode_combo.addItem(lbl)
        self.btn_set_primary = QPushButton("Set Primary Color")
        custom_row.addWidget(self.custom_mode_combo)
        custom_row.addWidget(self.btn_set_primary)
        custom_row.addStretch(1)
        left_layout.addLayout(custom_row)

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

        self.btn_apply.setDefault(True)

        for b in (
            self.btn_save,
            self.btn_load,
            self.btn_export,
            self.btn_import,
            self.btn_apply,
            self.btn_reset,
        ):
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

        # Initialize preset UI controls after all widgets are created
        self._init_presets_ui()

    def _build_color_groups(self) -> None:
        """Build color editor groups from category map."""
        cats = build_category_map()
        for cat, names in cats.items():
            group = QGroupBox(cat)
            lay = QVBoxLayout(group)
            lay.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)
            lay.setSpacing(SPACING_8)

            for var_name in names:
                default_hex = self.defaults.get(var_name, FALLBACK_COLOR)
                row = ColorRow(
                    var_name,
                    default_hex,
                    on_changed=self._on_color_changed,
                    parent=group,
                )
                self._rows[var_name] = row
                lay.addWidget(row)

            lay.addStretch(1)
            self.left_inner_layout.addWidget(group)
            self._category_groups[cat] = group
            self._category_items[cat] = list(names)

    def _init_presets_ui(self) -> None:
        """Initialize preset combo selection and wire events."""
        current = getattr(self.tm, "current_preset", "custom")
        label = next(
            (lbl for lbl, key in self._preset_key_by_label.items() if key == current),
            "Custom",
        )
        idx = self.preset_combo.findText(label)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)

        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.custom_mode_combo.currentIndexChanged.connect(self._on_custom_mode_changed)
        self.btn_set_primary.clicked.connect(self._on_set_custom_primary)

        self._set_custom_editor_visible(current == "custom")

    def _on_preset_changed(self) -> None:
        """Handle preset selection change."""
        label = self.preset_combo.currentText()
        key = self._preset_key_by_label.get(label, "custom")
        if key != "custom":
            self.tm.apply_preset(key)
            self._sync_rows_from_theme()
            self.refresh_preview()
            self._set_custom_editor_visible(False)
        else:
            self._apply_custom_now()
            self._set_custom_editor_visible(True)

    def _on_custom_mode_changed(self) -> None:
        """Handle custom mode change."""
        if self.preset_combo.currentText() == "Custom":
            self._apply_custom_now()

    def _on_set_custom_primary(self) -> None:
        """Open color picker for custom primary color."""
        try:
            r, g, b = hex_to_rgb(self._custom_seed_hex)
            initial = QColor(r, g, b)
        except Exception:
            initial = QColor(0, 120, 212)
        color = QColorDialog.getColor(initial, self, "Select primary color for Custom theme")
        if color.isValid():
            self._custom_seed_hex = f"#{color.red():02x}{color.green():02x}{color.blue():02x}"
            self._apply_custom_now()

    def _apply_custom_now(self) -> None:
        """Apply derived custom theme."""
        mode_label = self.custom_mode_combo.currentText()
        mode = self._custom_mode_key_by_label.get(mode_label, "auto")
        self.tm.apply_preset("custom", custom_mode=mode, base_primary=self._custom_seed_hex)
        self._sync_rows_from_theme()
        self.refresh_preview()

    def _set_custom_editor_visible(self, show: bool) -> None:
        """Show/hide custom editor controls."""
        self.search_edit.setVisible(show)
        self.scroll_area.setVisible(show)

    def _on_color_changed(self, var_name: str, hex_val: str) -> None:
        """Update ThemeManager with color override."""
        try:
            self._pending_overrides[var_name] = hex_val
            self.tm.set_colors({var_name: hex_val})
            self.refresh_preview()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(
                self,
                "Theme Update Error",
                f"Failed to apply color for {var_name}:\n{exc}",
            )

    def _on_save(self) -> None:
        """Save theme to settings."""
        try:
            self.tm.save_to_settings()
            QMessageBox.information(self, "Theme", "Theme saved to AppData.")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Save Failed", f"Failed to save theme:\n{exc}")

    def _on_load(self) -> None:
        """Load theme from settings."""
        try:
            self.tm.load_from_settings()
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Theme loaded from AppData.")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Load Failed", f"Failed to load theme:\n{exc}")

    def _on_export(self) -> None:
        """Export theme to JSON file."""
        fn, _ = QFileDialog.getSaveFileName(
            self, "Export Theme", filter="JSON Files (*.json);;All Files (*.*)"
        )
        if not fn:
            return
        try:
            p = Path(fn)
            if p.suffix.lower() != ".json":
                p = p.with_suffix(".json")
            self.tm.export_theme(p)
            QMessageBox.information(self, "Theme", f"Theme exported to:\n{p}")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Export Failed", f"Failed to export theme:\n{exc}")

    def _on_import(self) -> None:
        """Import theme from JSON file."""
        fn, _ = QFileDialog.getOpenFileName(
            self, "Import Theme", filter="JSON Files (*.json);;All Files (*.*)"
        )
        if not fn:
            return
        try:
            self.tm.import_theme(fn)
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Theme imported successfully.")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Import Failed", f"Failed to import theme:\n{exc}")

    def _on_apply(self) -> None:
        """Apply theme to application."""
        try:
            self.tm.apply_to_registered()
            self.themeApplied.emit(self.tm.colors)
            QMessageBox.information(self, "Theme", "Theme applied to application.")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Apply Failed", f"Failed to apply theme:\n{exc}")

    def _on_reset_defaults(self) -> None:
        """Reset to default theme."""
        try:
            self.tm.set_colors(self.defaults)
            self._sync_rows_from_theme()
            self.refresh_preview()
            QMessageBox.information(self, "Theme", "Reset to default theme.")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset theme:\n{exc}")

    def refresh_preview(self) -> None:
        """Re-process and set stylesheet on preview window."""
        try:
            self.tm.apply_stylesheet(self.preview)
        except Exception:
            pass

    def _sync_rows_from_theme(self) -> None:
        """Reset each ColorRow to reflect current ThemeManager values."""
        for row in self._rows.values():
            row.update_from_theme()

    def _on_filter_text_changed(self, text: str) -> None:
        """Filter rows by substring in variable name or label."""
        s = (text or "").strip().lower()
        for cat, group in self._category_groups.items():
            any_visible = False
            for var_name in self._category_items.get(cat, []):
                row = self._rows[var_name]
                target = f"{var_name} {pretty_label(var_name)}".lower()
                visible = (s in target) if s else True
                row.setVisible(visible)
                any_visible = any_visible or visible
            group.setVisible(any_visible)

    @classmethod
    def open_dialog(cls, parent: Optional[QWidget] = None) -> "ThemeManagerWidget":
        """Convenience helper to open as a dialog from main window menu."""
        dlg = cls(parent)
        dlg.setModal(True)
        dlg.exec()
        return dlg

    def closeEvent(self, event) -> None:
        """Cleanup preview on close."""
        try:
            if self.preview:
                self.preview.deleteLater()
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = ThemeManagerWidget()
    w.show()
    sys.exit(app.exec())
