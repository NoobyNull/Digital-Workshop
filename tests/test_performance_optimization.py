"""
Performance optimization tests for 3D-MM application.

This module contains tests to verify that the performance optimizations
meet the specified requirements for load times, memory usage, and responsiveness.
"""

import gc
import os
import psutil
import tempfile
import time
import unittest
from pathlib import Path
from typing import List, Dict, Any

from src.core.performance_monitor import get_performance_monitor, PerformanceLevel
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.stl_parser import STLParser
from src.parsers.base_parser import LoadingState


class TestPerformanceOptimization(unittest.TestCase):
    """Test performance optimization features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with common resources."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_files = {}
        
        # Create test files of different sizes
        cls._create_test_files()
        
        # Initialize performance components
        cls.performance_monitor = get_performance_monitor()
        cls.model_cache = get_model_cache()
        
        # Start performance monitoring
        cls.performance_monitor.start_monitoring()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class resources."""
        # Stop performance monitoring
        cls.performance_monitor.stop_monitoring()
        
        # Clean up cache
        cls.model_cache.cleanup()
        
        # Remove test files
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def setUp(self):
        """Set up each test."""
        # Clear cache before each test
        self.model_cache.clear()
        
        # Reset performance monitor statistics
        self.performance_monitor.stats = self.performance_monitor.Stats()
    
    @classmethod
    def _create_test_files(cls):
        """Create test STL files of different sizes."""
        from tests.sample_files.create_sample_stl import create_stl_file
        
        # Small file (< 100MB equivalent in triangles)
        small_file = os.path.join(cls.temp_dir, "small.stl")
        create_stl_file(small_file, triangle_count=1000)
        cls.test_files['small'] = small_file
        
        # Medium file (100-500MB equivalent in triangles)
        medium_file = os.path.join(cls.temp_dir, "medium.stl")
        create_stl_file(medium_file, triangle_count=50000)
        cls.test_files['medium'] = medium_file
        
        # Large file (> 500MB equivalent in triangles)
        large_file = os.path.join(cls.temp_dir, "large.stl")
        create_stl_file(large_file, triangle_count=200000)
        cls.test_files['large'] = large_file
    
    def test_performance_monitor_initialization(self):
        """Test that performance monitor initializes correctly."""
        self.assertIsNotNone(self.performance_monitor)
        self.assertIsInstance(self.performance_monitor.get_performance_profile().performance_level, PerformanceLevel)
        self.assertGreater(self.performance_monitor.get_performance_profile().max_memory_mb, 0)
        self.assertGreater(self.performance_monitor.get_performance_profile().recommended_cache_size_mb, 0)
    
    def test_model_cache_initialization(self):
        """Test that model cache initializes correctly."""
        self.assertIsNotNone(self.model_cache)
        stats = self.model_cache.get_stats()
        self.assertEqual(stats.total_entries, 0)
        self.assertEqual(stats.hit_count, 0)
        self.assertEqual(stats.miss_count, 0)
    
    def test_lazy_loading_metadata_only(self):
        """Test that lazy loading can load metadata only."""
        parser = STLParser()
        file_path = self.test_files['large']
        
        # Load metadata only
        start_time = time.time()
        metadata_model = parser.parse_metadata_only(file_path)
        load_time = time.time() - start_time
        
        # Verify metadata is loaded
        self.assertIsNotNone(metadata_model)
        self.assertEqual(metadata_model.loading_state, LoadingState.METADATA_ONLY)
        self.assertEqual(len(metadata_model.triangles), 0)  # No geometry
        self.assertGreater(metadata_model.stats.triangle_count, 0)  # But stats are available
        
        # Verify load time is fast (should be < 1 second for metadata)
        self.assertLess(load_time, 1.0, "Metadata loading should be fast")
    
    def test_progressive_loading_caching(self):
        """Test that progressive loading works with caching."""
        parser = STLParser()
        file_path = self.test_files['medium']
        
        # First load - should parse file
        start_time = time.time()
        model1 = parser.parse_file(file_path, lazy_loading=True)
        first_load_time = time.time() - start_time
        
        # Verify model is loaded
        self.assertIsNotNone(model1)
        self.assertGreater(len(model1.triangles), 0)
        
        # Second load - should use cache
        start_time = time.time()
        model2 = parser.parse_file(file_path, lazy_loading=True)
        second_load_time = time.time() - start_time
        
        # Verify cache was used (second load should be much faster)
        self.assertLess(second_load_time, first_load_time / 2, "Cached load should be faster")
        
        # Verify models are equivalent
        self.assertEqual(model1.stats.triangle_count, model2.stats.triangle_count)
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during repeated operations."""
        parser = STLParser()
        file_path = self.test_files['medium']
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Perform multiple load operations
        memory_readings = [initial_memory]
        for i in range(10):
            model = parser.parse_file(file_path, lazy_loading=True)
            memory_readings.append(process.memory_info().rss / (1024 * 1024))
            
            # Clean up reference
            del model
            gc.collect()
        
        # Check memory stability
        max_memory = max(memory_readings)
        min_memory = min(memory_readings)
        memory_growth = max_memory - min_memory
        
        # Memory growth should be minimal (< 50MB)
        self.assertLess(memory_growth, 50.0, "Memory usage should be stable during repeated operations")
    
    def test_load_time_requirements(self):
        """Test that load times meet the specified requirements."""
        parser = STLParser()
        
        # Test small file (< 100MB equivalent)
        file_path = self.test_files['small']
        start_time = time.time()
        model = parser.parse_file(file_path, lazy_loading=True)
        load_time = time.time() - start_time
        
        # Small files should load in < 5 seconds
        self.assertLess(load_time, 5.0, "Small files should load in < 5 seconds")
        
        # Test medium file (100-500MB equivalent)
        file_path = self.test_files['medium']
        start_time = time.time()
        model = parser.parse_file(file_path, lazy_loading=True)
        load_time = time.time() - start_time
        
        # Medium files should load in < 15 seconds
        self.assertLess(load_time, 15.0, "Medium files should load in < 15 seconds")
    
    def test_cache_hit_ratio_improvement(self):
        """Test that cache improves performance with good hit ratio."""
        parser = STLParser()
        file_paths = [self.test_files['small'], self.test_files['medium']]
        
        # Load files multiple times
        for _ in range(5):
            for file_path in file_paths:
                parser.parse_file(file_path, lazy_loading=True)
        
        # Check cache hit ratio
        stats = self.model_cache.get_stats()
        hit_ratio = self.model_cache.get_hit_ratio()
        
        # Hit ratio should be good (> 50%)
        self.assertGreater(hit_ratio, 0.5, "Cache hit ratio should be > 50%")
    
    def test_adaptive_performance_settings(self):
        """Test that performance settings adapt to system capabilities."""
        profile = self.performance_monitor.get_performance_profile()
        
        # Verify adaptive settings based on performance level
        if profile.performance_level == PerformanceLevel.MINIMAL:
            self.assertLessEqual(profile.max_triangles_for_full_quality, 50000)
            self.assertTrue(profile.adaptive_quality_enabled)
        elif profile.performance_level == PerformanceLevel.ULTRA:
            self.assertGreaterEqual(profile.max_triangles_for_full_quality, 500000)
    
    def test_performance_monitoring_accuracy(self):
        """Test that performance monitoring accurately tracks operations."""
        parser = STLParser()
        file_path = self.test_files['small']
        
        # Parse file
        model = parser.parse_file(file_path, lazy_loading=True)
        
        # Check that operation was tracked
        metrics = self.performance_monitor.get_operation_metrics("parse_STLParser")
        self.assertGreater(len(metrics), 0)
        
        # Verify metrics are reasonable
        latest_metric = metrics[0]
        self.assertGreater(latest_metric.duration_ms, 0)
        self.assertTrue(latest_metric.success)
    
    def test_memory_leak_detection(self):
        """Test that memory leak detection works."""
        parser = STLParser()
        file_path = self.test_files['small']
        
        # Perform operation multiple times
        for _ in range(10):
            model = parser.parse_file(file_path, lazy_loading=True)
            del model
            gc.collect()
        
        # Check for memory leaks
        has_leak = self.performance_monitor.detect_memory_leak("parse_STLParser")
        self.assertFalse(has_leak, "Memory leak detected in parser operations")
    
    def test_cache_memory_management(self):
        """Test that cache manages memory correctly."""
        # Fill cache with models
        parser = STLParser()
        for file_path in self.test_files.values():
            model = parser.parse_file(file_path, lazy_loading=True)
            self.model_cache.put(file_path, CacheLevel.GEOMETRY_FULL, model)
        
        # Check memory usage
        memory_usage_mb = self.model_cache.get_memory_usage_mb()
        profile = self.performance_monitor.get_performance_profile()
        
        # Memory usage should be within recommended limits
        self.assertLessEqual(
            memory_usage_mb, 
            profile.recommended_cache_size_mb * 1.2,  # Allow 20% overhead
            "Cache memory usage should be within recommended limits"
        )
    
    def test_performance_report_generation(self):
        """Test that performance reports can be generated."""
        # Perform some operations
        parser = STLParser()
        for file_path in self.test_files.values():
            parser.parse_file(file_path, lazy_loading=True)
        
        # Generate report
        report_path = os.path.join(self.temp_dir, "performance_report.json")
        self.performance_monitor.export_performance_report(report_path)
        
        # Verify report was created
        self.assertTrue(os.path.exists(report_path))
        
        # Verify report content
        import json
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn('performance_profile', report)
        self.assertIn('current_memory', report)
        self.assertIn('operation_summary', report)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance optimization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.temp_dir = tempfile.mkdtemp()
        cls._create_test_files()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class."""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    @classmethod
    def _create_test_files(cls):
        """Create test files."""
        from tests.sample_files.create_sample_stl import create_stl_file
        
        # Create test files
        small_file = os.path.join(cls.temp_dir, "integration_test.stl")
        create_stl_file(small_file, triangle_count=10000)
        cls.test_file = small_file
    
    def test_end_to_end_performance(self):
        """Test end-to-end performance with all optimizations."""
        # Initialize components
        performance_monitor = get_performance_monitor()
        model_cache = get_model_cache()
        parser = STLParser()
        
        # Start monitoring
        performance_monitor.start_monitoring()
        
        try:
            # Load model with lazy loading
            start_time = time.time()
            model = parser.parse_file(self.test_file, lazy_loading=True)
            load_time = time.time() - start_time
            
            # Verify model loaded
            self.assertIsNotNone(model)
            self.assertGreater(len(model.triangles), 0)
            
            # Verify performance
            self.assertLess(load_time, 5.0, "Model should load quickly with optimizations")
            
            # Check cache effectiveness
            stats = model_cache.get_stats()
            self.assertGreaterEqual(stats.total_entries, 1)
            
            # Check memory usage
            memory_stats = performance_monitor.get_current_memory_stats()
            self.assertLess(memory_stats.percent_used, 90.0, "Memory usage should be reasonable")
            
        finally:
            # Clean up
            performance_monitor.stop_monitoring()
            model_cache.cleanup()


if __name__ == '__main__':
    unittest.main()