# Installer Update Summary - USER vs SYSTEM Installation Support

## Overview
Updated the NSIS installer (`config/installer.nsi`) to support both USER and SYSTEM installation modes, with corresponding detection improvements in `src/core/installation_detector.py`.

## Changes Made

### 1. **config/installer.nsi** - Complete Redesign

#### Key Additions:
- **Admin Privilege Request**: Added `RequestExecutionLevel highest` to enable system-level operations
- **Installation Type Variables**: Added variables to track installation type and registry root
- **Custom Selection Page**: New dialog page allowing users to choose between USER and SYSTEM installation
- **Dynamic Installation Paths**:
  - **USER**: `$LOCALAPPDATA\Digital Workshop` (no admin required)
  - **SYSTEM**: `$PROGRAMFILES\Digital Workshop` (admin required)
- **Registry Handling**:
  - **USER**: Writes to `HKEY_CURRENT_USER`
  - **SYSTEM**: Writes to `HKEY_LOCAL_MACHINE`
- **Installation Type Marker**: Stores `InstallationType` value in registry for later detection
- **Smart Uninstaller**: Detects installation type from registry and removes from correct location

#### Installation Type Selection Page Features:
- Radio button selection between USER and SYSTEM
- Clear descriptions of each option
- Default selection: USER (Recommended)
- Shows data storage location for each option
- Validates selection before proceeding

#### Registry Keys Written:
- **System Installation**: 
  - `HKLM\Software\Digital Workshop\InstallationType = "system"`
  - `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Digital Workshop`
  
- **User Installation**:
  - `HKCU\Software\Digital Workshop\InstallationType = "user"`
  - `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Digital Workshop`

### 2. **src/core/installation_detector.py** - Enhanced Detection

#### Improvements to `_is_system_installation()`:
- **Registry-First Detection**: Now checks `HKEY_LOCAL_MACHINE` for explicit `InstallationType = "system"` marker
- **Fallback to Admin Check**: If registry marker not found, falls back to checking admin privileges
- **Windows-Specific**: Uses `winreg` module for Windows registry access
- **Graceful Degradation**: Handles missing registry keys and import errors

#### Detection Priority:
1. Check registry for explicit installation type marker
2. Fall back to admin privilege check
3. Default to USER installation if all else fails

## Behavior

### Installation Flow:
1. User runs installer
2. Presented with installation type selection page
3. Chooses USER or SYSTEM installation
4. Installer proceeds with appropriate paths and registry locations
5. Installation type is stored in registry for future detection

### Uninstallation Flow:
1. Uninstaller reads installation type from registry
2. Removes files from correct location
3. Removes registry keys from correct hive (HKLM or HKCU)

## Compatibility

- **Backward Compatible**: Existing installations will still work
- **Detection Fallback**: If registry marker missing, falls back to admin privilege check
- **Cross-Platform Ready**: Code structure supports future macOS/Linux implementation

## Testing Recommendations

1. **USER Installation**:
   - Run installer as regular user
   - Select "User Installation"
   - Verify files in `%LOCALAPPDATA%\Digital Workshop`
   - Verify registry in `HKCU\Software\Digital Workshop`

2. **SYSTEM Installation**:
   - Run installer as administrator
   - Select "System Installation"
   - Verify files in `%PROGRAMFILES%\Digital Workshop`
   - Verify registry in `HKLM\Software\Digital Workshop`

3. **Uninstallation**:
   - Test uninstall for both USER and SYSTEM installations
   - Verify all files and registry keys removed correctly

## Files Modified
- `config/installer.nsi` - Complete redesign with USER/SYSTEM support
- `src/core/installation_detector.py` - Enhanced `_is_system_installation()` method

