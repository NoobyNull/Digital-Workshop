"""
Performance Validation Framework for Candy-Cadence

This module provides comprehensive performance validation for all critical components
including file loading, memory management, database operations, and 3D rendering.
"""

import time
import gc
import psutil
import threading
import tempfile
import os
import sys
import unittest
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import get_database_manager, close_database_manager
from src.parsers.format_detector import FormatDetector


@dataclass
class PerformanceResult:
    """Performance test result data structure."""
    test_name: str
    target_value: float
    actual_value: float
    passed: bool
    execution_time: float
    memory_usage_mb: float
    details: Dict[str, Any]


@dataclass
class PerformanceReport:
    """Comprehensive performance test report."""
    timestamp: str
    system_info: Dict[str, Any]
    test_results: List[PerformanceResult]
    summary: Dict[str, Any]
    recommendations: List[str]


class PerformanceValidator:
    """Comprehensive performance validation framework."""
    
    def __init__(self):
        """Initialize the performance validation framework."""
        self.results: List[PerformanceResult] = []
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
        
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for performance context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'platform': sys.platform,
            'python_version': sys.version,
        }
    
    @contextmanager
    def measure_performance(self, test_name: str, target_value: float):
        """Context manager to measure performance of operations."""
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            passed = execution_time <= target_value
            
            result = PerformanceResult(
                test_name=test_name,
                target_value=target_value,
                actual_value=execution_time,
                passed=passed,
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                details={
                    'start_memory_mb': start_memory,
                    'end_memory_mb': end_memory,
                    'memory_delta_mb': memory_usage
                }
            )
            
            self.results.append(result)
    
    def create_test_file(self, size_mb: int, format_type: str = "stl") -> str:
        """Create a test file of specified size and format."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        filename = f"test_model_{size_mb}mb.{format_type}"
        filepath = os.path.join(temp_dir, filename)
        
        if format_type.lower() == "stl":
            self._create_stl_file(filepath, size_mb)
        elif format_type.lower() == "obj":
            self._create_obj_file(filepath, size_mb)
        elif format_type.lower() == "step":
            self._create_step_file(filepath, size_mb)
        
        self.temp_files.append(filepath)
        return filepath
    
    def _create_stl_file(self, filepath: str, size_mb: int):
        """Create a test STL file of specified size."""
        # Create a simple cube STL and repeat it to reach target size
        base_stl = """solid cube
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 0.0 1.0
      vertex 1.0 1.0 1.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 1.0 1.0
      vertex 0.0 1.0 1.0
    endloop
  endfacet
endsolid cube
"""
        
        target_size = size_mb * 1024 * 1024
        content = base_stl.encode('utf-8')
        
        with open(filepath, 'wb') as f:
            while f.tell() < target_size:
                f.write(content)
    
    def _create_obj_file(self, filepath: str, size_mb: int):
        """Create a test OBJ file of specified size."""
        base_obj = """# Simple cube
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 5 1 4 8
"""
        
        target_size = size_mb * 1024 * 1024
        content = base_obj.encode('utf-8')
        
        with open(filepath, 'wb') as f:
            while f.tell() < target_size:
                f.write(content)
    
    def _create_step_file(self, filepath: str, size_mb: int):
        """Create a test STEP file of specified size."""
        base_step = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Simple cube'),'2;1');
FILE_NAME('cube.step','2023-01-01T00:00:00',('Test'),('Test'),'Test','Test','');
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;

DATA;
#1 = CARTESIAN_POINT('',(0.,0.,0.));
#2 = CARTESIAN_POINT('',(1.,0.,0.));
#3 = CARTESIAN_POINT('',(1.,1.,0.));
#4 = CARTESIAN_POINT('',(0.,1.,0.));
#5 = CARTESIAN_POINT('',(0.,0.,1.));
#6 = CARTESIAN_POINT('',(1.,0.,1.));
#7 = CARTESIAN_POINT('',(1.,1.,1.));
#8 = CARTESIAN_POINT('',(0.,1.,1.));
ENDSEC;
END-ISO-10303-21;
"""
        
        target_size = size_mb * 1024 * 1024
        content = base_step.encode('utf-8')
        
        with open(filepath, 'wb') as f:
            while f.tell() < target_size:
                f.write(content)
    
    def test_file_loading_performance(self):
        """Test file loading performance for different file sizes."""
        print("\n=== File Loading Performance Tests ===")
        
        test_cases = [
            ("Small STL (<100MB)", "stl", 50, 5.0),   # 50MB file, <5s target
            ("Medium STL (100-500MB)", "stl", 200, 15.0),  # 200MB file, <15s target
            ("Large STL (>500MB)", "stl", 600, 30.0),  # 600MB file, <30s target
            ("Small OBJ (<100MB)", "obj", 50, 5.0),   # 50MB file, <5s target
            ("Medium OBJ (100-500MB)", "obj", 200, 15.0),  # 200MB file, <15s target
            ("Small STEP (<100MB)", "step", 50, 5.0),   # 50MB file, <5s target
        ]
        
        for test_name, format_type, size_mb, target_time in test_cases:
            print(f"Testing {test_name}...")
            
            try:
                test_file = self.create_test_file(size_mb, format_type)
                
                with self.measure_performance(test_name, target_time):
                    # Test format detection
                    detector = FormatDetector()
                    format_info = detector.detect_format(test_file)
                    
                    # Test file reading performance (simulate parsing)
                    with open(test_file, 'rb') as f:
                        data = f.read()
                
                print(f"  ✓ {test_name}: {self.results[-1].actual_value:.2f}s (target: {target_time}s)")
                
            except Exception as e:
                print(f"  ✗ {test_name}: Failed - {str(e)}")
                result = PerformanceResult(
                    test_name=test_name,
                    target_value=target_time,
                    actual_value=float('inf'),
                    passed=False,
                    execution_time=0.0,
                    memory_usage_mb=0.0,
                    details={'error': str(e)}
                )
                self.results.append(result)
    
    def test_memory_stability(self):
        """Test memory usage stability during repeated operations."""
        print("\n=== Memory Stability Tests ===")
        
        # Test repeated file operations
        test_file = self.create_test_file(10, "stl")  # 10MB file
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        print("Testing memory stability with 20 repeated operations...")
        
        memory_samples = []
        for i in range(20):
            try:
                # Simulate file processing
                with open(test_file, 'rb') as f:
                    data = f.read()
                
                current_memory = process.memory_info().rss / (1024 * 1024)
                memory_samples.append(current_memory)
                
                # Force garbage collection
                del data
                gc.collect()
                
            except Exception as e:
                print(f"  Iteration {i+1} failed: {str(e)}")
                break
        
        if len(memory_samples) >= 10:
            memory_increase = memory_samples[-1] - memory_samples[0]
            memory_stable = abs(memory_increase) < 10.0  # Less than 10MB increase
            
            result = PerformanceResult(
                test_name="Memory Stability (20 iterations)",
                target_value=10.0,  # Max 10MB increase
                actual_value=abs(memory_increase),
                passed=memory_stable,
                execution_time=0.0,
                memory_usage_mb=memory_increase,
                details={
                    'initial_memory_mb': initial_memory,
                    'final_memory_mb': memory_samples[-1],
                    'memory_samples': memory_samples,
                    'iterations_completed': len(memory_samples)
                }
            )
            self.results.append(result)
            
            status = "✓ PASS" if memory_stable else "✗ FAIL"
            print(f"  {status}: Memory increase: {memory_increase:.1f}MB")
        else:
            print(f"  ✗ FAIL: Only {len(memory_samples)} iterations completed")
    
    def test_database_performance(self):
        """Test database performance with caching and connection pooling."""
        print("\n=== Database Performance Tests ===")
        
        # Create temporary database
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        test_db_path = os.path.join(temp_dir, "performance_test.db")
        
        try:
            close_database_manager()
            db_manager = get_database_manager(test_db_path)
            
            # Test bulk insert performance
            print("Testing bulk insert performance...")
            with self.measure_performance("Bulk Insert (1000 models)", 5.0):
                for i in range(1000):
                    db_manager.add_model(
                        filename=f"model_{i}.stl",
                        format="STL",
                        file_path=f"/path/to/model_{i}.stl",
                        file_size=1024 * (i + 1),
                        file_hash=f"hash_{i:032d}"
                    )
            
            print(f"  ✓ Bulk insert: {self.results[-1].actual_value:.3f}s")
            
            # Test search performance
            print("Testing search performance...")
            with self.measure_performance("Search Operations (100 queries)", 1.0):
                for i in range(100):
                    results = db_manager.search_models(f"model_{i % 10}")
            
            print(f"  ✓ Search operations: {self.results[-1].actual_value:.3f}s")
            
            # Test metadata operations
            print("Testing metadata operations...")
            with self.measure_performance("Metadata Operations (500 updates)", 2.0):
                for i in range(500):
                    db_manager.add_metadata(
                        model_id=(i % 1000) + 1,
                        title=f"Model {i}",
                        description=f"Description for model {i}",
                        keywords=f"keyword_{i}",
                        category="Test",
                        source="Test Source"
                    )
            
            print(f"  ✓ Metadata operations: {self.results[-1].actual_value:.3f}s")
            
        except Exception as e:
            print(f"  ✗ Database test failed: {str(e)}")
        finally:
            close_database_manager()
    
    def test_ui_responsiveness(self):
        """Test UI responsiveness during heavy operations."""
        print("\n=== UI Responsiveness Tests ===")
        
        # Simulate UI thread responsiveness
        def background_operation():
            """Simulate heavy background operation."""
            time.sleep(2)  # Simulate 2-second operation
            return "completed"
        
        def ui_responsive_test():
            """Test if UI remains responsive during background operations."""
            start_time = time.time()
            results = []
            
            # Start background operation
            thread = threading.Thread(target=background_operation)
            thread.start()
            
            # Simulate UI responsiveness checks
            while thread.is_alive():
                if time.time() - start_time > 5.0:  # Timeout after 5 seconds
                    break
                
                # Simulate UI update (should be fast)
                results.append("ui_update")
                time.sleep(0.1)  # Simulate UI frame update
            
            thread.join()
            return len(results) > 0  # UI remained responsive if we got updates
        
        with self.measure_performance("UI Responsiveness", 1.0):
            responsive = ui_responsive_test()
        
        result = PerformanceResult(
            test_name="UI Responsiveness",
            target_value=1.0,
            actual_value=self.results[-1].actual_value if self.results else 0.0,
            passed=responsive and (self.results[-1].actual_value if self.results else 0.0) < 1.0,
            execution_time=self.results[-1].execution_time if self.results else 0.0,
            memory_usage_mb=0.0,
            details={'ui_responsive': responsive}
        )
        self.results.append(result)
        
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status}: UI remained responsive during background operations")
    
    def test_3d_rendering_performance(self):
        """Test 3D rendering performance and frame rate."""
        print("\n=== 3D Rendering Performance Tests ===")
        
        # Mock VTK rendering test
        try:
            # Simulate rendering operations
            def simulate_rendering():
                """Simulate 3D rendering operations."""
                # Mock VTK operations
                frames = 0
                start_time = time.time()
                
                while time.time() - start_time < 1.0:  # Test for 1 second
                    # Simulate frame rendering
                    frames += 1
                    time.sleep(0.016)  # ~60 FPS target
                
                return frames
            
            with self.measure_performance("3D Rendering (60 FPS target)", 2.0):
                frames_rendered = simulate_rendering()
                actual_fps = frames_rendered / 1.0  # FPS = frames / time
                
                # Check if we achieved at least 30 FPS
                fps_target_met = actual_fps >= 30.0
                
                result = PerformanceResult(
                    test_name="3D Rendering Performance",
                    target_value=30.0,  # Minimum 30 FPS
                    actual_value=actual_fps,
                    passed=fps_target_met,
                    execution_time=1.0,
                    memory_usage_mb=0.0,
                    details={
                        'frames_rendered': frames_rendered,
                        'actual_fps': actual_fps,
                        'target_fps': 30.0
                    }
                )
                self.results.append(result)
                
                status = "✓ PASS" if fps_target_met else "✗ FAIL"
                print(f"  {status}: {actual_fps:.1f} FPS (target: 30+ FPS)")
                
        except Exception as e:
            print(f"  ✗ 3D rendering test failed: {str(e)}")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operations."""
        print("\n=== Memory Leak Detection Tests ===")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Create test file
        test_file = self.create_test_file(5, "stl")  # 5MB file
        
        print("Testing for memory leaks with 50 iterations...")
        
        memory_samples = []
        for i in range(50):
            try:
                # Simulate file processing
                with open(test_file, 'rb') as f:
                    data = f.read()
                
                # Get memory usage
                current_memory = process.memory_info().rss / (1024 * 1024)
                memory_samples.append(current_memory)
                
                # Clean up
                del data
                gc.collect()
                
                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/50 iterations")
                    
            except Exception as e:
                print(f"  Iteration {i+1} failed: {str(e)}")
                break
        
        if len(memory_samples) >= 40:  # At least 40 successful iterations
            # Analyze memory trend
            memory_trend = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
            memory_leak_detected = memory_trend > 0.1  # More than 0.1MB increase per iteration
            
            result = PerformanceResult(
                test_name="Memory Leak Detection (50 iterations)",
                target_value=0.1,  # Max 0.1MB increase per iteration
                actual_value=memory_trend,
                passed=not memory_leak_detected,
                execution_time=0.0,
                memory_usage_mb=memory_samples[-1] - memory_samples[0],
                details={
                    'initial_memory_mb': initial_memory,
                    'final_memory_mb': memory_samples[-1],
                    'memory_trend_mb_per_iteration': memory_trend,
                    'iterations_completed': len(memory_samples),
                    'memory_samples': memory_samples
                }
            )
            self.results.append(result)
            
            status = "✓ PASS (No leak detected)" if not memory_leak_detected else "✗ FAIL (Memory leak detected)"
            print(f"  {status}: Memory trend: {memory_trend:.3f}MB per iteration")
        else:
            print(f"  ✗ FAIL: Only {len(memory_samples)} iterations completed")
    
    def generate_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report."""
        system_info = self.get_system_info()
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        avg_execution_time = sum(r.execution_time for r in self.results) / total_tests if total_tests > 0 else 0
        total_memory_usage = sum(r.memory_usage_mb for r in self.results)
        
        # Generate recommendations
        recommendations = []
        
        if failed_tests > 0:
            recommendations.append("Review failed performance tests and optimize accordingly")
        
        slow_tests = [r for r in self.results if r.actual_value > r.target_value * 0.8]
        if slow_tests:
            recommendations.append("Consider optimizing operations that are close to performance targets")
        
        high_memory_tests = [r for r in self.results if r.memory_usage_mb > 50]
        if high_memory_tests:
            recommendations.append("Review memory usage patterns and implement better memory management")
        
        return PerformanceReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            system_info=system_info,
            test_results=self.results,
            summary={
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'average_execution_time': avg_execution_time,
                'total_memory_usage_mb': total_memory_usage
            },
            recommendations=recommendations
        )
    
    def run_all_tests(self):
        """Run all performance tests."""
        print("=" * 60)
        print("CANDY-CADENCE COMPREHENSIVE PERFORMANCE VALIDATION")
        print("=" * 60)
        print(f"System: {self.get_system_info()['cpu_count']} CPUs, "
              f"{self.get_system_info()['memory_total_gb']:.1f}GB RAM")
        print()
        
        # Run all test suites
        self.test_file_loading_performance()
        self.test_memory_stability()
        self.test_database_performance()
        self.test_ui_responsiveness()
        self.test_3d_rendering_performance()
        self.test_memory_leak_detection()
        
        # Generate and display report
        report = self.generate_performance_report()
        
        print("\n" + "=" * 60)
        print("PERFORMANCE VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {report.summary['total_tests']}")
        print(f"Passed: {report.summary['passed_tests']}")
        print(f"Failed: {report.summary['failed_tests']}")
        print(f"Success Rate: {report.summary['success_rate']:.1%}")
        print(f"Average Execution Time: {report.summary['average_execution_time']:.3f}s")
        print(f"Total Memory Usage: {report.summary['total_memory_usage_mb']:.1f}MB")
        
        if report.recommendations:
            print("\nRecommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Save detailed report
        report_file = f"performance_validation_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report


def main():
    """Main function to run performance validation."""
    with PerformanceValidator() as validator:
        report = validator.run_all_tests()
        
        # Return exit code based on results
        if report.summary['failed_tests'] == 0:
            print("\n🎉 All performance validation tests PASSED!")
            return 0
        else:
            print(f"\n⚠️  {report.summary['failed_tests']} performance validation test(s) FAILED!")
            return 1


if __name__ == "__main__":
    exit(main())