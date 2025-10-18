"""
ThemeManagerWidget - Facade for modular theme manager components.

This module provides backward-compatible access to the refactored theme manager.
All functionality has been moved to src/gui/theme_manager_components/ package.

Run standalone for testing:
    python -m src.gui.theme_manager_widget
"""

from src.gui.theme_manager_components import (
    ThemeManagerWidget,
    ColorRow,
    PreviewWindow,
)

__all__ = [
    "ThemeManagerWidget",
    "ColorRow",
    "PreviewWindow",
]
