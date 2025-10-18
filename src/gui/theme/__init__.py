"""
Theme system for 3D-MM application.

Public API for theme management:
- ThemeService: Unified API for all theme operations
- ThemeManager: Low-level color management (internal)
- Presets: Built-in theme definitions
- SystemThemeDetector: OS theme detection

Usage:
    from src.gui.theme import ThemeService

    service = ThemeService.instance()
    service.apply_preset("dark")
    service.set_color("primary", "#ff0000")
    service.save_theme()
    service.enable_system_detection()

Backward Compatibility:
    from src.gui.theme import COLORS, qcolor, vtk_rgb
    from src.gui.theme import load_theme_from_settings, save_theme_to_settings
"""

# Import and expose the public API from modular components
from .theme_constants import (
    SPACING_4,
    SPACING_8,
    SPACING_12,
    SPACING_16,
    SPACING_24,
    FALLBACK_COLOR,
    hex_to_rgb,
    hex_to_qcolor,
    hex_to_vtk_rgb,
)

from .theme_defaults import ThemeDefaults

from .theme_manager_core import ThemeManager

from .theme_api import (
    COLORS,
    color,
    qcolor,
    vtk_rgb,
    theme_to_dict,
    set_theme,
    list_theme_presets,
    apply_theme_preset,
    load_theme_from_settings,
    save_theme_to_settings,
    qss_tabs_lists_labels,
)

from .theme_palette import PRESETS

# Import service and other components if they exist
try:
    from .service import ThemeService
except ImportError:
    ThemeService = None
# Try to import optional components
try:
    from .presets import (
        PRESET_LIGHT,
        PRESET_DARK,
        PRESET_HIGH_CONTRAST,
        PRESET_SOLARIZED_LIGHT,
        PRESET_SOLARIZED_DARK,
        get_preset,
        list_presets,
    )
except ImportError:
    PRESET_LIGHT = None
    PRESET_DARK = None
    PRESET_HIGH_CONTRAST = None
    PRESET_SOLARIZED_LIGHT = None
    PRESET_SOLARIZED_DARK = None
    get_preset = None
    list_presets = None

try:
    from .detector import SystemThemeDetector
except ImportError:
    SystemThemeDetector = None

try:
    from .persistence import ThemePersistence
except ImportError:
    ThemePersistence = None

try:
    from .ui import ThemeSwitcher, ThemeDialog
except ImportError:
    ThemeSwitcher = None
    ThemeDialog = None

__all__ = [
    # Service (new unified API)
    "ThemeService",

    # Manager (existing, low-level)
    "ThemeManager",
    "ThemeDefaults",

    # Colors and spacing
    "COLORS",
    "FALLBACK_COLOR",
    "SPACING_4",
    "SPACING_8",
    "SPACING_12",
    "SPACING_16",
    "SPACING_24",

    # Color conversion helpers
    "qcolor",
    "vtk_rgb",
    "hex_to_rgb",
    "hex_to_qcolor",
    "hex_to_vtk_rgb",
    "color",

    # Stylesheet helpers
    "qss_tabs_lists_labels",

    # Theme management (backward compatible)
    "theme_to_dict",
    "set_theme",
    "list_theme_presets",
    "apply_theme_preset",
    "load_theme_from_settings",
    "save_theme_to_settings",

    # Presets
    "PRESETS",
    "PRESET_LIGHT",
    "PRESET_DARK",
    "PRESET_HIGH_CONTRAST",
    "PRESET_SOLARIZED_LIGHT",
    "PRESET_SOLARIZED_DARK",
    "get_preset",
    "list_presets",

    # System detection
    "SystemThemeDetector",

    # Persistence
    "ThemePersistence",

    # UI Components
    "ThemeSwitcher",
    "ThemeDialog",
]

