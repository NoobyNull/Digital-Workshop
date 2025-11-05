"""
Unit tests for the ModuleManager class
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path

from src.installer.installer import Installer
from src.installer.managers.module_manager import ModuleManager


class TestModuleManager:
    """Test cases for ModuleManager class."""
    
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
    def module_manager(self, installer):
        """Create module manager instance."""
        return ModuleManager(installer)
    
    def test_module_manager_initialization(self, module_manager):
        """Test module manager initialization."""
        assert module_manager.installer is not None
    
    def test_install_module_success(self, module_manager, installer):
        """Test successful module installation."""
        # Create a mock module directory
        mock_module_path = installer.app_dir / "mock_module"
        mock_module_path.mkdir(parents=True, exist_ok=True)
        (mock_module_path / "test_file.txt").write_text("test content")
        
        # Install module
        result = module_manager.install_module("test_module", mock_module_path, "0.1.5")
        
        assert result is True
        assert (installer.modules_dir / "test_module").exists()
    
    def test_install_module_nonexistent_path(self, module_manager):
        """Test module installation with nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")
        result = module_manager.install_module("test_module", nonexistent_path, "0.1.5")
        
        assert result is False
    
    def test_verify_module_success(self, module_manager, installer):
        """Test successful module verification."""
        # Create a module directory
        module_dir = installer.modules_dir / "test_module"
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "test_file.txt").write_text("test content")
        
        result = module_manager.verify_module("test_module")
        
        assert result is True
    
    def test_verify_module_nonexistent(self, module_manager):
        """Test verification of nonexistent module."""
        result = module_manager.verify_module("nonexistent_module")
        
        assert result is False
    
    def test_verify_module_empty_directory(self, module_manager, installer):
        """Test verification of empty module directory."""
        # Create empty module directory
        module_dir = installer.modules_dir / "empty_module"
        module_dir.mkdir(parents=True, exist_ok=True)
        
        result = module_manager.verify_module("empty_module")
        
        assert result is False
    
    def test_remove_module_success(self, module_manager, installer):
        """Test successful module removal."""
        # Create a module directory
        module_dir = installer.modules_dir / "test_module"
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "test_file.txt").write_text("test content")
        
        result = module_manager.remove_module("test_module")
        
        assert result is True
        assert not module_dir.exists()
    
    def test_remove_module_nonexistent(self, module_manager):
        """Test removal of nonexistent module."""
        result = module_manager.remove_module("nonexistent_module")
        
        assert result is True  # Should return True even if module doesn't exist
    
    def test_get_module_info(self, module_manager, installer):
        """Test getting module information."""
        # Create manifest with module info
        manifest = {
            "modules": {
                "test_module": {
                    "installed": True,
                    "version": "0.1.5",
                    "install_date": "2025-11-04T00:00:00"
                }
            }
        }
        installer._save_manifest(manifest)
        
        info = module_manager.get_module_info("test_module")
        
        assert info is not None
        assert info['version'] == "0.1.5"
        assert info['installed'] is True
    
    def test_get_module_info_nonexistent(self, module_manager):
        """Test getting info for nonexistent module."""
        info = module_manager.get_module_info("nonexistent_module")
        
        assert info is None
    
    def test_list_modules(self, module_manager, installer):
        """Test listing installed modules."""
        # Create multiple module directories
        for module_name in ["core", "pyside6", "vtk"]:
            module_dir = installer.modules_dir / module_name
            module_dir.mkdir(parents=True, exist_ok=True)
            (module_dir / "test_file.txt").write_text("test content")
        
        modules = module_manager.list_modules()
        
        assert len(modules) == 3
        assert "core" in modules
        assert "pyside6" in modules
        assert "vtk" in modules
    
    def test_list_modules_empty(self, module_manager):
        """Test listing modules when none exist."""
        modules = module_manager.list_modules()
        
        assert modules == []

