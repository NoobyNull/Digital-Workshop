"""
Theme system for Digital Workshop (Facade).

This module provides backward-compatible access to the refactored theme system.
All functionality has been moved to src/gui/theme/ package for better modularity.

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
"""

# Re-export all public API from the modular theme package
from src.gui.theme.theme_constants import (
    SPACING_4,
    SPACING_8,
    SPACING_12,
    SPACING_16,
    SPACING_24,
    MIN_WIDGET_SIZE,
    FALLBACK_COLOR,
    _normalize_hex,
    hex_to_rgb,
    hex_to_qcolor,
    hex_to_vtk_rgb,
)

from src.gui.theme.theme_defaults import ThemeDefaults

from src.gui.theme.theme_palette import (
    derive_mode_palette,
    PRESETS,
)

from src.gui.theme.theme_manager_core import ThemeManager

from src.gui.theme.theme_api import (
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
    qss_button_base,
    qss_progress_bar,
    qss_inputs_base,
    qss_tabs_lists_labels,
    qss_groupbox_base,
)

__all__ = [
    "SPACING_4",
    "SPACING_8",
    "SPACING_12",
    "SPACING_16",
    "SPACING_24",
    "MIN_WIDGET_SIZE",
    "FALLBACK_COLOR",
    "_normalize_hex",
    "hex_to_rgb",
    "hex_to_qcolor",
    "hex_to_vtk_rgb",
    "ThemeDefaults",
    "ThemeManager",
    "derive_mode_palette",
    "PRESETS",
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
    "qss_button_base",
    "qss_progress_bar",
    "qss_inputs_base",
    "qss_tabs_lists_labels",
    "qss_groupbox_base",
]
