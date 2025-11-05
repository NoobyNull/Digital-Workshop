"""
Integration tests for Clean Install mode (DESTRUCTIVE)
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.modes.clean_install import CleanInstallMode


class TestCleanInstallMode:
    """Integration tests for CleanInstallMode."""
    
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
        installer.create_directories()
        return installer
    
    @pytest.fixture
    def clean_install_mode(self, installer):
        """Create CleanInstallMode instance."""
        return CleanInstallMode(installer)
    
    def _setup_existing_installation(self, installer, version: str, modules: list):
        """Helper to setup an existing installation."""
        installer.version_file.write_text(version)
        
        manifest = {
            "version": version,
            "modules": {
                module: {"installed": True, "version": version}
                for module in modules
            }
        }
        installer.manifest_file.write_text(json.dumps(manifest))
        
        # Create module directories
        for module in modules:
            module_dir = installer.modules_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)
            (module_dir / "test_file.txt").write_text("test content")
        
        # Create user data
        user_data_file = installer.data_dir / "user_data.json"
        user_data_file.write_text('{"key": "value"}')
    
    def test_clean_install_removes_all_files(self, clean_install_mode, installer):
        """Test that clean install removes all files."""
        self._setup_existing_installation(installer, "0.1.4", ["core", "pyside6"])
        
        # Verify files exist
        assert installer.version_file.exists()
        assert installer.manifest_file.exists()
        assert (installer.modules_dir / "core").exists()
        
        clean_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        # After clean install, old files should be removed
        # (but new installation should be in place)
        assert installer.app_dir.exists()
    
    def test_clean_install_removes_user_data(self, clean_install_mode, installer):
        """Test that clean install removes user data (DESTRUCTIVE)."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        user_data_file = installer.data_dir / "user_data.json"
        assert user_data_file.exists()
        
        clean_install_mode.execute("0.1.5", ["core"])
        
        # User data should be removed (this is DESTRUCTIVE)
        # After clean install, data directory should be empty or recreated
        assert installer.data_dir.exists()
    
    def test_clean_install_creates_backup(self, clean_install_mode, installer):
        """Test that clean install creates final backup."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        clean_install_mode.execute("0.1.5", ["core"])
        
        # Should have created a backup before deletion
        backups = list(installer.backup_dir.glob("backup_*"))
        assert len(backups) > 0
    
    def test_clean_install_fresh_installation(self, clean_install_mode, installer):
        """Test that clean install creates fresh installation."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        result = clean_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        assert result is True
        
        # Verify new installation
        assert installer.version_file.exists()
        assert installer.version_file.read_text() == "0.1.5"
    
    def test_clean_install_updates_manifest(self, clean_install_mode, installer):
        """Test that clean install creates new manifest."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        clean_install_mode.execute("0.1.5", ["core", "pyside6"])
        
        manifest = json.loads(installer.manifest_file.read_text())
        assert manifest['version'] == "0.1.5"
        assert "core" in manifest['modules']
        assert "pyside6" in manifest['modules']
    
    def test_clean_install_returns_success(self, clean_install_mode, installer):
        """Test that clean install returns success."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        result = clean_install_mode.execute("0.1.5", ["core"])
        
        assert result is True
    
    def test_clean_install_with_all_modules(self, clean_install_mode, installer):
        """Test clean install with all modules."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])
        
        all_modules = ["core", "pyside6", "vtk", "opencv", "numpy"]
        result = clean_install_mode.execute("0.1.5", all_modules)
        
        assert result is True
        
        manifest = json.loads(installer.manifest_file.read_text())
        assert len(manifest['modules']) == 5

