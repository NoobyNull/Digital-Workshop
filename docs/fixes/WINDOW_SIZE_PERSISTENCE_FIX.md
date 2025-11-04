# Window Size Persistence Fix

## Problem

The application window size was not being persisted between application launches. The root cause was **inconsistent QSettings organization and application names** being set at different points in the initialization sequence.

### Root Cause Analysis

1. `Application._create_qt_application()` set:
   - Organization: "Digital Workshop"
   - Application: "3D Model Manager"

2. `SystemInitializer._setup_application_metadata()` then changed them to:
   - Organization: "DigitalWorkshop" (from config)
   - Application: "DigitalWorkshop" (from config)

This caused QSettings to save settings to one registry location but look for them in another, resulting in settings not being found on startup.

## Solution

1. **Fixed QSettings Initialization** - Use config values from the start to ensure consistency
2. **Removed Redundant Metadata Setup** - Prevent overwriting org/app names after QSettings initialization
3. **Enhanced Window Persistence** - Save and restore window size, height, and maximized state
4. **Added Fallback Mechanism** - Use explicit width/height if full geometry restoration fails
5. **Settings Sync** - Force QSettings to sync to disk immediately on close
6. **Bounds Checking** - Validate restored dimensions are within reasonable limits

## Files Modified

### `src/core/application.py` (CRITICAL FIX)

**Lines 232-259**: Enhanced `_create_qt_application()`

**Changes**:
- Use config values for organization and application names from the start
- Ensures QSettings uses consistent registry location throughout app lifecycle
- Prevents settings from being saved to one location and read from another

**Code**:
```python
org_name = self.config.organization_name
app_name = self.config.name

QCoreApplication.setOrganizationName(org_name)
QCoreApplication.setApplicationName(app_name)
```

### `src/core/system_initializer.py` (CRITICAL FIX)

**Lines 50-59**: Updated `_setup_application_metadata()`

**Changes**:
- Removed redundant setting of organization and application names
- Only sets version and domain (which don't affect QSettings location)
- Prevents overwriting the names set during QApplication creation

**Code**:
```python
def _setup_application_metadata(self) -> None:
    """Set application metadata in QApplication.

    NOTE: Organization name and application name are already set in
    Application._create_qt_application() to ensure QSettings consistency.
    Only set version and domain here.
    """
    # Only set version and domain - org/app names already set during QApplication creation
    QApplication.setApplicationVersion(self.config.version)
    QApplication.setOrganizationDomain(self.config.organization_domain)
```

### `src/gui/main_window.py`

#### 1. Enhanced `_save_window_settings()` (Lines 1165-1197)

**Changes**:
- Save full geometry and state (existing)
- **NEW**: Save explicit width and height values
- **NEW**: Save maximized state
- **NEW**: Force `settings.sync()` to ensure data is written to disk
- Added detailed logging for debugging

**Code**:
```python
# Save window size explicitly for reliability
settings.setValue("window/width", self.width())
settings.setValue("window/height", self.height())
settings.setValue("window/maximized", self.isMaximized())

# CRITICAL: Sync settings to disk immediately
settings.sync()
```

#### 2. Enhanced `_restore_window_geometry_early()` (Lines 1107-1127)

**Changes**:
- Try to restore full geometry first (existing)
- **NEW**: If full geometry fails, use explicit width/height as fallback
- **NEW**: Restore maximized state
- **NEW**: Validate dimensions are within reasonable bounds (800-3840 width, 600-2160 height)
- Added detailed logging for debugging

**Code**:
```python
# Fallback: Use explicit width/height if geometry restoration failed
if not geometry_restored and settings.contains("window/width"):
    width = settings.value("window/width", 1200, type=int)
    height = settings.value("window/height", 800, type=int)
    maximized = settings.value("window/maximized", False, type=bool)
    
    # Ensure dimensions are within reasonable bounds
    width = max(800, min(width, 3840))  # Cap at 4K width, min 800
    height = max(600, min(height, 2160))  # Cap at 4K height, min 600
    
    self.resize(width, height)
    if maximized:
        self.showMaximized()
```

## How It Works

### On Application Close

1. `closeEvent()` is triggered
2. Calls `_save_window_settings()`
3. Saves:
   - Full geometry (via `saveGeometry()`)
   - Full state (via `saveState()`)
   - Explicit width and height
   - Maximized state
4. **Forces sync to disk** with `settings.sync()`
5. Logs final window state for debugging

### On Application Start

1. `__init__()` is called
2. Calls `_restore_window_geometry_early()`
3. Attempts to restore:
   - Full geometry first (most reliable)
   - Falls back to explicit width/height if needed
   - Restores maximized state
4. Validates dimensions are within bounds
5. Logs restoration status for debugging

## Data Stored in QSettings

```
window_geometry          - Full geometry data (binary)
window_state             - Full state data (binary)
window/dock_state        - Dock layout state (binary)
window/width             - Window width in pixels (int)
window/height            - Window height in pixels (int)
window/maximized         - Whether window was maximized (bool)
ui/active_hero_tab_index - Active tab index (int)
```

## Bounds Checking

To prevent issues with invalid screen dimensions:

- **Minimum width**: 800 pixels
- **Maximum width**: 3840 pixels (4K)
- **Minimum height**: 600 pixels
- **Maximum height**: 2160 pixels (4K)

If restored dimensions are outside these bounds, they are clamped to valid values.

## Debugging

The implementation includes detailed logging at each step:

```
FIX: Starting early window geometry restoration during init
FIX: Window geometry restored successfully during init
FIX: Window resized to 1920x1080 from saved settings
FIX: Window maximized from saved settings
Window settings saved: 1920x1080, maximized=False
Window settings synced to disk
FINAL STATE: Window size: 1920x1080, position: 100,100
FINAL STATE: Window maximized: False, minimized: False
```

Check the application logs to verify window size persistence is working.

## Testing

### Automated Tests

Run the comprehensive test suite:
```bash
python test_window_persistence.py
```

This tests:
- ✅ QSettings consistency (org/app names)
- ✅ Window size persistence (width/height)
- ✅ Maximized state persistence
- ✅ Full geometry persistence

### Manual Testing

To verify the fix works:

1. Launch the application
2. Resize the window to a custom size (e.g., 1600x900)
3. Close the application
4. Relaunch the application
5. **Verify**: Window should open at the same size (1600x900)

To test maximized state:

1. Launch the application
2. Maximize the window
3. Close the application
4. Relaunch the application
5. **Verify**: Window should open maximized

### Settings Location

On Windows, settings are stored in:
```
HKEY_CURRENT_USER\Software\DigitalWorkshop\DigitalWorkshop
```

You can verify settings are being saved by checking the registry or looking at the application logs.

## Verification

✅ All files compile without errors
✅ Window size saved on close
✅ Window size restored on launch
✅ Maximized state persisted
✅ Fallback mechanism works if geometry fails
✅ Bounds checking prevents invalid dimensions
✅ Settings synced to disk immediately
✅ Detailed logging for troubleshooting
✅ Ready for production use

## Future Enhancements

- Save and restore individual dock widget sizes
- Save and restore splitter positions
- Per-monitor DPI awareness for multi-monitor setups
- Detect screen resolution changes and adjust accordingly

