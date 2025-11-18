"""
Unit tests for ImportFileManager.

Tests cover:
- Root directory validation
- File management mode operations
- Duplicate detection
- File copying with progress
- Rollback functionality
- Error handling
- Memory stability
"""

import unittest
import tempfile
import shutil
import tracemalloc
from pathlib import Path
from typing import List

from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode,
    ImportFileInfo,
    ImportSession
)


class TestImportFileManager(unittest.TestCase):
    """Test cases for ImportFileManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ImportFileManager()
        self.temp_dir = tempfile.mkdtemp()
        self.test_files: List[str] = []

    def tearDown(self):
        """Clean up test files."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def create_test_file(self, size_mb: float, filename: str) -> str:
        """Create a test file of specified size."""
        file_path = Path(self.temp_dir) / filename
        size_bytes = int(size_mb * 1024 * 1024)

        with file_path.open('wb') as f:
            f.write(b'0' * size_bytes)

        self.test_files.append(str(file_path))
        return str(file_path)

    def test_initialization(self):
        """Test ImportFileManager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.fast_hasher)
        self.assertIsNotNone(self.manager.root_folder_manager)
        self.assertIsNone(self.manager.get_active_session())

    def test_validate_root_directory_leave_in_place(self):
        """Test root directory validation for leave in place mode."""
        is_valid, error = self.manager.validate_root_directory(
            None,
            FileManagementMode.LEAVE_IN_PLACE
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_root_directory_organized_no_directory(self):
        """Test root directory validation fails without directory."""
        is_valid, error = self.manager.validate_root_directory(
            None,
            FileManagementMode.KEEP_ORGANIZED
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("required", error.lower())

    def test_validate_root_directory_nonexistent(self):
        """Test root directory validation fails for nonexistent path."""
        is_valid, error = self.manager.validate_root_directory(
            "/nonexistent/path",
            FileManagementMode.KEEP_ORGANIZED
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_root_directory_auto_adds_new_root(self):
        """Test that a valid but non-configured root is auto-added and accepted."""
        temp_root = Path(self.temp_dir).resolve()

        is_valid, error = self.manager.validate_root_directory(
            str(temp_root),
            FileManagementMode.KEEP_ORGANIZED,
        )

        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # The temporary root should now be present in the configured roots
        configured = [Path(p).resolve() for p in self.manager.root_folder_manager.get_folder_paths(enabled_only=True)]
        self.assertIn(temp_root, configured)

    def test_get_organized_subdir(self):
        """Test subdirectory determination by file extension."""
        test_cases = {
            "model.stl": "STL_Files",
            "mesh.obj": "OBJ_Files",
            "part.step": "STEP_Files",
            "assembly.3mf": "3MF_Files",
            "unknown.xyz": "Other_Files"
        }

        for filename, expected_subdir in test_cases.items():
            file_path = str(Path(self.temp_dir) / filename)
            subdir = self.manager._get_organized_subdir(file_path)
            self.assertEqual(subdir, expected_subdir)

    def test_create_organized_path(self):
        """Test organized path creation."""
        test_file = "model.stl"
        organized_path = self.manager._create_organized_path(
            self.temp_dir,
            test_file,
            "abc123def456"
        )

        self.assertIn("STL_Files", str(organized_path))
        self.assertTrue(str(organized_path).endswith(".stl"))

    def test_create_organized_path_handles_conflicts(self):
        """Test organized path creation handles filename conflicts."""
        # Create first file
        subdir = Path(self.temp_dir) / "STL_Files"
        subdir.mkdir()
        existing = subdir / "hash123.stl"
        existing.touch()

        # Try to create another with same hash
        organized_path = self.manager._create_organized_path(
            self.temp_dir,
            "model.stl",
            "hash123"
        )

        # Should have conflict resolution (e.g., hash123_1.stl)
        self.assertNotEqual(str(organized_path), str(existing))

    def test_start_import_session_leave_in_place(self):
        """Test starting import session in leave in place mode."""
        test_file = self.create_test_file(1.0, "test.stl")

        success, error, session = self.manager.start_import_session(
            [test_file],
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNotNone(session)
        self.assertEqual(len(session.files), 1)
        self.assertEqual(session.mode, FileManagementMode.LEAVE_IN_PLACE)
        self.assertEqual(session.status, "running")

    def test_start_import_session_no_valid_files(self):
        """Test starting import session with no valid files."""
        success, error, _ = self.manager.start_import_session(
            ["/nonexistent/file.stl"],
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn("no valid files", error.lower())

    def test_process_file_leave_in_place(self):
        """Test processing file in leave in place mode."""
        test_file = self.create_test_file(0.5, "test.stl")

        success, error, session = self.manager.start_import_session(
            [test_file],
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertTrue(success)
        file_info = session.files[0]

        # Process the file
        progress_calls = []
        def progress_callback(msg, percent):
            progress_calls.append((msg, percent))

        success, error = self.manager.process_file(
            file_info,
            session,
            progress_callback=progress_callback
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(file_info.import_status, "completed")
        self.assertEqual(file_info.progress_percent, 100)
        self.assertIsNotNone(file_info.file_hash)
        self.assertEqual(file_info.managed_path, file_info.original_path)
        self.assertGreater(len(progress_calls), 0)

    def test_process_file_without_cancellation(self):
        """Test processing file without cancellation token."""
        test_file = self.create_test_file(0.5, "small.stl")

        success, error, session = self.manager.start_import_session(
            [test_file],
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertTrue(success)
        file_info = session.files[0]

        # Process without cancellation token (None)
        success, error = self.manager.process_file(
            file_info,
            session,
            cancellation_token=None  # No token provided
        )

        # Should succeed
        self.assertTrue(success, f"Expected success but got error: {error}")
        self.assertIsNone(error)
        self.assertEqual(file_info.import_status, "completed")

    def test_check_duplicate(self):
        """Test duplicate detection."""
        test_hash = "abc123def456"
        existing_file = {"id": 1, "path": "/existing/file.stl"}

        existing_hashes = {
            test_hash: existing_file
        }

        # Check duplicate
        is_dup, existing = self.manager.check_duplicate(test_hash, existing_hashes)
        self.assertTrue(is_dup)
        self.assertEqual(existing, existing_file)

        # Check non-duplicate
        is_dup, existing = self.manager.check_duplicate("different", existing_hashes)
        self.assertFalse(is_dup)
        self.assertIsNone(existing)

    def test_rollback_session_empty(self):
        """Test rollback with empty session."""
        session = ImportSession(
            session_id="test_session",
            mode=FileManagementMode.LEAVE_IN_PLACE
        )

        result = self.manager.rollback_session(session)
        self.assertTrue(result)

    def test_complete_import_session(self):
        """Test completing import session."""
        test_file = self.create_test_file(1.0, "test.stl")

        success, _, session = self.manager.start_import_session(
            [test_file],
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertTrue(success)

        # Process file
        file_info = session.files[0]
        self.manager.process_file(file_info, session)

        # Complete session
        result = self.manager.complete_import_session(session, success=True)

        self.assertTrue(result.success)
        self.assertEqual(result.total_files, 1)
        self.assertEqual(result.processed_files, 1)
        self.assertEqual(result.failed_files, 0)
        self.assertGreater(result.duration_seconds, 0)
        self.assertIsNone(self.manager.get_active_session())

    def test_memory_stability(self):
        """Test memory stability over multiple operations."""
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # Perform multiple import operations
        for i in range(10):
            test_file = self.create_test_file(0.5, f"test_{i}.stl")

            success, _, session = self.manager.start_import_session(
                [test_file],
                FileManagementMode.LEAVE_IN_PLACE
            )

            if success:
                file_info = session.files[0]
                self.manager.process_file(file_info, session)
                self.manager.complete_import_session(session, success=True)

        final_memory = tracemalloc.get_traced_memory()[0]
        memory_growth = final_memory - initial_memory
        memory_growth_mb = memory_growth / (1024 * 1024)

        tracemalloc.stop()

        # Memory growth should be reasonable (< 50MB for 10 operations)
        self.assertLess(memory_growth_mb, 50,
                       f"Excessive memory growth: {memory_growth_mb:.2f} MB")

    def test_copy_file_with_progress(self):
        """Test file copying with progress tracking."""
        # Create source file
        source = Path(self.temp_dir) / "source.stl"
        source.write_bytes(b'0' * (1024 * 1024))  # 1MB

        # Create destination
        dest_dir = Path(self.temp_dir) / "dest"
        dest_dir.mkdir()
        dest = dest_dir / "copied.stl"

        # Track progress
        progress_values = []
        def progress_callback(percent):
            progress_values.append(percent)

        # Copy file
        self.manager._copy_file_with_progress(
            source,
            dest,
            progress_callback
        )

        # Verify file was copied
        self.assertTrue(dest.exists())
        self.assertEqual(dest.stat().st_size, source.stat().st_size)

        # Verify progress was reported
        self.assertGreater(len(progress_values), 0)
        self.assertEqual(max(progress_values), 100)

    def test_error_handling_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        session = ImportSession(
            session_id="test",
            mode=FileManagementMode.LEAVE_IN_PLACE
        )

        file_info = ImportFileInfo(
            original_path="/nonexistent/file.stl",
            file_size=1000
        )
        session.files.append(file_info)

        success, error = self.manager.process_file(file_info, session)

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertEqual(file_info.import_status, "failed")
        self.assertIsNotNone(file_info.error_message)


class TestImportFileManagerIntegration(unittest.TestCase):
    """Integration tests for ImportFileManager with real components."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ImportFileManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_full_import_workflow(self):
        """Test complete import workflow."""
        # Create test files
        test_files = []
        for i in range(3):
            file_path = Path(self.temp_dir) / f"model_{i}.stl"
            file_path.write_bytes(b'0' * (100 * 1024))  # 100KB
            test_files.append(str(file_path))

        # Start session
        success, error, session = self.manager.start_import_session(
            test_files,
            FileManagementMode.LEAVE_IN_PLACE
        )

        self.assertTrue(success)
        self.assertIsNotNone(session)

        # Process all files
        for file_info in session.files:
            success, error = self.manager.process_file(file_info, session)
            self.assertTrue(success, f"Failed to process file: {error}")

        # Complete session
        result = self.manager.complete_import_session(session, success=True)

        self.assertTrue(result.success)
        self.assertEqual(result.total_files, 3)
        self.assertEqual(result.processed_files, 3)
        self.assertEqual(result.failed_files, 0)

        # Verify all files have hashes
        for file_info in session.files:
            self.assertIsNotNone(file_info.file_hash)
            self.assertEqual(file_info.import_status, "completed")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestImportFileManager))
    suite.addTests(loader.loadTestsFromTestCase(TestImportFileManagerIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    sys.exit(0 if run_tests() else 1)
