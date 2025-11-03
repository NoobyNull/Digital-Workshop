"""
Tests for Phase 3: UI Components

Tests RunModeSetupDialog and ProjectManagerWidget.
"""

import os
import tempfile
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.gui.dialogs.run_mode_setup_dialog import RunModeSetupDialog
from src.gui.project_manager.project_manager_widget import ProjectManagerWidget
from src.core.database.database_manager import DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


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


class TestRunModeSetupDialog:
    """Test Run Mode Setup Dialog."""

    def test_dialog_creation(self, qapp):
        """Test dialog creation."""
        dialog = RunModeSetupDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Digital Workshop - First Run Setup"

    def test_dialog_storage_location(self, qapp):
        """Test storage location display."""
        dialog = RunModeSetupDialog()
        location = dialog.get_storage_location()
        assert location is not None
        assert len(location) > 0

    def test_dialog_signals(self, qapp):
        """Test dialog signals."""
        dialog = RunModeSetupDialog()
        
        # Check that signals exist
        assert hasattr(dialog, 'setup_complete')
        assert dialog.setup_complete is not None


class TestProjectManagerWidget:
    """Test Project Manager Widget."""

    def test_widget_creation(self, qapp, db_manager):
        """Test widget creation."""
        widget = ProjectManagerWidget(db_manager)
        assert widget is not None

    def test_widget_signals(self, qapp, db_manager):
        """Test widget signals."""
        widget = ProjectManagerWidget(db_manager)
        
        # Check that signals exist
        assert hasattr(widget, 'project_opened')
        assert hasattr(widget, 'project_created')
        assert hasattr(widget, 'project_deleted')

    def test_project_list_empty(self, qapp, db_manager):
        """Test project list is empty initially."""
        widget = ProjectManagerWidget(db_manager)
        assert widget.project_list.count() == 0

    def test_project_list_refresh(self, qapp, db_manager):
        """Test project list refresh."""
        widget = ProjectManagerWidget(db_manager)
        
        # Create a project
        db_manager.create_project("Test Project")
        
        # Refresh list
        widget._refresh_project_list()
        
        # Check list has item
        assert widget.project_list.count() == 1

    def test_project_list_shows_imported_tag(self, qapp, db_manager):
        """Test project list shows imported tag."""
        widget = ProjectManagerWidget(db_manager)
        
        # Create imported project
        db_manager.create_project(
            "Imported Library",
            import_tag="imported_project"
        )
        
        # Refresh list
        widget._refresh_project_list()
        
        # Check list shows imported tag
        item = widget.project_list.item(0)
        assert "[Imported]" in item.text()

    def test_project_list_multiple_projects(self, qapp, db_manager):
        """Test project list with multiple projects."""
        widget = ProjectManagerWidget(db_manager)
        
        # Create multiple projects
        db_manager.create_project("Project 1")
        db_manager.create_project("Project 2")
        db_manager.create_project("Project 3")
        
        # Refresh list
        widget._refresh_project_list()
        
        # Check list has all projects
        assert widget.project_list.count() == 3

    def test_widget_buttons_exist(self, qapp, db_manager):
        """Test that all buttons exist."""
        widget = ProjectManagerWidget(db_manager)
        
        # Check buttons are created (they should be in the layout)
        assert widget.project_list is not None


class TestUIIntegration:
    """Test UI integration."""

    def test_run_mode_dialog_and_project_manager(self, qapp, db_manager):
        """Test run mode dialog and project manager together."""
        # Create dialog
        dialog = RunModeSetupDialog()
        assert dialog is not None
        
        # Create widget
        widget = ProjectManagerWidget(db_manager)
        assert widget is not None
        
        # Both should work together
        location = dialog.get_storage_location()
        assert location is not None

    def test_project_manager_with_imported_projects(self, qapp, db_manager):
        """Test project manager with imported projects."""
        widget = ProjectManagerWidget(db_manager)
        
        # Create regular project
        db_manager.create_project("Regular Project")
        
        # Create imported project
        db_manager.create_project(
            "Imported Library",
            import_tag="imported_project",
            original_path="/original/path"
        )
        
        # Refresh list
        widget._refresh_project_list()
        
        # Check both projects are listed
        assert widget.project_list.count() == 2
        
        # Check imported tag is shown
        imported_found = False
        for i in range(widget.project_list.count()):
            item = widget.project_list.item(i)
            if "[Imported]" in item.text():
                imported_found = True
        
        assert imported_found is True

