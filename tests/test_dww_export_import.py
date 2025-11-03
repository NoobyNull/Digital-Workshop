"""
Tests for DWW (Digital Wood Works) export and import functionality.
"""

import json
import tempfile
import zipfile
from pathlib import Path
import pytest

from src.core.export.dww_export_manager import DWWExportManager
from src.core.export.dww_import_manager import DWWImportManager


class MockDatabaseManager:
    """Mock database manager for testing."""

    def __init__(self):
        self.projects = {
            "test-project-1": {
                "id": "test-project-1",
                "name": "Test Project",
                "description": "A test project",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        }
        self.files = {
            "test-project-1": [
                {
                    "file_name": "model.stl",
                    "file_path": None,  # Will be set in tests
                },
                {
                    "file_name": "gcode.nc",
                    "file_path": None,  # Will be set in tests
                },
            ]
        }

    def get_project(self, project_id):
        return self.projects.get(project_id)

    def get_files_by_project(self, project_id):
        return self.files.get(project_id, [])


class TestDWWExportManager:
    """Test DWW export functionality."""

    def test_export_project_creates_dww_file(self):
        """Test that export creates a valid DWW file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file_1 = Path(tmpdir) / "model.stl"
            test_file_1.write_text("STL file content")

            test_file_2 = Path(tmpdir) / "gcode.nc"
            test_file_2.write_text("G-code content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file_1)
            db_manager.files["test-project-1"][1]["file_path"] = str(test_file_2)

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path)
            )

            assert success, f"Export failed: {message}"
            assert output_path.exists(), "DWW file was not created"

    def test_export_includes_thumbnails(self):
        """Test that export includes thumbnails when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Create thumbnail
            thumb_file = Path(tmpdir) / "model.thumb.png"
            thumb_file.write_bytes(b"PNG thumbnail data")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"][0]["thumbnail_path"] = str(thumb_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path), include_thumbnails=True
            )

            assert success, f"Export failed: {message}"

            # Verify thumbnail is in archive
            with zipfile.ZipFile(output_path, 'r') as dww:
                files = dww.namelist()
                assert any("thumbnails/" in f for f in files), "Thumbnails not found in archive"

    def test_export_includes_metadata(self):
        """Test that export includes metadata when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"][0]["file_hash"] = "abc123"
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path), include_metadata=True
            )

            assert success, f"Export failed: {message}"

            # Verify metadata is in archive
            with zipfile.ZipFile(output_path, 'r') as dww:
                files = dww.namelist()
                assert "metadata/files_metadata.json" in files, "Metadata not found in archive"
                metadata = json.loads(dww.read("metadata/files_metadata.json").decode())
                assert "files_metadata" in metadata

    def test_dww_file_contains_manifest(self):
        """Test that DWW file contains manifest.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify manifest exists
            with zipfile.ZipFile(output_path, 'r') as dww:
                assert "manifest.json" in dww.namelist()
                manifest = json.loads(dww.read("manifest.json").decode())
                assert manifest["version"] == "1.0"
                assert manifest["format"] == "Digital Wood Works"
                assert manifest["project"]["name"] == "Test Project"

    def test_dww_file_contains_integrity_data(self):
        """Test that DWW file contains integrity.json with hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify integrity data exists
            with zipfile.ZipFile(output_path, 'r') as dww:
                assert "integrity.json" in dww.namelist()
                integrity = json.loads(dww.read("integrity.json").decode())
                assert "salt" in integrity
                assert "hash" in integrity
                assert integrity["algorithm"] == "SHA256"

    def test_verify_dww_file_integrity(self):
        """Test DWW file integrity verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = DWWExportManager(db_manager)
            output_path = Path(tmpdir) / "export.dww"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify integrity
            is_valid, message = export_manager.verify_dww_file(str(output_path))
            assert is_valid, f"Integrity verification failed: {message}"


class TestDWWImportManager:
    """Test DWW import functionality."""

    def test_import_project_extracts_files(self):
        """Test that import extracts files from DWW archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = DWWExportManager(db_manager)
            export_path = Path(tmpdir) / "export.dww"
            export_manager.export_project("test-project-1", str(export_path))

            # Import project
            import_dir = Path(tmpdir) / "import"
            import_manager = DWWImportManager(db_manager)
            success, message, manifest = import_manager.import_project(
                str(export_path), str(import_dir), verify_integrity=True
            )

            assert success, f"Import failed: {message}"
            assert manifest is not None
            assert manifest["project"]["name"] == "Test Project"

    def test_import_project_extracts_thumbnails(self):
        """Test that import extracts thumbnails correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            thumb_file = Path(tmpdir) / "model.thumb.png"
            thumb_file.write_bytes(b"PNG thumbnail data")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"][0]["thumbnail_path"] = str(thumb_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = DWWExportManager(db_manager)
            export_path = Path(tmpdir) / "export.dww"
            export_manager.export_project("test-project-1", str(export_path), include_thumbnails=True)

            # Import project with thumbnails
            import_dir = Path(tmpdir) / "import"
            import_manager = DWWImportManager(db_manager)
            success, message, _ = import_manager.import_project(
                str(export_path), str(import_dir), import_thumbnails=True
            )

            assert success, f"Import failed: {message}"
            assert (import_dir / "thumbnails").exists(), "Thumbnails directory not created"
            assert any((import_dir / "thumbnails").glob("*.png")), "No thumbnails extracted"

    def test_get_dww_info_without_extraction(self):
        """Test getting DWW info without extracting files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = DWWExportManager(db_manager)
            export_path = Path(tmpdir) / "export.dww"
            export_manager.export_project("test-project-1", str(export_path))

            # Get info
            import_manager = DWWImportManager()
            success, manifest = import_manager.get_dww_info(str(export_path))

            assert success
            assert manifest is not None
            assert manifest["project"]["name"] == "Test Project"

    def test_list_dww_files(self):
        """Test listing files in DWW archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = DWWExportManager(db_manager)
            export_path = Path(tmpdir) / "export.dww"
            export_manager.export_project("test-project-1", str(export_path))

            # List files
            import_manager = DWWImportManager()
            success, files = import_manager.list_dww_files(str(export_path))

            assert success
            assert files is not None
            assert len(files) > 0
            assert any("model.stl" in f for f in files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

