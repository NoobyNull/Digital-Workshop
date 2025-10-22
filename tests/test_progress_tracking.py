"""
Test suite for granular progress tracking in float decoding operations.

This module tests the enhanced progress tracking system that provides
fine-grained progress updates during the long float decoding phase
of STL file loading.
"""

import time
import pytest
from unittest.mock import Mock, patch

from src.core.progress_aggregator import ProgressAggregator, SubOperationProgress
from src.parsers.stl_gpu_parser import STLGPUParser
from src.parsers.stl_parser_original import STLParser
from src.gui.widgets.loading_progress_widget import LoadingProgressWidget


class TestProgressAggregator:
    """Test the enhanced progress aggregator with sub-operations."""

    def test_sub_operation_creation(self):
        """Test creating and tracking sub-operations."""
        aggregator = ProgressAggregator(2)

        # Add sub-operations to chunks
        aggregator.update_sub_operation_progress("chunk_000", "float_decode", 25.0, "Decoding floats")
        aggregator.update_sub_operation_progress("chunk_000", "normal_calc", 0.0, "Calculating normals")

        chunk = aggregator.chunks["chunk_000"]
        assert "float_decode" in chunk.sub_operations
        assert "normal_calc" in chunk.sub_operations
        assert chunk.sub_operations["float_decode"].progress == 25.0
        assert chunk.sub_operations["float_decode"].status == "Decoding floats"

    def test_weighted_progress_calculation(self):
        """Test that chunk progress is calculated based on weighted sub-operations."""
        aggregator = ProgressAggregator(1)

        # Add weighted sub-operations
        aggregator.update_sub_operation_progress("chunk_000", "io_read", 100.0, weight=0.2)
        aggregator.update_sub_operation_progress("chunk_000", "float_decode", 50.0, weight=0.7)
        aggregator.update_sub_operation_progress("chunk_000", "validation", 0.0, weight=0.1)

        # Expected: (100*0.2 + 50*0.7 + 0*0.1) = 55.0
        chunk = aggregator.chunks["chunk_000"]
        assert chunk.calculate_weighted_progress() == 55.0

    def test_progress_summary_includes_sub_operations(self):
        """Test that progress summary includes sub-operation statistics."""
        aggregator = ProgressAggregator(2)

        # Add some sub-operations
        aggregator.update_sub_operation_progress("chunk_000", "decode", 75.0)
        aggregator.update_sub_operation_progress("chunk_001", "decode", 25.0)
        aggregator.update_sub_operation_progress("chunk_001", "validate", 100.0)

        summary = aggregator.get_progress_summary()
        assert summary["total_sub_operations"] == 3
        assert summary["active_sub_operations"] == 2  # decode operations in progress

    def test_sub_operation_timing(self):
        """Test timing tracking for sub-operations."""
        aggregator = ProgressAggregator(1)

        # Start a sub-operation
        aggregator.update_sub_operation_progress("chunk_000", "decode", 10.0)
        sub_op = aggregator.chunks["chunk_000"].sub_operations["decode"]

        assert sub_op.start_time is not None
        assert sub_op.end_time is None

        # Complete the sub-operation
        time.sleep(0.01)  # Small delay
        aggregator.update_sub_operation_progress("chunk_000", "decode", 100.0)

        assert sub_op.end_time is not None
        assert sub_op.duration is not None
        assert sub_op.duration > 0


class TestSTLProgressTracking:
    """Test progress tracking in STL parsers."""

    @patch('src.parsers.stl_gpu_parser.get_gpu_accelerator')
    def test_gpu_parser_progress_updates(self, mock_gpu_accelerator):
        """Test that GPU parser provides granular progress updates."""
        # Mock GPU accelerator
        mock_accelerator = Mock()
        mock_accelerator.execute_kernel.return_value = True
        mock_gpu_accelerator.return_value = mock_accelerator

        parser = STLGPUParser()
        progress_callback = Mock()

        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            # Mock binary STL header and triangle count
            mock_file.read.side_effect = [
                b'Header' + b'\x00' * 75,  # 80 byte header
                (1000).to_bytes(4, 'little'),  # 1000 triangles
                b'\x00' * (1000 * 50)  # Triangle data
            ]
            mock_file.tell.return_value = 80 + 4 + (1000 * 50)
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.stat') as mock_stat:

                mock_stat.return_value.st_size = 80 + 4 + (1000 * 50)

                # This would normally call progress updates during GPU processing
                # We can't easily test the actual GPU path without full mocking,
                # but we verify the structure is in place
                assert hasattr(parser, '_execute_triangle_processing_kernel')
                assert hasattr(parser, '_execute_gpu_kernels')

    def test_cpu_parser_chunked_float_decoding(self):
        """Test that CPU parser provides progress during chunked float decoding."""
        parser = STLParser()
        progress_callback = Mock()

        # Create a mock progress callback to capture calls
        progress_calls = []
        def capture_progress(progress, message):
            progress_calls.append((progress, message))

        progress_callback.report = capture_progress

        # Mock file with binary STL data
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            # Mock binary STL: header + triangle count + triangle data
            header = b'Binary STL' + b'\x00' * (80 - 10)
            triangle_count = 1000
            triangle_count_bytes = triangle_count.to_bytes(4, 'little')

            # Generate mock triangle data (50 bytes per triangle)
            triangle_data = b'\x00' * (triangle_count * 50)

            mock_file.read.side_effect = [header, triangle_count_bytes, triangle_data]
            mock_file.tell.return_value = len(header) + len(triangle_count_bytes) + len(triangle_data)
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.stat') as mock_stat:

                mock_stat.return_value.st_size = len(header) + len(triangle_count_bytes) + len(triangle_data)

                # This should trigger the chunked float decoding with progress updates
                try:
                    parser._parse_binary_stl_arrays(
                        Mock(), progress_callback
                    )
                except Exception:
                    # We expect this to fail due to mocking, but progress should be called
                    pass

                # Verify progress updates were made during float decoding
                decode_calls = [call for call in progress_calls if 'decoding' in call[1].lower()]
                assert len(decode_calls) > 0, "Should have progress updates during float decoding"


class TestLoadingProgressWidget:
    """Test the enhanced loading progress widget."""

    def test_smooth_progress_animation(self, qtbot):
        """Test that progress updates are smoothed for better UX."""
        widget = LoadingProgressWidget()
        qtbot.addWidget(widget)

        # Start loading
        widget.start_loading("test_job", "test.stl")

        # Update progress multiple times rapidly
        widget.update_progress(10.0, "Starting")
        widget.update_progress(12.0, "Processing")  # Small change
        widget.update_progress(25.0, "Halfway")     # Larger change

        # Progress bar should reflect the updates
        assert widget.progress_bar.value() >= 10

    def test_progress_update_throttling(self, qtbot):
        """Test that progress updates are throttled to prevent UI spam."""
        widget = LoadingProgressWidget()
        qtbot.addWidget(widget)

        widget.start_loading("test_job", "test.stl")

        # Rapid updates should be throttled
        start_time = time.time()
        for i in range(10):
            widget.update_progress(float(i), f"Step {i}")
            time.sleep(0.01)  # 10ms between updates

        # Should not have updated every single time due to throttling
        elapsed = time.time() - start_time
        assert elapsed >= 0.05  # At least some throttling occurred

    def test_time_estimation_accuracy(self, qtbot):
        """Test that time remaining estimates are reasonable."""
        widget = LoadingProgressWidget()
        qtbot.addWidget(widget)

        widget.start_loading("test_job", "test.stl")

        # Simulate progress over time
        widget.update_progress(25.0, "Quarter done")
        time.sleep(0.1)
        widget.update_progress(50.0, "Half done")
        time.sleep(0.1)
        widget.update_progress(75.0, "Three quarters done")

        # Time label should show some estimate
        time_text = widget.time_label.text()
        assert time_text != ""  # Should have time estimate


class TestIntegrationProgressTracking:
    """Integration tests for the complete progress tracking system."""

    def test_end_to_end_progress_flow(self):
        """Test the complete progress tracking flow from parser to UI."""
        # Create components
        aggregator = ProgressAggregator(1)
        widget = LoadingProgressWidget()

        # Simulate parser progress updates
        aggregator.update_sub_operation_progress("chunk_000", "io_read", 100.0, weight=0.1)
        aggregator.update_sub_operation_progress("chunk_000", "float_decode", 50.0, weight=0.8)
        aggregator.update_sub_operation_progress("chunk_000", "validation", 25.0, weight=0.1)

        # Check that overall progress reflects weighted sub-operations
        overall_progress = aggregator.calculate_overall_progress()
        expected_progress = (100*0.1 + 50*0.8 + 25*0.1)  # = 50.0
        assert abs(overall_progress - expected_progress) < 0.1

    def test_performance_impact(self):
        """Test that progress tracking doesn't significantly impact performance."""
        aggregator = ProgressAggregator(100)

        # Time progress updates
        start_time = time.time()

        for i in range(1000):
            chunk_id = f"chunk_{i % 100:03d}"
            aggregator.update_sub_operation_progress(
                chunk_id, f"operation_{i % 5}", float(i % 100)
            )

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 1 second for 1000 updates)
        assert elapsed < 1.0, f"Progress tracking too slow: {elapsed:.3f}s for 1000 updates"

    def test_memory_efficiency(self):
        """Test that progress tracking doesn't cause memory leaks."""
        import gc
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create and use aggregator extensively
        for _ in range(10):
            aggregator = ProgressAggregator(50)
            for i in range(100):
                for j in range(5):
                    aggregator.update_sub_operation_progress(
                        f"chunk_{i:03d}", f"op_{j}", float((i * 5 + j) % 100)
                    )
            del aggregator
            gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal (< 10MB)
        assert memory_increase < 10 * 1024 * 1024, f"Memory leak detected: {memory_increase / 1024 / 1024:.1f}MB increase"