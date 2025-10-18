"""
Theme Manager Components - Modular theme editor UI.

This package provides a comprehensive theme editor with live preview.
Components are organized for maintainability and reusability.

Public API:
- ThemeManagerWidget: Main dialog with color editor and preview
- ColorRow: Single color variable editor widget
- PreviewWindow: Live preview window
"""

from .color_row import ColorRow
from .preview_window import PreviewWindow
from .theme_manager_widget_main import ThemeManagerWidget

__all__ = [
    "ColorRow",
    "PreviewWindow",
    "ThemeManagerWidget",
]

