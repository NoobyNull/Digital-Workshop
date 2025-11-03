# GitHub Build Process - Explained

## Overview
The GitHub builder creates **TWO separate artifacts**:
1. **Standalone All-in-One EXE** - `Digital Workshop.exe` (portable executable)
2. **NSIS Installer** - `Digital Workshop-Setup-1.0.0.exe` (installer with USER/SYSTEM options)

---

## Build Process Flow

### Step 1: PyInstaller Compilation
**File**: `pyinstaller.spec`

```
Input: src/main.py + all dependencies
↓
PyInstaller (--onefile mode)
↓
Output: dist/Digital Workshop.exe (standalone executable)
```

**Key Configuration**:
- **Mode**: `--onefile` (creates single executable)
- **Includes**: 
  - All Python code compiled to bytecode
  - PySide6 (Qt framework)
  - VTK (3D visualization)
  - SQLite3
  - All resources bundled inside
- **Excludes**: matplotlib, scipy, numpy.distutils (to reduce size)
- **Result**: ~150-200MB standalone EXE with everything included

### Step 2: NSIS Installer Creation
**File**: `config/installer.nsi`

```
Input: dist/Digital Workshop.exe (from Step 1)
↓
NSIS Compiler (makensis)
↓
Output: dist/Digital Workshop-Setup-1.0.0.exe (installer)
```

**What the Installer Contains**:
- The compiled `Digital Workshop.exe` from PyInstaller
- Installation type selection dialog (USER vs SYSTEM)
- Registry configuration
- Shortcut creation logic
- Uninstaller

---

## Two Artifacts Explained

### Artifact 1: `Digital Workshop.exe` (Standalone)
- **Size**: ~150-200MB
- **Type**: Portable executable
- **What it is**: The compiled Python application with all dependencies
- **How to use**: 
  - Run directly without installation
  - Can be placed on USB drive
  - Detected as PORTABLE installation type
  - Creates temporary extraction directory on first run

### Artifact 2: `Digital Workshop-Setup-1.0.0.exe` (Installer)
- **Size**: ~5-10MB (much smaller - just wraps the EXE)
- **Type**: NSIS installer
- **What it contains**: 
  - The `Digital Workshop.exe` from Artifact 1
  - Installation logic
  - Registry configuration
  - Shortcut creation
- **How to use**:
  - Run installer
  - Choose USER or SYSTEM installation
  - Installer extracts and places files
  - Creates shortcuts and registry entries

---

## Installation Type Detection

### When Running `Digital Workshop.exe` Directly (Portable)
```
Application detects:
- Executable name contains "Digital Workshop.exe"
- No app data directory exists
- No registry entries
→ Detected as: PORTABLE installation
```

### When Running from Installer (USER Installation)
```
Installer writes:
- Files to: %LOCALAPPDATA%\Digital Workshop\
- Registry to: HKEY_CURRENT_USER\Software\Digital Workshop
- InstallationType = "user"

Application detects:
- Registry entry: InstallationType = "user"
→ Detected as: USER installation
```

### When Running from Installer (SYSTEM Installation)
```
Installer writes:
- Files to: %PROGRAMFILES%\Digital Workshop\
- Registry to: HKEY_LOCAL_MACHINE\Software\Digital Workshop
- InstallationType = "system"

Application detects:
- Registry entry: InstallationType = "system"
→ Detected as: SYSTEM installation
```

---

## GitHub Workflow Steps

### Build Workflow (`.github/workflows/build.yml`)
Triggered on: **Release published**

1. Checkout code
2. Setup Python 3.10
3. Install dependencies (pip install -r requirements.txt)
4. Install PyInstaller
5. Install NSIS (via Chocolatey)
6. Run `python build.py --no-tests`
   - Cleans previous builds
   - Runs PyInstaller → creates `Digital Workshop.exe`
   - Runs NSIS → creates `Digital Workshop-Setup-1.0.0.exe`
7. Verify both artifacts exist
8. Upload to GitHub Release:
   - `dist/Digital Workshop.exe`
   - `dist/Digital Workshop-Setup-1.0.0.exe`
   - `dist/build_report.json`

### Release Workflow (`.github/workflows/release.yml`)
Triggered on: **Manual workflow dispatch**

1. Checkout code
2. Setup Python 3.10
3. Calculate new version (major/minor/patch bump)
4. Update version in `build.py`
5. Update version in `config/installer.nsi`
6. Create release branch
7. Build application (same as Build Workflow)
8. Generate release notes from git commits
9. Create GitHub Release with tag
10. Merge to main branch
11. Push version tag
12. Clean up release branch

---

## What Gets Compiled

### PyInstaller Bundles:
- ✅ All Python source code (compiled to bytecode)
- ✅ PySide6 (Qt framework for GUI)
- ✅ VTK (3D visualization library)
- ✅ SQLite3 (database)
- ✅ Resources folder (icons, license, readme)
- ✅ Config files (installer.nsi)

### Excluded (to reduce size):
- ❌ matplotlib
- ❌ scipy
- ❌ numpy.distutils
- ❌ unittest/test modules

---

## File Sizes (Approximate)

| File | Size | Type |
|------|------|------|
| Digital Workshop.exe | 150-200MB | Standalone executable |
| Digital Workshop-Setup-1.0.0.exe | 5-10MB | Installer wrapper |
| build_report.json | <1MB | Build metadata |

---

## Summary

**GitHub Builder Creates**:
1. **Standalone EXE** - All-in-one executable with everything compiled
2. **Installer EXE** - Wrapper that installs the standalone EXE with USER/SYSTEM options

**When User Downloads**:
- Option A: Download `Digital Workshop.exe` → Run directly (PORTABLE mode)
- Option B: Download `Digital Workshop-Setup-1.0.0.exe` → Install (USER or SYSTEM mode)

Both are valid, just different use cases.

