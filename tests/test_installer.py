"""
Unit tests for the main Installer class
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.installer.installer import Installer


class TestInstaller:
    """Test cases for Installer class."""
    
    @pytest.fixture
    def temp_app_dir(self):
        """Create temporary app directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def installer(self, temp_app_dir, monkeypatch):
        """Create installer instance with temporary directory."""
        monkeypatch.setattr(Path, 'home', lambda: temp_app_dir)
        installer = Installer()
        installer.app_dir = temp_app_dir / "DigitalWorkshop"
        installer.modules_dir = installer.app_dir / "modules"
        installer.data_dir = installer.app_dir / "data"
        installer.config_dir = installer.app_dir / "config"
        installer.backup_dir = installer.app_dir / "backups"
        installer.logs_dir = installer.app_dir / "logs"
        installer.manifest_file = installer.app_dir / "manifest.json"
        installer.version_file = installer.app_dir / "version.txt"
        return installer
    
    def test_installer_initialization(self, installer):
        """Test installer initialization."""
        assert installer.app_dir is not None
        assert installer.modules_dir is not None
        assert installer.data_dir is not None
        assert installer.config_dir is not None
        assert installer.backup_dir is not None
        assert installer.logs_dir is not None
    
    def test_detect_installation_no_existing(self, installer):
        """Test detection when no installation exists."""
        result = installer.detect_installation()
        assert result is None
    
    def test_detect_installation_existing(self, installer):
        """Test detection of existing installation."""
        # Create version file
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.version_file.write_text("0.1.5")
        
        # Create manifest
        manifest = {
            "version": "0.1.5",
            "modules": {
                "core": {"installed": True, "version": "0.1.5"},
                "pyside6": {"installed": True, "version": "0.1.5"},
            }
        }
        installer.manifest_file.write_text(json.dumps(manifest))
        
        result = installer.detect_installation()
        
        assert result is not None
        assert result['exists'] is True
        assert result['version'] == "0.1.5"
        assert len(result['installed_modules']) == 2
    
    def test_select_mode_no_installation(self, installer):
        """Test mode selection with no existing installation."""
        mode = installer.select_mode(None)
        assert mode == "full_install"
    
    def test_select_mode_existing_installation(self, installer):
        """Test mode selection with existing installation."""
        existing = {
            'exists': True,
            'version': '0.1.5',
            'installed_modules': ['core', 'pyside6'],
        }
        mode = installer.select_mode(existing)
        assert mode == "patch"
    
    def test_create_directories(self, installer):
        """Test directory creation."""
        installer.create_directories()
        
        assert installer.app_dir.exists()
        assert installer.modules_dir.exists()
        assert installer.data_dir.exists()
        assert installer.config_dir.exists()
        assert installer.backup_dir.exists()
        assert installer.logs_dir.exists()
    
    def test_load_manifest_empty(self, installer):
        """Test loading manifest when it doesn't exist."""
        manifest = installer._load_manifest()
        assert manifest == {'modules': {}}
    
    def test_load_manifest_existing(self, installer):
        """Test loading existing manifest."""
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        
        test_manifest = {
            "version": "0.1.5",
            "modules": {
                "core": {"installed": True, "version": "0.1.5"},
            }
        }
        installer.manifest_file.write_text(json.dumps(test_manifest))
        
        manifest = installer._load_manifest()
        
        assert manifest['version'] == "0.1.5"
        assert 'core' in manifest['modules']
    
    def test_save_manifest(self, installer):
        """Test saving manifest."""
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        
        test_manifest = {
            "version": "0.1.5",
            "modules": {
                "core": {"installed": True, "version": "0.1.5"},
            }
        }
        
        installer._save_manifest(test_manifest)
        
        assert installer.manifest_file.exists()
        
        saved_manifest = json.loads(installer.manifest_file.read_text())
        assert saved_manifest['version'] == "0.1.5"
    
    def test_update_version_file(self, installer):
        """Test updating version file."""
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        
        installer._update_version_file("0.1.5")
        
        assert installer.version_file.exists()
        assert installer.version_file.read_text() == "0.1.5"
    
    def test_get_installation_info_no_installation(self, installer):
        """Test getting installation info when none exists."""
        info = installer.get_installation_info()
        
        assert info['installed'] is False
        assert info['version'] is None
        assert info['modules'] == []
    
    def test_get_installation_info_existing(self, installer):
        """Test getting installation info for existing installation."""
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.version_file.write_text("0.1.5")
        
        manifest = {
            "version": "0.1.5",
            "modules": {
                "core": {"installed": True, "version": "0.1.5"},
                "pyside6": {"installed": True, "version": "0.1.5"},
            }
        }
        installer.manifest_file.write_text(json.dumps(manifest))
        
        info = installer.get_installation_info()
        
        assert info['installed'] is True
        assert info['version'] == "0.1.5"
        assert len(info['modules']) == 2
    
    def test_modules_list(self, installer):
        """Test that MODULES list is correct."""
        assert len(installer.MODULES) == 5
        assert "core" in installer.MODULES
        assert "pyside6" in installer.MODULES
        assert "vtk" in installer.MODULES
        assert "opencv" in installer.MODULES
        assert "numpy" in installer.MODULES

