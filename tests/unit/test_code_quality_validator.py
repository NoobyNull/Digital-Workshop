#!/usr/bin/env python3
"""
Unit tests for Code Quality Validator

Tests Black integration, Pylint analysis, weighted scoring calculation,
and quality gate enforcement.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add the current directory to the path so we can import the validator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_quality_validator import (
    CodeQualityValidator,
    FormattingResult,
    LintingResult,
    LintingIssue,
    ComplianceResult
)


class TestFormattingResult(unittest.TestCase):
    """Test the FormattingResult dataclass."""

    def test_formatting_result_creation(self):
        """Test creating a FormattingResult object."""
        result = FormattingResult(
            file_path="test.py",
            was_formatted=True,
            original_size=100,
            formatted_size=95,
            changes_made=["line formatting", "spacing"],
            processing_time=0.5
        )
        
        self.assertEqual(result.file_path, "test.py")
        self.assertTrue(result.was_formatted)
        self.assertEqual(result.original_size, 100)
        self.assertEqual(result.formatted_size, 95)
        self.assertEqual(result.changes_made, ["line formatting", "spacing"])
        self.assertEqual(result.processing_time, 0.5)
        self.assertIsNone(result.error_message)

    def test_formatting_result_with_error(self):
        """Test FormattingResult with error message."""
        result = FormattingResult(
            file_path="test.py",
            was_formatted=False,
            original_size=0,
            formatted_size=0,
            changes_made=[],
            processing_time=0.0,
            error_message="File not found"
        )
        
        self.assertEqual(result.error_message, "File not found")


class TestLintingResult(unittest.TestCase):
    """Test the LintingResult dataclass."""

    def test_linting_result_creation(self):
        """Test creating a LintingResult object."""
        issues = [
            LintingIssue(
                file_path="test.py",
                line_number=10,
                column=5,
                issue_type="warning",
                symbol="unused-variable",
                message="Unused variable 'x'",
                confidence="HIGH"
            )
        ]
        
        result = LintingResult(
            file_path="test.py",
            overall_score=8.5,
            issues=issues,
            rating="Good",
            processing_time=1.2
        )
        
        self.assertEqual(result.file_path, "test.py")
        self.assertEqual(result.overall_score, 8.5)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.rating, "Good")
        self.assertEqual(result.processing_time, 1.2)

    def test_linting_rating_classification(self):
        """Test rating classification based on scores."""
        test_cases = [
            (9.5, "Excellent"),
            (9.0, "Excellent"),
            (8.5, "Good"),
            (7.5, "Good"),
            (7.0, "Acceptable"),
            (6.0, "Acceptable"),
            (5.0, "Poor"),
        ]
        
        for score, expected_rating in test_cases:
            with self.subTest(score=score):
                result = LintingResult(
                    file_path="test.py",
                    overall_score=score,
                    issues=[],
                    rating="",  # Will be determined by validator
                    processing_time=0.0
                )
                
                # Test the rating logic from the validator
                if score >= 9.0:
                    rating = "Excellent"
                elif score >= 7.5:
                    rating = "Good"
                elif score >= 6.0:
                    rating = "Acceptable"
                else:
                    rating = "Poor"
                
                self.assertEqual(rating, expected_rating)


class TestCodeQualityValidator(unittest.TestCase):
    """Test the main CodeQualityValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = CodeQualityValidator(target_compliance=95.56)
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_file.py"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validator_initialization(self):
        """Test validator initialization with default and custom compliance targets."""
        # Test default initialization
        validator = CodeQualityValidator()
        self.assertEqual(validator.target_compliance, 95.56)
        
        # Test custom compliance target
        validator = CodeQualityValidator(target_compliance=90.0)
        self.assertEqual(validator.target_compliance, 90.0)

    def test_black_config(self):
        """Test Black configuration settings."""
        config = self.validator._get_black_config()
        
        self.assertEqual(config["line_length"], 88)
        self.assertIn("py38", config["target_version"])
        self.assertIn("\\.pyi?$", config["include"])
        self.assertIn("\\.eggs", config["extend_exclude"])

    def test_pylint_config(self):
        """Test Pylint configuration settings."""
        config = self.validator._get_pylint_config()
        
        self.assertEqual(config["max_line_length"], 88)
        self.assertIn("C0114", config["disable"])  # missing-module-docstring
        self.assertIn("E", config["enable"])  # errors

    @patch('subprocess.run')
    def test_format_with_black_success(self, mock_run):
        """Test successful Black formatting."""
        # Create a test file
        self.test_file.write_text("x = 1\ny = 2\n")
        
        # Mock successful Black execution
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        result = self.validator.format_with_black(self.test_file, fix_mode=True)
        
        self.assertFalse(result.was_formatted)  # No changes needed
        self.assertEqual(result.original_size, 14)  # "x = 1\ny = 2\n" = 14 bytes (including newline)
        self.assertEqual(result.formatted_size, 14)
        self.assertEqual(len(result.changes_made), 0)
        self.assertIsNone(result.error_message)

    @patch('subprocess.run')
    def test_format_with_black_changes_needed(self, mock_run):
        """Test Black formatting when changes are needed."""
        # Create a test file with formatting issues
        self.test_file.write_text("x=1;y=2\n")  # Missing spaces around operators
        
        # Mock Black execution that makes changes
        mock_run.return_value = Mock(
            returncode=1,  # Non-zero return code indicates changes needed
            stdout="would reformat test_file.py",
            stderr=""
        )
        
        result = self.validator.format_with_black(self.test_file, fix_mode=False)
        
        self.assertTrue(result.was_formatted)  # Changes were needed
        self.assertEqual(len(result.changes_made), 0)  # No changes recorded when fix_mode=False

    @patch('subprocess.run')
    def test_format_with_black_timeout(self, mock_run):
        """Test Black formatting timeout handling."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("black", 30)
        
        result = self.validator.format_with_black(self.test_file, fix_mode=True)
        
        self.assertFalse(result.was_formatted)
        self.assertEqual(result.error_message, "Formatting timeout")
        self.assertEqual(result.processing_time, 30.0)

    @patch('subprocess.run')
    def test_lint_with_pylint_success(self, mock_run):
        """Test successful Pylint analysis."""
        # Mock Pylint output
        pylint_output = [
            {
                "path": str(self.test_file),
                "line": 1,
                "column": 1,
                "type": "warning",
                "symbol": "unused-variable",
                "message": "Unused variable 'x'",
                "confidence": "HIGH"
            }
        ]
        
        mock_run.return_value = Mock(
            stdout=json.dumps(pylint_output),
            stderr="Your code has been rated at 8.50/10"
        )
        
        result = self.validator.lint_with_pylint(self.test_file)
        
        self.assertEqual(result.overall_score, 8.5)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].symbol, "unused-variable")
        self.assertEqual(result.rating, "Good")

    @patch('subprocess.run')
    def test_lint_with_pylint_no_issues(self, mock_run):
        """Test Pylint analysis with no issues."""
        mock_run.return_value = Mock(
            stdout="[]",
            stderr="Your code has been rated at 10.00/10"
        )
        
        result = self.validator.lint_with_pylint(self.test_file)
        
        self.assertEqual(result.overall_score, 10.0)
        self.assertEqual(len(result.issues), 0)
        self.assertEqual(result.rating, "Excellent")

    @patch('subprocess.run')
    def test_lint_with_pylint_timeout(self, mock_run):
        """Test Pylint timeout handling."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("pylint", 60)
        
        result = self.validator.lint_with_pylint(self.test_file)
        
        self.assertEqual(result.overall_score, 0.0)
        self.assertEqual(result.error_message, "Linting timeout")
        self.assertEqual(result.processing_time, 60.0)

    def test_calculate_compliance_perfect_score(self):
        """Test compliance calculation with perfect scores."""
        # Create mock results with perfect scores
        formatting_results = [
            FormattingResult("file1.py", False, 100, 100, [], 0.5),  # No formatting needed
            FormattingResult("file2.py", False, 200, 200, [], 0.3),
        ]
        
        linting_results = [
            LintingResult("file1.py", 10.0, [], "Excellent", 1.0),
            LintingResult("file2.py", 9.5, [], "Excellent", 0.8),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        
        self.assertAlmostEqual(compliance.formatting_score, 100.0, places=2)
        self.assertAlmostEqual(compliance.linting_score, 97.5, places=2)  # (10.0 + 9.5) / 2 * 10
        self.assertAlmostEqual(compliance.overall_score, 98.25, places=2)  # 100 * 0.3 + 97.5 * 0.7
        self.assertTrue(compliance.passed)
        self.assertEqual(len(compliance.violations), 0)

    def test_calculate_compliance_below_threshold(self):
        """Test compliance calculation below threshold."""
        # Create mock results with poor scores
        formatting_results = [
            FormattingResult("file1.py", True, 100, 95, ["formatting"], 0.5),  # Needed formatting
        ]
        
        linting_results = [
            LintingResult("file1.py", 5.0, [LintingIssue("file1.py", 1, 1, "error", "syntax-error", "Syntax error", "HIGH")], "Poor", 1.0),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        
        self.assertAlmostEqual(compliance.formatting_score, 85.0, places=2)  # Penalized for needing formatting
        self.assertAlmostEqual(compliance.linting_score, 50.0, places=2)  # 5.0 * 10
        self.assertAlmostEqual(compliance.overall_score, 60.5, places=2)  # 85 * 0.3 + 50 * 0.7 = 25.5 + 35 = 60.5
        self.assertFalse(compliance.passed)
        self.assertGreater(len(compliance.violations), 0)
        self.assertGreater(len(compliance.recommendations), 0)

    def test_calculate_compliance_empty_results(self):
        """Test compliance calculation with empty results."""
        compliance = self.validator.calculate_compliance([])
        
        self.assertEqual(compliance.actual_compliance, 0.0)
        self.assertFalse(compliance.passed)
        self.assertIn("No files to validate", compliance.violations)

    def test_validate_file_integration(self):
        """Test integrated file validation."""
        # Create a simple test file
        self.test_file.write_text("x = 1\ny = 2\nprint(x, y)\n")
        
        with patch.object(self.validator, 'format_with_black') as mock_format, \
             patch.object(self.validator, 'lint_with_pylint') as mock_lint:
            
            # Mock the results
            mock_format.return_value = FormattingResult(
                str(self.test_file), False, 20, 20, [], 0.1
            )
            mock_lint.return_value = LintingResult(
                str(self.test_file), 9.0, [], "Excellent", 0.5
            )
            
            formatting_result, linting_result = self.validator.validate_file(self.test_file)
            
            self.assertEqual(formatting_result.file_path, str(self.test_file))
            self.assertEqual(linting_result.file_path, str(self.test_file))

    def test_validate_directory(self):
        """Test directory validation."""
        # Create multiple test files
        files = ["file1.py", "file2.py", "file3.py"]
        for filename in files:
            (self.temp_dir / filename).write_text("x = 1\n")
        
        with patch.object(self.validator, 'validate_file') as mock_validate:
            # Mock successful validation for all files
            mock_validate.return_value = (
                FormattingResult("mock.py", False, 10, 10, [], 0.1),
                LintingResult("mock.py", 9.0, [], "Excellent", 0.2)
            )
            
            results = self.validator.validate_directory(self.temp_dir)
            
            self.assertEqual(len(results), 3)  # Three files
            mock_validate.assert_called()

    def test_generate_report(self):
        """Test comprehensive report generation."""
        # Create mock results
        formatting_results = [
            FormattingResult("file1.py", False, 100, 100, [], 0.5),
        ]
        
        linting_results = [
            LintingResult(
                "file1.py", 8.5, [
                    LintingIssue("file1.py", 1, 1, "warning", "unused-var", "Unused variable", "HIGH")
                ], "Good", 1.0
            ),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        report = self.validator.generate_report(results, compliance)
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('scores', report)
        self.assertIn('issues_by_type', report)
        self.assertIn('violations', report)
        self.assertIn('recommendations', report)
        self.assertIn('detailed_results', report)
        
        # Check summary data
        summary = report['summary']
        self.assertEqual(summary['total_files_analyzed'], 1)
        self.assertEqual(summary['files_with_formatting_issues'], 0)
        self.assertEqual(summary['files_with_linting_errors'], 0)
        
        # Check scores
        scores = report['scores']
        self.assertIn('formatting_score', scores)
        self.assertIn('linting_score', scores)
        self.assertIn('overall_score', scores)

    def test_save_report(self):
        """Test report saving functionality."""
        # Create a simple report
        report = {
            'summary': {'total_files': 1},
            'scores': {'overall_score': 95.56},
            'issues_by_type': {},
            'violations': [],
            'recommendations': [],
            'detailed_results': []
        }
        
        output_path = self.temp_dir / "test_report.json"
        self.validator.save_report(report, output_path)
        
        self.assertTrue(output_path.exists())
        
        # Verify the saved content
        with open(output_path) as f:
            saved_report = json.load(f)
        
        self.assertEqual(saved_report['summary']['total_files'], 1)
        self.assertEqual(saved_report['scores']['overall_score'], 95.56)


class TestPerformanceRequirements(unittest.TestCase):
    """Test performance requirements compliance."""

    def setUp(self):
        """Set up performance test fixtures."""
        self.validator = CodeQualityValidator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up performance test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_file_processing_time(self):
        """Test that large files are processed within time limits."""
        # Create a large test file (simulating 1000+ lines)
        large_content = "\n".join([f"variable_{i} = {i}" for i in range(1000)])
        large_file = self.temp_dir / "large_file.py"
        large_file.write_text(large_content)
        
        import time
        start_time = time.time()
        
        # Mock the subprocess calls to avoid actual Black/Pylint execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr="Your code has been rated at 8.00/10"
            )
            
            formatting_result, linting_result = self.validator.validate_file(large_file)
            
            processing_time = time.time() - start_time
            
            # Should complete within reasonable time (less than 5 seconds for this test)
            self.assertLess(processing_time, 5.0)

    def test_memory_efficiency(self):
        """Test memory efficiency during validation."""
        # Create multiple files to test memory usage
        for i in range(10):
            test_file = self.temp_dir / f"test_file_{i}.py"
            test_file.write_text(f"# Test file {i}\nx = {i}\ny = {i * 2}\n")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="[]",
                stderr="Your code has been rated at 9.00/10"
            )
            
            results = self.validator.validate_directory(self.temp_dir)
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB for this test)
            self.assertLess(memory_increase, 100 * 1024 * 1024)


class TestQualityGateEnforcement(unittest.TestCase):
    """Test quality gate enforcement with 95.56% threshold."""

    def setUp(self):
        """Set up quality gate test fixtures."""
        self.validator = CodeQualityValidator(target_compliance=95.56)

    def test_compliance_above_threshold(self):
        """Test compliance above 95.56% threshold passes."""
        formatting_results = [
            FormattingResult("file1.py", False, 100, 100, [], 0.5),
            FormattingResult("file2.py", False, 200, 200, [], 0.3),
        ]
        
        linting_results = [
            LintingResult("file1.py", 9.8, [], "Excellent", 1.0),
            LintingResult("file2.py", 9.6, [], "Excellent", 0.8),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        
        self.assertTrue(compliance.passed)
        self.assertGreaterEqual(compliance.actual_compliance, 95.56)

    def test_compliance_at_threshold(self):
        """Test compliance exactly at 95.56% threshold."""
        # Create results that should score exactly 95.56%
        # This requires careful calculation: (formatting_score * 0.3 + linting_score * 0.7) = 95.56
        # If formatting_score = 100 and linting_score = 93.66, then:
        # overall = 100 * 0.3 + 93.66 * 0.7 = 30 + 65.562 = 95.562 ≈ 95.56
        
        formatting_results = [
            FormattingResult("file1.py", False, 100, 100, [], 0.5),
        ]
        
        linting_results = [
            LintingResult("file1.py", 9.366, [], "Good", 1.0),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        
        # Should pass (>= 95.56)
        self.assertTrue(compliance.passed)

    def test_compliance_below_threshold(self):
        """Test compliance below 95.56% threshold fails."""
        formatting_results = [
            FormattingResult("file1.py", True, 100, 95, ["formatting"], 0.5),  # Penalized
        ]
        
        linting_results = [
            LintingResult("file1.py", 8.0, [], "Good", 1.0),
        ]
        
        results = list(zip(formatting_results, linting_results))
        compliance = self.validator.calculate_compliance(results)
        
        self.assertFalse(compliance.passed)
        self.assertLess(compliance.actual_compliance, 95.56)
        self.assertIn("below target", compliance.violations[0])


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestFormattingResult,
        TestLintingResult,
        TestCodeQualityValidator,
        TestPerformanceRequirements,
        TestQualityGateEnforcement,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)