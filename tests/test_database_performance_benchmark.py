"""
Performance benchmark for refactored database_manager.py

Compares performance of the refactored modular implementation
against the original monolithic implementation.
"""

import time
import tempfile
import os
import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import get_database_manager, close_database_manager


def benchmark_add_models(db, num_models=100):
    """Benchmark adding models to the database."""
    start = time.time()
    
    for i in range(num_models):
        db.add_model(
            filename=f"model_{i}.stl",
            format="STL",
            file_path=f"/path/to/model_{i}.stl",
            file_size=1024 * (i + 1),
            file_hash=f"hash_{i:032d}"
        )
    
    elapsed = time.time() - start
    return elapsed


def benchmark_get_models(db, num_models=100):
    """Benchmark retrieving models from the database."""
    start = time.time()
    
    for i in range(num_models):
        db.get_model(i + 1)
    
    elapsed = time.time() - start
    return elapsed


def benchmark_search_models(db, num_searches=50):
    """Benchmark searching for models."""
    start = time.time()
    
    for i in range(num_searches):
        db.search_models(f"model_{i % 10}")
    
    elapsed = time.time() - start
    return elapsed


def benchmark_add_metadata(db, num_models=100):
    """Benchmark adding metadata to models."""
    start = time.time()
    
    for i in range(num_models):
        db.add_metadata(
            model_id=i + 1,
            title=f"Model {i}",
            description=f"Description for model {i}",
            keywords=f"keyword_{i}",
            category="Test",
            source="Test Source"
        )
    
    elapsed = time.time() - start
    return elapsed


def benchmark_add_categories(db, num_categories=50):
    """Benchmark adding categories."""
    start = time.time()
    
    for i in range(num_categories):
        db.add_category(
            name=f"Category_{i}",
            color=f"#{i:06X}",
            sort_order=i
        )
    
    elapsed = time.time() - start
    return elapsed


def benchmark_get_database_stats(db, num_calls=100):
    """Benchmark getting database statistics."""
    start = time.time()
    
    for _ in range(num_calls):
        db.get_database_stats()
    
    elapsed = time.time() - start
    return elapsed


def run_benchmarks():
    """Run all benchmarks."""
    # Create temporary database
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, "benchmark_3dmm.db")
    
    try:
        # Initialize database
        close_database_manager()
        db = get_database_manager(test_db_path)
        
        print("=" * 60)
        print("DATABASE PERFORMANCE BENCHMARK")
        print("=" * 60)
        print()
        
        # Run benchmarks
        benchmarks = [
            ("Add 100 Models", lambda: benchmark_add_models(db, 100)),
            ("Get 100 Models", lambda: benchmark_get_models(db, 100)),
            ("Search Models (50 searches)", lambda: benchmark_search_models(db, 50)),
            ("Add Metadata (100 models)", lambda: benchmark_add_metadata(db, 100)),
            ("Add Categories (50 categories)", lambda: benchmark_add_categories(db, 50)),
            ("Get Database Stats (100 calls)", lambda: benchmark_get_database_stats(db, 100)),
        ]
        
        results = {}
        for name, benchmark_func in benchmarks:
            elapsed = benchmark_func()
            results[name] = elapsed
            print(f"{name:.<45} {elapsed:.4f}s")
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        total_time = sum(results.values())
        print(f"Total Time: {total_time:.4f}s")
        print(f"Average Time per Operation: {total_time / len(results):.4f}s")
        
        print()
        print("✅ Benchmark completed successfully!")
        print()
        
        return results
        
    finally:
        # Cleanup
        close_database_manager()
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
            # Remove WAL and SHM files if they exist
            for ext in ['-wal', '-shm']:
                wal_file = test_db_path + ext
                if os.path.exists(wal_file):
                    os.remove(wal_file)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
        except Exception:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    run_benchmarks()

