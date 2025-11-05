"""
Consolidated theme core module for Digital Workshop.

This module serves as a facade/re-export point for the modular theme system:
- theme_constants.py - Constants and color utilities
- theme_defaults.py - Default theme values
- theme_palette.py - Palette generation and presets
- presets.py - Individual preset definitions
- persistence.py - Theme persistence (save/load)

Single Responsibility: Provide unified import point for backward compatibility.

All functionality has been extracted to separate modules following SRP.
This file now only imports and re-exports for backward compatibility.
"""

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

# Individual preset access functions
from .presets import (
    get_preset,  # noqa: F401 - Re-exported for backward compatibility
    list_presets,  # noqa: F401 - Re-exported for backward compatibility
    PRESET_LIGHT,  # noqa: F401 - Re-exported for backward compatibility
    PRESET_DARK,  # noqa: F401 - Re-exported for backward compatibility
    PRESET_HIGH_CONTRAST,  # noqa: F401 - Re-exported for backward compatibility
    PRESET_SOLARIZED_LIGHT,  # noqa: F401 - Re-exported for backward compatibility
    PRESET_SOLARIZED_DARK,  # noqa: F401 - Re-exported for backward compatibility
)

# Theme persistence
from .persistence import ThemePersistence  # noqa: F401 - Re-exported for backward compatibility

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
    "get_preset",
    "list_presets",
    "PRESET_LIGHT",
    "PRESET_DARK",
    "PRESET_HIGH_CONTRAST",
    "PRESET_SOLARIZED_LIGHT",
    "PRESET_SOLARIZED_DARK",
    # Persistence
    "ThemePersistence",
]
