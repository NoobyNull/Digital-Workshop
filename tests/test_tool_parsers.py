"""
Unit tests for tool database parsers.

Comprehensive testing of all parser implementations for CSV, JSON, VTDB, and TDB formats.
"""

import unittest
import json
import csv
import tempfile
from pathlib import Path

from src.parsers.tool_parsers import (
    CSVToolParser,
    JSONToolParser,
    VTDBToolParser,
    TDBToolParser,
    ToolData,
    ProgressCallback
)


class MockProgressCallback(ProgressCallback):
    """Mock progress callback for testing."""

    def __init__(self):
        self.progress_updates = []

    def report(self, progress: float, message: str = ""):
        """Report progress."""
        self.progress_updates.append((progress, message))


class TestCSVToolParser(unittest.TestCase):
    """Test CSV tool parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = CSVToolParser()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def create_sample_csv(self, filename: str) -> str:
        """Create a sample CSV file for testing."""
        file_path = Path(self.temp_dir.name) / filename
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'GUID', 'Description', 'Type', 'Diameter (mm)',
                'Vendor', 'Flute Length (mm)', 'Overall Length (mm)'
            ])
            writer.writerow([
                'tool-001', 'Carbide End Mill', 'End Mill', '3.175',
                'IDC Woodcraft', '10', '50'
            ])
            writer.writerow([
                'tool-002', 'Carbide Bit', 'Ball Nose', '6.35',
                'IDC Woodcraft', '15', '60'
            ])
        return str(file_path)

    def test_csv_validation(self):
        """Test CSV file validation."""
        file_path = self.create_sample_csv('test.csv')
        valid, message = self.parser.validate_file(file_path)
        self.assertTrue(valid)
        self.assertEqual(message, "")

    def test_csv_validation_invalid_file(self):
        """Test CSV validation with invalid file."""
        valid, message = self.parser.validate_file('/nonexistent/file.csv')
        self.assertFalse(valid)
        self.assertIn("does not exist", message)

    def test_csv_parsing(self):
        """Test CSV parsing."""
        file_path = self.create_sample_csv('test.csv')
        callback = MockProgressCallback()
        tools = self.parser.parse(file_path, callback)

        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].guid, 'tool-001')
        self.assertEqual(tools[0].description, 'Carbide End Mill')
        self.assertEqual(tools[1].guid, 'tool-002')

    def test_csv_parsing_with_progress(self):
        """Test CSV parsing with progress callback."""
        file_path = self.create_sample_csv('test.csv')
        callback = MockProgressCallback()
        tools = self.parser.parse(file_path, callback)

        self.assertGreater(len(callback.progress_updates), 0)
        self.assertLessEqual(callback.progress_updates[-1][0], 1.0)


class TestJSONToolParser(unittest.TestCase):
    """Test JSON tool parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = JSONToolParser()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def create_sample_json(self, filename: str) -> str:
        """Create a sample JSON file for testing."""
        file_path = Path(self.temp_dir.name) / filename
        data = {
            "tools": [
                {
                    "guid": "tool-001",
                    "description": "Carbide End Mill",
                    "type": "End Mill",
                    "diameter": 3.175,
                    "vendor": "IDC Woodcraft",
                    "properties": {"flute_length": 10}
                },
                {
                    "guid": "tool-002",
                    "description": "Carbide Bit",
                    "type": "Ball Nose",
                    "diameter": 6.35,
                    "vendor": "IDC Woodcraft",
                    "properties": {"flute_length": 15}
                }
            ]
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return str(file_path)

    def test_json_validation(self):
        """Test JSON file validation."""
        file_path = self.create_sample_json('test.json')
        valid, message = self.parser.validate_file(file_path)
        self.assertTrue(valid)
        self.assertEqual(message, "")

    def test_json_validation_invalid_file(self):
        """Test JSON validation with invalid file."""
        valid, message = self.parser.validate_file('/nonexistent/file.json')
        self.assertFalse(valid)
        self.assertIn("does not exist", message)

    def test_json_parsing(self):
        """Test JSON parsing."""
        file_path = self.create_sample_json('test.json')
        callback = MockProgressCallback()
        tools = self.parser.parse(file_path, callback)

        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].guid, 'tool-001')
        self.assertEqual(tools[0].description, 'Carbide End Mill')


class TestVTDBToolParser(unittest.TestCase):
    """Test VTDB tool parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = VTDBToolParser()

    def test_format_name(self):
        """Test format name."""
        self.assertEqual(self.parser.get_format_name(), "VTDB")


class TestTDBToolParser(unittest.TestCase):
    """Test TDB tool parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = TDBToolParser()

    def test_format_name(self):
        """Test format name."""
        self.assertEqual(self.parser.get_format_name(), "TDB")


class TestToolDataStructure(unittest.TestCase):
    """Test ToolData dataclass."""

    def test_tool_data_creation(self):
        """Test ToolData creation."""
        tool = ToolData(
            guid="tool-001",
            description="Test Tool",
            tool_type="End Mill",
            diameter=3.175,
            vendor="Test Vendor"
        )
        self.assertEqual(tool.guid, "tool-001")
        self.assertEqual(tool.description, "Test Tool")
        self.assertEqual(tool.tool_type, "End Mill")
        self.assertEqual(tool.diameter, 3.175)

    def test_tool_data_with_properties(self):
        """Test ToolData with custom properties."""
        properties = {"flute_length": 10, "rpm": 5000}
        tool = ToolData(
            guid="tool-001",
            description="Test Tool",
            tool_type="End Mill",
            diameter=3.175,
            vendor="Test Vendor",
            custom_properties=properties
        )
        self.assertEqual(tool.custom_properties["flute_length"], 10)


class TestParserIntegration(unittest.TestCase):
    """Integration tests for parser workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_parser_error_handling(self):
        """Test parser error handling."""
        parser = CSVToolParser()
        # Invalid file should not raise exception
        try:
            parser.parse('/nonexistent/file.csv')
        except Exception as e:
            self.fail(f"Parser raised exception: {e}")


if __name__ == '__main__':
    unittest.main()
