"""
Menu Bar Management Module

This module handles the creation and management of the application's menu bar,
including file operations, view controls, and help menus.

Classes:
    MenuManager: Main class for managing menu bar functionality
"""

import logging
from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenuBar




class MenuManager:
    """
    Manages the application's menu bar and all associated menu actions.

    This class handles the creation of menus, actions, and their connections
    to provide a complete menu system for the main window.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the menu manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

        # Action references for external access
        self.show_metadata_action = None
        self.show_model_library_action = None
        self.toggle_layout_edit_action = None

    def setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        self.logger.debug("Setting up menu bar")

        menubar = self.main_window.menuBar()
        try:
            menubar.setObjectName("AppMenuBar")
            menubar.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open action
        open_action = QAction("&Open Model...", self.main_window)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a 3D model file")
        open_action.triggered.connect(self._open_model)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self.main_window)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # Analyze Model action
        self.edit_model_action = QAction("&Analyze & Fix Errors...", self.main_window)
        self.edit_model_action.setStatusTip("Analyze model for errors and fix them")
        self.edit_model_action.setEnabled(False)
        self.edit_model_action.triggered.connect(self._edit_model)
        edit_menu.addAction(self.edit_model_action)

        edit_menu.addSeparator()

        # Preferences action
        prefs_action = QAction("&Preferences...", self.main_window)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(prefs_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self.main_window)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in on the 3D view")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self.main_window)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out from the 3D view")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        view_menu.addSeparator()

        # Reset view action
        reset_view_action = QAction("&Reset View", self.main_window)
        reset_view_action.setStatusTip("Reset the 3D view to default")
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)

        # Save view action
        save_view_action = QAction("&Save View", self.main_window)
        save_view_action.setShortcut(QKeySequence("Ctrl+S"))
        save_view_action.setStatusTip("Save current camera view for this model")
        save_view_action.triggered.connect(self._save_current_view)
        view_menu.addAction(save_view_action)

        # Reset dock layout action (helps when a floating dock is hard to re-dock)
        reset_layout_action = QAction("Reset &Layout", self.main_window)
        reset_layout_action.setStatusTip("Restore default dock layout")
        reset_layout_action.triggered.connect(self._reset_dock_layout)
        view_menu.addAction(reset_layout_action)

        # Metadata Manager restoration action
        view_menu.addSeparator()
        self.show_metadata_action = QAction("Show &Metadata Manager", self.main_window)
        try:
            self.show_metadata_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
        except Exception:
            pass
        self.show_metadata_action.setStatusTip("Restore the Metadata Manager panel")
        self.show_metadata_action.setToolTip("Show the Metadata Manager (Ctrl+Shift+M)")
        self.show_metadata_action.triggered.connect(self._restore_metadata_manager)
        view_menu.addAction(self.show_metadata_action)

        # Model Library restoration action
        self.show_model_library_action = QAction("Show &Model Library", self.main_window)
        try:
            self.show_model_library_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        except Exception:
            pass
        self.show_model_library_action.setStatusTip("Restore the Model Library panel")
        self.show_model_library_action.setToolTip("Show the Model Library (Ctrl+Shift+L)")
        self.show_model_library_action.triggered.connect(self._restore_model_library)
        view_menu.addAction(self.show_model_library_action)

        # Reload stylesheet action
        view_menu.addSeparator()
        reload_stylesheet_action = QAction("&Reload Stylesheet", self.main_window)
        reload_stylesheet_action.setStatusTip("Reload and apply the main stylesheet")
        reload_stylesheet_action.triggered.connect(self._reload_stylesheet_action)
        view_menu.addAction(reload_stylesheet_action)

        # Layout Edit Mode toggle
        view_menu.addSeparator()
        self.toggle_layout_edit_action = QAction("Layout Edit Mode", self.main_window)
        self.toggle_layout_edit_action.setCheckable(True)
        try:
            self.toggle_layout_edit_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        except Exception:
            pass
        self.toggle_layout_edit_action.setStatusTip("Enable rearranging docks. When off, docks are locked in place but still resize with the window.")
        self.toggle_layout_edit_action.setToolTip("Toggle Layout Edit Mode (Ctrl+Shift+E)")
        self.toggle_layout_edit_action.toggled.connect(self._set_layout_edit_mode)
        view_menu.addAction(self.toggle_layout_edit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Generate screenshots action
        generate_screenshots_action = QAction("Generate &Screenshots for Library", self.main_window)
        generate_screenshots_action.setStatusTip("Generate screenshots of all models in the library with applied materials")
        generate_screenshots_action.triggered.connect(self._generate_library_screenshots)
        tools_menu.addAction(generate_screenshots_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Tips & Tricks action
        tips_action = QAction("&Tips & Tricks", self.main_window)
        tips_action.setStatusTip("View helpful tips and tutorials")
        tips_action.triggered.connect(self._show_tips)
        help_menu.addAction(tips_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("&About Digital Workshop", self.main_window)
        about_action.setStatusTip("Show information about Digital Workshop")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # qt-material handles menubar styling automatically
        self.logger.debug("Menu bar setup completed")

    def _apply_bar_palettes(self) -> None:
        """Apply palette colors (no-op - qt-material handles this)."""
        pass

    # Action handler methods (these would need to be connected to actual implementations)
    def _open_model(self) -> None:
        """Handle open model action."""
        # This would need to be connected to the main window's model loading logic
        if hasattr(self.main_window, '_open_model'):
            self.main_window._open_model()

    def _edit_model(self) -> None:
        """Handle edit model action."""
        if hasattr(self.main_window, '_edit_model'):
            self.main_window._edit_model()

    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        if hasattr(self.main_window, '_show_preferences'):
            self.main_window._show_preferences()

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

    def _save_current_view(self) -> None:
        """Handle save current view action."""
        if hasattr(self.main_window, '_save_current_view'):
            self.main_window._save_current_view()

    def _reset_dock_layout(self) -> None:
        """Handle reset dock layout action."""
        if hasattr(self.main_window, '_reset_dock_layout'):
            self.main_window._reset_dock_layout()

    def _restore_metadata_manager(self) -> None:
        """Handle restore metadata manager action."""
        if hasattr(self.main_window, '_restore_metadata_manager'):
            self.main_window._restore_metadata_manager()

    def _restore_model_library(self) -> None:
        """Handle restore model library action."""
        if hasattr(self.main_window, '_restore_model_library'):
            self.main_window._restore_model_library()

    def _reload_stylesheet_action(self) -> None:
        """Handle reload stylesheet action."""
        if hasattr(self.main_window, '_reload_stylesheet_action'):
            self.main_window._reload_stylesheet_action()

    def _set_layout_edit_mode(self, enabled: bool) -> None:
        """Handle layout edit mode toggle."""
        if hasattr(self.main_window, '_set_layout_edit_mode'):
            self.main_window._set_layout_edit_mode(enabled)

    def _show_tips(self) -> None:
        """Show tips and tricks dialog."""
        try:
            from src.gui.walkthrough import WalkthroughDialog
            dialog = WalkthroughDialog(self.main_window)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to show tips dialog: {e}")

    def _show_about(self) -> None:
        """Handle show about action."""
        if hasattr(self.main_window, '_show_about'):
            self.main_window._show_about()

    def _generate_library_screenshots(self) -> None:
        """Handle generate library screenshots action."""
        if hasattr(self.main_window, '_generate_library_screenshots'):
            self.main_window._generate_library_screenshots()


# Convenience function for easy menu setup
def setup_main_window_menus(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> MenuManager:
    """
    Convenience function to set up menus for a main window.

    Args:
        main_window: The main window to set up menus for
        logger: Optional logger instance

    Returns:
        MenuManager instance for further menu operations
    """
    manager = MenuManager(main_window, logger)
    manager.setup_menu_bar()
    return manager
