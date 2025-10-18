"""
Main window components module for GUI.

Provides modular components for main window management.
"""

from .layout_manager import LayoutManager
from .settings_manager import SettingsManager
from .dock_manager import DockManager
from .event_handler import EventHandler
from .main_window_facade import MainWindowFacade

__all__ = [
    'LayoutManager',
    'SettingsManager',
    'DockManager',
    'EventHandler',
    'MainWindowFacade',
]

