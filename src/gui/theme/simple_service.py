"""
Simplified theme service using pyqtdarktheme and qt-material.

Single Responsibility: Apply professional themes to the application.
"""

from typing import Optional, Literal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings


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


class ThemeService:
    """Simplified theme service using professional theme libraries."""

    _instance: Optional["ThemeService"] = None
    _current_theme: str = "dark"
    _current_library: ThemeLibrary = "pyqtdarktheme"

    def __new__(cls) -> "ThemeService":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme service."""
        self.settings = QSettings("Candy-Cadence", "3D-MM")
        self._load_saved_theme()

    @classmethod
    def instance(cls) -> "ThemeService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def apply_theme(
        self,
        theme: ThemeType = "dark",
        library: ThemeLibrary = "qt-material"
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
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to apply theme: {e}", exc_info=True)
            return False

    def _apply_qt_material(self, app: QApplication, theme: ThemeType) -> bool:
        """Apply qt-material theme."""
        try:
            from qt_material import apply_stylesheet

            # Get the stored qt-material theme variant
            variant = self.settings.value("qt_material_variant", "blue")

            # qt-material themes
            if theme == "light":
                theme_name = f"light_{variant}.xml"
                apply_stylesheet(app, theme=theme_name, invert_secondary=True)
            elif theme == "dark":
                theme_name = f"dark_{variant}.xml"
                apply_stylesheet(app, theme=theme_name)
            elif theme == "auto":
                # Try to detect OS theme
                try:
                    import darkdetect
                    if darkdetect.isDark():
                        theme_name = f"dark_{variant}.xml"
                        apply_stylesheet(app, theme=theme_name)
                    else:
                        theme_name = f"light_{variant}.xml"
                        apply_stylesheet(app, theme=theme_name, invert_secondary=True)
                except ImportError:
                    theme_name = f"dark_{variant}.xml"
                    apply_stylesheet(app, theme=theme_name)

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

        except ImportError:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.warning("qt-material not installed")
            return False

    def get_available_themes(self) -> dict:
        """Get available Material Design themes."""
        return {
            "qt-material": {
                "themes": ["light", "dark", "auto"],
                "variants": {
                    "dark": QT_MATERIAL_DARK_THEMES,
                    "light": QT_MATERIAL_LIGHT_THEMES,
                }
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
        self.settings.sync()  # Force immediate write to disk

    def get_current_theme(self) -> tuple[str, ThemeLibrary]:
        """Get current theme and library."""
        return self._current_theme, self._current_library

    def _save_theme(self) -> None:
        """Save current theme to settings."""
        self.settings.setValue("theme", self._current_theme)
        self.settings.setValue("theme_library", self._current_library)

    def _load_saved_theme(self) -> None:
        """Load saved theme from settings."""
        self._current_theme = self.settings.value("theme", "dark")
        self._current_library = self.settings.value("theme_library", "pyqtdarktheme")

