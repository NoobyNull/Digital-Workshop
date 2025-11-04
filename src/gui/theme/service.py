"""
Unified theme service for Digital Workshop.

Provides a single API for all theme operations:
- Apply presets
- Set individual colors
- Save/load themes
- Import/export themes
- System theme detection

Single Responsibility: Orchestrate theme operations via unified API.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .detector import SystemThemeDetector
from .persistence import ThemePersistence
from .presets import get_preset, list_presets

logger = logging.getLogger(__name__)


class ThemeService:
    """
    Unified theme service providing a single API for all theme operations.

    This service orchestrates:
    - ThemeManager (existing, handles color management)
    - ThemePresets (preset definitions)
    - SystemThemeDetector (OS theme detection)
    - ThemePersistence (save/load/import/export)
    """

    _instance: Optional["ThemeService"] = None

    def __init__(self):
        """Initialize the theme service."""
        self._logger = logging.getLogger(__name__)
        self._detector = SystemThemeDetector()
        self._persistence = ThemePersistence()
        self._auto_save_enabled = True
        self._current_preset = "light"

        # Import ThemeManager here to avoid circular imports
        from .manager import ThemeManager

        self._manager = ThemeManager.instance()

        self._logger.info("ThemeService initialized")

    @classmethod
    def instance(cls) -> "ThemeService":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ============================================================
    # Preset Management
    # ============================================================

    def apply_preset(self, name: str) -> None:
        """
        Apply a theme preset by name.

        Args:
            name: Preset name (light, dark, high_contrast, solarized_light, solarized_dark)
        """
        try:
            preset = get_preset(name)
            self._manager.set_colors(preset)
            self._current_preset = name
            self._logger.info("Applied preset: %s", name)

            if self._auto_save_enabled:
                self.save_theme()
        except Exception as e:
            self._logger.error("Failed to apply preset %s: {e}", name)
            raise

    def get_available_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list_presets()

    def get_current_preset(self) -> str:
        """Get the name of the currently applied preset."""
        return self._current_preset

    # ============================================================
    # Color Management
    # ============================================================

    def set_color(self, name: str, value: str) -> None:
        """
        Set a single color variable.

        Args:
            name: Color variable name
            value: Hex color value
        """
        try:
            self._manager.set_colors({name: value})
            self._current_preset = "custom"
            self._logger.debug("Set color %s = {value}", name)

            if self._auto_save_enabled:
                self.save_theme()
        except Exception as e:
            self._logger.error("Failed to set color %s: {e}", name)
            raise

    def get_color(self, name: str) -> str:
        """
        Get a color value by name.

        Args:
            name: Color variable name

        Returns:
            Hex color value
        """
        return self._manager.get_color(name)

    def get_all_colors(self) -> Dict[str, str]:
        """Get all current color values."""
        return self._manager.colors.copy()

    # ============================================================
    # Persistence
    # ============================================================

    def save_theme(self) -> None:
        """Save current theme to AppData."""
        try:
            self._persistence.save_theme(self._manager.colors)
            self._logger.info("Theme saved")
        except Exception as e:
            self._logger.error("Failed to save theme: %s", e)

    def load_theme(self) -> bool:
        """
        Load theme from AppData.

        Returns:
            True if theme was loaded, False if no saved theme exists
        """
        try:
            colors = self._persistence.load_theme()
            if colors:
                self._manager.set_colors(colors)
                self._current_preset = "custom"
                self._logger.info("Theme loaded from AppData")
                return True
            return False
        except Exception as e:
            self._logger.error("Failed to load theme: %s", e)
            return False

    def export_theme(self, path: Path) -> None:
        """
        Export current theme to a JSON file.

        Args:
            path: Path to export to
        """
        try:
            self._persistence.export_theme(path, self._manager.colors)
            self._logger.info("Theme exported to %s", path)
        except Exception as e:
            self._logger.error("Failed to export theme: %s", e)
            raise

    def import_theme(self, path: Path) -> None:
        """
        Import theme from a JSON file.

        Args:
            path: Path to import from
        """
        try:
            colors = self._persistence.import_theme(path)
            if colors:
                self._manager.set_colors(colors)
                self._current_preset = "custom"
                self._logger.info("Theme imported from %s", path)
        except Exception as e:
            self._logger.error("Failed to import theme: %s", e)
            raise

    # ============================================================
    # System Theme Detection
    # ============================================================

    def enable_system_detection(self) -> None:
        """Enable automatic system theme detection."""
        self._detector.enable()
        mode = self._detector.get_current_mode()
        preset = "dark" if mode == "dark" else "light"
        self.apply_preset(preset)
        self._logger.info("System theme detection enabled, applied %s theme", preset)

    def disable_system_detection(self) -> None:
        """Disable system theme detection."""
        self._detector.disable()
        self._logger.info("System theme detection disabled")

    def is_system_detection_enabled(self) -> bool:
        """Check if system theme detection is enabled."""
        return self._detector.is_enabled()

    def get_system_theme(self) -> str:
        """Get the current system theme (light or dark)."""
        return self._detector.get_current_mode()

    # ============================================================
    # Auto-Save
    # ============================================================

    def enable_auto_save(self) -> None:
        """Enable automatic theme saving on changes."""
        self._auto_save_enabled = True
        self._logger.info("Auto-save enabled")

    def disable_auto_save(self) -> None:
        """Disable automatic theme saving on changes."""
        self._auto_save_enabled = False
        self._logger.info("Auto-save disabled")

    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return self._auto_save_enabled

    # ============================================================
    # Utility
    # ============================================================

    def reset_to_default(self) -> None:
        """Reset theme to default (light) preset."""
        self.apply_preset("light")
        self._logger.info("Theme reset to default")

    def get_manager(self):
        """Get the underlying ThemeManager instance."""
        return self._manager
