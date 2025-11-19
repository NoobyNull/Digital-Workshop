#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Monolithic Module Detection Tool

Tests all aspects of the monolithic detection functionality including:
- Basic detection logic
- Comment and docstring exclusion
- Multi-line statement handling
- Performance with large codebases
- Edge cases and error handling
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
# No mock imports needed for current tests
import sys

# Add the current directory to the path to import the detector
sys.path.insert(0, str(Path(__file__).parent))

try:
    from tools.maintenance.monolithic_detector import MonolithicDetector, ModuleMetrics
except ImportError:
    try:
        from monolithic_detector import MonolithicDetector, ModuleMetrics
    except ImportError:
        # Fall back to legacy relative import when running directly from tests
        from .monolithic_detector import MonolithicDetector, ModuleMetrics

class TestMonolithicDetector(unittest.TestCase):
    """Test cases for the MonolithicDetector class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.detector = MonolithicDetector(threshold=500, max_workers=2)
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, name: str, content: str) -> Path:
        """Helper method to create test Python files."""
        file_path = self.test_dir / name
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def test_basic_monolithic_detection(self):
        """Test Case 1: Basic Monolithic Detection"""
        # Create test files with actual Python code (not just comments)
        small_content = "\n".join([f"x{i} = {i}" for i in range(1, 51)])
        medium_content = "\n".join([f"x{i} = {i}" for i in range(1, 301)])
        large_content = "\n".join([f"x{i} = {i}" for i in range(1, 601)])
        monolithic_content = "\n".join([f"x{i} = {i}" for i in range(1, 1201)])
        
        small_file = self.create_test_file("small_module.py", small_content)
        medium_file = self.create_test_file("medium_module.py", medium_content)
        large_file = self.create_test_file("large_module.py", large_content)
        monolithic_file = self.create_test_file("monolithic_module.py", monolithic_content)
        
        # Analyze files
        small_metrics = self.detector.analyze_file(small_file)
        medium_metrics = self.detector.analyze_file(medium_file)
        large_metrics = self.detector.analyze_file(large_file)
        monolithic_metrics = self.detector.analyze_file(monolithic_file)
        
        # Verify results
        self.assertFalse(small_metrics.is_monolithic, "Small module should not be flagged")
        self.assertFalse(medium_metrics.is_monolithic, "Medium module should not be flagged")
        self.assertTrue(large_metrics.is_monolithic, "Large module should be flagged")
        self.assertTrue(monolithic_metrics.is_monolithic, "Monolithic module should be flagged")
        
        # Verify severity levels
        self.assertEqual(large_metrics.severity, "minor", "Large module should have minor severity")
        self.assertEqual(monolithic_metrics.severity, "critical", "Monolithic module should have critical severity")
    
    def test_comment_and_docstring_exclusion(self):
        """Test Case 2: Comment and Docstring Exclusion"""
        content = '''"""
This is a module docstring
Multiple lines
"""

# Single line comment
def function1():
    """Function docstring"""
    pass  # Inline comment

# Multiple comment lines
# Line 2
# Line 3
def function2():
    pass
'''
        
        test_file = self.create_test_file("test_module_with_comments.py", content)
        metrics = self.detector.analyze_file(test_file)
        
        # Should have some code lines (function definitions and statements)
        self.assertGreater(metrics.code_lines, 0, "Should count some code lines")
        self.assertGreater(metrics.comment_lines, 0, "Should count comment lines")
        self.assertGreater(metrics.docstring_lines, 0, "Should count docstring lines")
        self.assertFalse(metrics.is_monolithic, "Should not be flagged as monolithic")
        
        # Verify that comments and docstrings are being excluded from code count
        total_content_lines = len(content.splitlines())
        self.assertLess(metrics.code_lines, total_content_lines,
                       "Code lines should be less than total lines due to comments/docstrings")
    
    def test_multiline_statements_handling(self):
        """Test Case 3: Multi-line Statements Handling"""
        content = '''data = [
    item1, item2, item3,
    item4, item5, item6,
    item7, item8, item9
]

def complex_function(
    param1,
    param2,
    param3=None
):
    return (
        param1 + param2 +
        param3 if param3 else 0
    )

# Another complex expression
result = (value1 + value2 + value3 +
          value4 + value5 + value6 +
          value7 + value8 + value9)
'''
        
        test_file = self.create_test_file("test_multiline.py", content)
        metrics = self.detector.analyze_file(test_file)
        
        # Should correctly count logical lines, not physical lines
        self.assertGreater(metrics.code_lines, 0, "Should count code lines correctly")
        self.assertFalse(metrics.is_monolithic, "Should not be flagged as monolithic")
    
    def test_empty_file_handling(self):
        """Test edge case: Empty file handling"""
        empty_content = ""
        test_file = self.create_test_file("empty_module.py", empty_content)
        metrics = self.detector.analyze_file(test_file)
        
        self.assertEqual(metrics.code_lines, 0, "Empty file should have 0 code lines")
        self.assertEqual(metrics.total_lines, 0, "Empty file should have 0 total lines")
        self.assertFalse(metrics.is_monolithic, "Empty file should not be flagged")
    
    def test_syntax_error_handling(self):
        """Test edge case: Syntax error handling"""
        invalid_content = '''def broken_function(
    # Missing closing parenthesis
    pass
'''
        
        test_file = self.create_test_file("syntax_error.py", invalid_content)
        metrics = self.detector.analyze_file(test_file)
        
        # Should handle syntax errors gracefully - may return 0 or some heuristic count
        self.assertLessEqual(metrics.code_lines, 2, "Syntax error file should return minimal code lines")
        self.assertFalse(metrics.is_monolithic, "Syntax error file should not be flagged")
    
    def test_directory_scanning(self):
        """Test directory scanning functionality"""
        # Create multiple test files
        for i in range(5):
            content = f"# Module {i}\n" + "\n".join([f"def func_{j}():\n    pass" for j in range(10)])
            self.create_test_file(f"module_{i}.py", content)
        
        results = self.detector.scan_directory(self.test_dir)
        
        self.assertEqual(len(results), 5, "Should analyze all Python files in directory")
        self.assertTrue(all(isinstance(r, ModuleMetrics) for r in results), 
                       "All results should be ModuleMetrics objects")
    
    def test_performance_large_codebase(self):
        """Test Case 4: Performance with Large Codebases"""
        start_time = time.time()
        
        # Create 100 test files
        for i in range(100):
            content = "\n".join([f"# Line {j}" for j in range(100)])
            self.create_test_file(f"large_file_{i}.py", content)
        
        results = self.detector.scan_directory(self.test_dir)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify performance requirements
        self.assertLess(processing_time, 30, "Should process 100 files in under 30 seconds")
        self.assertEqual(len(results), 100, "Should analyze all 100 files")
    
    def test_custom_threshold(self):
        """Test custom threshold functionality"""
        # Create a file with exactly 100 lines of actual code
        content = "\n".join([f"x{i} = {i}" for i in range(1, 101)])
        test_file = self.create_test_file("custom_threshold.py", content)
        
        # Test with threshold of 50
        detector_50 = MonolithicDetector(threshold=50)
        metrics_50 = detector_50.analyze_file(test_file)
        self.assertTrue(metrics_50.is_monolithic, "Should be flagged with threshold 50")
        
        # Test with threshold of 200
        detector_200 = MonolithicDetector(threshold=200)
        metrics_200 = detector_200.analyze_file(test_file)
        self.assertFalse(metrics_200.is_monolithic, "Should not be flagged with threshold 200")
    
    def test_report_generation(self):
        """Test report generation functionality"""
        # Create test files with actual code (not just comments)
        content = "\n".join([f"x{i} = {i}" for i in range(1, 601)])
        test_file = self.create_test_file("report_test.py", content)
        
        results = [self.detector.analyze_file(test_file)]
        report = self.detector.generate_report(results)
        
        # Verify report structure
        self.assertIn('summary', report, "Report should contain summary")
        self.assertIn('violations', report, "Report should contain violations")
        self.assertIn('detailed_results', report, "Report should contain detailed results")
        
        # Verify summary data
        summary = report['summary']
        self.assertEqual(summary['total_files_analyzed'], 1)
        self.assertEqual(summary['monolithic_files_found'], 1)
        self.assertEqual(summary['threshold'], 500)
        self.assertLess(summary['compliance_rate'], 100)
    
    def test_report_save_functionality(self):
        """Test report saving functionality"""
        # Create test data with actual code (not just comments)
        content = "\n".join([f"x{i} = {i}" for i in range(1, 601)])
        test_file = self.create_test_file("save_test.py", content)
        
        results = [self.detector.analyze_file(test_file)]
        report = self.detector.generate_report(results)
        
        # Save report
        output_path = self.test_dir / "test_report.json"
        self.detector.save_report(report, output_path)
        
        # Verify file was created and contains valid JSON
        self.assertTrue(output_path.exists(), "Report file should be created")
        
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_report = json.load(f)
        
        self.assertEqual(saved_report['summary']['total_files_analyzed'], 1)
    
    def test_severity_classification(self):
        """Test severity classification logic"""
        # Test different severity levels
        test_cases = [
            (501, "minor"),    # Just over threshold
            (751, "major"),    # 1.5x threshold
            (1001, "critical") # 2x threshold
        ]
        
        for code_lines, expected_severity in test_cases:
            content = "\n".join([f"x{i} = {i}" for i in range(1, code_lines + 1)])
            test_file = self.create_test_file(f"severity_test_{code_lines}.py", content)
            metrics = self.detector.analyze_file(test_file)
            
            self.assertEqual(metrics.severity, expected_severity,
                           f"Should have {expected_severity} severity for {code_lines} lines")
    
    def test_parallel_processing(self):
        """Test parallel processing functionality"""
        # Create multiple files to test parallel processing
        for i in range(10):
            content = "\n".join([f"# Line {j}" for j in range(1, 101)])
            self.create_test_file(f"parallel_test_{i}.py", content)
        
        # Test with different worker counts
        for workers in [1, 2, 4]:
            detector = MonolithicDetector(max_workers=workers)
            start_time = time.time()
            results = detector.scan_directory(self.test_dir)
            end_time = time.time()
            
            self.assertEqual(len(results), 10, f"Should analyze all files with {workers} workers")
            self.assertLess(end_time - start_time, 10, "Should complete quickly")
    
    def test_encoding_handling(self):
        """Test handling of different file encodings"""
        # Test UTF-8 with special characters
        content = '''# -*- coding: utf-8 -*-
"""
Test file with special characters: é, ñ, 中文, 🚀
"""

def función_española():
    """Función con caracteres especiales"""
    return "Hola mundo 🌍"

class ClaseConCaracteres:
    """Clase con caracteres especiales"""
    pass
'''
        
        test_file = self.create_test_file("encoding_test.py", content)
        metrics = self.detector.analyze_file(test_file)
        
        self.assertGreater(metrics.code_lines, 0, "Should handle UTF-8 encoding")
        self.assertFalse(metrics.is_monolithic, "Should not be flagged as monolithic")

class TestModuleMetrics(unittest.TestCase):
    """Test cases for the ModuleMetrics dataclass."""
    
    def test_module_metrics_creation(self):
        """Test ModuleMetrics object creation"""
        metrics = ModuleMetrics(
            path="/test/path.py",
            total_lines=100,
            code_lines=50,
            comment_lines=30,
            docstring_lines=10,
            blank_lines=10,
            is_monolithic=False,
            severity="none",
            timestamp="2025-10-31T16:50:00"
        )
        
        self.assertEqual(metrics.path, "/test/path.py")
        self.assertEqual(metrics.total_lines, 100)
        self.assertEqual(metrics.code_lines, 50)
        self.assertFalse(metrics.is_monolithic)
        self.assertEqual(metrics.severity, "none")

class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios for real-world usage."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.detector = MonolithicDetector()
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, name: str, content: str) -> Path:
        """Helper method to create test Python files."""
        file_path = self.test_dir / name
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def create_realistic_module(self, name: str, lines: int, has_classes: bool = True, 
                              has_functions: bool = True, has_docstrings: bool = True) -> Path:
        """Create a realistic Python module for testing."""
        lines_content = []
        
        if has_docstrings:
            lines_content.append('"""')
            lines_content.append(f'Module: {name}')
            lines_content.append('Author: Test Author')
            lines_content.append('Description: A test module')
            lines_content.append('"""')
            lines_content.append('')
        
        if has_classes:
            for i in range(max(1, lines // 200)):
                lines_content.append(f'class TestClass{i}:')
                lines_content.append('    """A test class"""')
                lines_content.append('    def __init__(self):')
                lines_content.append('        self.value = 0')
                lines_content.append('')
                lines_content.append('    def method1(self):')
                lines_content.append('        """A test method"""')
                lines_content.append('        return self.value')
                lines_content.append('')
        
        if has_functions:
            for i in range(max(1, lines // 100)):
                lines_content.append(f'def test_function_{i}():')
                lines_content.append('    """A test function"""')
                lines_content.append('    result = 0')
                lines_content.append('    for i in range(10):')
                lines_content.append('        result += i')
                lines_content.append('    return result')
                lines_content.append('')
        
        # Fill remaining lines with simple code
        while len(lines_content) < lines:
            lines_content.append('x = 1  # Simple assignment')
        
        content = '\n'.join(lines_content[:lines])
        file_path = self.test_dir / name
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def test_realistic_codebase_analysis(self):
        """Test analysis of realistic codebase structure"""
        # Create modules of various sizes
        self.create_realistic_module("small_module.py", 50)
        self.create_realistic_module("medium_module.py", 300)
        self.create_realistic_module("large_module.py", 600)
        self.create_realistic_module("monolithic_module.py", 1200)
        
        results = self.detector.scan_directory(self.test_dir)
        
        self.assertEqual(len(results), 4, "Should analyze all created modules")
        
        # Check that results are properly classified
        small_result = next(r for r in results if "small" in r.path)
        large_result = next(r for r in results if "large" in r.path)
        monolithic_result = next(r for r in results if "monolithic" in r.path)
        
        self.assertFalse(small_result.is_monolithic, "Small module should not be flagged")
        self.assertTrue(large_result.is_monolithic, "Large module should be flagged")
        self.assertTrue(monolithic_result.is_monolithic, "Monolithic module should be flagged")
    
    def test_mixed_content_module(self):
        """Test module with mixed content types"""
        content = '''"""
This is a comprehensive test module
with various types of content.
"""

import os
import sys
from typing import List, Dict

# Constants
MAX_SIZE = 1000
DEFAULT_TIMEOUT = 30

class DataProcessor:
    """A class for processing data."""
    
    def __init__(self, config: Dict):
        """Initialize the processor."""
        self.config = config
        self.data = []
    
    def load_data(self, filename: str) -> bool:
        """Load data from file."""
        try:
            with open(filename, 'r') as f:
                self.data = f.readlines()
            return True
        except FileNotFoundError:
            return False
    
    def process(self) -> List[str]:
        """Process the loaded data."""
        result = []
        for line in self.data:
            processed = line.strip().upper()
            result.append(processed)
        return result

def utility_function(items: List[str]) -> str:
    """A utility function."""
    return ', '.join(items)

# Main execution
if __name__ == "__main__":
    processor = DataProcessor({})
    if processor.load_data("input.txt"):
        processed = processor.process()
        print(utility_function(processed))
'''
        
        test_file = self.create_test_file("mixed_content.py", content)
        metrics = self.detector.analyze_file(test_file)
        
        # Should correctly count different types of lines
        self.assertGreater(metrics.code_lines, 0, "Should count code lines")
        self.assertGreater(metrics.comment_lines, 0, "Should count comment lines")
        self.assertGreater(metrics.docstring_lines, 0, "Should count docstring lines")
        self.assertFalse(metrics.is_monolithic, "Should not be flagged as monolithic")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
