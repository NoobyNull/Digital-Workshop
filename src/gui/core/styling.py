"""
UI Styling and Theme Management Module

This module is kept for backward compatibility.
All theming is now handled by qt-material theme via ThemeService.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import QMainWindow


class StylingManager:
    """
    Backward compatibility class for styling management.

    All theming is now handled by qt-material theme via ThemeService.
    This class is kept for backward compatibility but does nothing.
    """

    def __init__(
        self, main_window: QMainWindow, logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the styling manager (no-op)."""
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

    def init_ui(self) -> None:
        """Initialize basic UI properties (no-op - qt-material handles this)."""

    def apply_theme_styles(self) -> None:
        """Apply theme (no-op - qt-material handles this)."""

    def apply_bar_palettes(self) -> None:
        """Apply bar palettes (no-op - qt-material handles this)."""

    def load_external_stylesheet(self) -> None:
        """Load external stylesheet (no-op - qt-material handles this)."""


# Convenience function for easy styling application
def apply_main_window_styling(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> StylingManager:
    """
    Convenience function to apply styling to a main window.

    Args:
        main_window: The main window to style
        logger: Optional logger instance

    Returns:
        StylingManager instance for further styling operations
    """
    manager = StylingManager(main_window, logger)
    manager.init_ui()
    manager.apply_theme_styles()
    return manager
