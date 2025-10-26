# Window Persistence Test Guide

## Quick Test

Follow these steps to verify window persistence is working:

### Step 1: First Run
1. Start the application: `python run.py`
2. Wait for the window to fully load
3. Note the window size and position
4. Close the application

### Step 2: Verify Settings Were Saved
Run this command to check if settings were saved:
```bash
python -c "from PySide6.QtCore import QSettings, QCoreApplication; QCoreApplication.setOrganizationName('Digital Workshop'); QCoreApplication.setApplicationName('3D Model Manager'); s = QSettings(); print('Saved keys:', s.allKeys()); print('Has window_geometry:', s.contains('window_geometry')); print('Has window_state:', s.contains('window_state'))"
```

Expected output:
```
Saved keys: ['preferences/last_tab_index', 'root_folders', 'window_geometry', 'window_state']
Has window_geometry: True
Has window_state: True
```

### Step 3: Modify Window and Close
1. Start the application again: `python run.py`
2. Resize the window to a different size (e.g., 1600x900)
3. Move the window to a different position on screen
4. Close the application

### Step 4: Verify Restoration
1. Start the application again: `python run.py`
2. **Expected:** The window should open at the size and position you set in Step 3
3. Check the application logs for messages like:
   - "Window geometry restored successfully"
   - "Window state restored successfully"

### Step 5: Test Maximized State
1. Start the application: `python run.py`
2. Maximize the window (double-click title bar or click maximize button)
3. Close the application
4. Start the application again
5. **Expected:** The window should open in maximized state

## Automated Test

Run the QSettings persistence test:
```bash
python test_qsettings_persistence.py
```

Expected output:
```
=== First Run: Saving Data ===
QSettings location: \HKEY_CURRENT_USER\Software\Digital Workshop\3D Model Manager
Saved window_geometry: PySide6.QtCore.QRect(100, 200, 1024, 768)
Saved window_state: b'test_state_data'
All keys: ['preferences/last_tab_index', 'root_folders', 'window_geometry', 'window_state']

=== Second Run: Reading Data ===
[OK] Restored window_geometry: PySide6.QtCore.QRect(100, 200, 1024, 768)
     Type: <class 'PySide6.QtCore.QRect'>
[OK] Restored window_state: b'test_state_data'
     Type: <class 'bytes'>
All keys: ['preferences/last_tab_index', 'root_folders', 'window_geometry', 'window_state']
```

## Troubleshooting

### Window Not Restoring to Previous Size/Position

**Check 1: Verify Settings Are Being Saved**
```bash
python -c "from PySide6.QtCore import QSettings, QCoreApplication; QCoreApplication.setOrganizationName('Digital Workshop'); QCoreApplication.setApplicationName('3D Model Manager'); s = QSettings(); print('window_geometry exists:', s.contains('window_geometry')); print('window_state exists:', s.contains('window_state'))"
```

**Check 2: Clear and Retry**
```bash
python -c "from PySide6.QtCore import QSettings, QCoreApplication; QCoreApplication.setOrganizationName('Digital Workshop'); QCoreApplication.setApplicationName('3D Model Manager'); QSettings().clear(); print('Settings cleared')"
```

Then run the application again.

**Check 3: Check Application Logs**
Look for log files in:
- `src/logs/` directory
- Or check Windows Event Viewer for application errors

### Window Opens at Wrong Position

This can happen if:
1. Monitor was disconnected since last run
2. Screen resolution changed
3. Registry was corrupted

**Solution:** Clear settings and restart:
```bash
python -c "from PySide6.QtCore import QSettings, QCoreApplication; QCoreApplication.setOrganizationName('Digital Workshop'); QCoreApplication.setApplicationName('3D Model Manager'); QSettings().clear()"
```

## What Gets Persisted

✓ Window width and height
✓ Window X and Y position
✓ Maximized/Normal state
✓ Dock widget positions and sizes
✓ Dock widget visibility
✓ Active tab index
✓ Dock layout (tabified docks, nested docks, etc.)

## What Doesn't Get Persisted

✗ Unsaved model data
✗ Temporary settings
✗ Cache data
✗ User preferences (those are saved separately)

## Implementation Files

- **Main Implementation:** `src/gui/main_window.py`
  - `_restore_window_state()` - Lines 867-890
  - `_save_window_settings()` - Lines 892-907
  - `closeEvent()` - Lines 923-957

- **Test Files:**
  - `test_qsettings_persistence.py` - QSettings persistence test
  - `test_window_persistence.py` - GUI window persistence test

- **Documentation:**
  - `WINDOW_PERSISTENCE_IMPLEMENTATION.md` - Technical details
  - `WINDOW_PERSISTENCE_TEST_GUIDE.md` - This file

