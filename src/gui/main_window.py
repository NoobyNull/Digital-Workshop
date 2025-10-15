"""
Main window implementation for 3D-MM application.

This module provides the main application window with menu bar, toolbar,
status bar, and dockable widgets for 3D model management.
"""

import logging
import sys
import json
import base64
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QSize, QTimer, Signal, QStandardPaths, QSettings
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QTextEdit,
    QFrame, QSplitter, QFileDialog, QMessageBox, QProgressBar, QTabWidget
)

from core.logging_config import get_logger
from core.database_manager import get_database_manager
from parsers.stl_parser import STLParser, STLProgressCallback
from gui.theme import COLORS, ThemeManager, qss_tabs_lists_labels, SPACING_4, SPACING_8, SPACING_12, SPACING_16, SPACING_24
from gui.preferences import PreferencesDialog
from gui.lighting_control_panel import LightingControlPanel
from gui.lighting_manager import LightingManager
from gui.material_manager import MaterialManager

class MainWindow(QMainWindow):
    """
    Main application window for 3D Model Manager.
    
    Provides the primary interface with menu bar, toolbar, status bar,
    and dockable widgets for model management and 3D visualization.
    """
    
    # Custom signals for application events
    model_loaded = Signal(str)  # Emitted when a model is loaded
    model_selected = Signal(int)  # Emitted when a model is selected
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget (typically None for main window)
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing main window")
        
        # Window properties
        self.setWindowTitle("3D-MM - 3D Model Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)  # Default size for desktop
        
        # Initialize UI components
        self._init_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_dock_widgets()
        self._setup_central_widget()
        
        # Set up status update timer
        self._setup_status_timer()
        
        # Log window initialization
        self.logger.info("Main window initialized successfully")
    
    def _init_ui(self) -> None:
        """Initialize basic UI properties and styling."""
        # Set window icon if available
        # self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        
        # Set application style for Windows desktop
        QApplication.setStyle("Fusion")  # Modern look and feel
        
        # Enable dock widget features for better layout management
        options = (
            QMainWindow.AllowNestedDocks |
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AnimatedDocks
        )
        # Grouped dragging (if available) improves docking behavior when tabs are involved
        if hasattr(QMainWindow, "GroupedDragging"):
            options |= QMainWindow.GroupedDragging
        self.setDockOptions(options)
        # Explicitly enable nesting (no-op on some styles, harmless)
        try:
            self.setDockNestingEnabled(True)
        except Exception:
            pass
        
        # Set central widget background using theme variables (spacing aligned to theme scale)
        # Base theme stylesheet
        base_qss = f"""
            QMainWindow {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QDockWidget {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                font-weight: bold;
            }}
            QDockWidget::title {{
                background-color: {COLORS.dock_title_bg};
                padding: {SPACING_12}px {SPACING_16}px;
                border-bottom: 1px solid {COLORS.dock_title_border};
                color: {COLORS.text};
                font-weight: 600;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QDockWidget::title:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLORS.hover},
                                            stop:1 {COLORS.surface});
            }}
            QDockWidget::close-button, QDockWidget::float-button {{
                border: 1px solid transparent;
                background: transparent;
                margin: 2px;
                padding: 2px;
                border-radius: 3px;
            }}
            QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
                background: {COLORS.hover};
                border: 1px solid {COLORS.border};
            }}
            QToolBar {{
                background-color: {COLORS.toolbar_bg};
                border: 1px solid {COLORS.toolbar_border};
                spacing: {SPACING_8}px;
                color: {COLORS.text};
            }}
            QMenuBar {{
                background-color: {COLORS.menubar_bg};
                color: {COLORS.menubar_text};
                border-bottom: 1px solid {COLORS.menubar_border};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: {SPACING_4}px {SPACING_8}px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS.menubar_item_hover_bg};
                color: {COLORS.menubar_item_hover_text};
            }}
            QStatusBar {{
                background-color: {COLORS.statusbar_bg};
                color: {COLORS.statusbar_text};
                border-top: 1px solid {COLORS.statusbar_border};
            }}
            QLabel {{
                color: {COLORS.text};
            }}
            QPushButton {{
                background-color: {COLORS.surface};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: {SPACING_8}px {SPACING_16}px;
                border-radius: 2px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
        """
        # Apply ThemeManager-managed external stylesheet, then append base_qss
        try:
            tm = ThemeManager.instance()
            css_abs_path = str(Path(__file__).resolve().parents[1] / "resources" / "styles" / "main_window.css")
            tm.register_widget(self, css_path=css_abs_path)
            tm.apply_stylesheet(self)
            # Append base_qss overrides
            self.setStyleSheet(self.styleSheet() + "\n" + base_qss)
        except Exception:
            # Fallback: apply base_qss only
            self.setStyleSheet(base_qss)
        # Notify via status bar for visible validation
        try:
            self.statusBar().showMessage("Applied main_window.css", 2000)
        except Exception:
            pass
        # Apply extended theme styling and confirm
        try:
            self._apply_theme_styles()
            self.statusBar().showMessage("Modern UI styling applied", 2500)
        except Exception:
            pass
    
    def _apply_theme_styles(self) -> None:
        """Apply theme to MainWindow and child widgets."""
        # Main window, menus, docks, labels, buttons (spacing aligned to theme scale)
        # Base theme stylesheet
        base_qss = f"""
            QMainWindow {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QDockWidget {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                font-weight: bold;
            }}
            QDockWidget::title {{
                background-color: {COLORS.dock_title_bg};
                padding: {SPACING_12}px {SPACING_16}px;
                border-bottom: 1px solid {COLORS.dock_title_border};
                color: {COLORS.text};
                font-weight: 600;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QDockWidget::title:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLORS.hover},
                                            stop:1 {COLORS.surface});
            }}
            QDockWidget::close-button, QDockWidget::float-button {{
                border: 1px solid transparent;
                background: transparent;
                margin: 2px;
                padding: 2px;
                border-radius: 3px;
            }}
            QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
                background: {COLORS.hover};
                border: 1px solid {COLORS.border};
            }}
            QToolBar {{
                background-color: {COLORS.toolbar_bg};
                border: 1px solid {COLORS.toolbar_border};
                spacing: {SPACING_8}px;
                color: {COLORS.text};
            }}
            QMenuBar {{
                background-color: {COLORS.menubar_bg};
                color: {COLORS.menubar_text};
                border-bottom: 1px solid {COLORS.menubar_border};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: {SPACING_4}px {SPACING_8}px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS.menubar_item_hover_bg};
                color: {COLORS.menubar_item_hover_text};
            }}
            QStatusBar {{
                background-color: {COLORS.statusbar_bg};
                color: {COLORS.statusbar_text};
                border-top: 1px solid {COLORS.statusbar_border};
            }}
            QLabel {{
                color: {COLORS.text};
            }}
            QPushButton {{
                background-color: {COLORS.surface};
                color: {COLORS.text};
                border: 1px solid {COLORS.border};
                padding: {SPACING_8}px {SPACING_16}px;
                border-radius: 2px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
        """
        # Re-apply ThemeManager stylesheet and append base_qss
        try:
            tm = ThemeManager.instance()
            tm.apply_stylesheet(self)
            self.setStyleSheet(self.styleSheet() + "\n" + base_qss)
            # Ensure child bars and dock headers re-apply their own registered styles
            try:
                if hasattr(self, "status_bar") and self.status_bar is not None:
                    tm.apply_stylesheet(self.status_bar)
                mb = self.menuBar()
                if mb is not None:
                    tm.apply_stylesheet(mb)
                if hasattr(self, "main_toolbar") and self.main_toolbar is not None:
                    tm.apply_stylesheet(self.main_toolbar)
                if hasattr(self, "model_library_dock"):
                    tm.apply_stylesheet(self.model_library_dock)
                if hasattr(self, "properties_dock"):
                    tm.apply_stylesheet(self.properties_dock)
                if hasattr(self, "metadata_dock"):
                    tm.apply_stylesheet(self.metadata_dock)
                # Also apply palette to force background paints on platforms that ignore QSS for bars
                self._apply_bar_palettes()
            except Exception:
                pass
        except Exception:
            self.setStyleSheet(base_qss)
        # Notify via status bar for visible validation
        try:
            self.statusBar().showMessage("Applied main_window.css", 2000)
            # Debug: log currently applied bar colors to diagnose any swaps
            try:
                tm = ThemeManager.instance()
                self.logger.debug(
                    f"Theme bars apply: menubar_bg={tm.get_color('menubar_bg')}, "
                    f"statusbar_bg={tm.get_color('statusbar_bg')}, dock_title_bg={tm.get_color('dock_title_bg')}"
                )
            except Exception:
                pass
        except Exception:
            pass
        # Propagate to known child widgets that support re-styling
        try:
            if hasattr(self, "model_library_widget") and hasattr(self.model_library_widget, "_apply_styling"):
                self.model_library_widget._apply_styling()
        except Exception:
            pass
        try:
            if hasattr(self, "metadata_editor") and hasattr(self.metadata_editor, "_apply_styling"):
                self.metadata_editor._apply_styling()
        except Exception:
            pass
        try:
            if hasattr(self, "viewer_widget") and hasattr(self.viewer_widget, "apply_theme"):
                self.viewer_widget.apply_theme()
        except Exception:
            pass

    def _load_external_stylesheet(self) -> None:
        """Append external CSS from resources/styles/main_window.css to current stylesheet."""
        css_path = Path(__file__).resolve().parents[1] / "resources" / "styles" / "main_window.css"
        try:
            self.logger.info(f"External CSS path: {css_path}")
            self.logger.info(f"External CSS exists: {css_path.exists()}")
            if not css_path.exists():
                return
            with css_path.open("r", encoding="utf-8") as f:
                css = f.read()
            if css:
                self.setStyleSheet(self.styleSheet() + "\n" + css)
        except Exception as e:
            self.logger.warning(f"Failed to load external CSS from {css_path}: {e}")

    def _setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        self.logger.debug("Setting up menu bar")
        
        menubar = self.menuBar()
        try:
            menubar.setObjectName("AppMenuBar")
            menubar.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open action
        open_action = QAction("&Open Model...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a 3D model file")
        open_action.triggered.connect(self._open_model)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Preferences action
        prefs_action = QAction("&Preferences...", self)
        prefs_action.setStatusTip("Open application preferences")
        prefs_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(prefs_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in on the 3D view")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out from the 3D view")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        # Reset view action
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.setStatusTip("Reset the 3D view to default")
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)

        # Reset dock layout action (helps when a floating dock is hard to re-dock)
        reset_layout_action = QAction("Reset &Layout", self)
        reset_layout_action.setStatusTip("Restore default dock layout")
        reset_layout_action.triggered.connect(self._reset_dock_layout)
        view_menu.addAction(reset_layout_action)

        # Reload stylesheet action
        view_menu.addSeparator()
        reload_stylesheet_action = QAction("&Reload Stylesheet", self)
        reload_stylesheet_action.setStatusTip("Reload and apply the main stylesheet")
        reload_stylesheet_action.triggered.connect(self._reload_stylesheet_action)
        view_menu.addAction(reload_stylesheet_action)

        # Theme Manager
        theme_manager_action = QAction("Theme Manager...", self)
        theme_manager_action.setStatusTip("Open Theme Manager")
        theme_manager_action.triggered.connect(self._show_theme_manager)
        view_menu.addAction(theme_manager_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About 3D-MM", self)
        about_action.setStatusTip("Show information about 3D-MM")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # Register explicit menubar stylesheet with ThemeManager to ensure updates on preset changes
        try:
            tm = ThemeManager.instance()
            _menubar_css = """
                QMenuBar#AppMenuBar {
                    background-color: {{menubar_bg}};
                    color: {{menubar_text}};
                    border-bottom: 1px solid {{menubar_border}};
                    padding: 2px;
                    spacing: 2px;
                }
                QMenuBar#AppMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    border-radius: 2px;
                    margin: 1px;
                }
                QMenuBar#AppMenuBar::item:selected {
                    background-color: {{menubar_item_hover_bg}};
                    color: {{menubar_item_hover_text}};
                }
                QMenuBar#AppMenuBar::item:pressed {
                    background-color: {{menubar_item_pressed_bg}};
                }
            """
            tm.register_widget(menubar, css_text=_menubar_css)
            tm.apply_stylesheet(menubar)
            # Also apply palettes to ensure native menubar paints themed background
            self._apply_bar_palettes()
            # Debug: log applied colors to identify unexpected cross-assignments
            try:
                self.logger.debug(
                    f"Bars styled: menubar_bg={tm.get_color('menubar_bg')}, "
                    f"statusbar_bg={tm.get_color('statusbar_bg')}"
                )
            except Exception:
                pass
        except Exception:
            pass

        self.logger.debug("Menu bar setup completed")
    
    def _setup_toolbar(self) -> None:
        """Set up the main application toolbar with icons and fallbacks."""
        self.logger.debug("Setting up toolbar")

        self.main_toolbar = self.addToolBar("Main")
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
                action = QAction(_icon(icon_name), text, self)
            else:
                action = QAction(text, self)
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

        # Show toolbar mode in status bar for immediate visual feedback
        try:
            if icons_ok:
                self.statusBar().showMessage("Toolbar icons active", 2000)
            else:
                self.statusBar().showMessage("Toolbar text-only (no qtawesome)", 2000)
        except Exception:
            pass

        self.logger.debug("Toolbar setup completed")
    
    def _setup_status_bar(self) -> None:
        """Set up the application status bar."""
        self.logger.debug("Setting up status bar")
        
        self.status_bar = QStatusBar()
        # Give the bar a stable objectName so we can target it precisely in QSS
        try:
            self.status_bar.setObjectName("AppStatusBar")
        except Exception:
            pass

        self.setStatusBar(self.status_bar)
        # Make sure the bar paints its background, some styles require this for QSS background-color to take effect
        try:
            self.status_bar.setAutoFillBackground(True)
            self.status_bar.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass

        # Apply ThemeManager-managed inline stylesheet specifically for QStatusBar so it always participates in theming
        try:
            tm = ThemeManager.instance()
            _statusbar_css = """
                QStatusBar#AppStatusBar {
                    background-color: {{statusbar_bg}};
                    color: {{statusbar_text}};
                    border-top: 1px solid {{statusbar_border}};
                    padding: 2px;
                }
                QStatusBar#AppStatusBar::item {
                    border: none;
                }
            """
            tm.register_widget(self.status_bar, css_text=_statusbar_css)
            tm.apply_stylesheet(self.status_bar)
        except Exception:
            # Non-fatal styling path
            pass
        
        # Permanent status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Memory usage indicator
        self.memory_label = QLabel("Memory: N/A")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        self.logger.debug("Status bar setup completed")

    def _apply_bar_palettes(self) -> None:
        """
        Force palette-based colors for menu/status bars to ensure background
        paints even when style engine ignores QSS for these native widgets.
        """
        try:
            tm = ThemeManager.instance()
            # Status bar
            if hasattr(self, "status_bar") and self.status_bar is not None:
                sp = self.status_bar.palette()
                sp.setColor(QPalette.Window, tm.qcolor("statusbar_bg"))
                sp.setColor(QPalette.WindowText, tm.qcolor("statusbar_text"))
                self.status_bar.setPalette(sp)
                self.status_bar.setAutoFillBackground(True)
            # Menu bar
            mb = self.menuBar()
            if mb is not None:
                mp = mb.palette()
                mp.setColor(QPalette.Window, tm.qcolor("menubar_bg"))
                mp.setColor(QPalette.WindowText, tm.qcolor("menubar_text"))
                mb.setPalette(mp)
                mb.setAutoFillBackground(True)
            # Toolbar palette
            if hasattr(self, "main_toolbar") and self.main_toolbar is not None:
                tp = self.main_toolbar.palette()
                tp.setColor(QPalette.Window, tm.qcolor("toolbar_bg"))
                tp.setColor(QPalette.WindowText, tm.qcolor("text"))
                self.main_toolbar.setPalette(tp)
                self.main_toolbar.setAutoFillBackground(True)
        except Exception:
            # Never break UI if palette application fails
            pass
    
    def _setup_dock_widgets(self) -> None:
        """Set up dockable widgets for the application."""
        self.logger.debug("Setting up dock widgets")
        
        # Model library dock (left side)
        self.model_library_dock = QDockWidget("Model Library", self)
        self.model_library_dock.setObjectName("ModelLibraryDock")
        self.model_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.model_library_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        
        # Create model library widget
        try:
            from gui.model_library import ModelLibraryWidget
            self.model_library_widget = ModelLibraryWidget(self)
            
            # Connect signals
            self.model_library_widget.model_selected.connect(self._on_model_selected)
            self.model_library_widget.model_double_clicked.connect(self._on_model_double_clicked)
            self.model_library_widget.models_added.connect(self._on_models_added)
            
            self.model_library_dock.setWidget(self.model_library_widget)
            # Add context menu helpers for docking
            try:
                self._setup_dock_context_menu(self.model_library_dock, Qt.LeftDockWidgetArea)
            except Exception:
                pass
            # Ensure dock header uses theme variables regardless of global QSS ordering
            try:
                tm = ThemeManager.instance()
                _dock_css_ml = """
                    QDockWidget#ModelLibraryDock::title {
                        background-color: {{dock_title_bg}};
                        color: {{text}};
                        border-bottom: 1px solid {{dock_title_border}};
                        padding: 6px;
                    }
                """
                tm.register_widget(self.model_library_dock, css_text=_dock_css_ml)
                tm.apply_stylesheet(self.model_library_dock)
            except Exception:
                pass
            self.logger.info("Model library widget created successfully")
            
        except ImportError as e:
            self.logger.warning(f"Failed to import model library widget: {str(e)}")
            
            # Fallback to placeholder
            model_library_widget = QTextEdit()
            model_library_widget.setReadOnly(True)
            model_library_widget.setPlainText(
                "Model Library\n\n"
                "Failed to load model library component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Model list with thumbnails\n"
                "- Category filtering\n"
                "- Search functionality\n"
                "- Import/export options"
            )
            self.model_library_dock.setWidget(model_library_widget)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.model_library_dock)
        except Exception:
            pass
        
        # Properties dock (right side)
        self.properties_dock = QDockWidget("Model Properties", self)
        self.properties_dock.setObjectName("PropertiesDock")
        self.properties_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.properties_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        
        # Placeholder for model properties
        properties_widget = QTextEdit()
        properties_widget.setReadOnly(True)
        properties_widget.setPlainText(
            "Model Properties\n\n"
            "This panel will display properties and metadata\n"
            "for the selected 3D model.\n"
            "Features will include:\n"
            "- Model information\n"
            "- Metadata editing\n"
            "- Tag management\n"
            "- Export settings"
        )
        self.properties_dock.setWidget(properties_widget)
        try:
            self._setup_dock_context_menu(self.properties_dock, Qt.RightDockWidgetArea)
        except Exception:
            pass
        # Ensure properties dock header uses theme variables
        try:
            tm = ThemeManager.instance()
            _dock_css_props = """
                QDockWidget#PropertiesDock::title {
                    background-color: {{dock_title_bg}};
                    color: {{text}};
                    border-bottom: 1px solid {{dock_title_border}};
                    padding: 6px;
                }
            """
            tm.register_widget(self.properties_dock, css_text=_dock_css_props)
            tm.apply_stylesheet(self.properties_dock)
        except Exception:
            pass
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.properties_dock)
        except Exception:
            pass

        # Lighting control dock (right side, initially hidden)
        try:
            self.lighting_panel = LightingControlPanel(self)
            self.lighting_panel.setObjectName("LightingDock")
            self.lighting_panel.setVisible(False)
            self.addDockWidget(Qt.RightDockWidgetArea, self.lighting_panel)
            # Autosave when lighting dock changes state/position
            self._connect_layout_autosave(self.lighting_panel)
            # Persist panel visibility via QSettings
            try:
                self.lighting_panel.visibilityChanged.connect(lambda _=False: self._save_lighting_panel_visibility())
            except Exception:
                pass
            # TODO: Add support for multiple light sources
        except Exception as e:
            self.logger.warning(f"Failed to create LightingControlPanel: {e}")
         
        # Metadata dock (bottom)
        self.metadata_dock = QDockWidget("Metadata Editor", self)
        self.metadata_dock.setObjectName("MetadataDock")
        self.metadata_dock.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        self.metadata_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        
        # Create metadata editor widget and wrap in a bottom tab bar for reduced clutter
        try:
            from gui.metadata_editor import MetadataEditorWidget
            self.metadata_editor = MetadataEditorWidget(self)

            # Connect signals
            self.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
            self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)

            # Bottom tabs: Metadata | Notes | History
            self.metadata_tabs = QTabWidget(self)
            self.metadata_tabs.setObjectName("MetadataTabs")
            self.metadata_tabs.addTab(self.metadata_editor, "Metadata")

            # Notes tab (placeholder)
            notes_widget = QTextEdit()
            notes_widget.setReadOnly(True)
            notes_widget.setPlainText(
                "Notes\n\n"
                "Add project or model-specific notes here.\n"
                "Future: rich text, timestamps, and attachments."
            )
            self.metadata_tabs.addTab(notes_widget, "Notes")

            # History tab (placeholder)
            history_widget = QTextEdit()
            history_widget.setReadOnly(True)
            history_widget.setPlainText(
                "History\n\n"
                "Timeline of edits and metadata changes will appear here."
            )
            self.metadata_tabs.addTab(history_widget, "History")

            # Apply themed styling to the tab widget
            try:
                self.metadata_tabs.setStyleSheet(qss_tabs_lists_labels())
            except Exception:
                pass

            self.metadata_dock.setWidget(self.metadata_tabs)
            try:
                self._setup_dock_context_menu(self.metadata_dock, Qt.BottomDockWidgetArea)
            except Exception:
                pass
            # Ensure metadata dock header uses theme variables
            try:
                tm = ThemeManager.instance()
                _dock_css_meta = """
                    QDockWidget#MetadataDock::title {
                        background-color: {{dock_title_bg}};
                        color: {{text}};
                        border-bottom: 1px solid {{dock_title_border}};
                        padding: 6px;
                    }
                """
                tm.register_widget(self.metadata_dock, css_text=_dock_css_meta)
                tm.apply_stylesheet(self.metadata_dock)
            except Exception:
                pass
            self.logger.info("Metadata editor widget created successfully (tabbed)")
        except ImportError as e:
            self.logger.warning(f"Failed to import metadata editor widget: {str(e)}")

            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText(
                "Metadata Editor\n\n"
                "Failed to load metadata editor component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Title and description editing\n"
                "- Category assignment\n"
                "- Keyword tagging\n"
                "- Custom properties"
            )
            self.metadata_dock.setWidget(metadata_widget)
        
        self.addDockWidget(Qt.BottomDockWidgetArea, self.metadata_dock)
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.metadata_dock)
        except Exception:
            pass
        
        # Capture the default layout as the baseline for future resets
        try:
            self._save_default_layout_state()
        except Exception:
            pass

        # Initialize autosave mechanics and attempt to restore last layout
        try:
            self._init_layout_persistence()
            self._load_saved_layout()
        except Exception:
            pass
        # Load persisted lighting panel visibility (in addition to dock state)
        try:
            if hasattr(self, "lighting_panel") and self.lighting_panel:
                settings = QSettings()
                visible = settings.value('lighting_panel/visible', False, type=bool)
                self.lighting_panel.setVisible(bool(visible))
                self.logger.info(f"Loaded lighting panel visibility: {bool(visible)}")
        except Exception as e:
            self.logger.warning(f"Failed to load lighting panel visibility: {e}")
        self.logger.debug("Dock widgets setup completed")
    
    def _setup_central_widget(self) -> None:
        """Set up the central widget: viewer, or viewer + metadata tabs in a vertical splitter."""
        self.logger.debug("Setting up central widget")

        # Import the viewer widget
        try:
            # Try to import VTK-based viewer first
            try:
                from gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                # Fallback to original viewer if VTK is not available
                try:
                    from gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None

            # Create the 3D viewer widget
            self.viewer_widget = Viewer3DWidget(self)
 
            # Connect signals
            self.viewer_widget.model_loaded.connect(self._on_model_loaded)
            self.viewer_widget.performance_updated.connect(self._on_performance_updated)

            # Managers
            try:
                # Material manager with database
                self.material_manager = MaterialManager(get_database_manager())
            except Exception as e:
                self.material_manager = None
                self.logger.warning(f"MaterialManager unavailable: {e}")

            try:
                # Lighting manager with viewer renderer
                renderer = getattr(self.viewer_widget, "renderer", None)
                self.lighting_manager = LightingManager(renderer) if renderer is not None else None
                if self.lighting_manager:
                    self.lighting_manager.create_light()
                    # Load persisted lighting settings
                    try:
                        self._load_lighting_settings()
                    except Exception as le:
                        self.logger.warning(f"Failed to load lighting settings: {le}")
            except Exception as e:
                self.lighting_manager = None
                self.logger.warning(f"LightingManager unavailable: {e}")

            # Viewer integration signals
            if hasattr(self.viewer_widget, "lighting_panel_requested"):
                self.viewer_widget.lighting_panel_requested.connect(self._toggle_lighting_panel)
            if hasattr(self.viewer_widget, "material_selected"):
                self.viewer_widget.material_selected.connect(self._apply_material_species)

            # Connect lighting panel controls to manager
            try:
                if hasattr(self, "lighting_panel") and self.lighting_panel and self.lighting_manager:
                    self.lighting_panel.position_changed.connect(self._update_light_position)
                    self.lighting_panel.color_changed.connect(self._update_light_color)
                    self.lighting_panel.intensity_changed.connect(self._update_light_intensity)
                    # Sync panel with current manager values
                    props = self.lighting_manager.get_properties()
                    self.lighting_panel.set_values(
                        position=tuple(props.get("position", (100.0, 100.0, 100.0))),
                        color=tuple(props.get("color", (1.0, 1.0, 1.0))),
                        intensity=float(props.get("intensity", 0.8)),
                        emit_signals=False,
                    )
            except Exception as e:
                self.logger.warning(f"Failed to connect lighting panel: {e}")
 
            # Apply theme to viewer if supported
            if hasattr(self.viewer_widget, "apply_theme"):
                try:
                    self.viewer_widget.apply_theme()
                except Exception:
                    pass

            self.logger.info("3D viewer widget created successfully")

        except ImportError as e:
            self.logger.warning(f"Failed to import 3D viewer widget: {str(e)}")

            # Create fallback widget
            self.viewer_widget = QTextEdit()
            self.viewer_widget.setReadOnly(True)
            self.viewer_widget.setPlainText(
                "3D Model Viewer\n\n"
                "Failed to load 3D viewer component.\n"
                "Please ensure VTK or PyQt3D is properly installed.\n\n"
                "Features will include:\n"
                "- Interactive 3D model rendering\n"
                "- Multiple view modes (wireframe, solid, textured)\n"
                "- Camera controls (orbit, pan, zoom)\n"
                "- Lighting controls\n"
                "- Measurement tools\n"
                "- Animation playback\n"
                "- Screenshot capture"
            )
            self.viewer_widget.setAlignment(Qt.AlignCenter)

        # If metadata tabs exist, create a vertical splitter: viewer (top) | metadata tabs (bottom)
        if hasattr(self, "metadata_tabs") and isinstance(self.metadata_tabs, QTabWidget):
            try:
                splitter = QSplitter(Qt.Vertical)
                splitter.setObjectName("CentralVerticalSplitter")

                # Top: 3D viewer
                splitter.addWidget(self.viewer_widget)

                # Detach tabs from dock to avoid duplication, then add to splitter
                try:
                    if hasattr(self, "metadata_dock") and self.metadata_dock.widget() is self.metadata_tabs:
                        # Keep dock valid but empty to retain layout integrity; we'll hide it
                        self.metadata_dock.setWidget(QWidget())
                except Exception:
                    pass

                # Bottom: metadata tabs
                splitter.addWidget(self.metadata_tabs)

                # Stretch: viewer 3, metadata 1
                splitter.setStretchFactor(0, 3)
                splitter.setStretchFactor(1, 1)

                # Set as central widget
                self.setCentralWidget(splitter)

                # Restore splitter sizes if available
                try:
                    settings = self._read_settings_json()
                    sizes = settings.get("central_splitter_sizes")
                    if isinstance(sizes, list) and sizes:
                        splitter.setSizes([int(x) for x in sizes])
                except Exception:
                    pass

                # Hide the original metadata dock to avoid duplication
                try:
                    if hasattr(self, "metadata_dock"):
                        self.metadata_dock.hide()
                except Exception:
                    pass

                self.logger.debug("Central splitter setup completed")

            except Exception as e:
                self.logger.warning(f"Failed to set up central splitter, falling back to viewer only: {e}")
                self.setCentralWidget(self.viewer_widget)
        else:
            # No metadata tabs available, use viewer alone
            self.setCentralWidget(self.viewer_widget)

        self.logger.debug("Central widget setup completed")
    
    def _setup_status_timer(self) -> None:
        """Set up timer for periodic status updates."""
        # Update memory usage every 5 seconds
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # 5 seconds
        
        # Initial update
        self._update_status()
    
    def _update_status(self) -> None:
        """Update status bar information."""
        try:
            # Check if current status message is an important UI feedback message
            current_message = self.status_label.text()
            important_messages = [
                "Applied main_window.css",
                "Modern UI styling applied",
                "Stylesheet reloaded",
                "Toolbar icons active",
                "Loading:",
                "Metadata saved",
                "Added"
            ]

            # Don't override important UI feedback messages
            is_important = any(msg in current_message for msg in important_messages)
            if not is_important:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
        except ImportError:
            if self.status_label.text() not in ["Applied main_window.css", "Modern UI styling applied", "Stylesheet reloaded", "Toolbar icons active"]:
                self.memory_label.setText("Memory: N/A (psutil not available)")
        except Exception as e:
            self.logger.warning(f"Failed to update memory status: {str(e)}")
            if self.status_label.text() not in ["Applied main_window.css", "Modern UI styling applied", "Stylesheet reloaded", "Toolbar icons active"]:
                self.memory_label.setText("Memory: Error")
    
    # --- Dock layout helpers ---
    def _save_default_layout_state(self) -> None:
        """Save the default geometry/state for later restore."""
        try:
            self._default_layout_state = self.saveState()
            self._default_geometry = self.saveGeometry()
        except Exception:
            self._default_layout_state = None
            self._default_geometry = None

    def _reset_dock_layout(self) -> None:
        """Restore dock widgets to their default docking layout."""
        try:
            if getattr(self, "_default_geometry", None):
                self.restoreGeometry(self._default_geometry)
            if getattr(self, "_default_layout_state", None):
                # restoreState returns bool; ignore on failure
                self.restoreState(self._default_layout_state)
        except Exception:
            pass
        # Fallback: programmatically re-dock common widgets
        self._redock_all()
        # Persist the reset layout
        try:
            self._schedule_layout_save()
        except Exception:
            pass

    def _redock_all(self) -> None:
        """Force re-dock of known dock widgets to their default areas."""
        try:
            if hasattr(self, "model_library_dock"):
                self.model_library_dock.setFloating(False)
                self.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
            if hasattr(self, "properties_dock"):
                self.properties_dock.setFloating(False)
                self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
            if hasattr(self, "metadata_dock"):
                self.metadata_dock.setFloating(False)
                self.addDockWidget(Qt.BottomDockWidgetArea, self.metadata_dock)
        except Exception as e:
            self.logger.warning(f"Failed to re-dock widgets: {str(e)}")

    # ---- Layout persistence (auto-save/auto-load) ----
    def _settings_json_path(self) -> Path:
        """Return AppData settings.json path."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "settings.json"

    def _read_settings_json(self) -> dict:
        try:
            p = self._settings_json_path()
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _write_settings_json(self, data: dict) -> None:
        try:
            p = self._settings_json_path()
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _init_layout_persistence(self) -> None:
        """Initialize debounced autosave timer."""
        try:
            self._layout_save_timer = QTimer(self)
            self._layout_save_timer.setSingleShot(True)
            self._layout_save_timer.setInterval(700)  # ms debounce
            self._layout_save_timer.timeout.connect(self._save_current_layout)
        except Exception:
            pass

    def _schedule_layout_save(self) -> None:
        """Request a debounced layout save."""
        try:
            if hasattr(self, "_layout_save_timer"):
                self._layout_save_timer.start()
        except Exception:
            pass

    def _save_current_layout(self) -> None:
        """Persist current window geometry, dock layout, and central splitter sizes to settings.json."""
        try:
            geom = bytes(self.saveGeometry())
            state = bytes(self.saveState())

            # Persist base window geometry/state
            payload = {
                "window_geometry": base64.b64encode(geom).decode("ascii"),
                "window_state": base64.b64encode(state).decode("ascii"),
                "layout_version": 1,
            }

            # Persist central splitter sizes if applicable
            try:
                cw = self.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = cw.sizes()
                    if sizes:
                        payload["central_splitter_sizes"] = [int(s) for s in sizes]
            except Exception:
                pass

            settings = self._read_settings_json()
            settings.update(payload)
            self._write_settings_json(settings)
            self.logger.debug("Layout autosaved")
        except Exception as e:
            self.logger.warning(f"Failed to save current layout: {e}")

    def _load_saved_layout(self) -> bool:
        """Restore previously saved layout from settings.json. Returns True if successful."""
        try:
            settings = self._read_settings_json()
            g64 = settings.get("window_geometry")
            s64 = settings.get("window_state")
            ok_any = False
            if g64:
                try:
                    geom = base64.b64decode(g64)
                    ok_any = self.restoreGeometry(geom) or ok_any
                except Exception:
                    pass
            if s64:
                try:
                    state = base64.b64decode(s64)
                    ok_any = self.restoreState(state) or ok_any
                except Exception:
                    pass

            # If central is already a splitter, restore sizes
            try:
                cw = self.centralWidget()
                if isinstance(cw, QSplitter):
                    sizes = settings.get("central_splitter_sizes")
                    if isinstance(sizes, list) and sizes:
                        cw.setSizes([int(s) for s in sizes])
            except Exception:
                pass

            if ok_any:
                self.logger.info("Restored window layout from saved settings")
            return ok_any
        except Exception as e:
            self.logger.warning(f"Failed to load saved layout: {e}")
            return False

    def _connect_layout_autosave(self, dock: QDockWidget) -> None:
        """Connect signals from a dock to trigger autosave."""
        try:
            dock.topLevelChanged.connect(lambda _=False: self._schedule_layout_save())
            # Some bindings expose dockLocationChanged(area)
            if hasattr(dock, "dockLocationChanged"):
                dock.dockLocationChanged.connect(lambda _area=None: self._schedule_layout_save())
            dock.visibilityChanged.connect(lambda _=False: self._schedule_layout_save())
        except Exception:
            pass

    def _reset_dock_layout_and_save(self) -> None:
        """Reset layout to defaults and persist immediately."""
        self._reset_dock_layout()
        try:
            self._schedule_layout_save()
        except Exception:
            pass
    
    # ---- Settings persistence (QSettings) ----
    def _save_lighting_settings(self) -> None:
        """Save current lighting settings to QSettings."""
        try:
            settings = QSettings()
            if hasattr(self, 'lighting_manager') and self.lighting_manager:
                props = self.lighting_manager.get_properties()
                settings.setValue('lighting/position_x', float(props['position'][0]))
                settings.setValue('lighting/position_y', float(props['position'][1]))
                settings.setValue('lighting/position_z', float(props['position'][2]))
                settings.setValue('lighting/color_r', float(props['color'][0]))
                settings.setValue('lighting/color_g', float(props['color'][1]))
                settings.setValue('lighting/color_b', float(props['color'][2]))
                settings.setValue('lighting/intensity', float(props['intensity']))
                self.logger.debug("Lighting settings saved to QSettings")
        except Exception as e:
            self.logger.warning(f"Failed to save lighting settings: {e}")
    
    def _load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings and apply to manager and panel."""
        try:
            settings = QSettings()
            if settings.contains('lighting/position_x'):
                pos_x = settings.value('lighting/position_x', 100.0, type=float)
                pos_y = settings.value('lighting/position_y', 100.0, type=float)
                pos_z = settings.value('lighting/position_z', 100.0, type=float)
                col_r = settings.value('lighting/color_r', 1.0, type=float)
                col_g = settings.value('lighting/color_g', 1.0, type=float)
                col_b = settings.value('lighting/color_b', 1.0, type=float)
                intensity = settings.value('lighting/intensity', 0.8, type=float)
                props = {
                    "position": (float(pos_x), float(pos_y), float(pos_z)),
                    "color": (float(col_r), float(col_g), float(col_b)),
                    "intensity": float(intensity),
                }
                if hasattr(self, 'lighting_manager') and self.lighting_manager:
                    self.lighting_manager.apply_properties(props)
                # Sync to lighting_panel without re-emitting
                try:
                    if hasattr(self, 'lighting_panel') and self.lighting_panel:
                        self.lighting_panel.set_values(
                            position=props["position"],
                            color=props["color"],
                            intensity=props["intensity"],
                            emit_signals=False,
                        )
                except Exception:
                    pass
                self.logger.info("Lighting settings loaded from QSettings")
        except Exception as e:
            self.logger.warning(f"Failed to load lighting settings: {e}")
    
    def _save_lighting_panel_visibility(self) -> None:
        """Persist the lighting panel visibility state."""
        try:
            if hasattr(self, 'lighting_panel') and self.lighting_panel:
                settings = QSettings()
                vis = bool(self.lighting_panel.isVisible())
                settings.setValue('lighting_panel/visible', vis)
                self.logger.debug(f"Saved lighting panel visibility: {vis}")
        except Exception as e:
            self.logger.warning(f"Failed to save lighting panel visibility: {e}")
    
    # TODO: Add material roughness/metallic sliders in picker
    # TODO: Add export material presets feature

    # Menu action handlers
     
    def _reload_stylesheet_action(self) -> None:
        """Reload and re-apply the external stylesheet via theme helper."""
        self._apply_theme_styles()
        self.logger.info("Reloaded external stylesheet")
        self.statusBar().showMessage("Stylesheet reloaded", 2000)

    def _open_model(self) -> None:
        """Handle open model action."""
        self.logger.info("Opening model file dialog")
        
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(
            "3D Model Files (*.stl *.obj *.step *.stp *.mf3);;All Files (*)"
        )
        
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.logger.info(f"Selected model file: {file_path}")
            
            # Update status
            self.status_label.setText(f"Loading: {Path(file_path).name}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Load the model using STL parser
            self._load_stl_model(file_path)
    
    def _finish_model_loading(self, file_path: str, success: bool = True, error_message: str = "") -> None:
        """Finish model loading process."""
        filename = Path(file_path).name
        
        if success:
            self.status_label.setText(f"Loaded: {filename}")
            self.logger.info(f"Model loaded successfully: {filename}")
        else:
            self.status_label.setText(f"Failed to load: {filename}")
            self.logger.error(f"Failed to load model: {filename} - {error_message}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load model {filename}:\n{error_message}"
            )
        
        self.progress_bar.setVisible(False)
        
        # Emit signal
        self.model_loaded.emit(file_path)
    
    def _load_stl_model(self, file_path: str) -> None:
        """
        Load an STL model using the STL parser and display it in the viewer.
        
        Args:
            file_path: Path to the STL file to load
        """
        try:
            # Create STL parser
            parser = STLParser()
            
            # Create progress callback
            progress_callback = STLProgressCallback(
                callback_func=lambda progress, message: self._update_loading_progress(progress, message)
            )
            
            # Parse the file
            model = parser.parse_file(file_path, progress_callback)
            
            # Load model into viewer if available
            if hasattr(self.viewer_widget, 'load_model'):
                success = self.viewer_widget.load_model(model)
                self._finish_model_loading(file_path, success, "" if success else "Failed to load model into viewer")
            else:
                self._finish_model_loading(file_path, False, "3D viewer not available")
                
        except Exception as e:
            self._finish_model_loading(file_path, False, str(e))
    
    def _update_loading_progress(self, progress_percent: float, message: str) -> None:
        """
        Update loading progress in the UI.
        
        Args:
            progress_percent: Progress percentage (0-100)
            message: Progress message
        """
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(progress_percent))
        if message:
            self.status_label.setText(f"Loading: {message}")
    
    def _on_model_loaded(self, info: str) -> None:
        """
        Handle model loaded signal from viewer widget.
        
        Args:
            info: Information about the loaded model
        """
        self.logger.info(f"Viewer model loaded: {info}")
        # Attempt to apply last-used material species
        try:
            settings = QSettings()
            last_species = settings.value('material/last_species', '', type=str)
            if last_species:
                if hasattr(self, "material_manager") and self.material_manager:
                    species_list = self.material_manager.get_species_list()
                    if last_species in species_list:
                        self.logger.info(f"Applying last material species on load: {last_species}")
                        self._apply_material_species(last_species)
                    else:
                        self.logger.warning(f"Last material '{last_species}' not found; skipping reapply")
        except Exception as e:
            self.logger.warning(f"Failed to reapply last material species: {e}")
        
        # Update model properties dock if it exists
        if hasattr(self, 'properties_dock'):
            properties_widget = self.properties_dock.widget()
            if isinstance(properties_widget, QTextEdit):
                if hasattr(self.viewer_widget, 'get_model_info'):
                    model_info = self.viewer_widget.get_model_info()
                    if model_info:
                        info_text = (
                            f"Model Properties\n\n"
                            f"Triangles: {model_info['triangle_count']:,}\n"
                            f"Vertices: {model_info['vertex_count']:,}\n"
                            f"Dimensions: {model_info['dimensions'][0]:.2f} x "
                            f"{model_info['dimensions'][1]:.2f} x "
                            f"{model_info['dimensions'][2]:.2f}\n"
                            f"File size: {model_info['file_size'] / 1024:.1f} KB\n"
                            f"Format: {model_info['format']}\n"
                            f"Parse time: {model_info['parsing_time']:.3f} s\n"
                            f"FPS: {model_info['current_fps']:.1f}"
                        )
                        properties_widget.setPlainText(info_text)
    
    def _on_performance_updated(self, fps: float) -> None:
        """
        Handle performance update signal from viewer widget.
        
        Args:
            fps: Current frames per second
        """
        # Update status with FPS if it's below threshold
        if fps < 30.0:
            self.status_label.setText(f"Performance: {fps:.1f} FPS (low)")
    
    def _on_model_selected(self, model_id: int) -> None:
        """
        Handle model selection from the model library.
        
        Args:
            model_id: ID of the selected model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)
            
            if model:
                self.logger.info(f"Model selected from library: {model['filename']} (ID: {model_id})")
                self.model_selected.emit(model_id)
                
                # Load metadata in the metadata editor
                if hasattr(self, 'metadata_editor'):
                    self.metadata_editor.load_model_metadata(model_id)
                
                # Update view count
                db_manager.increment_view_count(model_id)
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")
                
        except Exception as e:
            self.logger.error(f"Failed to handle model selection: {str(e)}")
    
    def _on_model_double_clicked(self, model_id: int) -> None:
        """
        Handle model double-click from the model library.
        
        Args:
            model_id: ID of the double-clicked model
        """
        try:
            # Get model information from database
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)
            
            if model:
                file_path = model['file_path']
                self.logger.info(f"Loading model from library: {file_path}")
                
                # Update status
                from pathlib import Path
                filename = Path(file_path).name
                self.status_label.setText(f"Loading: {filename}")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
                
                # Load the model using STL parser
                self._load_stl_model(file_path)
            else:
                self.logger.warning(f"Model with ID {model_id} not found in database")
                
        except Exception as e:
            self.logger.error(f"Failed to handle model double-click: {str(e)}")
    
    def _on_models_added(self, model_ids: List[int]) -> None:
        """
        Handle models added to the library.
        
        Args:
            model_ids: List of IDs of added models
        """
        self.logger.info(f"Added {len(model_ids)} models to library")
        
        # Update status
        if model_ids:
            self.status_label.setText(f"Added {len(model_ids)} models to library")
            
            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
    
    def _on_metadata_saved(self, model_id: int) -> None:
        """
        Handle metadata saved event from the metadata editor.
        
        Args:
            model_id: ID of the model whose metadata was saved
        """
        try:
            self.logger.info(f"Metadata saved for model ID: {model_id}")
            self.status_label.setText("Metadata saved")
            
            # Update the model library to reflect changes
            if hasattr(self, 'model_library_widget'):
                self.model_library_widget._load_models_from_database()
            
            # Clear status after a delay
            QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
            
        except Exception as e:
            self.logger.error(f"Failed to handle metadata saved event: {str(e)}")
    
    def _on_metadata_changed(self, model_id: int) -> None:
        """
        Handle metadata changed event from the metadata editor.
        
        Args:
            model_id: ID of the model whose metadata changed
        """
        try:
            self.logger.debug(f"Metadata changed for model ID: {model_id}")
            # Update status to indicate unsaved changes
            self.status_label.setText("Metadata modified (unsaved changes)")
            
        except Exception as e:
            self.logger.error(f"Failed to handle metadata changed event: {str(e)}")
    
    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        self.logger.info("Opening preferences dialog")
        dlg = PreferencesDialog(self, on_reset_layout=self._reset_dock_layout_and_save)
        # Live theme apply
        dlg.theme_changed.connect(self._apply_theme_styles)
        dlg.exec_()
    
    def _show_theme_manager(self) -> None:
        """Show the Theme Manager dialog and hook apply signal."""
        try:
            from gui.theme_manager_widget import ThemeManagerWidget
            dlg = ThemeManagerWidget(self)
            dlg.themeApplied.connect(self._on_theme_applied)
            dlg.show()
        except Exception as e:
            self.logger.error(f"Failed to open Theme Manager: {e}")
            QMessageBox.warning(self, "Theme Manager", f"Failed to open Theme Manager:\n{e}")

    def _on_theme_applied(self, _colors: dict) -> None:
        """Re-apply styles after a theme change."""
        try:
            ThemeManager.instance().apply_to_registered()
        except Exception:
            pass
        try:
            self._apply_theme_styles()
        except Exception:
            pass

    def _zoom_in(self) -> None:
        """Handle zoom in action."""
        self.logger.debug("Zoom in requested")
        self.status_label.setText("Zoomed in")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'zoom_in'):
            self.viewer_widget.zoom_in()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _zoom_out(self) -> None:
        """Handle zoom out action."""
        self.logger.debug("Zoom out requested")
        self.status_label.setText("Zoomed out")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'zoom_out'):
            self.viewer_widget.zoom_out()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _reset_view(self) -> None:
        """Handle reset view action."""
        self.logger.debug("Reset view requested")
        self.status_label.setText("View reset")
        
        # Forward to viewer widget if available
        if hasattr(self.viewer_widget, 'reset_view'):
            self.viewer_widget.reset_view()
        else:
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def _show_about(self) -> None:
        """Show about dialog."""
        self.logger.info("Showing about dialog")
        
        about_text = (
            "<h3>3D-MM - 3D Model Manager</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A desktop application for managing and viewing 3D models.</p>"
            "<p><b>Supported formats:</b> STL, OBJ, STEP, MF3</p>"
            "<p><b>Requirements:</b> Windows 7+, Python 3.8+, PySide5</p>"
            "<br>"
            "<p>&copy; 2023 3D-MM Development Team</p>"
        )
        
        QMessageBox.about(self, "About 3D-MM", about_text)
     
    # Lighting/Material integrations
    def _toggle_lighting_panel(self) -> None:
        """Show/hide the lighting control dock."""
        try:
            if hasattr(self, "lighting_panel") and self.lighting_panel:
                is_visible = self.lighting_panel.isVisible()
                self.lighting_panel.setVisible(not is_visible)
                if not is_visible:
                    try:
                        self.lighting_panel.raise_()  # type: ignore[attr-defined]
                    except Exception:
                        pass
        except Exception as e:
            self.logger.warning(f"Failed to toggle lighting panel: {e}")

    def _update_light_position(self, x: float, y: float, z: float) -> None:
        if hasattr(self, "lighting_manager") and self.lighting_manager:
            try:
                self.lighting_manager.update_position(x, y, z)
                self._save_lighting_settings()
            except Exception as e:
                self.logger.error(f"update_position failed: {e}")

    def _update_light_color(self, r: float, g: float, b: float) -> None:
        if hasattr(self, "lighting_manager") and self.lighting_manager:
            try:
                self.lighting_manager.update_color(r, g, b)
                self._save_lighting_settings()
            except Exception as e:
                self.logger.error(f"update_color failed: {e}")

    def _update_light_intensity(self, value: float) -> None:
        if hasattr(self, "lighting_manager") and self.lighting_manager:
            try:
                self.lighting_manager.update_intensity(value)
                self._save_lighting_settings()
            except Exception as e:
                self.logger.error(f"update_intensity failed: {e}")

    def _apply_material_species(self, species_name: str) -> None:
        """Apply selected material species to the current viewer actor."""
        try:
            if not species_name:
                return
            # TODO: Add UV mapping generation for models without texture coordinates
            if not hasattr(self, "viewer_widget") or not getattr(self.viewer_widget, "actor", None):
                self.logger.warning("No model loaded, cannot apply material")
                return
            if not hasattr(self, "material_manager") or self.material_manager is None:
                self.logger.warning("MaterialManager not available")
                return
            ok = self.material_manager.apply_material_to_actor(self.viewer_widget.actor, species_name)
            if ok:
                # Save last selected material species
                try:
                    settings = QSettings()
                    settings.setValue('material/last_species', species_name)
                    self.logger.info(f"Saved last material species: {species_name}")
                except Exception as se:
                    self.logger.warning(f"Failed to persist last material species: {se}")
                # Re-render
                try:
                    self.viewer_widget.vtk_widget.GetRenderWindow().Render()
                except Exception:
                    pass
                try:
                    self.statusBar().showMessage(f"Applied material: {species_name}", 2000)
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Failed to apply material '{species_name}': {e}")
    
    # Event handlers

    def resizeEvent(self, event) -> None:
        """Autosave geometry changes on resize (debounced)."""
        try:
            self._schedule_layout_save()
        except Exception:
            pass
        return super().resizeEvent(event)

    def moveEvent(self, event) -> None:
        """Autosave geometry changes on move (debounced)."""
        try:
            self._schedule_layout_save()
        except Exception:
            pass
        return super().moveEvent(event)
     
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.logger.info("Application closing")
        
        # Clean up resources
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Clean up widgets
        if hasattr(self, 'metadata_editor'):
            self.metadata_editor.cleanup()
        
        if hasattr(self, 'model_library_widget'):
            self.model_library_widget.cleanup()
        
        # Memory cleanup: clear material texture cache
        try:
            if hasattr(self, 'material_manager') and self.material_manager:
                self.material_manager.clear_texture_cache()
                self.logger.info("Cleared MaterialManager texture cache on close")
        except Exception as e:
            self.logger.warning(f"Failed to clear material texture cache: {e}")
        
        # Persist final lighting settings and panel visibility on close
        try:
            self._save_lighting_settings()
            self._save_lighting_panel_visibility()
        except Exception:
            pass
        
        # Accept the close event
        event.accept()
        
        self.logger.info("Application closed")