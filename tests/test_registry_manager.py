"""
Unit tests for the RegistryManager class
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.managers.registry_manager import RegistryManager


class TestRegistryManager:
    """Test cases for RegistryManager class."""

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
    def registry_manager(self, installer):
        """Create registry manager instance."""
        return RegistryManager(installer)

    def test_registry_manager_initialization(self, registry_manager):
        """Test registry manager initialization."""
        assert registry_manager.installer is not None

    def test_register_module(self, registry_manager, installer):
        """Test module registration."""
        result = registry_manager.register_module("core", "0.1.5")

        assert result is True

        # Verify module is registered
        manifest = installer._load_manifest()
        assert "core" in manifest["modules"]
        assert manifest["modules"]["core"]["version"] == "0.1.5"

    def test_unregister_module(self, registry_manager, installer):
        """Test module unregistration."""
        # Register module first
        registry_manager.register_module("core", "0.1.5")

        # Unregister module
        result = registry_manager.unregister_module("core")

        assert result is True

        # Verify module is unregistered
        manifest = installer._load_manifest()
        assert "core" not in manifest["modules"]

    def test_unregister_nonexistent_module(self, registry_manager):
        """Test unregistration of nonexistent module."""
        result = registry_manager.unregister_module("nonexistent")

        assert result is True  # Should return True even if module doesn't exist

    def test_get_module_version(self, registry_manager, installer):
        """Test getting module version."""
        # Register module
        registry_manager.register_module("core", "0.1.5")

        version = registry_manager.get_module_version("core")

        assert version == "0.1.5"

    def test_get_module_version_nonexistent(self, registry_manager):
        """Test getting version of nonexistent module."""
        version = registry_manager.get_module_version("nonexistent")

        assert version is None

    def test_is_module_installed(self, registry_manager):
        """Test checking if module is installed."""
        # Register module
        registry_manager.register_module("core", "0.1.5")

        is_installed = registry_manager.is_module_installed("core")

        assert is_installed is True

    def test_is_module_installed_nonexistent(self, registry_manager):
        """Test checking if nonexistent module is installed."""
        is_installed = registry_manager.is_module_installed("nonexistent")

        assert is_installed is False

    def test_get_all_modules(self, registry_manager):
        """Test getting all modules."""
        # Register multiple modules
        registry_manager.register_module("core", "0.1.5")
        registry_manager.register_module("pyside6", "0.1.5")
        registry_manager.register_module("vtk", "0.1.5")

        modules = registry_manager.get_all_modules()

        assert len(modules) == 3
        assert "core" in modules
        assert "pyside6" in modules
        assert "vtk" in modules

    def test_get_installed_modules(self, registry_manager):
        """Test getting installed modules."""
        # Register multiple modules
        registry_manager.register_module("core", "0.1.5")
        registry_manager.register_module("pyside6", "0.1.5")

        installed = registry_manager.get_installed_modules()

        assert len(installed) == 2
        assert "core" in installed
        assert "pyside6" in installed

    def test_update_module_version(self, registry_manager):
        """Test updating module version."""
        # Register module
        registry_manager.register_module("core", "0.1.5")

        # Update version
        result = registry_manager.update_module_version("core", "0.1.6")

        assert result is True

        # Verify version is updated
        version = registry_manager.get_module_version("core")
        assert version == "0.1.6"

    def test_update_module_version_nonexistent(self, registry_manager):
        """Test updating version of nonexistent module."""
        result = registry_manager.update_module_version("nonexistent", "0.1.6")

        assert result is False

    def test_get_registry_info(self, registry_manager):
        """Test getting registry information."""
        # Register modules
        registry_manager.register_module("core", "0.1.5")
        registry_manager.register_module("pyside6", "0.1.5")

        info = registry_manager.get_registry_info()

        assert info["total_modules"] == 2
        assert info["installed_modules"] == 2
        assert "modules" in info
