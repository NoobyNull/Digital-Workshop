"""
Tests for Phase 1: Database Schema - Projects and Files tables.

Tests the creation and functionality of the Projects and Files tables,
as well as the ProjectRepository and FileRepository classes.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from src.core.database.database_manager import DatabaseManager
from src.core.database.project_repository import ProjectRepository
from src.core.database.file_repository import FileRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    yield db_path

    # Cleanup
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(tmpdir):
            os.rmdir(tmpdir)
    except Exception:
        pass


@pytest.fixture
def db_manager(temp_db):
    """Create a database manager with temporary database."""
    manager = DatabaseManager(temp_db)
    yield manager
    try:
        manager.close()
    except Exception:
        pass


class TestDatabaseSchema:
    """Test database schema creation."""

    def test_projects_table_created(self, db_manager):
        """Test that projects table is created."""
        with db_manager._db_ops.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
            )
            assert cursor.fetchone() is not None

    def test_files_table_created(self, db_manager):
        """Test that files table is created."""
        with db_manager._db_ops.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
            )
            assert cursor.fetchone() is not None

    def test_projects_table_columns(self, db_manager):
        """Test that projects table has correct columns."""
        with db_manager._db_ops.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(projects)")
            columns = {row[1] for row in cursor.fetchall()}

            expected_columns = {
                "id",
                "name",
                "base_path",
                "import_tag",
                "original_path",
                "structure_type",
                "import_date",
                "created_at",
                "updated_at",
            }
            assert expected_columns.issubset(columns)

    def test_files_table_columns(self, db_manager):
        """Test that files table has correct columns."""
        with db_manager._db_ops.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(files)")
            columns = {row[1] for row in cursor.fetchall()}

            expected_columns = {
                "id",
                "project_id",
                "file_path",
                "file_name",
                "file_size",
                "file_hash",
                "status",
                "link_type",
                "original_path",
                "created_at",
                "updated_at",
            }
            assert expected_columns.issubset(columns)


class TestProjectRepository:
    """Test ProjectRepository functionality."""

    def test_create_project(self, db_manager):
        """Test creating a project."""
        project_id = db_manager.create_project(
            name="Test Project", base_path="/path/to/project"
        )

        assert project_id is not None
        assert isinstance(project_id, str)
        assert len(project_id) > 0

    def test_get_project(self, db_manager):
        """Test retrieving a project."""
        project_id = db_manager.create_project(
            name="Test Project", base_path="/path/to/project"
        )

        project = db_manager.get_project(project_id)
        assert project is not None
        assert project["name"] == "Test Project"
        assert project["base_path"] == "/path/to/project"

    def test_get_project_by_name(self, db_manager):
        """Test retrieving a project by name (case-insensitive)."""
        db_manager.create_project(name="Test Project", base_path="/path/to/project")

        # Test exact match
        project = db_manager.get_project_by_name("Test Project")
        assert project is not None
        assert project["name"] == "Test Project"

        # Test case-insensitive match
        project = db_manager.get_project_by_name("test project")
        assert project is not None
        assert project["name"] == "Test Project"

    def test_duplicate_project_detection(self, db_manager):
        """Test that duplicate projects are detected (case-insensitive)."""
        db_manager.create_project(name="Test Project")

        # Should raise ValueError for duplicate
        with pytest.raises(ValueError):
            db_manager.create_project(name="Test Project")

        # Should also detect case-insensitive duplicates
        with pytest.raises(ValueError):
            db_manager.create_project(name="test project")

    def test_list_projects(self, db_manager):
        """Test listing projects."""
        db_manager.create_project(name="Project 1")
        db_manager.create_project(name="Project 2")
        db_manager.create_project(name="Project 3")

        projects = db_manager.list_projects()
        assert len(projects) == 3

    def test_update_project(self, db_manager):
        """Test updating a project."""
        project_id = db_manager.create_project(name="Test Project")

        success = db_manager.update_project(project_id, base_path="/new/path")

        assert success
        project = db_manager.get_project(project_id)
        assert project["base_path"] == "/new/path"

    def test_delete_project(self, db_manager):
        """Test deleting a project."""
        project_id = db_manager.create_project(name="Test Project")

        success = db_manager.delete_project(project_id)
        assert success

        project = db_manager.get_project(project_id)
        assert project is None

    def test_imported_project_tagging(self, db_manager):
        """Test tagging imported projects."""
        project_id = db_manager.create_project(
            name="Imported Project",
            import_tag="imported_project",
            original_path="/original/path",
            structure_type="nested",
        )

        project = db_manager.get_project(project_id)
        assert project["import_tag"] == "imported_project"
        assert project["original_path"] == "/original/path"
        assert project["structure_type"] == "nested"

    def test_list_imported_projects(self, db_manager):
        """Test listing imported projects."""
        db_manager.create_project(name="Regular Project")
        db_manager.create_project(
            name="Imported Project 1", import_tag="imported_project"
        )
        db_manager.create_project(
            name="Imported Project 2", import_tag="imported_project"
        )

        imported = db_manager.list_imported_projects()
        assert len(imported) == 2
        assert all(p["import_tag"] == "imported_project" for p in imported)


class TestFileRepository:
    """Test FileRepository functionality."""

    def test_add_file(self, db_manager):
        """Test adding a file to a project."""
        project_id = db_manager.create_project(name="Test Project")

        file_id = db_manager.add_file(
            project_id=project_id,
            file_path="/path/to/file.stl",
            file_name="file.stl",
            file_size=1024,
            status="imported",
        )

        assert file_id is not None
        assert isinstance(file_id, int)

    def test_get_file(self, db_manager):
        """Test retrieving a file."""
        project_id = db_manager.create_project(name="Test Project")
        file_id = db_manager.add_file(
            project_id=project_id, file_path="/path/to/file.stl", file_name="file.stl"
        )

        file_data = db_manager.get_file(file_id)
        assert file_data is not None
        assert file_data["file_name"] == "file.stl"
        assert file_data["project_id"] == project_id

    def test_get_files_by_project(self, db_manager):
        """Test retrieving files by project."""
        project_id = db_manager.create_project(name="Test Project")

        db_manager.add_file(project_id, "/path/to/file1.stl", "file1.stl")
        db_manager.add_file(project_id, "/path/to/file2.obj", "file2.obj")

        files = db_manager.get_files_by_project(project_id)
        assert len(files) == 2

    def test_update_file_status(self, db_manager):
        """Test updating file status."""
        project_id = db_manager.create_project(name="Test Project")
        file_id = db_manager.add_file(
            project_id, "/path/to/file.stl", "file.stl", status="pending"
        )

        success = db_manager.update_file_status(file_id, "imported")
        assert success

        file_data = db_manager.get_file(file_id)
        assert file_data["status"] == "imported"

    def test_delete_file(self, db_manager):
        """Test deleting a file."""
        project_id = db_manager.create_project(name="Test Project")
        file_id = db_manager.add_file(project_id, "/path/to/file.stl", "file.stl")

        success = db_manager.delete_file(file_id)
        assert success

        file_data = db_manager.get_file(file_id)
        assert file_data is None

    def test_cascade_delete_files_with_project(self, db_manager):
        """Test that files are deleted when project is deleted."""
        project_id = db_manager.create_project(name="Test Project")
        db_manager.add_file(project_id, "/path/to/file1.stl", "file1.stl")
        db_manager.add_file(project_id, "/path/to/file2.obj", "file2.obj")

        # Delete project
        db_manager.delete_project(project_id)

        # Files should be deleted too
        files = db_manager.get_files_by_project(project_id)
        assert len(files) == 0
