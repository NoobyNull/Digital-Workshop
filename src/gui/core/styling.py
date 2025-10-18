"""
UI Styling and Theme Management Module

This module handles the styling and theme management for the main window,
including initialization of UI properties, application of theme stylesheets,
and management of visual appearance across the application.

Classes:
    StylingManager: Main class for managing UI styling and themes
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QMainWindow, QStatusBar, QMenuBar, QToolBar
from PySide6.QtGui import QPalette

from src.gui.theme import COLORS, ThemeManager, qss_tabs_lists_labels, SPACING_4, SPACING_8, SPACING_12, SPACING_16, SPACING_24, hex_to_rgb


class StylingManager:
    """
    Manages UI styling and theme application for the main window.

    This class handles the initialization of basic UI properties, application
    of theme stylesheets, and coordination of visual styling across all
    components of the main window.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the styling manager.

        Args:
            main_window: The main window instance to style
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

    def init_ui(self) -> None:
        """Initialize basic UI properties and styling."""
        # Set window icon if available
        # self.main_window.setWindowIcon(QIcon(":/icons/app_icon.png"))

        # Set application style for Windows desktop
        # QApplication.setStyle("Fusion")  # Modern look and feel

        # Enable dock widget features for better layout management
        # options = (
        #     QMainWindow.AllowNestedDocks |
        #     QMainWindow.AllowTabbedDocks |
        #     QMainWindow.AnimatedDocks
        # )
        # Grouped dragging (if available) improves docking behavior when tabs are involved
        # if hasattr(QMainWindow, "GroupedDragging"):
        #     options |= QMainWindow.GroupedDragging
        # self.main_window.setDockOptions(options)
        # Explicitly enable nesting (no-op on some styles, harmless)
        # try:
        #     self.main_window.setDockNestingEnabled(True)
        # except Exception:
        #     pass

        # Set central widget background using theme variables (spacing aligned to theme scale)
        # Base theme stylesheet
        # base_qss = f"""
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
            /* Splitters and dock separators */
            QSplitter {{
                background-color: {COLORS.window_bg};
            }}
            QSplitter::handle {{
                background-color: {COLORS.splitter_handle_bg};
                border: 1px solid {COLORS.border};
                width: 7px;
                height: 7px;
                border-radius: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {COLORS.primary};
                border-color: {COLORS.primary_hover};
            }}
            QMainWindow::separator {{
                background: {COLORS.splitter_handle_bg};
                width: 7px;
                height: 7px;
            }}
            QMainWindow::separator:hover {{
                background: {COLORS.primary};
            }}
        """
       # Apply ThemeManager-managed external stylesheet, then append base_qss
       # try:
       #     tm = ThemeManager.instance()
       #     css_abs_path = str(Path(__file__).resolve().parents[1] / "resources" / "styles" / "main_window.css")
       #     tm.register_widget(self.main_window, css_path=css_abs_path)
       #     tm.apply_stylesheet(self.main_window)
       #     # Append base_qss overrides
       #     self.main_window.setStyleSheet(self.main_window.styleSheet() + "\n" + base_qss)
       # except Exception:
       #     # Fallback: apply base_qss only
       #     self.main_window.setStyleSheet(base_qss)
       # Notify via status bar for visible validation
       # try:
       #     self.main_window.statusBar().showMessage("Applied main_window.css", 2000)
       # except Exception:
       #     pass
       # Apply extended theme styling and confirm
       # try:
       #     self._apply_theme_styles()
       #     self.main_window.statusBar().showMessage("Modern UI styling applied", 2500)
       # except Exception:
       #     pass

    def apply_theme_styles(self) -> None:
        """Apply theme to MainWindow and child widgets."""
        # NOTE: Qt-Material theme is applied globally via ThemeService.apply_theme()
        # This method is kept for backward compatibility but does NOT apply custom stylesheets
        # to avoid overriding the Material Design theme.
        #
        # If you need to customize the Material Design theme, modify the qt-material
        # theme files or use the ThemeService API.
        pass
        #     if hasattr(self, "hero_tabs") and isinstance(self.hero_tabs, QTabWidget):
        #         self.hero_tabs.setStyleSheet(qss_tabs_lists_labels())
        # except Exception:
        #     pass

    def apply_bar_palettes(self) -> None:
        """
        Force palette-based colors for menu/status bars to ensure background
        paints even when style engine ignores QSS for these native widgets.
        """
        try:
            tm = ThemeManager.instance()
            # Status bar
            if hasattr(self.main_window, "status_bar") and self.main_window.status_bar is not None:
                sp = self.main_window.status_bar.palette()
                sp.setColor(QPalette.Window, tm.qcolor("statusbar_bg"))
                sp.setColor(QPalette.WindowText, tm.qcolor("statusbar_text"))
                self.main_window.status_bar.setPalette(sp)
                self.main_window.status_bar.setAutoFillBackground(True)
            # Menu bar
            mb = self.main_window.menuBar()
            if mb is not None:
                mp = mb.palette()
                mp.setColor(QPalette.Window, tm.qcolor("menubar_bg"))
                mp.setColor(QPalette.WindowText, tm.qcolor("menubar_text"))
                mb.setPalette(mp)
                mb.setAutoFillBackground(True)
            # Toolbar palette
            if hasattr(self.main_window, "main_toolbar") and self.main_window.main_toolbar is not None:
                tp = self.main_window.main_toolbar.palette()
                tp.setColor(QPalette.Window, tm.qcolor("toolbar_bg"))
                tp.setColor(QPalette.WindowText, tm.qcolor("text"))
                self.main_window.main_toolbar.setPalette(tp)
                self.main_window.main_toolbar.setAutoFillBackground(True)
        except Exception:
            # Never break UI if palette application fails
            pass

    def load_external_stylesheet(self) -> None:
        """Append external CSS from resources/styles/main_window.css to current stylesheet."""
        # NOTE: Disabled to avoid overriding Material Design theme
        # External CSS is not applied when using qt-material theme
        pass


# Convenience function for easy styling application
def apply_main_window_styling(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> StylingManager:
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
