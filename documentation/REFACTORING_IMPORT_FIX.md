# Import Fix - Directory Shadowing Issue

## Problem

When creating the `src/gui/main_window/` directory for modular components, it shadowed the original `src/gui/main_window.py` file. This caused import errors:

```
ImportError: cannot import name 'MainWindow' from 'src.gui.main_window'
```

Python was importing the directory instead of the file, and the directory's `__init__.py` only exported component managers, not the `MainWindow` class.

## Solution

Renamed the directory from `src/gui/main_window/` to `src/gui/main_window_components/` to avoid shadowing the original file.

### Changes Made

1. **Renamed directory**:
   - `src/gui/main_window/` → `src/gui/main_window_components/`

2. **Updated __init__.py**:
   - Updated docstring to reflect new name
   - Exports remain the same (LayoutManager, SettingsManager, DockManager)

3. **Preserved original file**:
   - `src/gui/main_window.py` remains unchanged
   - Continues to export `MainWindow` class
   - Imports work correctly now

### Directory Structure

```
src/gui/
├── main_window.py (original file - exports MainWindow)
├── main_window_components/ (new directory - exports component managers)
│   ├── __init__.py
│   ├── layout_manager.py
│   ├── settings_manager.py
│   └── dock_manager.py
└── viewer_widget_vtk.py (compatibility layer)
```

## Verification

✅ `from src.gui.main_window import MainWindow` - Works  
✅ `from src.gui.viewer_widget_vtk import Viewer3DWidget, RenderMode` - Works  
✅ Application imports successfully  

## Impact

- **No breaking changes** - All existing imports continue to work
- **Backward compatible** - Original file structure preserved
- **Clean separation** - Component managers in separate directory
- **Future-proof** - Allows for facade pattern implementation

## Next Steps

1. Create event_handler.py in main_window_components/
2. Create main_window_facade.py in main_window_components/
3. Update main_window.py to use component managers (if needed)
4. Run tests to verify functionality

