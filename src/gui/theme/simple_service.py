"""
Simplified theme service using built-in PySide6 styling.

Single Responsibility: Apply professional themes to the application using PySide6's built-in palette system.
No external dependencies required.
"""

from typing import Optional, Literal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

ThemeType = Literal["light", "dark", "auto"]
# ThemeLibrary is deprecated - only builtin styling is supported now
ThemeLibrary = Literal["builtin"]

# Legacy qt-material theme lists (kept for reference, not used)
# QT_MATERIAL_DARK_THEMES = [
#     "dark_amber",
#     "dark_blue",
#     "dark_cyan",
#     "dark_lightgreen",
#     "dark_pink",
#     "dark_purple",
#     "dark_red",
#     "dark_teal",
#     "dark_yellow",
# ]
#
# QT_MATERIAL_LIGHT_THEMES = [
#     "light_amber",
#     "light_blue",
#     "light_cyan",
#     "light_cyan_500",
#     "light_lightgreen",
#     "light_pink",
#     "light_purple",
#     "light_red",
#     "light_teal",
#     "light_yellow",
# ]


class ThemeService:
    """Simplified theme service using built-in PySide6 styling."""

    _instance: Optional["ThemeService"] = None
    _current_theme: str = "dark"
    _current_library: ThemeLibrary = "builtin"

    def __new__(cls) -> "ThemeService":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme service."""
        self.settings = QSettings("Digital Workshop", "Digital Workshop")
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
        library: ThemeLibrary = "qdarkstyle",  # noqa: ARG002 - kept for compatibility
    ) -> bool:
        """
        Apply a professional theme using built-in PySide6 styling.

        Args:
            theme: "light", "dark", or "auto" (sync with OS)
            library: Deprecated - only built-in styling is supported

        Returns:
            True if successful, False otherwise
        """
        try:
            app = QApplication.instance()
            if not app:
                return False

            # Use built-in fallback theme system (no external dependencies)
            self._apply_fallback_theme(app, theme)
            return True

        except Exception as e:
            logger.error("Failed to apply theme: %s", e, exc_info=True)
            return False

    def _apply_fallback_theme(self, app: QApplication, theme: str) -> bool:
        """
        Apply fallback theme using PySide6 built-in styling.

        Args:
            app: QApplication instance
            theme: Theme type ("light", "dark", or "auto")

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate QApplication instance
            if not app:
                logger.warning("No QApplication instance available for fallback theme")
                return False

            # Import required PySide6 components
            from PySide6.QtWidgets import QStyleFactory
            from PySide6.QtGui import QPalette, QColor

            # Set Fusion style for consistent look across platforms
            app.setStyle(QStyleFactory.create("Fusion"))

            # Determine effective theme for auto mode
            effective_theme = theme
            if theme == "auto":
                try:
                    import darkdetect

                    effective_theme = "dark" if darkdetect.isDark() else "light"
                except ImportError:
                    effective_theme = "dark"  # Default to dark if detection fails
                    logger.debug("darkdetect not available, defaulting to dark theme")

            # Create palette based on effective theme
            palette = QPalette()

            if effective_theme == "dark":
                # Dark theme colors - professional dark palette
                palette.setColor(QPalette.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
                palette.setColor(QPalette.Base, QColor(25, 25, 25))
                palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
                palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
                palette.setColor(QPalette.Text, QColor(255, 255, 255))
                palette.setColor(QPalette.Button, QColor(53, 53, 53))
                palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
                palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
                palette.setColor(QPalette.Link, QColor(42, 130, 218))
                palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
                palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

                # Additional dark theme colors for better UI consistency
                palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.Base, QColor(32, 32, 32))

            else:
                # Light theme colors - professional light palette
                palette.setColor(QPalette.Window, QColor(240, 240, 240))
                palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
                palette.setColor(QPalette.Base, QColor(255, 255, 255))
                palette.setColor(QPalette.AlternateBase, QColor(247, 247, 247))
                palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
                palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
                palette.setColor(QPalette.Text, QColor(0, 0, 0))
                palette.setColor(QPalette.Button, QColor(240, 240, 240))
                palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
                palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
                palette.setColor(QPalette.Link, QColor(0, 0, 255))
                palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
                palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

                # Additional light theme colors for better UI consistency
                palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(255, 255, 255))
                palette.setColor(QPalette.Disabled, QPalette.Base, QColor(240, 240, 240))

            # Apply the palette to the application
            app.setPalette(palette)

            # Update current theme state
            self._current_theme = theme
            self._current_library = "builtin"
            self._save_theme()

            logger.info("Applied fallback theme: %s (effective: {effective_theme})", theme)
            return True

        except Exception as e:
            logger.error("Failed to apply fallback theme: %s", e, exc_info=True)
            return False

    # Old qt-material implementation removed - use built-in styling instead
    #
    #         # Get the stored qt-material theme variant
    #         variant = self.settings.value("qt_material_variant", "blue")
    #
    #         # qt-material themes
    #         if theme == "light":
    #             theme_name = f"light_{variant}.xml"
    #             apply_stylesheet(app, theme=theme_name, invert_secondary=True)
    #         elif theme == "dark":
    #             theme_name = f"dark_{variant}.xml"
    #             apply_stylesheet(app, theme=theme_name)
    #         elif theme == "auto":
    #             # Try to detect OS theme
    #             try:
    #                 import darkdetect
    #                 if darkdetect.isDark():
    #                     theme_name = f"dark_{variant}.xml"
    #                     apply_stylesheet(app, theme=theme_name)
    #                 else:
    #                     theme_name = f"light_{variant}.xml"
    #                     apply_stylesheet(app, theme=theme_name, invert_secondary=True)
    #             except ImportError:
    #                 theme_name = f"dark_{variant}.xml"
    #                 apply_stylesheet(app, theme=theme_name)
    #
    #         self._current_theme = theme
    #         self._current_library = "qt-material"
    #         self._save_theme()
    #
    #         # Notify WindowTitleBarManager to update all title bars
    #         try:
    #             from src.gui.window.title_bar_manager import WindowTitleBarManager
    #             manager = WindowTitleBarManager.instance()
    #             manager.update_all_title_bars(theme)
    #         except Exception:
    #             pass  # Title bar manager may not be initialized yet
    #
    #         return True
    #
    #     except ImportError:
    #         # qt-material not available, fallback will be used
    #         return False

    # DEPRECATED: Old fallback theme implementation - kept for reference only
    # def _apply_fallback_theme(self, app: QApplication, theme: ThemeType) -> None:
    #     """Apply fallback theme using PySide6 built-in styles (DEPRECATED)."""
    #     from PySide6.QtWidgets import QStyleFactory
    #     from PySide6.QtGui import QPalette, QColor
    #
    #     if not app:
    #         logger.warning("No QApplication instance available for fallback theme")
    #         return
    #
    #     # Set Fusion style for consistent look
    #     app.setStyle(QStyleFactory.create("Fusion"))
    #
    #     # Determine effective theme for auto
    #     effective_theme = theme
    #     if theme == "auto":
    #         try:
    #             import darkdetect
    #             effective_theme = "dark" if darkdetect.isDark() else "light"
    #         except ImportError:
    #             effective_theme = "dark"  # Default to dark if detection fails
    #
    #     # Create palette based on effective theme
    #     palette = QPalette()
    #
    #     if effective_theme == "dark":
    #         # Dark theme colors
    #         palette.setColor(QPalette.Window, QColor(53, 53, 53))
    #         palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    #         palette.setColor(QPalette.Base, QColor(25, 25, 25))
    #         palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    #         palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    #         palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    #         palette.setColor(QPalette.Text, QColor(255, 255, 255))
    #         palette.setColor(QPalette.Button, QColor(53, 53, 53))
    #         palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    #         palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    #         palette.setColor(QPalette.Link, QColor(42, 130, 218))
    #         palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    #         palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    #     else:
    #         # Light theme colors
    #         palette.setColor(QPalette.Window, QColor(240, 240, 240))
    #         palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    #         palette.setColor(QPalette.Base, QColor(255, 255, 255))
    #         palette.setColor(QPalette.AlternateBase, QColor(247, 247, 247))
    #         palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    #         palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    #         palette.setColor(QPalette.Text, QColor(0, 0, 0))
    #         palette.setColor(QPalette.Button, QColor(240, 240, 240))
    #         palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    #         palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    #         palette.setColor(QPalette.Link, QColor(0, 0, 255))
    #         palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    #         palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    #
    #     app.setPalette(palette)
    #
    #     self._current_theme = theme
    #     self._current_library = "fallback"
    #     self._save_theme()
    #
    #     logger.info("Applied fallback theme: %s (effective: {effective_theme})", theme)

    # DEPRECATED: Old qt-material methods - kept for reference only
    # def get_available_themes(self) -> dict:
    #     """Get available Material Design themes (DEPRECATED)."""
    #     return {
    #         "qdarkstyle": {
    #             "themes": ["light", "dark", "auto"],
    #         }
    #     }
    #
    # def get_qt_material_variants(self, theme_type: str = "dark") -> list:
    #     """Get available qt-material color variants (DEPRECATED)."""
    #     return []
    #
    # def set_qt_material_variant(self, variant: str) -> None:
    #     """Set the qt-material color variant (DEPRECATED)."""
    #     pass  # No-op for backward compatibility

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
        self._current_library = self.settings.value("theme_library", "builtin")
