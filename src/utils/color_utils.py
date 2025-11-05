"""
Color utility functions for Digital Workshop.

Provides color conversion and normalization utilities used across the application,
particularly in the theme system. Extracted from theme_core.py and manager.py
to eliminate code duplication and follow DRY principles.

Functions:
    - normalize_hex: Normalize hex color codes to #rrggbb format
    - hex_to_rgb: Convert hex color to RGB tuple (0-255)
    - hex_to_qcolor: Convert hex color to QColor object
    - rgb_to_hex: Convert RGB tuple to hex color
    - vtk_rgb: Convert hex color to VTK-compatible RGB tuple (0.0-1.0)
"""

import re
from typing import Tuple

from PySide6.QtGui import QColor

# Fallback color for undefined/invalid colors (hot pink for visibility)
FALLBACK_COLOR = "#E31C79"


def normalize_hex(h: str) -> str:
    """
    Return a normalized #rrggbb hex string for inputs that look like hex codes.
    
    If the input does not represent a hex color (e.g., 'rgba(255,255,255,0.8)' 
    or CSS keywords like 'transparent'), return it unchanged.
    
    Args:
        h: Input color string (hex code, CSS function, or keyword)
        
    Returns:
        Normalized #rrggbb hex string, or original string if not a hex color
        
    Examples:
        >>> normalize_hex("#abc")
        '#aabbcc'
        >>> normalize_hex("a1b2c3")
        '#a1b2c3'
        >>> normalize_hex("rgba(255,255,255,0.8)")
        'rgba(255,255,255,0.8)'
        >>> normalize_hex("transparent")
        'transparent'
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
    if (
        lower.startswith("#")
        and len(lower) == 7
        and all(c in "0123456789abcdef" for c in lower[1:])
    ):
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
    """
    Convert #rrggbb hex color to integer RGB tuple (0-255).
    
    Args:
        hex_code: Hex color code (e.g., "#a1b2c3" or "a1b2c3")
        
    Returns:
        Tuple of (red, green, blue) as integers 0-255
        
    Raises:
        ValueError: If hex_code is not a valid hex color
        
    Examples:
        >>> hex_to_rgb("#ffffff")
        (255, 255, 255)
        >>> hex_to_rgb("#000000")
        (0, 0, 0)
        >>> hex_to_rgb("abc")
        (170, 187, 204)
    """
    h = normalize_hex(hex_code)
    if not h.startswith("#") or len(h) != 7:
        raise ValueError(f"hex_to_rgb expects #rrggbb, got {hex_code!r}")
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def hex_to_qcolor(hex_code: str) -> QColor:
    """
    Convert #rrggbb hex color to QColor object.
    
    Args:
        hex_code: Hex color code (e.g., "#a1b2c3" or "a1b2c3")
        
    Returns:
        QColor object
        
    Examples:
        >>> color = hex_to_qcolor("#ff0000")
        >>> color.red(), color.green(), color.blue()
        (255, 0, 0)
    """
    r, g, b = hex_to_rgb(hex_code)
    return QColor(r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB tuple to #rrggbb hex color.
    
    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        
    Returns:
        Hex color string in #rrggbb format
        
    Examples:
        >>> rgb_to_hex(255, 0, 0)
        '#ff0000'
        >>> rgb_to_hex(170, 187, 204)
        '#aabbcc'
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def vtk_rgb(hex_code: str) -> Tuple[float, float, float]:
    """
    Convert hex color to VTK-compatible RGB tuple (0.0-1.0).

    VTK uses normalized RGB values in the range 0.0 to 1.0 instead of 0-255.

    Args:
        hex_code: Hex color code (e.g., "#a1b2c3" or "a1b2c3")

    Returns:
        Tuple of (red, green, blue) as floats 0.0-1.0

    Examples:
        >>> vtk_rgb("#ffffff")
        (1.0, 1.0, 1.0)
        >>> vtk_rgb("#000000")
        (0.0, 0.0, 0.0)
        >>> vtk_rgb("#808080")
        (0.5019607843137255, 0.5019607843137255, 0.5019607843137255)
    """
    r, g, b = hex_to_rgb(hex_code)
    return r / 255.0, g / 255.0, b / 255.0
