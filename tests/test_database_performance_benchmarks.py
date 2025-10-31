"""
Database Performance Benchmarking Tests.

This module provides comprehensive performance benchmarking tests for the refactored
database layer to ensure it meets performance requirements and maintains optimal
performance under various load conditions.
"""

import pytest
import sqlite3
import tempfile
import os
import time
import threading
import statistics
import psutil
import gc
import tracemalloc
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import concurrent.futures
import random
import string

# Import the refactored database components
from src.core.database.model_repository import ModelRepository
from src.core.database.metadata_repository import MetadataRepository
from src.core.database.search_repository import SearchRepository
from src.core.database.transaction_manager import TransactionManager
from src.core.database.cache_manager import DatabaseCacheManager
from src.core.database.health_monitor import DatabaseHealthMonitor


class PerformanceBenchmark:
    """Performance benchmarking utility class."""

    def __init__(self, name: str):
        """
        Initialize performance benchmark.

        Args:
            name: Benchmark name
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_end = None
        self.results = {}

    def __enter__(self):
        """Start benchmarking."""
        gc.collect()  # Clean up before starting
        tracemalloc.start()
        self.start_time = time.perf_counter()
        self.memory_start = psutil.Process().memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End benchmarking and record results."""
        self.end_time = time.perf_counter()
        self.memory_end = psutil.Process().memory_info().rss
        tracemalloc.stop()
        
        self.results = {
            'duration': self.end_time - self.start_time,
            'memory_delta': self.memory_end - self.memory_start,
            'memory_delta_mb': (self.memory_end - self.memory_start) / (1024 * 1024)
        }

    def get_duration(self) -> float:
        """Get benchmark duration in seconds."""
        return self.results.get('duration', 0.0)

    def get_memory_delta(self) -> int:
        """Get memory delta in bytes."""
        return self.results.get('memory_delta', 0)

    def get_memory_delta_mb(self) -> float:
        """Get memory delta in MB."""
        return self.results.get('memory_delta_mb', 0.0)


class TestQueryPerformance:
    """Test query performance benchmarks."""

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

    @pytest.fixture
    def metadata_repository(self, temp_db):
        """Create MetadataRepository instance for testing."""
        return MetadataRepository(temp_db)

    @pytest.fixture
    def search_repository(self, temp_db):
        """Create SearchRepository instance for testing."""
        return SearchRepository(temp_db)

    @pytest.fixture
    def transaction_manager(self, temp_db):
        """Create TransactionManager instance for testing."""
        return TransactionManager(temp_db)

    @pytest.fixture
    def cache_manager(self, temp_db):
        """Create DatabaseCacheManager instance for testing."""
        return DatabaseCacheManager(temp_db, memory_cache_mb=50, disk_cache_mb=200)

    def test_single_model_operations_performance(self, model_repository):
        """Test performance of single model CRUD operations."""
        model_data = {
            'name': 'Performance Test Model',
            'file_path': '/path/to/performance.stl',
            'file_size': 1024,
            'file_hash': 'perf_hash_123',
            'format': 'stl'
        }
        
        # Test CREATE performance
        with PerformanceBenchmark("create_single_model") as benchmark:
            model_id = model_repository.create(model_data)
        
        create_time = benchmark.get_duration()
        assert create_time < 0.1, f"CREATE operation took {create_time:.3f}s, should be < 0.1s"
        
        # Test READ performance
        with PerformanceBenchmark("read_single_model") as benchmark:
            retrieved_model = model_repository.read(model_id)
        
        read_time = benchmark.get_duration()
        assert read_time < 0.05, f"READ operation took {read_time:.3f}s, should be < 0.05s"
        assert retrieved_model is not None
        
        # Test UPDATE performance
        update_data = {'name': 'Updated Performance Model'}
        with PerformanceBenchmark("update_single_model") as benchmark:
            success = model_repository.update(model_id, update_data)
        
        update_time = benchmark.get_duration()
        assert update_time < 0.1, f"UPDATE operation took {update_time:.3f}s, should be < 0.1s"
        assert success is True
        
        # Test DELETE performance
        with PerformanceBenchmark("delete_single_model") as benchmark:
            success = model_repository.delete(model_id)
        
        delete_time = benchmark.get_duration()
        assert delete_time < 0.1, f"DELETE operation took {delete_time:.3f}s, should be < 0.1s"
        assert success is True

    def test_bulk_operations_performance(self, model_repository):
        """Test performance of bulk operations."""
        # Create 1000 models
        num_models = 1000
        model_ids = []
        
        with PerformanceBenchmark("bulk_create_models") as benchmark:
            for i in range(num_models):
                model_data = {
                    'name': f'Bulk Model {i}',
                    'file_path': f'/path/to/bulk{i}.stl',
                    'file_size': 1024 + i,
                    'file_hash': f'bulk_hash_{i}',
                    'format': 'stl'
                }
                model_id = model_repository.create(model_data)
                model_ids.append(model_id)
        
        bulk_create_time = benchmark.get_duration()
        avg_create_time = bulk_create_time / num_models
        assert avg_create_time < 0.01, f"Average CREATE time {avg_create_time:.4f}s, should be < 0.01s"
        
        # Test bulk READ performance
        with PerformanceBenchmark("bulk_read_models") as benchmark:
            for model_id in model_ids[:100]:  # Read first 100
                model = model_repository.read(model_id)
                assert model is not None
        
        bulk_read_time = benchmark.get_duration()
        avg_read_time = bulk_read_time / 100
        assert avg_read_time < 0.005, f"Average READ time {avg_read_time:.4f}s, should be < 0.005s"
        
        # Test LIST ALL performance
        with PerformanceBenchmark("list_all_models") as benchmark:
            all_models = model_repository.list_all()
        
        list_time = benchmark.get_duration()
        assert list_time < 0.5, f"LIST ALL operation took {list_time:.3f}s, should be < 0.5s"
        assert len(all_models) == num_models

    def test_search_performance(self, model_repository, metadata_repository, search_repository):
        """Test search operation performance."""
        # Create models with various characteristics for search testing
        formats = ['stl', 'obj', '3mf', 'ply']
        names = ['House', 'Car', 'Tree', 'Building', 'Person', 'Animal', 'Plant', 'Rock']
        
        model_ids = []
        for i in range(500):
            format_type = formats[i % len(formats)]
            name = names[i % len(names)]
            
            model_data = {
                'name': f'{name} Model {i}',
                'file_path': f'/path/to/{name.lower()}{i}.{format_type}',
                'file_size': 1024 + (i * 10),
                'file_hash': f'search_hash_{i}',
                'format': format_type
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
            
            # Add metadata for some models
            if i % 3 == 0:
                metadata = {
                    'author': f'Author {i % 10}',
                    'category': name.lower(),
                    'tags': [name.lower(), format_type, 'test']
                }
                metadata_repository.add_metadata(model_id, metadata)
        
        # Test text search performance
        with PerformanceBenchmark("text_search_performance") as benchmark:
            results = search_repository.search_models('House')
        
        search_time = benchmark.get_duration()
        assert search_time < 0.1, f"Text search took {search_time:.3f}s, should be < 0.1s"
        
        # Test filter search performance
        with PerformanceBenchmark("filter_search_performance") as benchmark:
            results = search_repository.search_models('', {'format': 'stl'})
        
        filter_search_time = benchmark.get_duration()
        assert filter_search_time < 0.1, f"Filter search took {filter_search_time:.3f}s, should be < 0.1s"
        
        # Test tag search performance
        with PerformanceBenchmark("tag_search_performance") as benchmark:
            results = search_repository.search_by_tags(['house'])
        
        tag_search_time = benchmark.get_duration()
        assert tag_search_time < 0.1, f"Tag search took {tag_search_time:.3f}s, should be < 0.1s"

    def test_metadata_operations_performance(self, model_repository, metadata_repository):
        """Test metadata operation performance."""
        # Create a model
        model_data = {
            'name': 'Metadata Performance Test',
            'file_path': '/path/to/metadata_perf.stl',
            'file_size': 1024,
            'file_hash': 'metadata_perf_hash',
            'format': 'stl'
        }
        model_id = model_repository.create(model_data)
        
        # Test ADD metadata performance
        metadata = {
            'author': 'Performance Author',
            'description': 'Performance test description',
            'vertices': 10000,
            'faces': 5000,
            'tags': ['performance', 'test', 'metadata'],
            'complex_data': {'nested': {'value': 123}}
        }
        
        with PerformanceBenchmark("add_metadata_performance") as benchmark:
            success = metadata_repository.add_metadata(model_id, metadata)
        
        add_metadata_time = benchmark.get_duration()
        assert add_metadata_time < 0.1, f"ADD metadata took {add_metadata_time:.3f}s, should be < 0.1s"
        assert success is True
        
        # Test GET metadata performance
        with PerformanceBenchmark("get_metadata_performance") as benchmark:
            retrieved_metadata = metadata_repository.get_metadata(model_id)
        
        get_metadata_time = benchmark.get_duration()
        assert get_metadata_time < 0.05, f"GET metadata took {get_metadata_time:.3f}s, should be < 0.05s"
        assert retrieved_metadata is not None
        
        # Test UPDATE metadata performance
        updated_metadata = {
            'author': 'Updated Performance Author',
            'new_field': 'new_value'
        }
        
        with PerformanceBenchmark("update_metadata_performance") as benchmark:
            success = metadata_repository.update_metadata(model_id, updated_metadata)
        
        update_metadata_time = benchmark.get_duration()
        assert update_metadata_time < 0.1, f"UPDATE metadata took {update_metadata_time:.3f}s, should be < 0.1s"
        
        # Test search by metadata performance
        with PerformanceBenchmark("search_metadata_performance") as benchmark:
            results = metadata_repository.search_by_metadata({'author': 'Updated Performance Author'})
        
        search_metadata_time = benchmark.get_duration()
        assert search_metadata_time < 0.1, f"Search metadata took {search_metadata_time:.3f}s, should be < 0.1s"
        assert model_id in results

    def test_cache_performance(self, model_repository, cache_manager):
        """Test caching performance improvements."""
        # Create test models
        model_ids = []
        for i in range(100):
            model_data = {
                'name': f'Cache Test Model {i}',
                'file_path': f'/path/to/cache{i}.stl',
                'file_size': 1024,
                'file_hash': f'cache_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        # Test uncached performance (first access)
        start_time = time.perf_counter()
        for model_id in model_ids[:50]:
            model = model_repository.read(model_id)
            assert model is not None
        uncached_time = time.perf_counter() - start_time
        
        # Cache the models
        for model_id in model_ids[:50]:
            model = model_repository.read(model_id)
            cache_manager.cache_model_metadata(model_id, model)
        
        # Test cached performance (second access)
        start_time = time.perf_counter()
        for model_id in model_ids[:50]:
            cached_model = cache_manager.get_model_metadata(model_id)
            assert cached_model is not None
        cached_time = time.perf_counter() - start_time
        
        # Cache should be significantly faster
        speedup = uncached_time / cached_time if cached_time > 0 else float('inf')
        assert speedup > 2, f"Cache speedup {speedup:.1f}x, should be > 2x"
        
        print(f"Cache performance: Uncached {uncached_time:.3f}s, Cached {cached_time:.3f}s, Speedup {speedup:.1f}x")

    def test_transaction_performance(self, model_repository, transaction_manager):
        """Test transaction performance."""
        # Test single transaction performance
        with PerformanceBenchmark("single_transaction") as benchmark:
            with transaction_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                             ('Transaction Test', '/path/to/transaction.stl', 1024, 'transaction_hash', 'stl'))
                conn.commit()
        
        single_tx_time = benchmark.get_duration()
        assert single_tx_time < 0.1, f"Single transaction took {single_tx_time:.3f}s, should be < 0.1s"
        
        # Test batch transaction performance
        with PerformanceBenchmark("batch_transaction") as benchmark:
            with transaction_manager.transaction() as conn:
                cursor = conn.cursor()
                for i in range(100):
                    cursor.execute("INSERT INTO models (name, file_path, file_size, file_hash, format) VALUES (?, ?, ?, ?, ?)",
                                 (f'Batch Model {i}', f'/path/to/batch{i}.stl', 1024, f'batch_hash_{i}', 'stl'))
                conn.commit()
        
        batch_tx_time = benchmark.get_duration()
        avg_batch_time = batch_tx_time / 100
        assert avg_batch_time < 0.01, f"Average batch transaction time {avg_batch_time:.4f}s, should be < 0.01s"


class TestMemoryPerformance:
    """Test memory usage and leak detection."""

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

    @pytest.fixture
    def cache_manager(self, temp_db):
        """Create DatabaseCacheManager instance for testing."""
        return DatabaseCacheManager(temp_db, memory_cache_mb=10, disk_cache_mb=50)

    def test_memory_usage_stability(self, model_repository):
        """Test that memory usage remains stable during repeated operations."""
        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss
        
        # Perform many operations
        model_ids = []
        for i in range(1000):
            model_data = {
                'name': f'Memory Test Model {i}',
                'file_path': f'/path/to/memory{i}.stl',
                'file_size': 1024,
                'file_hash': f'memory_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
            
            # Read the model
            model = model_repository.read(model_id)
            assert model is not None
            
            # Update occasionally
            if i % 10 == 0:
                model_repository.update(model_id, {'name': f'Updated Memory Test Model {i}'})
        
        # Check memory after operations
        gc.collect()
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - baseline_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory increase should be reasonable (less than 100MB for 1000 operations)
        assert memory_increase_mb < 100, f"Memory increase {memory_increase_mb:.1f}MB, should be < 100MB"
        
        # Clean up
        for model_id in model_ids:
            model_repository.delete(model_id)
        
        # Check memory after cleanup
        gc.collect()
        cleanup_memory = psutil.Process().memory_info().rss
        cleanup_increase = cleanup_memory - baseline_memory
        cleanup_increase_mb = cleanup_increase / (1024 * 1024)
        
        # Memory should return closer to baseline after cleanup
        assert cleanup_increase_mb < 50, f"Memory after cleanup {cleanup_increase_mb:.1f}MB, should be < 50MB"

    def test_cache_memory_management(self, cache_manager, model_repository):
        """Test cache memory management and cleanup."""
        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss
        
        # Create and cache many models
        model_ids = []
        for i in range(200):
            model_data = {
                'name': f'Cache Memory Test {i}',
                'file_path': f'/path/to/cache_memory{i}.stl',
                'file_size': 1024,
                'file_hash': f'cache_memory_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
            
            # Cache the model
            cache_manager.cache_model_metadata(model_id, model_data)
        
        # Check memory with cache
        gc.collect()
        cached_memory = psutil.Process().memory_info().rss
        cached_increase = cached_memory - baseline_memory
        cached_increase_mb = cached_increase / (1024 * 1024)
        
        # Cache should not use excessive memory
        assert cached_increase_mb < 50, f"Cache memory increase {cached_increase_mb:.1f}MB, should be < 50MB"
        
        # Clear cache
        cache_manager.clear_all_cache()
        
        # Check memory after cache clear
        gc.collect()
        cleared_memory = psutil.Process().memory_info().rss
        cleared_increase = cleared_memory - baseline_memory
        cleared_increase_mb = cleared_increase / (1024 * 1024)
        
        # Memory should be significantly reduced after cache clear
        memory_reduction = cached_increase_mb - cleared_increase_mb
        assert memory_reduction > 10, f"Cache clear should reduce memory by >10MB, reduced by {memory_reduction:.1f}MB"

    def test_large_dataset_memory_performance(self, model_repository):
        """Test memory performance with large datasets."""
        # Create a large number of models
        num_models = 5000
        
        with PerformanceBenchmark("large_dataset_creation") as benchmark:
            model_ids = []
            for i in range(num_models):
                model_data = {
                    'name': f'Large Dataset Model {i}',
                    'file_path': f'/path/to/large{i}.stl',
                    'file_size': 1024 + (i % 100) * 100,
                    'file_hash': f'large_hash_{i}',
                    'format': 'stl'
                }
                model_id = model_repository.create(model_data)
                model_ids.append(model_id)
        
        creation_time = benchmark.get_duration()
        creation_memory = benchmark.get_memory_delta_mb()
        
        print(f"Large dataset creation: {num_models} models in {creation_time:.2f}s, memory: {creation_memory:.1f}MB")
        
        # Test reading all models
        with PerformanceBenchmark("large_dataset_read") as benchmark:
            for model_id in model_ids:
                model = model_repository.read(model_id)
                assert model is not None
        
        read_time = benchmark.get_duration()
        read_memory = benchmark.get_memory_delta_mb()
        
        print(f"Large dataset read: {num_models} models in {read_time:.2f}s, memory: {read_memory:.1f}MB")
        
        # Performance should be reasonable
        avg_creation_time = creation_time / num_models
        avg_read_time = read_time / num_models
        
        assert avg_creation_time < 0.01, f"Average creation time {avg_creation_time:.4f}s, should be < 0.01s"
        assert avg_read_time < 0.005, f"Average read time {avg_read_time:.4f}s, should be < 0.005s"


class TestConcurrentPerformance:
    """Test concurrent operation performance."""

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

    @pytest.fixture
    def transaction_manager(self, temp_db):
        """Create TransactionManager instance for testing."""
        return TransactionManager(temp_db)

    def test_concurrent_read_performance(self, model_repository):
        """Test concurrent read performance."""
        # Create some models first
        model_ids = []
        for i in range(100):
            model_data = {
                'name': f'Concurrent Read Test {i}',
                'file_path': f'/path/to/concurrent_read{i}.stl',
                'file_size': 1024,
                'file_hash': f'concurrent_read_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
        
        def read_model(model_id):
            """Read a model."""
            model = model_repository.read(model_id)
            return model is not None
        
        # Test concurrent reads
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_model, model_id) for model_id in model_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = time.perf_counter() - start_time
        
        # All reads should succeed
        assert all(results), "All concurrent reads should succeed"
        
        # Concurrent reads should be faster than sequential
        sequential_start = time.perf_counter()
        for model_id in model_ids:
            model = model_repository.read(model_id)
            assert model is not None
        sequential_time = time.perf_counter() - sequential_start
        
        speedup = sequential_time / concurrent_time if concurrent_time > 0 else float('inf')
        assert speedup > 1.5, f"Concurrent reads should be faster, speedup: {speedup:.1f}x"
        
        print(f"Concurrent read performance: Sequential {sequential_time:.2f}s, Concurrent {concurrent_time:.2f}s, Speedup {speedup:.1f}x")

    def test_concurrent_write_performance(self, model_repository, transaction_manager):
        """Test concurrent write performance."""
        def create_model(index):
            """Create a model in a transaction."""
            try:
                with transaction_manager.transaction() as conn:
                    model_data = {
                        'name': f'Concurrent Write Test {index}',
                        'file_path': f'/path/to/concurrent_write{index}.stl',
                        'file_size': 1024,
                        'file_hash': f'concurrent_write_hash_{index}',
                        'format': 'stl'
                    }
                    model_id = model_repository.create(model_data)
                    conn.commit()
                    return model_id
            except Exception as e:
                return None
        
        # Test concurrent writes
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_model, i) for i in range(50)]
            model_ids = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = time.perf_counter() - start_time
        
        # Count successful creations
        successful_creations = len([mid for mid in model_ids if mid is not None])
        
        print(f"Concurrent write performance: {successful_creations}/50 models created in {concurrent_time:.2f}s")
        
        # Most writes should succeed (allowing for some contention)
        assert successful_creations >= 40, f"Expected at least 40 successful writes, got {successful_creations}"

    def test_mixed_concurrent_operations(self, model_repository, transaction_manager):
        """Test mixed concurrent read/write operations."""
        # Create initial models
        initial_model_ids = []
        for i in range(50):
            model_data = {
                'name': f'Initial Model {i}',
                'file_path': f'/path/to/initial{i}.stl',
                'file_size': 1024,
                'file_hash': f'initial_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            initial_model_ids.append(model_id)
        
        def read_operation(model_id):
            """Read operation."""
            model = model_repository.read(model_id)
            return model is not None
        
        def write_operation(index):
            """Write operation."""
            try:
                with transaction_manager.transaction() as conn:
                    model_data = {
                        'name': f'Mixed Write {index}',
                        'file_path': f'/path/to/mixed{index}.stl',
                        'file_size': 1024,
                        'file_hash': f'mixed_hash_{index}',
                        'format': 'obj'
                    }
                    model_id = model_repository.create(model_data)
                    conn.commit()
                    return model_id
            except Exception:
                return None
        
        # Mix of read and write operations
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # Submit read operations
            read_futures = [executor.submit(read_operation, model_id) for model_id in initial_model_ids[:25]]
            
            # Submit write operations
            write_futures = [executor.submit(write_operation, i) for i in range(25)]
            
            # Wait for all to complete
            read_results = [future.result() for future in concurrent.futures.as_completed(read_futures)]
            write_results = [future.result() for future in concurrent.futures.as_completed(write_futures)]
        
        concurrent_time = time.perf_counter() - start_time
        
        # Check results
        successful_reads = sum(read_results)
        successful_writes = len([mid for mid in write_results if mid is not None])
        
        print(f"Mixed concurrent operations: {successful_reads}/25 reads, {successful_writes}/25 writes in {concurrent_time:.2f}s")
        
        # Most operations should succeed
        assert successful_reads >= 20, f"Expected at least 20 successful reads, got {successful_reads}"
        assert successful_writes >= 15, f"Expected at least 15 successful writes, got {successful_writes}"


class TestLoadTesting:
    """Test database performance under load."""

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

    @pytest.fixture
    def cache_manager(self, temp_db):
        """Create DatabaseCacheManager instance for testing."""
        return DatabaseCacheManager(temp_db, memory_cache_mb=100, disk_cache_mb=500)

    def test_sustained_load_performance(self, model_repository, cache_manager):
        """Test performance under sustained load."""
        # Performance targets from requirements
        max_query_time = 0.1  # 100ms
        max_memory_increase = 200 * 1024 * 1024  # 200MB
        
        # Get baseline
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss
        
        # Simulate sustained load
        operations_per_second = 50
        test_duration = 10  # seconds
        total_operations = operations_per_second * test_duration
        
        start_time = time.time()
        operation_times = []
        
        for i in range(total_operations):
            operation_start = time.perf_counter()
            
            # Random operation type
            operation_type = random.choice(['create', 'read', 'update', 'delete', 'search'])
            
            if operation_type == 'create':
                model_data = {
                    'name': f'Load Test Model {i}',
                    'file_path': f'/path/to/load{i}.stl',
                    'file_size': 1024,
                    'file_hash': f'load_hash_{i}',
                    'format': 'stl'
                }
                model_id = model_repository.create(model_data)
                
                # Cache it
                cache_manager.cache_model_metadata(model_id, model_data)
                
            elif operation_type == 'read':
                if i > 0:
                    model_id = f'model_{random.randint(0, i-1)}'
                    model = model_repository.read(model_id)
                    
            elif operation_type == 'update' and i > 0:
                model_id = f'model_{random.randint(0, i-1)}'
                model_repository.update(model_id, {'name': f'Updated Load Test {i}'})
                
            elif operation_type == 'delete' and i > 0:
                model_id = f'model_{random.randint(0, i-1)}'
                model_repository.delete(model_id)
                
                # Invalidate cache
                cache_manager.invalidate_model_cache(model_id)
            
            operation_time = time.perf_counter() - operation_start
            operation_times.append(operation_time)
            
            # Check if we're meeting performance targets
            if operation_time > max_query_time:
                pytest.fail(f"Operation took {operation_time:.3f}s, exceeds target of {max_query_time}s")
            
            # Control operation rate
            elapsed = time.time() - start_time
            expected_time = i / operations_per_second
            if elapsed < expected_time:
                time.sleep(expected_time - elapsed)
        
        # Check final memory usage
        gc.collect()
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - baseline_memory
        
        assert memory_increase < max_memory_increase, f"Memory increase {memory_increase/(1024*1024):.1f}MB exceeds target"
        
        # Performance statistics
        avg_time = statistics.mean(operation_times)
        p95_time = statistics.quantiles(operation_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(operation_times, n=100)[98]  # 99th percentile
        
        print(f"Sustained load test results:")
        print(f"  Operations: {total_operations}")
        print(f"  Duration: {time.time() - start_time:.1f}s")
        print(f"  Avg time: {avg_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")
        print(f"  P99 time: {p99_time:.4f}s")
        print(f"  Memory increase: {memory_increase/(1024*1024):.1f}MB")
        
        # Performance assertions
        assert avg_time < 0.05, f"Average operation time {avg_time:.4f}s should be < 0.05s"
        assert p95_time < 0.1, f"95th percentile {p95_time:.4f}s should be < 0.1s"

    def test_cache_effectiveness_under_load(self, model_repository, cache_manager):
        """Test cache effectiveness under load."""
        # Create initial dataset
        model_ids = []
        for i in range(1000):
            model_data = {
                'name': f'Cache Load Test {i}',
                'file_path': f'/path/to/cache_load{i}.stl',
                'file_size': 1024,
                'file_hash': f'cache_load_hash_{i}',
                'format': 'stl'
            }
            model_id = model_repository.create(model_data)
            model_ids.append(model_id)
            
            # Cache every 10th model
            if i % 10 == 0:
                cache_manager.cache_model_metadata(model_id, model_data)
        
        # Measure cache hit rate under load
        cache_hits = 0
        cache_misses = 0
        total_requests = 10000
        
        start_time = time.perf_counter()
        
        for i in range(total_requests):
            # Access random models (some cached, some not)
            model_id = model_ids[random.randint(0, len(model_ids) - 1)]
            
            # Try cache first
            cached_model = cache_manager.get_model_metadata(model_id)
            if cached_model is not None:
                cache_hits += 1
            else:
                cache_misses += 1
                # Fall back to database
                model = model_repository.read(model_id)
        
        load_test_time = time.perf_counter() - start_time
        
        # Calculate cache hit rate
        total_requests_actual = cache_hits + cache_misses
        hit_rate = cache_hits / total_requests_actual if total_requests_actual > 0 else 0
        
        print(f"Cache effectiveness under load:")
        print(f"  Total requests: {total_requests_actual}")
        print(f"  Cache hits: {cache_hits}")
        print(f"  Cache misses: {cache_misses}")
        print(f"  Hit rate: {hit_rate:.2%}")
        print(f"  Test duration: {load_test_time:.2f}s")
        print(f"  Requests/second: {total_requests_actual/load_test_time:.0f}")
        
        # Cache should provide significant performance improvement
        assert hit_rate > 0.05, f"Cache hit rate {hit_rate:.2%} should be > 5%"
        assert load_test_time < 5.0, f"Load test took {load_test_time:.2f}s, should be < 5.0s"


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "--tb=short"])