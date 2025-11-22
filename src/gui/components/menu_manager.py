"""
Menu Bar Management Module

This module handles the creation and management of the application's menu bar,
including file operations, view controls, and help menus.

Classes:
    MenuManager: Main class for managing menu bar functionality
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import QMainWindow, QStyle


class MenuManager:
    """
    Manages the application's menu bar and all associated menu actions.

    This class handles the creation of menus, actions, and their connections
    to provide a complete menu system for the main window.
    """

    def __init__(
        self,
        main_window: QMainWindow,
        logger: Optional[logging.Logger] = None,
        handlers: Optional[object] = None,
    ) -> None:
        """
        Initialize the menu manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)
        self.handlers = handlers or main_window

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

        style = self.main_window.style()

        def _std_icon(standard_pixmap) -> QIcon:
            """Return a native Qt icon for the given standard pixmap."""
            try:
                return style.standardIcon(standard_pixmap)
            except Exception:
                return QIcon()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open action
        open_action = QAction("&Open Model...", self.main_window)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a 3D model file")
        open_action.setIcon(_std_icon(QStyle.SP_DirOpenIcon))
        open_action.triggered.connect(self._call("import_models"))
        file_menu.addAction(open_action)

        # Import Models action
        import_action = QAction("&Import Models...", self.main_window)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.setStatusTip("Import 3D models into the library")
        import_action.setIcon(_std_icon(QStyle.SP_FileDialogNewFolder))
        import_action.triggered.connect(self._call("import_models"))
        file_menu.addAction(import_action)

        import_url_action = QAction("Import from &URL...", self.main_window)
        import_url_action.setStatusTip(
            "Download a model from a URL and add it to the library"
        )
        import_url_action.setIcon(_std_icon(QStyle.SP_ArrowDown))
        import_url_action.triggered.connect(self._call("open_import_from_url_dialog"))
        file_menu.addAction(import_url_action)

        rebuild_action = QAction("Rebuild Managed Library...", self.main_window)
        rebuild_action.setStatusTip(
            "Scan the managed Projects folder and re-import existing files into the database"
        )
        rebuild_action.setIcon(_std_icon(QStyle.SP_FileDialogContentsView))
        rebuild_action.triggered.connect(self._call("start_library_rebuild"))
        file_menu.addAction(rebuild_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self.main_window)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")

        # Analyze Model action
        self.edit_model_action = QAction("&Analyze & Fix Errors...", self.main_window)
        self.edit_model_action.setStatusTip("Analyze model for errors and fix them")
        self.edit_model_action.setIcon(_std_icon(QStyle.SP_DialogApplyButton))
        self.edit_model_action.setEnabled(False)
        self.edit_model_action.triggered.connect(self._call("edit_model"))
        edit_menu.addAction(self.edit_model_action)

        edit_menu.addSeparator()

        # Preferences action
        prefs_action = QAction("&Preferences...", self.main_window)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.setIcon(_std_icon(QStyle.SP_FileDialogDetailedView))
        prefs_action.triggered.connect(self._call("show_preferences"))
        edit_menu.addAction(prefs_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self.main_window)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in on the 3D view")
        zoom_in_action.setIcon(_std_icon(QStyle.SP_ArrowUp))
        zoom_in_action.triggered.connect(self._call("zoom_in"))
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self.main_window)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out from the 3D view")
        zoom_out_action.setIcon(_std_icon(QStyle.SP_ArrowDown))
        zoom_out_action.triggered.connect(self._call("zoom_out"))
        view_menu.addAction(zoom_out_action)

        view_menu.addSeparator()

        # Reset view action
        reset_view_action = QAction("&Reset View", self.main_window)
        reset_view_action.setStatusTip("Reset the 3D view to default")
        reset_view_action.setIcon(_std_icon(QStyle.SP_BrowserReload))
        reset_view_action.triggered.connect(self._call("reset_view"))
        view_menu.addAction(reset_view_action)

        # Save view action
        save_view_action = QAction("&Save View", self.main_window)
        save_view_action.setShortcut(QKeySequence("Ctrl+S"))
        save_view_action.setStatusTip("Save current camera view for this model")
        save_view_action.setIcon(_std_icon(QStyle.SP_DialogSaveButton))
        save_view_action.triggered.connect(self._call("save_current_view"))
        view_menu.addAction(save_view_action)

        # Reset dock layout action (helps when a floating dock is hard to re-dock)
        reset_layout_action = QAction("Reset &Layout", self.main_window)
        reset_layout_action.setStatusTip("Restore default dock layout")
        reset_layout_action.setIcon(_std_icon(QStyle.SP_DialogResetButton))
        reset_layout_action.triggered.connect(self._call("reset_dock_layout"))
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
        self.show_metadata_action.setIcon(_std_icon(QStyle.SP_FileDialogInfoView))
        self.show_metadata_action.triggered.connect(
            self._call("restore_metadata_manager")
        )
        view_menu.addAction(self.show_metadata_action)

        # Model Library restoration action
        self.show_model_library_action = QAction(
            "Show &Model Library", self.main_window
        )
        try:
            self.show_model_library_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        except Exception:
            pass
        self.show_model_library_action.setStatusTip("Restore the Model Library panel")
        self.show_model_library_action.setToolTip(
            "Show the Model Library (Ctrl+Shift+L)"
        )
        self.show_model_library_action.setIcon(_std_icon(QStyle.SP_DirIcon))
        self.show_model_library_action.triggered.connect(
            self._call("restore_model_library")
        )
        view_menu.addAction(self.show_model_library_action)

        # Reload stylesheet action
        view_menu.addSeparator()
        reload_stylesheet_action = QAction("&Reload Stylesheet", self.main_window)
        reload_stylesheet_action.setStatusTip("Reload and apply the main stylesheet")
        reload_stylesheet_action.setIcon(_std_icon(QStyle.SP_BrowserReload))
        reload_stylesheet_action.triggered.connect(
            self._call("reload_stylesheet_action")
        )
        view_menu.addAction(reload_stylesheet_action)

        # Layout Edit Mode toggle
        view_menu.addSeparator()
        self.toggle_layout_edit_action = QAction("Layout Edit Mode", self.main_window)
        self.toggle_layout_edit_action.setCheckable(True)
        try:
            self.toggle_layout_edit_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        except Exception:
            pass
        self.toggle_layout_edit_action.setStatusTip(
            "Enable rearranging docks. When off, docks are locked in place but still resize with the window."
        )
        self.toggle_layout_edit_action.setToolTip(
            "Toggle Layout Edit Mode (Ctrl+Shift+E)"
        )
        self.toggle_layout_edit_action.setIcon(_std_icon(QStyle.SP_TitleBarShadeButton))
        self.toggle_layout_edit_action.toggled.connect(
            self._call("set_layout_edit_mode")
        )
        view_menu.addAction(self.toggle_layout_edit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Generate thumbnails action
        generate_thumbnails_action = QAction(
            "Generate &Thumbnails for Library", self.main_window
        )
        generate_thumbnails_action.setStatusTip(
            "Generate thumbnails for all models in the library with applied materials"
        )
        generate_thumbnails_action.setIcon(_std_icon(QStyle.SP_MediaPlay))
        generate_thumbnails_action.triggered.connect(
            self._call("generate_library_screenshots")
        )
        tools_menu.addAction(generate_thumbnails_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Tips & Tricks action
        tips_action = QAction("&Tips & Tricks", self.main_window)
        tips_action.setStatusTip("View helpful tips and tutorials")
        tips_action.setIcon(_std_icon(QStyle.SP_MessageBoxInformation))
        tips_action.triggered.connect(self._call("show_tips"))
        help_menu.addAction(tips_action)

        help_menu.addSeparator()

        # License / Activation
        license_action = QAction("Activate &AI Service...", self.main_window)
        license_action.setStatusTip(
            "Enter license key to enable hosted AI descriptions"
        )
        license_action.setIcon(_std_icon(QStyle.SP_DialogYesButton))
        license_action.triggered.connect(self._call("show_license_dialog"))
        help_menu.addAction(license_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("&About Digital Workshop", self.main_window)
        about_action.setStatusTip("Show information about Digital Workshop")
        about_action.setIcon(_std_icon(QStyle.SP_MessageBoxInformation))
        about_action.triggered.connect(self._call("show_about"))
        help_menu.addAction(about_action)

        # qt-material handles menubar styling automatically
        self.logger.debug("Menu bar setup completed")

    def _apply_bar_palettes(self) -> None:
        """Apply palette colors (no-op - qt-material handles this)."""

    def _call(self, name: str):
        """Return a callable that forwards to handlers if present."""

        def _wrapper(*args, **kwargs):
            target = getattr(self.handlers, name, None)
            if callable(target):
                target(*args, **kwargs)

        return _wrapper


# Convenience function for easy menu setup
def setup_main_window_menus(
    main_window: QMainWindow,
    logger: Optional[logging.Logger] = None,
    handlers: Optional[object] = None,
) -> MenuManager:
    """
    Convenience function to set up menus for a main window.

    Args:
        main_window: The main window to set up menus for
        logger: Optional logger instance

    Returns:
        MenuManager instance for further menu operations
    """
    manager = MenuManager(main_window, logger, handlers=handlers)
    manager.setup_menu_bar()
    return manager
