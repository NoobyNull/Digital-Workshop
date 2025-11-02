# Digital Workshop - Naming Convention Implementation Guide

## Overview
This document provides step-by-step implementation instructions for standardizing naming conventions across all four Windows installer variants (RAW, PORTABLE, USER, SYSTEM).

## Implementation Order
Follow the phases in order. Each phase builds on the previous one.

---

## PHASE 1: CORE INFRASTRUCTURE (Must be completed first)

### Step 1.1: Create Installation Type Detection System

Create `src/core/installation_detector.py`:

```python
"""
Installation type detection for Digital Workshop.

Determines which installation variant is running to enable
installation-type specific behavior and paths.
"""

import os
import sys
import platform
from pathlib import Path
from enum import Enum
from typing import Optional

class InstallationType(Enum):
    """Enumeration of installation types."""
    RAW = "raw"
    PORTABLE = "portable"
    USER = "user"
    SYSTEM = "system"

class InstallationDetector:
    """Detects the current installation type."""
    
    def __init__(self):
        """Initialize the installation detector."""
        self._installation_type: Optional[InstallationType] = None
        self._detection_performed = False
    
    def detect_installation_type(self) -> InstallationType:
        """
        Detect the current installation type.
        
        Returns:
            InstallationType: The detected installation type
        """
        if not self._detection_performed:
            self._installation_type = self._perform_detection()
            self._detection_performed = True
        
        return self._installation_type
    
    def _perform_detection(self) -> InstallationType:
        """
        Perform the actual installation type detection.
        
        Returns:
            InstallationType: The detected installation type
        """
        # Check for RAW (development) installation
        if self._is_raw_installation():
            return InstallationType.RAW
        
        # Check for PORTABLE installation
        if self._is_portable_installation():
            return InstallationType.PORTABLE
        
        # Check for SYSTEM vs USER installation
        if self._is_system_installation():
            return InstallationType.SYSTEM
        
        # Default to USER installation
        return InstallationType.USER
    
    def _is_raw_installation(self) -> bool:
        """
        Check if this is a raw development installation.
        
        Returns:
            bool: True if raw development installation
        """
        # Check if we're running from source directory
        current_script = Path(sys.argv[0])
        src_dir = Path(__file__).parent.parent.parent
        
        # If we're in development mode (running from src/)
        if current_script.name in ['run.py', 'main.py'] or current_script.parent == src_dir:
            return True
        
        # Check for development environment indicators
        if os.path.exists(src_dir / 'run.py') and os.path.exists(src_dir / 'requirements.txt'):
            return True
        
        return False
    
    def _is_portable_installation(self) -> bool:
        """
        Check if this is a portable installation.
        
        Returns:
            bool: True if portable installation
        """
        # Portable installations typically run from a specific directory
        # and have DigitalWorkshop-Portable.exe or similar
        
        current_script = Path(sys.argv[0])
        executable_name = current_script.name.lower()
        
        # Check for portable executable name
        if 'portable' in executable_name:
            return True
        
        # Check for common portable installation patterns
        app_data = Path(os.environ.get('LOCALAPPDATA', ''))
        if not (app_data / 'DigitalWorkshop').exists():
            # If no app data directory, might be portable
            return True
        
        return False
    
    def _is_system_installation(self) -> bool:
        """
        Check if this is a system-wide installation.
        
        Returns:
            bool: True if system installation
        """
        # Check if running with elevated privileges (admin)
        try:
            if platform.system() == 'Windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.getuid() == 0
        except (AttributeError, ImportError):
            return False
    
    def get_installation_type(self) -> InstallationType:
        """
        Get the current installation type (cached).
        
        Returns:
            InstallationType: The installation type
        """
        return self._installation_type or self.detect_installation_type()
    
    def is_development(self) -> bool:
        """
        Check if this is a development installation.
        
        Returns:
            bool: True if development/raw installation
        """
        return self.get_installation_type() == InstallationType.RAW
    
    def is_portable(self) -> bool:
        """
        Check if this is a portable installation.
        
        Returns:
            bool: True if portable installation
        """
        return self.get_installation_type() == InstallationType.PORTABLE
    
    def is_user_install(self) -> bool:
        """
        Check if this is a user installation.
        
        Returns:
            bool: True if user installation
        """
        return self.get_installation_type() == InstallationType.USER
    
    def is_system_install(self) -> bool:
        """
        Check if this is a system installation.
        
        Returns:
            bool: True if system installation
        """
        return self.get_installation_type() == InstallationType.SYSTEM

# Global installation detector instance
_installation_detector = InstallationDetector()

def get_installation_type() -> InstallationType:
    """
    Get the current installation type.
    
    Returns:
        InstallationType: The installation type
    """
    return _installation_detector.get_installation_type()

def is_development() -> bool:
    """
    Check if this is a development installation.
    
    Returns:
        bool: True if development installation
    """
    return _installation_detector.is_development()

def is_portable() -> bool:
    """
    Check if this is a portable installation.
    
    Returns:
        bool: True if portable installation
    """
    return _installation_detector.is_portable()

def is_user_install() -> bool:
    """
    Check if this is a user installation.
    
    Returns:
        bool: True if user installation
    """
    return _installation_detector.is_user_install()

def is_system_install() -> bool:
    """
    Check if this is a system installation.
    
    Returns:
        bool: True if system installation
    """
    return _installation_detector.is_system_install()
```

### Step 1.2: Create Version Management System

Create `src/core/version_manager.py`:

```python
"""
Version management for Digital Workshop.

Provides installation-type aware version information.
"""

import os
from typing import Optional
from dataclasses import dataclass
from .installation_detector import InstallationType, get_installation_type

@dataclass
class VersionInfo:
    """Version information container."""
    base_version: str
    installation_type: str
    display_version: str
    logger_name: str
    organization_name: str

class VersionManager:
    """Manages version information for different installation types."""
    
    def __init__(self):
        """Initialize the version manager."""
        self._base_version = "1.0.0"
        self._version_cache: Optional[VersionInfo] = None
    
    def get_version_info(self) -> VersionInfo:
        """
        Get version information for the current installation.
        
        Returns:
            VersionInfo: Version information for current installation
        """
        if self._version_cache is None:
            self._version_cache = self._create_version_info()
        
        return self._version_cache
    
    def _create_version_info(self) -> VersionInfo:
        """
        Create version information for the current installation.
        
        Returns:
            VersionInfo: Version information
        """
        installation_type = get_installation_type()
        
        # Determine display version based on installation type
        if installation_type == InstallationType.RAW:
            display_version = f"{self._base_version}-Raw"
            logger_name = "DigitalWorkshop-Raw"
            organization_name = "DigitalWorkshop"
        elif installation_type == InstallationType.PORTABLE:
            display_version = f"{self._base_version}-Portable"
            logger_name = "DigitalWorkshop-Portable"
            organization_name = "DigitalWorkshop"
        else:  # USER or SYSTEM
            display_version = self._base_version
            logger_name = "DigitalWorkshop"
            organization_name = "DigitalWorkshop"
        
        return VersionInfo(
            base_version=self._base_version,
            installation_type=installation_type.value,
            display_version=display_version,
            logger_name=logger_name,
            organization_name=organization_name
        )
    
    def get_display_version(self) -> str:
        """
        Get the display version for the current installation.
        
        Returns:
            str: The display version
        """
        return self.get_version_info().display_version
    
    def get_logger_name(self) -> str:
        """
        Get the logger name for the current installation.
        
        Returns:
            str: The logger name
        """
        return self.get_version_info().logger_name
    
    def get_organization_name(self) -> str:
        """
        Get the organization name for the current installation.
        
        Returns:
            str: The organization name
        """
        return self.get_version_info().organization_name
    
    def get_base_version(self) -> str:
        """
        Get the base version.
        
        Returns:
            str: The base version
        """
        return self._base_version

# Global version manager instance
_version_manager = VersionManager()

def get_display_version() -> str:
    """
    Get the display version for the current installation.
    
    Returns:
        str: The display version
    """
    return _version_manager.get_display_version()

def get_logger_name() -> str:
    """
    Get the logger name for the current installation.
    
    Returns:
        str: The logger name
    """
    return _version_manager.get_logger_name()

def get_organization_name() -> str:
    """
    Get the organization name for the current installation.
    
    Returns:
        str: The organization name
    """
    return _version_manager.get_organization_name()
```

### Step 1.3: Create Path Management System

Create `src/core/path_manager.py`:

```python
"""
Path management for Digital Workshop.

Provides installation-type aware path resolution.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from .installation_detector import InstallationType, get_installation_type

class PathManager:
    """Manages paths for different installation types."""
    
    def __init__(self):
        """Initialize the path manager."""
        self._paths_cache: Dict[str, Path] = {}
        self._installation_type = get_installation_type()
    
    def get_cache_directory(self) -> Path:
        """
        Get the cache directory for the current installation.
        
        Returns:
            Path: The cache directory path
        """
        if 'cache' not in self._paths_cache:
            self._paths_cache['cache'] = self._resolve_cache_path()
        
        return self._paths_cache['cache']
    
    def get_log_directory(self) -> Path:
        """
        Get the log directory for the current installation.
        
        Returns:
            Path: The log directory path
        """
        if 'log' not in self._paths_cache:
            self._paths_cache['log'] = self._resolve_log_path()
        
        return self._paths_cache['log']
    
    def get_data_directory(self) -> Path:
        """
        Get the data directory for the current installation.
        
        Returns:
            Path: The data directory path
        """
        if 'data' not in self._paths_cache:
            self._paths_cache['data'] = self._resolve_data_path()
        
        return self._paths_cache['data']
    
    def get_resource_directory(self) -> Path:
        """
        Get the resource directory for the current installation.
        
        Returns:
            Path: The resource directory path
        """
        if 'resource' not in self._paths_cache:
            self._paths_cache['resource'] = self._resolve_resource_path()
        
        return self._paths_cache['resource']
    
    def get_config_directory(self) -> Path:
        """
        Get the config directory for the current installation.
        
        Returns:
            Path: The config directory path
        """
        if 'config' not in self._paths_cache:
            self._paths_cache['config'] = self._resolve_config_path()
        
        return self._paths_cache['config']
    
    def get_database_file(self, db_name: str = "3dmm.db") -> Path:
        """
        Get the database file path for the current installation.
        
        Args:
            db_name: The database file name
            
        Returns:
            Path: The database file path
        """
        return self.get_data_directory() / db_name
    
    def _resolve_cache_path(self) -> Path:
        """
        Resolve the cache directory path based on installation type.
        
        Returns:
            Path: The cache directory path
        """
        if self._installation_type == InstallationType.RAW:
            # Development: use local cache directory
            return Path.cwd() / 'cache'
        elif self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = Path(sys.executable).parent if hasattr(sys, 'executable') else Path.cwd()
            return executable_dir / 'cache'
        else:  # USER or SYSTEM
            # Installed: use appropriate app data directory
            from PySide6.QtCore import QStandardPaths
            app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            base_path = Path(app_data_path) / 'DigitalWorkshop'
            
            if self._installation_type == InstallationType.SYSTEM:
                # System installation might use shared data
                try:
                    program_data = os.environ.get('PROGRAMDATA', '')
                    if program_data:
                        base_path = Path(program_data) / 'DigitalWorkshop'
                except (KeyError, OSError):
                    pass  # Fall back to user data
            
            return base_path / 'cache'
    
    def _resolve_log_path(self) -> Path:
        """
        Resolve the log directory path based on installation type.
        
        Returns:
            Path: The log directory path
        """
        cache_dir = self.get_cache_directory()
        return cache_dir / 'logs'
    
    def _resolve_data_path(self) -> Path:
        """
        Resolve the data directory path based on installation type.
        
        Returns:
            Path: The data directory path
        """
        cache_dir = self.get_cache_directory()
        return cache_dir / 'data'
    
    def _resolve_resource_path(self) -> Path:
        """
        Resolve the resource directory path based on installation type.
        
        Returns:
            Path: The resource directory path
        """
        if self._installation_type == InstallationType.RAW:
            # Development: use local resources directory
            return Path.cwd() / 'resources'
        elif self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = Path(sys.executable).parent if hasattr(sys, 'executable') else Path.cwd()
            return executable_dir / 'resources'
        else:  # USER or SYSTEM
            # Installed: use appropriate app data directory
            return self.get_data_directory() / 'resources'
    
    def _resolve_config_path(self) -> Path:
        """
        Resolve the config directory path based on installation type.
        
        Returns:
            Path: The config directory path
        """
        if self._installation_type == InstallationType.RAW:
            # Development: use local config directory
            return Path.cwd() / 'config'
        elif self._installation_type == InstallationType.PORTABLE:
            # Portable: use directory relative to executable
            executable_dir = Path(sys.executable).parent if hasattr(sys, 'executable') else Path.cwd()
            return executable_dir / 'config'
        else:  # USER or SYSTEM
            # Installed: use appropriate app data directory
            from PySide6.QtCore import QStandardPaths
            app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            base_path = Path(app_data_path) / 'DigitalWorkshop'
            
            if self._installation_type == InstallationType.SYSTEM:
                # System installation might use shared data
                try:
                    program_data = os.environ.get('PROGRAMDATA', '')
                    if program_data:
                        base_path = Path(program_data) / 'DigitalWorkshop'
                except (KeyError, OSError):
                    pass  # Fall back to user data
            
            return base_path / 'config'
    
    def ensure_directories_exist(self) -> None:
        """
        Ensure all required directories exist.
        """
        directories = [
            self.get_cache_directory(),
            self.get_log_directory(),
            self.get_data_directory(),
            self.get_resource_directory(),
            self.get_config_directory()
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# Global path manager instance
_path_manager = PathManager()

def get_cache_directory() -> Path:
    """
    Get the cache directory for the current installation.
    
    Returns:
        Path: The cache directory path
    """
    return _path_manager.get_cache_directory()

def get_log_directory() -> Path:
    """
    Get the log directory for the current installation.
    
    Returns:
        Path: The log directory path
    """
    return _path_manager.get_log_directory()

def get_data_directory() -> Path:
    """
    Get the data directory for the current installation.
    
    Returns:
        Path: The data directory path
    """
    return _path_manager.get_data_directory()

def get_resource_directory() -> Path:
    """
    Get the resource directory for the current installation.
    
    Returns:
        Path: The resource directory path
    """
    return _path_manager.get_resource_directory()

def get_config_directory() -> Path:
    """
    Get the config directory for the current installation.
    
    Returns:
        Path: The config directory path
    """
    return _path_manager.get_config_directory()

def get_database_file(db_name: str = "3dmm.db") -> Path:
    """
    Get the database file path for the current installation.
    
    Args:
        db_name: The database file name
        
    Returns:
        Path: The database file path
    """
    return _path_manager.get_database_file(db_name)

def ensure_directories_exist() -> None:
    """
    Ensure all required directories exist.
    """
    _path_manager.ensure_directories_exist()
```

---

## PHASE 2: UPDATE CORE MODULES

### Step 2.1: Update src/__init__.py

Replace the current content:

```python
"""
Digital Workshop (3D Model Manager) - A Windows desktop application for organizing and viewing 3D model collections.

This package contains the main source code for the Digital Workshop application.
"""

__version__ = "1.0.0"
__author__ = "Digital Workshop Development Team"
```

With:

```python
"""
Digital Workshop (3D Model Manager) - A Windows desktop application for organizing and viewing 3D model collections.

This package contains the main source code for the Digital Workshop application.
"""

from .core.version_manager import get_display_version, get_organization_name

__version__ = get_display_version()
__author__ = "Digital Workshop Development Team"

def get_version():
    """Get the current version string."""
    return __version__

def get_author():
    """Get the author information."""
    return __author__

def get_organization():
    """Get the organization name."""
    return get_organization_name()
```

### Step 2.2: Update src/core/logging_config.py

Find the logger name initialization (around line 272) and update:

```python
# OLD:
return logging.getLogger(f"Digital Workshop.{name}")

# NEW:
from .version_manager import get_logger_name
return logging.getLogger(f"{get_logger_name()}.{name}")
```

Find the log directory resolution (around line 240-242) and update:

```python
# OLD:
if log_dir == "logs":
    app_data = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    log_dir = str(app_data / 'DigitalWorkshop' / 'logs')

# NEW:
from .path_manager import get_log_directory
if log_dir == "logs":
    log_dir = str(get_log_directory())
```

### Step 2.3: Update src/core/model_cache.py

Find the cache directory initialization (around line 94-100) and update:

```python
# OLD:
if cache_dir == "cache":
    # Default to user local app data directory
    import os
    app_data = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    self.cache_dir = app_data / 'DigitalWorkshop' / 'cache'
else:
    self.cache_dir = Path(cache_dir)

# NEW:
from .path_manager import get_cache_directory
if cache_dir == "cache":
    self.cache_dir = get_cache_directory()
else:
    self.cache_dir = Path(cache_dir)
```

### Step 2.4: Update src/gui/theme/qt_material_service.py

Find the QSettings initialization (around line 90) and update:

```python
# OLD:
self.settings = QSettings("Digital Workshop", "Digital Workshop")

# NEW:
from ...core.version_manager import get_organization_name
organization = get_organization_name()
self.settings = QSettings(organization, organization)
```

### Step 2.5: Update src/gui/theme/theme_persistence.py

Find the QSettings initialization (around line 44-71) and update:

```python
# OLD:
self.settings = QSettings("Digital Workshop", "Digital Workshop")

# NEW:
from ...core.version_manager import get_organization_name
organization = get_organization_name()
self.settings = QSettings(organization, organization)
```

---

## PHASE 3: UPDATE VERSION DISPLAYS

### Step 3.1: Update src/gui/main_window.py

Find the about dialog implementation and update:

```python
# OLD:
about_text = f"""
<h3>Digital Workshop</h3>
<p>A comprehensive 3D modeling application built with Python, PySide6, and VTK.</p>
<p><b>Version:</b> 1.0.0</p>
<p><b>Author:</b> Digital Workshop Development Team</p>
"""

# NEW:
from ...core.version_manager import get_display_version
version = get_display_version()
about_text = f"""
<h3>Digital Workshop</h3>
<p>A comprehensive 3D modeling application built with Python, PySide6, and VTK.</p>
<p><b>Version:</b> {version}</p>
<p><b>Author:</b> Digital Workshop Development Team</p>
"""
```

### Step 3.2: Update src/gui/main_window_components/event_handler.py

Find the about dialog implementation and apply the same changes as above.

### Step 3.3: Update src/core/settings_migration.py

Find version fallback and update:

```python
# OLD:
version = settings.get("version", "1.0.0")

# NEW:
from ...core.version_manager import get_base_version
version = settings.get("version", get_base_version())
```

---

## PHASE 4: CREATE REQUIREMENTS FILES

### Step 4.1: Create requirements-raw.txt

```txt
# Digital Workshop - Development Requirements
# For RAW (development) installation

# Core dependencies
PySide6>=6.5.0
vtk>=9.2.0
numpy>=1.21.0
Pillow>=9.0.0

# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0

# Optional dependencies for enhanced functionality
matplotlib>=3.5.0
scipy>=1.8.0
```

### Step 4.2: Create requirements-portable.txt

```txt
# Digital Workshop - Portable Requirements
# For PORTABLE (self-contained) installation

# Core dependencies (minimal set for portable builds)
PySide6>=6.5.0
vtk>=9.2.0
numpy>=1.21.0
Pillow>=9.0.0
```

### Step 4.3: Create requirements-user.txt

```txt
# Digital Workshop - User Installation Requirements
# For USER installation

# Core dependencies
PySide6>=6.5.0
vtk>=9.2.0
numpy>=1.21.0
Pillow>=9.0.0

# Optional enhancements
matplotlib>=3.5.0
scipy>=1.8.0
```

### Step 4.4: Create requirements-system.txt

```txt
# Digital Workshop - System Installation Requirements
# For SYSTEM installation

# Core dependencies
PySide6>=6.5.0
vtk>=9.2.0
numpy>=1.21.0
Pillow>=9.0.0

# Optional enhancements for system installations
matplotlib>=3.5.0
scipy>=1.8.0
```

---

## PHASE 5: TESTING THE IMPLEMENTATION

### Step 5.1: Create Installation Type Test

Create `tests/test_installation_detection.py`:

```python
"""
Test installation type detection functionality.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.installation_detector import InstallationType, InstallationDetector

class TestInstallationDetector:
    """Test cases for installation detection."""
    
    def test_raw_installation_detection(self):
        """Test detection of raw development installation."""
        detector = InstallationDetector()
        
        # Mock raw installation conditions
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('os.path.exists') as mock_exists:
            
            mock_cwd.return_value = Path('/project/src')
            mock_exists.return_value = True
            
            result = detector.detect_installation_type()
            assert result == InstallationType.RAW
    
    def test_portable_installation_detection(self):
        """Test detection of portable installation."""
        detector = InstallationDetector()
        
        # Mock portable installation conditions
        with patch('sys.argv', ['DigitalWorkshop-Portable.exe']), \
             patch('os.path.exists') as mock_exists:
            
            mock_exists.return_value = False
            
            result = detector.detect_installation_type()
            assert result == InstallationType.PORTABLE
    
    def test_version_manager_functionality(self):
        """Test version management system."""
        from core.version_manager import VersionManager, get_display_version
        
        manager = VersionManager()
        
        # Test version info creation
        version_info = manager.get_version_info()
        assert version_info.base_version == "1.0.0"
        assert version_info.display_version in ["1.0.0-Raw", "1.0.0-Portable", "1.0.0"]
        assert version_info.logger_name in ["DigitalWorkshop-Raw", "DigitalWorkshop-Portable", "DigitalWorkshop"]
    
    def test_path_manager_functionality(self):
        """Test path management system."""
        from core.path_manager import PathManager, get_cache_directory
        
        manager = PathManager()
        
        # Test directory resolution
        cache_dir = manager.get_cache_directory()
        assert isinstance(cache_dir, Path)
        
        # Test global functions
        global_cache_dir = get_cache_directory()
        assert isinstance(global_cache_dir, Path)
```

### Step 5.2: Run Installation Type Tests

```bash
cd /path/to/digital-workshop
python -m pytest tests/test_installation_detection.py -v
```

### Step 5.3: Manual Testing Checklist

- [ ] **RAW Installation Test**: Run `python run.py` and verify:
  - [ ] Version shows as "1.0.0-Raw"
  - [ ] Logger names use "DigitalWorkshop-Raw"
  - [ ] Cache directory is `./cache`
  - [ ] No registry entries

- [ ] **PORTABLE Installation Test**: Run portable executable and verify:
  - [ ] Version shows as "1.0.0-Portable"
  - [ ] Logger names use "DigitalWorkshop-Portable"
  - [ ] Cache directory is `[exe_dir]/cache`
  - [ ] No registry entries

- [ ] **USER Installation Test**: Run user installer and verify:
  - [ ] Version shows as "1.0.0"
  - [ ] Logger names use "DigitalWorkshop"
  - [ ] Cache directory is `%LOCALAPPDATA%/DigitalWorkshop/cache`
  - [ ] Registry entries in HKEY_CURRENT_USER

- [ ] **SYSTEM Installation Test**: Run system installer and verify:
  - [ ] Version shows as "1.0.0"
  - [ ] Logger names use "DigitalWorkshop"
  - [ ] Cache directory uses appropriate system location
  - [ ] Registry entries in HKEY_LOCAL_MACHINE

---

## PHASE 6: UPDATE CHECKLIST

After implementing each phase, update `speckit.checklist.md`:

1. Mark completed items with `[x]`
2. Note any issues or dependencies in the Notes column
3. Update the overall completion percentage

### Checklist Update Example

```markdown
| V1.1.1 | `src/__init__.py` - Dynamic version | [x] | [x] | [x] | [x] | COMPLETED | Implemented using VersionManager |
| Q1.2.1 | `src/gui/theme/qt_material_service.py` | [x] | [x] | [x] | [x] | COMPLETED | Updated QSettings organization name |
```

---

## PHASE 7: FINAL VALIDATION

### Step 7.1: Code Quality Checks

Run code quality tools:

```bash
# Format code
black src/

# Lint code  
flake8 src/

# Type check
mypy src/

# Run tests
python -m pytest tests/ -v
```

### Step 7.2: Integration Testing

1. Test each installation type independently
2. Verify migration from old to new version works
3. Check that existing user data is preserved
4. Validate that all paths are correctly resolved

### Step 7.3: Performance Validation

- Verify no performance regression in path resolution
- Check memory usage remains stable
- Ensure startup time is not significantly affected

---

## TROUBLESHOOTING

### Common Issues and Solutions

1. **Import Errors**: Ensure `src/core/` modules are in Python path
2. **Path Resolution Issues**: Check InstallationDetector logic for your environment
3. **Registry Access**: Verify proper permissions for SYSTEM installation
4. **Testing Failures**: Mock appropriate environment variables for tests

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your application
```

---

## ROLLBACK PROCEDURE

If issues are encountered:

1. **Revert Core Changes**:
   - Restore original `src/__init__.py`
   - Restore original `src/core/logging_config.py`
   - Restore original theme files

2. **Remove New Files**:
   - Delete `src/core/installation_detector.py`
   - Delete `src/core/version_manager.py` 
   - Delete `src/core/path_manager.py`

3. **Update Imports**:
   - Remove new import statements
   - Restore original hardcoded values

4. **Test Rollback**:
   - Verify application starts correctly
   - Check all basic functionality works
   - Ensure no corruption of user data

---

*End of Implementation Guide*