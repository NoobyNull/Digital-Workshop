"""
Theme constants and color conversion utilities.

Provides spacing constants, fallback colors, and helper functions for
converting between different color formats (hex, RGB, QColor, VTK RGB).
"""

import re
from typing import Tuple

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
# Color Conversion Helpers
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

