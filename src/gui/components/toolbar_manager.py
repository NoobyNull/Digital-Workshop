"""
Toolbar Management Module

This module handles the creation and management of the application's toolbar,
including icon management, action creation, and toolbar styling.

Classes:
    ToolbarManager: Main class for managing toolbar functionality
"""

import logging
from typing import Optional, Callable

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QToolBar

from src.gui.theme import ThemeManager, COLORS


class ToolbarManager:
    """
    Manages the application's toolbar and all associated toolbar actions.

    This class handles the creation of toolbar actions, icon management,
    and styling to provide a complete toolbar system for the main window.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
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
        # Explicit ThemeManager toolbar styling so it doesn't inherit/bleed from other bars
        try:
            tm = ThemeManager.instance()
            _toolbar_css = """
                QToolBar#MainToolBar {
                    background-color: {{toolbar_bg}};
                    border: 1px solid {{toolbar_border}};
                    spacing: 3px;
                    padding: 4px;
                }
                QToolBar#MainToolBar::handle {
                    background-color: {{toolbar_handle_bg}};
                    width: 8px;
                    margin: 4px;
                }
            """
            tm.register_widget(toolbar, css_text=_toolbar_css)
            tm.apply_stylesheet(toolbar)
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
                icon_names = ["fa5s.folder-open", "fa5s.search-plus", "fa5s.search-minus", "fa5s.sync"]
                for _name in icon_names:
                    test_icon = qta.icon(_name, color=COLORS.text)
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

        def _icon(name: str):
            if not icons_ok or qta is None:
                return QIcon()
            try:
                # Use theme text color to keep icons legible in light/dark modes
                return qta.icon(name, color=COLORS.text)
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

        # Add theme switcher
        toolbar.addSeparator()
        try:
            from src.gui.theme.ui.simple_theme_switcher import SimpleThemeSwitcher
            self.theme_switcher = SimpleThemeSwitcher(self.main_window)
            toolbar.addWidget(self.theme_switcher)
            self.logger.debug("Theme switcher added to toolbar")
        except Exception as e:
            self.logger.warning(f"Failed to add theme switcher: {e}")

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
        if hasattr(self.main_window, '_open_model'):
            self.main_window._open_model()

    def _zoom_in(self) -> None:
        """Handle zoom in action."""
        if hasattr(self.main_window, '_zoom_in'):
            self.main_window._zoom_in()

    def _zoom_out(self) -> None:
        """Handle zoom out action."""
        if hasattr(self.main_window, '_zoom_out'):
            self.main_window._zoom_out()

    def _reset_view(self) -> None:
        """Handle reset view action."""
        if hasattr(self.main_window, '_reset_view'):
            self.main_window._reset_view()


# Convenience function for easy toolbar setup
def setup_main_window_toolbar(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> ToolbarManager:
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
