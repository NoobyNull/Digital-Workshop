"""
Theme palette derivation and presets.

Provides functions to generate cohesive color palettes from seed colors
and built-in theme presets (modern, high contrast, etc.).
"""

from typing import Dict

from .theme_constants import _normalize_hex, hex_to_rgb
from .presets import (
    PRESET_LIGHT,
    PRESET_DARK,
    PRESET_HIGH_CONTRAST as PRESET_HIGH_CONTRAST_MAIN,
    PRESET_SOLARIZED_LIGHT,
    PRESET_SOLARIZED_DARK,
)


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
    from .theme_defaults import ThemeDefaults

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
        "progress_disabled_border": (
            _lighten(border, 0.15) if not dark else _darken(border, 0.15)
        ),
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

# Merge all presets: main presets + palette-specific presets
PRESETS: Dict[str, Dict[str, str]] = {
    # Main presets from presets.py
    "light": PRESET_LIGHT,
    "dark": PRESET_DARK,
    "high_contrast": PRESET_HIGH_CONTRAST_MAIN,
    "solarized_light": PRESET_SOLARIZED_LIGHT,
    "solarized_dark": PRESET_SOLARIZED_DARK,
    # Palette-specific presets
    "modern": PRESET_MODERN,
}
