"""
Consolidated theme service for Digital Workshop.

This module consolidates the theme service functionality from:
- simple_service.py - Qt-material focused service (primary base)
- service.py - Complex orchestration service (selected features)
- theme_api.py - Public API functions
- detector.py - System theme detection

Single Responsibility: Unified API for all theme operations with focus on qt-material.
"""

import logging
import platform
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from .theme_core import (
    ThemePersistence,
    get_preset,
    list_presets,
    hex_to_qcolor,
    hex_to_vtk_rgb,
)

logger = logging.getLogger(__name__)

ThemeType = Literal["light", "dark", "auto"]
ThemeLibrary = Literal["qt-material"]

# Qt-Material available themes
QT_MATERIAL_DARK_THEMES = [
    "dark_amber",
    "dark_blue",
    "dark_cyan",
    "dark_lightgreen",
    "dark_pink",
    "dark_purple",
    "dark_red",
    "dark_teal",
    "dark_yellow",
]

QT_MATERIAL_LIGHT_THEMES = [
    "light_amber",
    "light_blue",
    "light_cyan",
    "light_cyan_500",
    "light_lightgreen",
    "light_pink",
    "light_purple",
    "light_red",
    "light_teal",
    "light_yellow",
]


class SystemThemeDetector:
    """
    Detects the system's theme preference (light or dark mode).

    Supports:
    - Windows: Registry-based detection
    - macOS: Defaults-based detection
    - Linux: Environment variable detection
    """

    def __init__(self):
        """Initialize the detector."""
        self._current_mode: Literal["light", "dark"] = "light"
        self._enabled = False
        self._detect_system_theme()

    def detect(self) -> Literal["light", "dark"]:
        """
        Detect current system theme preference.

        Returns:
            "light" or "dark"
        """
        system = platform.system()

        try:
            if system == "Windows":
                return self._detect_windows()
            elif system == "Darwin":
                return self._detect_macos()
            elif system == "Linux":
                return self._detect_linux()
        except Exception as e:
            logger.warning("Failed to detect system theme: %s", e)

        return "light"  # Default fallback

    def _detect_windows(self) -> Literal["light", "dark"]:
        r"""
        Detect Windows dark mode via registry.

        Checks: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
        Value: AppsUseLightTheme (0 = dark, 1 = light)
        """
        try:
            import winreg

            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
            value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)

            # value == 1 means light theme, value == 0 means dark theme
            return "light" if value == 1 else "dark"
        except Exception as e:
            logger.debug("Windows theme detection failed: %s", e)
            return "light"

    def _detect_macos(self) -> Literal["light", "dark"]:
        """
        Detect macOS dark mode via defaults.

        Checks: defaults read -g AppleInterfaceStyle
        Returns "dark" if set, "light" otherwise.
        """
        try:
            import subprocess

            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            # If command succeeds and output contains "Dark", it's dark mode
            if result.returncode == 0 and "Dark" in result.stdout:
                return "dark"
            return "light"
        except Exception as e:
            logger.debug("macOS theme detection failed: %s", e)
            return "light"

    def _detect_linux(self) -> Literal["light", "dark"]:
        """
        Detect Linux dark mode via environment variables and GTK settings.

        Checks:
        - GTK_THEME environment variable
        - dconf settings (GNOME)
        - Qt style hints
        """
        try:
            import os

            # Check GTK_THEME environment variable
            gtk_theme = os.environ.get("GTK_THEME", "").lower()
            if "dark" in gtk_theme:
                return "dark"

            # Check GNOME dconf settings
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "dconf",
                        "read",
                        "/org/gnome/desktop/interface/gtk-application-prefer-dark-theme",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                if result.returncode == 0 and "true" in result.stdout.lower():
                    return "dark"
            except Exception:
                pass

            # Check QT_STYLE_OVERRIDE
            qt_style = os.environ.get("QT_STYLE_OVERRIDE", "").lower()
            if "dark" in qt_style:
                return "dark"

            return "light"
        except Exception as e:
            logger.debug("Linux theme detection failed: %s", e)
            return "light"

    def _detect_system_theme(self) -> None:
        """Detect and cache current system theme."""
        self._current_mode = self.detect()
        logger.info("System theme detected: %s", self._current_mode)

    def get_current_mode(self) -> Literal["light", "dark"]:
        """Get the currently detected system theme mode."""
        return self._current_mode

    def enable(self) -> None:
        """Enable system theme detection."""
        self._enabled = True
        self._detect_system_theme()
        logger.info("System theme detection enabled")

    def disable(self) -> None:
        """Disable system theme detection."""
        self._enabled = False
        logger.info("System theme detection disabled")

    def is_enabled(self) -> bool:
        """Check if system theme detection is enabled."""
        return self._enabled

    def refresh(self) -> Literal["light", "dark"]:
        """
        Refresh the detected system theme.

        Returns:
            The newly detected theme mode
        """
        old_mode = self._current_mode
        self._detect_system_theme()

        if old_mode != self._current_mode:
            logger.info("System theme changed: %s -> %s", old_mode, self._current_mode)

        return self._current_mode


class ThemeService:
    """
    Unified theme service focusing on qt-material themes.

    This service consolidates:
    - Qt-material theme management
    - System theme detection
    - Settings persistence
    - Simplified orchestration
    - Backward-compatible API
    """

    _instance: Optional["ThemeService"] = None
    _current_theme: str = "dark"
    _current_library: ThemeLibrary = "qt-material"

    def __new__(cls) -> "ThemeService":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme service."""
        if hasattr(self, "_initialized"):
            return

        self.settings = QSettings("Digital Workshop", "Digital Workshop")
        self._detector = SystemThemeDetector()
        self._persistence = ThemePersistence()
        self._auto_save_enabled = True
        self._current_preset = "light"

        # Initialize color palette
        self._colors = self._get_default_colors()

        # Don't try to import ThemeManager - it's just an alias to ThemeService
        # This avoids circular references
        self._manager = None

        self._load_saved_theme()
        self._initialized = True
        logger.info("ThemeService initialized")

    @classmethod
    def instance(cls) -> "ThemeService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ============================================================
    # Core Theme Management (Qt-Material focused)
    # ============================================================

    def apply_theme(
        self,
        theme: ThemeType = "dark",
        library: ThemeLibrary = "qt-material",  # noqa: ARG002 - kept for compatibility
    ) -> bool:
        """
        Apply a professional Material Design theme.

        Args:
            theme: "light", "dark", or "auto" (sync with OS)
            library: "qt-material" (only option)

        Returns:
            True if successful, False otherwise
        """
        try:
            app = QApplication.instance()
            if not app:
                return False

            return self._apply_qt_material(app, theme)

        except Exception as e:
            logger.error("Failed to apply theme: %s", e, exc_info=True)
            return False

    def _apply_qt_material(self, app: QApplication, theme: ThemeType) -> bool:
        """Apply fallback theme (qt-material removed)."""
        try:
            # qt-material has been removed - use simple fallback theme
            self._current_theme = theme
            self._current_library = "qt-material"
            self._save_theme()

            # Notify WindowTitleBarManager to update all title bars
            try:
                from src.gui.window.title_bar_manager import WindowTitleBarManager

                manager = WindowTitleBarManager.instance()
                manager.update_all_title_bars(theme)
            except Exception:
                pass  # Title bar manager may not be initialized yet

            return True

        except Exception as e:
            logger.warning(f"Failed to apply fallback theme: {e}")
            return False

    def get_current_theme(self) -> tuple[str, ThemeLibrary]:
        """Get current theme and library."""
        return self._current_theme, self._current_library

    def get_available_themes(self) -> dict:
        """Get available Material Design themes."""
        return {
            "qt-material": {
                "themes": ["light", "dark", "auto"],
                "variants": {
                    "dark": QT_MATERIAL_DARK_THEMES,
                    "light": QT_MATERIAL_LIGHT_THEMES,
                },
            }
        }

    def get_qt_material_variants(self, theme_type: str = "dark") -> list:
        """Get available qt-material color variants for a theme type."""
        if theme_type == "dark":
            return QT_MATERIAL_DARK_THEMES
        return QT_MATERIAL_LIGHT_THEMES

    def set_qt_material_variant(self, variant: str) -> None:
        """Set the qt-material color variant."""
        self.settings.setValue("qt_material_variant", variant)

    # ============================================================
    # Preset Management (Legacy compatibility)
    # ============================================================

    def apply_preset(self, name: str) -> None:
        """
        Apply a theme preset by name.

        Args:
            name: Preset name (light, dark, high_contrast, solarized_light, solarized_dark)
        """
        try:
            if self._manager:
                preset = get_preset(name)
                self._manager.set_colors(preset)
                self._current_preset = name
                logger.info("Applied preset: %s", name)

                if self._auto_save_enabled:
                    self.save_theme()
        except Exception as e:
            logger.error("Failed to apply preset %s: %s", name, e)
            raise

    def get_available_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list_presets()

    def get_current_preset(self) -> str:
        """Get the name of the currently applied preset."""
        return self._current_preset

    # ============================================================
    # Color Management (Legacy compatibility)
    # ============================================================

    def set_color(self, name: str, value: str) -> None:
        """
        Set a single color variable.

        Args:
            name: Color variable name
            value: Hex color value
        """
        try:
            if self._manager:
                self._manager.set_colors({name: value})
                self._current_preset = "custom"
                logger.debug("Set color %s = %s", name, value)

                if self._auto_save_enabled:
                    self.save_theme()
        except Exception as e:
            logger.error("Failed to set color %s: %s", name, e)
            raise

    def _get_default_colors(self) -> dict:
        """Get default color palette for VTK and UI."""
        return {
            "light_color": "#FFFFFF",  # Light color for VTK lighting
            "grid": "#444444",  # Grid color
            "ground": "#333333",  # Ground plane color
            "canvas_bg": "#1E1E1E",  # Canvas background
            "edge_color": "#CCCCCC",  # Edge color
            "primary": "#1976D2",  # Primary brand color
            "secondary": "#424242",  # Secondary color
            "accent": "#E31C79",  # Accent color
        }

    def get_color(self, name: str) -> str:
        """
        Get a color value by name.

        Args:
            name: Color variable name

        Returns:
            Hex color value
        """
        # Return color from palette, with fallback to black
        return self._colors.get(name, "#000000")

    def get_all_colors(self) -> Dict[str, str]:
        """Get all current color values."""
        if self._manager:
            return self._manager.colors.copy()
        return {}

    # ============================================================
    # Public API Functions (from theme_api.py)
    # ============================================================

    def color(self, name: str) -> str:
        """Get a hex color string by name."""
        return self.get_color(name)

    def qcolor(self, name: str) -> QColor:
        """Get a QColor for a named color."""
        hex_color = self.get_color(name)
        return hex_to_qcolor(hex_color)

    def vtk_rgb(self, name: str) -> Tuple[float, float, float]:
        """Get a normalized RGB tuple (0..1) for VTK for the given named color."""
        hex_color = self.get_color(name)
        return hex_to_vtk_rgb(hex_color)

    def theme_to_dict(self) -> Dict[str, str]:
        """Dump current theme colors as a dict of strings."""
        return self.get_all_colors()

    def set_theme(self, overrides: Dict[str, str]) -> None:
        """
        Replace theme colors with provided overrides.
        Expects hex strings (with or without '#') or valid CSS color strings.
        Unknown keys are ignored to preserve stability.
        """
        if self._manager:
            self._manager.set_colors({k: str(v) for k, v in overrides.items()})

    def list_theme_presets(self) -> list[str]:
        """List names of available theme presets."""
        return self.get_available_presets()

    def apply_theme_preset(
        self,
        preset_name: str,
        custom_mode: Optional[str] = None,
        base_primary: Optional[str] = None,
    ) -> None:
        """Apply a theme preset via ThemeManager."""
        if self._manager:
            self._manager.apply_preset(
                preset_name, custom_mode=custom_mode, base_primary=base_primary
            )

    def load_theme_from_settings(self) -> None:
        """
        Load theme from theme.json in AppData and apply to manager.
        If file doesn't exist or is invalid, keep defaults.
        """
        if self._manager:
            self._manager.load_from_settings()

    def save_theme_to_settings(self) -> None:
        """Persist current theme to theme.json in AppData."""
        if self._manager:
            self._manager.save_to_settings()

    # ============================================================
    # Persistence
    # ============================================================

    def save_theme(self) -> None:
        """Save current theme to AppData."""
        try:
            if self._manager:
                self._persistence.save_theme(self._manager.colors)
            logger.info("Theme saved")
        except Exception as e:
            logger.error("Failed to save theme: %s", e)

    def load_theme(self) -> bool:
        """
        Load theme from AppData.

        Returns:
            True if theme was loaded, False if no saved theme exists
        """
        try:
            colors = self._persistence.load_theme()
            if colors and self._manager:
                self._manager.set_colors(colors)
                self._current_preset = "custom"
                logger.info("Theme loaded from AppData")
                return True
            return False
        except Exception as e:
            logger.error("Failed to load theme: %s", e)
            return False

    def export_theme(self, path: Path) -> None:
        """
        Export current theme to a JSON file.

        Args:
            path: Path to export to
        """
        try:
            if self._manager:
                self._persistence.export_theme(path, self._manager.colors)
            logger.info("Theme exported to %s", path)
        except Exception as e:
            logger.error("Failed to export theme: %s", e)
            raise

    def import_theme(self, path: Path) -> None:
        """
        Import theme from a JSON file.

        Args:
            path: Path to import from
        """
        try:
            colors = self._persistence.import_theme(path)
            if colors and self._manager:
                self._manager.set_colors(colors)
                self._current_preset = "custom"
            logger.info("Theme imported from %s", path)
        except Exception as e:
            logger.error("Failed to import theme: %s", e)
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
        logger.info("System theme detection enabled, applied %s theme", preset)

    def disable_system_detection(self) -> None:
        """Disable system theme detection."""
        self._detector.disable()
        logger.info("System theme detection disabled")

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
        logger.info("Auto-save enabled")

    def disable_auto_save(self) -> None:
        """Disable automatic theme saving on changes."""
        self._auto_save_enabled = False
        logger.info("Auto-save disabled")

    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return self._auto_save_enabled

    # ============================================================
    # Utility
    # ============================================================

    def reset_to_default(self) -> None:
        """Reset theme to default (light) preset."""
        self.apply_preset("light")
        logger.info("Theme reset to default")

    def get_manager(self):
        """Get the underlying ThemeManager instance."""
        return self._manager

    def _save_theme(self) -> None:
        """Save current theme to settings."""
        self.settings.setValue("theme", self._current_theme)
        self.settings.setValue("theme_library", self._current_library)

    def _load_saved_theme(self) -> None:
        """Load saved theme from settings."""
        self._current_theme = self.settings.value("theme", "dark")
        self._current_library = self.settings.value("theme_library", "qt-material")


# ============================================================
# Backward Compatibility API
# ============================================================


class _ColorsProxy:
    """
    Proxy object to allow f-string usage like f"color: {COLORS.text};"
    Values are resolved from ThemeService at access time.
    """

    def __getattr__(self, name: str) -> str:
        service = ThemeService.instance()
        return service.get_color(name)


# Singleton-like proxy for read access inside f-strings, etc.
COLORS = _ColorsProxy()


def color(name: str) -> str:
    """
    Get a hex color string by name (e.g., 'primary', 'text').
    Returns a normalized '#rrggbb' string for hex variables, or raw string for non-hex values.
    """
    service = ThemeService.instance()
    return service.color(name)


def qcolor(name: str) -> QColor:
    """Get a QColor for a named color (e.g., qcolor('primary'))."""
    service = ThemeService.instance()
    return service.qcolor(name)


def vtk_rgb(name: str) -> Tuple[float, float, float]:
    """Get a normalized RGB tuple (0..1) for VTK for the given named color."""
    service = ThemeService.instance()
    return service.vtk_rgb(name)


def theme_to_dict() -> Dict[str, str]:
    """Dump current theme colors as a dict of strings."""
    service = ThemeService.instance()
    return service.theme_to_dict()


def set_theme(overrides: Dict[str, str]) -> None:
    """
    Replace theme colors with provided overrides.
    Expects hex strings (with or without '#') or valid CSS color strings.
    Unknown keys are ignored to preserve stability.
    """
    service = ThemeService.instance()
    service.set_theme(overrides)


def list_theme_presets() -> list[str]:
    """List names of available theme presets."""
    service = ThemeService.instance()
    return service.list_theme_presets()


def apply_theme_preset(
    preset_name: str,
    custom_mode: Optional[str] = None,
    base_primary: Optional[str] = None,
) -> None:
    """Apply a theme preset via ThemeService."""
    service = ThemeService.instance()
    service.apply_theme_preset(preset_name, custom_mode=custom_mode, base_primary=base_primary)


def load_theme_from_settings() -> None:
    """
    Load theme from theme.json in AppData and apply to manager.
    If file doesn't exist or is invalid, keep defaults.
    """
    service = ThemeService.instance()
    service.load_theme_from_settings()


def save_theme_to_settings() -> None:
    """Persist current theme to theme.json in AppData."""
    service = ThemeService.instance()
    service.save_theme_to_settings()
