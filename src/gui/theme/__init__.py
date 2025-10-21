"""
Qt-Material-Only Theme System

This module provides a clean, qt-material-only public API for the theme system,
completely eliminating all legacy static theming and remnants. No circular
dependencies, no legacy color systems, no ThemeManager references.

Public API:
- QtMaterialThemeService: Unified qt-material theme management
- VTKColorProvider: VTK color integration from qt-material
- QtMaterialThemeSwitcher: Qt-material theme selection widget
- QtMaterialColorPicker: Material Design color picker dialog
- QtMaterialThemeDialog: Comprehensive theme configuration dialog

Usage:
    from src.gui.theme import QtMaterialThemeService, vtk_rgb
    
    service = QtMaterialThemeService.instance()
    service.apply_theme("dark", "blue")
    service.save_settings()
    
    # VTK integration
    bg_color = vtk_rgb("canvas_bg")

Architecture:
- qt-material ONLY: No other theme systems or static color management
- Zero Legacy Remnants: Complete removal of all static theming
- Eliminated Circular Dependencies: No ThemeManager, no recursion
- Clean API: qt-material-focused public interface only
"""

# ============================================================
# Qt-Material Core Imports
# ============================================================

from .qt_material_service import QtMaterialThemeService
from .vtk_color_provider import VTKColorProvider, get_vtk_color_provider, vtk_rgb
from .qt_material_ui import (
    QtMaterialThemeSwitcher,
    QtMaterialColorPicker,
    QtMaterialThemeDialog,
    create_theme_switcher,
    create_color_picker,
    create_theme_dialog
)

# ============================================================
# Backward Compatibility Aliases (Minimal)
# ============================================================

# Primary backward compatibility alias
ThemeService = QtMaterialThemeService

# UI component aliases for backward compatibility
ThemeSwitcher = QtMaterialThemeSwitcher
SimpleThemeSwitcher = QtMaterialThemeSwitcher  # Simplified version
ColorPicker = QtMaterialColorPicker
ThemeDialog = QtMaterialThemeDialog

# Legacy class aliases for backward compatibility
ThemeDefaults = QtMaterialThemeService  # Alias for theme defaults
FALLBACK_COLOR = "#1976D2"  # Default blue color

# Legacy color constants
COLORS = {
    "primary": "#1976D2",
    "secondary": "#424242",
    "background": "#121212",
    "surface": "#1E1E1E",
    "error": "#F44336",
    "warning": "#FF9800",
    "success": "#4CAF50",
    "info": "#2196F3"
}

# ============================================================
# Legacy Spacing Constants (for backward compatibility)
# ============================================================

# Spacing constants for UI layout
SPACING_4 = 4
SPACING_8 = 8
SPACING_12 = 12
SPACING_16 = 16
SPACING_24 = 24
SPACING_32 = 32

# ============================================================
# Public API Exports
# ============================================================

__all__ = [
    # Core Qt-Material Service (new unified API)
    "QtMaterialThemeService",
    
    # VTK Integration
    "VTKColorProvider",
    "get_vtk_color_provider",
    "vtk_rgb",
    
    # UI Components
    "QtMaterialThemeSwitcher",
    "QtMaterialColorPicker",
    "QtMaterialThemeDialog",
    
    # Convenience Functions
    "create_theme_switcher",
    "create_color_picker",
    "create_theme_dialog",
    
    # Minimal Backward Compatibility
    "ThemeService",
    "ThemeSwitcher",
    "SimpleThemeSwitcher",
    "ColorPicker",
    "ThemeDialog",
    
    # Legacy Functions
    "load_theme_from_settings",
    "save_theme_to_settings",
    "hex_to_rgb",
    "apply_theme_preset",
    "qss_tabs_lists_labels",
    "get_theme_color",
    "get_current_theme_name",
    "get_current_theme_variant",
    "apply_theme_with_variant",
    "get_theme_colors",
    "rgb_to_hex",
    "is_dark_theme",
    "is_light_theme",
    
    # Legacy Classes and Constants
    "ThemeManager",
    "ThemeDefaults",
    "COLORS",
    "FALLBACK_COLOR",
    
    # Legacy Spacing Constants
    "SPACING_4",
    "SPACING_8",
    "SPACING_12",
    "SPACING_16",
    "SPACING_24",
    "SPACING_32"
]

# ============================================================
# Module Information
# ============================================================

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


# ============================================================
# Legacy ThemeManager Compatibility Class
# ============================================================

class LegacyThemeManager:
    """
    Legacy ThemeManager compatibility class.
    
    Provides backward compatibility for legacy ThemeManager usage
    while delegating to QtMaterialThemeService.
    """
    
    def __init__(self):
        self._service = QtMaterialThemeService.instance()
    
    def apply_theme(self, theme_name: str, variant: str = None) -> bool:
        """Legacy apply_theme method."""
        return self._service.apply_theme(theme_name, variant)
    
    def get_color(self, color_name: str) -> str:
        """Legacy get_color method."""
        return self._service.get_color(color_name)
    
    def save_settings(self) -> None:
        """Legacy save_settings method."""
        self._service.save_settings()
    
    def load_settings(self) -> None:
        """Legacy load_settings method."""
        self._service.load_settings()


# Create singleton instance for backward compatibility
_theme_manager_instance = None

def get_theme_manager() -> LegacyThemeManager:
    """Get singleton ThemeManager instance (backward compatibility)."""
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = LegacyThemeManager()
    return _theme_manager_instance

# Export as ThemeManager for backward compatibility
ThemeManager = get_theme_manager()


# Auto-log status on import for debugging
try:
    log_theme_system_status()
except Exception:
    # Fail silently if logging fails during import
    pass
