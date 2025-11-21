"""
Unit tests for the MigrationManager class
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.installer.installer import Installer
from src.installer.managers.migration_manager import MigrationManager


class TestMigrationManager:
    """Test cases for MigrationManager class."""

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
    def migration_manager(self, installer):
        """Create migration manager instance."""
        return MigrationManager(installer)

    def test_migration_manager_initialization(self, migration_manager, installer):
        """Test migration manager initialization."""
        assert migration_manager.installer is not None
        assert migration_manager.db_path == installer.data_dir / "3dmm.db"

    def test_initialize_database(self, migration_manager):
        """Test database initialization."""
        result = migration_manager.initialize_database()

        assert result is True
        assert migration_manager.db_path.exists()

        # Verify tables were created
        conn = sqlite3.connect(str(migration_manager.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "projects" in tables
        assert "models" in tables
        assert "settings" in tables
        assert "migration_history" in tables

        conn.close()

    def test_initialize_database_creates_migration_history(self, migration_manager):
        """Test that initialization records migration history."""
        migration_manager.initialize_database()

        history = migration_manager.get_migration_history()

        assert len(history) > 0
        assert history[0]["version"] == "0.1.0"
        assert history[0]["migration_type"] == "initial"

    def test_apply_migrations(self, migration_manager):
        """Test applying migrations."""
        # Initialize database first
        migration_manager.initialize_database()

        # Apply migration
        result = migration_manager.apply_migrations("0.1.0", "0.1.1")

        assert result is True

    def test_apply_migrations_no_database(self, migration_manager):
        """Test applying migrations when database doesn't exist."""
        result = migration_manager.apply_migrations("0.1.0", "0.1.1")

        # Should initialize database and apply migrations
        assert result is True
        assert migration_manager.db_path.exists()

    def test_get_migration_history_empty(self, migration_manager):
        """Test getting migration history when database doesn't exist."""
        history = migration_manager.get_migration_history()

        assert history == []

    def test_get_migration_history(self, migration_manager):
        """Test getting migration history."""
        migration_manager.initialize_database()

        history = migration_manager.get_migration_history()

        assert len(history) > 0
        assert "version" in history[0]
        assert "migration_type" in history[0]
        assert "applied_date" in history[0]

    def test_get_current_schema_version_no_database(self, migration_manager):
        """Test getting schema version when database doesn't exist."""
        version = migration_manager.get_current_schema_version()

        assert version is None

    def test_get_current_schema_version(self, migration_manager):
        """Test getting current schema version."""
        migration_manager.initialize_database()

        version = migration_manager.get_current_schema_version()

        assert version == "0.1.0"

    def test_database_has_projects_table(self, migration_manager):
        """Test that projects table exists and has correct schema."""
        migration_manager.initialize_database()

        conn = sqlite3.connect(str(migration_manager.db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]

        assert "id" in columns
        assert "name" in columns
        assert "path" in columns
        assert "created_date" in columns
        assert "modified_date" in columns

        conn.close()

    def test_database_has_models_table(self, migration_manager):
        """Test that models table exists and has correct schema."""
        migration_manager.initialize_database()

        conn = sqlite3.connect(str(migration_manager.db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(models)")
        columns = [row[1] for row in cursor.fetchall()]

        assert "id" in columns
        assert "project_id" in columns
        assert "name" in columns
        assert "file_path" in columns

        conn.close()

    def test_database_has_settings_table(self, migration_manager):
        """Test that settings table exists and has correct schema."""
        migration_manager.initialize_database()

        conn = sqlite3.connect(str(migration_manager.db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(settings)")
        columns = [row[1] for row in cursor.fetchall()]

        assert "key" in columns
        assert "value" in columns
        assert "modified_date" in columns

        conn.close()
