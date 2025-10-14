"""
Unit tests for STEP parser.

This module tests the STEP parser functionality including parsing, validation,
and error handling.
"""

import unittest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.step_parser import STEPParser, STEPEntity, STEPCartesianPoint, STEPDirection
from core.data_structures import ModelFormat
from parsers.base_parser import ParseError


class TestSTEPParser(unittest.TestCase):
    """Test cases for STEP parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = STEPParser()
        self.test_files_dir = Path(__file__).parent / "sample_files"
    
    def test_parse_simple_step(self):
        """Test parsing a simple STEP file."""
        step_file = self.test_files_dir / "cube.step"
        
        if step_file.exists():
            model = self.parser.parse_file(step_file)
            
            # Check model properties
            self.assertEqual(model.format_type, ModelFormat.STEP)
            self.assertIsNotNone(model.header)
            self.assertGreater(len(model.triangles), 0)
            self.assertIsNotNone(model.stats)
            
            # Check stats
            self.assertGreater(model.stats.vertex_count, 0)
            self.assertGreater(model.stats.triangle_count, 0)
            self.assertEqual(model.stats.format_type, ModelFormat.STEP)
            self.assertGreater(model.stats.parsing_time_seconds, 0)
    
    def test_validate_valid_step(self):
        """Test validation of a valid STEP file."""
        step_file = self.test_files_dir / "cube.step"
        
        if step_file.exists():
            is_valid, error_msg = self.parser.validate_file(step_file)
            self.assertTrue(is_valid, f"Validation failed: {error_msg}")
            self.assertEqual(error_msg, "")
    
    def test_validate_invalid_step(self):
        """Test validation of an invalid STEP file."""
        # Create a temporary invalid file
        invalid_file = self.test_files_dir / "invalid.step"
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid STEP file")
        
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
        nonexistent_file = self.test_files_dir / "nonexistent.step"
        
        is_valid, error_msg = self.parser.validate_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error_msg)
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.parser.get_supported_extensions()
        self.assertIn('.step', extensions)
        self.assertIn('.stp', extensions)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.step"
        
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(nonexistent_file)
    
    def test_cancel_parsing(self):
        """Test cancelling parsing operation."""
        # This test would require a large file to properly test cancellation
        # For now, we just test that the method exists and can be called
        self.parser.cancel_parsing()
        self.parser.reset_cancel_state()
    
    def test_parse_step_with_entities(self):
        """Test parsing STEP file with entities."""
        step_file = self.test_files_dir / "cube.step"
        
        if step_file.exists():
            model = self.parser.parse_file(step_file)
            
            # Check that entities were loaded
            self.assertGreater(len(self.parser.entities), 0)
            
            # Check that cartesian points were loaded
            self.assertGreater(len(self.parser.cartesian_points), 0)


class TestSTEPEntity(unittest.TestCase):
    """Test cases for STEP entity class."""
    
    def test_entity_creation(self):
        """Test creating a STEP entity."""
        entity = STEPEntity(
            id=1,
            type="CARTESIAN_POINT",
            parameters=[(0.0, 0.0, 0.0)]
        )
        
        self.assertEqual(entity.id, 1)
        self.assertEqual(entity.type, "CARTESIAN_POINT")
        self.assertEqual(entity.parameters, [(0.0, 0.0, 0.0)])


class TestSTEPCartesianPoint(unittest.TestCase):
    """Test cases for STEP cartesian point class."""
    
    def test_cartesian_point_creation(self):
        """Test creating a STEP cartesian point."""
        point = STEPCartesianPoint(
            id=1,
            coordinates=(0.0, 0.0, 0.0)
        )
        
        self.assertEqual(point.id, 1)
        self.assertEqual(point.coordinates, (0.0, 0.0, 0.0))


class TestSTEPDirection(unittest.TestCase):
    """Test cases for STEP direction class."""
    
    def test_direction_creation(self):
        """Test creating a STEP direction."""
        direction = STEPDirection(
            id=1,
            direction_ratios=(1.0, 0.0, 0.0)
        )
        
        self.assertEqual(direction.id, 1)
        self.assertEqual(direction.direction_ratios, (1.0, 0.0, 0.0))


if __name__ == '__main__':
    unittest.main()