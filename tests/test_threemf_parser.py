"""
Unit tests for 3MF parser.

This module tests the 3MF parser functionality including parsing, validation,
and error handling.
"""

import unittest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.threemf_parser import ThreeMFParser, ThreeMFObject, ThreeMFComponent, ThreeMFBuildItem
from core.data_structures import ModelFormat
from parsers.base_parser import ParseError


class TestThreeMFParser(unittest.TestCase):
    """Test cases for 3MF parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ThreeMFParser()
        self.test_files_dir = Path(__file__).parent / "sample_files"
    
    def test_parse_simple_3mf(self):
        """Test parsing a simple 3MF file."""
        threemf_file = self.test_files_dir / "cube.3mf"
        
        if threemf_file.exists():
            model = self.parser.parse_file(threemf_file)
            
            # Check model properties
            self.assertEqual(model.format_type, ModelFormat.THREE_MF)
            self.assertIsNotNone(model.header)
            self.assertGreater(len(model.triangles), 0)
            self.assertIsNotNone(model.stats)
            
            # Check stats
            self.assertGreater(model.stats.vertex_count, 0)
            self.assertGreater(model.stats.triangle_count, 0)
            self.assertEqual(model.stats.format_type, ModelFormat.THREE_MF)
            self.assertGreater(model.stats.parsing_time_seconds, 0)
    
    def test_validate_valid_3mf(self):
        """Test validation of a valid 3MF file."""
        threemf_file = self.test_files_dir / "cube.3mf"
        
        if threemf_file.exists():
            is_valid, error_msg = self.parser.validate_file(threemf_file)
            self.assertTrue(is_valid, f"Validation failed: {error_msg}")
            self.assertEqual(error_msg, "")
    
    def test_validate_invalid_3mf(self):
        """Test validation of an invalid 3MF file."""
        # Create a temporary invalid file
        invalid_file = self.test_files_dir / "invalid.3mf"
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid 3MF file")
        
        try:
            is_valid, error_msg = self.parser.validate_file(invalid_file)
            self.assertFalse(is_valid)
            self.assertNotEqual(error_msg, "")
        finally:
            # Clean up
            if invalid_file.exists():
                invalid_file.unlink()
    
    def test_validate_nonexistent_file(self):
        """Test validation of a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.3mf"
        
        is_valid, error_msg = self.parser.validate_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error_msg)
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.parser.get_supported_extensions()
        self.assertIn('.3mf', extensions)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.3mf"
        
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(nonexistent_file)
    
    def test_cancel_parsing(self):
        """Test cancelling parsing operation."""
        # This test would require a large file to properly test cancellation
        # For now, we just test that the method exists and can be called
        self.parser.cancel_parsing()
        self.parser.reset_cancel_state()
    
    def test_parse_3mf_with_components(self):
        """Test parsing 3MF file with components."""
        threemf_file = self.test_files_dir / "cube.3mf"
        
        if threemf_file.exists():
            model = self.parser.parse_file(threemf_file)
            
            # Check that objects were loaded
            self.assertGreater(len(self.parser.objects), 0)
            
            # Check that build items were loaded
            self.assertGreater(len(self.parser.build_items), 0)


class TestThreeMFObject(unittest.TestCase):
    """Test cases for 3MF object class."""
    
    def test_object_creation(self):
        """Test creating a 3MF object."""
        object = ThreeMFObject(
            object_id=1,
            type="model",
            vertices=[],
            triangles=[],
            components=[],
            name="test_object"
        )
        
        self.assertEqual(object.object_id, 1)
        self.assertEqual(object.type, "model")
        self.assertEqual(object.name, "test_object")
        self.assertIsInstance(object.vertices, list)
        self.assertIsInstance(object.triangles, list)
        self.assertIsInstance(object.components, list)


class TestThreeMFComponent(unittest.TestCase):
    """Test cases for 3MF component class."""
    
    def test_component_creation(self):
        """Test creating a 3MF component."""
        transform = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]
        
        component = ThreeMFComponent(
            object_id=1,
            transform=transform
        )
        
        self.assertEqual(component.object_id, 1)
        self.assertEqual(component.transform, transform)


class TestThreeMFBuildItem(unittest.TestCase):
    """Test cases for 3MF build item class."""
    
    def test_build_item_creation(self):
        """Test creating a 3MF build item."""
        transform = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]
        
        build_item = ThreeMFBuildItem(
            object_id=1,
            transform=transform
        )
        
        self.assertEqual(build_item.object_id, 1)
        self.assertEqual(build_item.transform, transform)


if __name__ == '__main__':
    unittest.main()