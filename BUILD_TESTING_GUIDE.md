# Digital Workshop - Build Testing Guide

## What Was Fixed

✅ **Consolidated build system** - Now uses NSIS consistently  
✅ **Fixed installer script** - Proper version variables and uninstaller  
✅ **Created missing assets** - license.txt and readme.txt  
✅ **Updated workflows** - Both build.yml and release.yml now use build.py  
✅ **Consistent naming** - Installer output: `Digital Workshop-Setup-{version}.exe`  

---

## Prerequisites

### Windows System
- Windows 10 or later
- Administrator access (for NSIS installation)

### Required Software
```bash
# Python 3.10+
python --version

# Install NSIS (via Chocolatey)
choco install nsis -y

# Or download from: https://nsis.sourceforge.io/
```

### Python Dependencies
```bash
cd "D:/Digital Workshop"
pip install -r requirements.txt
pip install pyinstaller
```

---

## Testing the Build Locally

### Step 1: Clean Previous Builds
```bash
cd "D:/Digital Workshop"
python build.py --clean-only
```

### Step 2: Run Full Build
```bash
python build.py
```

This will:
1. ✓ Clean previous build directories
2. ✓ Check dependencies (Python, PyInstaller, NSIS)
3. ✓ Create app icon if missing
4. ✓ Run PyInstaller with spec file
5. ✓ Create NSIS installer
6. ✓ Generate build report

### Step 3: Verify Build Artifacts
```bash
# Check if files were created
dir dist\

# Expected output:
# - Digital Workshop.exe (the application)
# - Digital Workshop-Setup-1.0.0.exe (the installer)
# - build_report.json (build summary)
```

### Step 4: Test the Executable
```bash
# Run the application directly
"dist\Digital Workshop.exe"

# Verify it launches without errors
```

### Step 5: Test the Installer
```bash
# Run the installer
"dist\Digital Workshop-Setup-1.0.0.exe"

# Follow the installation wizard
# Verify shortcuts are created on Desktop and Start Menu
# Verify uninstaller works
```

---

## Build Options

### Skip Tests
```bash
python build.py --no-tests
```

### Skip Installer Creation
```bash
python build.py --no-installer
```

### Both
```bash
python build.py --no-tests --no-installer
```

---

## Build Report

After building, check `dist/build_report.json`:

```json
{
  "build_date": "2024-11-02T10:30:45.123456",
  "duration_seconds": 45.67,
  "app_name": "Digital Workshop",
  "version": "1.0.0",
  "python_version": "3.10.0",
  "success": true,
  "executable_created": true,
  "executable_size_mb": 125.45,
  "installer_created": true,
  "installer_size_mb": 95.23
}
```

---

## Troubleshooting

### Issue: "PyInstaller not found"
```bash
pip install pyinstaller
```

### Issue: "NSIS compiler not found"
```bash
choco install nsis -y
# Or download from https://nsis.sourceforge.io/
```

### Issue: "Installer assets missing"
Verify these files exist:
- `resources/license.txt`
- `resources/readme.txt`

### Issue: "Spec file not found"
Verify `pyinstaller.spec` exists in project root

### Issue: Build fails with import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Installer won't create
Check build log for details:
```bash
# Look for build_*.log files in project root
type build_*.log
```

---

## GitHub Actions Testing

### Trigger Build Workflow
1. Create a GitHub release
2. The build.yml workflow will automatically run
3. Check Actions tab for results
4. Artifacts will be attached to the release

### Trigger Release Workflow
1. Go to Actions → Release - Manual Release Workflow
2. Click "Run workflow"
3. Select version bump (major/minor/patch)
4. Optionally add release notes
5. Workflow will:
   - Bump version
   - Build application
   - Create installer
   - Generate release notes
   - Create GitHub release
   - Merge to main

---

## Next Steps

1. **Test locally** - Run `python build.py` and verify artifacts
2. **Test installer** - Run the .exe installer and verify installation
3. **Create test release** - Create a GitHub release to test workflows
4. **Monitor Actions** - Check GitHub Actions for any failures
5. **Iterate** - Fix any issues and re-test

---

## Success Criteria

✅ `dist/Digital Workshop.exe` created (125+ MB)  
✅ `dist/Digital Workshop-Setup-1.0.0.exe` created (95+ MB)  
✅ `dist/build_report.json` created with success=true  
✅ Application launches without errors  
✅ Installer runs and creates shortcuts  
✅ Uninstaller removes all files  
✅ GitHub Actions workflows complete successfully  

---

## Support

For issues or questions:
- Check build logs: `build_*.log`
- Review BUILD_ISSUES_ANALYSIS.md for background
- Check GitHub Actions logs for workflow issues

