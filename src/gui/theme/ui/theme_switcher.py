"""
Theme switcher widget for toolbar.

Provides a dropdown combobox for quick theme selection.

Single Responsibility: Quick theme switching via dropdown.
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QWidget

from ..service import ThemeService


class ThemeSwitcher(QComboBox):
    """
    Quick theme selector dropdown for toolbar.

    Displays available presets and allows one-click theme switching.

    Signals:
        theme_changed(str): Emitted when theme is changed with preset name
    """

    theme_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
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
