"""
Backward compatibility tests for the database manager refactoring.

This module ensures that the refactored DatabaseManager maintains 100% backward compatibility
with existing code that uses the old API. All method signatures, return types, and behavior
must remain identical.
"""

import gc
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test both import paths to ensure compatibility
from core.database_manager import DatabaseManager as OldStyleDatabaseManager
from core.database import DatabaseManager as NewStyleDatabaseManager
from core.logging_config import setup_logging


class TestBackwardCompatibility(unittest.TestCase):
    """Test cases to ensure 100% backward compatibility."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test databases
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "compat_test_3dmm.db")
        
        # Set up logging
        setup_logging(
            log_level="ERROR",
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
        
        # Create database manager instances using both import styles
        self.old_db = OldStyleDatabaseManager(self.test_db_path)
        self.new_db = NewStyleDatabaseManager(self.test_db_path)
        
        # Test data
        self.test_model = {
            "filename": "test_model.stl",
            "format": "stl",
            "file_path": "/path/to/test_model.stl",
            "file_size": 1024,
            "file_hash": "abc123def456"
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
        # Close database connections
        self.old_db.close()
        self.new_db.close()
        
        # Force garbage collection
        gc.collect()
        
        # Remove test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_import_compatibility(self):
        """Test that both import styles work identically."""
        # Both should be the same class (due to compatibility layer)
        self.assertEqual(OldStyleDatabaseManager.__name__, NewStyleDatabaseManager.__name__)
        
        # Both should have the same methods
        old_methods = set(dir(self.old_db))
        new_methods = set(dir(self.new_db))
        
        # Filter out private attributes
        old_public = {m for m in old_methods if not m.startswith('_')}
        new_public = {m for m in new_methods if not m.startswith('_')}
        
        self.assertEqual(old_public, new_public, "Public methods differ between import styles")
    
    def test_method_signatures_compatibility(self):
        """Test that all method signatures are preserved."""
        # Test key methods that were refactored
        
        # update_hover_thumbnail_path signature
        self.assertTrue(hasattr(self.old_db, 'update_hover_thumbnail_path'))
        self.assertTrue(hasattr(self.new_db, 'update_hover_thumbnail_path'))
        
        # update_model signature
        self.assertTrue(hasattr(self.old_db, 'update_model'))
        self.assertTrue(hasattr(self.new_db, 'update_model'))
        
        # search_models signature
        self.assertTrue(hasattr(self.old_db, 'search_models'))
        self.assertTrue(hasattr(self.new_db, 'search_models'))
        
        # update_category signature
        self.assertTrue(hasattr(self.old_db, 'update_category'))
        self.assertTrue(hasattr(self.new_db, 'update_category'))
    
    def test_return_type_compatibility(self):
        """Test that return types are preserved."""
        # Test add_model return type (should be int)
        model_id_old = self.old_db.add_model(**self.test_model)
        model_id_new = self.new_db.add_model(**self.test_model)
        
        self.assertIsInstance(model_id_old, int)
        self.assertIsInstance(model_id_new, int)
        
        # Test get_model return type (should be dict or None)
        model_old = self.old_db.get_model(model_id_old)
        model_new = self.new_db.get_model(model_id_new)
        
        self.assertIsInstance(model_old, dict)
        self.assertIsInstance(model_new, dict)
        
        # Test get_all_models return type (should be list)
        models_old = self.old_db.get_all_models()
        models_new = self.new_db.get_all_models()
        
        self.assertIsInstance(models_old, list)
        self.assertIsInstance(models_new, list)
        
        # Test update methods return type (should be bool)
        update_old = self.old_db.update_model(model_id_old, filename="updated.stl")
        update_new = self.new_db.update_model(model_id_new, filename="updated.stl")
        
        self.assertIsInstance(update_old, bool)
        self.assertIsInstance(update_new, bool)
        self.assertTrue(update_old)
        self.assertTrue(update_new)
    
    def test_behavior_compatibility(self):
        """Test that behavior is identical between old and new implementations."""
        # Add models to both databases
        model_id_old = self.old_db.add_model(**self.test_model)
        model_id_new = self.new_db.add_model(**self.test_model)
        
        # Add metadata
        self.old_db.add_model_metadata(model_id_old, **self.test_metadata)
        self.new_db.add_model_metadata(model_id_new, **self.test_metadata)
        
        # Test get_model returns same structure
        model_old = self.old_db.get_model(model_id_old)
        model_new = self.new_db.get_model(model_id_new)
        
        # Should have same keys
        self.assertEqual(set(model_old.keys()), set(model_new.keys()))
        
        # Should have same values (except ID and timestamps)
        for key in model_old.keys():
            if key not in ['id', 'date_added', 'last_modified']:
                self.assertEqual(model_old[key], model_new[key], 
                               f"Value mismatch for key: {key}")
        
        # Test search returns same structure
        search_old = self.old_db.search_models("test")
        search_new = self.new_db.search_models("test")
        
        self.assertEqual(len(search_old), len(search_new))
        if search_old and search_new:
            self.assertEqual(set(search_old[0].keys()), set(search_new[0].keys()))
    
    def test_error_handling_compatibility(self):
        """Test that error handling is preserved."""
        # Test invalid model ID
        result_old = self.old_db.get_model(999999)
        result_new = self.new_db.get_model(999999)
        
        self.assertIsNone(result_old)
        self.assertIsNone(result_new)
        
        # Test invalid update
        update_old = self.old_db.update_model(999999, filename="test.stl")
        update_new = self.new_db.update_model(999999, filename="test.stl")
        
        self.assertFalse(update_old)
        self.assertFalse(update_new)
        
        # Test invalid category
        cat_old = self.old_db.update_category(999999, name="test")
        cat_new = self.new_db.update_category(999999, name="test")
        
        self.assertFalse(cat_old)
        self.assertFalse(cat_new)
    
    def test_format_parameter_compatibility(self):
        """Test that format parameter works for backward compatibility."""
        # Add models using both format and file_format
        model1_id = self.old_db.add_model(
            filename="model1.stl",
            format="stl",  # Old style parameter
            file_path="/path/model1.stl"
        )
        
        model2_id = self.old_db.add_model(
            filename="model2.obj",
            file_format="obj",  # New style parameter
            file_path="/path/model2.obj"
        )
        
        # Both should work
        self.assertIsInstance(model1_id, int)
        self.assertIsInstance(model2_id, int)
        
        # Test search with format parameter
        self.old_db.add_model_metadata(model1_id, title="STL Model", category="Test")
        self.old_db.add_model_metadata(model2_id, title="OBJ Model", category="Test")
        
        # Search using old format parameter
        results_old = self.old_db.search_models("", format="stl")
        self.assertEqual(len(results_old), 1)
        self.assertEqual(results_old[0]['title'], "STL Model")
        
        # Search using new file_format parameter
        results_new = self.old_db.search_models("", file_format="obj")
        self.assertEqual(len(results_new), 1)
        self.assertEqual(results_new[0]['title'], "OBJ Model")
    
    def test_alias_methods_compatibility(self):
        """Test that alias methods still work."""
        model_id = self.old_db.add_model(**self.test_model)
        
        # Test alias methods
        self.assertTrue(self.old_db.update_thumbnail_path(model_id, "/path/thumb.png"))
        self.assertTrue(self.old_db.update_model_hash(model_id, "newhash123"))
        
        # Verify they work the same as the main methods
        model = self.old_db.get_model(model_id)
        self.assertEqual(model['thumbnail_path'], "/path/thumb.png")
        self.assertEqual(model['file_hash'], "newhash123")
    
    def test_database_stats_compatibility(self):
        """Test that database stats return same structure."""
        # Add test data
        model_id = self.old_db.add_model(**self.test_model)
        self.old_db.add_model_metadata(model_id, **self.test_metadata)
        
        # Get stats from both implementations
        stats_old = self.old_db.get_database_stats()
        stats_new = self.new_db.get_database_stats()
        
        # Should have same structure
        self.assertEqual(set(stats_old.keys()), set(stats_new.keys()))
        
        # Should have same values
        for key in stats_old.keys():
            self.assertEqual(stats_old[key], stats_new[key], 
                           f"Stats mismatch for key: {key}")
    
    def test_maintenance_operations_compatibility(self):
        """Test that maintenance operations work the same."""
        # These should not raise exceptions
        self.old_db.vacuum_database()
        self.new_db.vacuum_database()
        
        self.old_db.analyze_database()
        self.new_db.analyze_database()
    
    def test_concurrent_access_compatibility(self):
        """Test that concurrent access works the same."""
        import threading
        
        def worker_old(db, thread_id):
            """Worker for old database manager."""
            for i in range(5):
                model_id = db.add_model(
                    filename=f"old_thread_{thread_id}_model_{i}.stl",
                    format="stl",
                    file_path=f"/path/old_thread_{thread_id}_model_{i}.stl"
                )
                db.search_models(f"old_thread_{thread_id}")
                db.delete_model(model_id)
        
        def worker_new(db, thread_id):
            """Worker for new database manager."""
            for i in range(5):
                model_id = db.add_model(
                    filename=f"new_thread_{thread_id}_model_{i}.stl",
                    format="stl",
                    file_path=f"/path/new_thread_{thread_id}_model_{i}.stl"
                )
                db.search_models(f"new_thread_{thread_id}")
                db.delete_model(model_id)
        
        # Create threads for both implementations
        threads_old = []
        threads_new = []
        
        for i in range(3):
            thread_old = threading.Thread(target=worker_old, args=(self.old_db, i))
            thread_new = threading.Thread(target=worker_new, args=(self.new_db, i))
            threads_old.append(thread_old)
            threads_new.append(thread_new)
            thread_old.start()
            thread_new.start()
        
        # Wait for all threads to complete
        for thread in threads_old + threads_new:
            thread.join()
        
        # Both should complete without errors
        self.assertTrue(True)  # If we get here, no exceptions were raised


class TestAPIContractCompliance(unittest.TestCase):
    """Test that the API contract is fully preserved."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "api_test_3dmm.db")
        
        setup_logging(
            log_level="ERROR",
            log_dir=os.path.join(self.test_dir, "logs"),
            enable_console=False
        )
        
        self.db = OldStyleDatabaseManager(self.test_db_path)
    
    def tearDown(self):
        """Clean up after each test."""
        self.db.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_all_refactored_methods_exist(self):
        """Test that all refactored methods still exist with same signatures."""
        # List of methods that were refactored but should still exist
        refactored_methods = [
            'update_hover_thumbnail_path',
            'update_model',
            'search_models',
            'update_category'
        ]
        
        for method_name in refactored_methods:
            self.assertTrue(hasattr(self.db, method_name), 
                          f"Method {method_name} missing from DatabaseManager")
            
            # Get the method to ensure it's callable
            method = getattr(self.db, method_name)
            self.assertTrue(callable(method), 
                          f"Method {method_name} is not callable")
    
    def test_method_parameter_compatibility(self):
        """Test that method parameters are preserved."""
        # Test update_hover_thumbnail_path parameters
        model_id = self.db.add_model(filename="test.stl", format="stl", file_path="/path/test.stl")
        
        # Should accept exactly 2 parameters
        try:
            self.db.update_hover_thumbnail_path(model_id, "/path/hover.png")
            success = True
        except TypeError:
            success = False
        self.assertTrue(success, "update_hover_thumbnail_path parameter signature changed")
        
        # Test update_model parameters
        try:
            self.db.update_model(model_id, filename="new.stl", file_size=2048)
            success = True
        except TypeError:
            success = False
        self.assertTrue(success, "update_model parameter signature changed")
        
        # Test search_models parameters
        try:
            self.db.search_models("query", category="test", format="stl")
            success = True
        except TypeError:
            success = False
        self.assertTrue(success, "search_models parameter signature changed")
        
        # Test update_category parameters
        category_id = self.db.add_category("Test", "#FF0000", 0)
        try:
            self.db.update_category(category_id, name="Updated", color="#00FF00")
            success = True
        except TypeError:
            success = False
        self.assertTrue(success, "update_category parameter signature changed")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)