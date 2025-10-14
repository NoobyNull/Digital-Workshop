"""
Unit tests for format detector.

This module tests the format detector functionality including format detection
and validation.
"""

import unittest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.format_detector import FormatDetector
from core.data_structures import ModelFormat


class TestFormatDetector(unittest.TestCase):
    """Test cases for format detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = FormatDetector()
        self.test_files_dir = Path(__file__).parent / "sample_files"
    
    def test_detect_stl_format(self):
        """Test detecting STL format."""
        stl_file = self.test_files_dir / "cube_ascii.stl"
        
        if stl_file.exists():
            format_type = self.detector.detect_format(stl_file)
            self.assertEqual(format_type, ModelFormat.STL)
    
    def test_detect_obj_format(self):
        """Test detecting OBJ format."""
        obj_file = self.test_files_dir / "cube.obj"
        
        if obj_file.exists():
            format_type = self.detector.detect_format(obj_file)
            self.assertEqual(format_type, ModelFormat.OBJ)
    
    def test_detect_3mf_format(self):
        """Test detecting 3MF format."""
        threemf_file = self.test_files_dir / "cube.3mf"
        
        if threemf_file.exists():
            format_type = self.detector.detect_format(threemf_file)
            self.assertEqual(format_type, ModelFormat.THREE_MF)
    
    def test_detect_step_format(self):
        """Test detecting STEP format."""
        step_file = self.test_files_dir / "cube.step"
        
        if step_file.exists():
            format_type = self.detector.detect_format(step_file)
            self.assertEqual(format_type, ModelFormat.STEP)
    
    def test_detect_unknown_format(self):
        """Test detecting unknown format."""
        # Create a temporary file with unknown format
        unknown_file = self.test_files_dir / "unknown.xyz"
        with open(unknown_file, 'w') as f:
            f.write("This is an unknown file format")
        
        try:
            format_type = self.detector.detect_format(unknown_file)
            self.assertEqual(format_type, ModelFormat.UNKNOWN)
        finally:
            # Clean up
            if unknown_file.exists():
                unknown_file.unlink()
    
    def test_detect_nonexistent_file(self):
        """Test detecting format of a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.stl"
        
        with self.assertRaises(FileNotFoundError):
            self.detector.detect_format(nonexistent_file)
    
    def test_is_supported_format(self):
        """Test checking if format is supported."""
        # Test supported format
        stl_file = self.test_files_dir / "cube_ascii.stl"
        if stl_file.exists():
            is_supported = self.detector.is_supported_format(stl_file)
            self.assertTrue(is_supported)
        
        # Test unsupported format
        unknown_file = self.test_files_dir / "unknown.xyz"
        with open(unknown_file, 'w') as f:
            f.write("This is an unknown file format")
        
        try:
            is_supported = self.detector.is_supported_format(unknown_file)
            self.assertFalse(is_supported)
        finally:
            # Clean up
            if unknown_file.exists():
                unknown_file.unlink()
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.detector.get_supported_extensions()
        
        # Check that all expected extensions are present
        self.assertIn('.stl', extensions)
        self.assertIn('.obj', extensions)
        self.assertIn('.3mf', extensions)
        self.assertIn('.step', extensions)
        self.assertIn('.stp', extensions)
    
    def test_validate_valid_file(self):
        """Test validation of a valid file."""
        stl_file = self.test_files_dir / "cube_ascii.stl"
        
        if stl_file.exists():
            is_valid, error_msg = self.detector.validate_file(stl_file)
            self.assertTrue(is_valid, f"Validation failed: {error_msg}")
            self.assertEqual(error_msg, "")
    
    def test_validate_invalid_file(self):
        """Test validation of an invalid file."""
        # Create a temporary invalid file
        invalid_file = self.test_files_dir / "invalid.xyz"
        with open(invalid_file, 'w') as f:
            f.write("This is an invalid file")
        
        try:
            is_valid, error_msg = self.detector.validate_file(invalid_file)
            self.assertFalse(is_valid)
            self.assertNotEqual(error_msg, "")
        finally:
            # Clean up
            if invalid_file.exists():
                invalid_file.unlink()
    
    def test_validate_nonexistent_file(self):
        """Test validation of a non-existent file."""
        nonexistent_file = self.test_files_dir / "nonexistent.stl"
        
        is_valid, error_msg = self.detector.validate_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error_msg)
    
    def test_validate_empty_file(self):
        """Test validation of an empty file."""
        empty_file = self.test_files_dir / "empty.stl"
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        try:
            is_valid, error_msg = self.detector.validate_file(empty_file)
            self.assertFalse(is_valid)
            self.assertIn("empty", error_msg.lower())
        finally:
            # Clean up
            if empty_file.exists():
                empty_file.unlink()
    
    def test_detect_by_extension(self):
        """Test format detection by extension."""
        # Test STL extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.stl")),
            ModelFormat.STL
        )
        
        # Test OBJ extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.obj")),
            ModelFormat.OBJ
        )
        
        # Test 3MF extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.3mf")),
            ModelFormat.THREE_MF
        )
        
        # Test STEP extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.step")),
            ModelFormat.STEP
        )
        
        # Test STP extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.stp")),
            ModelFormat.STEP
        )
        
        # Test unknown extension
        self.assertEqual(
            self.detector._detect_by_extension(Path("test.xyz")),
            ModelFormat.UNKNOWN
        )


if __name__ == '__main__':
    unittest.main()