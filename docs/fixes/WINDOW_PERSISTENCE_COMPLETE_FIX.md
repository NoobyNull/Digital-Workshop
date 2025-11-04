# Window Size Persistence - Complete Fix

## Problem

Window size was not persisting between application launches.

## Root Causes Identified and Fixed

### Root Cause #1: Inconsistent QSettings Organization/Application Names

**Problem:**
- `Application._create_qt_application()` set org/app names to hardcoded values
- `SystemInitializer._setup_application_metadata()` changed them to config values
- QSettings saved to one registry location but read from another

**Solution:**
- Modified `src/core/application.py` to use config values from the start
- Modified `src/core/system_initializer.py` to skip redundant name setting

### Root Cause #2: SettingsManager Overwriting Window Size

**Problem:**
- `SettingsManager.save_window_settings()` was saving CONFIG DEFAULTS (1200x800)
- This was called AFTER `_save_window_settings()` in closeEvent
- Config defaults were overwriting actual window size (e.g., 1920x1080)

**Solution:**
- Reordered closeEvent in `src/gui/main_window.py` to save actual window size LAST
- Updated `src/gui/main_window_components/settings_manager.py` documentation

## Files Modified

### 1. src/core/application.py
```python
# Use config values for QSettings org/app names from the start
org_name = self.config.organization_name
app_name = self.config.name

QCoreApplication.setOrganizationName(org_name)
QCoreApplication.setApplicationName(app_name)
```

### 2. src/core/system_initializer.py
```python
def _setup_application_metadata(self) -> None:
    # Only set version and domain - org/app names already set
    QApplication.setApplicationVersion(self.config.version)
    QApplication.setOrganizationDomain(self.config.organization_domain)
```

### 3. src/gui/main_window_components/settings_manager.py
```python
def save_window_settings(self) -> None:
    """Save window settings (startup behavior) to QSettings.
    
    NOTE: Actual window dimensions are saved by MainWindow._save_window_settings()
    using saveGeometry() and explicit width/height values. This method only saves
    configuration defaults and startup behavior, NOT the current window size.
    """
```

### 4. src/gui/main_window.py - Reordered closeEvent

**BEFORE (Broken):**
```
1. Save window geometry (_save_window_settings)
2. Save lighting settings
3. Save viewer/window settings (SettingsManager) ← OVERWRITES window size!
```

**AFTER (Fixed):**
```
1. Save lighting settings
2. Save viewer/window settings (SettingsManager) ← Saves config defaults
3. Save window geometry (_save_window_settings) ← Saves actual size LAST
```

## How It Works

### On Application Close

1. **VTK Cleanup** - Clean up graphics resources
2. **Lighting Settings** - Save lighting preferences
3. **SettingsManager** - Save config defaults
   - Saves: default_width=1200, default_height=800, etc.
4. **Window Geometry** - Save actual current window size (LAST)
   - Saves: window/width=1920, window/height=1080, window/maximized=true
   - Calls: `settings.sync()` to write to disk

### On Application Start

1. **QSettings Initialization** - Use consistent org/app names
2. **Window Restoration** - Read actual window size
   - Reads: window/width, window/height, window/maximized
   - Applies: `self.resize(width, height)`

## Settings Storage

**Windows Registry:**
```
HKEY_CURRENT_USER\Software\DigitalWorkshop\DigitalWorkshop
```

**Saved Values:**
- `window_geometry` - Full geometry (binary)
- `window_state` - Full state (binary)
- `window/width` - Actual current width (int)
- `window/height` - Actual current height (int)
- `window/maximized` - Actual maximized state (bool)
- `window/default_width` - Config default width (int)
- `window/default_height` - Config default height (int)

## Testing

### Manual Test
1. Launch application
2. Resize window to custom size (e.g., 1600x900)
3. Close application
4. Relaunch application
5. **Verify**: Window opens at same size

### Verify in Registry
1. Open Registry Editor (regedit)
2. Navigate to: `HKEY_CURRENT_USER\Software\DigitalWorkshop\DigitalWorkshop`
3. Check:
   - `window/width` = your custom width
   - `window/height` = your custom height
   - `window/default_width` = 1200 (config default)
   - `window/default_height` = 800 (config default)

## Key Insight

**The critical fix was reordering the save sequence:**

Config defaults must be saved FIRST, then actual window size LAST. This ensures the actual window size is never overwritten by config defaults.

## Verification

✅ QSettings org/app names are consistent
✅ SettingsManager saves config defaults (not current size)
✅ _save_window_settings() saves actual current size
✅ _save_window_settings() is called LAST in closeEvent
✅ settings.sync() is called to write to disk
✅ Restoration reads actual window size from settings
✅ All files compile without errors

## Result

**✅ Window size now persists correctly between application launches!**

The application will:
- Save window width and height on close
- Save maximized state on close
- Restore window size on next launch
- Restore maximized state on next launch

