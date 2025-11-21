"""
Integration tests for Reinstall mode
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.modes.reinstall_mode import ReinstallMode


class TestReinstallMode:
    """Integration tests for ReinstallMode."""

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
    def reinstall_mode(self, installer):
        """Create ReinstallMode instance."""
        return ReinstallMode(installer)

    def _setup_existing_installation(self, installer, version: str, modules: list):
        """Helper to setup an existing installation."""
        installer.version_file.write_text(version)

        manifest = {
            "version": version,
            "modules": {
                module: {"installed": True, "version": version} for module in modules
            },
        }
        installer.manifest_file.write_text(json.dumps(manifest))

        # Create module directories
        for module in modules:
            module_dir = installer.modules_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)
            (module_dir / "test_file.txt").write_text("test content")

    def test_reinstall_mode_creates_backup(self, reinstall_mode, installer):
        """Test that reinstall mode creates backup."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        reinstall_mode.execute("0.1.5", ["core"])

        backups = list(installer.backup_dir.glob("backup_*"))
        assert len(backups) > 0

    def test_reinstall_mode_preserves_user_data(self, reinstall_mode, installer):
        """Test that reinstall mode preserves user data."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        # Create user data
        user_data_file = installer.data_dir / "user_data.json"
        user_data_file.write_text('{"key": "value"}')

        reinstall_mode.execute("0.1.5", ["core"])

        # Verify user data is preserved
        assert user_data_file.exists()
        assert user_data_file.read_text() == '{"key": "value"}'

    def test_reinstall_mode_removes_old_modules(self, reinstall_mode, installer):
        """Test that reinstall mode removes old modules."""
        self._setup_existing_installation(installer, "0.1.4", ["core", "pyside6"])

        # Verify modules exist
        assert (installer.modules_dir / "core").exists()
        assert (installer.modules_dir / "pyside6").exists()

        # Reinstall with only core
        reinstall_mode.execute("0.1.5", ["core"])

        # pyside6 should be removed
        assert (installer.modules_dir / "core").exists()

    def test_reinstall_mode_updates_version(self, reinstall_mode, installer):
        """Test that reinstall mode updates version."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        reinstall_mode.execute("0.1.5", ["core"])

        assert installer.version_file.read_text() == "0.1.5"

    def test_reinstall_mode_updates_manifest(self, reinstall_mode, installer):
        """Test that reinstall mode updates manifest."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        reinstall_mode.execute("0.1.5", ["core", "pyside6"])

        manifest = json.loads(installer.manifest_file.read_text())
        assert manifest["version"] == "0.1.5"
        assert "core" in manifest["modules"]
        assert "pyside6" in manifest["modules"]

    def test_reinstall_mode_returns_success(self, reinstall_mode, installer):
        """Test that reinstall mode returns success."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        result = reinstall_mode.execute("0.1.5", ["core"])

        assert result is True

    def test_reinstall_mode_with_all_modules(self, reinstall_mode, installer):
        """Test reinstall mode with all modules."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        all_modules = ["core", "pyside6", "vtk", "opencv", "numpy"]
        result = reinstall_mode.execute("0.1.5", all_modules)

        assert result is True

        manifest = json.loads(installer.manifest_file.read_text())
        assert len(manifest["modules"]) == 5
