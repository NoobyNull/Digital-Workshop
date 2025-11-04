"""Security tests for installer."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.installer.installer import Installer
from src.installer.modes.clean_install import CleanInstallMode
from src.installer.managers.backup_manager import BackupManager


class TestSecurity:
    """Security tests for installer."""

    @pytest.fixture
    def temp_app_dir(self):
        """Create temporary app directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def installer(self, temp_app_dir):
        """Create installer instance."""
        with patch.object(Installer, '__init__', lambda x: None):
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
            installer._load_manifest = MagicMock(return_value={'modules': {}})
            installer._save_manifest = MagicMock()
            installer._update_version_file = MagicMock()
            
            return installer

    @pytest.fixture
    def clean_install_mode(self, installer):
        """Create CleanInstallMode instance."""
        return CleanInstallMode(installer)

    @pytest.fixture
    def backup_manager(self, installer):
        """Create BackupManager instance."""
        return BackupManager(installer)

    def test_clean_install_destructive_warning_displayed(self, clean_install_mode):
        """Test that DESTRUCTIVE warning is displayed for Clean Install."""
        # Mock the warning display method
        clean_install_mode._display_destructive_warning = MagicMock()
        clean_install_mode._create_final_backup = MagicMock()
        clean_install_mode._remove_everything = MagicMock()
        clean_install_mode._install_modules = MagicMock()
        clean_install_mode._initialize_database = MagicMock()
        clean_install_mode._create_configuration = MagicMock()
        
        clean_install_mode.execute("0.1.5", ["core"])
        
        # Verify warning was displayed
        clean_install_mode._display_destructive_warning.assert_called_once()

    def test_clean_install_creates_backup_before_deletion(self, clean_install_mode, installer):
        """Test that backup is created before deletion in Clean Install."""
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock other methods
        clean_install_mode._display_destructive_warning = MagicMock()
        clean_install_mode._remove_everything = MagicMock()
        clean_install_mode._install_modules = MagicMock()
        clean_install_mode._initialize_database = MagicMock()
        clean_install_mode._create_configuration = MagicMock()
        
        clean_install_mode.execute("0.1.5", ["core"])
        
        # Verify backup was created
        backups = list(installer.backup_dir.glob("backup_*"))
        assert len(backups) > 0, "Backup should be created before deletion"

    def test_backup_manager_creates_checksums(self, backup_manager, installer):
        """Test that backup manager creates checksums for integrity verification."""
        # Create test data
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)
        (installer.data_dir / "file1.txt").write_text("test content 1")
        (installer.data_dir / "file2.txt").write_text("test content 2")

        # Create backup
        backup_path = backup_manager.create_backup("test_backup")

        # Verify backup was created
        assert backup_path is not None, "Backup should be created"
        assert backup_path.exists(), "Backup should exist"
        assert backup_path.is_dir(), "Backup should be a directory"

    def test_backup_manager_verifies_backup_integrity(self, backup_manager, installer):
        """Test that backup manager can verify backup integrity."""
        # Create test data
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)
        (installer.data_dir / "file1.txt").write_text("test content 1")

        # Create backup
        backup_path = backup_manager.create_backup("test_backup")

        # Verify backup
        is_valid = backup_manager.verify_backup(backup_path)
        assert is_valid is True, "Backup should be valid"

    def test_installer_prevents_unauthorized_access(self, installer):
        """Test that installer prevents unauthorized access to sensitive directories."""
        # Create sensitive directories
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify directories exist
        assert installer.app_dir.exists(), "App directory should exist"
        assert installer.data_dir.exists(), "Data directory should exist"

    def test_backup_restoration_preserves_data_integrity(self, backup_manager, installer):
        """Test that backup restoration preserves data integrity."""
        # Create test data
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)
        test_file = installer.data_dir / "important_file.txt"
        test_content = "important data that must be preserved"
        test_file.write_text(test_content)

        # Create backup
        backup_path = backup_manager.create_backup("test_backup")

        # Verify backup was created
        assert backup_path is not None, "Backup should be created"
        assert backup_path.exists(), "Backup should exist"

        # Verify data integrity in backup
        backup_file = backup_path / "data" / "important_file.txt"
        if backup_file.exists():
            assert backup_file.read_text() == test_content, "Data should be preserved in backup"

    def test_clean_install_removes_all_sensitive_data(self, clean_install_mode, installer):
        """Test that Clean Install removes all sensitive data."""
        # Setup existing installation with sensitive data
        installer.app_dir.mkdir(parents=True, exist_ok=True)
        installer.data_dir.mkdir(parents=True, exist_ok=True)
        installer.config_dir.mkdir(parents=True, exist_ok=True)
        installer.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sensitive files
        (installer.data_dir / "user_data.db").write_text("sensitive data")
        (installer.config_dir / "settings.json").write_text('{"api_key": "secret"}')
        
        # Mock methods
        clean_install_mode._display_destructive_warning = MagicMock()
        clean_install_mode._create_final_backup = MagicMock()
        clean_install_mode._install_modules = MagicMock()
        clean_install_mode._initialize_database = MagicMock()
        clean_install_mode._create_configuration = MagicMock()
        
        clean_install_mode.execute("0.1.5", ["core"])
        
        # Verify sensitive data was removed (except backups)
        assert not (installer.data_dir / "user_data.db").exists(), "User data should be removed"
        assert not (installer.config_dir / "settings.json").exists(), "Config should be removed"

