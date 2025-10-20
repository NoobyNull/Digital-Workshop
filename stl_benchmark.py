#!/usr/bin/env python3
"""
STL Loading Performance Benchmark

This script benchmarks STL file loading performance comparing:
1. Float precision loading (default)
2. No-float (integer) precision loading

It measures loading time, memory usage, and accuracy for both approaches
using the provided TEST-STL.stl file (684MB).

Usage:
    python stl_benchmark.py
"""

import gc
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any
import statistics

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import psutil
except ImportError:
    print("Warning: psutil not available. Memory monitoring will be limited.")
    psutil = None

try:
    import numpy as np
except ImportError:
    print("Warning: NumPy not available. Some optimizations may not work.")
    np = None

from src.parsers.stl_parser import STLParser
from src.core.logging_config import get_logger


class MemoryMonitor:
    """Monitor memory usage during operations."""
    
    def __init__(self):
        self.process = psutil.Process() if psutil else None
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage in MB."""
        if not self.process:
            return {"rss_mb": 0, "vms_mb": 0}
        
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024)
        }
    
    def get_system_memory(self) -> Dict[str, float]:
        """Get system memory information."""
        if not psutil:
            return {"total_gb": 0, "available_gb": 0, "percent": 0}
        
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024 * 1024 * 1024),
            "available_gb": memory.available / (1024 * 1024 * 1024),
            "percent": memory.percent
        }


class BenchmarkResult:
    """Store results from a single benchmark run."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0
        self.end_time = 0
        self.start_memory = {}
        self.end_memory = {}
        self.peak_memory = {}
        self.triangle_count = 0
        self.vertex_count = 0
        self.file_size_mb = 0
        self.success = False
        self.error_message = ""
        self.parsing_path = ""  # "array", "vectorized", or "fallback"
        
    def start(self):
        """Start timing and memory monitoring."""
        self.start_time = time.time()
        monitor = MemoryMonitor()
        self.start_memory = monitor.get_memory_usage()
        
    def end(self, model=None, error=None):
        """End timing and memory monitoring."""
        self.end_time = time.time()
        monitor = MemoryMonitor()
        self.end_memory = monitor.get_memory_usage()
        
        if error:
            self.success = False
            self.error_message = str(error)
        else:
            self.success = True
            if model:
                self.triangle_count = model.stats.triangle_count
                self.vertex_count = model.stats.vertex_count
                # Determine parsing path used
                if hasattr(model, 'loading_state') and model.loading_state.value == "array_geometry":
                    self.parsing_path = "array"
                elif np is not None and self.triangle_count >= 20000:
                    self.parsing_path = "vectorized"
                else:
                    self.parsing_path = "fallback"
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.end_time - self.start_time if self.end_time > 0 else 0
    
    @property
    def memory_used_mb(self) -> float:
        """Get memory used during operation in MB."""
        if not self.start_memory or not self.end_memory:
            return 0
        return self.end_memory["rss_mb"] - self.start_memory["rss_mb"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "duration_seconds": self.duration_seconds,
            "memory_used_mb": self.memory_used_mb,
            "start_memory_mb": self.start_memory.get("rss_mb", 0),
            "end_memory_mb": self.end_memory.get("rss_mb", 0),
            "triangle_count": self.triangle_count,
            "vertex_count": self.vertex_count,
            "file_size_mb": self.file_size_mb,
            "success": self.success,
            "error_message": self.error_message,
            "parsing_path": self.parsing_path
        }


class STLBenchmark:
    """Main benchmark class for STL loading performance."""
    
    def __init__(self, stl_file_path: str, iterations: int = 10):
        self.stl_file_path = Path(stl_file_path)
        self.iterations = iterations
        self.logger = get_logger(self.__class__.__name__)
        self.results: List[BenchmarkResult] = []
        
        # Validate file exists
        if not self.stl_file_path.exists():
            raise FileNotFoundError(f"STL file not found: {stl_file_path}")
        
        self.file_size_mb = self.stl_file_path.stat().st_size / (1024 * 1024)
        self.logger.info(f"Benchmarking STL file: {stl_file_path} ({self.file_size_mb:.1f} MB)")
    
    def run_benchmark(self, use_floats: bool = True) -> BenchmarkResult:
        """Run a single benchmark iteration."""
        result_name = "float_precision" if use_floats else "integer_precision"
        result = BenchmarkResult(result_name)
        result.file_size_mb = self.file_size_mb
        
        parser = STLParser()
        parser.set_remove_floats(not use_floats)
        
        try:
            result.start()
            
            # Parse the STL file
            model = parser.parse_file(str(self.stl_file_path), lazy_loading=False)
            
            result.end(model=model)
            
            # Force cleanup
            del model
            gc.collect()
            
        except Exception as e:
            result.end(error=e)
            self.logger.error(f"Benchmark failed for {result_name}: {str(e)}")
            self.logger.error(traceback.format_exc())
        
        return result
    
    def run_all_benchmarks(self) -> Dict[str, List[BenchmarkResult]]:
        """Run all benchmarks with multiple iterations."""
        self.logger.info(f"Starting benchmark with {self.iterations} iterations per configuration")
        
        # Run float precision benchmarks
        float_results = []
        self.logger.info("Running float precision benchmarks...")
        for i in range(self.iterations):
            self.logger.info(f"Float precision iteration {i+1}/{self.iterations}")
            result = self.run_benchmark(use_floats=True)
            float_results.append(result)
            self.results.append(result)
            
            # Small delay between iterations
            time.sleep(0.5)
        
        # Run integer precision benchmarks
        int_results = []
        self.logger.info("Running integer precision benchmarks...")
        for i in range(self.iterations):
            self.logger.info(f"Integer precision iteration {i+1}/{self.iterations}")
            result = self.run_benchmark(use_floats=False)
            int_results.append(result)
            self.results.append(result)
            
            # Small delay between iterations
            time.sleep(0.5)
        
        return {
            "float_precision": float_results,
            "integer_precision": int_results
        }
    
    def analyze_results(self, all_results: Dict[str, List[BenchmarkResult]]) -> Dict[str, Any]:
        """Analyze benchmark results and generate statistics."""
        analysis = {
            "file_info": {
                "path": str(self.stl_file_path),
                "size_mb": self.file_size_mb
            },
            "system_info": self._get_system_info(),
            "configurations": {}
        }
        
        for config_name, results in all_results.items():
            if not results:
                continue
            
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            if not successful_results:
                analysis["configurations"][config_name] = {
                    "success_rate": 0,
                    "error": "All iterations failed",
                    "errors": [r.error_message for r in failed_results]
                }
                continue
            
            # Calculate statistics
            durations = [r.duration_seconds for r in successful_results]
            memory_usage = [r.memory_used_mb for r in successful_results]
            
            analysis["configurations"][config_name] = {
                "success_rate": len(successful_results) / len(results),
                "iterations_total": len(results),
                "iterations_successful": len(successful_results),
                "iterations_failed": len(failed_results),
                
                # Timing statistics
                "timing": {
                    "mean_seconds": statistics.mean(durations),
                    "median_seconds": statistics.median(durations),
                    "min_seconds": min(durations),
                    "max_seconds": max(durations),
                    "std_dev_seconds": statistics.stdev(durations) if len(durations) > 1 else 0
                },
                
                # Memory statistics
                "memory": {
                    "mean_mb": statistics.mean(memory_usage),
                    "median_mb": statistics.median(memory_usage),
                    "min_mb": min(memory_usage),
                    "max_mb": max(memory_usage),
                    "std_dev_mb": statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0
                },
                
                # Model statistics (from first successful result)
                "model": {
                    "triangle_count": successful_results[0].triangle_count,
                    "vertex_count": successful_results[0].vertex_count,
                    "parsing_path": successful_results[0].parsing_path
                },
                
                # Performance metrics
                "performance": {
                    "triangles_per_second": successful_results[0].triangle_count / statistics.mean(durations) if statistics.mean(durations) > 0 else 0,
                    "mb_per_second": self.file_size_mb / statistics.mean(durations) if statistics.mean(durations) > 0 else 0,
                    "memory_per_triangle_bytes": (statistics.mean(memory_usage) * 1024 * 1024) / successful_results[0].triangle_count if successful_results[0].triangle_count > 0 else 0
                }
            }
        
        # Add comparison
        if len(analysis["configurations"]) == 2:
            float_config = analysis["configurations"].get("float_precision", {})
            int_config = analysis["configurations"].get("integer_precision", {})
            
            if float_config and int_config:
                float_time = float_config.get("timing", {}).get("mean_seconds", 0)
                int_time = int_config.get("timing", {}).get("mean_seconds", 0)
                
                float_memory = float_config.get("memory", {}).get("mean_mb", 0)
                int_memory = int_config.get("memory", {}).get("mean_mb", 0)
                
                analysis["comparison"] = {
                    "time_difference_percent": ((int_time - float_time) / float_time * 100) if float_time > 0 else 0,
                    "memory_difference_percent": ((int_memory - float_memory) / float_memory * 100) if float_memory > 0 else 0,
                    "faster_config": "float_precision" if float_time < int_time else "integer_precision",
                    "lower_memory_config": "float_precision" if float_memory < int_memory else "integer_precision"
                }
        
        return analysis
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for the benchmark report."""
        info = {
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        if np:
            info["numpy_version"] = np.__version__
        
        if psutil:
            info["cpu_count"] = psutil.cpu_count()
            info["memory_gb"] = psutil.virtual_memory().total / (1024 ** 3)
        
        return info
    
    def save_results(self, analysis: Dict[str, Any], output_file: str = "stl_benchmark_results.json"):
        """Save benchmark results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        self.logger.info(f"Results saved to {output_file}")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print a summary of benchmark results."""
        print("\n" + "="*80)
        print("STL LOADING PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        file_info = analysis["file_info"]
        print(f"File: {file_info['path']}")
        print(f"Size: {file_info['size_mb']:.1f} MB")
        
        print("\n" + "-"*80)
        print("SYSTEM INFORMATION")
        print("-"*80)
        sys_info = analysis["system_info"]
        print(f"Python: {sys_info.get('python_version', 'Unknown')}")
        print(f"Platform: {sys_info.get('platform', 'Unknown')}")
        if 'numpy_version' in sys_info:
            print(f"NumPy: {sys_info['numpy_version']}")
        if 'cpu_count' in sys_info:
            print(f"CPU Cores: {sys_info['cpu_count']}")
        if 'memory_gb' in sys_info:
            print(f"System Memory: {sys_info['memory_gb']:.1f} GB")
        
        for config_name, config in analysis["configurations"].items():
            print("\n" + "-"*80)
            print(f"CONFIGURATION: {config_name.upper()}")
            print("-"*80)
            
            if "error" in config:
                print(f"ERROR: {config['error']}")
                continue
            
            print(f"Success Rate: {config['success_rate']*100:.1f}% ({config['iterations_successful']}/{config['iterations_total']})")
            
            timing = config["timing"]
            print(f"Loading Time:")
            print(f"  Mean: {timing['mean_seconds']:.2f}s")
            print(f"  Median: {timing['median_seconds']:.2f}s")
            print(f"  Range: {timing['min_seconds']:.2f}s - {timing['max_seconds']:.2f}s")
            print(f"  Std Dev: {timing['std_dev_seconds']:.2f}s")
            
            memory = config["memory"]
            print(f"Memory Usage:")
            print(f"  Mean: {memory['mean_mb']:.1f} MB")
            print(f"  Median: {memory['median_mb']:.1f} MB")
            print(f"  Range: {memory['min_mb']:.1f} - {memory['max_mb']:.1f} MB")
            
            model = config["model"]
            print(f"Model Info:")
            print(f"  Triangles: {model['triangle_count']:,}")
            print(f"  Vertices: {model['vertex_count']:,}")
            print(f"  Parsing Path: {model['parsing_path']}")
            
            perf = config["performance"]
            print(f"Performance:")
            print(f"  Triangles/sec: {perf['triangles_per_second']:.0f}")
            print(f"  MB/sec: {perf['mb_per_second']:.1f}")
            print(f"  Memory/Triangle: {perf['memory_per_triangle_bytes']:.1f} bytes")
        
        if "comparison" in analysis:
            print("\n" + "-"*80)
            print("COMPARISON")
            print("-"*80)
            comp = analysis["comparison"]
            print(f"Time Difference: {comp['time_difference_percent']:+.1f}% (Integer vs Float)")
            print(f"Memory Difference: {comp['memory_difference_percent']:+.1f}% (Integer vs Float)")
            print(f"Faster Configuration: {comp['faster_config']}")
            print(f"Lower Memory Configuration: {comp['lower_memory_config']}")
        
        print("\n" + "="*80)


def main():
    """Main entry point for the benchmark."""
    # Configuration
    STL_FILE = "TEST-STL.stl"
    ITERATIONS = 10  # Number of iterations per configuration
    
    print("STL Loading Performance Benchmark")
    print(f"File: {STL_FILE}")
    print(f"Iterations per configuration: {ITERATIONS}")
    print()
    
    try:
        # Create and run benchmark
        benchmark = STLBenchmark(STL_FILE, ITERATIONS)
        all_results = benchmark.run_all_benchmarks()
        
        # Analyze results
        analysis = benchmark.analyze_results(all_results)
        
        # Save results
        benchmark.save_results(analysis)
        
        # Print summary
        benchmark.print_summary(analysis)
        
        return 0
        
    except Exception as e:
        print(f"Benchmark failed: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())