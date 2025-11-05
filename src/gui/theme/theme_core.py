"""
Consolidated theme core module for Digital Workshop.

This module consolidates the core theme functionality from:
- theme_constants.py - Constants and definitions
- theme_defaults.py - Default values and configurations
- theme_palette.py - Color palette management
- presets.py - Theme preset definitions
- persistence.py - Save/load functionality

Single Responsibility: Core theme data and configuration management.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QStandardPaths

# Import color utilities from shared utils module
# These are re-exported for backward compatibility with existing code
from utils.color_utils import (
    FALLBACK_COLOR,  # noqa: F401 - Re-exported for backward compatibility
    normalize_hex as _normalize_hex,
    hex_to_rgb,
    hex_to_qcolor,  # noqa: F401 - Re-exported for backward compatibility
    vtk_rgb as hex_to_vtk_rgb,  # noqa: F401 - Re-exported for backward compatibility
)

logger = logging.getLogger(__name__)

# ============================================================
# Spacing scale constants (px)
# ============================================================

SPACING_4 = 4
SPACING_8 = 8
SPACING_12 = 12
SPACING_16 = 16
SPACING_24 = 24


# ============================================================
# Default Theme Definitions
# ============================================================


@dataclass(frozen=True)
class ThemeDefaults:
    """Default color definitions for light theme."""

    # Window & UI Elements
    window_bg: str = "#ffffff"
    text: str = "#000000"
    text_inverse: str = "#ffffff"
    text_muted: str = "#666666"
    disabled_text: str = "#9aa0a6"

    menubar_bg: str = "#f5f5f5"
    menubar_text: str = "#000000"
    menubar_border: str = "#d0d0d0"
    menubar_item_hover_bg: str = "#0078d4"
    menubar_item_hover_text: str = "#ffffff"
    menubar_item_pressed_bg: str = "#106ebe"

    # Surfaces
    surface: str = "#f5f5f5"  # toolbars, panes
    surface_alt: str = "#ffffff"  # cards/panels inner background
    card_bg: str = "#ffffff"
    surface_grad_start: str = "#fafafa"  # subtle gradient example
    surface_grad_end: str = "#f2f2f2"

    # Toolbars
    toolbar_bg: str = "#f5f5f5"
    toolbar_border: str = "#d0d0d0"
    toolbar_handle_bg: str = "#d0d0d0"
    toolbutton_bg: str = "transparent"
    toolbutton_border: str = "transparent"
    toolbutton_hover_bg: str = "#e1e1e1"
    toolbutton_hover_border: str = "#0078d4"
    toolbutton_pressed_bg: str = "#d0d0d0"
    toolbutton_checked_bg: str = "#0078d4"
    toolbutton_checked_border: str = "#0078d4"
    toolbutton_checked_text: str = "#ffffff"

    # Status Bar
    statusbar_bg: str = "#f5f5f5"
    statusbar_text: str = "#000000"
    statusbar_border: str = "#d0d0d0"

    # Dock Widgets
    dock_bg: str = "#ffffff"
    dock_text: str = "#000000"
    dock_border: str = "#d0d0d0"
    dock_title_bg: str = "#f5f5f5"
    dock_title_border: str = "#d0d0d0"

    # Controls - Buttons (all states)
    button_bg: str = "#f5f5f5"
    button_text: str = "#000000"
    button_border: str = "#d0d0d0"
    button_hover_bg: str = "#e1e1e1"
    button_hover_border: str = "#0078d4"
    button_pressed_bg: str = "#d0d0d0"
    button_checked_bg: str = "#0078d4"
    button_checked_text: str = "#ffffff"
    button_checked_border: str = "#0078d4"
    button_default_bg: str = "#0078d4"
    button_default_text: str = "#ffffff"
    button_default_border: str = "#0078d4"
    button_default_hover_bg: str = "#106ebe"
    button_disabled_bg: str = "#f0f0f0"
    button_disabled_text: str = "#a0a0a0"
    button_disabled_border: str = "#e0e0e0"

    # Inputs & Selection
    input_bg: str = "#ffffff"
    input_text: str = "#000000"
    input_border: str = "#d0d0d0"
    input_focus_border: str = "#0078d4"
    input_disabled_bg: str = "#f5f5f5"
    input_disabled_text: str = "#a0a0a0"

    selection_bg: str = "#0078d4"
    selection_text: str = "#ffffff"

    # Combobox
    combobox_bg: str = "#ffffff"
    combobox_text: str = "#000000"
    combobox_border: str = "#d0d0d0"
    combobox_focus_border: str = "#0078d4"
    combobox_arrow_color: str = "#666666"

    # Progress Bar
    progress_bg: str = "#ffffff"
    progress_text: str = "#000000"
    progress_border: str = "#d0d0d0"
    progress_chunk: str = "#0078d4"
    progress_disabled_border: str = "#e0e0e0"
    progress_disabled_bg: str = "#f5f5f5"
    progress_disabled_text: str = "#a0a0a0"
    progress_disabled_chunk: str = "#d0d0d0"

    # Tabs
    tab_pane_border: str = "#d0d0d0"
    tab_pane_bg: str = "#ffffff"
    tab_bg: str = "#f5f5f5"
    tab_text: str = "#000000"
    tab_border: str = "#d0d0d0"
    tab_selected_bg: str = "#ffffff"
    tab_selected_border: str = "#0078d4"
    tab_hover_bg: str = "#e1e1e1"

    # Tables & Lists
    table_bg: str = "#ffffff"
    table_text: str = "#000000"
    table_border: str = "#d0d0d0"
    table_gridline: str = "#e0e0e0"
    table_alternate_row_bg: str = "#f5f5f5"
    header_bg: str = "#f5f5f5"
    header_text: str = "#000000"
    header_border: str = "#d0d0d0"

    # Scrollbars
    scrollbar_bg: str = "#f5f5f5"
    scrollbar_border: str = "#d0d0d0"
    scrollbar_handle_bg: str = "#d0d0d0"
    scrollbar_handle_hover_bg: str = "#a0a0a0"

    # Splitters
    splitter_handle_bg: str = "#d0d0d0"

    # Group Boxes
    groupbox_border: str = "#d0d0d0"
    groupbox_bg: str = "#ffffff"
    groupbox_text: str = "#000000"
    groupbox_title_text: str = "#000000"

    # Checkboxes & Radios
    checkbox_unchecked_border: str = "#d0d0d0"
    checkbox_unchecked_bg: str = "#ffffff"
    checkbox_checked_border: str = "#0078d4"
    checkbox_checked_bg: str = "#0078d4"

    radio_unchecked_border: str = "#d0d0d0"
    radio_unchecked_bg: str = "#ffffff"
    radio_checked_border: str = "#0078d4"
    radio_checked_bg: str = "#0078d4"

    # Spin Boxes & Sliders
    spinbox_bg: str = "#ffffff"
    spinbox_text: str = "#000000"
    spinbox_border: str = "#d0d0d0"
    spinbox_focus_border: str = "#0078d4"

    slider_groove_bg: str = "#f5f5f5"
    slider_groove_border: str = "#d0d0d0"
    slider_handle: str = "#0078d4"  # legacy name preserved
    slider_handle_border: str = "#0078d4"

    # Date/Time Edits
    dateedit_bg: str = "#ffffff"
    dateedit_text: str = "#000000"
    dateedit_border: str = "#d0d0d0"
    dateedit_focus_border: str = "#0078d4"

    # Labels
    label_text: str = "#000000"

    # Status Indicators
    success: str = "#52c41a"
    warning: str = "#faad14"
    error: str = "#ff4d4f"

    status_good_bg: str = "#d4edda"
    status_good_text: str = "#155724"
    status_good_border: str = "#c3e6cb"

    status_warning_bg: str = "#fff3cd"
    status_warning_text: str = "#856404"
    status_warning_border: str = "#ffeeba"

    status_error_bg: str = "#f8d7da"
    status_error_text: str = "#721c24"
    status_error_border: str = "#f5c6cb"

    # Loading Overlay / Misc
    loading_overlay_bg_rgba: str = "rgba(255, 255, 255, 0.8)"

    # Accent / Brand
    primary: str = "#0078d4"
    primary_hover: str = "#106ebe"
    primary_text: str = "#ffffff"

    # Interactions
    hover: str = "#e1e1e1"
    pressed: str = "#d0d0d0"

    # Viewer / 3D
    canvas_bg: str = "#f0f0f0"
    model_surface: str = "#6496c8"  # Approx (100,150,200)
    model_ambient: str = "#324b64"  # Approx (50,75,100)
    model_specular: str = "#ffffff"
    light_color: str = "#ffffff"
    edge_color: str = "#000000"

    # Stars / Ratings
    star_filled: str = "#ffd700"
    star_empty: str = "#c8c8c8"
    star_hover: str = "#ffeb64"

    # Borders & Dividers
    border: str = "#d0d0d0"
    border_light: str = "#f0f0f0"
    focus_border: str = "#2684ff"


# ============================================================
# Palette Generation Functions
# ============================================================


def _srgb_to_linear(c: float) -> float:
    """Convert 0..1 sRGB channel to linear space."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance_from_hex(h: str) -> float:
    """WCAG relative luminance of a hex color."""
    try:
        r, g, b = hex_to_rgb(h)
    except Exception:
        return 0.5
    rl = _srgb_to_linear(r / 255.0)
    gl = _srgb_to_linear(g / 255.0)
    bl = _srgb_to_linear(b / 255.0)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def _choose_text_for_bg(bg_hex: str) -> str:
    """Choose black or white text for contrast against given background."""
    return "#000000" if _relative_luminance_from_hex(bg_hex) >= 0.5 else "#ffffff"


def _mix_hex(a_hex: str, b_hex: str, t: float) -> str:
    """Linear mix of two hex colors a..b with t in [0..1]."""
    a_r, a_g, a_b = hex_to_rgb(a_hex)
    b_r, b_g, b_b = hex_to_rgb(b_hex)
    r = int(round(a_r + (b_r - a_r) * t))
    g = int(round(a_g + (b_g - a_g) * t))
    b = int(round(a_b + (b_b - a_b) * t))
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_code: str, amount: float) -> str:
    """Lighten color by mixing with white."""
    return _mix_hex(hex_code, "#ffffff", min(max(amount, 0.0), 1.0))


def _darken(hex_code: str, amount: float) -> str:
    """Darken color by mixing with black."""
    return _mix_hex(hex_code, "#000000", min(max(amount, 0.0), 1.0))


def derive_mode_palette(seed_primary: str, mode: str = "auto") -> Dict[str, str]:
    """
    Generate a cohesive palette from a seed primary color.
    mode: 'auto' | 'light' | 'dark'
    """
    p = _normalize_hex(seed_primary)
    if not p.startswith("#") or len(p) != 7:
        p = ThemeDefaults.primary  # fallback to sane primary

    # Decide dark vs light
    if mode not in {"auto", "light", "dark"}:
        mode = "auto"
    if mode == "auto":
        # Brighter primaries work well with light UI by default
        dark = _relative_luminance_from_hex(p) < 0.35
    else:
        dark = mode == "dark"

    if dark:
        window_bg = "#1e1f22"
        surface = "#2a2d2f"
        text = "#eaeaea"
        border = "#3a3d40"
        border_light = "#2f3235"
        table_alt = "#25282a"
        primary_hover = _lighten(p, 0.12)
        hover = _lighten(surface, 0.06)
        pressed = _darken(surface, 0.06)
        input_bg = "#232527"
        header_bg = "#2f3133"
    else:
        window_bg = "#ffffff"
        surface = "#f5f6f7"
        text = "#212529"
        border = "#d0d0d0"
        border_light = "#f0f0f0"
        table_alt = "#f8f9fa"
        primary_hover = _darken(p, 0.12)
        hover = "#e9ecef"
        pressed = "#dfe3e6"
        input_bg = "#ffffff"
        header_bg = "#f5f6f7"

    selection_bg = p
    selection_text = _choose_text_for_bg(selection_bg)
    primary_text = _choose_text_for_bg(p)

    # A practical subset that drives most of the UI cohesively
    derived: Dict[str, str] = {
        # Core
        "primary": p,
        "primary_hover": primary_hover,
        "primary_text": primary_text,
        "window_bg": window_bg,
        "surface": surface,
        "text": text,
        "border": border,
        "border_light": border_light,
        "hover": hover,
        "pressed": pressed,
        "selection_bg": selection_bg,
        "selection_text": selection_text,
        # Menubar
        "menubar_bg": surface,
        "menubar_text": text,
        "menubar_border": border,
        "menubar_item_hover_bg": p,
        "menubar_item_hover_text": primary_text,
        "menubar_item_pressed_bg": primary_hover,
        # Status bar
        "statusbar_bg": surface,
        "statusbar_text": text,
        "statusbar_border": border,
        # Toolbars
        "toolbar_bg": surface,
        "toolbar_border": border,
        "toolbar_handle_bg": border,
        "toolbutton_bg": "transparent",
        "toolbutton_border": "transparent",
        "toolbutton_hover_bg": hover,
        "toolbutton_hover_border": p,
        "toolbutton_pressed_bg": pressed,
        "toolbutton_checked_bg": p,
        "toolbutton_checked_border": p,
        "toolbutton_checked_text": primary_text,
        # Dock
        "dock_bg": window_bg,
        "dock_text": text,
        "dock_border": border,
        "dock_title_bg": surface,
        "dock_title_border": border,
        # Buttons
        "button_bg": surface,
        "button_text": text,
        "button_border": border,
        "button_hover_bg": hover,
        "button_hover_border": p,
        "button_pressed_bg": pressed,
        "button_checked_bg": p,
        "button_checked_text": primary_text,
        "button_checked_border": p,
        "button_default_bg": p,
        "button_default_text": primary_text,
        "button_default_border": p,
        "button_default_hover_bg": primary_hover,
        "button_disabled_bg": _mix_hex(surface, border_light, 0.5),
        "button_disabled_text": "#9aa0a6",
        "button_disabled_border": _lighten(border, 0.2),
        # Inputs
        "input_bg": input_bg,
        "input_text": text,
        "input_border": border,
        "input_focus_border": p,
        "input_disabled_bg": _mix_hex(input_bg, border_light, 0.3),
        "input_disabled_text": "#9aa0a6",
        # Combo
        "combobox_bg": input_bg,
        "combobox_text": text,
        "combobox_border": border,
        "combobox_focus_border": p,
        "combobox_arrow_color": "#666666" if not dark else "#b7b7b7",
        # Progress
        "progress_bg": window_bg,
        "progress_text": text,
        "progress_border": border,
        "progress_chunk": p,
        "progress_disabled_border": (_lighten(border, 0.15) if not dark else _darken(border, 0.15)),
        "progress_disabled_bg": _mix_hex(window_bg, surface, 0.5),
        "progress_disabled_text": "#a0a0a0",
        "progress_disabled_chunk": _mix_hex(p, surface, 0.65),
        # Tabs
        "tab_pane_border": border,
        "tab_pane_bg": window_bg,
        "tab_bg": surface,
        "tab_text": text,
        "tab_border": border,
        "tab_selected_bg": window_bg,
        "tab_selected_border": p,
        "tab_hover_bg": hover,
        # Tables & Lists
        "table_bg": window_bg,
        "table_text": text,
        "table_border": border,
        "table_gridline": _lighten(border, 0.2) if not dark else _darken(border, 0.2),
        "table_alternate_row_bg": table_alt,
        "header_bg": header_bg,
        "header_text": text,
        "header_border": border,
        # Scrollbars
        "scrollbar_bg": surface,
        "scrollbar_border": border,
        "scrollbar_handle_bg": _mix_hex(border, p, 0.10),
        "scrollbar_handle_hover_bg": _mix_hex(border, p, 0.25),
        # Splitters
        "splitter_handle_bg": border,
        # Group Boxes
        "groupbox_border": border,
        "groupbox_bg": window_bg,
        "groupbox_text": text,
        "groupbox_title_text": text,
        # Slider & Spinbox
        "slider_groove_bg": surface,
        "slider_groove_border": border,
        "slider_handle": p,
        "slider_handle_border": p,
        "spinbox_bg": input_bg,
        "spinbox_text": text,
        "spinbox_border": border,
        "spinbox_focus_border": p,
        # Date edits
        "dateedit_bg": input_bg,
        "dateedit_text": text,
        "dateedit_border": border,
        "dateedit_focus_border": p,
        # Labels
        "label_text": text,
        # Focus
        "focus_border": _mix_hex(p, "#2684ff", 0.5),
    }
    return derived


# ============================================================
# Theme Presets
# ============================================================

# Modern preset - professional blue scheme
PRESET_MODERN: Dict[str, str] = {
    "primary": "#0078d4",
    "primary_hover": "#106ebe",
    "primary_text": "#ffffff",
    "window_bg": "#ffffff",
    "surface": "#f5f6f7",
    "text": "#323130",
    "border": "#edebe9",
    "border_light": "#f4f3f2",
    "hover": "#e9ecef",
    "pressed": "#dfe3e6",
    "selection_bg": "#0078d4",
    "selection_text": "#ffffff",
    "focus_border": "#2684ff",
}

# High contrast preset - accessibility focused
PRESET_HIGH_CONTRAST: Dict[str, str] = {
    "window_bg": "#000000",
    "text": "#ffffff",
    "primary": "#ffff00",
    "primary_hover": "#ffea00",
    "primary_text": "#000000",
    "surface": "#000000",
    "border": "#ffffff",
    "border_light": "#e0e0e0",
    "hover": "#ffffff",
    "pressed": "#c0c0c0",
    "selection_bg": "#ffff00",
    "selection_text": "#000000",
    "focus_border": "#ffffff",
    "menubar_bg": "#000000",
    "menubar_text": "#ffffff",
    "menubar_item_hover_bg": "#ffff00",
    "menubar_item_hover_text": "#000000",
}

# Light Theme Preset (Default)
PRESET_LIGHT: Dict[str, str] = {
    # Window & UI
    "window_bg": "#ffffff",
    "text": "#000000",
    "surface": "#f5f5f5",
    "surface_grad_start": "#f9f9f9",
    "surface_grad_end": "#f0f0f0",
    # Borders & Dividers
    "border": "#d0d0d0",
    "border_light": "#e8e8e8",
    "focus_border": "#0078d4",
    # Menu & Toolbar
    "menubar_bg": "#f5f5f5",
    "menubar_text": "#000000",
    "menubar_item_hover_bg": "#e1e1e1",
    "menubar_item_hover_text": "#000000",
    "toolbar_bg": "#f5f5f5",
    "toolbar_text": "#000000",
    # Status Bar
    "statusbar_bg": "#f5f5f5",
    "statusbar_text": "#000000",
    "statusbar_border": "#d0d0d0",
    # Dock Widgets
    "dock_title_bg": "#e8e8e8",
    "dock_title_text": "#000000",
    "dock_title_border": "#d0d0d0",
    # Buttons
    "button_default_bg": "#f0f0f0",
    "button_default_text": "#000000",
    "button_default_border": "#d0d0d0",
    "button_hover_bg": "#e1e1e1",
    "button_hover_text": "#000000",
    "button_pressed_bg": "#d0d0d0",
    "button_pressed_text": "#000000",
    # Inputs
    "input_bg": "#ffffff",
    "input_text": "#000000",
    "input_border": "#d0d0d0",
    "input_focus_border": "#0078d4",
    # Accent / Brand
    "primary": "#0078d4",
    "primary_hover": "#106ebe",
    "primary_text": "#ffffff",
    # Interactions
    "hover": "#e1e1e1",
    "pressed": "#d0d0d0",
    "selection_bg": "#0078d4",
    "selection_text": "#ffffff",
    # Viewer / 3D
    "canvas_bg": "#f0f0f0",
    "model_surface": "#6496c8",
    "model_ambient": "#324b64",
    "model_specular": "#ffffff",
    "light_color": "#ffffff",
    "edge_color": "#000000",
    # Status Indicators
    "status_success_bg": "#d4edda",
    "status_success_text": "#155724",
    "status_success_border": "#c3e6cb",
    "status_warning_bg": "#fff3cd",
    "status_warning_text": "#856404",
    "status_warning_border": "#ffeaa7",
    "status_error_bg": "#f8d7da",
    "status_error_text": "#721c24",
    "status_error_border": "#f5c6cb",
}

# Dark Theme Preset
PRESET_DARK: Dict[str, str] = {
    # Window & UI
    "window_bg": "#1e1e1e",
    "text": "#e0e0e0",
    "surface": "#2d2d2d",
    "surface_grad_start": "#333333",
    "surface_grad_end": "#2a2a2a",
    # Borders & Dividers
    "border": "#404040",
    "border_light": "#555555",
    "focus_border": "#0078d4",
    # Menu & Toolbar
    "menubar_bg": "#2d2d2d",
    "menubar_text": "#e0e0e0",
    "menubar_item_hover_bg": "#404040",
    "menubar_item_hover_text": "#ffffff",
    "toolbar_bg": "#2d2d2d",
    "toolbar_text": "#e0e0e0",
    # Status Bar
    "statusbar_bg": "#2d2d2d",
    "statusbar_text": "#e0e0e0",
    "statusbar_border": "#404040",
    # Dock Widgets
    "dock_title_bg": "#333333",
    "dock_title_text": "#e0e0e0",
    "dock_title_border": "#404040",
    # Buttons
    "button_default_bg": "#333333",
    "button_default_text": "#e0e0e0",
    "button_default_border": "#404040",
    "button_hover_bg": "#404040",
    "button_hover_text": "#ffffff",
    "button_pressed_bg": "#555555",
    "button_pressed_text": "#ffffff",
    # Inputs
    "input_bg": "#2a2a2a",
    "input_text": "#e0e0e0",
    "input_border": "#404040",
    "input_focus_border": "#0078d4",
    # Accent / Brand
    "primary": "#0078d4",
    "primary_hover": "#1084d7",
    "primary_text": "#ffffff",
    # Interactions
    "hover": "#404040",
    "pressed": "#555555",
    "selection_bg": "#0078d4",
    "selection_text": "#ffffff",
    # Viewer / 3D
    "canvas_bg": "#1a1a1a",
    "model_surface": "#6496c8",
    "model_ambient": "#324b64",
    "model_specular": "#ffffff",
    "light_color": "#ffffff",
    "edge_color": "#cccccc",
    # Status Indicators
    "status_success_bg": "#1e4620",
    "status_success_text": "#90ee90",
    "status_success_border": "#2d5a2d",
    "status_warning_bg": "#4d3d00",
    "status_warning_text": "#ffeb99",
    "status_warning_border": "#664d00",
    "status_error_bg": "#4d1a1a",
    "status_error_text": "#ff6b6b",
    "status_error_border": "#802020",
}

# Solarized Light Theme Preset
PRESET_SOLARIZED_LIGHT: Dict[str, str] = {
    # Window & UI
    "window_bg": "#fdf6e3",
    "text": "#657b83",
    "surface": "#eee8d5",
    "surface_grad_start": "#f5f0e8",
    "surface_grad_end": "#ebe6d9",
    # Borders & Dividers
    "border": "#d6d0c8",
    "border_light": "#e8e3db",
    "focus_border": "#268bd2",
    # Menu & Toolbar
    "menubar_bg": "#eee8d5",
    "menubar_text": "#657b83",
    "menubar_item_hover_bg": "#d6d0c8",
    "menubar_item_hover_text": "#073642",
    "toolbar_bg": "#eee8d5",
    "toolbar_text": "#657b83",
    # Status Bar
    "statusbar_bg": "#eee8d5",
    "statusbar_text": "#657b83",
    "statusbar_border": "#d6d0c8",
    # Dock Widgets
    "dock_title_bg": "#d6d0c8",
    "dock_title_text": "#657b83",
    "dock_title_border": "#c5bfb7",
    # Buttons
    "button_default_bg": "#eee8d5",
    "button_default_text": "#657b83",
    "button_default_border": "#d6d0c8",
    "button_hover_bg": "#d6d0c8",
    "button_hover_text": "#073642",
    "button_pressed_bg": "#c5bfb7",
    "button_pressed_text": "#073642",
    # Inputs
    "input_bg": "#fdf6e3",
    "input_text": "#657b83",
    "input_border": "#d6d0c8",
    "input_focus_border": "#268bd2",
    # Accent / Brand
    "primary": "#268bd2",
    "primary_hover": "#2aa198",
    "primary_text": "#fdf6e3",
    # Interactions
    "hover": "#d6d0c8",
    "pressed": "#c5bfb7",
    "selection_bg": "#268bd2",
    "selection_text": "#fdf6e3",
    # Viewer / 3D
    "canvas_bg": "#eee8d5",
    "model_surface": "#268bd2",
    "model_ambient": "#073642",
    "model_specular": "#fdf6e3",
    "light_color": "#fdf6e3",
    "edge_color": "#073642",
    # Status Indicators
    "status_success_bg": "#d5f4e6",
    "status_success_text": "#27ae60",
    "status_success_border": "#a9dfbf",
    "status_warning_bg": "#fef5e7",
    "status_warning_text": "#d68910",
    "status_warning_border": "#f8c471",
    "status_error_bg": "#fadbd8",
    "status_error_text": "#c0392b",
    "status_error_border": "#f5b7b1",
}

# Solarized Dark Theme Preset
PRESET_SOLARIZED_DARK: Dict[str, str] = {
    # Window & UI
    "window_bg": "#002b36",
    "text": "#839496",
    "surface": "#073642",
    "surface_grad_start": "#0d3f47",
    "surface_grad_end": "#0a3840",
    # Borders & Dividers
    "border": "#1a4d56",
    "border_light": "#2a5f68",
    "focus_border": "#268bd2",
    # Menu & Toolbar
    "menubar_bg": "#073642",
    "menubar_text": "#839496",
    "menubar_item_hover_bg": "#1a4d56",
    "menubar_item_hover_text": "#93a1a1",
    "toolbar_bg": "#073642",
    "toolbar_text": "#839496",
    # Status Bar
    "statusbar_bg": "#073642",
    "statusbar_text": "#839496",
    "statusbar_border": "#1a4d56",
    # Dock Widgets
    "dock_title_bg": "#0d3f47",
    "dock_title_text": "#839496",
    "dock_title_border": "#1a4d56",
    # Buttons
    "button_default_bg": "#073642",
    "button_default_text": "#839496",
    "button_default_border": "#1a4d56",
    "button_hover_bg": "#1a4d56",
    "button_hover_text": "#93a1a1",
    "button_pressed_bg": "#2a5f68",
    "button_pressed_text": "#93a1a1",
    # Inputs
    "input_bg": "#002b36",
    "input_text": "#839496",
    "input_border": "#1a4d56",
    "input_focus_border": "#268bd2",
    # Accent / Brand
    "primary": "#268bd2",
    "primary_hover": "#2aa198",
    "primary_text": "#002b36",
    # Interactions
    "hover": "#1a4d56",
    "pressed": "#2a5f68",
    "selection_bg": "#268bd2",
    "selection_text": "#002b36",
    # Viewer / 3D
    "canvas_bg": "#002b36",
    "model_surface": "#268bd2",
    "model_ambient": "#073642",
    "model_specular": "#93a1a1",
    "light_color": "#93a1a1",
    "edge_color": "#839496",
    # Status Indicators
    "status_success_bg": "#0d3f2d",
    "status_success_text": "#2ecc71",
    "status_success_border": "#1a5f3f",
    "status_warning_bg": "#3f3d0d",
    "status_warning_text": "#f1c40f",
    "status_warning_border": "#5f5f1a",
    "status_error_bg": "#3f0d0d",
    "status_error_text": "#e74c3c",
    "status_error_border": "#5f1a1a",
}

# Preset Registry
PRESETS: Dict[str, Dict[str, str]] = {
    "light": PRESET_LIGHT,
    "dark": PRESET_DARK,
    "high_contrast": PRESET_HIGH_CONTRAST,
    "solarized_light": PRESET_SOLARIZED_LIGHT,
    "solarized_dark": PRESET_SOLARIZED_DARK,
    "modern": PRESET_MODERN,
}

# Additional palette presets
PALETTE_PRESETS: Dict[str, Dict[str, str]] = {
    "modern": PRESET_MODERN,
    "high_contrast": PRESET_HIGH_CONTRAST,
}


def get_preset(name: str) -> Dict[str, str]:
    """Get a preset by name. Returns light preset if not found."""
    return PRESETS.get(name, PRESET_LIGHT)


def list_presets() -> list[str]:
    """List all available preset names."""
    return list(PRESETS.keys())


# ============================================================
# Theme Persistence
# ============================================================


class ThemePersistence:
    """
    Handles theme persistence operations:
    - Save theme to AppData
    - Load theme from AppData
    - Export theme to JSON file
    - Import theme from JSON file
    """

    THEME_FILENAME = "theme.json"

    def __init__(self) -> None:
        """Initialize persistence handler."""
        self._app_data_path = self._get_app_data_path()

    def _get_app_data_path(self) -> Path:
        """Get the application data directory path."""
        app_data = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        path = Path(app_data)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_theme_file_path(self) -> Path:
        """Get the path to the theme.json file in AppData."""
        return self._app_data_path / self.THEME_FILENAME

    def save_theme(self, colors: Dict[str, str]) -> None:
        """
        Save theme colors to AppData/theme.json.

        Args:
            colors: Dictionary of color variable names to hex values

        Raises:
            IOError: If file cannot be written
        """
        try:
            path = self._get_theme_file_path()

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(colors, f, indent=2)

            logger.info("Theme saved to %s", path)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to save theme: %s", e)
            raise

    def load_theme(self) -> Optional[Dict[str, str]]:
        """
        Load theme colors from AppData/theme.json.

        Returns:
            Dictionary of colors, or None if file doesn't exist or is invalid
        """
        try:
            path = self._get_theme_file_path()

            if not path.exists():
                logger.debug("Theme file not found: %s", path)
                return None

            with open(path, "r", encoding="utf-8") as f:
                colors = json.load(f)

            if not isinstance(colors, dict):
                logger.warning("Theme file contains invalid data: %s", path)
                return None

            logger.info("Theme loaded from %s", path)
            return colors
        except json.JSONDecodeError as e:
            logger.error("Failed to parse theme file: %s", e)
            return None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to load theme: %s", e)
            return None

    def export_theme(self, path: Path, colors: Dict[str, str]) -> None:
        """
        Export theme colors to a JSON file.

        Args:
            path: Path to export to
            colors: Dictionary of color variable names to hex values

        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure .json extension
            if path.suffix.lower() != ".json":
                path = path.with_suffix(".json")

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(colors, f, indent=2)

            logger.info("Theme exported to %s", path)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to export theme: %s", e)
            raise

    def import_theme(self, path: Path) -> Optional[Dict[str, str]]:
        """
        Import theme colors from a JSON file.

        Args:
            path: Path to import from

        Returns:
            Dictionary of colors, or None if file is invalid

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            if not path.exists():
                raise FileNotFoundError(f"Theme file not found: {path}")

            with open(path, "r", encoding="utf-8") as f:
                colors = json.load(f)

            if not isinstance(colors, dict):
                logger.warning("Theme file contains invalid data: %s", path)
                return None

            logger.info("Theme imported from %s", path)
            return colors
        except json.JSONDecodeError as e:
            logger.error("Failed to parse theme file: %s", e)
            raise
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to import theme: %s", e)
            raise

    def theme_exists(self) -> bool:
        """Check if a saved theme exists in AppData."""
        return self._get_theme_file_path().exists()

    def get_app_data_path(self) -> Path:
        """Get the application data directory path."""
        return self._app_data_path
