# Window Position, Dock Snapping, and Default Size - Complete Fix

## Summary

Fixed three critical issues with window management:

1. **Window position not being recalled** between application launches
2. **Dock widgets cannot snap back** into the main window when undocked
3. **Default window size** now calculated as "snapped to middle wide, full height" (50% screen width, 100% screen height)

## Issue 1: Window Position Not Being Recalled

### Problem
Window position was not being restored between application launches, even though window size appeared to be saved.

### Root Cause
Qt's `restoreGeometry()` method only works properly AFTER the window is shown on screen, not during initialization.

### Solution
1. **Moved geometry restoration to after window is shown** (lines 1244-1277 in `showEvent()`):
   - Changed from calling `restoreGeometry()` during `__init__` (too early)
   - Now defers restoration using `QTimer.singleShot(50ms)` after window is visible
   - This ensures Qt can properly restore both size AND position

2. **Added `_deferred_geometry_restoration()` method** (lines 1279-1341):
   - Called via QTimer after window is shown
   - Attempts to restore full geometry (size + position) from `window_geometry` key
   - Falls back to explicit width/height/x/y coordinates if needed
   - Includes bounds checking to prevent off-screen windows

3. **Enhanced `_save_window_settings()` method** (lines 1223-1260):
   - Now saves window position (x, y coordinates) in addition to size
   - Saves both `window_geometry` (Qt binary format) and explicit coordinates (fallback)
   - Flushes logger handlers to ensure logs are written immediately

## Issue 2: Default Window Size

### Problem
The default window size was hardcoded to 1200x800, which didn't adapt to different screen sizes.

### Solution
1. **Added `calculate_default_window_size()` static method** in `ApplicationConfig`:
   - Calculates default size as 50% of screen width and 100% of screen height
   - This creates the "snapped to middle wide, full height" layout
   - Falls back to 1200x800 if screen detection fails

2. **Updated `get_default()` method** in `ApplicationConfig`:
   - Now calls `calculate_default_window_size()` to set dynamic defaults
   - Ensures the config has screen-aware defaults

3. **Updated MainWindow initialization** (lines 107-130):
   - Calls `calculate_default_window_size()` when MainWindow is created
   - This happens AFTER QApplication is created, so screen info is available
   - Logs the calculated size for debugging

### How It Works
- **Screen Width**: 5120px (dual monitors) → Default width = 2560px (50%)
- **Screen Height**: 1440px → Default height = 1440px (100%)
- **Result**: Window opens at 2560x1440, positioned in the middle 50% of the screen

## Issue 3: Dock Widgets Cannot Snap Back

### Problem
When a dock widget is undocked (floated), it cannot be snapped back into the main window.

### Root Causes
1. The `_snap_dock_to_edge()` method was missing (called by DockDragHandler but didn't exist)
2. The `_register_dock_for_snapping()` method was missing (needed to set up snapping)
3. Dock widgets were not being registered for snapping during setup

### Solution
1. **Added `_snap_dock_to_edge()` method** (lines 2472-2505):
   - Performs the actual snapping operation when user drags dock near window edge
   - Checks if dock is allowed to dock to target area
   - Sets `setFloating(False)` to re-dock the widget
   - Calls `addDockWidget()` to place it in the target area
   - Saves the new layout

2. **Added `_register_dock_for_snapping()` method** (lines 2507-2541):
   - Initializes the snapping system on first use
   - Creates `SnapOverlayLayer` (visual feedback) and `DockDragHandler` (event handling)
   - Installs event filter on dock widget to track mouse events
   - Stores handler reference for later cleanup

3. **Registered all dock widgets for snapping** during setup:
   - Updated `_setup_model_library_dock()` (lines 373-389)
   - Updated `_setup_project_manager_dock()` (lines 440-455)
   - Updated `_setup_properties_dock()` (lines 478-494)
   - Updated `_setup_metadata_dock()` (lines 557-573)

## How to Test

### Test Window Position
1. Resize the window to a custom size (e.g., 1920x1080)
2. Move the window to a different position (e.g., 100,50)
3. Close the application
4. Reopen the application
5. Window should restore to the exact position and size

### Test Dock Snapping
1. Enable Layout Edit Mode (View → Layout Edit Mode)
2. Float a dock widget by dragging its title bar
3. Drag the floating dock near the window edges
4. You should see colored overlay zones appear
5. Release the mouse over an edge to snap the dock back
6. The dock should re-dock to that area

## Viewing the Logs

### Option 1: Console Output (Recommended for Testing)
Run the application with console logging enabled:
```bash
python src/main.py --log-console --log-human
```

This will show all logs in the console in human-readable format, including:
- Window geometry restoration messages
- Dock snapping messages
- All other application logs

### Option 2: Log Files
Logs are automatically saved to files in:
- **Windows**: `%APPDATA%\DigitalWorkshop\DigitalWorkshop\logs\`
- **Linux**: `~/.local/share/DigitalWorkshop/DigitalWorkshop/logs/`
- **macOS**: `~/Library/Application Support/DigitalWorkshop/DigitalWorkshop/logs/`

Log files are named: `Log - MMDDYY-HH-MM-SS INFO.txt`

### Expected Log Output

**Window Geometry (Startup)**:
```
FIX: Starting deferred window geometry restoration (after window is shown)
FIX: Found saved window_geometry, size: 128 bytes
FIX: Window geometry restored successfully (position and size)
```

**Window Geometry (Shutdown)**:
```
FIX: Saving window geometry and state (size, position, maximized state, dock layout)
FIX: Window settings saved: 1920x1080 at (100,50), maximized=False
FIX: Saved window_geometry: 128 bytes
FIX: Saved window_state (dock layout): 2048 bytes
FIX: Window settings synced to disk
```

**Dock Snapping**:
```
Registered dock 'Model Library' for snapping
Snapped dock 'Model Library' to left area
```

## Files Modified

- `src/core/application_config.py`:
  - Added `calculate_default_window_size()` static method
  - Updated `get_default()` to use calculated defaults

- `src/gui/main_window.py`:
  - Added `_deferred_geometry_restoration()` method
  - Updated `showEvent()` to defer geometry restoration
  - Updated `_save_window_settings()` to save position and flush logs
  - Added `_snap_dock_to_edge()` method
  - Added `_register_dock_for_snapping()` method
  - Updated all dock setup methods to register for snapping
  - Updated initialization to calculate default window size based on screen
  - Updated fallback defaults in restoration methods to use calculated values

## Verification

All files compile successfully with no syntax errors.

## Testing the Default Size

Run the application with console logging to see the calculated size:
```bash
python src/main.py --log-console --log-human
```

You'll see:
```
FIX: Calculated default window size: 2560x1440 (50% width, 100% height)
```

The window will open at 50% of your screen width and 100% of your screen height, positioned in the middle of the screen.

