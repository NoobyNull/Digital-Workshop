"""
Performance benchmark for FastHasher.

Verifies that performance targets are met:
- Files under 100MB: hash in < 1 second
- Files 100-500MB: hash in < 3 seconds
- Files over 500MB: hash in < 5 seconds

Also tests:
- Memory stability over repeated operations
- Throughput consistency
- Cancellation overhead
- Batch processing efficiency
"""

import os
import sys
import time
import tempfile
import tracemalloc
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.fast_hasher import FastHasher, HashResult
from src.core.cancellation_token import CancellationToken


class PerformanceBenchmark:
    """Performance benchmark suite for FastHasher."""
    
    def __init__(self):
        """Initialize benchmark."""
        self.hasher = FastHasher()
        self.temp_dir = tempfile.mkdtemp()
        self.results = []
        
    def cleanup(self):
        """Clean up temporary files."""
        for file in Path(self.temp_dir).glob("*"):
            try:
                file.unlink()
            except Exception:
                pass
        try:
            Path(self.temp_dir).rmdir()
        except Exception:
            pass
    
    def create_test_file(self, size_mb: float, name: str) -> str:
        """Create a test file of specified size."""
        file_path = os.path.join(self.temp_dir, name)
        size_bytes = int(size_mb * 1024 * 1024)
        
        print(f"  Creating {size_mb}MB test file...")
        
        with open(file_path, 'wb') as f:
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = size_bytes
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(os.urandom(write_size))  # Random data for realistic testing
                remaining -= write_size
        
        return file_path
    
    def format_time(self, seconds: float) -> str:
        """Format time for display."""
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        return f"{seconds:.2f}s"
    
    def format_throughput(self, mbps: float) -> str:
        """Format throughput for display."""
        return f"{mbps:.1f} MB/s"
    
    def run_benchmark(self, name: str, size_mb: float, target_time: float) -> Dict:
        """
        Run a single benchmark test.
        
        Args:
            name: Test name
            size_mb: File size in megabytes
            target_time: Target completion time in seconds
            
        Returns:
            Dict with benchmark results
        """
        print(f"\n{'='*60}")
        print(f"Benchmark: {name}")
        print(f"File Size: {size_mb} MB")
        print(f"Target Time: < {target_time}s")
        print(f"{'='*60}")
        
        file_path = self.create_test_file(size_mb, f"{name}.bin")
        
        # Warm-up run
        print("  Running warm-up...")
        _ = self.hasher.hash_file(file_path)
        
        # Actual benchmark runs (3 runs for consistency)
        print("  Running benchmark (3 iterations)...")
        times = []
        hashes = []
        
        for i in range(3):
            result = self.hasher.hash_file(file_path)
            times.append(result.hash_time)
            hashes.append(result.hash_value)
            print(f"    Run {i+1}: {self.format_time(result.hash_time)}")
        
        # Verify consistency
        if len(set(hashes)) != 1:
            print("  ⚠️  WARNING: Hash values inconsistent across runs!")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = (size_mb / avg_time) if avg_time > 0 else 0
        
        passed = avg_time < target_time
        
        result_dict = {
            'name': name,
            'size_mb': size_mb,
            'target_time': target_time,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'throughput': throughput,
            'passed': passed
        }
        
        print(f"\n  Results:")
        print(f"    Average: {self.format_time(avg_time)}")
        print(f"    Min: {self.format_time(min_time)}")
        print(f"    Max: {self.format_time(max_time)}")
        print(f"    Throughput: {self.format_throughput(throughput)}")
        print(f"    Status: {'✓ PASS' if passed else '✗ FAIL'}")
        
        self.results.append(result_dict)
        return result_dict
    
    def test_memory_stability(self) -> Dict:
        """Test memory stability over repeated operations."""
        print(f"\n{'='*60}")
        print("Memory Stability Test")
        print(f"{'='*60}")
        
        file_path = self.create_test_file(50.0, "memory_test.bin")
        
        # Track memory usage
        tracemalloc.start()
        
        memory_samples = []
        iteration_times = []
        
        print("  Running 20 iterations...")
        for i in range(20):
            start_mem = tracemalloc.get_traced_memory()[0]
            
            result = self.hasher.hash_file(file_path)
            iteration_times.append(result.hash_time)
            
            end_mem = tracemalloc.get_traced_memory()[0]
            memory_samples.append((start_mem, end_mem))
            
            if (i + 1) % 5 == 0:
                print(f"    Iteration {i+1}/20 complete")
        
        tracemalloc.stop()
        
        # Analyze memory growth
        first_peak = memory_samples[0][1]
        last_peak = memory_samples[-1][1]
        memory_growth = (last_peak - first_peak) / (1024 * 1024)  # MB
        
        # Analyze time consistency
        avg_time = sum(iteration_times) / len(iteration_times)
        time_variance = max(iteration_times) - min(iteration_times)
        
        # Memory leak considered if growth > 10MB over 20 iterations
        no_leak = memory_growth < 10.0
        stable_time = time_variance < (avg_time * 0.5)  # Less than 50% variance
        
        result_dict = {
            'iterations': 20,
            'memory_growth_mb': memory_growth,
            'avg_time': avg_time,
            'time_variance': time_variance,
            'no_memory_leak': no_leak,
            'stable_performance': stable_time,
            'passed': no_leak and stable_time
        }
        
        print(f"\n  Results:")
        print(f"    Iterations: 20")
        print(f"    Memory Growth: {memory_growth:.2f} MB")
        print(f"    Avg Time: {self.format_time(avg_time)}")
        print(f"    Time Variance: {self.format_time(time_variance)}")
        print(f"    No Memory Leak: {'✓' if no_leak else '✗'}")
        print(f"    Stable Performance: {'✓' if stable_time else '✗'}")
        print(f"    Status: {'✓ PASS' if result_dict['passed'] else '✗ FAIL'}")
        
        self.results.append(result_dict)
        return result_dict
    
    def test_batch_performance(self) -> Dict:
        """Test batch hashing performance."""
        print(f"\n{'='*60}")
        print("Batch Processing Performance")
        print(f"{'='*60}")
        
        # Create 10 files of 20MB each
        print("  Creating 10 test files (20MB each)...")
        files = [
            self.create_test_file(20.0, f"batch_{i}.bin")
            for i in range(10)
        ]
        
        print("  Running batch hash...")
        start_time = time.time()
        results = self.hasher.hash_files_batch(files)
        batch_time = time.time() - start_time
        
        # Calculate sequential estimate
        individual_times = [r.hash_time for r in results if r.success]
        sequential_estimate = sum(individual_times)
        
        efficiency = (sequential_estimate / batch_time) * 100 if batch_time > 0 else 0
        
        result_dict = {
            'file_count': len(files),
            'file_size_mb': 20.0,
            'batch_time': batch_time,
            'sequential_estimate': sequential_estimate,
            'efficiency_percent': efficiency,
            'passed': len([r for r in results if r.success]) == len(files)
        }
        
        print(f"\n  Results:")
        print(f"    Files: {len(files)}")
        print(f"    Batch Time: {self.format_time(batch_time)}")
        print(f"    Sequential Estimate: {self.format_time(sequential_estimate)}")
        print(f"    Efficiency: {efficiency:.1f}%")
        print(f"    Status: {'✓ PASS' if result_dict['passed'] else '✗ FAIL'}")
        
        self.results.append(result_dict)
        return result_dict
    
    def test_cancellation_overhead(self) -> Dict:
        """Test overhead of cancellation token checking."""
        print(f"\n{'='*60}")
        print("Cancellation Overhead Test")
        print(f"{'='*60}")
        
        file_path = self.create_test_file(50.0, "cancel_test.bin")
        
        # Hash without cancellation token
        print("  Hashing without cancellation token...")
        result_no_token = self.hasher.hash_file(file_path)
        time_no_token = result_no_token.hash_time
        
        # Hash with cancellation token (but don't cancel)
        print("  Hashing with cancellation token...")
        token = CancellationToken()
        result_with_token = self.hasher.hash_file(file_path, cancellation_token=token)
        time_with_token = result_with_token.hash_time
        
        overhead = ((time_with_token - time_no_token) / time_no_token) * 100
        acceptable = abs(overhead) < 10  # Less than 10% overhead
        
        result_dict = {
            'time_without_token': time_no_token,
            'time_with_token': time_with_token,
            'overhead_percent': overhead,
            'passed': acceptable
        }
        
        print(f"\n  Results:")
        print(f"    Without Token: {self.format_time(time_no_token)}")
        print(f"    With Token: {self.format_time(time_with_token)}")
        print(f"    Overhead: {overhead:+.1f}%")
        print(f"    Status: {'✓ PASS' if acceptable else '✗ FAIL'}")
        
        self.results.append(result_dict)
        return result_dict
    
    def print_summary(self):
        """Print benchmark summary."""
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}\n")
        
        all_passed = all(
            r.get('passed', False) for r in self.results
        )
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {sum(1 for r in self.results if r.get('passed', False))}")
        print(f"Failed: {sum(1 for r in self.results if not r.get('passed', False))}")
        print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
        
        if not all_passed:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.get('passed', False):
                    print(f"  - {r.get('name', 'Unknown Test')}")
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        try:
            print("\n" + "="*60)
            print("FastHasher Performance Benchmark Suite")
            print("="*60)
            
            # Core performance targets
            self.run_benchmark("Small File (50MB)", 50.0, 1.0)
            self.run_benchmark("Medium File (150MB)", 150.0, 3.0)
            self.run_benchmark("Large File (600MB)", 600.0, 5.0)
            
            # Stability and efficiency tests
            self.test_memory_stability()
            self.test_batch_performance()
            self.test_cancellation_overhead()
            
            # Print summary
            self.print_summary()
            
        finally:
            print("\nCleaning up...")
            self.cleanup()
            print("Done!")


if __name__ == '__main__':
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()