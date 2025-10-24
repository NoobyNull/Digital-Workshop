"""
Theme system for Digital Workshop.

Centralizes ALL UI colors as variables and provides helpers to use them
consistently across Qt widgets, Qt3D, and VTK. This makes the color scheme
easy to tweak, ensures readability, and supports future theming.

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

from __future__ import annotations

import json
import logging
import re
import time
import weakref
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QColor

# ============================================================
# Spacing scale constants (px)
# ============================================================

SPACING_4 = 4
SPACING_8 = 8
SPACING_12 = 12
SPACING_16 = 16
SPACING_24 = 24

# ============================================================
# Fallback color for undefined variables
# ============================================================

FALLBACK_COLOR = "#E31C79"  # Hot pink for undefined colors


# ============================================================
# Helpers
# ============================================================

def _normalize_hex(h: str) -> str:
    """
    Return a normalized #rrggbb hex string for inputs that look like hex codes.
    If the input does not represent a hex color (e.g., 'rgba(255,255,255,0.8)' or CSS keywords like 'transparent'),
    return it unchanged.
    """
    if not h:
        return FALLBACK_COLOR

    s = str(h).strip()
    lower = s.lower()

    # Pass through CSS color functions and keywords without modification
    css_keywords = {"transparent", "inherit", "initial", "unset", "currentcolor"}
    if lower.startswith("rgba(") or lower.startswith("rgb(") or lower in css_keywords:
        return lower

    # If already a valid #rrggbb, return normalized lowercase
    if lower.startswith("#") and len(lower) == 7 and all(c in "0123456789abcdef" for c in lower[1:]):
        return lower

    # Accept 3 or 6 hex digits with optional '#'
    # Examples: abc, #abc, a1b2c3, #a1b2c3
    m = re.fullmatch(r"#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", s)
    if m:
        hex_digits = m.group(1)
        if len(hex_digits) == 3:
            r, g, b = hex_digits[0], hex_digits[1], hex_digits[2]
            return f"#{r}{r}{g}{g}{b}{b}".lower()
        return f"#{hex_digits}".lower()

    # Unknown/unsupported format: return as-is to let QSS handle or upstream validate
    return s


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert #rrggbb to integer RGB tuple (0..255)."""
    h = _normalize_hex(hex_code)
    if not h.startswith("#") or len(h) != 7:
        raise ValueError(f"hex_to_rgb expects #rrggbb, got {hex_code!r}")
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def hex_to_qcolor(hex_code: str) -> QColor:
    """Convert #rrggbb to QColor."""
    r, g, b = hex_to_rgb(hex_code)
    return QColor(r, g, b)


def hex_to_vtk_rgb(hex_code: str) -> Tuple[float, float, float]:
    """Convert #rrggbb to normalized RGB tuple (0..1) for VTK."""
    r, g, b = hex_to_rgb(hex_code)
    return (r / 255.0, g / 255.0, b / 255.0)


# ============================================================
# Comprehensive Theme Defaults
# Grouped by functional categories to align with stylesheet
# ============================================================

@dataclass(frozen=True)
class ThemeDefaults:
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
    surface: str = "#f5f5f5"            # toolbars, panes
    surface_alt: str = "#ffffff"        # cards/panels inner background
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
# Preset utilities and built-in presets
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
        dark = (mode == "dark")

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
        "progress_disabled_border": _lighten(border, 0.15) if not dark else _darken(border, 0.15),
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

PRESETS: Dict[str, Dict[str, str]] = {
    "modern": PRESET_MODERN,
    "high_contrast": PRESET_HIGH_CONTRAST,
}

# ============================================================
# ThemeManager Singleton
# ============================================================

class ThemeManager:
    """
    ThemeManager provides:
    - Central color registry with descriptive variable names
    - Fallback handling for undefined variables (returns FALLBACK_COLOR, logs WARNING)
    - CSS template processing for {{VARIABLE_NAME}} replacement
    - Processed CSS caching by file mtime and theme version for performance
    - Widget registry for applying/re-applying stylesheets
    - JSON theme save/load plus export/import helpers
    """

    _instance: Optional["ThemeManager"] = None

    VARIABLE_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

    def __init__(self) -> None:
        self._logger = logging.getLogger("gui.theme")
        self._colors: Dict[str, str] = {k: _normalize_hex(v) for k, v in asdict(ThemeDefaults()).items()}
        self._version: int = 0  # bump whenever theme is updated
        self._preset_name: str = "custom"  # last applied preset name
        # CSS caches
        self._css_file_cache: Dict[str, Tuple[float, int, str]] = {}  # path -> (mtime, version, processed_css)
        self._css_text_cache: Dict[str, Tuple[int, str]] = {}  # key -> (version, processed_css)
        # Widget registry: weak refs to (widget, css_path, css_text)
        self._widgets: "weakref.WeakSet[Any]" = weakref.WeakSet()
        self._widget_sources: Dict[int, Tuple[Optional[str], Optional[str]]] = {}

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    # ------------- Logging helpers -------------

    def _log_json(self, level: int, event: str, **kwargs: Any) -> None:
        """
        Emit structured JSON logs. Upstream logging_config can format as JSON;
        to be safe, we serialize here as well.
        """
        payload = {"event": event, "ts": int(time.time() * 1000), **kwargs}
        self._logger.log(level, json.dumps(payload, ensure_ascii=False))

    # ------------- Color access -------------

    @property
    def colors(self) -> Dict[str, str]:
        """Return a copy of the color registry."""
        return dict(self._colors)

    def get_color(self, name: str, *, context: Optional[str] = None) -> str:
        """
        Get a color by name.
        - If found and is hex-like, return normalized #rrggbb
        - If found and is non-hex (e.g., rgba), return as-is
        - If not found, return FALLBACK_COLOR and log WARNING
        """
        if name in self._colors:
            return _normalize_hex(self._colors[name])
        self._log_json(logging.WARNING, "theme_fallback_color", variable=name, context=context or "")
        return FALLBACK_COLOR

    def set_colors(self, overrides: Dict[str, Any]) -> None:
        """
        Update known colors with overrides, ignoring unknown keys to preserve stability.
        Values may be hex or other CSS color strings; we normalize hex at access time.
        """
        changed = False
        for k, v in overrides.items():
            if k in self._colors:
                self._colors[k] = str(v).strip()
                changed = True
        if changed:
            self._version += 1
            # Invalidate caches
            self._css_file_cache.clear()
            self._css_text_cache.clear()
            self._log_json(logging.INFO, "theme_updated", changed_keys=[k for k in overrides.keys() if k in self._colors])

    # ------------- Presets API -------------
    def available_presets(self) -> list[str]:
        """Return list of available built-in theme presets."""
        return sorted(list(PRESETS.keys()) + ["custom"])

    @property
    def current_preset(self) -> str:
        """Name of the last applied preset. 'custom' when user edited manually."""
        return getattr(self, "_preset_name", "custom")

    def apply_preset(self, preset_name: str, *, custom_mode: Optional[str] = None, base_primary: Optional[str] = None) -> None:
        """
        Apply a named preset.
        - preset_name: 'modern', 'high_contrast', or 'custom'
        - custom_mode: for 'custom', one of {'auto','light','dark'}
        - base_primary: optional primary color seed for 'custom'

        For built-in presets: derives a full palette then applies preset key colors on top
        to ensure all 148 variables are cohesive.
        """
        name = (preset_name or "custom").lower()
        if name in PRESETS:
            preset_colors = PRESETS[name]
            # Derive full palette from preset's primary color
            primary = preset_colors.get("primary", ThemeDefaults.primary)
            mode = "dark" if preset_colors.get("window_bg", "#ffffff").lower() == "#000000" else "auto"
            derived = derive_mode_palette(primary, mode=mode)

            # Merge: derived palette first, then preset overrides on top
            merged = {**derived, **preset_colors}
            self.set_colors(merged)

            self._preset_name = name
            self._log_json(logging.INFO, "theme_preset_applied", preset=name, colors_defined=len(merged))
            return

        # Custom derived theme
        mode = (custom_mode or "auto").lower()
        seed = base_primary or self._colors.get("primary", ThemeDefaults.primary)
        derived = derive_mode_palette(seed, mode=mode)
        self.set_colors(derived)
        self._preset_name = "custom"
        self._log_json(logging.INFO, "theme_preset_applied", preset="custom", mode=mode, seed=seed)

    # ------------- QColor / VTK helpers -------------

    def qcolor(self, name: str) -> QColor:
        return hex_to_qcolor(self.get_color(name, context="qcolor"))

    def vtk_rgb(self, name: str) -> Tuple[float, float, float]:
        return hex_to_vtk_rgb(self.get_color(name, context="vtk_rgb"))

    # ------------- CSS template processing -------------

    def _strip_css_comments(self, text: str) -> str:
        """
        Remove CSS block comments (/* ... */) so placeholders inside comments
        like {{variable_name}} in documentation headers do not trigger fallback logs.
        """
        try:
            return re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        except Exception:
            return text

    def process_css_template(self, css_text: str) -> str:
        """
        Replace {{VARIABLE_NAME}} patterns with actual color values.
        Uses a cache keyed by text hash and theme version.
        Strips /* ... */ comments before processing to avoid false fallbacks from examples in comments.
        """
        key = f"{hash(css_text)}"
        cached = self._css_text_cache.get(key)
        if cached and cached[0] == self._version:
            return cached[1]

        def replace(match: re.Match[str]) -> str:
            var = match.group(1)
            value = self.get_color(var, context="css_template")
            if not value:
                value = FALLBACK_COLOR
            return value

        try:
            text = self._strip_css_comments(css_text)
            processed = re.sub(self.VARIABLE_PATTERN, replace, text)
            self._css_text_cache[key] = (self._version, processed)
            return processed
        except Exception as exc:
            self._log_json(logging.ERROR, "css_template_processing_error", error=str(exc))
            return css_text  # fail-safe: return unprocessed

    def process_css_file(self, path: Union[str, Path]) -> str:
        """
        Read a CSS file, replace {{VARIABLE_NAME}} with actual values.
        Caches processed content based on file mtime and theme version.
        """
        p = str(path)
        try:
            mtime = Path(p).stat().st_mtime
        except Exception as exc:
            self._log_json(logging.ERROR, "css_file_stat_error", path=p, error=str(exc))
            # Best effort: try to process once without cache
            try:
                text = Path(p).read_text(encoding="utf-8")
                return self.process_css_template(text)
            except Exception as exc2:
                self._log_json(logging.ERROR, "css_file_read_error", path=p, error=str(exc2))
                return ""

        cached = self._css_file_cache.get(p)
        if cached and cached[0] == mtime and cached[1] == self._version:
            return cached[2]

        try:
            text = Path(p).read_text(encoding="utf-8")
            processed = self.process_css_template(text)
            self._css_file_cache[p] = (mtime, self._version, processed)
            return processed
        except Exception as exc:
            self._log_json(logging.ERROR, "css_file_processing_error", path=p, error=str(exc))
            return ""

    # ------------- Widget registry -------------

    def register_widget(self, widget: Any, *, css_path: Optional[Union[str, Path]] = None, css_text: Optional[str] = None) -> None:
        """
        Register a widget for style application. Provide either css_path or raw css_text
        (which can contain {{VARIABLE_NAME}} placeholders). If neither provided,
        the widget will be tracked but no stylesheet will be applied.
        """
        try:
            self._widgets.add(widget)
            key = id(widget)
            self._widget_sources[key] = (str(css_path) if css_path is not None else None, css_text)
        except Exception as exc:
            self._log_json(logging.ERROR, "widget_register_error", error=str(exc))

    def apply_stylesheet(self, widget: Any) -> None:
        """
        Apply the registered stylesheet to a single widget. Logs at DEBUG level.
        """
        key = id(widget)
        src = self._widget_sources.get(key)
        if not src:
            return
        css_path, css_text = src
        try:
            if css_text:
                ss = self.process_css_template(css_text)
            elif css_path:
                ss = self.process_css_file(css_path)
            else:
                ss = ""
            if hasattr(widget, "setStyleSheet"):
                widget.setStyleSheet(ss)
                self._log_json(logging.DEBUG, "stylesheet_applied", widget=str(widget), css_path=css_path or "", css_text_len=len(css_text or ""))
        except Exception as exc:
            self._log_json(logging.ERROR, "stylesheet_apply_error", error=str(exc))

    def apply_to_registered(self) -> None:
        """
        Re-apply styles to all registered widgets. Safe to call multiple times.
        """
        dead: list[int] = []
        for w in list(self._widgets):
            if w is None:
                continue
            try:
                self.apply_stylesheet(w)
            except ReferenceError:
                dead.append(id(w))
                continue
            except Exception:
                # Fail-safe: never break UI due to theme update
                continue
        for k in dead:
            self._widget_sources.pop(k, None)

    # ------------- Save/Load/Export/Import -------------

    def _settings_path(self) -> Path:
        """Return the path to the theme.json in AppData."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "theme.json"

    def save_to_settings(self) -> None:
        """Persist current theme to theme.json in AppData."""
        try:
            path = self._settings_path()
            path.write_text(json.dumps(self.colors, indent=2), encoding="utf-8")
            self._log_json(logging.INFO, "theme_saved", path=str(path))
        except Exception as exc:
            self._log_json(logging.ERROR, "theme_save_error", error=str(exc))

    def load_from_settings(self) -> None:
        """
        Load theme from theme.json in AppData.
        If file doesn't exist or is invalid, keep defaults.
        """
        try:
            path = self._settings_path()
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.set_colors({k: v for k, v in data.items() if k in self._colors})
                self._log_json(logging.INFO, "theme_loaded", path=str(path))
        except Exception as exc:
            # Fail-safe: ignore malformed files
            self._log_json(logging.ERROR, "theme_load_error", error=str(exc))

    def export_theme(self, file_path: Union[str, Path]) -> None:
        """Export current theme to a JSON file at file_path."""
        try:
            Path(file_path).write_text(json.dumps(self.colors, indent=2), encoding="utf-8")
            self._log_json(logging.INFO, "theme_exported", path=str(file_path))
        except Exception as exc:
            self._log_json(logging.ERROR, "theme_export_error", path=str(file_path), error=str(exc))

    def import_theme(self, file_path: Union[str, Path]) -> None:
        """Import a theme from a JSON file at file_path."""
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.set_colors({k: v for k, v in data.items() if k in self._colors})
                self._log_json(logging.INFO, "theme_imported", path=str(file_path))
        except Exception as exc:
            self._log_json(logging.ERROR, "theme_import_error", path=str(file_path), error=str(exc))


# ============================================================
# Backward-compatible API and convenience wrappers
# ============================================================

class _ColorsProxy:
    """
    Proxy object to allow f-string usage like f\"color: {COLORS.text};\"
    Values are resolved from ThemeManager at access time.
    """

    def __getattr__(self, name: str) -> str:
        return ThemeManager.instance().get_color(name, context="COLORS_proxy")


# Singleton-like proxy for read access inside f-strings, etc.
COLORS = _ColorsProxy()


def color(name: str) -> str:
    """
    Get a hex color string by name (e.g., 'primary', 'text').
    Returns a normalized '#rrggbb' string for hex variables, or raw string for non-hex values.
    """
    return ThemeManager.instance().get_color(name, context="function_color")


def qcolor(name: str) -> QColor:
    """Get a QColor for a named color (e.g., qcolor('primary'))."""
    return ThemeManager.instance().qcolor(name)


def vtk_rgb(name: str) -> Tuple[float, float, float]:
    """Get a normalized RGB tuple (0..1) for VTK for the given named color."""
    return ThemeManager.instance().vtk_rgb(name)


# ---------- Persistence and runtime updates (backward-compatible) ----------

def theme_to_dict() -> Dict[str, str]:
    """Dump current theme colors as a dict of strings."""
    return ThemeManager.instance().colors


def set_theme(overrides: Dict[str, Any]) -> None:
    """
    Replace theme colors with provided overrides.
    Expects hex strings (with or without '#') or valid CSS color strings.
    Unknown keys are ignored to preserve stability.
    """
    ThemeManager.instance().set_colors({k: str(v) for k, v in overrides.items()})

def list_theme_presets() -> list[str]:
    """List names of available theme presets."""
    return ThemeManager.instance().available_presets()

def apply_theme_preset(preset_name: str, custom_mode: Optional[str] = None, base_primary: Optional[str] = None) -> None:
    """Apply a theme preset via ThemeManager."""
    ThemeManager.instance().apply_preset(preset_name, custom_mode=custom_mode, base_primary=base_primary)


def load_theme_from_settings() -> None:
    """
    Load theme from theme.json in AppData and apply to manager.
    If file doesn't exist or is invalid, keep defaults.
    """
    ThemeManager.instance().load_from_settings()


def save_theme_to_settings() -> None:
    """Persist current theme to theme.json in AppData."""
    ThemeManager.instance().save_to_settings()


# ============================================================
# Prebuilt QSS snippets (unchanged for backward compatibility)
# ============================================================

def qss_button_base() -> str:
    return (
        f"QPushButton {{"
        f"  background-color: {COLORS.surface};"
        f"  color: {COLORS.text};"
        f"  border: 1px solid {COLORS.border};"
        f"  padding: 6px 12px;"
        f"  border-radius: 2px;"
        f"}}"
        f"QPushButton:hover {{"
        f"  background-color: {COLORS.hover};"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
        f"QPushButton:pressed {{"
        f"  background-color: {COLORS.pressed};"
        f"}}"
        f"QPushButton:checked {{"
        f"  background-color: {COLORS.primary};"
        f"  color: {COLORS.primary_text};"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
        f"QPushButton:default {{"
        f"  border: 1px solid {COLORS.primary};"
        f"  background-color: {COLORS.primary};"
        f"  color: {COLORS.primary_text};"
        f"  font-weight: bold;"
        f"}}"
        f"QPushButton:default:hover {{"
        f"  background-color: {COLORS.primary_hover};"
        f"}}"
    )


def qss_progress_bar() -> str:
    return (
        f"QProgressBar {{"
        f"  border: 1px solid {COLORS.border};"
        f"  border-radius: 2px;"
        f"  text-align: center;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QProgressBar::chunk {{"
        f"  background-color: {COLORS.progress_chunk};"
        f"  border-radius: 1px;"
        f"}}"
    )


def qss_inputs_base() -> str:
    return (
        f"QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {{"
        f"  border: 1px solid {COLORS.border};"
        f"  border-radius: 2px;"
        f"  padding: 6px;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"  selection-background-color: {COLORS.selection_bg};"
        f"  selection-color: {COLORS.selection_text};"
        f"}}"
        f"QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{"
        f"  border: 2px solid {COLORS.primary};"
        f"  outline: none;"
        f"}}"
        f"QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDateEdit:hover {{"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
    )


def qss_tabs_lists_labels() -> str:
    return (
        f"QTabWidget::pane {{"
        f"  border: 1px solid {COLORS.border};"
        f"  background-color: {COLORS.window_bg};"
        f"}}"
        f"QTabBar::tab {{"
        f"  background: {COLORS.surface};"
        f"  padding: 8px;"
        f"  margin-right: 2px;"
        f"  border: 1px solid {COLORS.border};"
        f"  border-bottom: none;"
        f"  color: {COLORS.text};"
        f"}}"
        f"QTabBar::tab:selected {{"
        f"  background: {COLORS.window_bg};"
        f"  border-bottom: 2px solid {COLORS.tab_selected_border};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QTabBar::tab:hover {{"
        f"  background: {COLORS.hover};"
        f"}}"
        f"QListWidget {{"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"  border: 1px solid {COLORS.border};"
        f"  selection-background-color: {COLORS.selection_bg};"
        f"  selection-color: {COLORS.selection_text};"
        f"}}"
        f"QListWidget::item {{"
        f"  padding: 5px;"
        f"  border-bottom: 1px solid {COLORS.border_light};"
        f"}}"
        f"QListWidget::item:selected {{"
        f"  background-color: {COLORS.selection_bg};"
        f"  color: {COLORS.selection_text};"
        f"}}"
        f"QLabel {{"
        f"  color: {COLORS.text};"
        f"  background-color: transparent;"
        f"}}"
    )


def qss_groupbox_base() -> str:
    return (
        f"QGroupBox {{"
        f"  font-weight: bold;"
        f"  border: 2px solid {COLORS.border};"
        f"  border-radius: 4px;"
        f"  margin-top: 1ex;"
        f"  padding-top: 10px;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QGroupBox::title {{"
        f"  subcontrol-origin: margin;"
        f"  left: 10px;"
        f"  padding: 0 5px 0 5px;"
        f"  color: {COLORS.text};"
        f"}}"
    )
