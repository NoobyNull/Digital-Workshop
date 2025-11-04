# Installer Implementation Guide

**Date**: 2025-11-04  
**Status**: Ready to implement  
**Scope**: Complete installer with 4 modes and per-module compilation

---

## 🎯 Overview

The installer is a Python application that:
- ✅ Detects existing installations
- ✅ Selects appropriate installation mode
- ✅ Manages per-module installation
- ✅ Handles backups and rollbacks
- ✅ Verifies integrity with checksums

---

## 📁 Installer Structure

```
src/installer/
├── __init__.py
├── installer.py              ← Main installer class
├── modes/
│   ├── __init__.py
│   ├── full_install.py       ← Full install mode
│   ├── patch_mode.py         ← Patch mode
│   ├── reinstall_mode.py     ← Reinstall mode
│   └── clean_install.py      ← Clean install mode
├── managers/
│   ├── __init__.py
│   ├── module_manager.py     ← Module management
│   ├── backup_manager.py     ← Backup/restore
│   ├── registry_manager.py   ← Installation registry
│   └── migration_manager.py  ← Database migrations
└── utils/
    ├── __init__.py
    ├── checksum_utils.py     ← Checksum verification
    ├── path_utils.py         ← Path management
    └── logger.py             ← Logging
```

---

## 💻 Core Installer Class

**File**: `src/installer/installer.py`

```python
import os
import sys
import json
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class Installer:
    """Main installer class managing all installation modes"""
    
    def __init__(self):
        self.app_name = "Digital Workshop"
        self.app_dir = Path.home() / "AppData" / "Local" / "DigitalWorkshop"
        self.modules_dir = self.app_dir / "modules"
        self.data_dir = self.app_dir / "data"
        self.config_dir = self.app_dir / "config"
        self.backup_dir = self.app_dir / "backups"
        self.manifest_file = self.app_dir / "manifest.json"
        self.version_file = self.app_dir / "version.txt"
        
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        log_dir = self.app_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(__name__)
        handler = logging.FileHandler(
            log_dir / f"installer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    def detect_installation(self) -> Optional[Dict]:
        """Detect existing installation"""
        if not self.version_file.exists():
            return None
        
        try:
            version = self.version_file.read_text().strip()
            manifest = self._load_manifest()
            
            return {
                'exists': True,
                'version': version,
                'manifest': manifest,
                'path': str(self.app_dir),
                'installed_modules': list(manifest.get('modules', {}).keys())
            }
        except Exception as e:
            self.logger.error(f"Error detecting installation: {e}")
            return None
    
    def select_mode(self, existing_install: Optional[Dict]) -> str:
        """Select installation mode"""
        if not existing_install:
            return "full_install"
        
        # Existing installation found
        # User selects from: patch, reinstall, clean
        # For now, return patch as default
        return "patch"
    
    def install(self, mode: str, modules: List[str] = None):
        """Execute installation"""
        self.logger.info(f"Starting {mode} installation")
        
        if mode == "full_install":
            from .modes.full_install import FullInstallMode
            installer = FullInstallMode(self)
            installer.execute(modules or ["core", "pyside6", "vtk", "opencv", "numpy"])
        
        elif mode == "patch":
            from .modes.patch_mode import PatchMode
            installer = PatchMode(self)
            installer.execute()
        
        elif mode == "reinstall":
            from .modes.reinstall_mode import ReinstallMode
            installer = ReinstallMode(self)
            installer.execute()
        
        elif mode == "clean_install":
            from .modes.clean_install import CleanInstallMode
            installer = CleanInstallMode(self)
            installer.execute()
        
        else:
            raise ValueError(f"Unknown installation mode: {mode}")
    
    def _load_manifest(self) -> Dict:
        """Load installation manifest"""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                return json.load(f)
        return {'modules': {}}
    
    def _save_manifest(self, manifest: Dict):
        """Save installation manifest"""
        self.app_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def verify_checksum(self, file_path: Path, expected: str) -> bool:
        """Verify file checksum"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        actual = sha256_hash.hexdigest()
        return actual == expected.replace("sha256:", "")
```

---

## 🔧 Installation Modes

### Full Install Mode

**File**: `src/installer/modes/full_install.py`

```python
class FullInstallMode:
    """Fresh installation with all modules"""
    
    def __init__(self, installer):
        self.installer = installer
        self.logger = installer.logger
    
    def execute(self, modules: List[str]):
        """Execute full installation"""
        try:
            self.logger.info("Starting full installation")
            
            # Create directory structure
            self._create_directories()
            
            # Install modules
            self._install_modules(modules)
            
            # Initialize database
            self._initialize_database()
            
            # Create configuration
            self._create_configuration()
            
            # Create shortcuts
            self._create_shortcuts()
            
            # Register application
            self._register_application()
            
            # Update manifest
            self._update_manifest(modules)
            
            self.logger.info("Full installation completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Full installation failed: {e}")
            return False
    
    def _create_directories(self):
        """Create application directory structure"""
        dirs = [
            self.installer.app_dir,
            self.installer.modules_dir,
            self.installer.data_dir,
            self.installer.config_dir,
            self.installer.backup_dir,
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {dir_path}")
    
    def _install_modules(self, modules: List[str]):
        """Install specified modules"""
        for module in modules:
            self.logger.info(f"Installing module: {module}")
            # Download and extract module
            # Verify checksum
            # Register module
    
    def _initialize_database(self):
        """Initialize SQLite database"""
        self.logger.info("Initializing database")
        # Create database
        # Create tables
        # Set schema version
    
    def _create_configuration(self):
        """Create default configuration"""
        self.logger.info("Creating configuration")
        # Create config.json
        # Set defaults
    
    def _create_shortcuts(self):
        """Create desktop and start menu shortcuts"""
        self.logger.info("Creating shortcuts")
        # Create desktop shortcut
        # Create start menu shortcut
    
    def _register_application(self):
        """Register application in Windows"""
        self.logger.info("Registering application")
        # Add to registry
        # Add to Programs & Features
    
    def _update_manifest(self, modules: List[str]):
        """Update installation manifest"""
        manifest = {
            'version': '0.1.5',
            'mode': 'full_install',
            'installed_date': datetime.now().isoformat(),
            'modules': {m: {'installed': True} for m in modules}
        }
        self.installer._save_manifest(manifest)
```

### Patch Mode

**File**: `src/installer/modes/patch_mode.py`

```python
class PatchMode:
    """Update existing installation"""
    
    def __init__(self, installer):
        self.installer = installer
        self.logger = installer.logger
    
    def execute(self):
        """Execute patch installation"""
        try:
            self.logger.info("Starting patch installation")
            
            # Detect existing installation
            existing = self.installer.detect_installation()
            
            # Create backup
            self._create_backup(existing)
            
            # Compare versions
            changed_modules = self._compare_versions(existing)
            
            # Update changed modules
            self._update_modules(changed_modules)
            
            # Run migrations
            self._run_migrations()
            
            # Verify installation
            self._verify_installation()
            
            # Clean up backup
            self._cleanup_backup()
            
            self.logger.info("Patch installation completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Patch installation failed: {e}")
            self._rollback_backup()
            return False
    
    def _create_backup(self, existing: Dict):
        """Create backup of current installation"""
        self.logger.info("Creating backup")
        # Backup modules
        # Backup database
        # Backup configuration
    
    def _compare_versions(self, existing: Dict) -> List[str]:
        """Compare versions and identify changed modules"""
        self.logger.info("Comparing versions")
        # Get current version
        # Get new version
        # Identify changed modules
        return []
    
    def _update_modules(self, modules: List[str]):
        """Update specified modules"""
        for module in modules:
            self.logger.info(f"Updating module: {module}")
            # Download new version
            # Verify checksum
            # Replace old module
    
    def _run_migrations(self):
        """Run database migrations"""
        self.logger.info("Running migrations")
        # Check for pending migrations
        # Apply migrations
        # Update schema version
    
    def _verify_installation(self):
        """Verify installation integrity"""
        self.logger.info("Verifying installation")
        # Check all modules present
        # Verify checksums
        # Test application launch
    
    def _cleanup_backup(self):
        """Remove backup if successful"""
        self.logger.info("Cleaning up backup")
    
    def _rollback_backup(self):
        """Restore from backup on failure"""
        self.logger.info("Rolling back to backup")
```

---

## 📊 Module Manager

**File**: `src/installer/managers/module_manager.py`

```python
class ModuleManager:
    """Manage module installation and verification"""
    
    def __init__(self, installer):
        self.installer = installer
        self.logger = installer.logger
    
    def install_module(self, module_name: str, module_path: Path):
        """Install a module"""
        self.logger.info(f"Installing module: {module_name}")
        
        # Extract module
        # Verify checksum
        # Register module
        # Update manifest
    
    def verify_module(self, module_name: str) -> bool:
        """Verify module integrity"""
        self.logger.info(f"Verifying module: {module_name}")
        
        # Check module exists
        # Verify checksum
        # Check dependencies
        
        return True
    
    def get_installed_modules(self) -> List[str]:
        """Get list of installed modules"""
        manifest = self.installer._load_manifest()
        return list(manifest.get('modules', {}).keys())
    
    def remove_module(self, module_name: str):
        """Remove a module"""
        self.logger.info(f"Removing module: {module_name}")
        
        # Delete module files
        # Update manifest
```

---

## ✅ Checklist

- [ ] Create installer.py
- [ ] Create full_install.py
- [ ] Create patch_mode.py
- [ ] Create reinstall_mode.py
- [ ] Create clean_install.py
- [ ] Create module_manager.py
- [ ] Create backup_manager.py
- [ ] Create registry_manager.py
- [ ] Create migration_manager.py
- [ ] Create checksum_utils.py
- [ ] Create path_utils.py
- [ ] Create logger.py
- [ ] Test all modes
- [ ] Test mode transitions
- [ ] Test backup/restore
- [ ] Test rollback scenarios

---

**Status**: ✅ IMPLEMENTATION GUIDE COMPLETE

**Next**: Build system integration

