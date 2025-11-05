"""
Integration tests for Full Install mode
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.modes.full_install import FullInstallMode


class TestFullInstallMode:
    """Integration tests for FullInstallMode."""
    
    @pytest.fixture
    def temp_app_dir(self):
        """Create temporary app directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def installer(self, temp_app_dir):
        """Create installer instance with temporary directory."""
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
    
    @pytest.fixture
    def full_install_mode(self, installer):
        """Create FullInstallMode instance."""
        return FullInstallMode(installer)
    
    def test_full_install_creates_directories(self, full_install_mode, installer):
        """Test that full install creates all required directories."""
        full_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        assert installer.app_dir.exists()
        assert installer.modules_dir.exists()
        assert installer.data_dir.exists()
        assert installer.config_dir.exists()
        assert installer.logs_dir.exists()
    
    def test_full_install_creates_manifest(self, full_install_mode, installer):
        """Test that full install creates manifest file."""
        full_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        assert installer.manifest_file.exists()
        
        manifest = json.loads(installer.manifest_file.read_text())
        assert manifest['version'] == "0.1.5"
        assert 'modules' in manifest
    
    def test_full_install_creates_version_file(self, full_install_mode, installer):
        """Test that full install creates version file."""
        full_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        assert installer.version_file.exists()
        assert installer.version_file.read_text() == "0.1.5"
    
    def test_full_install_registers_modules(self, full_install_mode, installer):
        """Test that full install registers all modules."""
        modules = ["core", "pyside6", "vtk"]
        full_install_mode.execute("0.1.5", modules)
        
        manifest = json.loads(installer.manifest_file.read_text())
        
        for module in modules:
            assert module in manifest['modules']
            assert manifest['modules'][module]['version'] == "0.1.5"
    
    def test_full_install_initializes_database(self, full_install_mode, installer):
        """Test that full install initializes database."""
        full_install_mode.execute("0.1.5", ["core"])
        
        db_path = installer.data_dir / "3dmm.db"
        assert db_path.exists()
    
    def test_full_install_returns_success(self, full_install_mode):
        """Test that full install returns success."""
        result = full_install_mode.execute("0.1.5", ["core"])
        
        assert result is True
    
    def test_full_install_with_all_modules(self, full_install_mode, installer):
        """Test full install with all 5 modules."""
        all_modules = ["core", "pyside6", "vtk", "opencv", "numpy"]
        result = full_install_mode.execute("0.1.5", all_modules)
        
        assert result is True
        
        manifest = json.loads(installer.manifest_file.read_text())
        assert len(manifest['modules']) == 5
    
    def test_full_install_empty_modules_list(self, full_install_mode):
        """Test full install with empty modules list."""
        result = full_install_mode.execute("0.1.5", [])
        
        # Should still succeed but with no modules
        assert result is True

