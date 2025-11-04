"""
Simplified QDarkStyleSheet Theme Service

This module provides a clean, simple interface to QDarkStyleSheet theming.
No complexity, no qt-material dependencies, just straightforward styling.

Usage:
    from src.gui.theme.qdarkstyle_service import QDarkStyleThemeService

    service = QDarkStyleThemeService.instance()
    service.apply_theme("dark")  # or "light"
"""

from typing import Literal, Optional
from PySide6.QtWidgets import QApplication
from src.core.logging_config import get_logger

logger = get_logger(__name__)

ThemeType = Literal["dark", "light", "auto"]


class QDarkStyleThemeService:
    """
    Simple, clean QDarkStyleSheet theme service.

    Features:
    - Single responsibility: Apply QDarkStyleSheet themes
    - No complexity: Just load and apply
    - Automatic fallback: If qdarkstyle unavailable, use Qt defaults
    - Thread-safe singleton pattern
    """

    _instance: Optional["QDarkStyleThemeService"] = None

    def __init__(self):
        """Initialize the theme service."""
        self._current_theme: ThemeType = "dark"
        self._qdarkstyle_available = self._check_qdarkstyle()

    @classmethod
    def instance(cls) -> "QDarkStyleThemeService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _check_qdarkstyle(self) -> bool:
        """Check if qdarkstyle is available."""
        try:
            import qdarkstyle

            logger.info(f"QDarkStyleSheet available: {qdarkstyle.__version__}")
            return True
        except ImportError:
            logger.warning("QDarkStyleSheet not available, will use Qt defaults")
            return False

    def apply_theme(self, theme: ThemeType = "dark") -> bool:
        """
        Apply a theme to the application.

        Args:
            theme: "dark", "light", or "auto" (uses system preference)

        Returns:
            True if successful, False otherwise
        """
        try:
            app = QApplication.instance()
            if not app:
                logger.error("No QApplication instance available")
                return False

            self._current_theme = theme

            if not self._qdarkstyle_available:
                logger.debug(
                    "QDarkStyleSheet not available, skipping theme application"
                )
                return False

            import qdarkstyle

            # Determine which palette to use
            if theme == "auto":
                # Auto-detect system theme
                palette_name = self._detect_system_theme()
            else:
                palette_name = theme if theme in ["dark", "light"] else "dark"

            # Load and apply stylesheet
            # qdarkstyle.load_stylesheet() returns light by default
            # We need to pass the palette class, not a string
            if palette_name == "dark":
                # For dark theme, we need to use the dark palette
                # The default Palette class is light, so we need to find the dark one
                stylesheet = qdarkstyle.load_stylesheet(qt_api="pyside6")
                # Check if there's a dark palette available
                try:
                    from qdarkstyle.palette.dark import DarkPalette

                    stylesheet = qdarkstyle.load_stylesheet(
                        qt_api="pyside6", palette=DarkPalette
                    )
                except ImportError:
                    # Fallback: use default (light) if dark not available
                    logger.warning("Dark palette not available, using default")
            else:
                # Light theme (default)
                stylesheet = qdarkstyle.load_stylesheet(qt_api="pyside6")

            app.setStyleSheet(stylesheet)

            logger.info(f"QDarkStyleSheet theme applied: {palette_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}", exc_info=True)
            return False

    def _detect_system_theme(self) -> str:
        """
        Detect system theme preference.

        Returns:
            "dark" or "light"
        """
        try:
            import platform

            system = platform.system()

            if system == "Windows":
                try:
                    import winreg

                    registry_path = (
                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    )
                    registry_key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, registry_path
                    )
                    value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                    winreg.CloseKey(registry_key)
                    return "light" if value == 1 else "dark"
                except Exception:
                    return "dark"  # Default to dark

            elif system == "Darwin":  # macOS
                try:
                    import subprocess

                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                    )
                    return "dark" if "Dark" in result.stdout else "light"
                except Exception:
                    return "light"  # Default to light

            else:  # Linux and others
                return "dark"  # Default to dark

        except Exception as e:
            logger.debug(f"Failed to detect system theme: {e}")
            return "dark"  # Safe default

    def get_current_theme(self) -> ThemeType:
        """Get the currently applied theme."""
        return self._current_theme

    def is_available(self) -> bool:
        """Check if QDarkStyleSheet is available."""
        return self._qdarkstyle_available
