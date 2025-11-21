"""
Unit tests for the BackupManager class
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.installer.installer import Installer
from src.installer.managers.backup_manager import BackupManager


class TestBackupManager:
    """Test cases for BackupManager class."""

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
    def backup_manager(self, installer):
        """Create backup manager instance."""
        return BackupManager(installer)

    def test_backup_manager_initialization(self, backup_manager):
        """Test backup manager initialization."""
        assert backup_manager.installer is not None
        assert backup_manager.max_backups == 5

    def test_create_backup_success(self, backup_manager, installer):
        """Test successful backup creation."""
        # Create version file
        installer.version_file.write_text("0.1.5")

        # Create manifest
        manifest = {"version": "0.1.5", "modules": {}}
        installer._save_manifest(manifest)

        backup_dir = backup_manager.create_backup("test_backup")

        assert backup_dir is not None
        assert backup_dir.exists()
        assert (backup_dir / "manifest.json").exists()
        assert (backup_dir / "version.txt").exists()
        assert (backup_dir / "backup_metadata.json").exists()

    def test_create_backup_auto_name(self, backup_manager, installer):
        """Test backup creation with auto-generated name."""
        installer.version_file.write_text("0.1.5")
        installer._save_manifest({"version": "0.1.5", "modules": {}})

        backup_dir = backup_manager.create_backup()

        assert backup_dir is not None
        assert backup_dir.exists()
        assert "backup_" in backup_dir.name

    def test_verify_backup_success(self, backup_manager, installer):
        """Test successful backup verification."""
        # Create a backup
        installer.version_file.write_text("0.1.5")
        installer._save_manifest({"version": "0.1.5", "modules": {}})

        backup_dir = backup_manager.create_backup("test_backup")

        # Verify backup
        result = backup_manager.verify_backup(backup_dir)

        assert result is True

    def test_verify_backup_nonexistent(self, backup_manager):
        """Test verification of nonexistent backup."""
        nonexistent_backup = Path("/nonexistent/backup")
        result = backup_manager.verify_backup(nonexistent_backup)

        assert result is False

    def test_restore_backup_success(self, backup_manager, installer):
        """Test successful backup restoration."""
        # Create initial version
        installer.version_file.write_text("0.1.5")
        manifest = {"version": "0.1.5", "modules": {"core": {"installed": True}}}
        installer._save_manifest(manifest)

        # Create backup
        backup_dir = backup_manager.create_backup("test_backup")

        # Modify version
        installer.version_file.write_text("0.1.6")

        # Restore backup
        result = backup_manager.restore_backup(backup_dir)

        assert result is True
        assert installer.version_file.read_text() == "0.1.5"

    def test_restore_backup_nonexistent(self, backup_manager):
        """Test restoration of nonexistent backup."""
        nonexistent_backup = Path("/nonexistent/backup")
        result = backup_manager.restore_backup(nonexistent_backup)

        assert result is False

    def test_list_backups_empty(self, backup_manager):
        """Test listing backups when none exist."""
        backups = backup_manager.list_backups()

        assert backups == []

    def test_list_backups_multiple(self, backup_manager, installer):
        """Test listing multiple backups."""
        installer.version_file.write_text("0.1.5")
        installer._save_manifest({"version": "0.1.5", "modules": {}})

        # Create multiple backups
        for i in range(3):
            backup_manager.create_backup(f"backup_{i}")

        backups = backup_manager.list_backups()

        assert len(backups) == 3

    def test_delete_backup_success(self, backup_manager, installer):
        """Test successful backup deletion."""
        installer.version_file.write_text("0.1.5")
        installer._save_manifest({"version": "0.1.5", "modules": {}})

        backup_dir = backup_manager.create_backup("test_backup")

        result = backup_manager.delete_backup(backup_dir)

        assert result is True
        assert not backup_dir.exists()

    def test_delete_backup_nonexistent(self, backup_manager):
        """Test deletion of nonexistent backup."""
        nonexistent_backup = Path("/nonexistent/backup")
        result = backup_manager.delete_backup(nonexistent_backup)

        assert result is True  # Should return True even if backup doesn't exist

    def test_cleanup_old_backups(self, backup_manager, installer):
        """Test cleanup of old backups."""
        installer.version_file.write_text("0.1.5")
        installer._save_manifest({"version": "0.1.5", "modules": {}})

        # Create more backups than max_backups
        for i in range(7):
            backup_manager.create_backup(f"backup_{i}")

        # Cleanup should keep only max_backups
        backups = backup_manager.list_backups()

        assert len(backups) <= backup_manager.max_backups
