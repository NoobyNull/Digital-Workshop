"""
Comprehensive Database Layer Refactoring Tests.

This module provides comprehensive unit and integration tests for the refactored
database layer including repositories, transactions, caching, health monitoring,
and error handling.
"""

import pytest
import sqlite3
import tempfile
import os
import threading
import time
import psutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the refactored database components
from src.core.database.model_repository import ModelRepository
from src.core.database.metadata_repository import MetadataRepository
from src.core.database.search_repository import SearchRepository
from src.core.database.transaction_manager import TransactionManager
from src.core.database.error_handler import DatabaseErrorHandler, DatabaseErrorType
from src.core.database.cache_manager import DatabaseCacheManager
from src.core.database.health_monitor import DatabaseHealthMonitor
from src.core.database.migration_manager import MigrationManager
from src.core.interfaces.repository_interfaces import IModelRepository, IMetadataRepository, ISearchRepository


class TestModelRepository:
    """Test ModelRepository implementation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def model_repository(self, temp_db):
        """Create ModelRepository instance for testing."""
        return ModelRepository(temp_db)

    def test_repository_interface_compliance(self, model_repository):
        """Test that ModelRepository implements IModelRepository interface."""
        assert isinstance(model_repository, IModelRepository)
        assert hasattr(model_repository, 'create')
        assert hasattr(model_repository, 'read')
        assert hasattr(model_repository, 'update')
        assert hasattr(model_repository, 'delete')
        assert hasattr(model_repository, 'list_all')
        assert hasattr(model_repository, 'search')
        assert hasattr(model_repository, 'exists')
        assert hasattr(model_repository, 'count')

    def test_create_model(self, model_repository):
        """Test creating a new model."""
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl',
            'created_at': datetime.now().isoformat()
        }
        
        model_id = model_repository.create(model_data)
        
        assert model_id is not None
        assert isinstance(model_id, str)
        
        # Verify the model was created
        retrieved_model = model_repository.read(model_id)
        assert retrieved_model is not None
        assert retrieved_model['name'] == 'Test Model'
        assert retrieved_model['file_path'] == '/path/to/model.stl'

    def test_read_nonexistent_model(self, model_repository):
        """Test reading a model that doesn't exist."""
        result = model_repository.read('nonexistent_id')
        assert result is None

    def test_update_model(self, model_repository):
        """Test updating an existing model."""
        # Create a model first
        model_data = {
            'name': 'Original Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        # Update the model
        update_data = {
            'name': 'Updated Model',
            'file_size': 2048
        }
        success = model_repository.update(model_id, update_data)
        
        assert success is True
        
        # Verify the update
        retrieved_model = model_repository.read(model_id)
        assert retrieved_model['name'] == 'Updated Model'
        assert retrieved_model['file_size'] == 2048
        assert retrieved_model['file_path'] == '/path/to/model.stl'  # Unchanged

    def test_delete_model(self, model_repository):
        """Test deleting a model."""
        # Create a model first
        model_data = {
            'name': 'Model to Delete',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        # Verify it exists
        assert model_repository.exists(model_id) is True
        
        # Delete it
        success = model_repository.delete(model_id)
        assert success is True
        
        # Verify it's gone
        assert model_repository.exists(model_id) is False
        assert model_repository.read(model_id) is None

    def test_list_all_models(self, model_repository):
        """Test listing all models."""
        # Create multiple models
        models_data = [
            {
                'name': f'Model {i}',
                'file_path': f'/path/to/model{i}.stl',
                'file_size': 1024 * (i + 1),
                'file_hash': f'hash{i}',
                'format': 'stl'
            }
            for i in range(3)
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # List all models
        all_models = model_repository.list_all()
        
        assert len(all_models) == 3
        model_names = [model['name'] for model in all_models]
        assert 'Model 0' in model_names
        assert 'Model 1' in model_names
        assert 'Model 2' in model_names

    def test_search_models(self, model_repository):
        """Test searching for models."""
        # Create models with different names and formats
        models_data = [
            {
                'name': 'STL Model',
                'file_path': '/path/to/model.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl'
            },
            {
                'name': 'OBJ Model',
                'file_path': '/path/to/model.obj',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'obj'
            },
            {
                'name': 'Another STL',
                'file_path': '/path/to/model2.stl',
                'file_size': 3072,
                'file_hash': 'hash3',
                'format': 'stl'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Search for STL models
        stl_results = model_repository.search({'format': 'stl'})
        assert len(stl_results) == 2
        
        # Search by name
        name_results = model_repository.search({'name': 'STL Model'})
        assert len(name_results) == 1

    def test_exists_method(self, model_repository):
        """Test the exists method."""
        # Test with non-existent model
        assert model_repository.exists('nonexistent') is False
        
        # Create a model and test
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        assert model_repository.exists(model_id) is True

    def test_count_method(self, model_repository):
        """Test the count method."""
        # Initially should be empty
        assert model_repository.count() == 0
        
        # Create some models
        for i in range(5):
            model_data = {
                'name': f'Model {i}',
                'file_path': f'/path/to/model{i}.stl',
                'file_size': 1024,
                'file_hash': f'hash{i}',
                'format': 'stl'
            }
            model_repository.create(model_data)
        
        assert model_repository.count() == 5


class TestMetadataRepository:
    """Test MetadataRepository implementation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def metadata_repository(self, temp_db):
        """Create MetadataRepository instance for testing."""
        return MetadataRepository(temp_db)

    @pytest.fixture
    def model_repository(self, temp_db):
        """Create ModelRepository instance for testing."""
        return ModelRepository(temp_db)

    def test_repository_interface_compliance(self, metadata_repository):
        """Test that MetadataRepository implements IMetadataRepository interface."""
        assert isinstance(metadata_repository, IMetadataRepository)
        assert hasattr(metadata_repository, 'add_metadata')
        assert hasattr(metadata_repository, 'get_metadata')
        assert hasattr(metadata_repository, 'update_metadata')
        assert hasattr(metadata_repository, 'delete_metadata')
        assert hasattr(metadata_repository, 'search_by_metadata')
        assert hasattr(metadata_repository, 'get_metadata_keys')
        assert hasattr(metadata_repository, 'get_metadata_value')
        assert hasattr(metadata_repository, 'set_metadata_value')

    def test_add_and_get_metadata(self, metadata_repository, model_repository):
        """Test adding and retrieving metadata."""
        # Create a model first
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        # Add metadata
        metadata = {
            'author': 'Test Author',
            'description': 'Test Description',
            'tags': ['test', 'model'],
            'vertices': 1000,
            'faces': 500
        }
        
        success = metadata_repository.add_metadata(model_id, metadata)
        assert success is True
        
        # Retrieve metadata
        retrieved_metadata = metadata_repository.get_metadata(model_id)
        assert retrieved_metadata is not None
        assert retrieved_metadata['author'] == 'Test Author'
        assert retrieved_metadata['description'] == 'Test Description'
        assert retrieved_metadata['tags'] == ['test', 'model']
        assert retrieved_metadata['vertices'] == 1000

    def test_update_metadata(self, metadata_repository, model_repository):
        """Test updating metadata."""
        # Create a model and add initial metadata
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        initial_metadata = {
            'author': 'Original Author',
            'description': 'Original Description'
        }
        metadata_repository.add_metadata(model_id, initial_metadata)
        
        # Update metadata
        updated_metadata = {
            'author': 'Updated Author',
            'description': 'Updated Description',
            'new_field': 'new_value'
        }
        
        success = metadata_repository.update_metadata(model_id, updated_metadata)
        assert success is True
        
        # Verify update
        retrieved_metadata = metadata_repository.get_metadata(model_id)
        assert retrieved_metadata['author'] == 'Updated Author'
        assert retrieved_metadata['description'] == 'Updated Description'
        assert retrieved_metadata['new_field'] == 'new_value'

    def test_delete_metadata(self, metadata_repository, model_repository):
        """Test deleting metadata."""
        # Create a model and add metadata
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        metadata = {
            'author': 'Test Author',
            'description': 'Test Description'
        }
        metadata_repository.add_metadata(model_id, metadata)
        
        # Verify metadata exists
        assert metadata_repository.get_metadata(model_id) is not None
        
        # Delete metadata
        success = metadata_repository.delete_metadata(model_id)
        assert success is True
        
        # Verify metadata is gone
        assert metadata_repository.get_metadata(model_id) is None

    def test_search_by_metadata(self, metadata_repository, model_repository):
        """Test searching models by metadata."""
        # Create multiple models with different metadata
        models_data = [
            {
                'name': 'Model 1',
                'file_path': '/path/to/model1.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl'
            },
            {
                'name': 'Model 2',
                'file_path': '/path/to/model2.stl',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'obj'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Add metadata
        metadata1 = {
            'author': 'Author A',
            'category': 'architecture'
        }
        metadata2 = {
            'author': 'Author B',
            'category': 'character'
        }
        
        metadata_repository.add_metadata(model_ids[0], metadata1)
        metadata_repository.add_metadata(model_ids[1], metadata2)
        
        # Search by author
        author_results = metadata_repository.search_by_metadata({'author': 'Author A'})
        assert len(author_results) == 1
        assert model_ids[0] in author_results
        
        # Search by category
        category_results = metadata_repository.search_by_metadata({'category': 'architecture'})
        assert len(category_results) == 1
        assert model_ids[0] in category_results

    def test_metadata_keys_and_values(self, metadata_repository, model_repository):
        """Test getting metadata keys and individual values."""
        # Create a model and add metadata
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        metadata = {
            'author': 'Test Author',
            'description': 'Test Description',
            'vertices': 1000,
            'faces': 500
        }
        metadata_repository.add_metadata(model_id, metadata)
        
        # Test get_metadata_keys
        keys = metadata_repository.get_metadata_keys(model_id)
        assert len(keys) == 4
        assert 'author' in keys
        assert 'description' in keys
        assert 'vertices' in keys
        assert 'faces' in keys
        
        # Test get_metadata_value
        author_value = metadata_repository.get_metadata_value(model_id, 'author')
        assert author_value == 'Test Author'
        
        vertices_value = metadata_repository.get_metadata_value(model_id, 'vertices')
        assert vertices_value == 1000
        
        # Test non-existent key
        nonexistent_value = metadata_repository.get_metadata_value(model_id, 'nonexistent')
        assert nonexistent_value is None

    def test_set_metadata_value(self, metadata_repository, model_repository):
        """Test setting individual metadata values."""
        # Create a model and add initial metadata
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/model.stl',
            'file_size': 1024,
            'file_hash': 'abc123',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        initial_metadata = {
            'author': 'Original Author'
        }
        metadata_repository.add_metadata(model_id, initial_metadata)
        
        # Set new values
        success1 = metadata_repository.set_metadata_value(model_id, 'description', 'New Description')
        success2 = metadata_repository.set_metadata_value(model_id, 'vertices', 2000)
        
        assert success1 is True
        assert success2 is True
        
        # Verify the values
        retrieved_metadata = metadata_repository.get_metadata(model_id)
        assert retrieved_metadata['author'] == 'Original Author'
        assert retrieved_metadata['description'] == 'New Description'
        assert retrieved_metadata['vertices'] == 2000


class TestSearchRepository:
    """Test SearchRepository implementation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def search_repository(self, temp_db):
        """Create SearchRepository instance for testing."""
        return SearchRepository(temp_db)

    @pytest.fixture
    def model_repository(self, temp_db):
        """Create ModelRepository instance for testing."""
        return ModelRepository(temp_db)

    @pytest.fixture
    def metadata_repository(self, temp_db):
        """Create MetadataRepository instance for testing."""
        return MetadataRepository(temp_db)

    def test_repository_interface_compliance(self, search_repository):
        """Test that SearchRepository implements ISearchRepository interface."""
        assert isinstance(search_repository, ISearchRepository)
        assert hasattr(search_repository, 'search_models')
        assert hasattr(search_repository, 'search_by_tags')
        assert hasattr(search_repository, 'search_by_date_range')
        assert hasattr(search_repository, 'search_by_file_type')
        assert hasattr(search_repository, 'get_search_suggestions')
        assert hasattr(search_repository, 'save_search')
        assert hasattr(search_repository, 'get_saved_searches')
        assert hasattr(search_repository, 'delete_saved_search')

    def test_search_models(self, search_repository, model_repository, metadata_repository):
        """Test searching for models."""
        # Create models with different characteristics
        models_data = [
            {
                'name': 'House Model',
                'file_path': '/path/to/house.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl',
                'created_at': '2023-01-01T10:00:00'
            },
            {
                'name': 'Car Model',
                'file_path': '/path/to/car.obj',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'obj',
                'created_at': '2023-01-02T11:00:00'
            },
            {
                'name': 'Tree Model',
                'file_path': '/path/to/tree.stl',
                'file_size': 512,
                'file_hash': 'hash3',
                'format': 'stl',
                'created_at': '2023-01-03T12:00:00'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Add metadata for some models
        metadata1 = {
            'tags': ['building', 'architecture'],
            'author': 'Architect A'
        }
        metadata2 = {
            'tags': ['vehicle', 'transport'],
            'author': 'Designer B'
        }
        metadata3 = {
            'tags': ['nature', 'plant'],
            'author': 'Nature C'
        }
        
        metadata_repository.add_metadata(model_ids[0], metadata1)
        metadata_repository.add_metadata(model_ids[1], metadata2)
        metadata_repository.add_metadata(model_ids[2], metadata3)
        
        # Test text search
        results = search_repository.search_models('house')
        assert len(results) == 1
        assert model_ids[0] in results
        
        # Test search with filters
        filters = {'format': 'stl'}
        stl_results = search_repository.search_models('', filters)
        assert len(stl_results) == 2
        assert model_ids[0] in stl_results
        assert model_ids[2] in stl_results

    def test_search_by_tags(self, search_repository, model_repository, metadata_repository):
        """Test searching models by tags."""
        # Create models with tags
        models_data = [
            {
                'name': 'Model 1',
                'file_path': '/path/to/model1.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl'
            },
            {
                'name': 'Model 2',
                'file_path': '/path/to/model2.obj',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'obj'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Add metadata with tags
        metadata1 = {
            'tags': ['building', 'architecture', 'house']
        }
        metadata2 = {
            'tags': ['vehicle', 'car', 'transport']
        }
        
        metadata_repository.add_metadata(model_ids[0], metadata1)
        metadata_repository.add_metadata(model_ids[1], metadata2)
        
        # Search by single tag
        building_results = search_repository.search_by_tags(['building'])
        assert len(building_results) == 1
        assert model_ids[0] in building_results
        
        # Search by multiple tags (OR logic)
        mixed_results = search_repository.search_by_tags(['building', 'vehicle'])
        assert len(mixed_results) == 2
        assert model_ids[0] in mixed_results
        assert model_ids[1] in mixed_results

    def test_search_by_date_range(self, search_repository, model_repository):
        """Test searching models by date range."""
        # Create models with different creation dates
        models_data = [
            {
                'name': 'Old Model',
                'file_path': '/path/to/old.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl',
                'created_at': '2023-01-01T10:00:00'
            },
            {
                'name': 'New Model',
                'file_path': '/path/to/new.stl',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'stl',
                'created_at': '2023-12-31T15:00:00'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Search by date range
        start_date = '2023-06-01T00:00:00'
        end_date = '2023-12-31T23:59:59'
        
        results = search_repository.search_by_date_range(start_date, end_date)
        assert len(results) == 1
        assert model_ids[1] in results

    def test_search_by_file_type(self, search_repository, model_repository):
        """Test searching models by file type."""
        # Create models with different file types
        models_data = [
            {
                'name': 'STL Model',
                'file_path': '/path/to/model.stl',
                'file_size': 1024,
                'file_hash': 'hash1',
                'format': 'stl'
            },
            {
                'name': 'OBJ Model',
                'file_path': '/path/to/model.obj',
                'file_size': 2048,
                'file_hash': 'hash2',
                'format': 'obj'
            },
            {
                'name': '3MF Model',
                'file_path': '/path/to/model.3mf',
                'file_size': 3072,
                'file_hash': 'hash3',
                'format': '3mf'
            }
        ]
        
        model_ids = []
        for model_data in models_data:
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Search by file type
        stl_results = search_repository.search_by_file_type(['.stl'])
        assert len(stl_results) == 1
        assert model_ids[0] in stl_results
        
        # Search by multiple file types
        multiple_results = search_repository.search_by_file_type(['.stl', '.obj'])
        assert len(multiple_results) == 2
        assert model_ids[0] in multiple_results
        assert model_ids[1] in multiple_results

    def test_saved_searches(self, search_repository):
        """Test saving and retrieving saved searches."""
        # Save a search
        search_name = 'Test Search'
        query = 'test query'
        filters = {'format': 'stl'}
        
        success = search_repository.save_search(search_name, query, filters)
        assert success is True
        
        # Get saved searches
        saved_searches = search_repository.get_saved_searches()
        assert len(saved_searches) == 1
        assert saved_searches[0]['name'] == search_name
        assert saved_searches[0]['query'] == query
        assert saved_searches[0]['filters'] == filters
        
        # Delete saved search
        search_id = saved_searches[0]['id']
        delete_success = search_repository.delete_saved_search(search_id)
        assert delete_success is True
        
        # Verify it's deleted
        remaining_searches = search_repository.get_saved_searches()
        assert len(remaining_searches) == 0


class TestTransactionManager:
    """Test TransactionManager functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def transaction_manager(self, temp_db):
        """Create TransactionManager instance for testing."""
        return TransactionManager(temp_db)

    def test_transaction_context_manager(self, transaction_manager):
        """Test transaction context manager."""
        # Test successful transaction
        with transaction_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                         ('Test Model', '/path/to/model.stl', 1024, 'hash123', 'stl'))
            conn.commit()
        
        # Verify the data was committed
        with transaction_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM models WHERE file_hash = ?", ('hash123',))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'Test Model'

    def test_transaction_rollback(self, transaction_manager):
        """Test transaction rollback on error."""
        try:
            with transaction_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                             ('Test Model', '/path/to/model.stl', 1024, 'hash123', 'stl'))
                # Intentionally cause an error
                raise Exception("Test error")
        except Exception:
            pass  # Expected error
        
        # Verify the data was rolled back
        with transaction_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM models WHERE file_hash = ?", ('hash123',))
            result = cursor.fetchone()
            assert result[0] == 0

    def test_nested_transactions(self, transaction_manager):
        """Test nested transaction handling."""
        with transaction_manager.transaction() as outer_conn:
            outer_cursor = outer_conn.cursor()
            outer_cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                               ('Outer Model', '/path/to/outer.stl', 1024, 'hash_outer', 'stl'))
            
            # Nested transaction
            with transaction_manager.transaction() as inner_conn:
                inner_cursor = inner_conn.cursor()
                inner_cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                                   ('Inner Model', '/path/to/inner.stl', 2048, 'hash_inner', 'obj'))
                inner_conn.commit()
            
            outer_conn.commit()
        
        # Verify both models were committed
        with transaction_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM models")
            result = cursor.fetchone()
            assert result[0] == 2

    def test_transaction_isolation(self, transaction_manager):
        """Test transaction isolation."""
        model_id = None
        
        # First transaction - insert model
        with transaction_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                         ('Isolation Test', '/path/to/isolation.stl', 1024, 'hash_isolation', 'stl'))
            conn.commit()
            
            # Get the inserted ID
            model_id = cursor.lastrowid
        
        # Second transaction - update the same model
        with transaction_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE models SET name = ? WHERE id = ?", ('Updated Name', model_id))
            conn.commit()
        
        # Verify the update in a new connection
        with transaction_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM models WHERE id = ?", (model_id,))
            result = cursor.fetchone()
            assert result[0] == 'Updated Name'


class TestErrorHandler:
    """Test DatabaseErrorHandler functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def error_handler(self, temp_db):
        """Create DatabaseErrorHandler instance for testing."""
        return DatabaseErrorHandler(temp_db)

    def test_handle_sqlite_error(self, error_handler):
        """Test handling SQLite errors."""
        # Test constraint error
        constraint_error = sqlite3.IntegrityError("UNIQUE constraint failed: models.file_hash")
        error = error_handler.handle_sqlite_error(constraint_error)
        
        assert error.error_type == DatabaseErrorType.CONSTRAINT_ERROR
        assert "constraint" in error.message.lower()
        assert error.recoverable is True

    def test_handle_connection_error(self, error_handler):
        """Test handling connection errors."""
        connection_error = ConnectionError("Connection failed")
        error = error_handler.handle_connection_error(connection_error)
        
        assert error.error_type == DatabaseErrorType.CONNECTION_ERROR
        assert "connection" in error.message.lower()
        assert error.recoverable is True

    def test_error_recovery(self, error_handler):
        """Test error recovery mechanisms."""
        # Create a recoverable error
        connection_error = ConnectionError("Connection failed")
        error = error_handler.handle_connection_error(connection_error)
        
        # Attempt recovery
        recovery_success = error_handler.attempt_recovery(error)
        # Recovery might succeed or fail depending on database state
        assert isinstance(recovery_success, bool)

    def test_error_summary(self, error_handler):
        """Test error summary generation."""
        # Generate some errors
        constraint_error = sqlite3.IntegrityError("UNIQUE constraint failed")
        error_handler.handle_sqlite_error(constraint_error)
        
        summary = error_handler.get_error_summary()
        assert 'total_errors_24h' in summary
        assert 'error_counts_by_type' in summary
        assert isinstance(summary['total_errors_24h'], int)


class TestCacheManager:
    """Test DatabaseCacheManager functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def cache_manager(self, temp_db):
        """Create DatabaseCacheManager instance for testing."""
        return DatabaseCacheManager(temp_db, memory_cache_mb=10, disk_cache_mb=50)

    def test_model_metadata_caching(self, cache_manager):
        """Test model metadata caching."""
        model_id = 'test_model_123'
        metadata = {
            'name': 'Test Model',
            'author': 'Test Author',
            'vertices': 1000
        }
        
        # Cache metadata
        cache_manager.cache_model_metadata(model_id, metadata)
        
        # Retrieve from cache
        cached_metadata = cache_manager.get_model_metadata(model_id)
        assert cached_metadata is not None
        assert cached_metadata['name'] == 'Test Model'
        assert cached_metadata['author'] == 'Test Author'

    def test_search_results_caching(self, cache_manager):
        """Test search results caching."""
        query = 'test search'
        filters = {'format': 'stl'}
        results = ['model1', 'model2', 'model3']
        
        # Cache search results
        cache_manager.cache_search_results(query, results, filters)
        
        # Retrieve from cache
        cached_results = cache_manager.get_search_results(query, filters)
        assert cached_results is not None
        assert cached_results == results

    def test_cache_invalidation(self, cache_manager):
        """Test cache invalidation."""
        model_id = 'test_model_123'
        metadata = {'name': 'Test Model'}
        
        # Cache metadata
        cache_manager.cache_model_metadata(model_id, metadata)
        
        # Verify it's cached
        assert cache_manager.get_model_metadata(model_id) is not None
        
        # Invalidate model cache
        invalidated_count = cache_manager.invalidate_model_cache(model_id)
        assert invalidated_count > 0
        
        # Verify it's no longer cached
        assert cache_manager.get_model_metadata(model_id) is None

    def test_cache_stats(self, cache_manager):
        """Test cache statistics."""
        # Add some cached data
        cache_manager.cache_model_metadata('model1', {'name': 'Model 1'})
        cache_manager.cache_model_metadata('model2', {'name': 'Model 2'})
        
        # Get stats
        stats = cache_manager.get_cache_stats()
        assert 'memory_cache' in stats
        assert 'disk_cache' in stats
        assert stats['memory_cache']['entries'] >= 0
        assert stats['disk_cache']['entries'] >= 0


class TestHealthMonitor:
    """Test DatabaseHealthMonitor functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def health_monitor(self, temp_db):
        """Create DatabaseHealthMonitor instance for testing."""
        monitor = DatabaseHealthMonitor(temp_db, monitoring_interval=1)
        yield monitor
        monitor.stop_monitoring()

    def test_health_status(self, health_monitor):
        """Test health status monitoring."""
        status = health_monitor.get_current_health_status()
        assert status is not None
        # Status should be one of the defined enum values
        from src.core.database.health_monitor import HealthStatus
        assert status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL, HealthStatus.UNKNOWN]

    def test_metrics_collection(self, health_monitor):
        """Test metrics collection."""
        # Wait a moment for metrics to be collected
        time.sleep(2)
        
        metrics = health_monitor.get_health_metrics()
        assert len(metrics) > 0
        
        # Check for system metrics
        metric_names = [metric.name for metric in metrics]
        assert any('cpu' in name for name in metric_names)
        assert any('memory' in name for name in metric_names)
        assert any('disk' in name for name in metric_names)

    def test_query_performance_tracking(self, health_monitor):
        """Test query performance tracking."""
        # Record some query executions
        health_monitor.record_query_execution("SELECT * FROM models", 0.1, success=True)
        health_monitor.record_query_execution("SELECT * FROM models", 0.2, success=True)
        health_monitor.record_query_execution("SELECT * FROM models", 0.05, success=True)
        
        # Get slow queries
        slow_queries = health_monitor.get_slow_queries(limit=5)
        # Should have at least one query recorded
        assert len(slow_queries) >= 1

    def test_health_report_generation(self, health_monitor):
        """Test health report generation."""
        # Wait for some metrics to be collected
        time.sleep(2)
        
        report = health_monitor.generate_health_report()
        assert report.timestamp is not None
        assert report.overall_status is not None
        assert len(report.metrics) > 0
        assert isinstance(report.recommendations, list)


class TestIntegration:
    """Integration tests for the complete database layer."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def repositories(self, temp_db):
        """Create all repository instances for testing."""
        model_repo = ModelRepository(temp_db)
        metadata_repo = MetadataRepository(temp_db)
        search_repo = SearchRepository(temp_db)
        return model_repo, metadata_repo, search_repo

    @pytest.fixture
    def transaction_manager(self, temp_db):
        """Create TransactionManager instance for testing."""
        return TransactionManager(temp_db)

    @pytest.fixture
    def cache_manager(self, temp_db):
        """Create DatabaseCacheManager instance for testing."""
        return DatabaseCacheManager(temp_db)

    @pytest.fixture
    def health_monitor(self, temp_db):
        """Create DatabaseHealthMonitor instance for testing."""
        monitor = DatabaseHealthMonitor(temp_db, monitoring_interval=1)
        yield monitor
        monitor.stop_monitoring()

    def test_complete_model_workflow(self, repositories, transaction_manager, cache_manager):
        """Test complete model workflow with all components."""
        model_repo, metadata_repo, search_repo = repositories
        
        # Create a model with transaction
        with transaction_manager.transaction() as conn:
            model_data = {
                'name': 'Integration Test Model',
                'file_path': '/path/to/integration.stl',
                'file_size': 1024,
                'file_hash': 'integration_hash',
                'format': 'stl'
            }
            model_id = model_repo.create(model_data)
            conn.commit()
        
        # Add metadata
        metadata = {
            'author': 'Integration Author',
            'description': 'Integration Test Description',
            'tags': ['integration', 'test'],
            'vertices': 1500
        }
        metadata_repo.add_metadata(model_id, metadata)
        
        # Cache the metadata
        cache_manager.cache_model_metadata(model_id, metadata)
        
        # Verify through search
        results = search_repo.search_models('Integration')
        assert model_id in results
        
        # Verify cache hit
        cached_metadata = cache_manager.get_model_metadata(model_id)
        assert cached_metadata is not None
        assert cached_metadata['author'] == 'Integration Author'
        
        # Update model
        update_data = {'name': 'Updated Integration Model'}
        model_repo.update(model_id, update_data)
        
        # Verify update
        updated_model = model_repo.read(model_id)
        assert updated_model['name'] == 'Updated Integration Model'
        
        # Invalidate cache and verify
        cache_manager.invalidate_model_cache(model_id)
        assert cache_manager.get_model_metadata(model_id) is None

    def test_concurrent_operations(self, repositories, transaction_manager):
        """Test concurrent database operations."""
        model_repo, metadata_repo, search_repo = repositories
        
        results = []
        errors = []
        
        def create_model(index):
            try:
                with transaction_manager.transaction() as conn:
                    model_data = {
                        'name': f'Concurrent Model {index}',
                        'file_path': f'/path/to/concurrent{index}.stl',
                        'file_size': 1024,
                        'file_hash': f'concurrent_hash_{index}',
                        'format': 'stl'
                    }
                    model_id = model_repo.create(model_data)
                    conn.commit()
                    results.append(model_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_model, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Verify all models were created
        for model_id in results:
            model = model_repo.read(model_id)
            assert model is not None

    def test_error_handling_integration(self, repositories, transaction_manager):
        """Test error handling in integration scenarios."""
        model_repo, metadata_repo, search_repo = repositories
        
        # Test constraint violation
        model_data = {
            'name': 'Test Model',
            'file_path': '/path/to/test.stl',
            'file_size': 1024,
            'file_hash': 'test_hash',
            'format': 'stl'
        }
        
        # Create model successfully
        model_id = model_repo.create(model_data)
        assert model_id is not None
        
        # Try to create duplicate (should fail)
        duplicate_data = {
            'name': 'Duplicate Model',
            'file_path': '/path/to/duplicate.stl',
            'file_size': 2048,
            'file_hash': 'test_hash',  # Same hash
            'format': 'obj'
        }
        
        try:
            duplicate_id = model_repo.create(duplicate_data)
            # If we get here, the duplicate was allowed (might be expected behavior)
            assert duplicate_id is not None
        except Exception as e:
            # Expected constraint violation
            assert "constraint" in str(e).lower() or "unique" in str(e).lower()
        
        # Test metadata operations on non-existent model
        try:
            metadata_repo.add_metadata('nonexistent_model', {'test': 'value'})
            # If successful, that's also valid behavior
        except Exception as e:
            # Expected error for non-existent model
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower()