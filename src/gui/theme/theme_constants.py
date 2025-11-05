"""
Theme constants and color conversion utilities.

Provides spacing constants, fallback colors, and helper functions for
converting between different color formats (hex, RGB, QColor, VTK RGB).
"""

# Import color utilities from shared utils module
# These are re-exported for backward compatibility with existing code
from src.utils.color_utils import (
    FALLBACK_COLOR,  # noqa: F401 - Re-exported for backward compatibility
    normalize_hex as _normalize_hex,  # noqa: F401 - Re-exported for backward compatibility
    hex_to_rgb,  # noqa: F401 - Re-exported for backward compatibility
    hex_to_qcolor,  # noqa: F401 - Re-exported for backward compatibility
    vtk_rgb as hex_to_vtk_rgb,  # noqa: F401 - Re-exported for backward compatibility
)

# ============================================================
# Spacing scale constants (px)
# ============================================================

SPACING_4 = 4
SPACING_8 = 8
SPACING_12 = 12
SPACING_16 = 16
SPACING_24 = 24
