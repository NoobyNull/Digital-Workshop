"""
Toolbar Management Module

This module handles the creation and management of the application's toolbar,
including icon management, action creation, and toolbar styling.

Classes:
    ToolbarManager: Main class for managing toolbar functionality
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow


class ToolbarManager:
    """
    Manages the application's toolbar and all associated toolbar actions.

    This class handles the creation of toolbar actions, icon management,
    and styling to provide a complete toolbar system for the main window.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the toolbar manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)
        self.main_toolbar = None

    def setup_toolbar(self) -> None:
        """Set up the main application toolbar with icons and fallbacks."""
        self.logger.debug("Setting up toolbar")

        self.main_toolbar = self.main_window.addToolBar("Main")
        toolbar = self.main_toolbar
        toolbar.setObjectName("MainToolBar")
        try:
            toolbar.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass

        # Attempt to import QtAwesome for icon-based actions and determine icon availability
        try:
            import qtawesome as qta  # type: ignore

            has_qta = True
        except Exception:
            qta = None  # type: ignore
            has_qta = False

        # Determine if icons can actually be built
        icons_ok = False
        if has_qta and qta is not None:
            try:
                # Validate all icons we plan to use can be created
                icon_names = [
                    "fa5s.folder-open",
                    "fa5s.search-plus",
                    "fa5s.search-minus",
                    "fa5s.sync",
                    "fa5s.cloud-download-alt",
                ]
                for _name in icon_names:
                    test_icon = qta.icon(_name)
                    if test_icon.isNull():
                        raise ValueError(f"qtawesome returned null icon for '{_name}'")
                icons_ok = True
            except Exception:
                icons_ok = False
        else:
            icons_ok = False

        # Configure toolbar presentation based on actual icon availability
        if icons_ok:
            toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
            toolbar.setIconSize(QSize(16, 16))
            self.logger.info("Toolbar set to icon-only mode")
        else:
            toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
            self.logger.info("Toolbar in text-only mode (qtawesome unavailable)")

        def _icon(name: str) -> None:
            if not icons_ok or qta is None:
                return QIcon()
            try:
                # qtawesome will use theme colors automatically
                return qta.icon(name)
            except Exception:
                return QIcon()

        def _add_action(text: str, icon_name: str, slot, tooltip: str) -> QAction:
            if icons_ok:
                action = QAction(_icon(icon_name), text, self.main_window)
            else:
                action = QAction(text, self.main_window)
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
            action.triggered.connect(slot)
            toolbar.addAction(action)
            return action

        # Open
        _add_action(
            "Open",
            "fa5s.folder-open",
            self._open_model,
            "Open a 3D model file",
        )

        _add_action(
            "Import URL",
            "fa5s.cloud-download-alt",
            self._import_from_url,
            "Download and import a model from a URL",
        )

        # Analyze Model
        self.edit_model_action = _add_action(
            "Analyze",
            "fa5s.stethoscope",
            self._edit_model,
            "Analyze model for errors and fix them",
        )
        self.edit_model_action.setEnabled(False)
        # Add to Project
        self.add_to_project_action = _add_action(
            "Add to Project",
            "fa5s.save",
            self._add_to_project,
            "Save current tab data to the active project",
        )

        toolbar.addSeparator()

        # Zoom controls
        _add_action(
            "Zoom In",
            "fa5s.search-plus",
            self._zoom_in,
            "Zoom in on the 3D view",
        )
        _add_action(
            "Zoom Out",
            "fa5s.search-minus",
            self._zoom_out,
            "Zoom out from the 3D view",
        )

        # Reset view
        _add_action(
            "Reset View",
            "fa5s.sync",
            self._reset_view,
            "Reset the 3D view to default",
        )

        # Theme cycle moved to status bar

        # Show toolbar mode in status bar for immediate visual feedback
        try:
            if icons_ok:
                self.main_window.statusBar().showMessage("Toolbar icons active", 2000)
            else:
                self.main_window.statusBar().showMessage("Toolbar text-only (no qtawesome)", 2000)
        except Exception:
            pass

        self.logger.debug("Toolbar setup completed")

    # Action handler methods (these would need to be connected to actual implementations)
    def _open_model(self) -> None:
        """Handle open model action."""
        if hasattr(self.main_window, "_open_model"):
            self.main_window._open_model()

    def _import_from_url(self) -> None:
        """Handle toolbar import-from-URL action."""
        if hasattr(self.main_window, "_open_import_from_url_dialog"):
            self.main_window._open_import_from_url_dialog()

    def _edit_model(self) -> None:
        """Handle edit model action."""
        if hasattr(self.main_window, "_edit_model"):
            self.main_window._edit_model()

    def _zoom_in(self) -> None:
        """Handle zoom in action."""
        if hasattr(self.main_window, "_zoom_in"):
            self.main_window._zoom_in()

    def _add_to_project(self) -> None:
        """Handle Add to Project action."""
        if hasattr(self.main_window, "_add_to_project"):
            self.main_window._add_to_project()

    def _zoom_out(self) -> None:
        """Handle zoom out action."""
        if hasattr(self.main_window, "_zoom_out"):
            self.main_window._zoom_out()

    def _reset_view(self) -> None:
        """Handle reset view action."""
        if hasattr(self.main_window, "_reset_view"):
            self.main_window._reset_view()


# Convenience function for easy toolbar setup
def setup_main_window_toolbar(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> ToolbarManager:
    """
    Convenience function to set up toolbar for a main window.

    Args:
        main_window: The main window to set up toolbar for
        logger: Optional logger instance

    Returns:
        ToolbarManager instance for further toolbar operations
    """
    manager = ToolbarManager(main_window, logger)
    manager.setup_toolbar()
    return manager
