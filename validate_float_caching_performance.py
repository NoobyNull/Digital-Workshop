#!/usr/bin/env python3
"""
Float Caching Performance Validation Script

This script validates the performance improvement assumptions for float caching
by measuring actual parsing bottlenecks and demonstrating potential improvements.
"""

import sys
import time
import struct
from pathlib import Path
from typing import List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: NumPy not available, some tests will be skipped")

from src.core.float_cache_analyzer import get_float_cache_analyzer
from src.core.logging_config import get_logger


def create_test_stl_data(triangle_count: int) -> bytes:
    """
    Create synthetic STL binary data for testing.
    
    Args:
        triangle_count: Number of triangles to generate
        
    Returns:
        Binary STL data
    """
    # STL header (80 bytes)
    header = b"Synthetic STL for performance testing".ljust(80, b'\x00')
    
    # Triangle count (4 bytes)
    count_bytes = struct.pack('<I', triangle_count)
    
    # Generate triangle data
    triangle_data = b""
    for i in range(triangle_count):
        # Normal vector (3 floats)
        normal = (0.0, 0.0, 1.0)
        # Three vertices (9 floats total)
        v1 = (i * 0.1, i * 0.1, 0.0)
        v2 = ((i + 1) * 0.1, i * 0.1, 0.0)
        v3 = (i * 0.1, (i + 1) * 0.1, 0.0)
        
        # Pack triangle data (12 floats + 2 bytes attribute)
        triangle_bytes = struct.pack('<12fH', 
                                   normal[0], normal[1], normal[2],  # normal
                                   v1[0], v1[1], v1[2],               # vertex 1
                                   v2[0], v2[1], v2[2],               # vertex 2
                                   v3[0], v3[1], v3[2],               # vertex 3
                                   0)                                   # attribute
        
        triangle_data += triangle_bytes
    
    return header + count_bytes + triangle_data


def parse_with_struct_unpack(data: bytes) -> Tuple[List[Tuple[float, ...]], float]:
    """
    Parse STL data using traditional struct.unpack approach.
    
    Args:
        data: Binary STL data
        
    Returns:
        Tuple of (parsed_triangles, parsing_time)
    """
    start_time = time.time()
    
    # Skip header and get triangle count
    triangle_count = struct.unpack('<I', data[80:84])[0]
    
    triangles = []
    triangle_data = data[84:]
    
    for i in range(triangle_count):
        offset = i * 50  # 50 bytes per triangle
        triangle_bytes = triangle_data[offset:offset + 50]
        
        # Unpack 12 floats + 2 bytes attribute
        values = struct.unpack('<12fH', triangle_bytes)
        triangles.append(values[:12])  # Only store the 12 floats
    
    parse_time = time.time() - start_time
    return triangles, parse_time


def parse_with_numpy_array(data: bytes) -> Tuple[np.ndarray, float]:
    """
    Parse STL data using NumPy array approach.
    
    Args:
        data: Binary STL data
        
    Returns:
        Tuple of (float_array, parsing_time)
    """
    if not HAS_NUMPY:
        raise RuntimeError("NumPy not available")
    
    start_time = time.time()
    
    # Skip header and get triangle count
    triangle_count = struct.unpack('<I', data[80:84])[0]
    
    # Extract triangle data
    triangle_data = data[84:]
    
    # Convert to NumPy array and extract floats
    u8 = np.frombuffer(triangle_data, dtype=np.uint8).reshape(triangle_count, 50)
    floats = u8[:, :48].copy().view('<f4').reshape(triangle_count, 12)
    
    parse_time = time.time() - start_time
    return floats, parse_time


def simulate_cache_load(float_arrays: np.ndarray) -> float:
    """
    Simulate loading from cache (just memory copy time).
    
    Args:
        float_arrays: NumPy arrays to "load"
        
    Returns:
        Time taken for cache load simulation
    """
    start_time = time.time()
    
    # Simulate cache load by copying arrays
    cached_arrays = float_arrays.copy()
    
    # Force the copy to complete
    _ = cached_arrays.sum()
    
    return time.time() - start_time


def run_performance_validation():
    """Run comprehensive performance validation tests."""
    analyzer = get_float_cache_analyzer()
    
    print("=== Float Caching Performance Validation ===\n")
    
    # Test different file sizes
    test_sizes = [1000, 10000, 100000]  # triangles
    
    for triangle_count in test_sizes:
        print(f"Testing with {triangle_count:,} triangles...")
        
        # Create test data
        test_data = create_test_stl_data(triangle_count)
        file_size_mb = len(test_data) / (1024 * 1024)
        
        # Create temporary file path for analysis
        temp_file = Path(f"temp_test_{triangle_count}.stl")
        temp_file.write_bytes(test_data)
        
        try:
            # Start analysis
            context = analyzer.start_analysis(str(temp_file))
            
            # Test 1: Traditional struct.unpack approach
            print("  1. Testing struct.unpack approach...")
            analyzer.mark_float_decode_start(context)
            analyzer.mark_struct_unpack_start(context)
            
            _, struct_time = parse_with_struct_unpack(test_data)
            
            analyzer.mark_struct_unpack_end(context)
            analyzer.mark_float_decode_end(context)
            
            print(f"     Struct unpack time: {struct_time:.4f}s")
            if struct_time > 0:
                print(f"     Triangles per second: {triangle_count / struct_time:.0f}")
            else:
                print(f"     Triangles per second: Too fast to measure (< {1/0.000001:.0f})")
            
            # Test 2: NumPy array approach (if available)
            if HAS_NUMPY:
                print("  2. Testing NumPy array approach...")
                analyzer.mark_array_creation_start(context)
                
                float_arrays, numpy_time = parse_with_numpy_array(test_data)
                
                analyzer.mark_array_creation_end(context)
                
                print(f"     NumPy parse time: {numpy_time:.4f}s")
                if numpy_time > 0:
                    print(f"     Speedup vs struct: {struct_time / numpy_time:.2f}x")
                else:
                    print("     Speedup vs struct: Too fast to measure")
                
                # Test 3: Simulated cache load
                print("  3. Testing simulated cache load...")
                cache_time = simulate_cache_load(float_arrays)
                analyzer.mark_cache_hit(context, cache_time)
                
                print(f"     Cache load time: {cache_time:.4f}s")
                if cache_time > 0:
                    if numpy_time > 0:
                        print(f"     Speedup vs parsing: {numpy_time / cache_time:.2f}x")
                    print(f"     Speedup vs struct: {struct_time / cache_time:.2f}x")
                else:
                    print("     Speedup vs parsing: Too fast to measure")
            
            # End analysis
            metrics = analyzer.end_analysis(context, triangle_count)
            
            print("  Results:")
            print(f"     File size: {file_size_mb:.2f} MB")
            print(f"     Total parse time: {metrics.total_parse_time:.4f}s")
            print(f"     Float decode time: {metrics.float_decode_time:.4f}s")
            print(f"     Struct unpack time: {metrics.struct_unpack_time:.4f}s")
            print(f"     Memory delta: {metrics.final_memory_mb - metrics.baseline_memory_mb:.2f} MB")
            print(f"     IO throughput: {metrics.io_read_mb_per_sec:.2f} MB/s")
            print()
            
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    # Generate comprehensive report
    print("=== Performance Summary ===")
    summary = analyzer.get_performance_summary()
    
    if "error" not in summary:
        print(f"Files processed: {summary['summary']['total_files_processed']}")
        print(f"Total triangles: {summary['summary']['total_triangles_processed']:,}")
        print(f"Average parse time: {summary['timing']['average_total_parse_time']:.4f}s")
        print(f"Float decode percentage: {summary['timing']['float_decode_percentage']:.1f}%")
        print(f"Struct unpack percentage: {summary['timing']['struct_unpack_percentage']:.1f}%")
        
        if HAS_NUMPY:
            print(f"Cache hit ratio: {summary['summary']['cache_hit_ratio']:.1%}")
            print(f"Cache time savings: {summary['cache_performance']['time_savings_percentage']:.1f}%")
            print(f"Average cache load time: {summary['cache_performance']['average_cache_load_time']:.4f}s")
        
        print(f"Average memory delta: {summary['memory']['average_memory_delta_mb']:.2f} MB")
        print(f"Average throughput: {summary['throughput']['triangles_per_second']:.0f} triangles/sec")
        print()
    
    # Validate assumptions
    print("=== Assumption Validation ===")
    validations = analyzer.validate_performance_assumptions()
    
    for assumption, result in validations.items():
        status = "✓ VALIDATED" if result else "✗ NOT VALIDATED"
        status_symbol = "VALIDATED" if result else "NOT VALIDATED"
        print(f"{assumption}: {status_symbol}")
    
    print()
    
    # Recommendations
    print("=== Recommendations ===")
    
    if validations.get("float_decode_is_bottleneck", False):
        print("+ Float decoding is a significant bottleneck - caching will provide benefits")
    else:
        print("! Float decoding is not the primary bottleneck - investigate other areas")
    
    if validations.get("struct_unpack_is_major_component", False):
        print("+ Struct unpack operations are major component - focus optimization here")
    else:
        print("! Struct unpack is not the main issue - look at other parsing stages")
    
    if HAS_NUMPY:
        if validations.get("cache_provides_significant_savings", False):
            print("+ Cache provides significant time savings - implementation recommended")
        else:
            print("! Cache savings are minimal - may not justify implementation cost")
        
        if validations.get("memory_overhead_is_acceptable", False):
            print("+ Memory overhead is acceptable - proceed with implementation")
        else:
            print("! Memory overhead is high - consider memory optimization strategies")
    
    if not HAS_NUMPY:
        print("! NumPy not available - install NumPy for better performance analysis")
    
    print()
    
    # Cleanup
    analyzer.reset_metrics()
    print("Validation completed.")


if __name__ == "__main__":
    run_performance_validation()