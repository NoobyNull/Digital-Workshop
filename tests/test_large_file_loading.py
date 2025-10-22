"""
Comprehensive testing suite for multi-threaded loading system with large files.

This module provides comprehensive testing for the improved loading system,
focusing on performance, stability, and UI responsiveness with large STL files.
"""

import time
import psutil
import threading
import unittest
import struct
from pathlib import Path

from src.gui.services.background_loading_manager import BackgroundLoadingManager
from src.core.logging_config import get_logger


class LargeFileLoadingTest(unittest.TestCase):
    """Test suite for large file loading functionality."""

    def setUp(self):
        """Set up test environment."""
        self.logger = get_logger(__name__)
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

        # Initialize background loading manager
        self.loading_manager = BackgroundLoadingManager(max_concurrent_jobs=2)

        # Test file sizes (in MB)
        self.test_sizes = [50, 100, 200, 500]

        # Performance targets (seconds)
        self.performance_targets = {
            50: 3.0,   # < 3 seconds for 50MB
            100: 5.0,  # < 5 seconds for 100MB
            200: 10.0, # < 10 seconds for 200MB
            500: 20.0  # < 20 seconds for 500MB
        }

    def tearDown(self):
        """Clean up test environment."""
        # Clean up test files
        for file_path in self.test_dir.glob("*.stl"):
            try:
                file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file_path}: {e}")

        # Shutdown loading manager
        if hasattr(self.loading_manager, 'executor'):
            self.loading_manager.executor.shutdown(wait=True)

    def _generate_large_stl_file(self, size_mb: int) -> Path:
        """
        Generate a large STL file for testing.

        Args:
            size_mb: Target file size in MB

        Returns:
            Path to generated file
        """
        file_path = self.test_dir / f"test_model_{size_mb}mb.stl"

        # Estimate triangles needed (rough approximation)
        # Binary STL: ~50 bytes per triangle
        triangles_per_mb = 1024 * 1024 // 50
        num_triangles = size_mb * triangles_per_mb

        # Generate a simple repeating pattern to reach target size
        with open(file_path, 'wb') as f:
            # Write header (80 bytes)
            header = f"Large Test STL - {size_mb}MB - Generated for testing".encode()
            f.write(header.ljust(80, b'\x00'))

            # Write triangle count
            f.write(num_triangles.to_bytes(4, byteorder='little'))

            # Generate triangles in a grid pattern
            for i in range(num_triangles):
                # Simple triangle pattern
                x = (i % 100) * 0.1
                y = ((i // 100) % 100) * 0.1
                z = (i // 10000) * 0.1

                # Normal vector (normalized)
                normal = (0.0, 0.0, 1.0)

                # Triangle vertices
                v1 = (x, y, z)
                v2 = (x + 0.1, y, z)
                v3 = (x, y + 0.1, z)

                # Write triangle data
                for coord in normal + v1 + v2 + v3:
                    f.write(struct.pack('<f', coord))

                # Attribute byte count
                f.write(b'\x00\x00')

        actual_size = file_path.stat().st_size / (1024 * 1024)
        self.logger.info(".2f")

        return file_path

    def _monitor_memory_usage(self, duration_seconds: int = 60) -> dict:
        """
        Monitor memory usage during a test period.

        Args:
            duration_seconds: Duration to monitor

        Returns:
            Memory usage statistics
        """
        process = psutil.Process()
        memory_readings = []

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            memory_mb = process.memory_info().rss / (1024 * 1024)
            memory_readings.append(memory_mb)
            time.sleep(0.1)

        return {
            'min_memory_mb': min(memory_readings),
            'max_memory_mb': max(memory_readings),
            'avg_memory_mb': sum(memory_readings) / len(memory_readings),
            'memory_variance': sum((x - sum(memory_readings)/len(memory_readings))**2 for x in memory_readings) / len(memory_readings)
        }

    def test_performance_with_large_files(self):
        """Test loading performance with various file sizes."""
        results = {}

        for size_mb in self.test_sizes:
            with self.subTest(file_size=size_mb):
                self.logger.info(f"Testing {size_mb}MB file performance")

                # Generate test file
                file_path = self._generate_large_stl_file(size_mb)

                # Test loading performance
                start_time = time.time()

                # Mock progress callback
                progress_updates = []
                def progress_callback(progress: float, message: str):
                    progress_updates.append((progress, message, time.time() - start_time))

                # Start background loading
                job_id = self.loading_manager.load_file_async(
                    str(file_path),
                    progress_callback=progress_callback
                )

                # Wait for completion with timeout
                timeout = self.performance_targets.get(size_mb, 30) * 2  # 2x target as timeout
                end_time = start_time + timeout

                while time.time() < end_time:
                    status = self.loading_manager.get_job_status(job_id)
                    if status and status['state'] in ['completed', 'failed', 'cancelled']:
                        break
                    time.sleep(0.1)

                load_time = time.time() - start_time
                status = self.loading_manager.get_job_status(job_id)

                results[size_mb] = {
                    'load_time_seconds': load_time,
                    'target_seconds': self.performance_targets.get(size_mb, 30),
                    'status': status['state'] if status else 'timeout',
                    'progress_updates': len(progress_updates),
                    'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                }

                # Assert performance targets
                if status and status['state'] == 'completed':
                    self.assertLess(load_time, self.performance_targets.get(size_mb, 30),
                                  f"Load time {load_time:.2f}s exceeded target for {size_mb}MB file")
                else:
                    self.fail(f"Loading failed for {size_mb}MB file: {status}")

                self.logger.info(f"{size_mb}MB file loaded in {load_time:.2f}s")

        # Log comprehensive results
        self.logger.info("Performance Test Results:")
        for size, result in results.items():
            self.logger.info(f"  {size}MB: {result['load_time_seconds']:.2f}s "
                           f"(target: {result['target_seconds']}s) - {result['status']}")

        return results

    def test_ui_responsiveness_during_loading(self):
        """Test that UI remains responsive during large file loading."""
        # Generate a large test file
        large_file = self._generate_large_stl_file(200)

        # Mock UI responsiveness test
        ui_events_processed = []
        ui_lock = threading.Lock()

        def simulate_ui_events():
            """Simulate UI event processing."""
            for i in range(100):  # Simulate 100 UI events
                with ui_lock:
                    ui_events_processed.append(time.time())
                time.sleep(0.01)  # 10ms between events

        # Start UI simulation in background
        ui_thread = threading.Thread(target=simulate_ui_events, daemon=True)
        ui_thread.start()

        # Start loading
        start_time = time.time()
        job_id = self.loading_manager.load_file_async(str(large_file))

        # Wait for completion
        while True:
            status = self.loading_manager.get_job_status(job_id)
            if status and status['state'] in ['completed', 'failed', 'cancelled']:
                break
            time.sleep(0.1)

        load_time = time.time() - start_time

        # Verify UI events were processed during loading
        with ui_lock:
            events_during_load = [t for t in ui_events_processed
                                if start_time <= t <= start_time + load_time]

        self.assertGreater(len(events_during_load), 50,
                          "UI should process at least 50 events during loading")

        # Check event timing distribution
        if len(events_during_load) > 1:
            intervals = [events_during_load[i+1] - events_during_load[i]
                        for i in range(len(events_during_load)-1)]
            avg_interval = sum(intervals) / len(intervals)
            self.assertLess(avg_interval, 0.05, "UI events should be processed regularly")

        self.logger.info(f"UI responsiveness test passed - {len(events_during_load)} events processed")

    def test_cancellation_functionality(self):
        """Test cancellation of large file loading operations."""
        # Generate large test file
        large_file = self._generate_large_stl_file(500)

        # Start loading
        job_id = self.loading_manager.load_file_async(str(large_file))

        # Wait a bit then cancel
        time.sleep(0.5)
        cancelled = self.loading_manager.cancel_loading(job_id)

        self.assertTrue(cancelled, "Cancellation should succeed")

        # Wait for cancellation to complete
        start_wait = time.time()
        while time.time() - start_wait < 5:  # Wait up to 5 seconds
            status = self.loading_manager.get_job_status(job_id)
            if status and status['state'] == 'cancelled':
                break
            time.sleep(0.1)

        status = self.loading_manager.get_job_status(job_id)
        self.assertEqual(status['state'], 'cancelled', "Job should be cancelled")

        # Verify cancellation was quick
        cancellation_time = time.time() - start_wait
        self.assertLess(cancellation_time, 1.0, "Cancellation should be quick")

        self.logger.info("Cancellation test passed")

    def test_memory_usage_stability(self):
        """Test memory usage remains stable during repeated loading operations."""
        # Generate test file
        test_file = self._generate_large_stl_file(100)

        memory_stats = []

        # Run loading operations multiple times
        for i in range(10):
            self.logger.info(f"Memory test iteration {i+1}/10")

            # Monitor memory during loading
            memory_monitor = self._monitor_memory_usage(duration_seconds=15)

            # Start loading
            job_id = self.loading_manager.load_file_async(str(test_file))

            # Wait for completion
            while True:
                status = self.loading_manager.get_job_status(job_id)
                if status and status['state'] in ['completed', 'failed', 'cancelled']:
                    break
                time.sleep(0.1)

            memory_stats.append(memory_monitor)

            # Clean up completed jobs
            self.loading_manager.cleanup_completed_jobs()

        # Analyze memory stability
        max_memories = [stat['max_memory_mb'] for stat in memory_stats]
        avg_memories = [stat['avg_memory_mb'] for stat in memory_stats]
        variances = [stat['memory_variance'] for stat in memory_stats]

        # Check memory doesn't grow significantly
        memory_growth = max(max_memories) - min(max_memories)
        self.assertLess(memory_growth, 100, "Memory usage should not grow by more than 100MB")

        # Check variance is reasonable
        avg_variance = sum(variances) / len(variances)
        self.assertLess(avg_variance, 50, "Memory variance should be reasonable")

        self.logger.info(f"Memory stability test passed - growth: {memory_growth:.1f}MB, "
                        f"avg variance: {avg_variance:.1f}")

    def test_concurrent_loading_scenarios(self):
        """Test loading multiple large files concurrently."""
        # Generate multiple test files
        test_files = []
        for size in [50, 100, 150]:
            test_files.append(self._generate_large_stl_file(size))

        # Start concurrent loading
        job_ids = []
        for file_path in test_files:
            job_id = self.loading_manager.load_file_async(str(file_path))
            job_ids.append(job_id)

        # Wait for all to complete
        start_time = time.time()
        completed_jobs = set()

        while len(completed_jobs) < len(job_ids) and time.time() - start_time < 120:  # 2 min timeout
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    status = self.loading_manager.get_job_status(job_id)
                    if status and status['state'] in ['completed', 'failed', 'cancelled']:
                        completed_jobs.add(job_id)
            time.sleep(0.1)

        total_time = time.time() - start_time

        # Verify all jobs completed
        self.assertEqual(len(completed_jobs), len(job_ids), "All concurrent jobs should complete")

        # Check that concurrent loading was faster than sequential
        # (This is a rough estimate - concurrent should be faster than sum of individual times)
        estimated_sequential = sum(self.performance_targets.get(50, 3) +
                                 self.performance_targets.get(100, 5) +
                                 self.performance_targets.get(150, 8))

        self.assertLess(total_time, estimated_sequential * 1.5,
                       "Concurrent loading should be reasonably faster than sequential")

        self.logger.info(f"Concurrent loading test passed - {len(job_ids)} jobs in {total_time:.2f}s")

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test with non-existent file
        job_id = self.loading_manager.load_file_async("non_existent_file.stl")

        # Wait for failure
        start_time = time.time()
        while time.time() - start_time < 10:
            status = self.loading_manager.get_job_status(job_id)
            if status and status['state'] == 'failed':
                break
            time.sleep(0.1)

        status = self.loading_manager.get_job_status(job_id)
        self.assertEqual(status['state'], 'failed', "Should fail with non-existent file")

        # Test error recovery suggestions
        error = Exception("File not found")
        suggestions = self.loading_manager.get_error_recovery_suggestions(error)

        self.assertGreater(len(suggestions), 0, "Should provide recovery suggestions")
        self.assertIn("Check file permissions", suggestions[0], "Should suggest checking permissions")

        # Test cleanup on error
        self.loading_manager.cleanup_on_error(job_id)

        # Verify job is cleaned up
        status_after_cleanup = self.loading_manager.get_job_status(job_id)
        self.assertIsNone(status_after_cleanup, "Job should be cleaned up after error")

        self.logger.info("Error handling test passed")


if __name__ == '__main__':
    # Set up logging for test output
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Run tests
    unittest.main(verbosity=2)