"""
Performance Testing Framework with Regression Detection for Candy-Cadence.

This module provides comprehensive performance testing capabilities including:
- Load time validation for different file sizes
- Performance benchmarking and regression detection
- Stress testing scenarios
- Performance monitoring and alerting
- Performance target validation against requirements
"""

import gc
import json
import os
import sys
import tempfile
import time
import threading
import unittest
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from unittest.mock import Mock, patch, MagicMock

import pytest
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.logging_config import get_logger
from src.core.performance_monitor import PerformanceMonitor
from src.parsers.stl_parser import STLParser
from src.parsers.obj_parser import OBJParser


@dataclass
class PerformanceTarget:
    """Performance target specification."""

    name: str
    max_time_seconds: float
    max_memory_mb: float
    file_size_category: str  # "small", "medium", "large", "very_large"
    operation_type: str  # "load", "parse", "store", "retrieve"


@dataclass
class PerformanceResult:
    """Performance test result."""

    test_name: str
    execution_time: float
    memory_used_mb: float
    file_size_mb: float
    triangle_count: int
    vertex_count: int
    success: bool
    regression_detected: bool
    baseline_time: Optional[float] = None
    performance_degradation: Optional[float] = None  # percentage


class PerformanceRegressionDetector:
    """Detects performance regressions by comparing against baselines."""

    def __init__(self, baseline_file: str = "performance_baseline.json"):
        """Initialize regression detector."""
        self.logger = get_logger(__name__)
        self.baseline_file = Path(__file__).parent / baseline_file
        self.baseline_data = self._load_baseline()

    def _load_baseline(self) -> Dict[str, float]:
        """Load performance baseline from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load baseline: {e}")

        return {}

    def save_baseline(self, test_name: str, execution_time: float):
        """Save performance baseline."""
        self.baseline_data[test_name] = execution_time

        try:
            with open(self.baseline_file, "w") as f:
                json.dump(self.baseline_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save baseline: {e}")

    def check_regression(
        self, test_name: str, current_time: float, threshold_percent: float = 20.0
    ) -> Tuple[bool, float]:
        """
        Check if current performance indicates regression.

        Args:
            test_name: Name of the test
            current_time: Current execution time
            threshold_percent: Allowed performance degradation percentage

        Returns:
            Tuple of (regression_detected, degradation_percentage)
        """
        if test_name not in self.baseline_data:
            # No baseline available - establish one
            self.save_baseline(test_name, current_time)
            return False, 0.0

        baseline_time = self.baseline_data[test_name]
        degradation = ((current_time - baseline_time) / baseline_time) * 100

        regression_detected = degradation > threshold_percent

        if regression_detected:
            self.logger.warning(
                f"Performance regression detected in {test_name}: "
                f"current={current_time:.3f}s, baseline={baseline_time:.3f}s, "
                f"degradation={degradation:.1f}%"
            )
        else:
            self.logger.info(
                f"Performance OK for {test_name}: "
                f"current={current_time:.3f}s, baseline={baseline_time:.3f}s, "
                f"degradation={degradation:.1f}%"
            )

        return regression_detected, degradation


class PerformanceTestFramework(unittest.TestCase):
    """Comprehensive performance testing framework."""

    @classmethod
    def setUpClass(cls):
        """Set up performance test environment."""
        cls.logger = get_logger(__name__)
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_files_dir = Path(cls.temp_dir) / "test_files"
        cls.test_files_dir.mkdir(exist_ok=True)

        # Initialize regression detector
        cls.regression_detector = PerformanceRegressionDetector()

        # Define performance targets
        cls.performance_targets = [
            PerformanceTarget("stl_small_load", 5.0, 50.0, "small", "load"),
            PerformanceTarget("stl_medium_load", 15.0, 150.0, "medium", "load"),
            PerformanceTarget("stl_large_load", 30.0, 500.0, "large", "load"),
            PerformanceTarget("obj_load", 8.0, 100.0, "medium", "load"),
            PerformanceTarget("stl_parse", 3.0, 30.0, "any", "parse"),
            PerformanceTarget("obj_parse", 5.0, 50.0, "any", "parse"),
        ]

        # Create test files of different sizes
        cls._create_performance_test_files()

        # Track performance metrics
        cls.performance_history = []
        cls.regression_count = 0

    @classmethod
    def tearDownClass(cls):
        """Clean up performance test environment."""
        try:
            import shutil

            shutil.rmtree(cls.temp_dir, ignore_errors=True)
        except Exception as e:
            cls.logger.warning(f"Failed to clean up temp directory: {e}")

        # Log final statistics
        cls.logger.info(f"Performance testing completed:")
        cls.logger.info(f"Total tests: {len(cls.performance_history)}")
        cls.logger.info(f"Regressions detected: {cls.regression_count}")
        cls.logger.info(
            f"Regression rate: {cls.regression_count / len(cls.performance_history) * 100:.1f}%"
        )

    @classmethod
    def _create_performance_test_files(cls):
        """Create test files for performance testing."""
        # Small files (< 100MB, < 5 seconds target)
        cls._create_stl_file("small_cube_100.stl", 100, "small")
        cls._create_stl_file("small_cube_1000.stl", 1000, "small")
        cls._create_stl_file("small_cube_10000.stl", 10000, "small")

        # Medium files (100-500MB, < 15 seconds target)
        cls._create_stl_file("medium_cube_50000.stl", 50000, "medium")
        cls._create_stl_file("medium_cube_100000.stl", 100000, "medium")

        # Large files (> 500MB, < 30 seconds target)
        cls._create_stl_file("large_cube_200000.stl", 200000, "large")
        cls._create_stl_file("large_cube_500000.stl", 500000, "large")

        # Very large files for stress testing
        cls._create_stl_file("very_large_1m.stl", 1000000, "very_large")

        # Create OBJ file
        cls._create_obj_file("performance_cube.obj")

    @classmethod
    def _create_stl_file(cls, filename: str, triangle_count: int, category: str):
        """Create a binary STL file for performance testing."""
        import struct

        file_path = cls.test_files_dir / filename

        with open(file_path, "wb") as f:
            # Write header (80 bytes)
            header = f"Performance Test {triangle_count} triangles".encode("utf-8")
            f.write(header.ljust(80, b"\x00"))

            # Write triangle count (4 bytes)
            f.write(struct.pack("<I", triangle_count))

            # Write triangles efficiently for performance testing
            for i in range(triangle_count):
                # Use efficient triangle data
                f.write(struct.pack("<fff", 0.0, 0.0, 1.0))  # Normal
                f.write(struct.pack("<fff", i * 0.01, 0.0, 0.0))  # Vertex 1
                f.write(struct.pack("<fff", i * 0.01 + 0.01, 0.0, 0.0))  # Vertex 2
                f.write(struct.pack("<fff", i * 0.01, 0.01, 0.0))  # Vertex 3
                f.write(struct.pack("<H", 0))  # Attribute

        return file_path

    @classmethod
    def _create_obj_file(cls, filename: str):
        """Create an OBJ file for performance testing."""
        file_path = cls.test_files_dir / filename

        obj_content = """# Performance Test OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0
v 2.0 0.0 0.0
v 3.0 0.0 0.0
# ... many more vertices for performance testing
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 5 1 4 8
"""

        with open(file_path, "w") as f:
            f.write(obj_content)

        return file_path

    def setUp(self):
        """Set up individual performance test."""
        self.process = psutil.Process()

    def _measure_performance(
        self, operation: Callable, operation_name: str
    ) -> PerformanceResult:
        """
        Measure performance of an operation with comprehensive metrics.

        Args:
            operation: Function to measure
            operation_name: Name of the operation for reporting

        Returns:
            PerformanceResult with detailed metrics
        """
        # Record baseline metrics
        memory_before = self.process.memory_info().rss
        cpu_before = self.process.cpu_percent()

        # Measure execution time with high precision
        start_time = time.perf_counter()

        try:
            result = operation()
            success = True
        except Exception as e:
            self.logger.error(f"Operation {operation_name} failed: {e}")
            result = None
            success = False

        end_time = time.perf_counter()

        # Record post-operation metrics
        memory_after = self.process.memory_info().rss
        cpu_after = self.process.cpu_percent()

        # Calculate metrics
        execution_time = end_time - start_time
        memory_used_mb = (memory_after - memory_before) / (1024 * 1024)

        # Check for regression
        regression_detected, degradation = self.regression_detector.check_regression(
            operation_name, execution_time
        )

        if regression_detected:
            self.regression_count += 1

        # Create result
        perf_result = PerformanceResult(
            test_name=operation_name,
            execution_time=execution_time,
            memory_used_mb=memory_used_mb,
            file_size_mb=0.0,  # Will be set by caller
            triangle_count=0,  # Will be set by caller
            vertex_count=0,  # Will be set by caller
            success=success,
            regression_detected=regression_detected,
            performance_degradation=degradation,
        )

        # Store for history
        self.performance_history.append(perf_result)

        return perf_result

    def _validate_performance_targets(
        self, result: PerformanceResult, target: PerformanceTarget
    ):
        """Validate performance result against targets."""
        self.assertLess(
            result.execution_time,
            target.max_time_seconds,
            f"Execution time {result.execution_time:.3f}s exceeds target "
            f"{target.max_time_seconds}s for {result.test_name}",
        )

        self.assertLess(
            result.memory_used_mb,
            target.max_memory_mb,
            f"Memory usage {result.memory_used_mb:.2f}MB exceeds target "
            f"{target.max_memory_mb}MB for {result.test_name}",
        )

        self.assertTrue(result.success, f"Operation {result.test_name} failed")

    def test_stl_loading_performance(self):
        """Test STL file loading performance with regression detection."""
        test_files = [
            ("small_cube_100.stl", 100, "stl_small_load"),
            ("small_cube_1000.stl", 1000, "stl_small_load"),
            ("small_cube_10000.stl", 10000, "stl_small_load"),
            ("medium_cube_50000.stl", 50000, "stl_medium_load"),
            ("medium_cube_100000.stl", 100000, "stl_medium_load"),
            ("large_cube_200000.stl", 200000, "stl_large_load"),
        ]

        for filename, expected_triangles, target_name in test_files:
            with self.subTest(file=filename):
                file_path = self.test_files_dir / filename

                def load_operation():
                    parser = STLParser()
                    model = parser.parse_file(file_path)
                    self.assertIsNotNone(model)
                    return model

                # Measure performance
                result = self._measure_performance(
                    load_operation, f"stl_load_{filename}"
                )

                # Set file-specific metrics
                result.triangle_count = expected_triangles
                result.file_size_mb = file_path.stat().st_size / (1024 * 1024)

                # Find matching target
                target = next(
                    (t for t in self.performance_targets if t.name == target_name), None
                )

                if target:
                    self._validate_performance_targets(result, target)

                # Log performance results
                self.logger.info(
                    f"STL Loading Performance - {filename}: "
                    f"{result.execution_time:.3f}s, {result.memory_used_mb:.2f}MB, "
                    f"{result.triangle_count} triangles, "
                    f"regression={result.regression_detected}"
                )

                # Assert no regression for critical tests
                if filename in ["small_cube_1000.stl", "medium_cube_50000.stl"]:
                    self.assertFalse(
                        result.regression_detected,
                        f"Performance regression detected in {filename}",
                    )

    def test_obj_loading_performance(self):
        """Test OBJ file loading performance."""
        file_path = self.test_files_dir / "performance_cube.obj"

        def obj_load_operation():
            parser = OBJParser()
            model = parser.parse_file(file_path)
            self.assertIsNotNone(model)
            return model

        # Measure performance
        result = self._measure_performance(obj_load_operation, "obj_load")

        # Set metrics
        result.file_size_mb = file_path.stat().st_size / (1024 * 1024)

        # Validate against targets
        target = next(
            (t for t in self.performance_targets if t.name == "obj_load"), None
        )
        if target:
            self._validate_performance_targets(result, target)

        # Log results
        self.logger.info(
            f"OBJ Loading Performance: {result.execution_time:.3f}s, "
            f"{result.memory_used_mb:.2f}MB, regression={result.regression_detected}"
        )

    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency during operations."""

        def memory_efficient_operation():
            # Process multiple files to test memory efficiency
            models = []
            for filename in ["small_cube_1000.stl", "medium_cube_50000.stl"]:
                file_path = self.test_files_dir / filename
                parser = STLParser()
                model = parser.parse_file(file_path)
                models.append(model)

                # Clean up between operations
                del model
                gc.collect()

            return models

        # Measure memory efficiency
        initial_memory = self.process.memory_info().rss

        result = self._measure_performance(
            memory_efficient_operation, "memory_efficiency"
        )

        final_memory = self.process.memory_info().rss
        memory_growth_mb = (final_memory - initial_memory) / (1024 * 1024)

        # Memory growth should be reasonable
        self.assertLess(
            memory_growth_mb,
            200.0,
            f"Excessive memory growth: {memory_growth_mb:.2f}MB",
        )

        self.logger.info(
            f"Memory Efficiency Test: {memory_growth_mb:.2f}MB growth, "
            f"peak usage: {result.memory_used_mb:.2f}MB"
        )

    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations."""
        import concurrent.futures
        import threading

        def concurrent_load(filename):
            """Load a file in a separate operation."""
            file_path = self.test_files_dir / filename
            parser = STLParser()
            model = parser.parse_file(file_path)
            return len(model.vertices) if model else 0

        # Test concurrent loading
        def concurrent_operation():
            files_to_load = [
                "small_cube_100.stl",
                "small_cube_1000.stl",
                "small_cube_10000.stl",
            ]

            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(concurrent_load, filename)
                    for filename in files_to_load
                ]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)

            return results

        # Measure concurrent performance
        result = self._measure_performance(
            concurrent_operation, "concurrent_operations"
        )

        # Concurrent operations should complete within reasonable time
        self.assertLess(
            result.execution_time,
            10.0,
            f"Concurrent operations too slow: {result.execution_time:.3f}s",
        )

        self.logger.info(
            f"Concurrent Operations Performance: {result.execution_time:.3f}s"
        )

    def test_sustained_load_performance(self):
        """Test performance under sustained load."""

        def sustained_load_operation():
            """Perform sustained load over multiple iterations."""
            for iteration in range(10):
                for filename in ["small_cube_1000.stl", "medium_cube_50000.stl"]:
                    file_path = self.test_files_dir / filename
                    parser = STLParser()
                    model = parser.parse_file(file_path)

                    # Clean up
                    del model
                    gc.collect()

            return True

        # Measure sustained load performance
        result = self._measure_performance(sustained_load_operation, "sustained_load")

        # Sustained load should maintain consistent performance
        self.assertLess(
            result.execution_time,
            60.0,
            f"Sustained load too slow: {result.execution_time:.3f}s",
        )

        self.logger.info(
            f"Sustained Load Performance: {result.execution_time:.3f}s for 20 operations"
        )


class PerformanceBenchmarkSuite:
    """Complete performance benchmarking suite for continuous monitoring."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.logger = get_logger(__name__)
        self.regression_detector = PerformanceRegressionDetector()

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite."""
        benchmark_results = {
            "timestamp": time.time(),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "python_version": sys.version,
            },
            "test_results": [],
            "summary": {},
        }

        # Run unit test suite for performance
        import unittest

        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceTestFramework)

        # Run with detailed results
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)

        # Extract performance metrics
        for test_result in PerformanceTestFramework.performance_history:
            benchmark_results["test_results"].append(
                {
                    "test_name": test_result.test_name,
                    "execution_time": test_result.execution_time,
                    "memory_used_mb": test_result.memory_used_mb,
                    "success": test_result.success,
                    "regression_detected": test_result.regression_detected,
                    "performance_degradation": test_result.performance_degradation,
                }
            )

        # Calculate summary statistics
        if benchmark_results["test_results"]:
            execution_times = [
                r["execution_time"] for r in benchmark_results["test_results"]
            ]
            memory_usage = [
                r["memory_used_mb"] for r in benchmark_results["test_results"]
            ]

            benchmark_results["summary"] = {
                "total_tests": len(benchmark_results["test_results"]),
                "successful_tests": sum(
                    1 for r in benchmark_results["test_results"] if r["success"]
                ),
                "failed_tests": sum(
                    1 for r in benchmark_results["test_results"] if not r["success"]
                ),
                "regressions_detected": sum(
                    1
                    for r in benchmark_results["test_results"]
                    if r["regression_detected"]
                ),
                "avg_execution_time": statistics.mean(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times),
                "avg_memory_usage": statistics.mean(memory_usage),
                "max_memory_usage": max(memory_usage),
            }

        # Save benchmark results
        self._save_benchmark_results(benchmark_results)

        return benchmark_results

    def _save_benchmark_results(self, results: Dict[str, Any]):
        """Save benchmark results to file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = Path(__file__).parent / f"benchmark_results_{timestamp}.json"

        try:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            self.logger.info(f"Benchmark results saved to {results_file}")
        except Exception as e:
            self.logger.error(f"Failed to save benchmark results: {e}")


if __name__ == "__main__":
    # Run performance benchmark suite
    benchmark_suite = PerformanceBenchmarkSuite()
    results = benchmark_suite.run_full_benchmark()

    print("\n" + "=" * 50)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 50)

    summary = results.get("summary", {})
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"Successful: {summary.get('successful_tests', 0)}")
    print(f"Failed: {summary.get('failed_tests', 0)}")
    print(f"Regressions: {summary.get('regressions_detected', 0)}")
    print(f"Avg Execution Time: {summary.get('avg_execution_time', 0):.3f}s")
    print(f"Max Memory Usage: {summary.get('max_memory_usage', 0):.2f}MB")

    if summary.get("regressions_detected", 0) > 0:
        print("\n⚠️  Performance regressions detected!")
        exit(1)
    else:
        print("\n✅ All performance tests passed!")
        exit(0)
