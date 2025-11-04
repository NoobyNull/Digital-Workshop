"""
Window Title Bar Manager for centralized theme-aware title bar management.

Single Responsibility: Track all application windows and update their title bars
when the theme changes.
"""

import logging
from typing import Dict, Optional
from weakref import WeakSet

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

from src.gui.window.custom_title_bar import CustomTitleBar


class WindowTitleBarManager(QObject):
    """
    Centralized manager for custom title bars across all application windows.

    Tracks all windows and updates their title bars when theme changes.
    Uses weak references to avoid memory leaks.
    """

    # Signal emitted when theme changes (for external listeners)
    theme_changed = Signal(str)  # Emits theme name ("dark" or "light")

    _instance: Optional["WindowTitleBarManager"] = None
    _windows: WeakSet = WeakSet()
    _title_bars: Dict[int, CustomTitleBar] = {}

    def __new__(cls) -> "WindowTitleBarManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager."""
        if self._initialized:
            return
        super().__init__()
        self.logger = self._get_logger()
        self._initialized = True
        self.logger.debug("WindowTitleBarManager initialized")

    @classmethod
    def instance(cls) -> "WindowTitleBarManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _get_logger() -> logging.Logger:
        """Get logger instance."""
        from src.core.logging_config import get_logger

        return get_logger(__name__)

    def register_window(self, window: QWidget, title_bar: Optional[CustomTitleBar] = None) -> None:
        """
        Register a window with the manager.

        Args:
            window: The window to register
            title_bar: Optional CustomTitleBar instance for this window
        """
        try:
            self._windows.add(window)
            if title_bar:
                self._title_bars[id(window)] = title_bar
            self.logger.debug("Registered window: %s", window.__class__.__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to register window: %s", e)

    def unregister_window(self, window: QWidget) -> None:
        """
        Unregister a window from the manager.

        Args:
            window: The window to unregister
        """
        try:
            window_id = id(window)
            if window_id in self._title_bars:
                del self._title_bars[window_id]
            self.logger.debug("Unregistered window: %s", window.__class__.__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to unregister window: %s", e)

    def update_all_title_bars(self, theme: str) -> None:
        """
        Update all registered title bars when theme changes.

        Args:
            theme: The new theme ("dark" or "light")
        """
        try:
            updated_count = 0
            for window_id, title_bar in list(self._title_bars.items()):
                try:
                    if title_bar and hasattr(title_bar, "update_theme"):
                        title_bar.update_theme()
                        updated_count += 1
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.debug("Failed to update title bar: %s", e)

            self.logger.debug("Updated %s title bars for theme: {theme}", updated_count)
            self.theme_changed.emit(theme)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update all title bars: %s", e)

    def get_registered_windows_count(self) -> int:
        """Get count of registered windows."""
        return len(self._windows)

    def get_title_bars_count(self) -> int:
        """Get count of registered title bars."""
        return len(self._title_bars)

    def clear_dead_references(self) -> None:
        """Clean up dead window references."""
        try:
            # WeakSet automatically removes dead references
            # This method is here for explicit cleanup if needed
            dead_ids = [
                wid
                for wid in self._title_bars.keys()
                if not any(id(w) == wid for w in self._windows)
            ]
            for wid in dead_ids:
                del self._title_bars[wid]
            if dead_ids:
                self.logger.debug("Cleaned up %s dead references", len(dead_ids))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to clean dead references: %s", e)
