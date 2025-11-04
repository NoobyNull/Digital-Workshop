"""
Simple theme switcher widget for toolbar.

Single Responsibility: Provide quick theme switching UI.
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from ..simple_service import ThemeService


class SimpleThemeSwitcher(QWidget):
    """Simple theme switcher for toolbar."""

    theme_changed = Signal(str)  # Emitted when theme changes

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
            from .qt_material_color_picker import QtMaterialColorPicker

            dialog = QtMaterialColorPicker(self)
            dialog.exec()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            print(f"Error opening color picker: {e}")
