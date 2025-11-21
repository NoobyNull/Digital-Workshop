"""
Event Coordination and Signal Handling Module

This module handles event coordination, signal management, and cleanup
operations for the main window, ensuring proper resource management
and graceful application shutdown.

Classes:
    EventCoordinator: Main class for managing events and signals
"""

import logging
from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow


class EventCoordinator:
    """
    Manages event coordination and signal handling for the main window.

    This class handles window events, cleanup operations, and ensures
    proper resource management throughout the application lifecycle.
    """

    def __init__(
        self, main_window: QMainWindow, logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize the event coordinator.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

    def handle_resize_event(self, event) -> None:
        """Handle window resize events."""
        try:
            # Autosave geometry changes on resize (debounced)
            if hasattr(self.main_window, "_schedule_layout_save"):
                self.main_window._schedule_layout_save()
        except Exception:
            pass

        # Keep snap overlays aligned with the window
        try:
            if hasattr(self.main_window, "_snap_layer"):
                self.main_window._snap_layer.update_geometry()
        except Exception:
            pass

        # Call original resize event
        if hasattr(super(), "resizeEvent"):
            super(self.main_window.__class__, self.main_window).resizeEvent(event)

    def handle_move_event(self, event) -> None:
        """Handle window move events."""
        try:
            # Autosave geometry changes on move (debounced)
            if hasattr(self.main_window, "_schedule_layout_save"):
                self.main_window._schedule_layout_save()
        except Exception:
            pass

        # Call original move event
        if hasattr(super(), "moveEvent"):
            super(self.main_window.__class__, self.main_window).moveEvent(event)

    def handle_close_event(self, event) -> None:
        """Handle window close event."""
        self.logger.info("Application closing")

        # Stop background hasher if running
        if (
            hasattr(self.main_window, "background_hasher")
            and self.main_window.background_hasher
        ):
            if self.main_window.background_hasher.isRunning():
                try:
                    self.logger.info("Stopping background hasher...")
                    self.main_window.background_hasher.stop()
                    self.main_window.background_hasher.wait(
                        3000
                    )  # Wait up to 3 seconds
                    self.logger.info("Background hasher stopped")
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning(
                        "Failed to stop background hasher cleanly: %s", e
                    )

        # Safety: Ensure layout edit mode is locked before closing
        try:
            if (
                hasattr(self.main_window, "layout_edit_mode")
                and self.main_window.layout_edit_mode
            ):
                self.logger.info("Locking layout edit mode before application close")
                if hasattr(self.main_window, "_set_layout_edit_mode"):
                    # Don't show message during close
                    self.main_window._set_layout_edit_mode(False, show_message=False)
                if hasattr(self.main_window, "toggle_layout_edit_action"):
                    self.main_window.toggle_layout_edit_action.setChecked(False)
                # Persist the locked state
                settings = QSettings()
                settings.setValue("ui/layout_edit_mode", False)
                self.logger.info("Layout edit mode locked for safety on close")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to lock layout edit mode on close: %s", e)

        # Clean up resources
        if hasattr(self.main_window, "status_timer"):
            self.main_window.status_timer.stop()

        # Clean up widgets
        if hasattr(self.main_window, "metadata_editor"):
            self.main_window.metadata_editor.cleanup()

        if hasattr(self.main_window, "model_library_widget"):
            self.main_window.model_library_widget.cleanup()

        # Memory cleanup: clear material texture cache
        try:
            if (
                hasattr(self.main_window, "material_manager")
                and self.main_window.material_manager
            ):
                self.main_window.material_manager.clear_texture_cache()
                self.logger.info("Cleared MaterialManager texture cache on close")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to clear material texture cache: %s", e)

        # Persist final lighting settings on close
        try:
            if hasattr(self.main_window, "_save_lighting_settings"):
                self.main_window._save_lighting_settings()
        except Exception:
            pass

        # Accept the close event
        event.accept()

        self.logger.info("Application closed")


# Convenience function for easy event coordination setup
def setup_event_coordination(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> EventCoordinator:
    """
    Convenience function to set up event coordination for a main window.

    Args:
        main_window: The main window to set up event coordination for
        logger: Optional logger instance

    Returns:
        EventCoordinator instance for further event operations
    """
    return EventCoordinator(main_window, logger)
