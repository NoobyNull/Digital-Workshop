"""
Performance benchmarking tests for Loading-Optimizations implementation.

This module provides comprehensive performance benchmarking against the
specified requirements, measuring load times, memory usage, and UI responsiveness.
"""

import gc
import json
import os
import psutil
import pytest
import statistics
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.memory_manager import get_memory_manager
from src.core.gpu_memory_manager import get_gpu_memory_manager
from src.parsers.stl_gpu_parser import STLGPUParser, GPUParseConfig
from src.parsers.base_parser import Model, ModelFormat


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    file_size_mb: int
    load_time_seconds: float
    memory_peak_mb: float
    memory_final_mb: float
    triangles_parsed: int
    success: bool
    error_message: Optional[str] = None
    gpu_used: bool = False
    ui_responsive: bool = True


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    benchmarks: List[BenchmarkResult]
    summary: Dict[str, Any]
    compliance_status: Dict[str, bool]
    recommendations: List[str]


class PerformanceBenchmarks:
    """Performance benchmarking suite."""

    # Performance requirements from specifications
    REQUIREMENTS = {
        "load_time": {
            "under_100mb": 5.0,    # < 5 seconds
            "100_500mb": 15.0,     # < 15 seconds
            "over_500mb": 30.0     # < 30 seconds
        },
        "memory_limit": 2048,      # 2GB maximum
        "ui_responsiveness": 100,  # < 100ms UI block time
        "memory_stability": 0.05   # < 5% memory variation
    }

    def __init__(self):
        """Initialize performance benchmarks."""
        self.logger = get_logger(__name__)
        self.memory_manager = get_memory_manager()
        self.gpu_memory_manager = get_gpu_memory_manager()
        self.test_files: Dict[int, Path] = {}
        self.results: List[BenchmarkResult] = []

    def run_comprehensive_benchmarks(self) -> PerformanceReport:
        """
        Run comprehensive performance benchmarks.

        Tests loading performance across different file sizes and configurations.
        """
        self.logger.info("Starting comprehensive performance benchmarks")

        # Test file sizes based on requirements
        test_sizes = [50, 100, 200, 500, 750, 1000]  # MB

        for size_mb in test_sizes:
            self.logger.info(f"Benchmarking {size_mb}MB file")
            result = self._benchmark_file_size(size_mb)
            self.results.append(result)

        # Generate comprehensive report
        report = self._generate_performance_report()
        return report

    def _benchmark_file_size(self, size_mb: int) -> BenchmarkResult:
        """Benchmark loading performance for a specific file size."""
        # Create or get test file
        test_file = self._get_test_file(size_mb)

        # Initialize parser with optimal settings
        config = GPUParseConfig(
            use_memory_mapping=True,
            chunk_size_triangles=50000,
            enable_progressive_loading=True
        )
        parser = STLGPUParser(config)

        # Track memory and timing
        memory_samples = []
        ui_block_times = []

        def memory_monitor():
            """Monitor memory usage during parsing."""
            while not hasattr(memory_monitor, 'stop'):
                memory_samples.append(psutil.virtual_memory().used / (1024 * 1024))  # MB
                time.sleep(0.1)

        # Start memory monitoring
        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()

        try:
            # Measure load time
            start_time = time.time()

            # Parse file with progress tracking
            progress_updates = []

            def progress_callback(progress: float, message: str):
                current_time = time.time()
                ui_block_times.append(current_time - start_time)
                progress_updates.append((progress, message, current_time))

            model = parser._parse_file_internal(str(test_file), progress_callback)
            load_time = time.time() - start_time

            # Stop memory monitoring
            memory_monitor.stop = True
            monitor_thread.join(timeout=1.0)

            # Calculate memory statistics
            if memory_samples:
                memory_peak = max(memory_samples)
                memory_final = memory_samples[-1]
            else:
                memory_peak = memory_final = 0

            # Check UI responsiveness
            max_ui_block = max(ui_block_times) if ui_block_times else 0
            ui_responsive = max_ui_block < (self.REQUIREMENTS["ui_responsiveness"] / 1000)  # Convert to seconds

            # Check GPU usage
            gpu_used = self._check_gpu_usage_during_parsing()

            return BenchmarkResult(
                file_size_mb=size_mb,
                load_time_seconds=load_time,
                memory_peak_mb=memory_peak,
                memory_final_mb=memory_final,
                triangles_parsed=model.stats.triangle_count if model else 0,
                success=model is not None,
                gpu_used=gpu_used,
                ui_responsive=ui_responsive
            )

        except Exception as e:
            # Stop memory monitoring
            memory_monitor.stop = True
            monitor_thread.join(timeout=1.0)

            return BenchmarkResult(
                file_size_mb=size_mb,
                load_time_seconds=0,
                memory_peak_mb=0,
                memory_final_mb=0,
                triangles_parsed=0,
                success=False,
                error_message=str(e)
            )

        finally:
            # Clean up
            gc.collect()

    def _get_test_file(self, size_mb: int) -> Path:
        """Get or create a test file of specified size."""
        if size_mb not in self.test_files:
            self.test_files[size_mb] = self._create_benchmark_file(size_mb)
        return self.test_files[size_mb]

    def _create_benchmark_file(self, size_mb: int) -> Path:
        """Create a realistic benchmark STL file."""
        file_path = Path(f"benchmark_{size_mb}mb.stl")

        if file_path.exists():
            return file_path

        # Calculate triangles needed (50 bytes per triangle + 84 header)
        target_bytes = size_mb * 1024 * 1024
        triangle_count = (target_bytes - 84) // 50

        self.logger.info(f"Creating benchmark file: {size_mb}MB ({triangle_count} triangles)")

        # Create binary STL
        header = f"Benchmark {size_mb}MB test file".encode('utf-8').ljust(80, b'\x00')
        count_bytes = triangle_count.to_bytes(4, byteorder='little')

        # Generate triangles in a grid pattern for realistic distribution
        triangles_data = b""
        grid_size = int(triangle_count ** 0.5) + 1

        triangle_idx = 0
        for x in range(grid_size):
            for y in range(grid_size):
                if triangle_idx >= triangle_count:
                    break

                # Create triangle at grid position
                x_pos = float(x) * 0.1
                y_pos = float(y) * 0.1

                # Triangle vertices
                normal = (0.0, 0.0, 1.0)
                v1 = (x_pos, y_pos, 0.0)
                v2 = (x_pos + 0.1, y_pos, 0.0)
                v3 = (x_pos, y_pos + 0.1, 0.0)
                attribute = 0

                triangle = struct.pack('<12fH',
                                     normal[0], normal[1], normal[2],
                                     v1[0], v1[1], v1[2],
                                     v2[0], v2[1], v2[2],
                                     v3[0], v3[1], v3[2],
                                     attribute)
                triangles_data += triangle
                triangle_idx += 1

            if triangle_idx >= triangle_count:
                break

        # Write file
        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(count_bytes)
            f.write(triangles_data)

        actual_size = file_path.stat().st_size
        self.logger.info(f"Created benchmark file: {actual_size / (1024*1024):.1f}MB")

        return file_path

    def _check_gpu_usage_during_parsing(self) -> bool:
        """Check if GPU was used during parsing."""
        try:
            device_info = self.gpu_memory_manager.gpu_accelerator.get_device_info()
            return device_info.get("available", False)
        except Exception:
            return False

    def _generate_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report."""
        # Analyze results
        successful_results = [r for r in self.results if r.success]

        if not successful_results:
            return PerformanceReport(
                benchmarks=self.results,
                summary={"error": "No successful benchmarks"},
                compliance_status={"overall": False},
                recommendations=["All benchmarks failed - check system configuration"]
            )

        # Calculate summary statistics
        load_times = [r.load_time_seconds for r in successful_results]
        memory_peaks = [r.memory_peak_mb for r in successful_results]

        summary = {
            "total_benchmarks": len(self.results),
            "successful_benchmarks": len(successful_results),
            "average_load_time": statistics.mean(load_times) if load_times else 0,
            "median_load_time": statistics.median(load_times) if load_times else 0,
            "min_load_time": min(load_times) if load_times else 0,
            "max_load_time": max(load_times) if load_times else 0,
            "average_memory_peak": statistics.mean(memory_peaks) if memory_peaks else 0,
            "max_memory_peak": max(memory_peaks) if memory_peaks else 0,
            "gpu_utilization": sum(1 for r in successful_results if r.gpu_used) / len(successful_results),
            "ui_responsiveness_rate": sum(1 for r in successful_results if r.ui_responsive) / len(successful_results)
        }

        # Check compliance with requirements
        compliance_status = self._check_compliance(successful_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(successful_results, compliance_status)

        return PerformanceReport(
            benchmarks=self.results,
            summary=summary,
            compliance_status=compliance_status,
            recommendations=recommendations
        )

    def _check_compliance(self, results: List[BenchmarkResult]) -> Dict[str, bool]:
        """Check compliance with performance requirements."""
        compliance = {}

        for result in results:
            # Load time compliance
            if result.file_size_mb < 100:
                target_time = self.REQUIREMENTS["load_time"]["under_100mb"]
            elif result.file_size_mb < 500:
                target_time = self.REQUIREMENTS["load_time"]["100_500mb"]
            else:
                target_time = self.REQUIREMENTS["load_time"]["over_500mb"]

            load_time_compliant = result.load_time_seconds < target_time

            # Memory compliance
            memory_compliant = result.memory_peak_mb < self.REQUIREMENTS["memory_limit"]

            # UI responsiveness compliance
            ui_compliant = result.ui_responsive

            compliance[f"load_time_{result.file_size_mb}mb"] = load_time_compliant
            compliance[f"memory_{result.file_size_mb}mb"] = memory_compliant
            compliance[f"ui_responsive_{result.file_size_mb}mb"] = ui_compliant

        # Overall compliance
        compliance["overall"] = all(compliance.values())

        return compliance

    def _generate_recommendations(self, results: List[BenchmarkResult],
                                compliance: Dict[str, bool]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Load time analysis
        slow_loads = [r for r in results if not compliance.get(f"load_time_{r.file_size_mb}mb", True)]
        if slow_loads:
            recommendations.append(
                f"Optimize load times for {len(slow_loads)} file sizes exceeding targets"
            )

        # Memory analysis
        high_memory = [r for r in results if r.memory_peak_mb > self.REQUIREMENTS["memory_limit"] * 0.8]
        if high_memory:
            recommendations.append(
                f"Reduce memory usage for {len(high_memory)} configurations approaching limits"
            )

        # GPU utilization analysis
        gpu_results = [r for r in results if r.gpu_used]
        if len(gpu_results) < len(results) * 0.5:
            recommendations.append("Improve GPU utilization - many benchmarks fell back to CPU")

        # UI responsiveness analysis
        unresponsive = [r for r in results if not r.ui_responsive]
        if unresponsive:
            recommendations.append(
                f"Improve UI responsiveness for {len(unresponsive)} file sizes"
            )

        # Size-specific recommendations
        large_files = [r for r in results if r.file_size_mb >= 500]
        if large_files:
            avg_large_time = statistics.mean(r.load_time_seconds for r in large_files)
            if avg_large_time > 20:
                recommendations.append("Consider additional optimizations for files >500MB")

        if not recommendations:
            recommendations.append("All performance targets met - consider further optimizations for even better performance")

        return recommendations

    def run_memory_stability_test(self, iterations: int = 20) -> Dict[str, Any]:
        """
        Test memory stability over multiple iterations.

        Args:
            iterations: Number of iterations to run

        Returns:
            Memory stability analysis
        """
        self.logger.info(f"Running memory stability test with {iterations} iterations")

        parser = STLGPUParser()
        test_file = self._create_benchmark_file(100)  # 100MB test file

        memory_usage = []
        load_times = []

        try:
            for i in range(iterations):
                self.logger.debug(f"Memory stability iteration {i+1}/{iterations}")

                # Force garbage collection
                gc.collect()

                # Record memory before
                mem_before = psutil.virtual_memory().used / (1024 * 1024)  # MB

                # Parse file
                start_time = time.time()
                model = parser._parse_file_internal(str(test_file))
                load_time = time.time() - start_time

                # Record memory after
                mem_after = psutil.virtual_memory().used / (1024 * 1024)  # MB

                memory_usage.append(mem_after - mem_before)
                load_times.append(load_time)

                # Clean up model
                del model

            # Analyze stability
            if len(memory_usage) >= 3:
                avg_memory = statistics.mean(memory_usage)
                memory_std = statistics.stdev(memory_usage)
                memory_variation = memory_std / avg_memory if avg_memory > 0 else 0

                stability_compliant = memory_variation < self.REQUIREMENTS["memory_stability"]

                return {
                    "iterations": iterations,
                    "average_memory_delta_mb": avg_memory,
                    "memory_std_dev": memory_std,
                    "memory_variation_ratio": memory_variation,
                    "stability_compliant": stability_compliant,
                    "average_load_time": statistics.mean(load_times),
                    "load_time_std_dev": statistics.stdev(load_times) if len(load_times) > 1 else 0
                }
            else:
                return {"error": "Insufficient data for stability analysis"}

        finally:
            test_file.unlink(missing_ok=True)

    def cleanup(self):
        """Clean up test files and resources."""
        for file_path in self.test_files.values():
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

        self.test_files.clear()
        self.results.clear()


# Standalone benchmark functions for pytest
@pytest.mark.parametrize("file_size_mb,target_time", [
    (50, 5.0),
    (200, 15.0),
    (750, 30.0),
])
def test_load_time_requirements(file_size_mb: int, target_time: float):
    """Test that loading meets time requirements."""
    benchmarks = PerformanceBenchmarks()

    try:
        result = benchmarks._benchmark_file_size(file_size_mb)

        assert result.success, f"Benchmark failed: {result.error_message}"
        assert result.load_time_seconds < target_time, \
            f"Load time {result.load_time_seconds:.2f}s exceeds target {target_time}s for {file_size_mb}MB file"

    finally:
        benchmarks.cleanup()


def test_memory_stability():
    """Test memory stability over multiple operations."""
    benchmarks = PerformanceBenchmarks()

    try:
        stability_results = benchmarks.run_memory_stability_test(iterations=10)

        assert "error" not in stability_results, f"Stability test failed: {stability_results.get('error')}"
        assert stability_results["stability_compliant"], \
            f"Memory not stable: {stability_results['memory_variation_ratio']:.1%} variation"

    finally:
        benchmarks.cleanup()


def test_comprehensive_performance_report():
    """Test generation of comprehensive performance report."""
    benchmarks = PerformanceBenchmarks()

    try:
        # Run a few benchmarks
        for size in [50, 200]:
            result = benchmarks._benchmark_file_size(size)
            benchmarks.results.append(result)

        # Generate report
        report = benchmarks._generate_performance_report()

        assert isinstance(report, PerformanceReport)
        assert len(report.benchmarks) == 2
        assert "total_benchmarks" in report.summary
        assert "compliance_status" in report.compliance_status
        assert isinstance(report.recommendations, list)

    finally:
        benchmarks.cleanup()


if __name__ == "__main__":
    # Run comprehensive benchmarks
    benchmarks = PerformanceBenchmarks()

    try:
        print("Running comprehensive performance benchmarks...")
        report = benchmarks.run_comprehensive_benchmarks()

        print("\n=== PERFORMANCE REPORT ===")
        print(json.dumps(report.summary, indent=2))

        print("\n=== COMPLIANCE STATUS ===")
        for key, compliant in report.compliance_status.items():
            status = "✓" if compliant else "✗"
            print(f"{status} {key}")

        print("\n=== RECOMMENDATIONS ===")
        for rec in report.recommendations:
            print(f"- {rec}")

        # Run memory stability test
        print("\n=== MEMORY STABILITY TEST ===")
        stability = benchmarks.run_memory_stability_test()
        print(json.dumps(stability, indent=2))

    finally:
        benchmarks.cleanup()