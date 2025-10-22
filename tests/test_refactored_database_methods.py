"""
Specific tests for the four refactored database methods.

This module tests the methods that were moved from DatabaseManager facade
to specialized repositories during the refactoring:
1. update_hover_thumbnail_path() -> ModelRepository
2. update_model() -> ModelRepository  
3. search_models() -> SearchRepository
4. update_category() -> MetadataRepository
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

from core.database_manager import DatabaseManager
from core.logging_config import setup_logging


class TestRefactoredMethods(unittest.TestCase):
    """Test cases for the four refactored database methods."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "refactored_test_3dmm.db")
        
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
    
    # ===== Test update_hover_thumbnail_path() =====
    
    def test_update_hover_thumbnail_path_success(self):
        """Test successful hover thumbnail path update."""
        # Add a model first
        model_id = self.db.add_model(**self.test_model)
        
        # Update hover thumbnail path
        hover_path = "/path/to/hover_thumbnail.png"
        success = self.db.update_hover_thumbnail_path(model_id, hover_path)
        
        # Verify success
        self.assertTrue(success)
        
        # Verify the hover_thumbnail column was added and value set
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT hover_thumbnail FROM models WHERE id = ?", (model_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], hover_path)
    
    def test_update_hover_thumbnail_path_invalid_model_id(self):
        """Test hover thumbnail update with invalid model ID."""
        hover_path = "/path/to/hover_thumbnail.png"
        success = self.db.update_hover_thumbnail_path(-1, hover_path)
        self.assertFalse(success)
        
        success = self.db.update_hover_thumbnail_path(999999, hover_path)
        self.assertFalse(success)
    
    def test_update_hover_thumbnail_path_column_creation(self):
        """Test that hover_thumbnail column is created if it doesn't exist."""
        # Add a model first
        model_id = self.db.add_model(**self.test_model)
        
        # Verify column doesn't exist initially
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(models)")
        columns = [column[1] for column in cursor.fetchall()]
        conn.close()
        
        # Update hover thumbnail path (should create column)
        hover_path = "/path/to/hover_thumbnail.png"
        success = self.db.update_hover_thumbnail_path(model_id, hover_path)
        
        # Verify success and column exists
        self.assertTrue(success)
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(models)")
        columns = [column[1] for column in cursor.fetchall()]
        cursor.execute("SELECT hover_thumbnail FROM models WHERE id = ?", (model_id,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIn("hover_thumbnail", columns)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], hover_path)
    
    # ===== Test update_model() =====
    
    def test_update_model_success(self):
        """Test successful model update."""
        # Add a model first
        model_id = self.db.add_model(**self.test_model)
        
        # Update model
        updates = {
            "filename": "updated_model.stl",
            "file_size": 2048,
            "file_path": "/new/path/to/updated_model.stl"
        }
        success = self.db.update_model(model_id, **updates)
        
        # Verify success
        self.assertTrue(success)
        
        # Verify updates
        model = self.db.get_model(model_id)
        self.assertEqual(model['filename'], "updated_model.stl")
        self.assertEqual(model['file_size'], 2048)
        self.assertEqual(model['file_path'], "/new/path/to/updated_model.stl")
    
    def test_update_model_invalid_model_id(self):
        """Test model update with invalid model ID."""
        updates = {"filename": "updated_model.stl"}
        success = self.db.update_model(-1, **updates)
        self.assertFalse(success)
        
        success = self.db.update_model(999999, **updates)
        self.assertFalse(success)
    
    def test_update_model_no_fields(self):
        """Test model update with no fields provided."""
        model_id = self.db.add_model(**self.test_model)
        success = self.db.update_model(model_id)
        self.assertFalse(success)
    
    def test_update_model_invalid_fields(self):
        """Test model update with invalid fields."""
        model_id = self.db.add_model(**self.test_model)
        
        # Test with invalid field names
        updates = {"invalid_field": "value", "another_invalid": 123}
        success = self.db.update_model(model_id, **updates)
        self.assertFalse(success)
        
        # Test with mix of valid and invalid fields
        updates = {"filename": "valid.stl", "invalid_field": "value"}
        success = self.db.update_model(model_id, **updates)
        self.assertTrue(success)  # Should succeed with valid field
        
        # Verify only valid field was updated
        model = self.db.get_model(model_id)
        self.assertEqual(model['filename'], "valid.stl")
    
    def test_update_model_format_field(self):
        """Test updating the format field specifically."""
        model_id = self.db.add_model(**self.test_model)
        
        # Update format
        success = self.db.update_model(model_id, format="obj")
        self.assertTrue(success)
        
        # Verify update
        model = self.db.get_model(model_id)
        self.assertEqual(model['format'], "obj")
    
    # ===== Test search_models() =====
    
    def test_search_models_basic(self):
        """Test basic search functionality."""
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
    
    def test_search_models_with_filters(self):
        """Test search with category and format filters."""
        # Add test models with metadata
        model1_id = self.db.add_model(filename="car.stl", format="stl", file_path="/path/car.stl")
        self.db.add_model_metadata(model1_id, title="Sports Car", 
                                  keywords="car, sports, red, vehicle",
                                  category="Vehicles")
        
        model2_id = self.db.add_model(filename="house.obj", format="obj", file_path="/path/house.obj")
        self.db.add_model_metadata(model2_id, title="Modern House", 
                                  keywords="house, modern, building",
                                  category="Buildings")
        
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
    
    def test_search_models_backward_compatibility(self):
        """Test search_models maintains backward compatibility with format parameter."""
        # Add test model
        model_id = self.db.add_model(filename="test.stl", format="stl", file_path="/path/test.stl")
        self.db.add_model_metadata(model_id, title="Test Model", category="Test")
        
        # Test with format parameter (old style)
        results = self.db.search_models("", format="stl")
        self.assertEqual(len(results), 1)
        
        # Test with file_format parameter (new style)
        results = self.db.search_models("", file_format="stl")
        self.assertEqual(len(results), 1)
        
        # Test that file_format takes precedence
        results = self.db.search_models("", format="obj", file_format="stl")
        self.assertEqual(len(results), 1)
    
    def test_search_models_empty_query(self):
        """Test search with empty query returns all models."""
        # Add test models
        model1_id = self.db.add_model(filename="model1.stl", format="stl", file_path="/path/model1.stl")
        model2_id = self.db.add_model(filename="model2.obj", format="obj", file_path="/path/model2.obj")
        
        # Search with empty query
        results = self.db.search_models("")
        self.assertEqual(len(results), 2)
        
        # Search with None query
        results = self.db.search_models(None)
        self.assertEqual(len(results), 2)
    
    # ===== Test update_category() =====
    
    def test_update_category_success(self):
        """Test successful category update."""
        # Add a category first
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Update category
        updates = {
            "name": "Updated Category",
            "color": "#00FF00",
            "description": "Updated description",
            "sort_order": 100
        }
        success = self.db.update_category(category_id, **updates)
        
        # Verify success
        self.assertTrue(success)
        
        # Verify updates
        categories = self.db.get_categories()
        updated_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertIsNotNone(updated_category)
        self.assertEqual(updated_category['name'], "Updated Category")
        self.assertEqual(updated_category['color'], "#00FF00")
        self.assertEqual(updated_category['description'], "Updated description")
        self.assertEqual(updated_category['sort_order'], 100)
    
    def test_update_category_invalid_category_id(self):
        """Test category update with invalid category ID."""
        updates = {"name": "Updated Category"}
        success = self.db.update_category(-1, **updates)
        self.assertFalse(success)
        
        success = self.db.update_category(999999, **updates)
        self.assertFalse(success)
    
    def test_update_category_no_fields(self):
        """Test category update with no fields provided."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        success = self.db.update_category(category_id)
        self.assertFalse(success)
    
    def test_update_category_invalid_fields(self):
        """Test category update with invalid fields."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Test with invalid field names
        updates = {"invalid_field": "value", "another_invalid": 123}
        success = self.db.update_category(category_id, **updates)
        self.assertFalse(success)
        
        # Test with mix of valid and invalid fields
        updates = {"name": "valid", "invalid_field": "value"}
        success = self.db.update_category(category_id, **updates)
        self.assertTrue(success)  # Should succeed with valid field
        
        # Verify only valid field was updated
        categories = self.db.get_categories()
        updated_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertEqual(updated_category['name'], "valid")
    
    def test_update_category_partial_fields(self):
        """Test category update with only some fields."""
        category_id = self.db.add_category("Test Category", "#FF0000", 99)
        
        # Update only name
        success = self.db.update_category(category_id, name="New Name")
        self.assertTrue(success)
        
        # Verify only name was updated
        categories = self.db.get_categories()
        updated_category = next((c for c in categories if c['id'] == category_id), None)
        self.assertEqual(updated_category['name'], "New Name")
        self.assertEqual(updated_category['color'], "#FF0000")  # Unchanged
        self.assertEqual(updated_category['sort_order'], 99)    # Unchanged


class TestRefactoredMethodsPerformance(unittest.TestCase):
    """Performance tests for the refactored methods."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "perf_refactored_test_3dmm.db")
        
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
    
    def test_search_models_performance(self):
        """Test search performance with many models."""
        # Insert test data
        num_models = 100
        model_ids = []
        
        for i in range(num_models):
            model_id = self.db.add_model(
                filename=f"model_{i}.stl",
                format="stl",
                file_path=f"/path/model_{i}.stl",
                file_size=1024 * (i + 1)
            )
            model_ids.append(model_id)
            
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
        
        print(f"Average search time for {num_models} models: {avg_search_time:.3f}s")
    
    def test_update_operations_performance(self):
        """Test performance of update operations."""
        # Insert test data
        num_models = 50
        model_ids = []
        
        for i in range(num_models):
            model_id = self.db.add_model(
                filename=f"model_{i}.stl",
                format="stl",
                file_path=f"/path/model_{i}.stl",
                file_size=1024
            )
            model_ids.append(model_id)
        
        # Test update_model performance
        start_time = time.time()
        for i, model_id in enumerate(model_ids):
            self.db.update_model(model_id, filename=f"updated_model_{i}.stl")
        update_time = time.time() - start_time
        
        # Performance check
        self.assertLess(update_time, 1.0, f"Model updates took too long: {update_time:.2f}s")
        
        # Test update_hover_thumbnail_path performance
        start_time = time.time()
        for i, model_id in enumerate(model_ids):
            self.db.update_hover_thumbnail_path(model_id, f"/path/hover_{i}.png")
        hover_update_time = time.time() - start_time
        
        # Performance check
        self.assertLess(hover_update_time, 1.0, f"Hover thumbnail updates took too long: {hover_update_time:.2f}s")
        
        print(f"Updated {num_models} models in {update_time:.3f}s ({num_models/update_time:.2f} models/sec)")
        print(f"Updated {num_models} hover thumbnails in {hover_update_time:.3f}s ({num_models/hover_update_time:.2f} models/sec)")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)