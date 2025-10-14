"""
Unit tests for STL parser module.

This module contains comprehensive tests for the STL parser including:
- Format detection tests
- Binary STL parsing tests
- ASCII STL parsing tests
- Error handling tests
- Performance tests
- Memory leak tests
"""

import os
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import psutil
import gc

from src.parsers.stl_parser import (
    STLParser, STLFormat, Vector3D, Triangle, ModelStats, STLModel,
    STLParseError, STLProgressCallback
)


class TestVector3D(unittest.TestCase):
    """Test cases for Vector3D class."""
    
    def test_vector_creation(self):
        """Test creating a 3D vector."""
        v = Vector3D(1.0, 2.0, 3.0)
        self.assertEqual(v.x, 1.0)
        self.assertEqual(v.y, 2.0)
        self.assertEqual(v.z, 3.0)
    
    def test_vector_iteration(self):
        """Test vector iteration."""
        v = Vector3D(1.0, 2.0, 3.0)
        self.assertEqual(list(v), [1.0, 2.0, 3.0])
    
    def test_vector_indexing(self):
        """Test vector indexing."""
        v = Vector3D(1.0, 2.0, 3.0)
        self.assertEqual(v[0], 1.0)
        self.assertEqual(v[1], 2.0)
        self.assertEqual(v[2], 3.0)


class TestTriangle(unittest.TestCase):
    """Test cases for Triangle class."""
    
    def test_triangle_creation(self):
        """Test creating a triangle."""
        normal = Vector3D(0.0, 0.0, 1.0)
        v1 = Vector3D(0.0, 0.0, 0.0)
        v2 = Vector3D(1.0, 0.0, 0.0)
        v3 = Vector3D(0.0, 1.0, 0.0)
        
        triangle = Triangle(normal, v1, v2, v3)
        self.assertEqual(triangle.normal, normal)
        self.assertEqual(triangle.vertex1, v1)
        self.assertEqual(triangle.vertex2, v2)
        self.assertEqual(triangle.vertex3, v3)
    
    def test_get_vertices(self):
        """Test getting vertices from triangle."""
        normal = Vector3D(0.0, 0.0, 1.0)
        v1 = Vector3D(0.0, 0.0, 0.0)
        v2 = Vector3D(1.0, 0.0, 0.0)
        v3 = Vector3D(0.0, 1.0, 0.0)
        
        triangle = Triangle(normal, v1, v2, v3)
        vertices = triangle.get_vertices()
        self.assertEqual(len(vertices), 3)
        self.assertEqual(vertices[0], v1)
        self.assertEqual(vertices[1], v2)
        self.assertEqual(vertices[2], v3)


class TestModelStats(unittest.TestCase):
    """Test cases for ModelStats class."""
    
    def test_model_stats_creation(self):
        """Test creating model statistics."""
        min_bounds = Vector3D(0.0, 0.0, 0.0)
        max_bounds = Vector3D(1.0, 1.0, 1.0)
        
        stats = ModelStats(
            vertex_count=3,
            triangle_count=1,
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=100,
            format_type=STLFormat.BINARY,
            parsing_time_seconds=0.1
        )
        
        self.assertEqual(stats.vertex_count, 3)
        self.assertEqual(stats.triangle_count, 1)
        self.assertEqual(stats.min_bounds, min_bounds)
        self.assertEqual(stats.max_bounds, max_bounds)
        self.assertEqual(stats.file_size_bytes, 100)
        self.assertEqual(stats.format_type, STLFormat.BINARY)
        self.assertEqual(stats.parsing_time_seconds, 0.1)
    
    def test_get_dimensions(self):
        """Test getting model dimensions."""
        min_bounds = Vector3D(0.0, 0.0, 0.0)
        max_bounds = Vector3D(2.0, 3.0, 4.0)
        
        stats = ModelStats(
            vertex_count=3,
            triangle_count=1,
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=100,
            format_type=STLFormat.BINARY,
            parsing_time_seconds=0.1
        )
        
        dimensions = stats.get_dimensions()
        self.assertEqual(dimensions, (2.0, 3.0, 4.0))


class TestSTLModel(unittest.TestCase):
    """Test cases for STLModel class."""
    
    def test_model_creation(self):
        """Test creating an STL model."""
        header = "Test Model"
        normal = Vector3D(0.0, 0.0, 1.0)
        v1 = Vector3D(0.0, 0.0, 0.0)
        v2 = Vector3D(1.0, 0.0, 0.0)
        v3 = Vector3D(0.0, 1.0, 0.0)
        triangle = Triangle(normal, v1, v2, v3)
        
        min_bounds = Vector3D(0.0, 0.0, 0.0)
        max_bounds = Vector3D(1.0, 1.0, 1.0)
        stats = ModelStats(
            vertex_count=3,
            triangle_count=1,
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=100,
            format_type=STLFormat.BINARY,
            parsing_time_seconds=0.1
        )
        
        model = STLModel(header=header, triangles=[triangle], stats=stats)
        self.assertEqual(model.header, header)
        self.assertEqual(len(model.triangles), 1)
        self.assertEqual(model.stats, stats)
    
    def test_get_vertices(self):
        """Test getting all vertices from model."""
        header = "Test Model"
        normal = Vector3D(0.0, 0.0, 1.0)
        v1 = Vector3D(0.0, 0.0, 0.0)
        v2 = Vector3D(1.0, 0.0, 0.0)
        v3 = Vector3D(0.0, 1.0, 0.0)
        triangle = Triangle(normal, v1, v2, v3)
        
        min_bounds = Vector3D(0.0, 0.0, 0.0)
        max_bounds = Vector3D(1.0, 1.0, 1.0)
        stats = ModelStats(
            vertex_count=3,
            triangle_count=1,
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=100,
            format_type=STLFormat.BINARY,
            parsing_time_seconds=0.1
        )
        
        model = STLModel(header=header, triangles=[triangle], stats=stats)
        vertices = model.get_vertices()
        self.assertEqual(len(vertices), 3)
        self.assertEqual(vertices[0], v1)
        self.assertEqual(vertices[1], v2)
        self.assertEqual(vertices[2], v3)


class TestSTLProgressCallback(unittest.TestCase):
    """Test cases for STLProgressCallback class."""
    
    def test_callback_creation(self):
        """Test creating progress callback."""
        callback = STLProgressCallback()
        self.assertIsNone(callback.callback_func)
    
    def test_callback_with_function(self):
        """Test callback with function."""
        mock_func = MagicMock()
        callback = STLProgressCallback(mock_func)
        self.assertEqual(callback.callback_func, mock_func)
    
    def test_report_progress(self):
        """Test reporting progress."""
        mock_func = MagicMock()
        callback = STLProgressCallback(mock_func)
        
        # First call should trigger callback
        callback.report(50.0, "Test message")
        mock_func.assert_called_once_with(50.0, "Test message")
        
        # Reset mock
        mock_func.reset_mock()
        
        # Immediate second call should not trigger due to time limit
        callback.report(60.0, "Test message 2")
        mock_func.assert_not_called()


class TestSTLParser(unittest.TestCase):
    """Test cases for STLParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = STLParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_binary_stl_file(self, filename, triangle_count=1, header=b"Binary STL Test"):
        """Create a binary STL file for testing."""
        filepath = Path(self.temp_dir) / filename
        
        with open(filepath, 'wb') as f:
            # Write header (80 bytes)
            f.write(header.ljust(80, b'\x00'))
            
            # Write triangle count (4 bytes)
            f.write(struct.pack('<I', triangle_count))
            
            # Write triangles
            for i in range(triangle_count):
                # Normal vector (3 floats)
                f.write(struct.pack('<fff', 0.0, 0.0, 1.0))
                
                # Vertex 1 (3 floats)
                f.write(struct.pack('<fff', i * 1.0, 0.0, 0.0))
                
                # Vertex 2 (3 floats)
                f.write(struct.pack('<fff', i * 1.0 + 1.0, 0.0, 0.0))
                
                # Vertex 3 (3 floats)
                f.write(struct.pack('<fff', i * 1.0, 1.0, 0.0))
                
                # Attribute byte count (2 bytes)
                f.write(struct.pack('<H', 0))
        
        return filepath
    
    def create_ascii_stl_file(self, filename, triangle_count=1):
        """Create an ASCII STL file for testing."""
        filepath = Path(self.temp_dir) / filename
        
        with open(filepath, 'w') as f:
            f.write("solid ASCII STL Test\n")
            
            for i in range(triangle_count):
                f.write(f"  facet normal 0.0 0.0 1.0\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {i * 1.0} 0.0 0.0\n")
                f.write(f"      vertex {i * 1.0 + 1.0} 0.0 0.0\n")
                f.write(f"      vertex {i * 1.0} 1.0 0.0\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            
            f.write("endsolid ASCII STL Test\n")
        
        return filepath
    
    def test_detect_binary_format(self):
        """Test detecting binary STL format."""
        filepath = self.create_binary_stl_file("test_binary.stl")
        format_type = self.parser._detect_format(filepath)
        self.assertEqual(format_type, STLFormat.BINARY)
    
    def test_detect_ascii_format(self):
        """Test detecting ASCII STL format."""
        filepath = self.create_ascii_stl_file("test_ascii.stl")
        format_type = self.parser._detect_format(filepath)
        self.assertEqual(format_type, STLFormat.ASCII)
    
    def test_detect_unknown_format(self):
        """Test detecting unknown STL format."""
        filepath = Path(self.temp_dir) / "invalid.stl"
        with open(filepath, 'w') as f:
            f.write("This is not an STL file\n")
        
        format_type = self.parser._detect_format(filepath)
        self.assertEqual(format_type, STLFormat.UNKNOWN)
    
    def test_parse_binary_stl(self):
        """Test parsing binary STL file."""
        filepath = self.create_binary_stl_file("test_binary.stl")
        model = self.parser.parse_file(filepath)
        
        self.assertIsInstance(model, STLModel)
        self.assertEqual(model.stats.triangle_count, 1)
        self.assertEqual(model.stats.vertex_count, 3)
        self.assertEqual(model.stats.format_type, STLFormat.BINARY)
        self.assertEqual(len(model.triangles), 1)
        
        triangle = model.triangles[0]
        self.assertEqual(triangle.normal.x, 0.0)
        self.assertEqual(triangle.normal.y, 0.0)
        self.assertEqual(triangle.normal.z, 1.0)
    
    def test_parse_ascii_stl(self):
        """Test parsing ASCII STL file."""
        filepath = self.create_ascii_stl_file("test_ascii.stl")
        model = self.parser.parse_file(filepath)
        
        self.assertIsInstance(model, STLModel)
        self.assertEqual(model.stats.triangle_count, 1)
        self.assertEqual(model.stats.vertex_count, 3)
        self.assertEqual(model.stats.format_type, STLFormat.ASCII)
        self.assertEqual(len(model.triangles), 1)
        
        triangle = model.triangles[0]
        self.assertEqual(triangle.normal.x, 0.0)
        self.assertEqual(triangle.normal.y, 0.0)
        self.assertEqual(triangle.normal.z, 1.0)
    
    def test_parse_multiple_triangles(self):
        """Test parsing STL file with multiple triangles."""
        filepath = self.create_binary_stl_file("test_multi.stl", triangle_count=10)
        model = self.parser.parse_file(filepath)
        
        self.assertEqual(model.stats.triangle_count, 10)
        self.assertEqual(model.stats.vertex_count, 30)
        self.assertEqual(len(model.triangles), 10)
    
    def test_parse_large_binary_stl(self):
        """Test parsing large binary STL file."""
        # Create a file with 10000 triangles
        filepath = self.create_binary_stl_file("test_large.stl", triangle_count=10000)
        
        # Test with progress callback
        progress_values = []
        def progress_callback(percent, message):
            progress_values.append(percent)
        
        callback = STLProgressCallback(progress_callback)
        start_time = time.time()
        model = self.parser.parse_file(filepath, callback)
        parsing_time = time.time() - start_time
        
        self.assertEqual(model.stats.triangle_count, 10000)
        self.assertEqual(model.stats.vertex_count, 30000)
        self.assertGreater(len(progress_values), 0)
        self.assertLess(parsing_time, 5.0)  # Should parse quickly
    
    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        filepath = Path(self.temp_dir) / "nonexistent.stl"
        
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(filepath)
    
    def test_parse_empty_file(self):
        """Test parsing empty file."""
        filepath = Path(self.temp_dir) / "empty.stl"
        with open(filepath, 'w') as f:
            pass  # Create empty file
        
        with self.assertRaises(STLParseError):
            self.parser.parse_file(filepath)
    
    def test_cancel_parsing(self):
        """Test cancelling parsing operation."""
        # Create a file with many triangles
        filepath = self.create_binary_stl_file("test_cancel.stl", triangle_count=10000)
        
        # Set cancel flag before parsing
        self.parser._cancel_parsing = True
        
        with self.assertRaises(STLParseError) as context:
            self.parser.parse_file(filepath)
        
        self.assertIn("cancelled", str(context.exception).lower())
        
        # Reset cancel state
        self.parser.reset_cancel_state()
    
    def test_validate_file_binary(self):
        """Test validating binary STL file."""
        filepath = self.create_binary_stl_file("test_valid_binary.stl")
        is_valid, error = self.parser.validate_file(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_validate_file_ascii(self):
        """Test validating ASCII STL file."""
        filepath = self.create_ascii_stl_file("test_valid_ascii.stl")
        is_valid, error = self.parser.validate_file(filepath)
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_validate_invalid_file(self):
        """Test validating invalid STL file."""
        filepath = Path(self.temp_dir) / "invalid.stl"
        with open(filepath, 'w') as f:
            f.write("This is not an STL file\n")
        
        is_valid, error = self.parser.validate_file(filepath)
        
        self.assertFalse(is_valid)
        self.assertNotEqual(error, "")
    
    def test_model_bounds_calculation(self):
        """Test model bounds calculation."""
        # Create a model with known bounds
        filepath = self.create_binary_stl_file("test_bounds.stl", triangle_count=2)
        
        # Create a custom file with specific bounds
        with open(filepath, 'wb') as f:
            # Write header (80 bytes)
            header = b"Custom bounds test"
            f.write(header.ljust(80, b'\x00'))
            
            # Write triangle count (4 bytes)
            f.write(struct.pack('<I', 2))
            
            # First triangle at origin
            # Normal vector
            f.write(struct.pack('<fff', 0.0, 0.0, 1.0))
            # Vertex 1
            f.write(struct.pack('<fff', 0.0, 0.0, 0.0))
            # Vertex 2
            f.write(struct.pack('<fff', 1.0, 0.0, 0.0))
            # Vertex 3
            f.write(struct.pack('<fff', 0.0, 1.0, 0.0))
            # Attribute byte count
            f.write(struct.pack('<H', 0))
            
            # Second triangle at (10, 10, 10)
            # Normal vector
            f.write(struct.pack('<fff', 0.0, 0.0, 1.0))
            # Vertex 1
            f.write(struct.pack('<fff', 10.0, 10.0, 10.0))
            # Vertex 2
            f.write(struct.pack('<fff', 11.0, 10.0, 10.0))
            # Vertex 3
            f.write(struct.pack('<fff', 10.0, 11.0, 10.0))
            # Attribute byte count
            f.write(struct.pack('<H', 0))
        
        model = self.parser.parse_file(filepath)
        
        # Check bounds
        self.assertEqual(model.stats.min_bounds.x, 0.0)
        self.assertEqual(model.stats.min_bounds.y, 0.0)
        self.assertEqual(model.stats.min_bounds.z, 0.0)
        self.assertEqual(model.stats.max_bounds.x, 11.0)
        self.assertEqual(model.stats.max_bounds.y, 11.0)
        self.assertEqual(model.stats.max_bounds.z, 10.0)
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during repeated parsing."""
        filepath = self.create_binary_stl_file("test_memory.stl", triangle_count=1000)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Parse file multiple times
        for _ in range(20):
            model = self.parser.parse_file(filepath)
            del model  # Explicitly delete model
            gc.collect()  # Force garbage collection
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 10MB)
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                       f"Memory increased by {memory_increase / 1024 / 1024:.2f} MB")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for different file sizes."""
        # Small file (less than 100MB equivalent)
        small_file = self.create_binary_stl_file("test_small.stl", triangle_count=1000)
        start_time = time.time()
        model = self.parser.parse_file(small_file)
        parsing_time = time.time() - start_time
        self.assertLess(parsing_time, 1.0, "Small file should parse in under 1 second")
        
        # Medium file (100-500MB equivalent in triangles)
        medium_file = self.create_binary_stl_file("test_medium.stl", triangle_count=100000)
        start_time = time.time()
        model = self.parser.parse_file(medium_file)
        parsing_time = time.time() - start_time
        self.assertLess(parsing_time, 5.0, "Medium file should parse in under 5 seconds")
    
    def test_corrupted_binary_file(self):
        """Test handling of corrupted binary STL file."""
        filepath = Path(self.temp_dir) / "corrupted.stl"
        
        with open(filepath, 'wb') as f:
            # Write valid header
            f.write(b"Corrupted STL".ljust(80, b'\x00'))
            
            # Write invalid triangle count (too large)
            f.write(struct.pack('<I', 999999999))
            
            # Write incomplete triangle data
            f.write(b"\x00" * 100)  # Incomplete triangle
        
        with self.assertRaises(STLParseError):
            self.parser.parse_file(filepath)
    
    def test_corrupted_ascii_file(self):
        """Test handling of corrupted ASCII STL file."""
        filepath = Path(self.temp_dir) / "corrupted_ascii.stl"
        
        with open(filepath, 'w') as f:
            f.write("solid Corrupted ASCII\n")
            f.write("  facet normal 0.0 0.0 1.0\n")
            f.write("    outer loop\n")
            f.write("      vertex 0.0 0.0 0.0\n")
            f.write("      vertex 1.0 0.0 0.0\n")
            # Missing third vertex and endloop/endfacet
        
        with self.assertRaises(STLParseError):
            self.parser.parse_file(filepath)


if __name__ == '__main__':
    unittest.main()