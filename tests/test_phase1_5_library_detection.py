"""
Tests for Phase 1.5: Library Structure Detection & Project Import

Tests the library structure detector, file type filter, dry run analyzer,
and project importer functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.core.services.library_structure_detector import LibraryStructureDetector
from src.core.services.file_type_filter import FileTypeFilter
from src.core.services.dry_run_analyzer import DryRunAnalyzer
from src.core.services.project_importer import ProjectImporter
from src.core.database.database_manager import DatabaseManager


@pytest.fixture
def temp_library():
    """Create a temporary library structure for testing."""
    tmpdir = tempfile.mkdtemp()
    
    # Create folder structure
    models_dir = os.path.join(tmpdir, "models")
    docs_dir = os.path.join(tmpdir, "documentation")
    os.makedirs(models_dir)
    os.makedirs(docs_dir)
    
    # Create test files
    Path(os.path.join(models_dir, "model1.stl")).touch()
    Path(os.path.join(models_dir, "model2.obj")).touch()
    Path(os.path.join(docs_dir, "readme.md")).touch()
    Path(os.path.join(docs_dir, "guide.pdf")).touch()
    Path(os.path.join(tmpdir, "image.png")).touch()
    
    yield tmpdir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass


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


class TestLibraryStructureDetector:
    """Test library structure detection."""

    def test_detect_organized_library(self, temp_library):
        """Test detection of organized library."""
        detector = LibraryStructureDetector()
        analysis = detector.analyze(temp_library)
        
        assert analysis.folder_path == temp_library
        assert analysis.total_files == 5
        assert analysis.total_folders == 2
        assert analysis.is_organized is True
        assert analysis.confidence_score > 0

    def test_detect_structure_type(self, temp_library):
        """Test structure type detection."""
        detector = LibraryStructureDetector()
        analysis = detector.analyze(temp_library)
        
        assert analysis.structure_type in ("flat", "nested", "balanced")

    def test_file_type_grouping(self, temp_library):
        """Test file type grouping."""
        detector = LibraryStructureDetector()
        analysis = detector.analyze(temp_library)
        
        assert "3D Models" in analysis.file_type_grouping
        assert "Documents" in analysis.file_type_grouping
        assert "Images" in analysis.file_type_grouping

    def test_metadata_detection(self, temp_library):
        """Test metadata file detection."""
        detector = LibraryStructureDetector()
        analysis = detector.analyze(temp_library)
        
        assert analysis.has_metadata is True
        assert "readme.md" in analysis.metadata_files


class TestFileTypeFilter:
    """Test file type filtering."""

    def test_allow_supported_file(self):
        """Test that supported files are allowed."""
        filter = FileTypeFilter()
        result = filter.filter_file("/path/to/model.stl")
        
        assert result.is_allowed is True
        assert result.category == "3D Models"

    def test_block_executable(self):
        """Test that executables are blocked."""
        filter = FileTypeFilter()
        result = filter.filter_file("/path/to/malware.exe")
        
        assert result.is_allowed is False
        assert "Blocked" in result.reason

    def test_block_script(self):
        """Test that scripts are blocked."""
        filter = FileTypeFilter()
        result = filter.filter_file("/path/to/script.ps1")
        
        assert result.is_allowed is False

    def test_allow_document(self):
        """Test that documents are allowed."""
        filter = FileTypeFilter()
        result = filter.filter_file("/path/to/guide.pdf")
        
        assert result.is_allowed is True
        assert result.category == "Documents"

    def test_filter_multiple_files(self):
        """Test filtering multiple files."""
        filter = FileTypeFilter()
        files = [
            "/path/to/model.stl",
            "/path/to/script.exe",
            "/path/to/image.png",
            "/path/to/malware.bat"
        ]
        
        allowed, blocked = filter.filter_files(files)
        
        assert len(allowed) == 2
        assert len(blocked) == 2

    def test_block_system_filename(self):
        """Test blocking system filenames."""
        filter = FileTypeFilter()
        result = filter.filter_file("/path/to/autorun.inf")
        
        assert result.is_allowed is False


class TestDryRunAnalyzer:
    """Test dry run analysis."""

    def test_dry_run_analysis(self, temp_library):
        """Test dry run analysis."""
        analyzer = DryRunAnalyzer()
        report = analyzer.analyze(temp_library, "Test Project")
        
        assert report.project_name == "Test Project"
        assert report.total_files == 5
        assert report.allowed_files > 0
        assert report.can_proceed is True

    def test_dry_run_blocked_files(self, temp_library):
        """Test dry run with blocked files."""
        # Create a blocked file
        Path(os.path.join(temp_library, "malware.exe")).touch()
        
        analyzer = DryRunAnalyzer()
        report = analyzer.analyze(temp_library, "Test Project")
        
        assert report.blocked_files > 0

    def test_dry_run_size_calculation(self, temp_library):
        """Test size calculation in dry run."""
        analyzer = DryRunAnalyzer()
        report = analyzer.analyze(temp_library, "Test Project")
        
        assert report.total_size_bytes >= 0
        assert report.total_size_mb >= 0

    def test_dry_run_recommendations(self, temp_library):
        """Test recommendations generation."""
        analyzer = DryRunAnalyzer()
        report = analyzer.analyze(temp_library, "Test Project")
        
        assert len(report.recommendations) > 0


class TestProjectImporter:
    """Test project import."""

    def test_import_project(self, temp_library, db_manager):
        """Test project import."""
        importer = ProjectImporter(db_manager)
        report = importer.import_project(temp_library, "Imported Library")
        
        assert report.project_name == "Imported Library"
        assert report.files_imported > 0
        assert report.success is True

    def test_import_creates_project(self, temp_library, db_manager):
        """Test that import creates project in database."""
        importer = ProjectImporter(db_manager)
        report = importer.import_project(temp_library, "Test Import")
        
        # Verify project was created
        project = db_manager.get_project(report.project_id)
        assert project is not None
        assert project['name'] == "Test Import"
        assert project['import_tag'] == "imported_project"

    def test_import_adds_files(self, temp_library, db_manager):
        """Test that import adds files to database."""
        importer = ProjectImporter(db_manager)
        report = importer.import_project(temp_library, "Test Import")
        
        # Verify files were added
        files = db_manager.get_files_by_project(report.project_id)
        assert len(files) == report.files_imported

    def test_import_blocks_executables(self, temp_library, db_manager):
        """Test that import blocks executable files."""
        # Create an executable
        Path(os.path.join(temp_library, "malware.exe")).touch()
        
        importer = ProjectImporter(db_manager)
        report = importer.import_project(temp_library, "Test Import")
        
        assert report.files_blocked > 0

    def test_import_summary(self, temp_library, db_manager):
        """Test import summary generation."""
        importer = ProjectImporter(db_manager)
        report = importer.import_project(temp_library, "Test Import")
        
        summary = importer.get_import_summary(report)
        assert "Test Import" in summary
        assert "Success" in summary or "Failed" in summary


class TestImportWorkflow:
    """Test complete import workflow."""

    def test_full_import_workflow(self, temp_library, db_manager):
        """Test complete import workflow."""
        # Step 1: Analyze structure
        detector = LibraryStructureDetector()
        structure = detector.analyze(temp_library)
        assert structure.is_organized is True
        
        # Step 2: Dry run
        analyzer = DryRunAnalyzer()
        dry_run = analyzer.analyze(temp_library, "My Library")
        assert dry_run.can_proceed is True
        
        # Step 3: Import
        importer = ProjectImporter(db_manager)
        report = importer.import_project(
            temp_library,
            "My Library",
            structure_type=structure.structure_type
        )
        assert report.success is True
        
        # Step 4: Verify
        project = db_manager.get_project(report.project_id)
        assert project is not None
        assert project['import_tag'] == "imported_project"
        
        files = db_manager.get_files_by_project(report.project_id)
        assert len(files) > 0

