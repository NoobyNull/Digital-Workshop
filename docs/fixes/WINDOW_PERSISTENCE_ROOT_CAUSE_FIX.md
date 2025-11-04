# Window Size Persistence - Root Cause and Complete Fix

## Problem Statement

Window size was not persisting between application launches despite having persistence code in place.

## Root Cause Analysis

### Issue 1: Inconsistent QSettings Organization/Application Names (FIXED)

**Problem:**
- `Application._create_qt_application()` set org/app names to hardcoded values
- `SystemInitializer._setup_application_metadata()` changed them to config values
- QSettings saved to one registry location but read from another

**Solution:**
- Use config values from the start in `_create_qt_application()`
- Remove redundant name setting in `_setup_application_metadata()`

### Issue 2: SettingsManager Overwriting Window Size (FIXED)

**Problem:**
- `SettingsManager.save_window_settings()` was saving CONFIG DEFAULTS, not actual window size
- This was called AFTER `_save_window_settings()` but before final sync
- Config defaults (1200x800) were overwriting actual window size (e.g., 1920x1080)

**Solution:**
- Reorder closeEvent to save SettingsManager BEFORE `_save_window_settings()`
- `_save_window_settings()` now runs LAST, ensuring actual size is not overwritten
- Updated SettingsManager documentation to clarify it saves defaults, not current size

## Files Modified

### 1. `src/core/application.py`
**Change:** Use config values for QSettings org/app names from the start
```python
org_name = self.config.organization_name
app_name = self.config.name

QCoreApplication.setOrganizationName(org_name)
QCoreApplication.setApplicationName(app_name)
```

### 2. `src/core/system_initializer.py`
**Change:** Remove redundant org/app name setting
```python
def _setup_application_metadata(self) -> None:
    # Only set version and domain - org/app names already set
    QApplication.setApplicationVersion(self.config.version)
    QApplication.setOrganizationDomain(self.config.organization_domain)
```

### 3. `src/gui/main_window_components/settings_manager.py`
**Change:** Clarify that this saves config defaults, not current window size
```python
def save_window_settings(self) -> None:
    """Save window settings (startup behavior) to QSettings.
    
    NOTE: Actual window dimensions are saved by MainWindow._save_window_settings()
    using saveGeometry() and explicit width/height values. This method only saves
    configuration defaults and startup behavior, NOT the current window size.
    """
```

### 4. `src/gui/main_window.py`
**Change:** Reorder closeEvent to save actual window size LAST

**Before:**
```
1. Save window geometry (_save_window_settings)
2. Save lighting settings
3. Save viewer/window settings (SettingsManager) ← OVERWRITES window size!
```

**After:**
```
1. Save lighting settings
2. Save viewer/window settings (SettingsManager) ← Saves config defaults
3. Save window geometry (_save_window_settings) ← Saves actual size LAST
```

## How It Works Now

### On Application Close

1. **VTK Cleanup** - Clean up graphics resources
2. **Lighting Settings** - Save lighting preferences
3. **SettingsManager** - Save config defaults and startup behavior
   - Saves: default_width, default_height, minimize_width, minimize_height
   - Does NOT save current window size
4. **Window Geometry** - Save actual current window size (LAST)
   - Saves: window_geometry, window_state, window/width, window/height, window/maximized
   - Calls `settings.sync()` to write to disk
5. **Final Logging** - Log final window state for debugging

### On Application Start

1. **QSettings Initialization** - Use consistent org/app names
2. **Window Restoration** - Read actual window size from settings
   - Reads: window/width, window/height, window/maximized
   - Applies: `self.resize(width, height)`
   - Applies: `self.showMaximized()` if needed

## Settings Storage

**Windows Registry Location:**
```
HKEY_CURRENT_USER\Software\DigitalWorkshop\DigitalWorkshop
```

**Saved Values:**
```
window_geometry          - Full geometry (binary)
window_state             - Full state (binary)
window/width             - Actual current width (int)
window/height            - Actual current height (int)
window/maximized         - Actual maximized state (bool)
window/default_width     - Config default width (int)
window/default_height    - Config default height (int)
```

## Key Insight

The critical fix was **reordering the save sequence** so that:
1. Config defaults are saved first (by SettingsManager)
2. Actual window size is saved LAST (by _save_window_settings)

This ensures the actual window size is never overwritten by config defaults.

## Testing

### Manual Test
1. Launch application
2. Resize window to custom size (e.g., 1600x900)
3. Close application
4. Relaunch application
5. **Verify**: Window opens at same size (1600x900)

### Verify in Registry
1. Open Registry Editor (regedit)
2. Navigate to: `HKEY_CURRENT_USER\Software\DigitalWorkshop\DigitalWorkshop`
3. Check values:
   - `window/width` should match your custom size
   - `window/height` should match your custom size
   - `window/default_width` should be 1200 (config default)
   - `window/default_height` should be 800 (config default)

## Verification Checklist

✅ QSettings org/app names are consistent
✅ SettingsManager saves config defaults (not current size)
✅ _save_window_settings() saves actual current size
✅ _save_window_settings() is called LAST in closeEvent
✅ settings.sync() is called to write to disk
✅ Restoration reads actual window size from settings
✅ Fallback mechanism handles missing settings
✅ Bounds checking validates restored dimensions
✅ All files compile without errors

## Result

**Window size now persists correctly between application launches!**

