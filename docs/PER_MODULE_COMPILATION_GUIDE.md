# Per-Module Compilation Guide

**Date**: 2025-11-04  
**Status**: Ready to implement  
**Scope**: Compile each module separately for independent updates

---

## 🎯 Overview

Instead of one monolithic executable, we compile:
- **Core Module** - App executable + core dependencies
- **PySide6 Module** - GUI framework
- **VTK Module** - 3D rendering
- **OpenCV Module** - Image processing
- **NumPy Module** - Numerical computing

Each module is:
- ✅ Compiled separately
- ✅ Versioned independently
- ✅ Updated independently
- ✅ Verified with checksums

---

## 📁 Directory Structure

```
dist/
├── modules/
│   ├── core/
│   │   ├── Digital Workshop.exe
│   │   ├── manifest.json
│   │   └── checksum.txt
│   │
│   ├── pyside6/
│   │   ├── pyside6_module.zip
│   │   ├── manifest.json
│   │   └── checksum.txt
│   │
│   ├── vtk/
│   │   ├── vtk_module.zip
│   │   ├── manifest.json
│   │   └── checksum.txt
│   │
│   ├── opencv/
│   │   ├── opencv_module.zip
│   │   ├── manifest.json
│   │   └── checksum.txt
│   │
│   └── numpy/
│       ├── numpy_module.zip
│       ├── manifest.json
│       └── checksum.txt
│
└── installer/
    ├── Digital Workshop Installer.exe
    └── modules_manifest.json
```

---

## 🔧 PyInstaller Specs

### 1. Core Module Spec

**File**: `config/pyinstaller-core.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'sqlite3',
        'json',
        'pathlib',
    ],
    excludes=[
        'vtk',
        'cv2',
        'numpy',
        'matplotlib',
        'scipy',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Digital Workshop',
    debug=False,
    console=False,
    icon='resources/icons/app_icon.ico',
)
```

### 2. PySide6 Module Spec

**File**: `config/pyinstaller-pyside6.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))

# Collect only PySide6 and dependencies
a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtOpenGL',
        'PySide6.QtSvg',
    ],
    excludes=[
        'vtk',
        'cv2',
        'numpy',
        'matplotlib',
        'scipy',
        'src',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

# Create as ZIP for module distribution
collect = COLLECT(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='pyside6_module'
)
```

### 3. VTK Module Spec

**File**: `config/pyinstaller-vtk.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'vtk',
        'vtk.vtkRenderingCore',
        'vtk.vtkFiltersSources',
        'vtk.vtkIOGeometry',
        'vtk.vtkIOPLY',
        'vtk.vtkIOSTL',
    ],
    excludes=[
        'cv2',
        'numpy',
        'matplotlib',
        'scipy',
        'src',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

collect = COLLECT(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='vtk_module'
)
```

### 4. OpenCV Module Spec

**File**: `config/pyinstaller-opencv.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'cv2',
        'cv2.cv2',
    ],
    excludes=[
        'vtk',
        'numpy',
        'matplotlib',
        'scipy',
        'src',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

collect = COLLECT(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='opencv_module'
)
```

### 5. NumPy Module Spec

**File**: `config/pyinstaller-numpy.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'numpy',
        'numpy.core',
        'numpy.linalg',
    ],
    excludes=[
        'vtk',
        'cv2',
        'matplotlib',
        'scipy',
        'src',
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

collect = COLLECT(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='numpy_module'
)
```

---

## 🏗️ Build Process

### Step 1: Build Core Module
```bash
pyinstaller config/pyinstaller-core.spec
# Output: dist/Digital Workshop.exe (~40 MB)
```

### Step 2: Build PySide6 Module
```bash
pyinstaller config/pyinstaller-pyside6.spec
# Output: dist/pyside6_module/ (~70 MB)
# Compress: dist/pyside6_module.zip
```

### Step 3: Build VTK Module
```bash
pyinstaller config/pyinstaller-vtk.spec
# Output: dist/vtk_module/ (~80 MB)
# Compress: dist/vtk_module.zip
```

### Step 4: Build OpenCV Module
```bash
pyinstaller config/pyinstaller-opencv.spec
# Output: dist/opencv_module/ (~50 MB)
# Compress: dist/opencv_module.zip
```

### Step 5: Build NumPy Module
```bash
pyinstaller config/pyinstaller-numpy.spec
# Output: dist/numpy_module/ (~30 MB)
# Compress: dist/numpy_module.zip
```

---

## 📝 Module Manifest

Each module has a `manifest.json`:

```json
{
  "module_name": "core",
  "version": "0.1.5",
  "size_mb": 40,
  "checksum": "sha256:abc123...",
  "dependencies": [],
  "required": true,
  "description": "Core application executable",
  "build_date": "2025-11-04T10:30:00Z",
  "python_version": "3.12",
  "platform": "win64"
}
```

---

## 🔐 Checksum Verification

### Generate Checksums
```python
import hashlib

def generate_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# For each module
checksum = generate_checksum("dist/pyside6_module.zip")
print(f"sha256:{checksum}")
```

### Verify Checksums
```python
def verify_checksum(file_path, expected_checksum):
    actual = generate_checksum(file_path)
    return actual == expected_checksum.replace("sha256:", "")

# Verify before installation
if verify_checksum("pyside6_module.zip", manifest["checksum"]):
    print("✓ Checksum verified")
else:
    print("✗ Checksum mismatch - corrupted file")
```

---

## 🔄 Module Dependencies

```
Core Module (required)
├─ PySide6 Module (required)
├─ VTK Module (optional)
├─ OpenCV Module (optional)
└─ NumPy Module (optional)
```

### Dependency Resolution
```python
DEPENDENCIES = {
    "core": [],
    "pyside6": ["core"],
    "vtk": ["core", "numpy"],
    "opencv": ["core", "numpy"],
    "numpy": ["core"],
}

def get_required_modules(modules_to_install):
    """Get all required modules including dependencies"""
    required = set(modules_to_install)
    
    for module in modules_to_install:
        deps = DEPENDENCIES.get(module, [])
        required.update(deps)
    
    return required
```

---

## 📊 Module Sizes

| Module | Size | Compressed |
|--------|------|-----------|
| Core | 40 MB | 35 MB |
| PySide6 | 70 MB | 60 MB |
| VTK | 80 MB | 65 MB |
| OpenCV | 50 MB | 40 MB |
| NumPy | 30 MB | 25 MB |
| **Total** | **270 MB** | **225 MB** |

---

## 🚀 Build Script Integration

### Updated build.py
```python
class ModularBuildManager:
    def build_modules(self):
        """Build all modules separately"""
        modules = ["core", "pyside6", "vtk", "opencv", "numpy"]
        
        for module in modules:
            self.build_module(module)
    
    def build_module(self, module_name):
        """Build single module"""
        spec_file = f"config/pyinstaller-{module_name}.spec"
        
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            spec_file,
            "--distpath", f"dist/modules/{module_name}",
            "--buildpath", f"build/{module_name}",
        ]
        
        subprocess.run(cmd, check=True)
        
        # Generate manifest and checksum
        self.generate_manifest(module_name)
        self.generate_checksum(module_name)
```

---

## ✅ Checklist

- [ ] Create pyinstaller-core.spec
- [ ] Create pyinstaller-pyside6.spec
- [ ] Create pyinstaller-vtk.spec
- [ ] Create pyinstaller-opencv.spec
- [ ] Create pyinstaller-numpy.spec
- [ ] Test each spec individually
- [ ] Verify module sizes
- [ ] Generate checksums
- [ ] Create manifests
- [ ] Test module combinations
- [ ] Update build.py
- [ ] Test build process
- [ ] Document module dependencies

---

**Status**: ✅ GUIDE COMPLETE

**Next**: Installer implementation

