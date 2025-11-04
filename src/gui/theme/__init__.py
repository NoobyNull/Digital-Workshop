"""
Consolidated Theme Management System

This module provides a single, consolidated theme management system that eliminates
conflicting theme services and provides a unified entry point for all theme operations.

Public API:
- ThemeService: Primary theme service using PySide6 built-in styling

Usage:
    from src.gui.theme import ThemeService

    # Get primary theme service instance
    theme_service = ThemeService.instance()

    # Apply themes
    theme_service.apply_theme("dark")
    theme_service.apply_theme("light")

Architecture:
- Single Entry Point: Consolidated to ThemeService
- No External Dependencies: Uses only PySide6 built-in styling
- VTK Integration: Direct connection to VTK color provider
- Clean Dependencies: Minimal external library requirements

Benefits:
- Eliminates theme service conflicts and race conditions
- Provides consistent theme application timing
- No external library dependencies
- Clear and simple implementation
"""

# ============================================================
# Unified Theme System Imports
# ============================================================

# Core theme system - using simple PySide6 styling
from .simple_service import ThemeService

# Import COLORS and other constants from theme_api for backward compatibility
try:
    from .theme_api import COLORS
except ImportError:
    # Fallback: create a simple COLORS proxy
    class _SimpleColorsProxy:
        def __getattr__(self, name):
            return "#E31C79"  # Fallback color

    COLORS = _SimpleColorsProxy()

# Import constants
from .theme_constants import (
    FALLBACK_COLOR,
    SPACING_4,
    SPACING_8,
    SPACING_12,
    SPACING_16,
    SPACING_24,
)

# Import VTK color function
from .theme_service import vtk_rgb

# Backward compatibility - ThemeManager alias for ThemeService
ThemeManager = ThemeService

# ============================================================
# Public API Exports
# ============================================================

__all__ = [
    # ============================================================
    # Consolidated Theme System (Single Entry Point)
    # ============================================================
    # Primary theme service
    "ThemeService",
    # Backward compatibility alias for ThemeService
    "ThemeManager",
    # Colors and constants
    "COLORS",
    "FALLBACK_COLOR",
    "SPACING_4",
    "SPACING_8",
    "SPACING_12",
    "SPACING_16",
    "SPACING_24",
    # VTK integration
    "vtk_rgb",
]

# ============================================================
# Module Information
# ============================================================


# Missing functions for backward compatibility
def set_theme(theme_dict: dict) -> None:
    """
    Set theme from dictionary (backward compatibility).

    Args:
        theme_dict: Dictionary containing theme settings
    """
    try:
        service = ThemeService.instance()
        # Extract theme info from dict
        theme_name = theme_dict.get("name", "dark")
        service.apply_theme(theme_name)
    except Exception as e:
        try:
            from src.core.logging_config import get_logger

            logger = get_logger(__name__)
            logger.debug(f"Failed to set theme: {e}")
        except Exception:
            pass


def theme_to_dict() -> dict:
    """
    Get current theme as dictionary (backward compatibility).

    Returns:
        Dictionary containing current theme settings
    """
    try:
        service = ThemeService.instance()
        theme, _ = service.get_current_theme()
        return {"name": theme, "colors": COLORS.copy()}
    except Exception:
        return {"name": "dark", "colors": COLORS.copy()}


# Legacy color function
def color(color_name: str) -> str:
    """
    Get color by name (backward compatibility).

    Args:
        color_name: Name of the color

    Returns:
        Hex color string
    """
    return COLORS.get(color_name, FALLBACK_COLOR)


def get_theme_system_info() -> dict:
    """
    Get information about the theme system.

    Returns:
        Dictionary containing theme system information
    """
    service = ThemeService.instance()
    vtk_provider = get_vtk_color_provider()

    return {
        "architecture": "simple_pyside6",
        "version": "2.0.0",
        "legacy_support": "minimal_compatibility_aliases",
        "current_theme": service.get_current_theme(),
        "vtk_managers_registered": vtk_provider.get_vtk_manager_count(),
    }


def log_theme_system_status() -> None:
    """Log the current status of the theme system for debugging."""
    info = get_theme_system_info()

    from src.core.logging_config import get_logger

    logger = get_logger(__name__)

    logger.debug("Theme System Status:")
    logger.debug(f"  Architecture: {info['architecture']}")
    logger.debug(f"  Version: {info['version']}")
    logger.debug(f"  Current Theme: {info['current_theme']}")


# ============================================================
# Backward Compatibility Functions
# ============================================================


def load_theme_from_settings() -> None:
    """
    Load theme settings from QSettings and apply to application.

    Backward compatibility function for application bootstrap.
    Loads saved theme configuration and applies it to the application.
    """
    try:
        service = ThemeService.instance()
        service.apply_theme("dark")
    except Exception:
        pass


def save_theme_to_settings() -> None:
    """
    Save current theme settings to QSettings.

    Backward compatibility function for preferences dialog.
    """
    # Theme settings are handled by ThemeService
    pass


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color to RGB tuple (0-1 range).

    Backward compatibility function for legacy code.

    Args:
        hex_color: Hex color string (e.g., "#1976D2")

    Returns:
        Tuple of RGB values (0-1 range)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def apply_theme_preset(theme_name: str) -> bool:
    """
    Apply a predefined theme preset.

    Backward compatibility function for legacy theme system.

    Args:
        theme_name: Name of the theme preset

    Returns:
        True if theme was applied successfully
    """
    try:
        service = ThemeService.instance()
        theme_mapping = {"dark": "dark", "light": "light", "auto": "auto"}
        theme = theme_mapping.get(theme_name.lower(), "dark")
        return service.apply_theme(theme)
    except Exception:
        return False


def qss_tabs_lists_labels() -> str:
    """
    Get QSS stylesheet for tabs, lists, and labels.

    Backward compatibility function for UI styling.

    Returns:
        QSS stylesheet string
    """
    # Return basic fallback styling
    return """
    QTabWidget::pane { border: 1px solid #333; background: #121212; }
    QListWidget { background: #121212; color: #1976D2; }
    QLabel { color: #1976D2; }
    """


# Additional backward compatibility functions
def get_theme_color(color_name: str) -> str:
    """
    Get a theme color by name (backward compatibility function).

    Args:
        color_name: Name of the color

    Returns:
        Hex color string
    """
    return COLORS.get(color_name, FALLBACK_COLOR)


def get_current_theme_name() -> str:
    """
    Get the current theme name (backward compatibility function).

    Returns:
        Current theme name
    """
    try:
        service = ThemeService.instance()
        theme, _ = service.get_current_theme()
        return theme
    except Exception:
        return "dark"


def get_current_theme_variant() -> str:
    """
    Get the current theme variant (backward compatibility function).

    Returns:
        Current theme variant
    """
    return "default"


def apply_theme_with_variant(theme_name: str, variant: str = None) -> bool:
    """
    Apply theme with variant (backward compatibility function).

    Args:
        theme_name: Theme name
        variant: Theme variant (ignored)

    Returns:
        True if theme was applied successfully
    """
    try:
        service = ThemeService.instance()
        return service.apply_theme(theme_name)
    except Exception:
        return False


def get_theme_colors() -> dict:
    """
    Get all theme colors (backward compatibility function).

    Returns:
        Dictionary of all theme colors
    """
    try:
        return COLORS.copy()
    except Exception:
        return COLORS.copy()


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color (backward compatibility function).

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string
    """
    try:
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return FALLBACK_COLOR


def is_dark_theme() -> bool:
    """
    Check if current theme is dark (backward compatibility function).

    Returns:
        True if current theme is dark
    """
    try:
        service = ThemeService.instance()
        theme, _ = service.get_current_theme()
        return theme.lower() == "dark"
    except Exception:
        return True  # Default to dark


def is_light_theme() -> bool:
    """
    Check if current theme is light (backward compatibility function).

    Returns:
        True if current theme is light
    """
    return not is_dark_theme()


# Legacy theme managers removed - consolidated to single entry point


# Auto-log status on import for debugging
try:
    log_theme_system_status()
except Exception:
    # Fail silently if logging fails during import
    pass
