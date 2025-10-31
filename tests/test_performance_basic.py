#!/usr/bin/env python3
"""
Basic Performance Test for Candy-Cadence Application

This test verifies that the core application components can handle basic operations
efficiently and meet performance requirements.
"""

import time
import psutil
import os
from pathlib import Path

def test_import_performance():
    """Test import performance of core modules."""
    print("Testing Import Performance...")
    
    start_time = time.time()
    
    # Test core imports
    from src.core.data_structures import Triangle, ModelStats, Model
    from src.parsers.format_detector import FormatDetector
    from src.core.interfaces.parser_interfaces import ModelFormat
    
    import_time = time.time() - start_time
    print(f"  Core imports: {import_time:.3f}s")
    
    return import_time < 1.0  # Should import in under 1 second

def test_format_detection_performance():
    """Test format detection performance."""
    print("Testing Format Detection Performance...")
    
    detector = FormatDetector()
    
    # Test with various file extensions
    test_files = [
        Path("test.stl"),
        Path("test.obj"), 
        Path("test.3mf"),
        Path("test.step"),
        Path("test.unknown")
    ]
    
    start_time = time.time()
    
    for test_file in test_files:
        format_result = detector.detect_format(test_file)
        print(f"  {test_file.suffix}: {format_result}")
    
    detection_time = time.time() - start_time
    print(f"  Format detection (5 files): {detection_time:.3f}s")
    
    return detection_time < 0.1  # Should detect formats quickly

def test_data_structure_performance():
    """Test data structure creation and manipulation performance."""
    print("Testing Data Structure Performance...")
    
    from src.core.data_structures import Triangle, ModelStats, Model
    
    start_time = time.time()
    
    # Create test data
    vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    normal = (0.0, 0.0, 1.0)
    
    # Test triangle creation
    triangles = []
    for i in range(1000):
        triangle = Triangle(normal=normal, vertices=vertices)
        triangles.append(triangle)
    
    # Test model stats
    stats = ModelStats(
        triangle_count=len(triangles),
        vertex_count=3,
        file_size=1024,
        parsing_time=0.1
    )
    
    # Test model creation
    model = Model(
        triangles=triangles,
        stats=stats,
        format="STL"
    )
    
    creation_time = time.time() - start_time
    print(f"  Created 1000 triangles + model: {creation_time:.3f}s")
    
    return creation_time < 0.5  # Should create data structures quickly

def test_memory_usage():
    """Test memory usage during basic operations."""
    print("Testing Memory Usage...")
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    from src.core.data_structures import Triangle, ModelStats, Model
    
    # Create larger dataset
    vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    normal = (0.0, 0.0, 1.0)
    
    triangles = []
    for i in range(10000):  # 10k triangles
        triangle = Triangle(normal=normal, vertices=vertices)
        triangles.append(triangle)
    
    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = peak_memory - initial_memory
    
    print(f"  Initial memory: {initial_memory:.1f} MB")
    print(f"  Peak memory: {peak_memory:.1f} MB") 
    print(f"  Memory used: {memory_used:.1f} MB")
    
    # Clean up
    del triangles
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_leaked = final_memory - initial_memory
    
    print(f"  Final memory: {final_memory:.1f} MB")
    print(f"  Memory leaked: {memory_leaked:.1f} MB")
    
    return memory_used < 100 and memory_leaked < 10  # Reasonable memory usage

def test_file_operations():
    """Test basic file operations performance."""
    print("Testing File Operations Performance...")
    
    # Create test file
    test_content = """solid test
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.0 1.0 0.0
    endloop
  endfacet
endsolid test"""
    
    test_file = Path("test_performance.stl")
    test_file.write_text(test_content)
    
    start_time = time.time()
    
    # Test file reading
    content = test_file.read_text()
    file_size = test_file.stat().st_size
    
    read_time = time.time() - start_time
    print(f"  File read ({file_size} bytes): {read_time:.3f}s")
    
    # Clean up
    test_file.unlink()
    
    return read_time < 0.1  # Should read files quickly

def main():
    """Run all performance tests."""
    print("Candy-Cadence Basic Performance Test")
    print("=" * 50)
    
    tests = [
        ("Import Performance", test_import_performance),
        ("Format Detection Performance", test_format_detection_performance),
        ("Data Structure Performance", test_data_structure_performance),
        ("Memory Usage", test_memory_usage),
        ("File Operations", test_file_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            results.append((test_name, status))
            print(f"Result: {status}")
        except Exception as e:
            results.append((test_name, f"ERROR: {str(e)}"))
            print(f"Result: ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        print(f"{test_name:<30} [{result}]")
        if result == "PASS":
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All performance tests PASSED")
        return 0
    else:
        print("⚠️  Some performance tests FAILED")
        return 1

if __name__ == "__main__":
    exit(main())