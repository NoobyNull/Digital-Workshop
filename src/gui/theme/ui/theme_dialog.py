"""
Consolidated theme management dialog.

Provides a unified interface for:
- Selecting and applying presets
- Customizing individual colors
- Importing/exporting themes
- System theme detection settings

Single Responsibility: Unified theme management UI.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QPushButton, QComboBox, QColorDialog,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox
)
from PySide6.QtGui import QColor

from ..service import ThemeService
from ..manager import ThemeManager, qcolor


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
        self.manager = ThemeManager.instance()
        self.color_buttons = {}

        self.setWindowTitle("Theme Manager")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        try:
            self._setup_ui()
            self._load_current_theme()
        except Exception as e:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize ThemeDialog: {e}", exc_info=True)
            raise

    def _setup_ui(self) -> None:
        """Setup the UI with tabs."""
        layout = QVBoxLayout()

        # Create tab widget
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

        colors = self.manager.colors

        # Group colors by category (prefix)
        categories = {}
        for color_name in sorted(colors.keys()):
            prefix = color_name.split('_')[0]
            if prefix not in categories:
                categories[prefix] = []
            categories[prefix].append(color_name)

        # Create collapsible groups for each category
        from PySide6.QtWidgets import QGroupBox
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
        colors = self.manager.colors
        for color_name, hex_value in colors.items():
            if color_name in self.color_buttons:
                btn = self.color_buttons[color_name]
                qc = QColor(hex_value)
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
        current_color = QColor(self.manager.get_color(color_name))
        color = QColorDialog.getColor(current_color, self, f"Select {color_name}")

        if color.isValid():
            hex_value = color.name()
            self.service.set_color(color_name, hex_value)
            self.color_buttons[color_name].setStyleSheet(f"background-color: {hex_value};")
            self.theme_applied.emit("custom")

    def _on_export(self) -> None:
        """Export theme to file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Theme", "", "JSON Files (*.json)"
        )
        if path:
            try:
                self.service.export_theme(Path(path))
                QMessageBox.information(self, "Success", "Theme exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export theme: {e}")

    def _on_import(self) -> None:
        """Import theme from file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Theme", "", "JSON Files (*.json)"
        )
        if path:
            try:
                self.service.import_theme(Path(path))
                self._load_current_theme()
                QMessageBox.information(self, "Success", "Theme imported successfully")
                self.theme_applied.emit("custom")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import theme: {e}")

    def _on_reset(self) -> None:
        """Reset to default theme."""
        reply = QMessageBox.question(
            self, "Reset Theme", "Reset to default theme?",
            QMessageBox.Yes | QMessageBox.No
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

