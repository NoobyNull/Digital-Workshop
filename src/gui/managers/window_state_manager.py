"""
Window State Manager for MainWindow.

Handles window geometry, state persistence, and restoration.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging
import sys

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QDockWidget


class WindowStateManager:
    """Manages window state persistence and restoration."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the window state manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def restore_window_geometry_early(self) -> None:
        """Restore window geometry during initialization."""
        try:
            settings = QSettings()
            self.logger.debug("Starting early window geometry restoration")

            # Try to restore window geometry
            geometry_restored = False
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data and self.main_window.restoreGeometry(geometry_data):
                    self.logger.info("Window geometry restored successfully")
                    geometry_restored = True

            # Fallback: Use explicit width/height
            if not geometry_restored and settings.contains("window/width"):
                try:
                    from src.core.application_config import ApplicationConfig

                    config = ApplicationConfig.get_default()
                    default_width, default_height = (
                        ApplicationConfig.calculate_default_window_size()
                    )

                    width = settings.value("window/width", default_width, type=int)
                    height = settings.value("window/height", default_height, type=int)
                    maximized = settings.value("window/maximized", False, type=bool)

                    # Ensure dimensions are within reasonable bounds
                    width = max(800, min(width, 3840))
                    height = max(600, min(height, 2160))

                    self.main_window.resize(width, height)
                    if maximized:
                        self.main_window.showMaximized()

                    geometry_restored = True
                    self.logger.info("Window resized to %sx{height}", width)
                except Exception as e:
                    self.logger.debug("Failed to restore explicit size: %s", e)

            # Validate window position
            self.validate_window_position()

            # Try to restore window state
            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                if state_data and self.main_window.restoreState(state_data):
                    self.logger.info("Window state restored successfully")
                    self.ensure_no_floating_docks()

            # Handle maximize_on_startup setting
            if hasattr(self.main_window, "maximize_on_startup"):
                if self.main_window.maximize_on_startup:
                    self.main_window.showMaximized()
                    self.logger.info("Window maximized on startup")

            self.logger.debug("Early window geometry restoration completed")

        except Exception as e:
            self.logger.warning("Failed to restore window geometry: %s", e)

    def ensure_no_floating_docks(self) -> None:
        """Ensure no dock widgets are floating."""
        try:
            for dock in self.main_window.findChildren(QDockWidget):
                if dock.isFloating():
                    self.logger.debug(
                        "Re-docking floating dock: %s", dock.windowTitle()
                    )
                    dock.setFloating(False)
                    self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
            self.logger.debug("All floating docks have been re-docked")
        except Exception as e:
            self.logger.warning("Failed to ensure no floating docks: %s", e)

    def validate_window_position(self) -> None:
        """Validate that the window is positioned on a visible screen."""
        try:
            window_rect = self.main_window.frameGeometry()
            screens = QGuiApplication.screens()

            if not screens:
                self.logger.warning("No screens available")
                return

            # Check if window is on any screen
            is_on_screen = any(
                window_rect.intersects(screen.geometry()) for screen in screens
            )

            # If window is off-screen, center it on the primary screen
            if not is_on_screen:
                self.logger.warning(
                    f"Window position {window_rect.x()},{window_rect.y()} is off-screen"
                )
                primary_screen = QGuiApplication.primaryScreen()
                if primary_screen:
                    screen_rect = primary_screen.geometry()
                    x = (
                        screen_rect.x()
                        + (screen_rect.width() - window_rect.width()) // 2
                    )
                    y = (
                        screen_rect.y()
                        + (screen_rect.height() - window_rect.height()) // 2
                    )
                    self.main_window.move(x, y)
                    self.logger.info("Window moved to (%s,{y})", x)
        except Exception as e:
            self.logger.warning("Failed to validate window position: %s", e)

    def restore_window_state(self) -> None:
        """Restore saved window state from QSettings."""
        try:
            settings = QSettings()

            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data:
                    self.main_window.restoreGeometry(geometry_data)
                    self.logger.info("Window geometry restored")

            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                if state_data:
                    self.main_window.restoreState(state_data)
                    self.logger.info("Window state restored")
        except Exception as e:
            self.logger.warning("Failed to restore window state: %s", e)

    def save_window_settings(self) -> None:
        """Save current window geometry and dock state."""
        try:
            settings = QSettings()

            # Save window geometry and state
            geometry = self.main_window.saveGeometry()
            state = self.main_window.saveState()

            settings.setValue("window_geometry", geometry)
            settings.setValue("window_state", state)

            # Save window size and position explicitly
            settings.setValue("window/width", self.main_window.width())
            settings.setValue("window/height", self.main_window.height())
            settings.setValue("window/x", self.main_window.x())
            settings.setValue("window/y", self.main_window.y())
            settings.setValue("window/maximized", self.main_window.isMaximized())

            # Save current tab index
            if hasattr(self.main_window, "hero_tabs") and self.main_window.hero_tabs:
                settings.setValue(
                    "ui/active_hero_tab_index",
                    self.main_window.hero_tabs.currentIndex(),
                )

            # Sync settings to disk
            settings.sync()

            msg = f"Window settings saved: {self.main_window.width()}x{self.main_window.height()}"
            self.logger.info(msg)
            print(msg, file=sys.stdout, flush=True)

            # Flush logger handlers
            for handler in self.logger.handlers:
                handler.flush()

        except Exception as e:
            self.logger.error("Failed to save window settings: %s", e)

    def setup_periodic_save(self) -> None:
        """Set up periodic window state saving (every 5 seconds)."""
        try:
            self._save_timer = QTimer()
            self._save_timer.timeout.connect(self._periodic_save)
            self._save_timer.start(5000)
            self.logger.debug("Periodic window state save timer started")
        except Exception as e:
            self.logger.warning("Failed to set up periodic save: %s", e)

    def _periodic_save(self) -> None:
        """Periodically save window state without verbose logging."""
        try:
            settings = QSettings()
            settings.setValue("window_geometry", self.main_window.saveGeometry())
            settings.setValue("window_state", self.main_window.saveState())
            settings.setValue("window/width", self.main_window.width())
            settings.setValue("window/height", self.main_window.height())
            settings.setValue("window/maximized", self.main_window.isMaximized())
            settings.sync()
        except Exception:
            pass  # Silent failure for periodic saves
