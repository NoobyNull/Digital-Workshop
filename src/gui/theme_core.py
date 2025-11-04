"""
Simple, clean theme core for the application.

This is the ONLY file that should handle theming.
All widgets should import from here and call apply_theme() on initialization.

Usage:
    from src.gui.theme_core import apply_theme

    # In widget __init__:
    apply_theme(self)

    # When theme changes:
    apply_theme(self)  # Re-apply to update colors
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QColor


def apply_theme(widget: Optional[QWidget] = None) -> None:
    """
    Apply qt-material theme to a widget or the entire application.

    This is the ONLY theming function that should be used.
    Call this on widget initialization and whenever theme changes.

    Args:
        widget: Optional widget to apply theme to. If None, applies to QApplication.
    """
    try:
        if widget is None:
            # Apply to entire application
            app = QApplication.instance()
            if app is None:
                return
            # qt-material is already applied globally via ThemeService
            # This is a no-op for the app level
            return

        # For individual widgets, qt-material stylesheet inheritance handles it
        # No need to do anything - just let qt-material cascade
        return
    except Exception:
        pass


def get_theme_color(color_name: str) -> QColor:
    """
    Get a color from the current qt-material theme.

    This should only be used for VTK rendering or other non-Qt APIs.
    For Qt widgets, let qt-material handle styling automatically.

    Args:
        color_name: Name of the color (e.g., 'primary', 'text', 'background')

    Returns:
        QColor object
    """
    try:
        from src.gui.theme.manager import ThemeManager

        tm = ThemeManager.instance()
        return tm.qcolor(color_name)
    except Exception:
        # Fallback to neutral colors
        if "text" in color_name.lower():
            return QColor(0, 0, 0)
        elif "bg" in color_name.lower() or "background" in color_name.lower():
            return QColor(255, 255, 255)
        else:
            return QColor(128, 128, 128)


def reload_theme() -> None:
    """
    Reload the theme across the entire application.

    Call this when the user changes theme settings.
    """
    try:
        app = QApplication.instance()
        if app is None:
            return

        # qt-material theme is already applied globally
        # Just trigger a style update
        app.style().polish(app)

        # Update all widgets
        for widget in app.allWidgets():
            widget.style().polish(widget)
    except Exception:
        pass
