"""
Theme system for Digital Workshop (Legacy Compatibility Layer).

This module provides backward-compatible access to the refactored theme system.
All functionality has been moved to modular files for better maintainability.

Backward-compatible API is preserved:
- Import hex colors for QSS (Qt Stylesheets) with: from gui.theme import COLORS
  and use Python f-strings in setStyleSheet, e.g. f"color: {COLORS.text};"
- Get QColor for Qt APIs with: from gui.theme import qcolor
- Get normalized RGB tuple (0..1) for VTK with: from gui.theme import vtk_rgb
- Load and persist theme settings: from gui.theme import load_theme_from_settings, save_theme_to_settings
- Convenience: from gui.theme import color as color_hex, hex_to_rgb

New capabilities:
- ThemeManager singleton with fallback color handling, logging, CSS template processing,
  widget registry, JSON save/load, export/import, processed CSS caching.

This file now serves as a facade/re-export point for backward compatibility.
All functionality has been extracted to separate modules following SRP.
"""

from __future__ import annotations

# ============================================================
# Import from modular theme system
# ============================================================

# Constants and color utilities
from .theme_constants import (
    FALLBACK_COLOR,  # noqa: F401 - Re-exported for backward compatibility
    SPACING_4,  # noqa: F401 - Re-exported for backward compatibility
    SPACING_8,  # noqa: F401 - Re-exported for backward compatibility
    SPACING_12,  # noqa: F401 - Re-exported for backward compatibility
    SPACING_16,  # noqa: F401 - Re-exported for backward compatibility
    SPACING_24,  # noqa: F401 - Re-exported for backward compatibility
    _normalize_hex,  # noqa: F401 - Re-exported for backward compatibility
    hex_to_rgb,  # noqa: F401 - Re-exported for backward compatibility
    hex_to_qcolor,  # noqa: F401 - Re-exported for backward compatibility
    hex_to_vtk_rgb,  # noqa: F401 - Re-exported for backward compatibility
)

# Theme defaults
from .theme_defaults import ThemeDefaults  # noqa: F401 - Re-exported for backward compatibility

# Palette generation and presets
from .theme_palette import (
    derive_mode_palette,  # noqa: F401 - Re-exported for backward compatibility
    PRESETS,  # noqa: F401 - Re-exported for backward compatibility
)

# Theme manager core
from .theme_manager_core import ThemeManager  # noqa: F401 - Re-exported for backward compatibility

# Theme API functions
from .theme_api import (
    COLORS,  # noqa: F401 - Re-exported for backward compatibility
    color,  # noqa: F401 - Re-exported for backward compatibility
    qcolor,  # noqa: F401 - Re-exported for backward compatibility
    vtk_rgb,  # noqa: F401 - Re-exported for backward compatibility
    theme_to_dict,  # noqa: F401 - Re-exported for backward compatibility
    set_theme,  # noqa: F401 - Re-exported for backward compatibility
    list_theme_presets,  # noqa: F401 - Re-exported for backward compatibility
    apply_theme_preset,  # noqa: F401 - Re-exported for backward compatibility
    load_theme_from_settings,  # noqa: F401 - Re-exported for backward compatibility
    save_theme_to_settings,  # noqa: F401 - Re-exported for backward compatibility
    qss_button_base,  # noqa: F401 - Re-exported for backward compatibility
    qss_progress_bar,  # noqa: F401 - Re-exported for backward compatibility
    qss_inputs_base,  # noqa: F401 - Re-exported for backward compatibility
    qss_tabs_lists_labels,  # noqa: F401 - Re-exported for backward compatibility
    qss_groupbox_base,  # noqa: F401 - Re-exported for backward compatibility
)

# ============================================================
# Backward Compatibility Exports
# ============================================================

__all__ = [
    # Constants
    "FALLBACK_COLOR",
    "SPACING_4",
    "SPACING_8",
    "SPACING_12",
    "SPACING_16",
    "SPACING_24",
    # Color utilities
    "_normalize_hex",
    "hex_to_rgb",
    "hex_to_qcolor",
    "hex_to_vtk_rgb",
    # Theme defaults
    "ThemeDefaults",
    # Palette and presets
    "derive_mode_palette",
    "PRESETS",
    # Theme manager
    "ThemeManager",
    # Theme API
    "COLORS",
    "color",
    "qcolor",
    "vtk_rgb",
    "theme_to_dict",
    "set_theme",
    "list_theme_presets",
    "apply_theme_preset",
    "load_theme_from_settings",
    "save_theme_to_settings",
    # QSS helpers
    "qss_button_base",
    "qss_progress_bar",
    "qss_inputs_base",
    "qss_tabs_lists_labels",
    "qss_groupbox_base",
]

