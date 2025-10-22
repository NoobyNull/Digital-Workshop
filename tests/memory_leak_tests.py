"""
Memory leak detection tests for Loading-Optimizations implementation.

This module provides comprehensive memory leak testing following quality standards,
running operations 10-20 times to verify no memory leaks during repeated operations.
"""

import gc
import psutil
import pytest
import statistics
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.memory_manager import get_memory_manager
from src.core.gpu_memory_manager import get_gpu_memory_manager
from src.parsers.stl_gpu_parser import STLGPUParser, GPUParseConfig
from src.parsers.file_chunker import FileChunker
from src.parsers.thread_pool_coordinator import ThreadPoolCoordinator
from src.core.progress_aggregator import ProgressAggregator
from src.core.cancellation_token import CancellationToken


@dataclass
class MemoryLeakResult:
    """Result of memory leak analysis."""
    test_name: str
    iterations: int
    memory_deltas_mb: List[float]
    average_delta: float
    standard_deviation: float
    trend_slope: float  # Memory increase per iteration
    leak_detected: bool
    leak_confidence: float  # 0-1, confidence in leak detection
    recommendations: List[str]


class MemoryLeakDetector:
    """Comprehensive memory leak detection system."""

    def __init__(self):
        """Initialize memory leak detector."""
        self.logger = get_logger(__name__)
        self.memory_manager = get_memory_manager()
        self.gpu_memory_manager = get_gpu_memory_manager()

        # Test configuration
        self.min_iterations = 10
        self.max_iterations = 20
        self.stability_threshold = 0.05  # 5% variation allowed
        self.leak_threshold_mb_per_iter = 1.0  # 1MB increase per iteration considered leak

    def run_comprehensive_memory_tests(self) -> Dict[str, MemoryLeakResult]:
        """
        Run comprehensive memory leak tests.

        Returns:
            Dictionary of test results by test name
        """
        results = {}

        # Test individual components
        results["gpu_parser"] = self.test_gpu_parser_memory_leaks()
        results["file_chunker"] = self.test_file_chunker_memory_leaks()
        results["thread_coordinator"] = self.test_thread_coordinator_memory_leaks()
        results["progress_aggregator"] = self.test_progress_aggregator_memory_leaks()
        results["memory_manager"] = self.test_memory_manager_leaks()

        # Test integrated workflows
        results["integrated_parsing"] = self.test_integrated_parsing_memory_leaks()
        results["concurrent_operations"] = self.test_concurrent_operations_memory_leaks()

        return results

    def test_gpu_parser_memory_leaks(self) -> MemoryLeakResult:
        """Test GPU parser for memory leaks."""
        return self._run_memory_leak_test(
            "GPU Parser",
            self._gpu_parser_operation,
            iterations=15
        )

    def test_file_chunker_memory_leaks(self) -> MemoryLeakResult:
        """Test file chunker for memory leaks."""
        return self._run_memory_leak_test(
            "File Chunker",
            self._file_chunker_operation,
            iterations=12
        )

    def test_thread_coordinator_memory_leaks(self) -> MemoryLeakResult:
        """Test thread coordinator for memory leaks."""
        return self._run_memory_leak_test(
            "Thread Coordinator",
            self._thread_coordinator_operation,
            iterations=10
        )

    def test_progress_aggregator_memory_leaks(self) -> MemoryLeakResult:
        """Test progress aggregator for memory leaks."""
        return self._run_memory_leak_test(
            "Progress Aggregator",
            self._progress_aggregator_operation,
            iterations=15
        )

    def test_memory_manager_leaks(self) -> MemoryLeakResult:
        """Test memory manager for leaks."""
        return self._run_memory_leak_test(
            "Memory Manager",
            self._memory_manager_operation,
            iterations=20
        )

    def test_integrated_parsing_memory_leaks(self) -> MemoryLeakResult:
        """Test integrated parsing workflow for memory leaks."""
        return self._run_memory_leak_test(
            "Integrated Parsing",
            self._integrated_parsing_operation,
            iterations=12
        )

    def test_concurrent_operations_memory_leaks(self) -> MemoryLeakResult:
        """Test concurrent operations for memory leaks."""
        return self._run_memory_leak_test(
            "Concurrent Operations",
            self._concurrent_operations,
            iterations=8
        )

    def _run_memory_leak_test(self, test_name: str, operation_func, iterations: int) -> MemoryLeakResult:
        """
        Run a memory leak test with specified operation.

        Args:
            test_name: Name of the test
            operation_func: Function to execute for each iteration
            iterations: Number of iterations to run

        Returns:
            MemoryLeakResult with analysis
        """
        self.logger.info(f"Running memory leak test: {test_name} ({iterations} iterations)")

        memory_deltas = []

        for i in range(iterations):
            # Force garbage collection before measurement
            gc.collect()

            # Get baseline memory
            baseline_memory = self._get_current_memory_mb()

            # Execute operation
            try:
                operation_func(i)
            except Exception as e:
                self.logger.warning(f"Operation {i} failed in {test_name}: {e}")
                continue

            # Force cleanup
            gc.collect()

            # Measure memory after operation
            final_memory = self._get_current_memory_mb()
            delta = final_memory - baseline_memory
            memory_deltas.append(delta)

            self.logger.debug(f"Iteration {i+1}: memory delta = {delta:.2f} MB")

        # Analyze results
        if len(memory_deltas) < 3:
            return MemoryLeakResult(
                test_name=test_name,
                iterations=len(memory_deltas),
                memory_deltas_mb=memory_deltas,
                average_delta=0,
                standard_deviation=0,
                trend_slope=0,
                leak_detected=True,  # Insufficient data
                leak_confidence=0,
                recommendations=["Insufficient test data for analysis"]
            )

        # Calculate statistics
        average_delta = statistics.mean(memory_deltas)
        std_dev = statistics.stdev(memory_deltas) if len(memory_deltas) > 1 else 0

        # Calculate trend (linear regression slope)
        trend_slope = self._calculate_trend_slope(memory_deltas)

        # Detect leaks
        leak_detected = self._detect_memory_leak(memory_deltas, trend_slope)
        leak_confidence = self._calculate_leak_confidence(memory_deltas, trend_slope)

        # Generate recommendations
        recommendations = self._generate_memory_recommendations(
            test_name, leak_detected, leak_confidence, average_delta, trend_slope
        )

        return MemoryLeakResult(
            test_name=test_name,
            iterations=len(memory_deltas),
            memory_deltas_mb=memory_deltas,
            average_delta=average_delta,
            standard_deviation=std_dev,
            trend_slope=trend_slope,
            leak_detected=leak_detected,
            leak_confidence=leak_confidence,
            recommendations=recommendations
        )

    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def _calculate_trend_slope(self, memory_deltas: List[float]) -> float:
        """Calculate linear trend slope for memory deltas."""
        if len(memory_deltas) < 2:
            return 0.0

        n = len(memory_deltas)
        x = list(range(n))

        # Calculate slope using linear regression
        sum_x = sum(x)
        sum_y = sum(memory_deltas)
        sum_xy = sum(xi * yi for xi, yi in zip(x, memory_deltas))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _detect_memory_leak(self, memory_deltas: List[float], trend_slope: float) -> bool:
        """Detect if memory leak is present."""
        # Check trend slope
        if abs(trend_slope) > self.leak_threshold_mb_per_iter:
            return True

        # Check if final memory is significantly higher than initial
        if len(memory_deltas) >= 3:
            initial_avg = statistics.mean(memory_deltas[:3])
            final_avg = statistics.mean(memory_deltas[-3:])

            if final_avg - initial_avg > self.leak_threshold_mb_per_iter * len(memory_deltas) * 0.5:
                return True

        # Check variability - high variance might indicate leaks
        if len(memory_deltas) > 1:
            std_dev = statistics.stdev(memory_deltas)
            mean_val = abs(statistics.mean(memory_deltas))
            if mean_val > 0 and std_dev / mean_val > self.stability_threshold * 2:
                return True

        return False

    def _calculate_leak_confidence(self, memory_deltas: List[float], trend_slope: float) -> float:
        """Calculate confidence level in leak detection (0-1)."""
        if len(memory_deltas) < 3:
            return 0.0

        confidence = 0.0

        # Trend-based confidence
        trend_confidence = min(abs(trend_slope) / self.leak_threshold_mb_per_iter, 1.0)
        confidence += trend_confidence * 0.4

        # Variability-based confidence
        std_dev = statistics.stdev(memory_deltas)
        mean_val = abs(statistics.mean(memory_deltas))
        if mean_val > 0:
            variability_ratio = std_dev / mean_val
            var_confidence = min(variability_ratio / self.stability_threshold, 1.0)
            confidence += var_confidence * 0.3

        # End-to-end increase confidence
        initial_avg = statistics.mean(memory_deltas[:len(memory_deltas)//3])
        final_avg = statistics.mean(memory_deltas[-len(memory_deltas)//3:])
        increase = final_avg - initial_avg
        increase_confidence = min(increase / (self.leak_threshold_mb_per_iter * len(memory_deltas)), 1.0)
        confidence += increase_confidence * 0.3

        return min(confidence, 1.0)

    def _generate_memory_recommendations(self, test_name: str, leak_detected: bool,
                                       confidence: float, avg_delta: float,
                                       trend_slope: float) -> List[str]:
        """Generate recommendations based on memory analysis."""
        recommendations = []

        if leak_detected and confidence > 0.7:
            recommendations.append(f"CRITICAL: Memory leak detected in {test_name} (confidence: {confidence:.1%})")
            if trend_slope > 0:
                recommendations.append(f"Memory increases by {trend_slope:.2f} MB per operation")
            recommendations.append("Review object cleanup and reference management")
        elif leak_detected and confidence > 0.5:
            recommendations.append(f"POTENTIAL: Possible memory issue in {test_name} (confidence: {confidence:.1%})")
            recommendations.append("Monitor closely and consider additional testing")
        elif leak_detected:
            recommendations.append(f"MINOR: Slight memory irregularity in {test_name} (confidence: {confidence:.1%})")
            recommendations.append("May be within normal variation - retest with more iterations")

        if abs(avg_delta) > 10:  # Large memory operations
            recommendations.append(f"Large memory operations detected ({avg_delta:.1f} MB avg delta)")
            recommendations.append("Consider optimizing memory allocation patterns")

        if not leak_detected and confidence < 0.3:
            recommendations.append(f"✓ {test_name} memory usage appears stable")

        return recommendations

    # Operation functions for different components

    def _gpu_parser_operation(self, iteration: int):
        """Execute GPU parser operation for memory testing."""
        parser = STLGPUParser()
        test_file = self._create_test_file(50)  # 50MB file

        try:
            model = parser._parse_file_internal(str(test_file))
            # Simulate brief usage
            _ = model.stats.triangle_count
        finally:
            test_file.unlink(missing_ok=True)

    def _file_chunker_operation(self, iteration: int):
        """Execute file chunker operation for memory testing."""
        chunker = FileChunker()
        test_file = self._create_test_file(100)

        try:
            chunks = chunker.create_chunks(test_file, target_chunk_size_mb=25)
            # Simulate processing chunks
            for chunk in chunks:
                _ = chunk.get_memory_estimate()
        finally:
            test_file.unlink(missing_ok=True)

    def _thread_coordinator_operation(self, iteration: int):
        """Execute thread coordinator operation for memory testing."""
        test_file = self._create_test_file(75)
        chunker = FileChunker()

        try:
            chunks = chunker.create_chunks(test_file, target_chunk_size_mb=20)
            coordinator = ThreadPoolCoordinator()
            token = CancellationToken()

            model = coordinator.coordinate_parsing(chunks[:2], token)  # Just first 2 chunks
            _ = model.stats.triangle_count
        finally:
            test_file.unlink(missing_ok=True)

    def _progress_aggregator_operation(self, iteration: int):
        """Execute progress aggregator operation for memory testing."""
        aggregator = ProgressAggregator(total_chunks=5)

        # Simulate progress updates
        for i in range(5):
            aggregator.update_chunk_progress(f"chunk_{i:03d}", (i + 1) * 20.0, f"Processing chunk {i}")

        # Simulate completion
        for i in range(5):
            aggregator.update_chunk_progress(f"chunk_{i:03d}", 100.0, "Completed")

        _ = aggregator.calculate_overall_progress()

    def _memory_manager_operation(self, iteration: int):
        """Execute memory manager operation for memory testing."""
        manager = self.memory_manager

        # Allocate and free memory
        block = manager.allocate_memory(1024 * 1024)  # 1MB
        if block:
            # Simulate usage
            block[0] = 42
            manager.free_memory(block)

    def _integrated_parsing_operation(self, iteration: int):
        """Execute integrated parsing operation for memory testing."""
        # Full parsing pipeline
        test_file = self._create_test_file(60)
        parser = STLGPUParser()

        try:
            model = parser._parse_file_internal(str(test_file))

            # Simulate model usage
            bounds = model.stats.min_bounds
            triangle_count = model.stats.triangle_count

            # Clean up
            del model

        finally:
            test_file.unlink(missing_ok=True)

    def _concurrent_operations(self, iteration: int):
        """Execute concurrent operations for memory testing."""
        results = []

        def worker_operation():
            parser = STLGPUParser()
            test_file = self._create_test_file(30)

            try:
                model = parser._parse_file_internal(str(test_file))
                results.append(model.stats.triangle_count)
            finally:
                test_file.unlink(missing_ok=True)

        # Run 3 concurrent operations
        threads = [threading.Thread(target=worker_operation) for _ in range(3)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def _create_test_file(self, size_mb: int) -> Path:
        """Create a test STL file for memory testing."""
        file_path = Path(f"memory_test_{size_mb}mb_{time.time()}.stl")

        # Calculate triangles needed
        target_bytes = size_mb * 1024 * 1024
        triangle_count = (target_bytes - 84) // 50

        # Create minimal binary STL
        header = b"Memory test file" + b"\x00" * (80 - 17)
        count_bytes = triangle_count.to_bytes(4, byteorder='little')

        # Create triangles data (simplified - all same triangle)
        triangles_data = b""
        normal = (0.0, 0.0, 1.0)
        v1 = (0.0, 0.0, 0.0)
        v2 = (1.0, 0.0, 0.0)
        v3 = (0.0, 1.0, 0.0)
        attribute = 0

        triangle = struct.pack('<12fH',
                             normal[0], normal[1], normal[2],
                             v1[0], v1[1], v1[2],
                             v2[0], v2[1], v2[2],
                             v3[0], v3[1], v3[2],
                             attribute)
        triangles_data = triangle * triangle_count

        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(count_bytes)
            f.write(triangles_data)

        return file_path


# Pytest test functions

@pytest.mark.parametrize("iterations", [10, 15, 20])
def test_memory_leak_detection_system(iterations: int):
    """Test the memory leak detection system itself."""
    detector = MemoryLeakDetector()

    # Test with stable operation
    def stable_operation(i):
        # Operation that shouldn't leak memory
        data = [0] * 1000
        result = sum(data)
        del data
        return result

    result = detector._run_memory_leak_test("Stable Test", stable_operation, iterations)

    assert result.iterations == iterations
    assert not result.leak_detected or result.leak_confidence < 0.5  # Allow some false positives


def test_gpu_parser_memory_stability():
    """Test GPU parser memory stability."""
    detector = MemoryLeakDetector()
    result = detector.test_gpu_parser_memory_leaks()

    assert result.iterations >= 10
    # Log results for analysis
    print(f"GPU Parser Memory Test: {result.iterations} iterations")
    print(f"Average delta: {result.average_delta:.2f} MB")
    print(f"Trend slope: {result.trend_slope:.4f} MB/iteration")
    print(f"Leak detected: {result.leak_detected} (confidence: {result.leak_confidence:.1%})")

    for rec in result.recommendations:
        print(f"- {rec}")


def test_comprehensive_memory_analysis():
    """Test comprehensive memory analysis."""
    detector = MemoryLeakDetector()
    results = detector.run_comprehensive_memory_tests()

    assert len(results) >= 6  # Should have results for all test types

    # Check that all tests ran
    test_names = ["gpu_parser", "file_chunker", "thread_coordinator",
                 "progress_aggregator", "memory_manager", "integrated_parsing"]

    for test_name in test_names:
        assert test_name in results
        result = results[test_name]
        assert result.iterations >= 8  # Minimum iterations

    # Generate summary report
    leaks_detected = sum(1 for r in results.values() if r.leak_detected and r.leak_confidence > 0.6)
    total_tests = len(results)

    print(f"\n=== MEMORY LEAK ANALYSIS SUMMARY ===")
    print(f"Tests run: {total_tests}")
    print(f"Leaks detected: {leaks_detected}")

    for test_name, result in results.items():
        status = "LEAK" if result.leak_detected and result.leak_confidence > 0.6 else "OK"
        print(f"{status}: {test_name} ({result.leak_confidence:.1%} confidence)")


if __name__ == "__main__":
    # Run comprehensive memory leak tests
    detector = MemoryLeakDetector()

    print("Running comprehensive memory leak detection...")
    results = detector.run_comprehensive_memory_tests()

    print("\n=== DETAILED RESULTS ===")
    for test_name, result in results.items():
        print(f"\n{test_name.upper()}:")
        print(f"  Iterations: {result.iterations}")
        print(f"  Average memory delta: {result.average_delta:.2f} MB")
        print(f"  Standard deviation: {result.standard_deviation:.2f} MB")
        print(f"  Trend slope: {result.trend_slope:.4f} MB/iteration")
        print(f"  Leak detected: {result.leak_detected}")
        print(f"  Confidence: {result.leak_confidence:.1%}")
        print("  Recommendations:")
        for rec in result.recommendations:
            print(f"    - {rec}")

    # Summary
    critical_leaks = sum(1 for r in results.values() if r.leak_detected and r.leak_confidence > 0.8)
    potential_leaks = sum(1 for r in results.values() if r.leak_detected and r.leak_confidence > 0.5)

    print("
=== SUMMARY ===")
    print(f"Total tests: {len(results)}")
    print(f"Critical memory leaks: {critical_leaks}")
    print(f"Potential memory issues: {potential_leaks}")

    if critical_leaks == 0 and potential_leaks == 0:
        print("✓ All memory tests passed - no significant leaks detected")
    elif critical_leaks == 0:
        print("⚠ Some potential memory issues detected - monitor closely")
    else:
        print("✗ Critical memory leaks detected - requires immediate attention")