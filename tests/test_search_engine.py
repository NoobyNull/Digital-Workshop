"""
Tests for the search engine module.

This module contains unit tests and integration tests for the search functionality
including FTS5 search, filtering, search history, and saved searches.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from src.core.search_engine import SearchEngine, get_search_engine
from src.core.database_manager import DatabaseManager


class TestSearchEngine(unittest.TestCase):
    """Test cases for the SearchEngine class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests."""
        # Create temporary database
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        cls.db_path = cls.temp_db.name
        
        # Initialize database manager
        cls.db_manager = DatabaseManager(cls.db_path)
        
        # Add test data
        cls._add_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        # Close database connections
        cls.db_manager.close()
        
        # Remove temporary database file
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)
    
    def setUp(self):
        """Set up for each test."""
        # Create new search engine instance for each test
        self.search_engine = SearchEngine(self.db_path)
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up any search history
        self.search_engine.clear_search_history(0)
    
    @classmethod
    def _add_test_data(cls):
        """Add test data to the database."""
        # Add test models
        model_ids = []
        
        # Model 1: Character model
        model_id = cls.db_manager.add_model(
            filename="character.stl",
            format="stl",
            file_path="/models/character.stl",
            file_size=1024000
        )
        model_ids.append(model_id)
        cls.db_manager.add_model_metadata(
            model_id=model_id,
            title="Fantasy Character",
            description="A fantasy character model for game development",
            keywords="character, fantasy, game, hero",
            category="Characters",
            source="Test Asset",
            rating=5
        )
        
        # Model 2: Building model
        model_id = cls.db_manager.add_model(
            filename="building.obj",
            format="obj",
            file_path="/models/building.obj",
            file_size=2048000
        )
        model_ids.append(model_id)
        cls.db_manager.add_model_metadata(
            model_id=model_id,
            title="Medieval Castle",
            description="A medieval castle model with detailed architecture",
            keywords="building, medieval, castle, architecture",
            category="Buildings",
            source="Test Asset",
            rating=4
        )
        
        # Model 3: Vehicle model
        model_id = cls.db_manager.add_model(
            filename="car.step",
            format="step",
            file_path="/models/car.step",
            file_size=5120000
        )
        model_ids.append(model_id)
        cls.db_manager.add_model_metadata(
            model_id=model_id,
            title="Sports Car",
            description="A sports car model with high detail",
            keywords="vehicle, car, sports, automotive",
            category="Vehicles",
            source="Test Asset",
            rating=3
        )
        
        # Model 4: Nature model
        model_id = cls.db_manager.add_model(
            filename="tree.3mf",
            format="3mf",
            file_path="/models/tree.3mf",
            file_size=3072000
        )
        model_ids.append(model_id)
        cls.db_manager.add_model_metadata(
            model_id=model_id,
            title="Oak Tree",
            description="A detailed oak tree model for outdoor scenes",
            keywords="nature, tree, oak, outdoor, plant",
            category="Nature",
            source="Test Asset",
            rating=4
        )
        
        # Model 5: Object without metadata
        model_id = cls.db_manager.add_model(
            filename="cube.stl",
            format="stl",
            file_path="/models/cube.stl",
            file_size=102400
        )
        model_ids.append(model_id)
        cls.db_manager.add_model_metadata(
            model_id=model_id,
            title="Simple Cube",
            description="A basic cube shape",
            keywords="cube, basic, shape, simple",
            category="Objects",
            source="Test Asset",
            rating=2
        )
        
        return model_ids
    
    def test_fts_initialization(self):
        """Test that FTS5 tables are properly initialized."""
        # Check if FTS tables exist
        with self.search_engine.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check models_fts table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models_fts'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, "models_fts table should exist")
            
            # Check model_metadata_fts table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_metadata_fts'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, "model_metadata_fts table should exist")
    
    def test_basic_search(self):
        """Test basic text search functionality."""
        # Search for "character"
        results = self.search_engine.search("character")
        
        self.assertIn("results", results)
        self.assertIn("total_count", results)
        self.assertGreater(results["total_count"], 0)
        self.assertGreater(len(results["results"]), 0)
        
        # Check that the expected model is in results
        found_character = False
        for result in results["results"]:
            if result.get("title") == "Fantasy Character":
                found_character = True
                break
        
        self.assertTrue(found_character, "Fantasy Character should be found in search results")
    
    def test_keyword_search(self):
        """Test searching by keywords."""
        # Search for "medieval" which is in keywords
        results = self.search_engine.search("medieval")
        
        self.assertGreater(results["total_count"], 0)
        
        # Check that the castle model is in results
        found_castle = False
        for result in results["results"]:
            if result.get("title") == "Medieval Castle":
                found_castle = True
                break
        
        self.assertTrue(found_castle, "Medieval Castle should be found when searching for 'medieval'")
    
    def test_category_filter(self):
        """Test category-based filtering."""
        # Filter by "Vehicles" category
        filters = {"category": "Vehicles"}
        results = self.search_engine.search("", filters)
        
        self.assertGreater(results["total_count"], 0)
        
        # All results should be in Vehicles category
        for result in results["results"]:
            self.assertEqual(result.get("category"), "Vehicles")
    
    def test_format_filter(self):
        """Test format-based filtering."""
        # Filter by STL format
        filters = {"format": "stl"}
        results = self.search_engine.search("", filters)
        
        self.assertGreater(results["total_count"], 0)
        
        # All results should be STL format
        for result in results["results"]:
            self.assertEqual(result.get("format"), "stl")
    
    def test_rating_filter(self):
        """Test rating-based filtering."""
        # Filter by minimum rating of 4
        filters = {"min_rating": 4}
        results = self.search_engine.search("", filters)
        
        self.assertGreater(results["total_count"], 0)
        
        # All results should have rating >= 4
        for result in results["results"]:
            self.assertGreaterEqual(result.get("rating", 0), 4)
    
    def test_multiple_filters(self):
        """Test using multiple filters together."""
        # Filter by Buildings category and minimum rating of 4
        filters = {
            "category": "Buildings",
            "min_rating": 4
        }
        results = self.search_engine.search("", filters)
        
        # Should find the Medieval Castle
        self.assertGreater(results["total_count"], 0)
        
        for result in results["results"]:
            self.assertEqual(result.get("category"), "Buildings")
            self.assertGreaterEqual(result.get("rating", 0), 4)
    
    def test_search_with_query_and_filters(self):
        """Test combining text search with filters."""
        # Search for "car" in Vehicles category
        filters = {"category": "Vehicles"}
        results = self.search_engine.search("car", filters)
        
        self.assertGreater(results["total_count"], 0)
        
        # Should find the Sports Car
        found_car = False
        for result in results["results"]:
            if result.get("title") == "Sports Car":
                found_car = True
                break
        
        self.assertTrue(found_car, "Sports Car should be found with query 'car' and Vehicles filter")
    
    def test_boolean_operators(self):
        """Test boolean operators in search queries."""
        # Search for "character AND fantasy"
        results = self.search_engine.search("character AND fantasy")
        
        self.assertGreater(results["total_count"], 0)
        
        # Should find the Fantasy Character
        found_character = False
        for result in results["results"]:
            if result.get("title") == "Fantasy Character":
                found_character = True
                break
        
        self.assertTrue(found_character, "Fantasy Character should be found with 'character AND fantasy'")
    
    def test_search_history(self):
        """Test search history functionality."""
        # Perform a search
        self.search_engine.search("test query")
        
        # Get search history
        history = self.search_engine.get_search_history()
        
        self.assertGreater(len(history), 0)
        
        # Check that our search is in history
        found_search = False
        for item in history:
            if item.get("query") == "test query":
                found_search = True
                break
        
        self.assertTrue(found_search, "Search should be recorded in history")
    
    def test_saved_searches(self):
        """Test saved searches functionality."""
        # Save a search
        search_id = self.search_engine.save_search(
            name="Test Search",
            query="building",
            filters={"category": "Buildings"}
        )
        
        self.assertIsNotNone(search_id)
        self.assertGreater(search_id, 0)
        
        # Get saved searches
        saved_searches = self.search_engine.get_saved_searches()
        
        self.assertGreater(len(saved_searches), 0)
        
        # Check that our search is saved
        found_search = False
        for item in saved_searches:
            if item.get("name") == "Test Search":
                found_search = True
                self.assertEqual(item.get("query"), "building")
                self.assertEqual(item.get("filters", {}).get("category"), "Buildings")
                break
        
        self.assertTrue(found_search, "Saved search should be retrievable")
    
    def test_delete_saved_search(self):
        """Test deleting saved searches."""
        # Save a search
        search_id = self.search_engine.save_search(
            name="Delete Test",
            query="delete me",
            filters={}
        )
        
        # Delete the search
        success = self.search_engine.delete_saved_search(search_id)
        self.assertTrue(success)
        
        # Check that it's gone
        saved_searches = self.search_engine.get_saved_searches()
        found_search = False
        for item in saved_searches:
            if item.get("name") == "Delete Test":
                found_search = True
                break
        
        self.assertFalse(found_search, "Deleted search should not be in saved searches")
    
    def test_search_suggestions(self):
        """Test search suggestions functionality."""
        # Get suggestions for "cha"
        suggestions = self.search_engine.get_search_suggestions("cha")
        
        self.assertIsInstance(suggestions, list)
        
        # Should suggest "character" or similar
        found_character = False
        for suggestion in suggestions:
            if "character" in suggestion.lower():
                found_character = True
                break
        
        self.assertTrue(found_character, "Should suggest 'character' for 'cha' query")
    
    def test_search_performance(self):
        """Test search performance for multiple queries."""
        import time
        
        # Perform multiple searches and measure time
        start_time = time.time()
        
        for i in range(10):
            results = self.search_engine.search(f"test query {i}")
            self.assertIn("results", results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Average search time should be less than 1 second
        avg_time = total_time / 10
        self.assertLess(avg_time, 1.0, "Average search time should be less than 1 second")
    
    def test_empty_search(self):
        """Test handling of empty searches."""
        # Empty search with no filters should return empty results
        results = self.search_engine.search("", {})
        
        self.assertEqual(results["total_count"], 0)
        self.assertEqual(len(results["results"]), 0)
    
    def test_no_results_search(self):
        """Test handling of searches with no results."""
        # Search for something that doesn't exist
        results = self.search_engine.search("nonexistent_model_xyz")
        
        self.assertEqual(results["total_count"], 0)
        self.assertEqual(len(results["results"]), 0)
    
    def test_rebuild_fts_indexes(self):
        """Test rebuilding FTS indexes."""
        # This should not raise an exception
        self.search_engine.rebuild_fts_indexes()
        
        # Search should still work after rebuild
        results = self.search_engine.search("character")
        self.assertGreater(results["total_count"], 0)


class TestSearchEngineIntegration(unittest.TestCase):
    """Integration tests for the search engine with database operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests."""
        # Create temporary database
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        cls.db_path = cls.temp_db.name
        
        # Initialize database manager
        cls.db_manager = DatabaseManager(cls.db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        # Close database connections
        cls.db_manager.close()
        
        # Remove temporary database file
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)
    
    def test_fts_triggers(self):
        """Test that FTS triggers work correctly when adding/updating models."""
        # Create search engine
        search_engine = SearchEngine(self.db_path)
        
        # Add a model
        model_id = self.db_manager.add_model(
            filename="test_model.stl",
            format="stl",
            file_path="/test/test_model.stl",
            file_size=1024000
        )
        
        # Add metadata
        self.db_manager.add_model_metadata(
            model_id=model_id,
            title="Test Model",
            description="A test model for FTS trigger testing",
            keywords="test, model, trigger",
            category="Test",
            source="Integration Test",
            rating=5
        )
        
        # Search for the model
        results = search_engine.search("trigger")
        
        self.assertGreater(results["total_count"], 0)
        
        # Find our test model
        found_model = False
        for result in results["results"]:
            if result.get("title") == "Test Model":
                found_model = True
                break
        
        self.assertTrue(found_model, "Newly added model should be searchable via FTS")
    
    def test_singleton_pattern(self):
        """Test that the get_search_engine singleton function works correctly."""
        # Get search engine instance
        engine1 = get_search_engine(self.db_path)
        engine2 = get_search_engine(self.db_path)
        
        # Should be the same instance
        self.assertIs(engine1, engine2, "get_search_engine should return the same instance")


if __name__ == '__main__':
    unittest.main()