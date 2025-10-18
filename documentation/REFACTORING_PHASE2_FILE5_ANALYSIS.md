# Phase 2, File 5: theme/manager.py - Analysis

**File**: `src/gui/theme/manager.py`  
**Lines**: 1129  
**Status**: 🔄 ANALYSIS COMPLETE

---

## File Structure

### Constants & Helpers (Lines 35-360)
- **SPACING_* constants** (4, 8, 12, 16, 24)
- **FALLBACK_COLOR** constant
- **Helper functions**:
  - `_normalize_hex()` - Normalize hex colors
  - `hex_to_rgb()` - Convert hex to RGB
  - `hex_to_qcolor()` - Convert hex to QColor
  - `hex_to_vtk_rgb()` - Convert hex to VTK RGB
  - `_srgb_to_linear()` - Color space conversion
  - `_relative_luminance_from_hex()` - Calculate luminance
  - `_choose_text_for_bg()` - Choose text color for background
  - `_mix_hex()` - Mix two colors
  - `_lighten()` - Lighten color
  - `_darken()` - Darken color

### ThemeDefaults Class (Lines 117-327)
- Dataclass with default color definitions
- ~200 lines of color definitions
- Organized by category (backgrounds, text, accents, etc.)

### Palette Derivation (Lines 364-610)
- `derive_mode_palette()` - Generate color palette from seed
- Complex color derivation logic
- ~250 lines

### ThemeManager Class (Lines 611-924)
- Main theme management class
- ~310 lines
- Methods:
  - `__init__()` - Initialize
  - `_load_from_json()` - Load from JSON
  - `_save_to_json()` - Save to JSON
  - `_apply_to_widgets()` - Apply theme to widgets
  - `_process_css_template()` - Process CSS templates
  - `get_color()` - Get color by name
  - `set_color()` - Set color by name
  - `export_theme()` - Export theme
  - `import_theme()` - Import theme
  - And more...

### _ColorsProxy Class (Lines 925-938)
- Proxy for accessing colors
- ~15 lines

### Module-Level Functions (Lines 939-1129)
- `color()` - Get color hex
- `qcolor()` - Get QColor
- `vtk_rgb()` - Get VTK RGB
- `theme_to_dict()` - Export theme
- `set_theme()` - Set theme
- `list_theme_presets()` - List presets
- `apply_theme_preset()` - Apply preset
- `load_theme_from_settings()` - Load from settings
- `save_theme_to_settings()` - Save to settings
- `qss_button_base()` - Generate button CSS
- `qss_progress_bar()` - Generate progress bar CSS
- `qss_inputs_base()` - Generate input CSS
- `qss_tabs_lists_labels()` - Generate tabs/lists CSS
- `qss_groupbox_base()` - Generate groupbox CSS

---

## Proposed Modularization

### Module 1: theme_constants.py (~80 lines)
- SPACING_* constants
- FALLBACK_COLOR constant
- Color conversion helpers
- Utility functions

### Module 2: theme_defaults.py (~220 lines)
- ThemeDefaults dataclass
- Default color definitions
- Color organization

### Module 3: theme_palette.py (~250 lines)
- `derive_mode_palette()` function
- Color derivation logic
- Palette generation

### Module 4: theme_manager.py (~310 lines)
- ThemeManager class
- Core theme management
- JSON persistence
- Widget application

### Module 5: theme_api.py (~150 lines)
- Module-level API functions
- _ColorsProxy class
- Public interface functions
- CSS generation functions

### Module 6: __init__.py (~30 lines)
- Module exports
- Backward compatibility

---

## Extraction Strategy

1. **Extract constants** → theme_constants.py
2. **Extract ThemeDefaults** → theme_defaults.py
3. **Extract palette derivation** → theme_palette.py
4. **Keep ThemeManager** → theme_manager.py (refactored)
5. **Extract API functions** → theme_api.py
6. **Create __init__.py** → Module exports

---

## Backward Compatibility

- All public functions remain accessible
- Import paths preserved
- Facade pattern for unified interface
- No breaking changes

---

## Next Steps

1. Create theme_constants.py
2. Create theme_defaults.py
3. Create theme_palette.py
4. Refactor theme_manager.py
5. Create theme_api.py
6. Update __init__.py
7. Run tests and verify

---

**Status**: ✅ **ANALYSIS COMPLETE - READY FOR EXTRACTION**

