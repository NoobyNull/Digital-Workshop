"""
Integration tests for Patch mode
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.modes.patch_mode import PatchMode


class TestPatchMode:
    """Integration tests for PatchMode."""

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
    def patch_mode(self, installer):
        """Create PatchMode instance."""
        return PatchMode(installer)

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

    def test_patch_mode_detects_existing_installation(self, patch_mode, installer):
        """Test that patch mode detects existing installation."""
        self._setup_existing_installation(installer, "0.1.4", ["core", "pyside6"])

        existing = patch_mode.installer.detect_installation()

        assert existing is not None
        assert existing["version"] == "0.1.4"

    def test_patch_mode_creates_backup(self, patch_mode, installer):
        """Test that patch mode creates backup before patching."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        patch_mode.execute("0.1.5", ["core"])

        backups = list(installer.backup_dir.glob("backup_*"))
        assert len(backups) > 0

    def test_patch_mode_updates_version(self, patch_mode, installer):
        """Test that patch mode updates version."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        patch_mode.execute("0.1.5", ["core"])

        assert installer.version_file.read_text() == "0.1.5"

    def test_patch_mode_updates_manifest(self, patch_mode, installer):
        """Test that patch mode updates manifest."""
        self._setup_existing_installation(installer, "0.1.4", ["core", "pyside6"])

        patch_mode.execute("0.1.5", ["core", "pyside6"])

        manifest = json.loads(installer.manifest_file.read_text())
        assert manifest["version"] == "0.1.5"

    def test_patch_mode_preserves_data(self, patch_mode, installer):
        """Test that patch mode preserves user data."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        # Create user data
        user_data_file = installer.data_dir / "user_data.json"
        user_data_file.write_text('{"key": "value"}')

        patch_mode.execute("0.1.5", ["core"])

        # Verify user data is preserved
        assert user_data_file.exists()
        assert user_data_file.read_text() == '{"key": "value"}'

    def test_patch_mode_returns_success(self, patch_mode, installer):
        """Test that patch mode returns success."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        result = patch_mode.execute("0.1.5", ["core"])

        assert result is True

    def test_patch_mode_with_multiple_modules(self, patch_mode, installer):
        """Test patch mode with multiple modules."""
        self._setup_existing_installation(
            installer, "0.1.4", ["core", "pyside6", "vtk"]
        )

        result = patch_mode.execute("0.1.5", ["core", "pyside6", "vtk"])

        assert result is True

        manifest = json.loads(installer.manifest_file.read_text())
        assert len(manifest["modules"]) == 3

    def test_patch_mode_adds_new_modules(self, patch_mode, installer):
        """Test patch mode adding new modules."""
        self._setup_existing_installation(installer, "0.1.4", ["core"])

        patch_mode.execute("0.1.5", ["core", "pyside6"])

        manifest = json.loads(installer.manifest_file.read_text())
        assert "pyside6" in manifest["modules"]
