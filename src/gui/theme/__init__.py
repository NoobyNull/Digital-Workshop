"""
Consolidated Theme Management System

This module provides a single, consolidated theme management system that eliminates
conflicting theme services and provides a unified entry point for all theme operations.

Public API:
- QtMaterialThemeService: Primary qt-material-based theme service (recommended)
- ThemeService: Backward compatibility theme service using PySide6 built-in styling

Usage:
    from src.gui.theme import QtMaterialThemeService

    # Get primary theme service instance
    theme_service = QtMaterialThemeService.instance()

    # Apply themes
    theme_service.apply_theme("dark", "blue")
    theme_service.apply_theme("light", "amber")

    # Or use backward compatibility service
    from src.gui.theme import ThemeService
    legacy_service = ThemeService.instance()
    legacy_service.apply_theme("dark")

Architecture:
- Single Entry Point: Consolidated to QtMaterialThemeService as primary
- Backward Compatibility: ThemeService available for legacy code
- No Conflicts: Eliminates multiple competing theme managers
- VTK Integration: Direct connection to VTK color provider
- Clean Dependencies: Minimal external library requirements

Benefits:
- Eliminates theme service conflicts and race conditions
- Provides consistent theme application timing
- Maintains backward compatibility for existing code
- Supports both qt-material and built-in PySide6 styling
- Clear migration path from legacy systems
"""

# ============================================================
# Unified Theme System Imports
# ============================================================

# Core theme system - consolidated to single entry point
from .qt_material_service import QtMaterialThemeService

# ThemeService for backward compatibility (used in tests and other modules)
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

# Backward compatibility - ThemeManager alias for QtMaterialThemeService
from .qt_material_service import QtMaterialThemeService as ThemeManager

# No backward compatibility - pure dynamic system only

# ============================================================
# Public API Exports
# ============================================================

__all__ = [
    # ============================================================
    # Consolidated Theme System (Single Entry Point)
    # ============================================================

    # Primary theme service (qt-material based)
    "QtMaterialThemeService",

    # Backward compatibility theme service
    "ThemeService",

    # Backward compatibility alias for QtMaterialThemeService
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
        service = QtMaterialThemeService.instance()
        # Extract theme info from dict
        theme_name = theme_dict.get('name', 'dark')
        variant = theme_dict.get('variant', 'blue')
        service.apply_theme(theme_name, variant)
    except Exception as e:
        try:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to set theme: {e}")
        except Exception:
            pass

def theme_to_dict() -> dict:
    """
    Get current theme as dictionary (backward compatibility).
    
    Returns:
        Dictionary containing current theme settings
    """
    try:
        service = QtMaterialThemeService.instance()
        theme, variant = service.get_current_theme()
        return {
            'name': theme,
            'variant': variant,
            'colors': service.get_all_colors()
        }
    except Exception:
        return {
            'name': 'dark',
            'variant': 'blue',
            'colors': COLORS.copy()
        }

# Legacy color function
def color(color_name: str) -> str:
    """
    Get color by name (backward compatibility).
    
    Args:
        color_name: Name of the color
        
    Returns:
        Hex color string
    """
    try:
        service = QtMaterialThemeService.instance()
        return service.get_color(color_name)
    except Exception:
        return COLORS.get(color_name, FALLBACK_COLOR)

def get_theme_system_info() -> dict:
    """
    Get information about the qt-material theme system.
    
    Returns:
        Dictionary containing theme system information
    """
    service = QtMaterialThemeService.instance()
    vtk_provider = get_vtk_color_provider()
    
    return {
        "architecture": "qt-material-only",
        "version": "2.0.0",
        "legacy_support": "minimal_compatibility_aliases",
        "circular_dependencies": "eliminated",
        "current_theme": service.get_current_theme(),
        "available_themes": service.get_available_themes(),
        "vtk_managers_registered": vtk_provider.get_vtk_manager_count(),
        "qt_material_available": hasattr(service, 'qtmaterial') and service.qtmaterial is not None
    }

def log_theme_system_status() -> None:
    """Log the current status of the theme system for debugging."""
    info = get_theme_system_info()
    
    from src.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    logger.info("Qt-Material Theme System Status:")
    logger.info(f"  Architecture: {info['architecture']}")
    logger.info(f"  Version: {info['version']}")
    logger.info(f"  Legacy Support: {info['legacy_support']}")
    logger.info(f"  Circular Dependencies: {info['circular_dependencies']}")
    logger.info(f"  Current Theme: {info['current_theme']}")
    logger.info(f"  Available Themes: {list(info['available_themes'].keys())}")
    logger.info(f"  VTK Managers: {info['vtk_managers_registered']}")
    logger.info(f"  Qt-Material Available: {info['qt_material_available']}")

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
        from src.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        service = QtMaterialThemeService.instance()
        service.load_settings()
        logger.info("Theme settings loaded from QSettings")
    except Exception as e:
        try:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to load theme settings: {e}")
        except Exception:
            # If logging fails, continue without it
            pass
        
        # Apply default theme as fallback
        try:
            service = QtMaterialThemeService.instance()
            service.apply_theme("dark", "blue")
            try:
                logger = get_logger(__name__)
                logger.info("Applied default theme as fallback")
            except Exception:
                pass
        except Exception as fallback_error:
            try:
                logger = get_logger(__name__)
                logger.error(f"Failed to apply fallback theme: {fallback_error}")
            except Exception:
                pass


def save_theme_to_settings() -> None:
    """
    Save current theme settings to QSettings.
    
    Backward compatibility function for preferences dialog.
    """
    try:
        from src.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        service = QtMaterialThemeService.instance()
        service.save_settings()
        logger.info("Theme settings saved to QSettings")
    except Exception as e:
        try:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to save theme settings: {e}")
        except Exception:
            pass
        raise


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color to RGB tuple (0-1 range).
    
    Backward compatibility function for legacy code.
    
    Args:
        hex_color: Hex color string (e.g., "#1976D2")
        
    Returns:
        Tuple of RGB values (0-1 range)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


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
        from src.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        service = QtMaterialThemeService.instance()
        # Map legacy theme names to qt-material themes
        theme_mapping = {
            "dark": "dark",
            "light": "light",
            "auto": "auto"
        }
        qt_theme = theme_mapping.get(theme_name.lower(), "dark")
        return service.apply_theme(qt_theme)
    except Exception as e:
        try:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to apply theme preset {theme_name}: {e}")
        except Exception:
            pass
        return False


def qss_tabs_lists_labels() -> str:
    """
    Get QSS stylesheet for tabs, lists, and labels.
    
    Backward compatibility function for UI styling.
    
    Returns:
        QSS stylesheet string
    """
    try:
        service = QtMaterialThemeService.instance()
        # Return basic styling based on current theme
        return f"""
        QTabWidget::pane {{
            border: 1px solid {service.get_color('surface')};
            background: {service.get_color('background')};
        }}
        QListWidget {{
            background: {service.get_color('background')};
            color: {service.get_color('primary')};
        }}
        QLabel {{
            color: {service.get_color('primary')};
        }}
        """
    except Exception:
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
    try:
        from src.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        service = QtMaterialThemeService.instance()
        return service.get_color(color_name)
    except Exception:
        return COLORS.get(color_name, FALLBACK_COLOR)


def get_current_theme_name() -> str:
    """
    Get the current theme name (backward compatibility function).
    
    Returns:
        Current theme name
    """
    try:
        service = QtMaterialThemeService.instance()
        theme, variant = service.get_current_theme()
        return theme
    except Exception:
        return "dark"


def get_current_theme_variant() -> str:
    """
    Get the current theme variant (backward compatibility function).
    
    Returns:
        Current theme variant
    """
    try:
        service = QtMaterialThemeService.instance()
        theme, variant = service.get_current_theme()
        return variant
    except Exception:
        return "blue"


def apply_theme_with_variant(theme_name: str, variant: str = None) -> bool:
    """
    Apply theme with variant (backward compatibility function).
    
    Args:
        theme_name: Theme name
        variant: Theme variant
        
    Returns:
        True if theme was applied successfully
    """
    try:
        from src.core.logging_config import get_logger
        logger = get_logger(__name__)
        
        service = QtMaterialThemeService.instance()
        if variant is None:
            variant = "blue"
        return service.apply_theme(theme_name, variant)
    except Exception as e:
        try:
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to apply theme with variant: {e}")
        except Exception:
            pass
        return False


def get_theme_colors() -> dict:
    """
    Get all theme colors (backward compatibility function).
    
    Returns:
        Dictionary of all theme colors
    """
    try:
        service = QtMaterialThemeService.instance()
        return service.get_all_colors()
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
        service = QtMaterialThemeService.instance()
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
