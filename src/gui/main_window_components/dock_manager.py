"""
Compatibility wrapper for dock management.

Re-exports the dock manager from ``src.gui.window.dock_manager`` to avoid duplicate code.
"""

from src.gui.window.dock_manager import DockManager

__all__ = ["DockManager"]
