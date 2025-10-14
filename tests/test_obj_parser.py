"""
Unit tests for OBJ parser.

This module tests the OBJ parser functionality including parsing, validation,
and error handling.
"""

import unittest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.obj_parser import OBJParser, OBJMaterial, OBJFace
from core.data_structures import ModelFormat
from parsers.base_parser import ParseError


class TestOBJParser(unittest.TestCase):
    """Test cases for OBJ parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = OBJParser()
        self.test_files_dir = Path(__file__).parent / "sample_files"
    
    def test_parse_simple_obj(self):
        """Test parsing a simple OBJ file."""
        obj_file = self.test_files_dir / "cube.obj"
        
        if obj_file.exists():
            model = self.parser.parse_file(obj_file)
            
            # Check model properties
            self.assertEqual(model.format_type, ModelFormat.OBJ)
            self.assertIsNotNone(model.header)
            self.assertGreater(len(model.triangles), 0)
            self.assertIsNotNone(model.stats)
            
            # Check stats
            self.assertGreater(model.stats.vertex_count, 0)
            self.assertGreater(model.stats.triangle_count, 0)
            self.assertEqual(model.stats.format_type, ModelFormat.OBJ)
            self.assertGreater(model.stats.parsing_time_seconds, 0)
    
    def test_validate_valid_obj(self):
        """Test validation of a valid OBJ file."""
        obj_file = self.test_files_dir / "cube.obj"
        
        if obj_file.exists():
            is_valid, error_msg = self.parser.validate_file(obj_file)
            self.assertTrue(is_valid, f"Validation failed: {error_msg}")
            self.assertEqual(error_msg, "")
    
    def test_validate_invalid_obj(self):
        """Test validation of an invalid OBJ file."""
        # Create a temporary invalid file
        invalid_file = self.test_files_dir / "invalid.obj"
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid OBJ file")
        
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
        nonexistent_file = self.test_files_dir / "nonexistent.obj"
        
        is_valid, error_msg = self.parser.validate_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error_msg)
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.parser.get_supported_extensions()
        self.assertIn('.obj', extensions)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.obj"
        
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(nonexistent_file)
    
    def test_cancel_parsing(self):
        """Test cancelling parsing operation."""
        # This test would require a large file to properly test cancellation
        # For now, we just test that the method exists and can be called
        self.parser.cancel_parsing()
        self.parser.reset_cancel_state()
    
    def test_parse_obj_with_mtl(self):
        """Test parsing OBJ file with MTL material."""
        obj_file = self.test_files_dir / "cube.obj"
        mtl_file = self.test_files_dir / "cube.mtl"
        
        if obj_file.exists() and mtl_file.exists():
            model = self.parser.parse_file(obj_file)
            
            # Check that materials were loaded
            self.assertGreater(len(self.parser.materials), 0)
            
            # Check material properties
            material = self.parser.materials.get("cube_material")
            if material:
                self.assertIsInstance(material, OBJMaterial)
                self.assertEqual(material.name, "cube_material")


class TestOBJMaterial(unittest.TestCase):
    """Test cases for OBJ material class."""
    
    def test_material_creation(self):
        """Test creating an OBJ material."""
        material = OBJMaterial(
            name="test_material",
            ambient=(0.2, 0.2, 0.2),
            diffuse=(0.8, 0.8, 0.8),
            specular=(1.0, 1.0, 1.0),
            specular_exponent=32.0
        )
        
        self.assertEqual(material.name, "test_material")
        self.assertEqual(material.ambient, (0.2, 0.2, 0.2))
        self.assertEqual(material.diffuse, (0.8, 0.8, 0.8))
        self.assertEqual(material.specular, (1.0, 1.0, 1.0))
        self.assertEqual(material.specular_exponent, 32.0)


class TestOBJFace(unittest.TestCase):
    """Test cases for OBJ face class."""
    
    def test_face_creation(self):
        """Test creating an OBJ face."""
        face = OBJFace(
            vertex_indices=[1, 2, 3],
            texture_indices=[1, 2, 3],
            normal_indices=[1, 2, 3],
            material_name="test_material"
        )
        
        self.assertEqual(face.vertex_indices, [1, 2, 3])
        self.assertEqual(face.texture_indices, [1, 2, 3])
        self.assertEqual(face.normal_indices, [1, 2, 3])
        self.assertEqual(face.material_name, "test_material")


if __name__ == '__main__':
    unittest.main()