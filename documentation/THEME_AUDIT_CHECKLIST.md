# Theme Audit Checklist - Files with Hardcoded Colors/CSS

## Files with setStyleSheet() Calls - NEED FIXING

### 1. ✅ src/gui/components/status_bar_manager.py
- **Issue**: `setStyleSheet("opacity: 0.3;")` - opacity only, OK
- **Status**: SAFE - only opacity, no colors

### 2. ❌ src/gui/files_tab.py
- **Issue**: `setStyleSheet("color: green;")` and `setStyleSheet("color: red;")`
- **Status**: NEEDS FIX - hardcoded colors

### 3. ❌ src/gui/lighting_control_panel.py
- **Issue**: Multiple `setStyleSheet()` calls with hardcoded colors
- **Status**: NEEDS FIX

### 4. ❌ src/gui/lighting_control_panel_improved.py
- **Issue**: Multiple `setStyleSheet()` calls with hardcoded colors
- **Status**: NEEDS FIX

### 5. ❌ src/gui/main_window.py
- **Issue**: `setStyleSheet(qss_tabs_lists_labels())` - applies custom stylesheet
- **Status**: NEEDS FIX

### 6. ❌ src/gui/material_picker_widget.py
- **Issue**: Multiple `setStyleSheet()` with `COLORS.*` references
- **Status**: NEEDS FIX

### 7. ❌ src/gui/preferences.py
- **Issue**: Multiple `setStyleSheet()` calls
- **Status**: NEEDS FIX

### 8. ❌ src/gui/theme/ui/theme_dialog.py
- **Issue**: `setStyleSheet()` with hardcoded colors
- **Status**: NEEDS FIX

### 9. ❌ src/gui/theme_manager_widget.py
- **Issue**: `setStyleSheet()` calls
- **Status**: NEEDS FIX

### 10. ❌ src/gui/viewer_widget.py
- **Issue**: `setStyleSheet()` with f-string (already partially fixed)
- **Status**: VERIFY

### 11. ❌ src/gui/viewer_widget_vtk.py
- **Issue**: `setStyleSheet()` calls including hardcoded `#4CAF50`
- **Status**: NEEDS FIX

### 12. ❌ src/gui/window/central_widget_manager.py
- **Issue**: `hero_tabs_css` with `COLORS.*` - MAJOR ISSUE
- **Status**: NEEDS FIX - This is styling the main tabs!

### 13. ❌ src/gui/window/dock_manager.py
- **Issue**: `setStyleSheet(qss_tabs_lists_labels())`
- **Status**: NEEDS FIX

### 14. ❌ src/gui/window/dock_snapping.py
- **Issue**: `setStyleSheet()` calls
- **Status**: NEEDS FIX

## Summary
- **Total files with setStyleSheet**: 14
- **Safe**: 1
- **Need fixing**: 13

## Priority Fixes
1. **CRITICAL**: central_widget_manager.py - hero_tabs styling
2. **CRITICAL**: dock_manager.py - metadata_tabs styling
3. **HIGH**: material_picker_widget.py
4. **HIGH**: lighting_control_panel*.py
5. **MEDIUM**: Others

