"""
Consolidated theme UI components for Digital Workshop.

This module consolidates UI-related theme components from:
- ui/theme_switcher.py - Quick theme selection dropdown
- ui/simple_theme_switcher.py - Simplified theme switcher
- ui/qt_material_color_picker.py - Material Design color picker
- ui/theme_dialog.py - Consolidated theme editor

Single Responsibility: Theme-related UI components with qt-material focus.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .theme_service import ThemeService

logger = logging.getLogger(__name__)


class ThemeSwitcher(QComboBox):
    """
    Quick theme selector dropdown for toolbar.

    Displays available presets and allows one-click theme switching.

    Signals:
        theme_changed(str): Emitted when theme is changed with preset name
    """

    theme_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the theme switcher.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.service = ThemeService.instance()
        self._setup_ui()
        self._populate_presets()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI."""
        self.setToolTip("Select a theme")
        self.setMaximumWidth(150)

    def _populate_presets(self) -> None:
        """Populate the dropdown with available presets."""
        presets = self.service.get_available_presets()

        for preset in presets:
            # Convert preset name to display name (e.g., "solarized_light" -> "Solarized Light")
            display_name = preset.replace("_", " ").title()
            self.addItem(display_name, preset)

        # Set current preset
        current = self.service.get_current_preset()
        index = self.findData(current)
        if index >= 0:
            self.setCurrentIndex(index)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self.currentIndexChanged.connect(self._on_theme_selected)

    def _on_theme_selected(self, index: int) -> None:
        """
        Handle theme selection.

        Args:
            index: Index of selected item
        """
        if index < 0:
            return

        preset_name = self.itemData(index)
        if preset_name:
            try:
                self.service.apply_preset(preset_name)
                self.theme_changed.emit(preset_name)
            except Exception:
                # Revert to previous selection on error
                current = self.service.get_current_preset()
                index = self.findData(current)
                if index >= 0:
                    self.blockSignals(True)
                    self.setCurrentIndex(index)
                    self.blockSignals(False)

    def set_theme(self, preset_name: str) -> None:
        """
        Set the theme programmatically.

        Args:
            preset_name: Name of preset to apply
        """
        index = self.findData(preset_name)
        if index >= 0:
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)
            self.service.apply_preset(preset_name)
            self.theme_changed.emit(preset_name)

    def refresh(self) -> None:
        """Refresh the dropdown to reflect current theme."""
        current = self.service.get_current_preset()
        index = self.findData(current)
        if index >= 0:
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)


class SimpleThemeSwitcher(QWidget):
    """Simple theme switcher for toolbar with qt-material focus."""

    theme_changed = Signal(str)  # Emitted when theme changes

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize theme switcher.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.service = ThemeService.instance()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)

        # Label
        label = QLabel("Theme:")
        layout.addWidget(label)

        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        layout.addWidget(self.theme_combo)

        # Qt-Material variant selector
        self.variant_combo = QComboBox()
        self._populate_variants()
        self.variant_combo.currentTextChanged.connect(self._on_variant_changed)
        layout.addWidget(self.variant_combo)

        # Color picker button
        self.color_picker_btn = QPushButton("🎨")
        self.color_picker_btn.setMaximumWidth(40)
        self.color_picker_btn.setToolTip("View Material Design colors")
        self.color_picker_btn.clicked.connect(self._on_show_colors)
        layout.addWidget(self.color_picker_btn)

        self.setLayout(layout)

    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change."""
        theme = theme_name.lower()
        self.service.apply_theme(theme, "qt-material")
        self.theme_changed.emit(theme)

    def _on_variant_changed(self, variant_name: str) -> None:
        """Handle qt-material variant change."""
        if not variant_name:
            return

        # Extract the base variant name (e.g., "blue" from "dark_blue")
        variant = variant_name.split("_")[-1]
        self.service.set_qt_material_variant(variant)

        # Reapply theme with new variant
        theme = self.theme_combo.currentText().lower()
        self.service.apply_theme(theme, "qt-material")

    def _populate_variants(self) -> None:
        """Populate variant combo with available qt-material variants."""
        self.variant_combo.blockSignals(True)
        self.variant_combo.clear()

        # Get dark variants by default
        variants = self.service.get_qt_material_variants("dark")
        self.variant_combo.addItems(variants)

        self.variant_combo.blockSignals(False)

    def set_theme(self, theme: str) -> None:
        """Set theme without triggering signal."""
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme.capitalize())
        self.theme_combo.blockSignals(False)

    def _on_show_colors(self) -> None:
        """Show the Material Design color picker dialog."""
        try:
            dialog = QtMaterialColorPicker(self)
            dialog.exec()
        except Exception as e:
            logger.error("Error opening color picker: %s", e)


class QtMaterialColorPicker(QDialog):
    """
    Dialog showing Material Design colors from qt-material theme.

    Displays color swatches for:
    - Primary colors (primaryColor, primaryLightColor, primaryDarkColor)
    - Secondary colors (secondaryColor, secondaryLightColor, secondaryDarkColor)
    - Text colors (primaryTextColor, secondaryTextColor)
    """

    theme_changed = Signal(str)  # Emitted when theme variant is changed

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the color picker dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Material Design Colors")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        self.color_swatches: Dict[str, QPushButton] = {}
        self._setup_ui()
        self._load_colors()

    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Material Design Theme Colors")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Theme variant selector
        variant_layout = QHBoxLayout()
        variant_layout.addWidget(QLabel("Theme Variant:"))

        self.variant_combo = QComboBox()
        self._populate_variants()
        self.variant_combo.currentTextChanged.connect(self._on_variant_changed)
        variant_layout.addWidget(self.variant_combo)
        variant_layout.addStretch()
        layout.addLayout(variant_layout)

        # Color swatches in scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        color_widget = QWidget()
        color_layout = QVBoxLayout()

        # Define color groups
        self.color_groups = {
            "Primary Colors": [
                "primaryColor",
                "primaryLightColor",
                "primaryDarkColor",
            ],
            "Secondary Colors": [
                "secondaryColor",
                "secondaryLightColor",
                "secondaryDarkColor",
            ],
            "Text Colors": [
                "primaryTextColor",
                "secondaryTextColor",
            ],
        }

        # Create color swatches for each group
        for group_name, colors in self.color_groups.items():
            group_label = QLabel(group_name)
            group_font = QFont()
            group_font.setBold(True)
            group_label.setFont(group_font)
            color_layout.addWidget(group_label)

            # Create grid for colors in this group
            from PySide6.QtWidgets import QGridLayout

            grid = QGridLayout()
            for i, color_name in enumerate(colors):
                # Color swatch button
                swatch = QPushButton()
                swatch.setMinimumHeight(50)
                swatch.setMinimumWidth(200)
                self.color_swatches[color_name] = swatch

                # Label with color name
                label = QLabel(color_name)
                label.setMinimumWidth(150)

                grid.addWidget(label, i, 0)
                grid.addWidget(swatch, i, 1)

            color_layout.addLayout(grid)
            color_layout.addSpacing(10)

        color_layout.addStretch()
        color_widget.setLayout(color_layout)
        scroll.setWidget(color_widget)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _populate_variants(self) -> None:
        """Populate the variant combo box with available qt-material variants."""
        try:
            service = ThemeService.instance()

            # Get current theme type
            theme_type, _ = service.get_current_theme()
            current_variant = service.settings.value("qt_material_variant", "blue")

            # Get available variants
            variants = service.get_qt_material_variants(theme_type)

            for variant in variants:
                # Extract color name from variant (e.g., "dark_blue" -> "blue")
                color_name = variant.split("_", 1)[1] if "_" in variant else variant
                self.variant_combo.addItem(color_name.title(), variant)

            # Set current variant
            index = self.variant_combo.findData(current_variant)
            if index >= 0:
                self.variant_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error("Error populating variants: %s", e)

    def _load_colors(self) -> None:
        """Load and display colors from current qt-material theme."""
        try:
            # Get colors from environment (set by qt-material)
            colors = {
                "primaryColor": os.environ.get("QTMATERIAL_PRIMARYCOLOR", "#2196F3"),
                "primaryLightColor": os.environ.get("QTMATERIAL_PRIMARYLIGHTCOLOR", "#BBDEFB"),
                "primaryDarkColor": os.environ.get("QTMATERIAL_PRIMARYDARKCOLOR", "#1976D2"),
                "secondaryColor": os.environ.get("QTMATERIAL_SECONDARYCOLOR", "#FFC107"),
                "secondaryLightColor": os.environ.get("QTMATERIAL_SECONDARYLIGHTCOLOR", "#FFE082"),
                "secondaryDarkColor": os.environ.get("QTMATERIAL_SECONDARYDARKCOLOR", "#FFA000"),
                "primaryTextColor": os.environ.get("QTMATERIAL_PRIMARYTEXTCOLOR", "#212121"),
                "secondaryTextColor": os.environ.get("QTMATERIAL_SECONDARYTEXTCOLOR", "#757575"),
            }

            # Update swatches
            for color_name, hex_color in colors.items():
                if color_name in self.color_swatches:
                    swatch = self.color_swatches[color_name]

                    # Set background color
                    swatch.setStyleSheet(
                        f"""
                        QPushButton {{
                            background-color: {hex_color};
                            border: 1px solid #cccccc;
                            border-radius: 4px;
                            color: {self._get_text_color(hex_color)};
                            font-weight: bold;
                        }}
                        QPushButton:hover {{
                            border: 2px solid #999999;
                        }}
                    """
                    )

                    # Set button text to hex value
                    swatch.setText(hex_color.upper())
        except Exception as e:
            logger.error("Error loading colors: %s", e)

    def _get_text_color(self, bg_hex: str) -> str:
        """
        Determine if text should be white or black based on background color.

        Args:
            bg_hex: Background color in hex format

        Returns:
            "#ffffff" for white text, "#000000" for black text
        """
        try:
            color = QColor(bg_hex)
            # Calculate luminance
            r, g, b = color.red(), color.green(), color.blue()
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#ffffff"
        except Exception:
            return "#000000"

    def _on_variant_changed(self, variant_name: str) -> None:
        """
        Handle theme variant change.

        Args:
            variant_name: Selected variant name
        """
        try:
            service = ThemeService.instance()

            # Get the full variant name (e.g., "blue" -> "dark_blue" or "light_blue")
            current_theme, _ = service.get_current_theme()
            theme_prefix = "dark" if current_theme == "dark" else "light"
            full_variant = f"{theme_prefix}_{variant_name.lower()}"

            # Set the variant and apply theme
            service.set_qt_material_variant(variant_name.lower())
            service.apply_theme(current_theme, "qt-material")

            # Reload colors
            self._load_colors()
            self.theme_changed.emit(full_variant)
        except Exception as e:
            logger.error("Error changing variant: %s", e)


class ThemeDialog(QDialog):
    """
    Consolidated theme management dialog.

    Provides tabs for:
    - Preset selection
    - Color customization
    - Import/export
    - System detection settings
    """

    theme_applied = Signal(str)  # Emitted when theme is applied

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the theme dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.service = ThemeService.instance()
        self.manager = self.service.get_manager()
        self.color_buttons = {}

        # Initialize UI attributes
        self.preset_combo = None
        self.status_label = None
        self.system_theme_label = None
        self.system_detection_btn = None

        self.setWindowTitle("Theme Manager")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        try:
            self._setup_ui()
            self._load_current_theme()
        except Exception as e:
            logger.error("Failed to initialize ThemeDialog: %s", e, exc_info=True)
            raise

    def _setup_ui(self) -> None:
        """Setup the UI with tabs."""
        layout = QVBoxLayout()

        # Create tab widget
        from PySide6.QtWidgets import QTabWidget

        tabs = QTabWidget()

        # Tab 1: Presets
        tabs.addTab(self._create_presets_tab(), "Presets")

        # Tab 2: Colors
        tabs.addTab(self._create_colors_tab(), "Colors")

        # Tab 3: Import/Export
        tabs.addTab(self._create_import_export_tab(), "Import/Export")

        # Tab 4: System Detection
        tabs.addTab(self._create_system_detection_tab(), "System")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_presets_tab(self) -> QWidget:
        """Create the presets tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Available Presets:"))

        # Preset selector
        self.preset_combo = QComboBox()
        presets = self.service.get_available_presets()
        for preset in presets:
            display_name = preset.replace("_", " ").title()
            self.preset_combo.addItem(display_name, preset)

        layout.addWidget(self.preset_combo)

        # Apply button
        apply_btn = QPushButton("Apply Preset")
        apply_btn.clicked.connect(self._on_apply_preset)
        layout.addWidget(apply_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_colors_tab(self) -> QWidget:
        """Create the colors customization tab with grouped colors."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Customize Colors (grouped by category):"))

        # Scrollable color grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        color_widget = QWidget()
        color_layout = QVBoxLayout()

        if self.manager:
            colors = self.manager.colors

            # Group colors by category (prefix)
            categories = {}
            for color_name in sorted(colors.keys()):
                prefix = color_name.split("_")[0]
                if prefix not in categories:
                    categories[prefix] = []
                categories[prefix].append(color_name)

            # Create collapsible groups for each category
            for category in sorted(categories.keys()):
                group = QGroupBox(category.replace("_", " ").title())
                group_layout = QGridLayout()

                col = 0
                for color_name in sorted(categories[category]):
                    # Label
                    label = QLabel(color_name.replace(f"{category}_", "").replace("_", " ").title())
                    group_layout.addWidget(label, col // 2, (col % 2) * 2)

                    # Color button
                    btn = QPushButton()
                    btn.setMaximumWidth(80)
                    btn.clicked.connect(lambda checked, cn=color_name: self._on_color_clicked(cn))
                    self.color_buttons[color_name] = btn
                    group_layout.addWidget(btn, col // 2, (col % 2) * 2 + 1)

                    col += 1

                group.setLayout(group_layout)
                color_layout.addWidget(group)

        color_layout.addStretch()
        color_widget.setLayout(color_layout)
        scroll.setWidget(color_widget)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def _create_import_export_tab(self) -> QWidget:
        """Create the import/export tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Theme Files:"))

        export_btn = QPushButton("Export Theme...")
        export_btn.clicked.connect(self._on_export)
        layout.addWidget(export_btn)

        import_btn = QPushButton("Import Theme...")
        import_btn.clicked.connect(self._on_import)
        layout.addWidget(import_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_system_detection_tab(self) -> QWidget:
        """Create the system detection tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("System Theme Detection:"))

        # Status
        is_enabled = self.service.is_system_detection_enabled()
        status_text = "Enabled" if is_enabled else "Disabled"
        self.status_label = QLabel(f"Status: {status_text}")
        layout.addWidget(self.status_label)

        # Current system theme
        system_theme = self.service.get_system_theme()
        self.system_theme_label = QLabel(f"System Theme: {system_theme.title()}")
        layout.addWidget(self.system_theme_label)

        # Toggle button
        self.system_detection_btn = QPushButton(
            "Disable System Detection" if is_enabled else "Enable System Detection"
        )
        self.system_detection_btn.clicked.connect(self._on_toggle_system_detection)
        layout.addWidget(self.system_detection_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _load_current_theme(self) -> None:
        """Load and display current theme colors."""
        if self.manager:
            colors = self.manager.colors
            for color_name, hex_value in colors.items():
                if color_name in self.color_buttons:
                    btn = self.color_buttons[color_name]
                    btn.setStyleSheet(f"background-color: {hex_value};")

    def _on_apply_preset(self) -> None:
        """Apply selected preset."""
        preset_name = self.preset_combo.currentData()
        if preset_name:
            self.service.apply_preset(preset_name)
            self._load_current_theme()
            self.theme_applied.emit(preset_name)

    def _on_color_clicked(self, color_name: str) -> None:
        """Handle color button click."""
        if self.manager:
            current_color = QColor(self.manager.get_color(color_name))
            from PySide6.QtWidgets import QColorDialog

            color = QColorDialog.getColor(current_color, self, f"Select {color_name}")

            if color.isValid():
                hex_value = color.name()
                self.service.set_color(color_name, hex_value)
                self.color_buttons[color_name].setStyleSheet(f"background-color: {hex_value};")
                self.theme_applied.emit("custom")

    def _on_export(self) -> None:
        """Export theme to file."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Theme", "", "JSON Files (*.json)")
        if path:
            try:
                self.service.export_theme(Path(path))
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(self, "Success", "Theme exported successfully")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(self, "Error", f"Failed to export theme: {e}")

    def _on_import(self) -> None:
        """Import theme from file."""
        path, _ = QFileDialog.getOpenFileName(self, "Import Theme", "", "JSON Files (*.json)")
        if path:
            try:
                self.service.import_theme(Path(path))
                self._load_current_theme()
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(self, "Success", "Theme imported successfully")
                self.theme_applied.emit("custom")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(self, "Error", f"Failed to import theme: {e}")

    def _on_reset(self) -> None:
        """Reset to default theme."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Reset Theme",
            "Reset to default theme?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.service.reset_to_default()
            self._load_current_theme()
            self.preset_combo.setCurrentIndex(0)
            self.theme_applied.emit("light")

    def _on_toggle_system_detection(self) -> None:
        """Toggle system theme detection."""
        if self.service.is_system_detection_enabled():
            self.service.disable_system_detection()
            self.system_detection_btn.setText("Enable System Detection")
            self.status_label.setText("Status: Disabled")
        else:
            self.service.enable_system_detection()
            self.system_detection_btn.setText("Disable System Detection")
            self.status_label.setText("Status: Enabled")
