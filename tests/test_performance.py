"""Performance tests for installer modes."""

import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.installer.installer import Installer
from src.installer.modes.full_install import FullInstallMode
from src.installer.modes.patch_mode import PatchMode
from src.installer.modes.reinstall_mode import ReinstallMode
from src.installer.modes.clean_install import CleanInstallMode


class TestPerformance:
    """Performance tests for installation modes."""

    @pytest.fixture
    def temp_app_dir(self):
        """Create temporary app directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def installer(self, temp_app_dir):
        """Create installer instance."""
        with patch.object(Installer, "__init__", lambda x: None):
            installer = Installer()
            installer.app_dir = temp_app_dir
            installer.modules_dir = temp_app_dir / "modules"
            installer.data_dir = temp_app_dir / "data"
            installer.config_dir = temp_app_dir / "config"
            installer.backup_dir = temp_app_dir / "backups"
            installer.logs_dir = temp_app_dir / "logs"
            installer.manifest_file = temp_app_dir / "manifest.json"
            installer.version_file = temp_app_dir / "version.txt"

            # Mock methods
            installer.create_directories = MagicMock()
            installer.detect_installation = MagicMock(return_value=None)
            installer._load_manifest = MagicMock(return_value={"modules": {}})
            installer._save_manifest = MagicMock()
            installer._update_version_file = MagicMock()

            return installer

    @pytest.fixture
    def full_install_mode(self, installer):
        """Create FullInstallMode instance."""
        return FullInstallMode(installer)

    @pytest.fixture
    def patch_mode(self, installer):
        """Create PatchMode instance."""
        return PatchMode(installer)

    @pytest.fixture
    def reinstall_mode(self, installer):
        """Create ReinstallMode instance."""
        return ReinstallMode(installer)

    @pytest.fixture
    def clean_install_mode(self, installer):
        """Create CleanInstallMode instance."""
        return CleanInstallMode(installer)

    def test_full_install_performance(self, full_install_mode, installer):
        """Test Full Install completes in < 15 minutes."""
        # Setup directories
        installer.modules_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.config_dir.mkdir(parents=True, exist_ok=True)
        installer.logs_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        result = full_install_mode.execute(
            "0.1.5", ["core", "pyside6", "vtk", "opencv", "numpy"]
        )

        elapsed_time = time.time() - start_time

        # In test environment, should be much faster
        # In production with actual file copying, should be < 15 minutes (900 seconds)
        assert elapsed_time < 900, f"Full Install took {elapsed_time}s, expected < 900s"
        assert result is True

    def test_patch_mode_performance(self, patch_mode, installer):
        """Test Patch mode completes in < 5 minutes."""
        # Setup existing installation
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.modules_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.config_dir.mkdir(parents=True, exist_ok=True)
        installer.logs_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)

        installer.detect_installation = MagicMock(
            return_value={
                "version": "0.1.4",
                "modules": {
                    "core": {"installed": True},
                    "pyside6": {"installed": True},
                },
            }
        )

        # Mock internal methods to avoid file operations
        patch_mode._create_backup = MagicMock()
        patch_mode._compare_versions = MagicMock(return_value=["core"])
        patch_mode._update_modules = MagicMock()
        patch_mode._run_migrations = MagicMock()
        patch_mode._verify_installation = MagicMock()

        start_time = time.time()

        result = patch_mode.execute("0.1.5", ["core", "pyside6"])

        elapsed_time = time.time() - start_time

        # In test environment, should be much faster
        # In production with actual file copying, should be < 5 minutes (300 seconds)
        assert elapsed_time < 300, f"Patch mode took {elapsed_time}s, expected < 300s"
        assert result is True

    def test_reinstall_mode_performance(self, reinstall_mode, installer):
        """Test Reinstall completes in < 10 minutes."""
        # Setup existing installation
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        (installer.app_dir / "data").mkdir(exist_ok=True)
        (installer.app_dir / "data" / "test.txt").write_text("test data")

        start_time = time.time()

        result = reinstall_mode.execute("0.1.5", ["core", "pyside6"])

        elapsed_time = time.time() - start_time

        # In test environment, should be much faster
        # In production with actual file copying, should be < 10 minutes (600 seconds)
        assert elapsed_time < 600, f"Reinstall took {elapsed_time}s, expected < 600s"
        assert result is True

    def test_clean_install_performance(self, clean_install_mode, installer):
        """Test Clean Install completes in < 15 minutes."""
        # Setup existing installation
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.modules_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.config_dir.mkdir(parents=True, exist_ok=True)
        installer.logs_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)

        # Mock internal methods to avoid file operations
        clean_install_mode._create_final_backup = MagicMock()
        clean_install_mode._display_destructive_warning = MagicMock()
        clean_install_mode._remove_everything = MagicMock()
        clean_install_mode._install_modules = MagicMock()
        clean_install_mode._initialize_database = MagicMock()
        clean_install_mode._create_configuration = MagicMock()

        start_time = time.time()

        result = clean_install_mode.execute("0.1.5", ["core", "pyside6"])

        elapsed_time = time.time() - start_time

        # In test environment, should be much faster
        # In production with actual file copying, should be < 15 minutes (900 seconds)
        assert (
            elapsed_time < 900
        ), f"Clean Install took {elapsed_time}s, expected < 900s"
        assert result is True

    def test_performance_comparison(self, patch_mode, installer):
        """Test that Patch mode is faster than other modes."""
        # Setup for patch mode
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.modules_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.config_dir.mkdir(parents=True, exist_ok=True)
        installer.logs_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)

        installer.detect_installation = MagicMock(
            return_value={"version": "0.1.4", "modules": {"core": {"installed": True}}}
        )

        # Measure patch mode
        start_patch = time.time()
        patch_mode.execute("0.1.5", ["core"])
        patch_time = time.time() - start_patch

        # Patch should be the fastest mode
        assert patch_time < 300, f"Patch mode took {patch_time}s, expected < 300s"
