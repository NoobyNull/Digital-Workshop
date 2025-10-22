"""
Performance and memory usage tests for the database manager refactoring.

This module tests that the refactored code maintains performance standards
and doesn't introduce memory leaks according to the quality requirements.
"""

import gc
import os
import psutil
import sqlite3
import tempfile
import time
import tracemalloc
import unittest
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database_manager import DatabaseManager
from core.logging_config import setup_logging


class TestPerformanceRequirements(unittest.TestCase):
    """Test cases for performance requirements."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "perf_test_3dmm.db")
        
        # Set up logging
        setup_logging(
            log_level="ERROR",
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
        
        self.db = DatabaseManager(self.test_db_path)
        
        # Test data
        self.test_models = []
        for i in range(100):
            self.test_models.append({
                "filename": f"model_{i}.stl",
                "format": "stl",
                "file_path": f"/path/model_{i}.stl",
                "file_size": 1024 * (i + 1)
            })
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.close()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_bulk_insert_performance(self):
        """Test bulk insert performance meets requirements."""
        num_models = 100
        
        # Measure insert time
        start_time = time.time()
        
        model_ids = []
        for i, model in enumerate(self.test_models):
            model_id = self.db.add_model(**model)
            model_ids.append(model_id)
            
            # Add metadata for every 10th model
            if i % 10 == 0:
                self.db.add_model_metadata(
                    model_id,
                    title=f"Model {i}",
                    description=f"Test model number {i}",
                    keywords=f"test, model, {i}",
                    category="Test"
                )
        
        insert_time = time.time() - start_time
        
        # Verify all models were inserted
        models = self.db.get_all_models()
        self.assertEqual(len(models), num_models)
        
        # Performance check (should complete in reasonable time)
        self.assertLess(insert_time, 5.0, f"Bulk insert took too long: {insert_time:.2f}s")
        
        print(f"Inserted {num_models} models in {insert_time:.2f}s "
              f"({num_models/insert_time:.2f} models/sec)")
    
    def test_search_performance_requirements(self):
        """Test search performance meets <100ms requirement."""
        # Insert test data
        num_models = 50
        model_ids = []
        
        for i in range(num_models):
            model_id = self.db.add_model(**self.test_models[i])
            model_ids.append(model_id)
            
            # Add metadata for each model
            self.db.add_model_metadata(
                model_id,
                title=f"Model {i}",
                description=f"Test model number {i} with various properties",
                keywords=f"test, model, {i}, property",
                category="Test"
            )
        
        # Measure search time for multiple queries
        search_terms = ["model", "test", "property", "various"]
        search_times = []
        
        for term in search_terms:
            start_time = time.time()
            results = self.db.search_models(term)
            search_time = time.time() - start_time
            search_times.append(search_time)
            
            # Should find results
            self.assertGreater(len(results), 0)
            
            # Performance requirement: <100ms per search
            self.assertLess(search_time * 1000, 100, 
                          f"Search for '{term}' took too long: {search_time*1000:.1f}ms")
        
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        
        print(f"Search performance: avg={avg_search_time*1000:.1f}ms, "
              f"max={max_search_time*1000:.1f}ms")
        
        # Overall average should also be fast
        self.assertLess(avg_search_time * 1000, 50, 
                       f"Average search time too long: {avg_search_time*1000:.1f}ms")
    
    def test_update_operations_performance(self):
        """Test update operations performance."""
        # Insert test data
        model_ids = []
        for i in range(50):
            model_id = self.db.add_model(**self.test_models[i])
            model_ids.append(model_id)
            self.db.add_model_metadata(model_id, title=f"Model {i}", category="Test")
        
        # Test update_model performance
        start_time = time.time()
        for i, model_id in enumerate(model_ids):
            self.db.update_model(model_id, filename=f"updated_model_{i}.stl")
        update_time = time.time() - start_time
        
        # Should be fast
        self.assertLess(update_time, 1.0, f"Model updates took too long: {update_time:.2f}s")
        
        # Test update_hover_thumbnail_path performance
        start_time = time.time()
        for i, model_id in enumerate(model_ids):
            self.db.update_hover_thumbnail_path(model_id, f"/path/hover_{i}.png")
        hover_update_time = time.time() - start_time
        
        # Should be fast
        self.assertLess(hover_update_time, 1.0, 
                       f"Hover thumbnail updates took too long: {hover_update_time:.2f}s")
        
        print(f"Update performance: models={update_time:.3f}s, "
              f"thumbnails={hover_update_time:.3f}s")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent load."""
        import threading
        
        def worker(worker_id, num_operations=20):
            """Worker function for concurrent operations."""
            results = []
            for i in range(num_operations):
                start_time = time.time()
                
                # Add model
                model_id = self.db.add_model(
                    filename=f"worker_{worker_id}_model_{i}.stl",
                    format="stl",
                    file_path=f"/path/worker_{worker_id}_model_{i}.stl",
                    file_size=1024
                )
                
                # Add metadata
                self.db.add_model_metadata(
                    model_id,
                    title=f"Worker {worker_id} Model {i}",
                    category="Test"
                )
                
                # Search
                self.db.search_models(f"worker_{worker_id}")
                
                # Update
                self.db.update_model(model_id, filename=f"updated_{worker_id}_{i}.stl")
                
                # Delete
                self.db.delete_model(model_id)
                
                operation_time = time.time() - start_time
                results.append(operation_time)
            
            return results
        
        # Create and start threads
        threads = []
        num_threads = 5
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        total_operations = num_threads * 20 * 5  # 5 operations per iteration
        
        # Should handle concurrent operations efficiently
        ops_per_second = total_operations / total_time
        self.assertGreater(ops_per_second, 50, 
                          f"Concurrent operations too slow: {ops_per_second:.1f} ops/sec")
        
        print(f"Concurrent performance: {ops_per_second:.1f} operations/second")


class TestMemoryUsage(unittest.TestCase):
    """Test cases for memory usage and leak detection."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "memory_test_3dmm.db")
        
        # Set up logging
        setup_logging(
            log_level="ERROR",
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
        
        # Start memory tracing
        tracemalloc.start()
        
        # Get initial memory usage
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop memory tracing
        tracemalloc.stop()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_memory_stability_repeated_operations(self):
        """Test memory usage remains stable during repeated operations."""
        db = DatabaseManager(self.test_db_path)
        
        # Perform multiple rounds of operations
        memory_samples = []
        
        for round_num in range(10):
            # Add models
            model_ids = []
            for i in range(20):
                model_id = db.add_model(
                    filename=f"round_{round_num}_model_{i}.stl",
                    format="stl",
                    file_path=f"/path/round_{round_num}_model_{i}.stl",
                    file_size=1024
                )
                model_ids.append(model_id)
                
                # Add metadata
                db.add_model_metadata(
                    model_id,
                    title=f"Round {round_num} Model {i}",
                    category="Test"
                )
            
            # Perform searches
            for i in range(10):
                db.search_models(f"round_{round_num}")
                db.search_models("", category="Test")
            
            # Update models
            for i, model_id in enumerate(model_ids):
                db.update_model(model_id, filename=f"updated_round_{round_num}_{i}.stl")
                db.update_hover_thumbnail_path(model_id, f"/path/hover_{round_num}_{i}.png")
            
            # Delete models
            for model_id in model_ids:
                db.delete_model(model_id)
            
            # Force garbage collection
            gc.collect()
            
            # Sample memory usage
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            
            print(f"Round {round_num}: Memory usage = {current_memory:.1f} MB")
        
        db.close()
        
        # Analyze memory usage
        memory_increase = max(memory_samples) - min(memory_samples)
        
        # Memory increase should be minimal (< 10MB)
        self.assertLess(memory_increase, 10, 
                       f"Memory usage increased too much: {memory_increase:.1f} MB")
        
        print(f"Memory stability: increase = {memory_increase:.1f} MB "
              f"(min={min(memory_samples):.1f}, max={max(memory_samples):.1f})")
    
    def test_no_memory_leaks_database_connections(self):
        """Test that database connections don't leak memory."""
        # Track memory allocations
        snapshot1 = tracemalloc.take_snapshot()
        
        # Create and destroy multiple database instances
        for i in range(20):
            db = DatabaseManager(self.test_db_path)
            
            # Perform operations
            model_id = db.add_model(
                filename=f"leak_test_{i}.stl",
                format="stl",
                file_path=f"/path/leak_test_{i}.stl"
            )
            db.search_models("leak_test")
            db.delete_model(model_id)
            
            db.close()
            
            # Force garbage collection every 5 iterations
            if i % 5 == 0:
                gc.collect()
        
        # Final garbage collection
        gc.collect()
        
        # Check for memory leaks
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Filter for our code
        our_code_stats = [stat for stat in top_stats 
                         if 'database' in str(stat.traceback[0].filename)]
        
        # Get total memory increase
        total_increase = sum(stat.size_diff for stat in our_code_stats)
        total_increase_mb = total_increase / 1024 / 1024
        
        # Should not have significant memory increase
        self.assertLess(total_increase_mb, 5, 
                       f"Potential memory leak detected: {total_increase_mb:.1f} MB increase")
        
        print(f"Memory leak test: increase = {total_increase_mb:.1f} MB")
        
        if our_code_stats:
            print("Top memory allocations:")
            for stat in our_code_stats[:5]:
                print(f"  {stat}")
    
    def test_memory_usage_limits(self):
        """Test that memory usage stays within reasonable limits."""
        db = DatabaseManager(self.test_db_path)
        
        # Add a large number of models
        num_models = 200
        model_ids = []
        
        for i in range(num_models):
            model_id = db.add_model(
                filename=f"memory_test_{i}.stl",
                format="stl",
                file_path=f"/path/memory_test_{i}.stl",
                file_size=1024
            )
            model_ids.append(model_id)
            
            # Add metadata
            db.add_model_metadata(
                model_id,
                title=f"Memory Test Model {i}",
                description=f"A test model for memory testing with number {i}",
                keywords=f"memory, test, model, {i}",
                category="Memory Test"
            )
        
        # Check memory usage after adding data
        memory_after_add = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many searches
        for i in range(100):
            db.search_models(f"test")
            db.search_models("", category="Memory Test")
            db.search_models(f"model {i % 10}")
        
        # Check memory usage after searches
        memory_after_search = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many updates
        for i, model_id in enumerate(model_ids):
            db.update_model(model_id, filename=f"updated_{i}.stl")
            db.update_hover_thumbnail_path(model_id, f"/path/hover_{i}.png")
        
        # Check memory usage after updates
        memory_after_update = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Delete all models
        for model_id in model_ids:
            db.delete_model(model_id)
        
        # Force garbage collection
        gc.collect()
        
        # Final memory usage
        memory_final = self.process.memory_info().rss / 1024 / 1024  # MB
        
        db.close()
        
        # Calculate memory increases
        increase_from_start = memory_final - self.initial_memory
        peak_increase = max(memory_after_add, memory_after_search, memory_after_update) - self.initial_memory
        
        print(f"Memory usage analysis:")
        print(f"  Initial: {self.initial_memory:.1f} MB")
        print(f"  After add: {memory_after_add:.1f} MB")
        print(f"  After search: {memory_after_search:.1f} MB")
        print(f"  After update: {memory_after_update:.1f} MB")
        print(f"  Final: {memory_final:.1f} MB")
        print(f"  Net increase: {increase_from_start:.1f} MB")
        print(f"  Peak increase: {peak_increase:.1f} MB")
        
        # Memory requirements: should stay under 2GB for typical usage
        self.assertLess(memory_final, 2048, 
                       f"Memory usage too high: {memory_final:.1f} MB")
        
        # Net increase should be minimal
        self.assertLess(increase_from_start, 50, 
                       f"Memory not cleaned up properly: {increase_from_start:.1f} MB increase")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)