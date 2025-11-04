"""
Performance profiling system for 3D model loading operations.

This module provides comprehensive performance tracking, benchmarking,
and analysis tools to monitor loading performance and identify bottlenecks.
"""

import cProfile
import functools
import io
import pstats
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.core.logging_config import get_logger, log_function_call


class PerformanceMetric(Enum):
    """Types of performance metrics."""

    LOAD_TIME = "load_time"
    PARSE_TIME = "parse_time"
    GPU_TIME = "gpu_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    IO_TIME = "io_time"
    CHUNK_TIME = "chunk_time"


@dataclass
class PerformanceSample:
    """Single performance measurement sample."""

    timestamp: float
    metric: PerformanceMetric
    value: float
    operation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def value_mb(self) -> float:
        """Get memory value in MB."""
        if self.metric == PerformanceMetric.MEMORY_USAGE:
            return self.value / (1024 * 1024)
        return self.value

    @property
    def value_seconds(self) -> float:
        """Get time value in seconds."""
        if self.metric in [
            PerformanceMetric.LOAD_TIME,
            PerformanceMetric.PARSE_TIME,
            PerformanceMetric.GPU_TIME,
            PerformanceMetric.IO_TIME,
            PerformanceMetric.CHUNK_TIME,
        ]:
            return self.value
        return self.value


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""

    operation: str
    metric: PerformanceMetric
    count: int = 0
    total: float = 0.0
    min_value: float = float("inf")
    max_value: float = 0.0
    avg_value: float = 0.0
    std_dev: float = 0.0

    def add_sample(self, value: float) -> None:
        """Add a sample to the statistics."""
        self.count += 1
        self.total += value
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.avg_value = self.total / self.count

        # Calculate running standard deviation
        if self.count > 1:
            # Welford's online algorithm
            delta = value - self.avg_value
            self.std_dev = (
                (self.std_dev * (self.count - 2) + delta * delta) / (self.count - 1)
            ) ** 0.5

    @property
    def is_significant(self) -> bool:
        """Check if statistics are significant (enough samples)."""
        return self.count >= 3


class PerformanceProfiler:
    """
    Main performance profiling system.

    Collects, analyzes, and reports performance metrics for loading operations.
    """

    def __init__(self, enable_profiling: bool = True, log_threshold_seconds: float = 1.0):
        """
        Initialize performance profiler.

        Args:
            enable_profiling: Whether to enable performance profiling
            log_threshold_seconds: Threshold for logging slow operations
        """
        self.logger = get_logger(__name__)
        self.enable_profiling = enable_profiling
        self.log_threshold = log_threshold_seconds

        # Data storage
        self.samples: List[PerformanceSample] = []
        self.stats: Dict[str, Dict[PerformanceMetric, PerformanceStats]] = defaultdict(dict)
        self.active_timers: Dict[str, float] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Profiling output
        self.profile_output_dir = Path("performance_profiles")
        self.profile_output_dir.mkdir(exist_ok=True)

        self.logger.info(f"PerformanceProfiler initialized (enabled: {enable_profiling})")

    @log_function_call
    @contextmanager
    def time_operation(
        self, operation: str, metric: PerformanceMetric = PerformanceMetric.LOAD_TIME
    ):
        """
        Context manager for timing operations.

        Args:
            operation: Name of the operation being timed
            metric: Type of metric to record
        """
        if not self.enable_profiling:
            yield
            return

        start_time = time.perf_counter()
        timer_key = f"{operation}_{metric.value}_{threading.current_thread().ident}"

        with self._lock:
            self.active_timers[timer_key] = start_time

        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            with self._lock:
                self.active_timers.pop(timer_key, None)

            # Record the sample
            self.record_sample(metric, duration, operation)

            # Log slow operations
            if duration > self.log_threshold:
                self.logger.warning(
                    f"Slow operation detected: {operation} took {duration:.3f}s "
                    f"(threshold: {self.log_threshold}s)"
                )

    @log_function_call
    def record_sample(
        self,
        metric: PerformanceMetric,
        value: float,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a performance sample.

        Args:
            metric: Type of metric
            value: Measured value
            operation: Operation name
            metadata: Additional metadata
        """
        if not self.enable_profiling:
            return

        sample = PerformanceSample(
            timestamp=time.time(),
            metric=metric,
            value=value,
            operation=operation,
            metadata=metadata or {},
        )

        with self._lock:
            self.samples.append(sample)

            # Update statistics
            if operation not in self.stats:
                self.stats[operation] = {}
            if metric not in self.stats[operation]:
                self.stats[operation][metric] = PerformanceStats(operation, metric)

            self.stats[operation][metric].add_sample(value)

    @log_function_call
    def get_operation_stats(self, operation: str) -> Dict[PerformanceMetric, PerformanceStats]:
        """
        Get performance statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            Dictionary mapping metrics to statistics
        """
        with self._lock:
            return dict(self.stats.get(operation, {}))

    @log_function_call
    def get_all_stats(self) -> Dict[str, Dict[PerformanceMetric, PerformanceStats]]:
        """
        Get all performance statistics.

        Returns:
            Nested dictionary of operation -> metric -> stats
        """
        with self._lock:
            return {op: dict(metrics) for op, metrics in self.stats.items()}

    @log_function_call
    def get_performance_report(self, operations: Optional[List[str]] = None) -> str:
        """
        Generate a performance report.

        Args:
            operations: List of operations to include (None for all)

        Returns:
            Formatted performance report
        """
        with self._lock:
            report_lines = ["Performance Report", "=" * 50]

            target_ops = operations if operations else list(self.stats.keys())

            for operation in sorted(target_ops):
                if operation not in self.stats:
                    continue

                report_lines.append(f"\nOperation: {operation}")
                report_lines.append("-" * 30)

                for metric, stats in self.stats[operation].items():
                    if not stats.is_significant:
                        continue

                    report_lines.append(f"  {metric.value}:")
                    report_lines.append(f"    Count: {stats.count}")
                    report_lines.append(f"    Avg: {stats.avg_value:.3f}")
                    report_lines.append(f"    Min: {stats.min_value:.3f}")
                    report_lines.append(f"    Max: {stats.max_value:.3f}")
                    if stats.std_dev > 0:
                        report_lines.append(f"    Std Dev: {stats.std_dev:.3f}")

            return "\n".join(report_lines)

    @log_function_call
    def profile_function(self, operation: str):
        """
        Decorator for profiling functions with cProfile.

        Args:
            operation: Name of the operation

        Returns:
            Profiling decorator
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enable_profiling:
                    return func(*args, **kwargs)

                profiler = cProfile.Profile()
                profiler.enable()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable()

                    # Save profile data
                    timestamp = int(time.time())
                    profile_file = self.profile_output_dir / f"{operation}_{timestamp}.prof"

                    # Save binary profile
                    profiler.dump_stats(str(profile_file))

                    # Generate text report
                    s = io.StringIO()
                    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
                    ps.print_stats(20)  # Top 20 functions

                    text_report = self.profile_output_dir / f"{operation}_{timestamp}.txt"
                    with open(text_report, "w") as f:
                        f.write(s.getvalue())

                    self.logger.info(f"Profile saved: {profile_file} and {text_report}")

            return wrapper

        return decorator

    @log_function_call
    def benchmark_operation(
        self,
        operation_func: Callable,
        operation_name: str,
        iterations: int = 10,
        warmup_iterations: int = 2,
    ) -> Dict[str, Any]:
        """
        Benchmark an operation over multiple iterations.

        Args:
            operation_func: Function to benchmark
            operation_name: Name for the operation
            iterations: Number of benchmark iterations
            warmup_iterations: Number of warmup iterations

        Returns:
            Benchmark results dictionary
        """
        if not self.enable_profiling:
            return {"error": "Profiling disabled"}

        self.logger.info(f"Starting benchmark: {operation_name} ({iterations} iterations)")

        # Warmup
        for i in range(warmup_iterations):
            try:
                operation_func()
            except Exception as e:
                return {"error": f"Warmup failed: {e}"}

        # Benchmark
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()

            try:
                operation_func()
                end_time = time.perf_counter()
                duration = end_time - start_time
                times.append(duration)

                # Record sample
                self.record_sample(
                    PerformanceMetric.LOAD_TIME,
                    duration,
                    f"{operation_name}_benchmark",
                    {"iteration": i + 1},
                )

            except Exception as e:
                self.logger.error(f"Benchmark iteration {i + 1} failed: {e}")
                continue

        if not times:
            return {"error": "No successful benchmark iterations"}

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Calculate standard deviation
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance**0.5

        results = {
            "operation": operation_name,
            "iterations": len(times),
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "times": times,
        }

        self.logger.info(
            f"Benchmark completed: {operation_name} - "
            f"Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s"
        )

        return results

    @log_function_call
    def detect_performance_regressions(
        self,
        baseline_stats: Dict[str, Dict[PerformanceMetric, PerformanceStats]],
        threshold_percent: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect performance regressions compared to baseline.

        Args:
            baseline_stats: Baseline performance statistics
            threshold_percent: Threshold for regression detection

        Returns:
            List of detected regressions
        """
        regressions = []

        with self._lock:
            for operation, metrics in self.stats.items():
                if operation not in baseline_stats:
                    continue

                baseline_metrics = baseline_stats[operation]

                for metric, current_stats in metrics.items():
                    if metric not in baseline_metrics:
                        continue

                    baseline_avg = baseline_metrics[metric].avg_value
                    current_avg = current_stats.avg_value

                    if baseline_avg == 0:
                        continue

                    percent_change = ((current_avg - baseline_avg) / baseline_avg) * 100

                    if percent_change > threshold_percent:
                        regressions.append(
                            {
                                "operation": operation,
                                "metric": metric.value,
                                "baseline_avg": baseline_avg,
                                "current_avg": current_avg,
                                "percent_change": percent_change,
                                "threshold": threshold_percent,
                            }
                        )

        return regressions

    @log_function_call
    def export_samples_to_csv(self, output_file: Path) -> bool:
        """
        Export performance samples to CSV file.

        Args:
            output_file: Path to output CSV file

        Returns:
            True if export successful
        """
        try:
            import csv

            with self._lock:
                with open(output_file, "w", newline="") as csvfile:
                    fieldnames = [
                        "timestamp",
                        "metric",
                        "value",
                        "operation",
                        "metadata",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for sample in self.samples:
                        writer.writerow(
                            {
                                "timestamp": sample.timestamp,
                                "metric": sample.metric.value,
                                "value": sample.value,
                                "operation": sample.operation,
                                "metadata": str(sample.metadata),
                            }
                        )

            self.logger.info(f"Exported {len(self.samples)} samples to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export samples to CSV: {e}")
            return False

    @log_function_call
    def clear_data(self) -> None:
        """Clear all collected performance data."""
        with self._lock:
            self.samples.clear()
            self.stats.clear()
            self.active_timers.clear()

        self.logger.info("Performance data cleared")

    def __str__(self) -> str:
        """String representation of profiler status."""
        with self._lock:
            return (
                f"PerformanceProfiler(samples={len(self.samples)}, "
                f"operations={len(self.stats)}, "
                f"active_timers={len(self.active_timers)})"
            )


# Global profiler instance
_performance_profiler: Optional[PerformanceProfiler] = None
_profiler_lock = threading.RLock()


def get_performance_profiler() -> PerformanceProfiler:
    """
    Get the global performance profiler instance.

    Returns:
        PerformanceProfiler instance
    """
    global _performance_profiler

    with _profiler_lock:
        if _performance_profiler is None:
            _performance_profiler = PerformanceProfiler()

        return _performance_profiler


def profile_function(operation: str):
    """
    Decorator to profile a function.

    Args:
        operation: Name of the operation

    Returns:
        Profiling decorator
    """
    profiler = get_performance_profiler()
    return profiler.profile_function(operation)


def time_operation(operation: str, metric: PerformanceMetric = PerformanceMetric.LOAD_TIME):
    """
    Context manager to time an operation.

    Args:
        operation: Name of the operation
        metric: Type of metric to record

    Returns:
        Context manager
    """
    profiler = get_performance_profiler()
    return profiler.time_operation(operation, metric)
