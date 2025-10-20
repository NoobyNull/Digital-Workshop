#!/usr/bin/env python3
"""
Multi-File STL Loading Performance Benchmark

This script benchmarks STL file loading performance across multiple files
comparing float precision vs. integer precision loading.

It randomly selects 10 STL files from the network location and tests both
precision modes on the same files for comprehensive comparison.

Usage:
    python stl_multi_file_benchmark.py
"""

import gc
import json
import os
import random
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


class FileBenchmarkResult:
    """Store results from a single file benchmark run."""
    
    def __init__(self, file_path: str, precision_mode: str):
        self.file_path = file_path
        self.precision_mode = precision_mode  # "float" or "integer"
        self.start_time = 0
        self.end_time = 0
        self.start_memory = {}
        self.end_memory = {}
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
            "file_path": self.file_path,
            "precision_mode": self.precision_mode,
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


class MultiFileSTLBenchmark:
    """Multi-file benchmark class for STL loading performance."""
    
    def __init__(self, network_path: str, num_files: int = 10, iterations: int = 3):
        self.network_path = network_path
        self.num_files = num_files
        self.iterations = iterations
        self.logger = get_logger(self.__class__.__name__)
        self.results: List[FileBenchmarkResult] = []
        self.selected_files: List[str] = []
        
    def discover_stl_files(self) -> List[str]:
        """Discover all STL files in the network location."""
        stl_files = []
        try:
            network_path = Path(self.network_path)
            if not network_path.exists():
                raise FileNotFoundError(f"Network path not found: {self.network_path}")
            
            # Find all STL files
            for stl_file in network_path.glob("*.stl"):
                if stl_file.is_file():
                    stl_files.append(str(stl_file))
            
            # Also check for uppercase STL
            for stl_file in network_path.glob("*.STL"):
                if stl_file.is_file():
                    stl_files.append(str(stl_file))
            
            self.logger.info(f"Found {len(stl_files)} STL files in network location")
            return stl_files
            
        except Exception as e:
            self.logger.error(f"Error discovering STL files: {str(e)}")
            raise
    
    def select_random_files(self) -> List[str]:
        """Select random files for benchmarking."""
        all_files = self.discover_stl_files()
        
        if len(all_files) < self.num_files:
            self.logger.warning(f"Only {len(all_files)} files found, using all of them")
            return all_files
        
        selected = random.sample(all_files, self.num_files)
        self.selected_files = selected
        
        # Log selected files with sizes
        self.logger.info(f"Selected {len(selected)} random files for benchmarking:")
        for file_path in selected:
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            self.logger.info(f"  - {Path(file_path).name}: {size_mb:.1f} MB")
        
        return selected
    
    def run_single_file_benchmark(self, file_path: str, use_floats: bool) -> FileBenchmarkResult:
        """Run benchmark on a single file."""
        precision_mode = "float" if use_floats else "integer"
        result = FileBenchmarkResult(file_path, precision_mode)
        
        # Get file size
        try:
            result.file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        except Exception:
            result.file_size_mb = 0
        
        parser = STLParser()
        parser.set_remove_floats(not use_floats)
        
        try:
            result.start()
            
            # Parse the STL file
            model = parser.parse_file(file_path, lazy_loading=False)
            
            result.end(model=model)
            
            # Force cleanup
            del model
            gc.collect()
            
        except Exception as e:
            result.end(error=e)
            self.logger.error(f"Benchmark failed for {precision_mode} precision on {Path(file_path).name}: {str(e)}")
        
        return result
    
    def run_all_benchmarks(self) -> Dict[str, List[FileBenchmarkResult]]:
        """Run all benchmarks on selected files."""
        if not self.selected_files:
            self.select_random_files()
        
        all_results = {
            "float_precision": [],
            "integer_precision": []
        }
        
        self.logger.info(f"Starting multi-file benchmark with {len(self.selected_files)} files, {self.iterations} iterations each")
        
        # Run benchmarks for each file
        for file_path in self.selected_files:
            file_name = Path(file_path).name
            self.logger.info(f"Benchmarking file: {file_name}")
            
            # Test float precision
            float_results = []
            for i in range(self.iterations):
                self.logger.info(f"  Float precision iteration {i+1}/{self.iterations}")
                result = self.run_single_file_benchmark(file_path, use_floats=True)
                float_results.append(result)
                self.results.append(result)
                time.sleep(0.2)  # Small delay between iterations
            
            # Test integer precision
            int_results = []
            for i in range(self.iterations):
                self.logger.info(f"  Integer precision iteration {i+1}/{self.iterations}")
                result = self.run_single_file_benchmark(file_path, use_floats=False)
                int_results.append(result)
                self.results.append(result)
                time.sleep(0.2)  # Small delay between iterations
            
            all_results["float_precision"].extend(float_results)
            all_results["integer_precision"].extend(int_results)
            
            # Small delay between files
            time.sleep(0.5)
        
        return all_results
    
    def analyze_results(self, all_results: Dict[str, List[FileBenchmarkResult]]) -> Dict[str, Any]:
        """Analyze benchmark results and generate statistics."""
        analysis = {
            "benchmark_info": {
                "network_path": self.network_path,
                "num_files_tested": len(self.selected_files),
                "iterations_per_file": self.iterations,
                "total_iterations": len(self.results)
            },
            "system_info": self._get_system_info(),
            "file_summary": [],
            "configurations": {}
        }
        
        # File-by-file summary
        for file_path in self.selected_files:
            file_name = Path(file_path).name
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            
            # Get results for this file
            float_results = [r for r in all_results["float_precision"] if r.file_path == file_path and r.success]
            int_results = [r for r in all_results["integer_precision"] if r.file_path == file_path and r.success]
            
            file_summary = {
                "file_name": file_name,
                "file_size_mb": file_size_mb,
                "float_precision": {
                    "success_rate": len(float_results) / self.iterations if self.iterations > 0 else 0,
                    "mean_time": statistics.mean([r.duration_seconds for r in float_results]) if float_results else 0,
                    "mean_memory": statistics.mean([r.memory_used_mb for r in float_results]) if float_results else 0,
                    "triangles": float_results[0].triangle_count if float_results else 0
                },
                "integer_precision": {
                    "success_rate": len(int_results) / self.iterations if self.iterations > 0 else 0,
                    "mean_time": statistics.mean([r.duration_seconds for r in int_results]) if int_results else 0,
                    "mean_memory": statistics.mean([r.memory_used_mb for r in int_results]) if int_results else 0,
                    "triangles": int_results[0].triangle_count if int_results else 0
                }
            }
            
            # Calculate comparison for this file
            if float_results and int_results:
                float_time = file_summary["float_precision"]["mean_time"]
                int_time = file_summary["integer_precision"]["mean_time"]
                float_memory = file_summary["float_precision"]["mean_memory"]
                int_memory = file_summary["integer_precision"]["mean_memory"]
                
                file_summary["comparison"] = {
                    "time_difference_percent": ((int_time - float_time) / float_time * 100) if float_time > 0 else 0,
                    "memory_difference_percent": ((int_memory - float_memory) / float_memory * 100) if float_memory > 0 else 0,
                    "faster_precision": "float" if float_time < int_time else "integer" if int_time < float_time else "equal",
                    "lower_memory_precision": "float" if float_memory < int_memory else "integer" if int_memory < float_memory else "equal"
                }
            
            analysis["file_summary"].append(file_summary)
        
        # Overall configuration analysis
        for config_name, results in all_results.items():
            if not results:
                continue
            
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            if not successful_results:
                analysis["configurations"][config_name] = {
                    "success_rate": 0,
                    "error": "All iterations failed",
                    "errors": list(set([r.error_message for r in failed_results]))
                }
                continue
            
            # Calculate statistics
            durations = [r.duration_seconds for r in successful_results]
            memory_usage = [r.memory_used_mb for r in successful_results]
            file_sizes = [r.file_size_mb for r in successful_results]
            triangle_counts = [r.triangle_count for r in successful_results]
            
            analysis["configurations"][config_name] = {
                "success_rate": len(successful_results) / len(results),
                "iterations_total": len(results),
                "iterations_successful": len(successful_results),
                "iterations_failed": len(failed_results),
                
                # File statistics
                "files": {
                    "count": len(set([r.file_path for r in successful_results])),
                    "size_mb": {
                        "mean": statistics.mean(file_sizes),
                        "median": statistics.median(file_sizes),
                        "min": min(file_sizes),
                        "max": max(file_sizes)
                    }
                },
                
                # Model statistics
                "models": {
                    "triangles": {
                        "mean": statistics.mean(triangle_counts),
                        "median": statistics.median(triangle_counts),
                        "min": min(triangle_counts),
                        "max": max(triangle_counts),
                        "total": sum(triangle_counts)
                    }
                },
                
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
                
                # Performance metrics
                "performance": {
                    "triangles_per_second": sum(triangle_counts) / sum(durations) if sum(durations) > 0 else 0,
                    "mb_per_second": sum(file_sizes) / sum(durations) if sum(durations) > 0 else 0,
                    "memory_per_triangle_bytes": (statistics.mean(memory_usage) * 1024 * 1024) / statistics.mean(triangle_counts) if statistics.mean(triangle_counts) > 0 else 0
                }
            }
        
        # Add overall comparison
        if len(analysis["configurations"]) == 2:
            float_config = analysis["configurations"].get("float_precision", {})
            int_config = analysis["configurations"].get("integer_precision", {})
            
            if float_config and int_config:
                float_time = float_config.get("timing", {}).get("mean_seconds", 0)
                int_time = int_config.get("timing", {}).get("mean_seconds", 0)
                
                float_memory = float_config.get("memory", {}).get("mean_mb", 0)
                int_memory = int_config.get("memory", {}).get("mean_mb", 0)
                
                analysis["overall_comparison"] = {
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
    
    def save_results(self, analysis: Dict[str, Any], output_file: str = "stl_multi_file_benchmark_results.json"):
        """Save benchmark results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Results saved to {output_file}")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print a summary of benchmark results."""
        print("\n" + "="*80)
        print("MULTI-FILE STL LOADING PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        benchmark_info = analysis["benchmark_info"]
        print(f"Network Path: {benchmark_info['network_path']}")
        print(f"Files Tested: {benchmark_info['num_files_tested']}")
        print(f"Iterations per File: {benchmark_info['iterations_per_file']}")
        print(f"Total Iterations: {benchmark_info['total_iterations']}")
        
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
        
        print("\n" + "-"*80)
        print("FILE-BY-FILE RESULTS")
        print("-"*80)
        for file_summary in analysis["file_summary"]:
            print(f"\nFile: {file_summary['file_name']} ({file_summary['file_size_mb']:.1f} MB)")
            
            float_prec = file_summary["float_precision"]
            int_prec = file_summary["integer_precision"]
            
            print(f"  Float Precision: {float_prec['mean_time']:.3f}s, {float_prec['mean_memory']:.1f}MB, {float_prec['triangles']:,} triangles")
            print(f"  Integer Precision: {int_prec['mean_time']:.3f}s, {int_prec['mean_memory']:.1f}MB, {int_prec['triangles']:,} triangles")
            
            if "comparison" in file_summary:
                comp = file_summary["comparison"]
                print(f"  Comparison: {comp['time_difference_percent']:+.1f}% time, {comp['memory_difference_percent']:+.1f}% memory")
                print(f"  Winner: {comp['faster_precision']} time, {comp['lower_memory_precision']} memory")
        
        print("\n" + "-"*80)
        print("OVERALL CONFIGURATION RESULTS")
        print("-"*80)
        
        for config_name, config in analysis["configurations"].items():
            print(f"\n{config_name.upper()}:")
            
            if "error" in config:
                print(f"  ERROR: {config['error']}")
                continue
            
            print(f"  Success Rate: {config['success_rate']*100:.1f}% ({config['iterations_successful']}/{config['iterations_total']})")
            print(f"  Files: {config['files']['count']}")
            print(f"  File Sizes: {config['files']['size_mb']['min']:.1f} - {config['files']['size_mb']['max']:.1f} MB (mean: {config['files']['size_mb']['mean']:.1f})")
            print(f"  Total Triangles: {config['models']['triangles']['total']:,}")
            
            timing = config["timing"]
            print(f"  Loading Time: {timing['mean_seconds']:.3f}s mean (range: {timing['min_seconds']:.3f}s - {timing['max_seconds']:.3f}s)")
            
            memory = config["memory"]
            print(f"  Memory Usage: {memory['mean_mb']:.1f}MB mean (range: {memory['min_mb']:.1f} - {memory['max_mb']:.1f} MB)")
            
            perf = config["performance"]
            print(f"  Performance: {perf['triangles_per_second']:.0f} triangles/sec, {perf['mb_per_second']:.1f} MB/sec")
        
        if "overall_comparison" in analysis:
            print("\n" + "-"*80)
            print("OVERALL COMPARISON")
            print("-"*80)
            comp = analysis["overall_comparison"]
            print(f"Time Difference: {comp['time_difference_percent']:+.1f}% (Integer vs Float)")
            print(f"Memory Difference: {comp['memory_difference_percent']:+.1f}% (Integer vs Float)")
            print(f"Faster Configuration: {comp['faster_config']}")
            print(f"Lower Memory Configuration: {comp['lower_memory_config']}")
        
        print("\n" + "="*80)


def main():
    """Main entry point for the multi-file benchmark."""
    # Configuration
    NETWORK_PATH = r"\\Synology\stl\Massive CNC Router STL Clipart Collection Ripped From Random Google Drive 1100+ STL"
    NUM_FILES = 10
    ITERATIONS = 3  # Number of iterations per file per configuration
    
    print("Multi-File STL Loading Performance Benchmark")
    print(f"Network Path: {NETWORK_PATH}")
    print(f"Files to Test: {NUM_FILES}")
    print(f"Iterations per Configuration: {ITERATIONS}")
    print()
    
    try:
        # Create and run benchmark
        benchmark = MultiFileSTLBenchmark(NETWORK_PATH, NUM_FILES, ITERATIONS)
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