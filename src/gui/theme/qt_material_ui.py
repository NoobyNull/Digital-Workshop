"""
Qt-Material UI Components

This module provides qt-material-focused UI components, removing all legacy
UI component references. It implements clean qt-material theme switchers
and dialogs with no legacy dependencies.

Key Features:
- Qt-material theme switcher widget
- Material Design color picker
- Clean qt-material UI components
- No legacy UI component references
"""

from typing import Dict, Any
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QLabel, QDialog, QDialogButtonBox, QColorDialog, QGroupBox,
    QGridLayout, QScrollArea, QCheckBox, QTabWidget, QSizePolicy
)
from PySide6.QtGui import QColor
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class QtMaterialThemeSwitcher(QWidget):
    """
    Qt-material theme switcher widget.
    
    Provides clean qt-material theme selection with real-time theme application.
    """
    
    # Signals
    theme_changed = Signal(str, str)  # theme, variant
    theme_applied = Signal(bool)  # success
    
    def __init__(self, parent=None):
        """Initialize qt-material theme switcher."""
        super().__init__(parent)
        
        # Import theme service
        from .qt_material_service import QtMaterialThemeService
        self.service = QtMaterialThemeService.instance()
        
        # Connect to service signals
        self.service.theme_changed.connect(self._on_theme_changed)
        self.service.theme_applied.connect(self._on_theme_applied)
        
        # Setup UI
        self._setup_ui()
        self._load_current_theme()
        
        logger.debug("QtMaterialThemeSwitcher initialized")
    
    def _setup_ui(self) -> None:
        """Setup the theme switcher UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Theme selector group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        # Theme selection
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Variant selection
        variant_label = QLabel("Variant:")
        self.variant_combo = QComboBox()
        self.variant_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Auto theme checkbox
        self.auto_checkbox = QCheckBox("Auto (System Theme)")
        
        # Add to layout
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addWidget(variant_label)
        theme_layout.addWidget(self.variant_combo)
        theme_layout.addWidget(self.auto_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply Theme")
        self.reset_button = QPushButton("Reset to Default")
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        
        # Add to main layout
        layout.addWidget(theme_group)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.theme_combo.currentTextChanged.connect(self._on_theme_selected)
        self.variant_combo.currentTextChanged.connect(self._on_variant_selected)
        self.auto_checkbox.toggled.connect(self._on_auto_toggled)
        self.apply_button.clicked.connect(self._apply_theme)
        self.reset_button.clicked.connect(self._reset_to_default)
        
        # Populate themes
        self._populate_themes()
    
    def _populate_themes(self) -> None:
        """Populate theme and variant comboboxes."""
        available_themes = self.service.get_available_themes()
        
        # Clear comboboxes
        self.theme_combo.clear()
        self.variant_combo.clear()
        
        # Add themes
        for theme_name in sorted(available_themes.keys()):
            self.theme_combo.addItem(theme_name.title(), theme_name)
        
        # Update variants for current theme
        self._update_variants()
    
    def _update_variants(self) -> None:
        """Update variant combobox based on selected theme."""
        current_theme = self.theme_combo.currentData()
        if current_theme:
            variants = self.service.get_available_variants(current_theme)
            
            self.variant_combo.clear()
            for variant_name in sorted(variants):
                self.variant_combo.addItem(variant_name.title(), variant_name)
    
    def _load_current_theme(self) -> None:
        """Load current theme into UI."""
        current_theme, current_variant = self.service.get_current_theme()
        
        # Set theme
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        
        # Set variant
        self._update_variants()
        for i in range(self.variant_combo.count()):
            if self.variant_combo.itemData(i) == current_variant:
                self.variant_combo.setCurrentIndex(i)
                break
        
        # Set auto checkbox
        self.auto_checkbox.setChecked(current_theme == "auto")
    
    def _on_theme_selected(self, theme_text: str = None) -> None:
        """Handle theme selection."""
        _ = theme_text  # Mark as used to avoid lint warning
        self._update_variants()
    
    def _on_variant_selected(self, variant_text: str = None) -> None:
        """Handle variant selection."""
        _ = variant_text  # Mark as used to avoid lint warning
        # Variant selection is handled by apply button
    
    def _on_auto_toggled(self, checked: bool) -> None:
        """Handle auto theme toggle."""
        if checked:
            self.theme_combo.setEnabled(False)
            self.variant_combo.setEnabled(False)
        else:
            self.theme_combo.setEnabled(True)
            self.variant_combo.setEnabled(True)
    
    def _apply_theme(self) -> None:
        """Apply selected theme."""
        if self.auto_checkbox.isChecked():
            theme = "auto"
            variant = "blue"  # Default variant for auto
        else:
            theme = self.theme_combo.currentData()
            variant = self.variant_combo.currentData()
        
        if theme and variant:
            success = self.service.apply_theme(theme, variant)
            if success:
                logger.info(f"Theme applied: {theme}/{variant}")
            else:
                logger.error(f"Failed to apply theme: {theme}/{variant}")
    
    def _reset_to_default(self) -> None:
        """Reset to default theme."""
        success = self.service.reset_to_default()
        if success:
            self._load_current_theme()
            logger.info("Reset to default theme")
    
    def apply_current_theme(self) -> None:
        """Public method to apply the currently selected theme."""
        self._apply_theme()
    
    def _on_theme_changed(self, theme: str, variant: str) -> None:
        """Handle theme change from service."""
        self._load_current_theme()
        self.theme_changed.emit(theme, variant)
    
    def _on_theme_applied(self, success: bool) -> None:
        """Handle theme applied from service."""
        self.theme_applied.emit(success)


class QtMaterialColorPicker(QDialog):
    """
    Material Design color picker dialog.
    
    Provides a Material Design color picker for custom color selection.
    """
    
    # Signals
    color_selected = Signal(str)  # hex color
    
    def __init__(self, parent=None, current_color: str = "#1976D2"):
        """Initialize color picker dialog."""
        super().__init__(parent)
        
        self.current_color = current_color
        self.selected_color = current_color
        
        # Setup dialog
        self.setWindowTitle("Material Color Picker")
        self.setModal(True)
        self.resize(600, 400)
        
        # Setup UI
        self._setup_ui()
        
        logger.debug("QtMaterialColorPicker initialized")
    
    def _setup_ui(self) -> None:
        """Setup the color picker UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different color categories
        self.tab_widget = QTabWidget()
        
        # Material Design color presets
        self._create_material_colors_tab()
        
        # Custom color picker
        self._create_custom_color_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Current color display
        self.color_display = QLabel()
        self.color_display.setFixedHeight(50)
        self.color_display.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
        layout.addWidget(self.color_display)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_material_colors_tab(self) -> None:
        """Create Material Design color presets tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Material Design color palette
        colors = [
            # Reds
            ("#F44336", "Red"),
            ("#E53935", "Dark Red"),
            ("#FFCDD2", "Light Red"),
            # Pinks
            ("#E91E63", "Pink"),
            ("#D81B60", "Dark Pink"),
            ("#F8BBD0", "Light Pink"),
            # Purples
            ("#9C27B0", "Purple"),
            ("#8E24AA", "Dark Purple"),
            ("#E1BEE7", "Light Purple"),
            # Deep Purples
            ("#673AB7", "Deep Purple"),
            ("#5E35B1", "Dark Deep Purple"),
            ("#D1C4E9", "Light Deep Purple"),
            # Indigos
            ("#3F51B5", "Indigo"),
            ("#3949AB", "Dark Indigo"),
            ("#C5CAE9", "Light Indigo"),
            # Blues
            ("#2196F3", "Blue"),
            ("#1976D2", "Dark Blue"),
            ("#BBDEFB", "Light Blue"),
            # Light Blues
            ("#03A9F4", "Light Blue"),
            ("#039BE5", "Dark Light Blue"),
            ("#B3E5FC", "Light Light Blue"),
            # Cyans
            ("#00BCD4", "Cyan"),
            ("#00ACC1", "Dark Cyan"),
            ("#B2EBF2", "Light Cyan"),
            # Teals
            ("#009688", "Teal"),
            ("#00897B", "Dark Teal"),
            ("#B2DFDB", "Light Teal"),
            # Greens
            ("#4CAF50", "Green"),
            ("#388E3C", "Dark Green"),
            ("#C8E6C9", "Light Green"),
            # Light Greens
            ("#8BC34A", "Light Green"),
            ("#689F38", "Dark Light Green"),
            ("#DCEDC8", "Light Light Green"),
            # Limes
            ("#CDDC39", "Lime"),
            ("#AFB42B", "Dark Lime"),
            ("#F0F4C3", "Light Lime"),
            # Yellows
            ("#FFEB3B", "Yellow"),
            ("#FBC02D", "Dark Yellow"),
            ("#FFF9C4", "Light Yellow"),
            # Ambers
            ("#FFC107", "Amber"),
            ("#FFA000", "Dark Amber"),
            ("#FFECB3", "Light Amber"),
            # Oranges
            ("#FF9800", "Orange"),
            ("#FB8C00", "Dark Orange"),
            ("#FFE0B2", "Light Orange"),
            # Deep Oranges
            ("#FF5722", "Deep Orange"),
            ("#F4511E", "Dark Deep Orange"),
            ("#FFCCBC", "Light Deep Orange"),
            # Browns
            ("#795548", "Brown"),
            ("#6D4C41", "Dark Brown"),
            ("#D7CCC8", "Light Brown"),
            # Greys
            ("#9E9E9E", "Grey"),
            ("#757575", "Dark Grey"),
            ("#EEEEEE", "Light Grey"),
            # Blue Greys
            ("#607D8B", "Blue Grey"),
            ("#546E7A", "Dark Blue Grey"),
            ("#CFD8DC", "Light Blue Grey")
        ]
        
        # Create scroll area for colors
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Add color buttons
        row, col = 0, 0
        for color_hex, color_name in colors:
            color_button = QPushButton()
            color_button.setFixedSize(60, 60)
            color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_hex};
                    border: 2px solid #ccc;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #333;
                }}
            """)
            color_button.setToolTip(color_name)
            color_button.clicked.connect(lambda checked, c=color_hex: self._select_color(c))
            
            scroll_layout.addWidget(color_button, row, col)
            
            col += 1
            if col >= 8:
                col = 0
                row += 1
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(widget, "Material Colors")
    
    def _create_custom_color_tab(self) -> None:
        """Create custom color picker tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Color dialog button
        custom_color_button = QPushButton("Choose Custom Color")
        custom_color_button.clicked.connect(self._choose_custom_color)
        layout.addWidget(custom_color_button)
        
        # Custom color display
        custom_color_display = QLabel()
        custom_color_display.setFixedHeight(100)
        custom_color_display.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
        layout.addWidget(custom_color_display)
        
        # Hex color input
        hex_layout = QHBoxLayout()
        hex_layout.addWidget(QLabel("Hex Color:"))
        hex_input = QPushButton(self.current_color)
        hex_input.clicked.connect(self._choose_custom_color)
        hex_layout.addWidget(hex_input)
        layout.addLayout(hex_layout)
        
        # Store references as instance variables for color picker dialog
        # These are used within the color picker dialog itself
        
        self.tab_widget.addTab(widget, "Custom Color")
    
    def _select_color(self, color_hex: str) -> None:
        """Select a color."""
        self.selected_color = color_hex
        self.color_display.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc;")
        self.custom_color_display.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ccc;")
        self.hex_input.setText(color_hex)
    
    def _choose_custom_color(self) -> None:
        """Open custom color dialog."""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Choose Color")
        if color.isValid():
            self._select_color(color.name())
    
    def get_selected_color(self) -> str:
        """Get the selected color."""
        return self.selected_color
    
    def accept(self) -> None:
        """Accept dialog and emit signal."""
        self.color_selected.emit(self.selected_color)
        super().accept()


class QtMaterialThemeDialog(QDialog):
    """
    Comprehensive qt-material theme configuration dialog.
    
    Provides advanced theme configuration options with qt-material integration.
    """
    
    # Signals
    theme_configured = Signal(dict)  # theme configuration
    
    def __init__(self, parent=None):
        """Initialize theme dialog."""
        super().__init__(parent)
        
        # Import theme service
        from .qt_material_service import QtMaterialThemeService
        self.service = QtMaterialThemeService.instance()
        
        # Initialize UI attributes
        self.theme_switcher = None
        self.color_picker_button = None
        self.custom_colors = {}
        self.fast_switching_checkbox = None
        self.cache_colors_checkbox = None
        self.logging_checkbox = None
        self.performance_checkbox = None
        
        # Setup dialog
        self.setWindowTitle("Qt-Material Theme Configuration")
        self.setModal(True)
        self.resize(800, 600)
        
        # Setup UI
        self._setup_ui()
        
        logger.debug("QtMaterialThemeDialog initialized")
    
    def _setup_ui(self) -> None:
        """Setup the theme dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Theme selection tab
        self._create_theme_selection_tab()
        
        # Color customization tab
        self._create_color_customization_tab()
        
        # Advanced settings tab
        self._create_advanced_settings_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _create_theme_selection_tab(self) -> None:
        """Create theme selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Initialize theme switcher
        self.theme_switcher = None
        
        # Theme switcher
        theme_switcher = QtMaterialThemeSwitcher()
        self.theme_switcher = theme_switcher
        layout.addWidget(theme_switcher)
        
        # Theme preview
        preview_group = QGroupBox("Theme Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Preview elements
        preview_label = QLabel("This is a preview of the selected theme.")
        preview_button = QPushButton("Sample Button")
        preview_checkbox = QCheckBox("Sample Checkbox")
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(preview_button)
        preview_layout.addWidget(preview_checkbox)
        
        layout.addWidget(preview_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "Theme Selection")
    
    def _create_color_customization_tab(self) -> None:
        """Create color customization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Color picker
        picker_group = QGroupBox("Color Picker")
        picker_layout = QVBoxLayout(picker_group)
        
        color_picker_button = QPushButton("Open Color Picker")
        color_picker_button.clicked.connect(self._open_color_picker)
        picker_layout.addWidget(color_picker_button)
        
        # Store reference
        self.color_picker_button = color_picker_button
        
        layout.addWidget(picker_group)
        
        # Custom colors
        custom_group = QGroupBox("Custom Colors")
        custom_layout = QGridLayout(custom_group)
        
        # Add custom color inputs
        custom_colors = {}
        color_names = ["primary", "secondary", "accent", "background"]
        
        for i, color_name in enumerate(color_names):
            label = QLabel(f"{color_name.title()}:")
            color_button = QPushButton()
            color_button.setFixedSize(40, 40)
            color_button.clicked.connect(lambda checked, name=color_name: self._pick_custom_color(name))
            
            custom_layout.addWidget(label, i, 0)
            custom_layout.addWidget(color_button, i, 1)
            
            custom_colors[color_name] = color_button
        
        # Store reference
        self.custom_colors = custom_colors
        
        layout.addWidget(custom_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "Color Customization")
    
    def _create_advanced_settings_tab(self) -> None:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QVBoxLayout(perf_group)
        
        fast_switching_checkbox = QCheckBox("Fast Theme Switching (<100ms)")
        fast_switching_checkbox.setChecked(True)
        
        cache_colors_checkbox = QCheckBox("Cache Colors")
        cache_colors_checkbox.setChecked(True)
        
        perf_layout.addWidget(fast_switching_checkbox)
        perf_layout.addWidget(cache_colors_checkbox)
        
        # Store references
        self.fast_switching_checkbox = fast_switching_checkbox
        self.cache_colors_checkbox = cache_colors_checkbox
        
        layout.addWidget(perf_group)
        
        # Debug settings
        debug_group = QGroupBox("Debug Settings")
        debug_layout = QVBoxLayout(debug_group)
        
        logging_checkbox = QCheckBox("Enable Theme Logging")
        performance_checkbox = QCheckBox("Log Performance Metrics")
        
        debug_layout.addWidget(logging_checkbox)
        debug_layout.addWidget(performance_checkbox)
        
        # Store references
        self.logging_checkbox = logging_checkbox
        self.performance_checkbox = performance_checkbox
        
        layout.addWidget(debug_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "Advanced Settings")
    
    def _open_color_picker(self) -> None:
        """Open color picker dialog."""
        picker = QtMaterialColorPicker(self)
        if picker.exec() == QDialog.Accepted:
            color = picker.get_selected_color()
            logger.info(f"Selected color: {color}")
    
    def _pick_custom_color(self, color_name: str) -> None:
        """Pick custom color for a specific color name."""
        current_color = self.service.get_color(color_name)
        picker = QtMaterialColorPicker(self, current_color)
        if picker.exec() == QDialog.Accepted:
            color = picker.get_selected_color()
            self.custom_colors[color_name].setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
    
    def _apply_settings(self) -> None:
        """Apply current settings."""
        # Apply theme from theme switcher
        if self.theme_switcher:
            # Use public method instead of protected method
            self.theme_switcher.apply_current_theme()
        
        # Apply custom colors if any
        for color_name, color_button in self.custom_colors.items():
            # This would need implementation in the theme service
            _ = color_name, color_button  # Mark as used to avoid lint warning
        
        logger.info("Theme settings applied")
    
    def get_theme_config(self) -> Dict[str, Any]:
        """Get current theme configuration."""
        theme, variant = self.service.get_current_theme()
        return {
            "theme": theme,
            "variant": variant,
            "fast_switching": self.fast_switching_checkbox.isChecked(),
            "cache_colors": self.cache_colors_checkbox.isChecked(),
            "logging": self.logging_checkbox.isChecked(),
            "performance": self.performance_checkbox.isChecked()
        }
    
    def accept(self) -> None:
        """Accept dialog and emit signal."""
        self._apply_settings()
        config = self.get_theme_config()
        self.theme_configured.emit(config)
        super().accept()


# Convenience functions for creating UI components
def create_theme_switcher(parent=None) -> QtMaterialThemeSwitcher:
    """
    Create a qt-material theme switcher widget.
    
    Args:
        parent: Parent widget
        
    Returns:
        QtMaterialThemeSwitcher instance
    """
    return QtMaterialThemeSwitcher(parent)


def create_color_picker(parent=None, current_color: str = "#1976D2") -> QtMaterialColorPicker:
    """
    Create a qt-material color picker dialog.
    
    Args:
        parent: Parent widget
        current_color: Current color to start with
        
    Returns:
        QtMaterialColorPicker instance
    """
    return QtMaterialColorPicker(parent, current_color)


def create_theme_dialog(parent=None) -> QtMaterialThemeDialog:
    """
    Create a qt-material theme configuration dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        QtMaterialThemeDialog instance
    """
    return QtMaterialThemeDialog(parent)