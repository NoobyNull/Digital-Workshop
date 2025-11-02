# Digital Workshop - Build System Issues Analysis

## Critical Issues Found

### 1. **Workflow Mismatch: Two Different Build Approaches**

#### `.github/workflows/build.yml` (Triggered on Release)
```yaml
pyinstaller --onefile --name "Digital Workshop" src/main.py
copy "dist\Digital Workshop.exe" "Digital-Workshop-Installer.exe"
```
- Uses PyInstaller **directly** (not via build.py)
- Creates `Digital-Workshop-Installer.exe` (wrong naming)
- Uses NSIS installer (makensis-action)

#### `.github/workflows/release.yml` (Manual Release)
```yaml
python build.py --no-tests
```
- Calls `build.py` script
- Expects `pyinstaller.spec` file
- Expects Inno Setup (iscc) compiler
- Expects installer output: `Digital Workshop-Setup-{version}.exe`

**Problem:** These workflows are incompatible!

---

### 2. **Installer Configuration Issues**

#### `config/installer.nsi` Problems:
- **Too basic** - missing version info, license, readme
- **Wrong output filename** - creates `Digital-Workshop-Installer.exe` instead of `Digital Workshop-Setup-{version}.exe`
- **No version variable** - release.yml tries to update `#define MyAppVersion` but it doesn't exist
- **Missing assets** - no license.txt, readme.txt references
- **No uninstaller** - no uninstall section

#### Expected by release.yml:
```
dist/Digital Workshop.exe
dist/Digital Workshop-Setup-1.0.0.exe
dist/build_report.json
```

#### Actually created:
```
dist/Digital Workshop.exe
Digital-Workshop-Installer.exe (in root, not dist/)
```

---

### 3. **build.py Script Issues**

- Expects **Inno Setup** (iscc) but workflows use **NSIS** (makensis)
- Looks for installer assets in `resources/` directory (don't exist)
- Spec file path hardcoded to `pyinstaller.spec`
- No version synchronization with GitHub releases

---

### 4. **Missing Build Assets**

Required but missing:
- `resources/license.txt` - License file for installer
- `resources/readme.txt` - Readme for installer
- `resources/icons/app_icon.ico` - Application icon (build.py creates placeholder)

---

### 5. **Version Management Issues**

- Version hardcoded in `build.py` as `"1.0.0"`
- release.yml tries to update version in `build.py` but uses wrong regex
- No version file for PyInstaller (version_file=None in spec)
- No version info in executable properties

---

## Recommended Solution

### Option A: Simplify to NSIS Only (Recommended)
1. Update `build.py` to use NSIS instead of Inno Setup
2. Create proper `config/installer.nsi` with version variables
3. Consolidate both workflows to use `build.py`
4. Create missing installer assets

### Option B: Use Inno Setup Only
1. Update GitHub Actions to use Inno Setup
2. Create proper Inno Setup script
3. Remove NSIS references

### Option C: Unified PyInstaller Approach (Simplest)
1. Remove build.py complexity
2. Use PyInstaller directly in both workflows
3. Skip installer creation (just distribute .exe)
4. Use GitHub Releases for distribution

---

## What's Needed for a Good Release

1. **Consistent build process** - One workflow, not two conflicting ones
2. **Proper installer** - With version info, license, uninstaller
3. **Version management** - Automated version bumping and sync
4. **Build artifacts** - Executable + installer + build report
5. **Asset management** - License, readme, icon files
6. **Error handling** - Clear failure messages and logs

---

## Next Steps

1. Choose which approach (A, B, or C)
2. Create missing installer assets
3. Fix installer script (NSIS or Inno Setup)
4. Consolidate workflows
5. Test locally with `python build.py`
6. Create a test release to verify

Would you like me to implement one of these solutions?

