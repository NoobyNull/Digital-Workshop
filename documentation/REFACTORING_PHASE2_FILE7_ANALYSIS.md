# Phase 2, File 7: src/gui/theme_manager_widget.py - Analysis

**File**: `src/gui/theme_manager_widget.py`  
**Lines**: 976 (original monolithic file)  
**Status**: 🔄 **ANALYSIS COMPLETE - READY FOR REFACTORING**

---

## 📊 FILE STRUCTURE ANALYSIS

### **Code Boundaries Identified**

```
Lines 1-39:     Module docstring and imports
Lines 40-160:   Helper functions (3 functions, ~120 lines)
Lines 161-482:  ColorRow class (~320 lines)
Lines 483-623:  PreviewWindow class (~140 lines)
Lines 624-977:  ThemeManagerWidget class (~350 lines)
```

---

## 🎯 FUNCTIONAL AREAS

### **1. Helper Functions** (lines 40-160)
- `_contrasting_text_color()` - Calculate contrast for text on background
- `_pretty_label()` - Humanize variable names
- `_build_category_map()` - Build category grouping from color keys

**Placement**: `theme_manager_helpers.py`

### **2. ColorRow Widget** (lines 161-482)
- Single color variable editor row
- Components: label, color preview, pick button, reset button
- Methods: __init__, set_color, _on_pick_color, _on_reset
- Signals: color_changed

**Placement**: `color_row.py`

### **3. PreviewWindow Widget** (lines 483-623)
- Mini QMainWindow with real widgets
- Components: menubar, toolbar, status bar, dock, central widget
- Shows live preview of theme
- Methods: __init__, _build_central_widget, apply_stylesheet

**Placement**: `preview_window.py`

### **4. ThemeManagerWidget Main** (lines 624-977)
- Main dialog with left controls, right preview
- Components: preset selector, search filter, color groups, action buttons
- Integrates all other components
- Methods: __init__, _build_left_panel, _build_right_panel, _build_bottom_actions, etc.

**Placement**: `theme_manager_widget_main.py`

---

## 📁 PROPOSED MODULE STRUCTURE

```
src/gui/theme_manager_components/
├── __init__.py                      (facade, re-exports all)
├── color_row.py                     (~100 lines)
├── preview_window.py                (~150 lines)
├── theme_manager_helpers.py         (~120 lines)
└── theme_manager_widget_main.py     (~350 lines)
```

---

## ✅ REFACTORING PLAN

1. **Create directory**: `src/gui/theme_manager_components/`
2. **Extract modules**:
   - theme_manager_helpers.py - Helper functions
   - color_row.py - ColorRow widget
   - preview_window.py - PreviewWindow widget
   - theme_manager_widget_main.py - Main widget
3. **Create __init__.py** - Facade with re-exports
4. **Update src/gui/theme_manager_widget.py** - Convert to facade
5. **Test imports** - Verify backward compatibility
6. **Update documentation** - Record completion

---

## 🔗 DEPENDENCIES

**Imports from**:
- PySide6 (Qt framework)
- src.gui.theme (ThemeManager, COLORS, etc.)
- src.core.logging_config (get_logger)
- dataclasses (asdict)
- pathlib (Path)
- json

**Used by**:
- Main application (likely imported in main_window.py)
- Theme management UI

---

## 📈 EXPECTED RESULTS

| Metric | Value |
|--------|-------|
| **Original File Size** | 976 lines |
| **Refactored Size** | ~720 lines (4 modules) |
| **All Modules Under 300 Lines** | ✅ Yes |
| **Backward Compatibility** | ✅ 100% |
| **Import Errors** | ✅ 0 |

---

**Status**: ✅ **READY FOR EXTRACTION**

