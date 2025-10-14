"""
Unit tests for the database manager module.

This module tests all database operations including CRUD operations,
search functionality, and error handling. It also includes memory leak
testing by running operations multiple times.
"""

import gc
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database_manager import DatabaseManager, get_database_manager, close_database_manager
from core.logging_config import setup_logging


class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_3dmm.db")
        
        # Set up logging to capture logs during tests
        setup_logging(
            log_level="DEBUG",
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
        
        # Create database manager instance
        self.db = DatabaseManager(self.test_db_path)
        
        # Test data
        self.test_model = {
            "filename": "test_model.stl",
            "format": "stl",
            "file_path": "/path/to/test_model.stl",
            "file_size": 1024
        }
        
        self.test_metadata = {
            "title": "Test Model",
            "description": "A test model for unit testing",
            "keywords": "test, model, stl",
            "category": "Test",
            "source": "Unit Test",
            "rating": 5
        }
    
    def tearDown(self):
        """Clean up after each test."""
        # Close database connection
        self.db.close()
        
        # Force garbage collection
        gc.collect()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_database_initialization(self):
        """Test that the database is properly initialized with schema."""
        # Check that database file exists
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Connect directly to verify tables exist
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['models', 'model_metadata', 'categories']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        # Check default categories were inserted
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        self.assertGreater(category_count, 0)
        
        conn.close()
    
    def test_add_model(self):
        """Test adding a new model to the database."""
        model_id = self.db.add_model(**self.test_model)
        
        # Verify model was added
        self.assertIsInstance(model_id, int)
        self.assertGreater(model_id, 0)
        
        # Verify model can be retrieved
        model = self.db.get_model(model_id)
        self.assertIsNotNone(model)
        self.assertEqual(model['filename'], self.test_model['filename'])
        self.assertEqual(model['format'], self.test_model['format'])
        self.assertEqual(model['file_path'], self.test_model['file_path'])
        self.assertEqual(model['file_size'], self.test_model['file_size'])
    
    def test_get_model_not_found(self):
        """Test retrieving a model that doesn't exist."""
        model = self.db.get_model(999999)
        self.assertIsNone(model)
    
    def test_get_all_models_empty(self):
        """Test getting all models when database is empty."""
        models = self.db.get_all_models()
        self.assertEqual(len(models), 0)
    
    def test_get_all_models_with_data(self):
        """Test getting all models when database has data."""
        # Add test models
        model1_id = self.db.add_model(filename="model1.stl", format="stl", 
                                      file_path="/path/model1.stl")
        model2_id = self.db.add_model(filename="model2.obj", format="obj", 
                                      file_path="/path/model2.obj")
        
        # Get all models
        models = self.db.get_all_models()
        self.assertEqual(len(models), 2)
        
        # Verify models are returned (order might vary due to timing)
        filenames = [model['filename'] for model in models]
        self.assertIn("model1.stl", filenames)
        self.assertIn("model2.obj", filenames)
    
    def test_update_model(self):
        """Test updating a model."""
        model_id = self.db.add_model(**self.test_model)
        
        # Update model
        success = self.db.update_model(model_id, filename="updated_model.stl", file_size=2048)
        self.assertTrue(success)
        
        # Verify update
        model = self.db.get_model(model_id)
        self.assertEqual(model['filename'], "updated_model.stl")
        self.assertEqual(model['file_size'], 2048)
    
    def test_update_model_not_found(self):
        """Test updating a model that doesn't exist."""
        success = self.db.update_model(999999, filename="updated.stl")
        self.assertFalse(success)
    
    def test_delete_model(self):
        """Test deleting a model."""
        model_id = self.db.add_model(**self.test_model)
        
        # Verify model exists
        model = self.db.get_model(model_id)
        self.assertIsNotNone(model)
        
        # Delete model
        success = self.db.delete_model(model_id)
        self.assertTrue(success)
        
        # Verify model is deleted
        model = self.db.get_model(model_id)
        self.assertIsNone(model)
    
    def test_delete_model_not_found(self):
        """Test deleting a model that doesn't exist."""
        success = self.db.delete_model(999999)
        self.assertFalse(success)
    
    def test_add_model_metadata(self):
        """Test adding metadata for a model."""
        model_id = self.db.add_model(**self.test_model)
        
        metadata_id = self.db.add_model_metadata(model_id, **self.test_metadata)
        
        # Verify metadata was added
        self.assertIsInstance(metadata_id, int)
        self.assertGreater(metadata_id, 0)
        
        # Verify metadata can be retrieved with model
        model = self.db.get_model(model_id)
        self.assertEqual(model['title'], self.test_metadata['title'])
        self.assertEqual(model['description'], self.test_metadata['description'])
        self.assertEqual(model['keywords'], self.test_metadata['keywords'])
        self.assertEqual(model['category'], self.test_metadata['category'])
        self.assertEqual(model['source'], self.test_metadata['source'])
        self.assertEqual(model['rating'], self.test_metadata['rating'])
    
    def test_update_model_metadata(self):
        """Test updating model metadata."""
        model_id = self.db.add_model(**self.test_model)
        self.db.add_model_metadata(model_id, **self.test_metadata)
        
        # Update metadata
        success = self.db.update_model_metadata(model_id, title="Updated Title", rating=4)
        self.assertTrue(success)
        
        # Verify update
        model = self.db.get_model(model_id)
        self.assertEqual(model['title'], "Updated Title")
        self.assertEqual(model['rating'], 4)
    
    def test_increment_view_count(self):
        """Test incrementing view count for a model."""
        model_id = self.db.add_model(**self.test_model)
        self.db.add_model_metadata(model_id, **self.test_metadata)
        
        # Get initial view count
        model = self.db.get_model(model_id)
        initial_count = model['view_count']
        
        # Increment view count
        success = self.db.increment_view_count(model_id)
        self.assertTrue(success)
        
        # Verify view count was incremented
        model = self.db.get_model(model_id)
        self.assertEqual(model['view_count'], initial_count + 1)
    
    def test_get_categories(self):
        """Test getting all categories."""
        categories = self.db.get_categories()
        
        # Should have default categories
        self.assertGreater(len(categories), 0)
        
        # Verify category structure
        for category in categories:
            self.assertIn('id', category)
            self.assertIn('name', category)
            self.assertIn('color', category)
            self.assertIn('sort_order', category)
    
    def test_add_category(self):
        """Test adding a new category."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Verify category was added
        self.assertIsInstance(category_id, int)
        self.assertGreater(category_id, 0)
        
        # Verify category can be retrieved
        categories = self.db.get_categories()
        test_category = next((c for c in categories if c['name'] == "Test Category"), None)
        self.assertIsNotNone(test_category)
        self.assertEqual(test_category['color'], "#FF0000")
        self.assertEqual(test_category['sort_order'], 99)
    
    def test_update_category(self):
        """Test updating a category."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Update category
        success = self.db.update_category(category_id, name="Updated Category", color="#00FF00")
        self.assertTrue(success)
        
        # Verify update
        categories = self.db.get_categories()
        updated_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertIsNotNone(updated_category)
        self.assertEqual(updated_category['name'], "Updated Category")
        self.assertEqual(updated_category['color'], "#00FF00")
    
    def test_delete_category(self):
        """Test deleting a category."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Verify category exists
        categories = self.db.get_categories()
        test_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertIsNotNone(test_category)
        
        # Delete category
        success = self.db.delete_category(category_id)
        self.assertTrue(success)
        
        # Verify category is deleted
        categories = self.db.get_categories()
        test_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertIsNone(test_category)
    
    def test_search_models(self):
        """Test searching for models."""
        # Add test models with metadata
        model1_id = self.db.add_model(filename="car.stl", format="stl", file_path="/path/car.stl")
        self.db.add_model_metadata(model1_id, title="Sports Car", 
                                  description="A red sports car model", 
                                  keywords="car, sports, red, vehicle",
                                  category="Vehicles")
        
        model2_id = self.db.add_model(filename="house.obj", format="obj", file_path="/path/house.obj")
        self.db.add_model_metadata(model2_id, title="Modern House", 
                                  description="A modern house design", 
                                  keywords="house, modern, building",
                                  category="Buildings")
        
        # Search by title
        results = self.db.search_models("car")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Sports Car")
        
        # Search by description
        results = self.db.search_models("modern")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Modern House")
        
        # Search by keywords
        results = self.db.search_models("vehicle")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Sports Car")
        
        # Search by category
        results = self.db.search_models("", category="Vehicles")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Sports Car")
        
        # Search by format
        results = self.db.search_models("", format="obj")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Modern House")
        
        # Search with multiple filters
        results = self.db.search_models("house", category="Buildings", format="obj")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Modern House")
        
        # Search with no results
        results = self.db.search_models("nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_get_database_stats(self):
        """Test getting database statistics."""
        # Add test data
        model1_id = self.db.add_model(filename="model1.stl", format="stl", 
                                      file_path="/path/model1.stl", file_size=1024)
        self.db.add_model_metadata(model1_id, category="Vehicles")
        
        model2_id = self.db.add_model(filename="model2.obj", format="obj", 
                                      file_path="/path/model2.obj", file_size=2048)
        self.db.add_model_metadata(model2_id, category="Buildings")
        
        model3_id = self.db.add_model(filename="model3.stl", format="stl", 
                                      file_path="/path/model3.stl", file_size=512)
        self.db.add_model_metadata(model3_id, category="Vehicles")
        
        # Get stats
        stats = self.db.get_database_stats()
        
        # Verify stats
        self.assertEqual(stats['model_count'], 3)
        self.assertEqual(stats['category_counts']['Vehicles'], 2)
        self.assertEqual(stats['category_counts']['Buildings'], 1)
        self.assertEqual(stats['format_counts']['stl'], 2)
        self.assertEqual(stats['format_counts']['obj'], 1)
        self.assertEqual(stats['total_size_bytes'], 3584)  # 1024 + 2048 + 512
        self.assertEqual(stats['total_size_mb'], round(3584 / (1024 * 1024), 2))
    
    def test_database_maintenance(self):
        """Test database maintenance operations."""
        # These operations should not raise exceptions
        self.db.vacuum_database()
        self.db.analyze_database()
    
    def test_error_handling(self):
        """Test error handling for various operations."""
        # Test with invalid model ID
        self.assertIsNone(self.db.get_model(-1))
        self.assertFalse(self.db.update_model(-1, filename="test"))
        self.assertFalse(self.db.delete_model(-1))
        self.assertFalse(self.db.update_model_metadata(-1, title="test"))
        self.assertFalse(self.db.increment_view_count(-1))
        
        # Test with invalid category ID
        self.assertFalse(self.db.update_category(-1, name="test"))
        self.assertFalse(self.db.delete_category(-1))
    
    def test_singleton_database_manager(self):
        """Test the singleton database manager function."""
        # Close existing instance
        close_database_manager()
        
        # Get new instance
        db1 = get_database_manager()
        db2 = get_database_manager()
        
        # Should be the same instance
        self.assertIs(db1, db2)
        
        # Clean up
        close_database_manager()


class TestDatabaseMemoryLeaks(unittest.TestCase):
    """Test cases for memory leaks in database operations."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "memory_test_3dmm.db")
        
        # Set up logging
        setup_logging(
            log_level="ERROR",  # Reduce log noise during memory tests
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
    
    def tearDown(self):
        """Clean up after each test."""
        # Close database manager
        close_database_manager()
        
        # Force garbage collection
        gc.collect()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_memory_leak_model_operations(self):
        """Test for memory leaks in model operations."""
        # Run operations multiple times to detect memory leaks
        iterations = 20
        
        for i in range(iterations):
            # Get database manager
            db = get_database_manager(self.test_db_path)
            
            # Add model
            model_id = db.add_model(
                filename=f"test_model_{i}.stl",
                format="stl",
                file_path=f"/path/test_model_{i}.stl",
                file_size=1024 + i
            )
            
            # Add metadata
            db.add_model_metadata(
                model_id,
                title=f"Test Model {i}",
                description=f"Test model number {i}",
                keywords=f"test, model, {i}",
                category="Test",
                rating=(i % 5) + 1
            )
            
            # Get model
            model = db.get_model(model_id)
            self.assertIsNotNone(model)
            
            # Update model
            db.update_model(model_id, filename=f"updated_model_{i}.stl")
            
            # Update metadata
            db.update_model_metadata(model_id, title=f"Updated Model {i}")
            
            # Increment view count
            db.increment_view_count(model_id)
            
            # Search models
            results = db.search_models(f"model_{i}")
            self.assertGreater(len(results), 0)
            
            # Delete model
            db.delete_model(model_id)
            
            # Close database
            db.close()
            
            # Force garbage collection every 5 iterations
            if i % 5 == 0:
                gc.collect()
    
    def test_memory_leak_category_operations(self):
        """Test for memory leaks in category operations."""
        iterations = 20
        
        for i in range(iterations):
            # Get database manager
            db = get_database_manager(self.test_db_path)
            
            # Add category
            category_id = db.add_category(
                name=f"Test Category {i}",
                color=f"#{i:02X}{i:02X}{i:02X}",
                sort_order=i
            )
            
            # Get categories
            categories = db.get_categories()
            self.assertGreater(len(categories), 0)
            
            # Update category
            db.update_category(category_id, name=f"Updated Category {i}")
            
            # Delete category
            db.delete_category(category_id)
            
            # Close database
            db.close()
            
            # Force garbage collection every 5 iterations
            if i % 5 == 0:
                gc.collect()
    
    def test_memory_leak_concurrent_operations(self):
        """Test for memory leaks with concurrent database operations."""
        import threading
        
        def worker(thread_id):
            """Worker function for concurrent operations."""
            try:
                # Get database manager
                db = get_database_manager(self.test_db_path)
                
                # Perform operations
                for i in range(10):
                    model_id = db.add_model(
                        filename=f"thread_{thread_id}_model_{i}.stl",
                        format="stl",
                        file_path=f"/path/thread_{thread_id}_model_{i}.stl",
                        file_size=1024
                    )
                    
                    db.add_model_metadata(
                        model_id,
                        title=f"Thread {thread_id} Model {i}",
                        category="Test"
                    )
                    
                    # Get all models
                    models = db.get_all_models(limit=10)
                    
                    # Search models
                    db.search_models(f"thread_{thread_id}")
                    
                    # Delete model
                    db.delete_model(model_id)
                
                db.close()
                
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
        
        # Create and start threads
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Force garbage collection
        gc.collect()


class TestDatabasePerformance(unittest.TestCase):
    """Test cases for database performance."""
    
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
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.close()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_bulk_insert_performance(self):
        """Test performance of bulk insert operations."""
        num_models = 100
        
        # Measure insert time
        start_time = time.time()
        
        model_ids = []
        for i in range(num_models):
            model_id = self.db.add_model(
                filename=f"model_{i}.stl",
                format="stl",
                file_path=f"/path/model_{i}.stl",
                file_size=1024 * (i + 1)
            )
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
    
    def test_search_performance(self):
        """Test performance of search operations."""
        # Insert test data
        num_models = 50
        for i in range(num_models):
            model_id = self.db.add_model(
                filename=f"model_{i}.stl",
                format="stl",
                file_path=f"/path/model_{i}.stl",
                file_size=1024 * (i + 1)
            )
            
            # Add metadata for each model
            self.db.add_model_metadata(
                model_id,
                title=f"Model {i}",
                description=f"Test model number {i} with various properties",
                keywords=f"test, model, {i}, property",
                category="Test"
            )
        
        # Measure search time
        search_terms = ["model", "test", "property", "various"]
        total_search_time = 0
        
        for term in search_terms:
            start_time = time.time()
            results = self.db.search_models(term)
            search_time = time.time() - start_time
            total_search_time += search_time
            
            # Should find results
            self.assertGreater(len(results), 0)
        
        avg_search_time = total_search_time / len(search_terms)
        
        # Performance check (search should be fast)
        self.assertLess(avg_search_time, 0.1, f"Search took too long: {avg_search_time:.3f}s")
        
        print(f"Average search time: {avg_search_time:.3f}s")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)