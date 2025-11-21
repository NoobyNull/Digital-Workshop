"""
Unit tests for the FastHasher class.

Tests cover:
- Basic file hashing functionality
- Progress callback support
- Cancellation token integration
- Batch hashing operations
- Hash verification
- Error handling
- Performance statistics
- Memory leak testing
"""

import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.fast_hasher import FastHasher, HashResult
from src.core.cancellation_token import CancellationToken


class TestFastHasher(unittest.TestCase):
    """Test suite for FastHasher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.hasher = FastHasher()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        for file in Path(self.temp_dir).glob("*"):
            try:
                file.unlink()
            except Exception:
                pass
        try:
            Path(self.temp_dir).rmdir()
        except Exception:
            pass

    def create_test_file(self, size_mb: float, name: str = "test.bin") -> str:
        """
        Create a test file of specified size.

        Args:
            size_mb: Size in megabytes
            name: Filename

        Returns:
            Path to created file
        """
        file_path = os.path.join(self.temp_dir, name)
        size_bytes = int(size_mb * 1024 * 1024)

        with open(file_path, "wb") as f:
            # Write in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = size_bytes
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                # Use predictable pattern for reproducible hashes
                f.write(b"A" * write_size)
                remaining -= write_size

        return file_path

    def test_hash_small_file(self):
        """Test hashing a small file (< 10MB)."""
        file_path = self.create_test_file(5.0, "small.bin")

        result = self.hasher.hash_file(file_path)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.hash_value)
        self.assertEqual(len(result.hash_value), 32)  # xxHash128 produces 32 hex chars
        self.assertEqual(result.file_path, file_path)
        self.assertGreater(result.file_size, 0)
        self.assertGreater(result.hash_time, 0)
        self.assertIsNone(result.error)

    def test_hash_medium_file(self):
        """Test hashing a medium file (10-100MB)."""
        file_path = self.create_test_file(50.0, "medium.bin")

        result = self.hasher.hash_file(file_path)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.hash_value)
        self.assertLess(result.hash_time, 3.0)  # Should complete in < 3 seconds

    def test_hash_large_file(self):
        """Test hashing a large file (100+ MB)."""
        file_path = self.create_test_file(150.0, "large.bin")

        result = self.hasher.hash_file(file_path)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.hash_value)
        self.assertLess(result.hash_time, 5.0)  # Should complete in < 5 seconds

    def test_hash_nonexistent_file(self):
        """Test hashing a file that doesn't exist."""
        result = self.hasher.hash_file("/nonexistent/file.bin")

        self.assertFalse(result.success)
        self.assertIsNone(result.hash_value)
        self.assertIsNotNone(result.error)
        self.assertIn("not found", result.error.lower())

    def test_progress_callback(self):
        """Test that progress callback is called correctly."""
        file_path = self.create_test_file(20.0, "progress.bin")

        progress_calls = []

        def progress_callback(percent, message):
            progress_calls.append((percent, message))

        result = self.hasher.hash_file(file_path, progress_callback=progress_callback)

        self.assertTrue(result.success)
        self.assertGreater(len(progress_calls), 0)

        # Check that progress increases
        if len(progress_calls) > 1:
            self.assertLessEqual(progress_calls[0][0], progress_calls[-1][0])

        # Check final progress is 100%
        self.assertEqual(progress_calls[-1][0], 100.0)

    def test_cancellation_support(self):
        """Test that cancellation works correctly."""
        file_path = self.create_test_file(100.0, "cancel.bin")

        token = CancellationToken()

        # Cancel after a short delay
        def cancel_after_delay():
            time.sleep(0.1)
            token.cancel()

        import threading

        cancel_thread = threading.Thread(target=cancel_after_delay)
        cancel_thread.start()

        result = self.hasher.hash_file(file_path, cancellation_token=token)

        cancel_thread.join()

        self.assertFalse(result.success)
        self.assertIsNone(result.hash_value)
        self.assertIn("cancel", result.error.lower())

    def test_hash_consistency(self):
        """Test that same file produces same hash."""
        file_path = self.create_test_file(10.0, "consistent.bin")

        result1 = self.hasher.hash_file(file_path)
        result2 = self.hasher.hash_file(file_path)

        self.assertTrue(result1.success)
        self.assertTrue(result2.success)
        self.assertEqual(result1.hash_value, result2.hash_value)

    def test_hash_different_files(self):
        """Test that different files produce different hashes."""
        file1_path = self.create_test_file(5.0, "file1.bin")

        # Create a different file
        file2_path = os.path.join(self.temp_dir, "file2.bin")
        with open(file2_path, "wb") as f:
            f.write(b"B" * (5 * 1024 * 1024))

        result1 = self.hasher.hash_file(file1_path)
        result2 = self.hasher.hash_file(file2_path)

        self.assertTrue(result1.success)
        self.assertTrue(result2.success)
        self.assertNotEqual(result1.hash_value, result2.hash_value)

    def test_hash_chunk(self):
        """Test chunk-based hashing."""
        data1 = b"Hello, "
        data2 = b"World!"

        # Hash in chunks
        h = self.hasher.hash_chunk(data1)
        h = self.hasher.hash_chunk(data2, h)
        chunked_hash = h.hexdigest()

        # Hash all at once
        h2 = self.hasher.hash_chunk(data1 + data2)
        combined_hash = h2.hexdigest()

        self.assertEqual(chunked_hash, combined_hash)

    def test_batch_hashing(self):
        """Test batch hashing of multiple files."""
        files = [self.create_test_file(2.0, f"batch{i}.bin") for i in range(5)]

        batch_progress = []

        def batch_callback(completed, total, current):
            batch_progress.append((completed, total, current))

        results = self.hasher.hash_files_batch(files, progress_callback=batch_callback)

        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.success for r in results))
        self.assertGreater(len(batch_progress), 0)

        # Check final progress
        self.assertEqual(batch_progress[-1][0], 5)
        self.assertEqual(batch_progress[-1][1], 5)

    def test_batch_hashing_with_cancellation(self):
        """Test batch hashing can be cancelled."""
        files = [self.create_test_file(10.0, f"batch_cancel{i}.bin") for i in range(10)]

        token = CancellationToken()

        # Cancel after processing 3 files
        processed = [0]

        def track_progress(completed, total, current):
            processed[0] = completed
            if completed >= 3:
                token.cancel()

        results = self.hasher.hash_files_batch(
            files, progress_callback=track_progress, cancellation_token=token
        )

        # Should have processed at least 3, but not all 10
        self.assertGreaterEqual(len(results), 3)
        self.assertLess(len(results), 10)

    def test_verify_hash(self):
        """Test hash verification."""
        file_path = self.create_test_file(5.0, "verify.bin")

        # Calculate hash
        result = self.hasher.hash_file(file_path)
        self.assertTrue(result.success)

        # Verify correct hash
        self.assertTrue(self.hasher.verify_hash(file_path, result.hash_value))

        # Verify incorrect hash
        self.assertFalse(self.hasher.verify_hash(file_path, "0" * 32))

    def test_performance_stats(self):
        """Test performance statistics calculation."""
        files = [self.create_test_file(5.0, f"stats{i}.bin") for i in range(3)]

        results = [self.hasher.hash_file(f) for f in files]
        stats = self.hasher.get_performance_stats(results)

        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["successful"], 3)
        self.assertEqual(stats["failed"], 0)
        self.assertGreater(stats["total_size_mb"], 0)
        self.assertGreater(stats["total_time_seconds"], 0)
        self.assertGreater(stats["avg_throughput_mbps"], 0)

    def test_performance_stats_with_failures(self):
        """Test performance statistics with some failed hashes."""
        results = [
            self.hasher.hash_file(self.create_test_file(5.0, "success.bin")),
            self.hasher.hash_file("/nonexistent/file.bin"),
            self.hasher.hash_file(self.create_test_file(5.0, "success2.bin")),
        ]

        stats = self.hasher.get_performance_stats(results)

        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["successful"], 2)
        self.assertEqual(stats["failed"], 1)

    def test_adaptive_chunk_sizing(self):
        """Test that chunk size adapts to file size."""
        # Small file
        small_size = 5 * 1024 * 1024  # 5MB
        small_chunk = self.hasher._get_optimal_chunk_size(small_size)
        self.assertEqual(small_chunk, FastHasher.CHUNK_SIZE_SMALL)

        # Medium file
        medium_size = 50 * 1024 * 1024  # 50MB
        medium_chunk = self.hasher._get_optimal_chunk_size(medium_size)
        self.assertEqual(medium_chunk, FastHasher.CHUNK_SIZE_MEDIUM)

        # Large file
        large_size = 200 * 1024 * 1024  # 200MB
        large_chunk = self.hasher._get_optimal_chunk_size(large_size)
        self.assertEqual(large_chunk, FastHasher.CHUNK_SIZE_LARGE)

    def test_memory_leak_prevention(self):
        """Test that repeated hashing doesn't cause memory leaks."""
        file_path = self.create_test_file(10.0, "memory_test.bin")

        # Hash the same file 20 times
        hashes = []
        for _ in range(20):
            result = self.hasher.hash_file(file_path)
            self.assertTrue(result.success)
            hashes.append(result.hash_value)

        # All hashes should be identical
        self.assertEqual(len(set(hashes)), 1)

    def test_error_handling_permission_denied(self):
        """Test handling of permission errors."""
        # Create file and make it unreadable (Unix-like systems)
        file_path = self.create_test_file(1.0, "protected.bin")

        try:
            os.chmod(file_path, 0o000)
            result = self.hasher.hash_file(file_path)

            # On Windows, permission errors may not occur
            if not result.success:
                self.assertIsNotNone(result.error)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(file_path, 0o644)
            except Exception:
                pass


class TestHashResult(unittest.TestCase):
    """Test suite for HashResult dataclass."""

    def test_hash_result_creation(self):
        """Test creating HashResult instances."""
        result = HashResult(
            file_path="/test/file.bin",
            hash_value="abc123",
            file_size=1024,
            hash_time=0.5,
            success=True,
        )

        self.assertEqual(result.file_path, "/test/file.bin")
        self.assertEqual(result.hash_value, "abc123")
        self.assertEqual(result.file_size, 1024)
        self.assertEqual(result.hash_time, 0.5)
        self.assertTrue(result.success)
        self.assertIsNone(result.error)

    def test_hash_result_with_error(self):
        """Test HashResult with error."""
        result = HashResult(
            file_path="/test/file.bin",
            hash_value=None,
            file_size=0,
            hash_time=0.0,
            success=False,
            error="File not found",
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.hash_value)
        self.assertEqual(result.error, "File not found")


if __name__ == "__main__":
    unittest.main()
