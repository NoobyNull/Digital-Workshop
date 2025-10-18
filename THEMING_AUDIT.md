# Comprehensive Theming Audit Report

## Overview
Complete audit of all theming code in the application. Goal: Ensure 100% of theming is handled by qt-material only.

## Files Requiring Updates

### CRITICAL - Core Application Files (Must Update First)
1. **src/gui/main_window.py**
   - Status: Has QPalette import, applies app_stylesheet
   - Action: Remove QPalette import, keep app_stylesheet application

2. **src/gui/preferences.py**
   - Status: Has COLORS import, _apply_theme_styling() method
   - Action: Remove COLORS, simplify _apply_theme_styling() to no-op

3. **src/gui/components/toolbar_manager.py**
   - Status: Has COLORS and ThemeManager imports
   - Action: Remove both, let qt-material handle toolbar styling

4. **src/gui/components/menu_manager.py**
   - Status: Has ThemeManager usage for menubar styling
   - Action: Remove ThemeManager palette application

5. **src/gui/components/status_bar_manager.py**
   - Status: Has ThemeManager usage for statusbar styling
   - Action: Remove ThemeManager palette application

### HIGH - Component Files (Update Second)
6. **src/gui/metadata_components/metadata_editor_main.py**
   - Status: Has COLORS, ThemeManager, qcolor imports
   - Action: Remove all, use apply_theme() only

7. **src/gui/model_library.py**
   - Status: Has COLORS, ThemeManager, qcolor imports
   - Action: Replace qcolor() with get_theme_color() for VTK only

8. **src/gui/model_library_components/library_ui_manager.py**
   - Status: Has COLORS, ThemeManager imports
   - Action: Remove all custom styling

9. **src/gui/viewer_components/viewer_3d_widget_main.py**
   - Status: Has COLORS, qcolor imports
   - Action: Replace qcolor() with get_theme_color() for VTK only

10. **src/gui/window/central_widget_manager.py**
    - Status: Has COLORS import
    - Action: Remove COLORS import

11. **src/gui/window/dock_snapping.py**
    - Status: Has COLORS, hex_to_rgb imports
    - Action: Remove COLORS, keep hex_to_rgb if needed

### MEDIUM - Theme Manager Components (Update Third)
12. **src/gui/theme_manager_components/color_row.py**
    - Status: Has ThemeManager, COLORS imports
    - Action: Remove custom styling

13. **src/gui/theme_manager_components/theme_manager_helpers.py**
    - Status: Has ThemeManager, COLORS imports
    - Action: Remove or refactor

14. **src/gui/theme/ui/theme_dialog.py**
    - Status: Has color picker button styling (KEEP THIS)
    - Action: Keep only color picker button background styling

## Summary Statistics
- **Total files to update:** 14
- **Critical files:** 5
- **High priority files:** 6
- **Medium priority files:** 3

## Verification Checklist
- [ ] All COLORS imports removed (except theme files)
- [ ] All ThemeManager imports removed (except theme files)
- [ ] All qcolor() calls replaced with get_theme_color() (VTK only)
- [ ] All _apply_theme_styles() methods removed
- [ ] All setStyleSheet() calls removed (except color picker button)
- [ ] All QPalette.setColor() calls removed
- [ ] Application starts without errors
- [ ] Theme switching works (light/dark/auto)
- [ ] All widgets properly themed
- [ ] No hardcoded colors visible

## Next Steps
1. Update CRITICAL files first
2. Update HIGH priority files
3. Update MEDIUM priority files
4. Run comprehensive tests
5. Final cleanup and commit

