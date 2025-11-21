"""
Tests for Phase 2: Core Services

Tests IFTService, RunModeManager, ProjectManager, and FileManager.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.core.services.ift_service import IFTService, IFTDefinition
from src.core.services.run_mode_manager import RunModeManager
from src.core.services.project_manager import ProjectManager
from src.core.services.file_manager import FileManager
from src.core.database.database_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    yield db_path

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


class TestIFTService:
    """Test IFT Service."""

    def test_ift_service_initialization(self):
        """Test IFT service initialization."""
        service = IFTService()
        assert service is not None
        assert service.get_ift_count() > 0

    def test_get_ift(self):
        """Test getting IFT definition."""
        service = IFTService()
        ift = service.get_ift("stl")
        assert ift is not None
        assert ift.extension == ".stl"

    def test_get_ift_by_extension(self):
        """Test getting IFT by extension."""
        service = IFTService()
        ift = service.get_ift_by_extension(".stl")
        assert ift is not None
        assert ift.name == "STL Model"

    def test_list_ifts(self):
        """Test listing IFTs."""
        service = IFTService()
        ifts = service.list_ifts()
        assert len(ifts) > 0

    def test_add_ift(self):
        """Test adding IFT."""
        service = IFTService()
        initial_count = service.get_ift_count()

        new_ift = IFTDefinition(
            name="Test Model", extension=".test", description="Test file type"
        )
        service.add_ift("test", new_ift)

        assert service.get_ift_count() > initial_count

    def test_enable_disable_ift(self):
        """Test enabling/disabling IFT."""
        service = IFTService()
        service.disable_ift("stl")

        ift = service.get_ift("stl")
        assert ift.enabled is False

        service.enable_ift("stl")
        ift = service.get_ift("stl")
        assert ift.enabled is True

    def test_reset_to_defaults(self):
        """Test resetting to defaults."""
        service = IFTService()
        service.reset_to_defaults()

        assert service.get_ift("stl") is not None
        assert service.get_ift("obj") is not None


class TestRunModeManager:
    """Test Run Mode Manager."""

    def test_run_mode_manager_initialization(self):
        """Test run mode manager initialization."""
        manager = RunModeManager()
        assert manager is not None

    def test_get_run_mode(self):
        """Test getting run mode."""
        manager = RunModeManager()
        mode = manager.get_run_mode()
        assert mode in (
            RunModeManager.RUN_MODE_FIRST_TIME,
            RunModeManager.RUN_MODE_NORMAL,
            RunModeManager.RUN_MODE_PORTABLE,
        )

    def test_set_run_mode(self):
        """Test setting run mode."""
        manager = RunModeManager()
        result = manager.set_run_mode(RunModeManager.RUN_MODE_NORMAL)
        assert result is True

    def test_storage_location(self):
        """Test storage location."""
        manager = RunModeManager()
        location = manager.get_storage_location()
        assert location is not None
        assert os.path.isdir(location)

    def test_database_path(self):
        """Test database path."""
        manager = RunModeManager()
        db_path = manager.get_database_path()
        assert db_path is not None
        assert db_path.endswith("3dmm.db")

    def test_projects_directory(self):
        """Test projects directory."""
        manager = RunModeManager()
        projects_dir = manager.get_projects_directory()
        assert projects_dir is not None
        assert os.path.isdir(projects_dir)

    def test_preferences(self):
        """Test preferences."""
        manager = RunModeManager()
        manager.set_preference("test_key", "test_value")
        value = manager.get_preference("test_key")
        assert value == "test_value"


class TestProjectManager:
    """Test Project Manager."""

    def test_create_project(self, db_manager):
        """Test creating project."""
        manager = ProjectManager(db_manager)
        project_id = manager.create_project("Test Project")
        assert project_id is not None

    def test_open_project(self, db_manager):
        """Test opening project."""
        manager = ProjectManager(db_manager)
        project_id = manager.create_project("Test Project")

        result = manager.open_project(project_id)
        assert result is True
        assert manager.get_current_project() is not None

    def test_close_project(self, db_manager):
        """Test closing project."""
        manager = ProjectManager(db_manager)
        project_id = manager.create_project("Test Project")
        manager.open_project(project_id)

        result = manager.close_project()
        assert result is True
        assert manager.get_current_project() is None

    def test_get_project(self, db_manager):
        """Test getting project."""
        manager = ProjectManager(db_manager)
        project_id = manager.create_project("Test Project")

        project = manager.get_project(project_id)
        assert project is not None
        assert project["name"] == "Test Project"

    def test_list_projects(self, db_manager):
        """Test listing projects."""
        manager = ProjectManager(db_manager)
        manager.create_project("Project 1")
        manager.create_project("Project 2")

        projects = manager.list_projects()
        assert len(projects) >= 2

    def test_check_duplicate(self, db_manager):
        """Test duplicate detection."""
        manager = ProjectManager(db_manager)
        manager.create_project("Test Project")

        is_duplicate = manager.check_duplicate("Test Project")
        assert is_duplicate is True

    def test_delete_project(self, db_manager):
        """Test deleting project."""
        manager = ProjectManager(db_manager)
        project_id = manager.create_project("Test Project")

        result = manager.delete_project(project_id)
        assert result is True


class TestFileManager:
    """Test File Manager."""

    def test_add_file(self, db_manager):
        """Test adding file."""
        project_manager = ProjectManager(db_manager)
        file_manager = FileManager(db_manager)

        project_id = project_manager.create_project("Test Project")
        file_id = file_manager.add_file(
            project_id=project_id, file_path="/path/to/file.stl", file_name="file.stl"
        )

        assert file_id is not None

    def test_get_file(self, db_manager):
        """Test getting file."""
        project_manager = ProjectManager(db_manager)
        file_manager = FileManager(db_manager)

        project_id = project_manager.create_project("Test Project")
        file_id = file_manager.add_file(
            project_id=project_id, file_path="/path/to/file.stl", file_name="file.stl"
        )

        file_data = file_manager.get_file(file_id)
        assert file_data is not None
        assert file_data["file_name"] == "file.stl"

    def test_update_file_status(self, db_manager):
        """Test updating file status."""
        project_manager = ProjectManager(db_manager)
        file_manager = FileManager(db_manager)

        project_id = project_manager.create_project("Test Project")
        file_id = file_manager.add_file(
            project_id=project_id, file_path="/path/to/file.stl", file_name="file.stl"
        )

        result = file_manager.update_file_status(file_id, "imported")
        assert result is True

    def test_get_files_by_project(self, db_manager):
        """Test getting files by project."""
        project_manager = ProjectManager(db_manager)
        file_manager = FileManager(db_manager)

        project_id = project_manager.create_project("Test Project")
        file_manager.add_file(project_id, "/path/to/file1.stl", "file1.stl")
        file_manager.add_file(project_id, "/path/to/file2.obj", "file2.obj")

        files = file_manager.get_files_by_project(project_id)
        assert len(files) == 2

    def test_delete_file(self, db_manager):
        """Test deleting file."""
        project_manager = ProjectManager(db_manager)
        file_manager = FileManager(db_manager)

        project_id = project_manager.create_project("Test Project")
        file_id = file_manager.add_file(
            project_id=project_id, file_path="/path/to/file.stl", file_name="file.stl"
        )

        result = file_manager.delete_file(file_id)
        assert result is True
