"""
Tests for PJCT project export and import functionality.
"""

import json
import tempfile
import zipfile
from pathlib import Path
import pytest

from src.core.export.dww_export_manager import PJCTExportManager
from src.core.export.dww_import_manager import PJCTImportManager


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


class TestPJCTExportManager:
    """Test PJCT export functionality."""

    def test_export_project_creates_pjct_file(self):
        """Test that export creates a valid PJCT file."""
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
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path)
            )

            assert success, f"Export failed: {message}"
            assert output_path.exists(), "PJCT file was not created"

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
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path), include_thumbnails=True
            )

            assert success, f"Export failed: {message}"

            # Verify thumbnail is in archive
            with zipfile.ZipFile(output_path, 'r') as pjct:
                files = pjct.namelist()
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
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            success, message = export_manager.export_project(
                "test-project-1", str(output_path), include_metadata=True
            )

            assert success, f"Export failed: {message}"

            # Verify metadata is in archive
            with zipfile.ZipFile(output_path, 'r') as pjct:
                files = pjct.namelist()
                assert "metadata/files_metadata.json" in files, "Metadata not found in archive"
                metadata = json.loads(pjct.read("metadata/files_metadata.json").decode())
                assert "files_metadata" in metadata

    def test_pjct_file_contains_manifest(self):
        """Test that PJCT file contains manifest.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify manifest exists
            with zipfile.ZipFile(output_path, 'r') as pjct:
                assert "manifest.json" in pjct.namelist()
                manifest = json.loads(pjct.read("manifest.json").decode())
                assert manifest["version"] == "1.0"
                assert manifest["format"] == "PJCT"
                assert manifest["project"]["name"] == "Test Project"

    def test_pjct_file_contains_integrity_data(self):
        """Test that PJCT file contains integrity.json with hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify integrity data exists
            with zipfile.ZipFile(output_path, 'r') as pjct:
                assert "integrity.json" in pjct.namelist()
                integrity = json.loads(pjct.read("integrity.json").decode())
                assert "salt" in integrity
                assert "hash" in integrity
                assert integrity["algorithm"] == "SHA256"

    def test_verify_pjct_file_integrity(self):
        """Test PJCT file integrity verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            # Export project
            export_manager = PJCTExportManager(db_manager)
            output_path = Path(tmpdir) / "export.pjt"

            export_manager.export_project("test-project-1", str(output_path))

            # Verify integrity
            is_valid, message = export_manager.verify_pjct_file(str(output_path))
            assert is_valid, f"Integrity verification failed: {message}"


    def test_export_includes_hero_tab_metadata(self):
        """Test that export writes hero tab summary metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create representative files for the different hero tabs
            model_file = tmpdir_path / "model.stl"
            model_file.write_text("STL file content")

            second_model = tmpdir_path / "part.obj"
            second_model.write_text("OBJ file content")

            gcode_file = tmpdir_path / "program.nc"
            gcode_file.write_text("G-code content")

            cut_list_file = tmpdir_path / "cut_list.json"
            cut_list_file.write_text("{}")

            feeds_file = tmpdir_path / "feeds_and_speeds.json"
            feeds_file.write_text("{}")

            cost_file = tmpdir_path / "cost_estimate.json"
            cost_file.write_text("{}")

            model_view_file = tmpdir_path / "model_view.json"
            model_view_file.write_text("{}")

            gcode_timing_file = tmpdir_path / "gcode_timing.json"
            gcode_timing_file.write_text("{}")

            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"] = [
                {"file_name": "model.stl", "file_path": str(model_file)},
                {"file_name": "part.obj", "file_path": str(second_model)},
                {"file_name": "program.nc", "file_path": str(gcode_file)},
                {"file_name": "cut_list.json", "file_path": str(cut_list_file)},
                {"file_name": "feeds_and_speeds.json", "file_path": str(feeds_file)},
                {"file_name": "cost_estimate.json", "file_path": str(cost_file)},
                {"file_name": "model_view.json", "file_path": str(model_view_file)},
                {"file_name": "gcode_timing.json", "file_path": str(gcode_timing_file)},
            ]

            export_manager = PJCTExportManager(db_manager)
            output_path = tmpdir_path / "export.pjt"

            success, message = export_manager.export_project("test-project-1", str(output_path))
            assert success, f"Export failed: {message}"

            with zipfile.ZipFile(output_path, "r") as pjct:
                files = pjct.namelist()
                assert "metadata/hero_tabs.json" in files

                hero = json.loads(pjct.read("metadata/hero_tabs.json").decode())
                assert hero.get("project_id") == "test-project-1"

                model_section = hero.get("model_previewer", {})
                assert set(model_section.get("model_files", [])) == {"model.stl", "part.obj"}
                assert model_section.get("has_view_state") is True

                gcode_section = hero.get("gcode_previewer", {})
                assert gcode_section.get("gcode_files") == ["program.nc"]
                assert gcode_section.get("has_timing_data") is True

                clo_section = hero.get("cut_list_optimizer", {})
                assert clo_section.get("has_tab_data") is True
                assert clo_section.get("filename") == "cut_list.json"

                fs_section = hero.get("feeds_and_speeds", {})
                assert fs_section.get("has_tab_data") is True
                assert fs_section.get("filename") == "feeds_and_speeds.json"

                cost_section = hero.get("project_cost_estimator", {})
                assert cost_section.get("has_tab_data") is True
                assert cost_section.get("filename") == "cost_estimate.json"


class TestPJCTImportManager:
    """Test PJCT import functionality."""

    def test_import_project_includes_hero_tab_metadata_in_manifest(self):
        """Test that hero tab metadata is attached to the returned manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            test_file = tmpdir_path / "model.stl"
            test_file.write_text("STL file content")

            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = PJCTExportManager(db_manager)
            export_path = tmpdir_path / "export.pjt"
            export_manager.export_project("test-project-1", str(export_path))

            import_dir = tmpdir_path / "import"
            import_manager = PJCTImportManager(db_manager)
            success, message, manifest = import_manager.import_project(
                str(export_path), str(import_dir), verify_integrity=True
            )

            assert success, f"Import failed: {message}"
            assert manifest is not None
            assert "hero_tabs" in manifest
            assert manifest["hero_tabs"].get("project_id") == "test-project-1"


    def test_import_project_extracts_files(self):
        """Test that import extracts files from PJT project archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = PJCTExportManager(db_manager)
            export_path = Path(tmpdir) / "export.pjt"
            export_manager.export_project("test-project-1", str(export_path))

            # Import project
            import_dir = Path(tmpdir) / "import"
            import_manager = PJCTImportManager(db_manager)
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

            export_manager = PJCTExportManager(db_manager)
            export_path = Path(tmpdir) / "export.pjt"
            export_manager.export_project("test-project-1", str(export_path), include_thumbnails=True)

            # Import project with thumbnails
            import_dir = Path(tmpdir) / "import"
            import_manager = PJCTImportManager(db_manager)
            success, message, _ = import_manager.import_project(
                str(export_path), str(import_dir), import_thumbnails=True
            )

            assert success, f"Import failed: {message}"
            assert (import_dir / "thumbnails").exists(), "Thumbnails directory not created"
            assert any((import_dir / "thumbnails").glob("*.png")), "No thumbnails extracted"

    def test_get_pjct_info_without_extraction(self):
        """Test getting PJCT manifest without extracting files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = PJCTExportManager(db_manager)
            export_path = Path(tmpdir) / "export.pjt"
            export_manager.export_project("test-project-1", str(export_path))

            # Get info
            import_manager = PJCTImportManager()
            success, manifest = import_manager.get_pjct_info(str(export_path))

            assert success
            assert manifest is not None
            assert manifest["project"]["name"] == "Test Project"

    def test_list_pjct_files(self):
        """Test listing files in PJCT archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "model.stl"
            test_file.write_text("STL file content")

            # Setup mock database and export
            db_manager = MockDatabaseManager()
            db_manager.files["test-project-1"][0]["file_path"] = str(test_file)
            db_manager.files["test-project-1"] = db_manager.files["test-project-1"][:1]

            export_manager = PJCTExportManager(db_manager)
            export_path = Path(tmpdir) / "export.pjt"
            export_manager.export_project("test-project-1", str(export_path))

            # List files
            import_manager = PJCTImportManager()
            success, files = import_manager.list_pjct_files(str(export_path))

            assert success
            assert files is not None
            assert len(files) > 0
            assert any("model.stl" in f for f in files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
