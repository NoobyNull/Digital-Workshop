# Digital Workshop - Running Guide

This guide provides comprehensive instructions for running the Digital Workshop application in both development and production modes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Running from Source Code (Development Mode)](#running-from-source-code-development-mode)
- [Running from Built Package (Production Mode)](#running-from-built-package-production-mode)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Known Issues and Fixes](#known-issues-and-fixes)

## Prerequisites

### System Requirements

**Minimum:**
- OS: Windows 7 SP1 (64-bit)
- CPU: Intel Core i3-3220 (Ivy Bridge) or equivalent
- GPU: Intel HD Graphics 4000 or equivalent
- RAM: 4GB
- Storage: 100MB free space

**Recommended:**
- OS: Windows 10/11 (64-bit)
- CPU: Intel Core i5-3470 or equivalent
- GPU: NVIDIA GeForce GTX 1050 or equivalent
- RAM: 8GB
- Storage: 500MB free space (SSD recommended)

### Software Requirements

**Required for Development:**
- Python 3.8-3.12 (64-bit)
- Git

**Required for Production:**
- None (included in installer)

**GUI Framework:**
- PySide6>=6.0.0 (default)
- PySide5>=5.15.0 (alternative, see troubleshooting)

### Graphics API Support

- **OpenGL:** 3.3 Core Profile minimum
- **DirectX:** 11.0 minimum (via ANGLE fallback)
- **Fallback:** Qt software rasterizer (limited performance)

## Running from Source Code (Development Mode)

### Step 1: Clone or Download the Repository

If you haven't already, clone the repository:

```bash
git clone <repository-url>
cd digital-workshop
```

### Step 2: Set Up Python Environment

1. Install Python 3.8-3.12 (64-bit) from [python.org](https://www.python.org/downloads/)
2. Verify installation:
   ```bash
   python --version
   ```
3. (Recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

### Step 3: Install Dependencies

**Option 1: Using pip (Recommended)**

Install the required Python packages:

```bash
pip install -r requirements.txt
```

If you encounter any issues with PyQt3D, you can install it separately:

```bash
pip install PyQt3D>=5.15.0
```

**Option 2: Using conda (Alternative)**

If you have conda installed, you can create a conda environment:

```bash
conda env create -f requirements-conda.yml
conda activate digital-workshop
```

**Troubleshooting PySide Installation Issues**

If you encounter errors like "ERROR: Could not find a version that satisfies the requirement PySide5>=5.15.0", try these solutions:

1. **Use PySide6 instead (Recommended)**:
   ```bash
   pip install PySide6>=6.0.0
   ```

2. **Update pip and setuptools**:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

3. **Check Python version compatibility**:
   - PySide6 requires Python 3.6 or later
   - PySide5 requires Python 3.5 or later
   - Verify your Python version: `python --version`

4. **Install from pre-built wheels**:
   ```bash
   pip install --only-binary :all: PySide6
   ```

5. **For Windows users**: If pip installation fails, try installing from wheel files:
   - Download wheels from: https://pypi.org/project/PySide6/#files
   - Install with: `pip install path/to/downloaded.whl`

6. **For Linux users**: Install system dependencies first:
   ```bash
   # Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install libegl1-mesa-dev libgl1-mesa-dev libglu1-mesa-dev libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
   
   # Then install PySide6:
   pip install PySide6
   ```

### Step 4: Fix Circular Import Issues

There's a known circular import issue between `parsers/base_parser.py` and `core/model_cache.py`. To fix this:

1. Open `src/parsers/base_parser.py`
2. Remove the direct import of `model_cache` and replace it with a local import in the methods that need it:

```python
# Remove this line from the top:
# from core.model_cache import get_model_cache, CacheLevel

# Add this inside the methods that need it:
def parse_file(self, file_path, progress_callback=None, lazy_loading=True):
    # ... existing code ...
    
    # Local import to avoid circular dependency
    from core.model_cache import get_model_cache, CacheLevel
    self.model_cache = get_model_cache()
    
    # ... rest of the method ...
```

Alternatively, you can apply this fix automatically by running:

```bash
python fix_circular_imports.py
```

### Step 5: Run the Application

Navigate to the project root directory and run:

```bash
python src/main.py
```

The application should start and display the main window.

### Step 6: Verify Installation

Once the application is running:
1. Check that the main window loads properly
2. Try importing a 3D model file (STL, OBJ, 3MF, or STEP)
3. Verify that the model renders correctly in the viewer

## Running from Built Package (Production Mode)

### Option 1: Using the Pre-built Installer

1. Download the latest installer from the releases page
2. Run the installer executable (`Digital Workshop-Setup-1.0.0.exe`)
3. Follow the installation wizard
4. Launch Digital Workshop from the Start menu or desktop shortcut

### Option 2: Building the Application Yourself

#### Step 1: Install Build Dependencies

```bash
pip install pyinstaller>=5.0.0
```

For creating the installer, you'll also need:
- [Inno Setup](https://jrsoftware.org/isinfo.php) (for Windows installer creation)

#### Step 2: Build the Executable

Run the build script:

```bash
python build.py
```

This will:
1. Clean previous build directories
2. Run PyInstaller to create the executable
3. Create the Inno Setup installer (if Inno Setup is installed)
4. Generate a build report

#### Step 3: Run the Built Application

After building successfully:

1. Navigate to the `dist` directory
2. Run `Digital Workshop.exe` directly
3. Or run the installer from `dist/Digital Workshop-Setup-1.0.0.exe`

#### Alternative: Manual PyInstaller Build

If you prefer to run PyInstaller directly:

```bash
pyinstaller pyinstaller.spec --clean
```

## Troubleshooting Common Issues

### Issue: ModuleNotFoundError: No module named 'PySide6' or 'PySide5'

**Solution:**
```bash
# For PySide6 (recommended):
pip install PySide6>=6.0.0

# For PySide5 (alternative):
pip install PySide5>=5.15.0
```

**Note:** The application has been updated to use PySide6 by default. If you encounter import errors, make sure you have the correct version installed.

### Issue: ModuleNotFoundError: No module named 'PyQt3D'

**Solution:**
```bash
pip install PyQt3D>=5.15.0
```

### Issue: OpenGL/DirectX rendering problems

**Symptoms:**
- Models don't display correctly
- Viewer widget appears black or blank
- Error messages about OpenGL context

**Solutions:**
1. Update your graphics drivers
2. Try running with software rendering:
   ```bash
   set QT_OPENGL=software
   python src/main.py
   ```
3. Check if your system supports OpenGL 3.3 or later

### Issue: SQLite FTS5 compatibility

**Symptoms:**
- Database errors on startup
- Search functionality not working

**Solutions:**
1. Ensure you're using SQLite 3.9.0 or later
2. Update Python to a newer version that includes a recent SQLite
3. If needed, install a newer SQLite version:
   ```bash
   pip install pysqlite3-binary
   ```

### Issue: Application won't start after installation

**Solutions:**
1. Check Windows Event Viewer for error details
2. Try running as administrator
3. Install Microsoft Visual C++ Redistributable (if missing)
4. Verify all required DLLs are present in the installation directory

### Issue: Performance problems with large models

**Solutions:**
1. Check the Performance Monitor in the application (View → Performance Monitor)
2. Reduce model cache size in Settings
3. Close other applications to free up RAM
4. Consider upgrading to an SSD for better disk performance

## Known Issues and Fixes

### Circular Import Issue (Development Mode)

**Problem:** Circular import between `parsers/base_parser.py` and `core/model_cache.py`

**Fix:** Apply the fix described in [Step 4: Fix Circular Import Issues](#step-4-fix-circular-import-issues) above.

### PySide5 vs PySide6 Import Inconsistency

**Problem:** The main.py uses PySide6 imports but requirements.txt specifies PySide5

**Fix:** The application has been updated to use PySide6 consistently. If you're still experiencing issues:

1. **Ensure PySide6 is installed**:
   ```bash
   pip install PySide6>=6.0.0
   ```

2. **If you need to use PySide5 instead**:
   - Update all imports in the codebase from `PySide6` to `PySide5`
   - Or modify requirements.txt to use PySide5 and comment out PySide6

3. **For mixed environments**, you can create a compatibility module:
   ```python
   # Try PySide6 first, fall back to PySide5
   try:
       from PySide6.QtWidgets import QApplication
       from PySide6.QtCore import QStandardPaths, QDir, Qt
   except ImportError:
       from PySide5.QtWidgets import QApplication
       from PySide5.QtCore import QStandardPaths, QDir, Qt
   ```

### Missing Application Icon

**Problem:** No application icon when running from source

**Fix:** The build script will create a placeholder icon. For a custom icon:
1. Create `resources/icons/app_icon.ico`
2. The icon should contain multiple sizes (16x16 to 256x256)

### Database Migration Issues

**Problem:** Settings migration fails on startup

**Fix:**
1. Delete the application data directory and restart
2. Or manually migrate settings:
   ```python
   from core.settings_migration import migrate_settings
   migrate_settings()
   ```

## Additional Resources

- [Developer Documentation](developer/architecture.md)
- [Parser Documentation](developer/)
- [Performance Optimization Guide](developer/performance_optimization_documentation.md)
- [Packaging Documentation](developer/packaging_documentation.md)

## Getting Help

If you encounter issues not covered in this guide:

1. Check the application logs in the `logs` directory
2. Search the existing issues on the project repository
3. Create a new issue with:
   - Detailed error description
   - Steps to reproduce
   - System information (OS, Python version, etc.)
   - Application logs if available