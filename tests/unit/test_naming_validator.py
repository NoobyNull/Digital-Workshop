#!/usr/bin/env python3
"""
Comprehensive Test Suite for File Naming Convention Validator

Tests all aspects of the naming convention validation including:
- Basic adjective detection
- Compound adjective detection
- Edge cases and false positives
- File extension handling
- Performance with large codebases
- Domain term filtering
- Severity classification
"""

import unittest
import tempfile
import shutil
import json
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules to test
import sys
sys.path.insert(0, '.')

from tools.maintenance.naming_validator import (
    AdjectiveDetector, 
    NamingConventionValidator, 
    NamingViolation, 
    NamingValidationResult
)

class TestAdjectiveDetector(unittest.TestCase):
    """Test cases for the AdjectiveDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = AdjectiveDetector()
    
    def test_basic_adjective_detection(self):
        """Test detection of basic replacement file adjectives."""
        test_cases = [
            ("refactored_parser.py", ["refactored"]),
            ("new_model_handler.py", ["new"]),
            ("old_viewer_widget.py", ["old"]),
            ("backup_config.py", ["backup"]),
            ("temp_solution.py", ["temp"]),
            ("improved_algorithm.py", ["improved"]),
            ("enhanced_ui_component.py", ["enhanced"]),
            ("optimized_renderer.py", ["optimized"]),
            ("modern_interface.py", ["modern"]),
            ("legacy_code_handler.py", ["legacy"]),
            ("experimental_feature.py", ["experimental"]),
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                self.assertEqual(set(detected), set(expected), 
                               f"Failed to detect adjectives in {filename}")
    
    def test_compound_adjective_detection(self):
        """Test detection of compound words and variations."""
        test_cases = [
            ("new_user_model.py", ["new"]),
            ("old_database_handler.py", ["old"]),
            ("backup_file_manager.py", ["backup"]),
            ("temp_data_processor.py", ["temp"]),
            ("improved_algorithm_v2.py", ["improved", "v2"]),
            ("enhanced_ui_component.py", ["enhanced"]),
            ("optimized_renderer.py", ["optimized"]),
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                self.assertEqual(set(detected), set(expected), 
                               f"Failed to detect compound adjectives in {filename}")
    
    def test_version_detection(self):
        """Test detection of version indicators."""
        test_cases = [
            ("model_v1.py", ["v1"]),
            ("handler_v2.py", ["v2"]),
            ("config_version3.json", ["version3"]),
            ("data_1.0.yaml", ["1.0"]),
            ("file_2.0.xml", ["2.0"]),
            ("final_release.py", ["final", "release"]),
            ("beta_version.py", ["beta"]),
            ("alpha_build.py", ["alpha"]),
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                self.assertEqual(set(detected), set(expected), 
                               f"Failed to detect version indicators in {filename}")
    
    def test_domain_term_filtering(self):
        """Test that domain terms are not flagged as adjectives."""
        domain_terms = [
            "user_model.py",
            "network_handler.py", 
            "database_connection.py",
            "file_validator.py",
            "api_client.py",
            "system_config.py",
            "admin_panel.py",
            "customer_data.py",
            "product_catalog.py",
            "main_application.py",
            "core_service.py",
            "shared_utils.py",
            "common_helper.py",
            "data_model.py",
            "view_controller.py",
        ]
        
        for filename in domain_terms:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                # Filter out domain terms
                filtered = [adj for adj in detected if not self.detector.is_domain_term(adj)]
                self.assertEqual(len(filtered), 0, 
                               f"Domain term incorrectly flagged as adjective in {filename}")
    
    def test_false_positive_prevention(self):
        """Test prevention of false positives for legitimate technical terms."""
        legitimate_terms = [
            "user_authentication.py",  # "user" is domain, "authentication" is technical
            "network_protocol.py",     # "network" is domain, "protocol" is technical
            "database_schema.py",      # "database" is domain, "schema" is technical
            "file_system.py",          # "file" is domain, "system" is technical
            "api_endpoint.py",         # "api" is domain, "endpoint" is technical
        ]
        
        for filename in legitimate_terms:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                filtered = [adj for adj in detected if not self.detector.is_domain_term(adj)]
                self.assertEqual(len(filtered), 0, 
                               f"False positive for legitimate term in {filename}")
    
    def test_suggested_name_generation(self):
        """Test generation of improved filenames."""
        test_cases = [
            ("refactored_parser.py", ["refactored"], "parser.py"),
            ("new_user_model.py", ["new"], "user_model.py"),
            ("old_database_handler.py", ["old"], "database_handler.py"),
            ("backup_config.json", ["backup"], "config.json"),
            ("temp_data.csv", ["temp"], "data.csv"),
            ("improved_algorithm_v2.py", ["improved", "v2"], "algorithm.py"),
            ("enhanced_ui_component.py", ["enhanced"], "ui_component.py"),
        ]
        
        for filename, adjectives, expected in test_cases:
            with self.subTest(filename=filename):
                suggested = self.detector.suggest_improved_name(filename, adjectives)
                self.assertEqual(suggested, expected, 
                               f"Incorrect suggestion for {filename}: got {suggested}, expected {expected}")
    
    def test_edge_cases(self):
        """Test edge cases and unusual filenames."""
        test_cases = [
            ("", []),  # Empty filename
            ("file", []),  # Single word
            ("file.py", []),  # Simple filename
            ("very_long_filename_with_many_words.py", []),  # Long but valid
            ("file_with_adjective_in_middle_new.py", ["new"]),  # Adjective in middle
            ("multiple_adjectives_old_new_temp.py", ["old", "new", "temp"]),  # Multiple adjectives
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                detected = self.detector.detect_adjectives(filename)
                self.assertEqual(set(detected), set(expected), 
                               f"Edge case failed for {filename}")

class TestNamingConventionValidator(unittest.TestCase):
    """Test cases for the NamingConventionValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = NamingConventionValidator(max_workers=2)
        self.temp_dir = None
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_files(self, file_list):
        """Create test files for validation."""
        self.temp_dir = tempfile.mkdtemp()
        created_files = []
        
        for filename in file_list:
            file_path = Path(self.temp_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"# Test file: {filename}")
            created_files.append(file_path)
        
        return created_files
    
    def test_single_file_validation_valid(self):
        """Test validation of a single valid file."""
        test_file = Path("valid_file.py")
        test_file.write_text("# Valid file")
        
        try:
            violation = self.validator.validate_filename(test_file)
            self.assertIsNone(violation, "Valid file should not have violations")
        finally:
            test_file.unlink()
    
    def test_single_file_validation_invalid(self):
        """Test validation of a single file with violations."""
        test_file = Path("refactored_parser.py")
        test_file.write_text("# Refactored file")
        
        try:
            violation = self.validator.validate_filename(test_file)
            self.assertIsNotNone(violation, "Invalid file should have violations")
            self.assertEqual(violation.file_name, "refactored_parser.py")
            self.assertIn("refactored", violation.detected_adjectives)
            self.assertEqual(violation.severity, "major")
            self.assertEqual(violation.suggested_name, "parser.py")
        finally:
            test_file.unlink()
    
    def test_severity_classification(self):
        """Test severity classification of violations."""
        test_cases = [
            ("backup_file.py", "critical"),  # backup is critical
            ("temp_data.py", "critical"),    # temp is critical
            ("old_handler.py", "critical"),  # old is critical
            ("refactored_module.py", "major"),  # refactored is major
            ("new_model.py", "major"),       # new is major
            ("improved_algorithm.py", "major"),  # improved is major
            ("working_solution.py", "minor"),    # working is minor
            ("final_version.py", "minor"),   # final is minor
        ]
        
        for filename, expected_severity in test_cases:
            with self.subTest(filename=filename):
                test_file = Path(filename)
                test_file.write_text(f"# Test file: {filename}")
                
                try:
                    violation = self.validator.validate_filename(test_file)
                    self.assertIsNotNone(violation)
                    self.assertEqual(violation.severity, expected_severity,
                                   f"Incorrect severity for {filename}")
                finally:
                    test_file.unlink()
    
    def test_directory_validation(self):
        """Test validation of a directory with multiple files."""
        test_files = [
            "valid_file.py",
            "user_model.py",
            "refactored_parser.py",
            "new_handler.py",
            "backup_config.json",
            "network_service.py",
            "temp_data.csv",
        ]
        
        created_files = self.create_test_files(test_files)
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            
            self.assertEqual(result.total_files, 7)
            self.assertEqual(result.violated_files, 4)  # refactored, new, backup, temp
            self.assertEqual(result.valid_files, 3)     # valid_file, user_model, network_service
            self.assertAlmostEqual(result.compliance_rate, 42.86, places=2)
            
            # Check that violations are correctly identified
            violated_names = {v.file_name for v in result.violations}
            expected_violations = {"refactored_parser.py", "new_handler.py", 
                                 "backup_config.json", "temp_data.csv"}
            self.assertEqual(violated_names, expected_violations)
            
        finally:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def test_domain_term_filtering_integration(self):
        """Test domain term filtering in full validation."""
        test_files = [
            "user_authentication.py",  # Should be valid (user is domain term)
            "network_protocol.py",     # Should be valid (network is domain term)
            "database_schema.py",      # Should be valid (database is domain term)
            "refactored_user_model.py", # Should be invalid (refactored is adjective)
            "new_network_handler.py",   # Should be invalid (new is adjective)
        ]
        
        created_files = self.create_test_files(test_files)
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            
            self.assertEqual(result.total_files, 5)
            self.assertEqual(result.violated_files, 2)  # Only refactored and new
            self.assertEqual(result.valid_files, 3)     # user_auth, network_protocol, database_schema
            
        finally:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def test_file_extension_handling(self):
        """Test proper handling across different file types."""
        test_files = [
            "refactored_parser.py",
            "new_config.json",
            "old_styles.css",
            "backup_script.sh",
            "temp_data.csv",
            "improved_config.yaml",
            "enhanced_template.html",
        ]
        
        created_files = self.create_test_files(test_files)
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            
            self.assertEqual(result.total_files, 7)
            self.assertEqual(result.violated_files, 7)  # All should be violations
            
            # Check that all file types are handled
            extensions = {Path(v.file_name).suffix for v in result.violations}
            expected_extensions = {'.py', '.json', '.css', '.sh', '.csv', '.yaml', '.html'}
            self.assertEqual(extensions, expected_extensions)
            
        finally:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

class TestPerformanceRequirements(unittest.TestCase):
    """Test cases for performance requirements."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.validator = NamingConventionValidator(max_workers=4)
        self.temp_dir = None
    
    def tearDown(self):
        """Clean up performance test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_large_test_directory(self, num_files=1000):
        """Create a large directory structure for performance testing."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mix of valid and invalid filenames
        valid_patterns = [
            "user_model.py", "network_handler.py", "database_service.py",
            "api_client.py", "file_validator.py", "system_config.py",
            "main_application.py", "core_service.py", "shared_utils.py",
        ]
        
        invalid_patterns = [
            "refactored_parser.py", "new_handler.py", "old_viewer.py",
            "backup_config.py", "temp_data.py", "improved_algorithm.py",
            "enhanced_ui.py", "optimized_renderer.py", "working_solution.py",
        ]
        
        files_created = 0
        
        # Create files in batches to simulate a real codebase
        for i in range(num_files):
            if i % 3 == 0:  # Every third file is invalid
                pattern = invalid_patterns[i % len(invalid_patterns)]
                filename = f"{pattern[:-3]}_{i}.py"
            else:
                pattern = valid_patterns[i % len(valid_patterns)]
                filename = f"{pattern[:-3]}_{i}.py"
            
            file_path = Path(self.temp_dir) / filename
            file_path.write_text(f"# Test file {i}")
            files_created += 1
        
        return files_created
    
    def test_performance_with_large_codebase(self):
        """Test performance with a large codebase (1000+ files)."""
        print("\n=== Performance Test: Large Codebase ===")
        
        num_files = self.create_large_test_directory(1000)
        print(f"Created {num_files} test files")
        
        start_time = time.time()
        result = self.validator.scan_directory(Path(self.temp_dir))
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Files processed: {result.total_files}")
        print(f"Compliance rate: {result.compliance_rate:.2f}%")
        
        # Performance assertions
        self.assertLess(processing_time, 15.0, 
                       f"Processing took {processing_time:.2f}s, should be under 15s")
        self.assertEqual(result.total_files, num_files)
        
        # Memory usage check (basic)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"Memory usage: {memory_mb:.2f} MB")
            
            self.assertLess(memory_mb, 200, 
                           f"Memory usage {memory_mb:.2f}MB exceeds 200MB limit")
        except ImportError:
            print("Memory check: psutil not available")
    
    def test_progress_reporting(self):
        """Test progress reporting functionality."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a moderate number of files
        for i in range(200):
            filename = f"file_{i}.py"
            file_path = Path(self.temp_dir) / filename
            file_path.write_text(f"# Test file {i}")
        
        progress_updates = []
        
        def progress_callback(processed, total, percentage):
            progress_updates.append((processed, total, percentage))
        
        start_time = time.time()
        result = self.validator.scan_directory(Path(self.temp_dir), progress_callback)
        end_time = time.time()
        
        # Check that progress was reported
        self.assertGreater(len(progress_updates), 0, "No progress updates received")
        
        # Check that progress increases
        for i in range(1, len(progress_updates)):
            prev_processed = progress_updates[i-1][0]
            curr_processed = progress_updates[i][0]
            self.assertGreaterEqual(curr_processed, prev_processed, 
                                  "Progress should not decrease")
        
        print(f"Progress updates: {len(progress_updates)}")
        print(f"Processing time: {end_time - start_time:.2f} seconds")

class TestJSONReporting(unittest.TestCase):
    """Test cases for JSON reporting functionality."""
    
    def setUp(self):
        """Set up JSON reporting test fixtures."""
        self.validator = NamingConventionValidator(max_workers=2)
        self.temp_dir = None
        self.report_file = None
    
    def tearDown(self):
        """Clean up JSON reporting test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if self.report_file and os.path.exists(self.report_file):
            os.unlink(self.report_file)
    
    def test_report_generation(self):
        """Test comprehensive report generation."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files with various violations
        test_files = [
            "valid_file.py",
            "refactored_parser.py",  # major
            "backup_config.json",    # critical
            "user_model.py",         # valid
            "new_handler.py",        # major
            "temp_data.csv",         # critical
            "working_solution.py",   # minor
        ]
        
        for filename in test_files:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text(f"# Test file: {filename}")
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            report = self.validator.generate_report(result)
            
            # Test report structure
            self.assertIn('summary', report)
            self.assertIn('violations_by_severity', report)
            self.assertIn('adjective_frequency', report)
            self.assertIn('recommendations', report)
            
            # Test summary data
            summary = report['summary']
            self.assertEqual(summary['total_files_analyzed'], 7)
            self.assertEqual(summary['violated_files'], 5)
            self.assertEqual(summary['valid_files'], 2)
            self.assertIsInstance(summary['compliance_rate'], float)
            self.assertIsInstance(summary['processing_time_seconds'], float)
            
            # Test violations by severity
            violations_by_severity = report['violations_by_severity']
            self.assertIn('critical', violations_by_severity)
            self.assertIn('major', violations_by_severity)
            self.assertIn('minor', violations_by_severity)
            
            # Check critical violations
            critical_violations = violations_by_severity['critical']
            self.assertEqual(len(critical_violations), 2)
            critical_files = {v['file_name'] for v in critical_violations}
            self.assertEqual(critical_files, {'backup_config.json', 'temp_data.csv'})
            
            # Check major violations
            major_violations = violations_by_severity['major']
            self.assertEqual(len(major_violations), 2)
            major_files = {v['file_name'] for v in major_violations}
            self.assertEqual(major_files, {'refactored_parser.py', 'new_handler.py'})
            
            # Check minor violations
            minor_violations = violations_by_severity['minor']
            self.assertEqual(len(minor_violations), 1)
            self.assertEqual(minor_violations[0]['file_name'], 'working_solution.py')
            
            # Test adjective frequency
            adjective_freq = report['adjective_frequency']
            self.assertIsInstance(adjective_freq, dict)
            
            # Test recommendations
            recommendations = report['recommendations']
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            
        finally:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def test_report_saving(self):
        """Test saving report to JSON file."""
        self.temp_dir = tempfile.mkdtemp()
        self.report_file = Path("test_report.json")
        
        # Create a simple test case
        test_file = Path(self.temp_dir) / "refactored_parser.py"
        test_file.write_text("# Test file")
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            report = self.validator.generate_report(result)
            self.validator.save_report(report, self.report_file)
            
            # Check that file was created
            self.assertTrue(self.report_file.exists())
            
            # Check that file contains valid JSON
            with open(self.report_file, 'r') as f:
                loaded_report = json.load(f)
            
            self.assertEqual(loaded_report['summary']['total_files_analyzed'], 1)
            self.assertEqual(loaded_report['summary']['violated_files'], 1)
            
        finally:
            if self.temp_dir:
                shutil.rmtree(self.temp_dir)
            if self.report_file and self.report_file.exists():
                os.unlink(self.report_file)

class TestIntegrationScenarios(unittest.TestCase):
    """Test cases for real-world integration scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.validator = NamingConventionValidator(max_workers=2)
        self.temp_dir = None
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_realistic_project_structure(self):
        """Test with a realistic project structure."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a realistic project structure
        project_structure = {
            "src/": [
                "main.py",
                "user_authentication.py",
                "database_service.py",
                "api_client.py",
                "refactored_parser.py",  # Should be flagged
                "new_handler.py",        # Should be flagged
            ],
            "tests/": [
                "test_main.py",
                "test_user_auth.py",
                "test_database.py",
                "backup_test_config.py",  # Should be flagged
            ],
            "config/": [
                "app_config.json",
                "database_config.yaml",
                "old_config_backup.py",   # Should be flagged
            ],
            "docs/": [
                "README.md",
                "API_documentation.md",
                "old_user_guide.md",      # Should be flagged
            ],
            "scripts/": [
                "deploy.sh",
                "backup_script.py",       # Should be flagged
                "temp_deployment.py",     # Should be flagged
            ]
        }
        
        # Create the directory structure and files
        for directory, files in project_structure.items():
            dir_path = Path(self.temp_dir) / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            for filename in files:
                file_path = dir_path / filename
                file_path.write_text(f"# {directory}{filename}")
        
        try:
            result = self.validator.scan_directory(Path(self.temp_dir))
            
            # Verify results
            self.assertEqual(result.total_files, sum(len(files) for files in project_structure.values()))
            self.assertEqual(result.violated_files, 7)  # 7 files with violations
            
            # Check that violations are in expected files
            violated_names = {v.file_name for v in result.violations}
            expected_violations = {
                "refactored_parser.py", "new_handler.py", "backup_test_config.py",
                "old_config_backup.py", "old_user_guide.md", "backup_script.py", "temp_deployment.py"
            }
            self.assertEqual(violated_names, expected_violations)
            
            # Check compliance rate
            expected_compliance = ((result.total_files - result.violated_files) / result.total_files) * 100
            self.assertAlmostEqual(result.compliance_rate, expected_compliance, places=2)
            
        finally:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

def run_performance_benchmark():
    """Run a performance benchmark and print results."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    validator = NamingConventionValidator(max_workers=4)
    
    # Create a large test directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create 1500 files for stress testing
        print("Creating 1500 test files...")
        for i in range(1500):
            if i % 4 == 0:
                filename = f"refactored_module_{i}.py"
            elif i % 4 == 1:
                filename = f"new_handler_{i}.py"
            elif i % 4 == 2:
                filename = f"backup_config_{i}.json"
            else:
                filename = f"user_model_{i}.py"
            
            file_path = Path(temp_dir) / filename
            file_path.write_text(f"# Test file {i}")
        
        print(f"Created files in {temp_dir}")
        
        # Run validation
        print("Running validation...")
        start_time = time.time()
        result = validator.scan_directory(Path(temp_dir))
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Print results
        print(f"\nResults:")
        print(f"  Total files: {result.total_files}")
        print(f"  Valid files: {result.valid_files}")
        print(f"  Violated files: {result.violated_files}")
        print(f"  Compliance rate: {result.compliance_rate:.2f}%")
        print(f"  Processing time: {processing_time:.2f} seconds")
        print(f"  Files per second: {result.total_files / processing_time:.2f}")
        
        # Check performance requirements
        if processing_time < 15.0:
            print(f"  [PASS] Performance: PASS (< 15 seconds)")
        else:
            print(f"  [FAIL] Performance: FAIL (>= 15 seconds)")
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"  Memory usage: {memory_mb:.2f} MB")
            
            if memory_mb < 200:
                print(f"  [PASS] Memory: PASS (< 200 MB)")
            else:
                print(f"  [FAIL] Memory: FAIL (>= 200 MB)")
        except ImportError:
            print("  Memory check: psutil not available")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # Run all tests
    print("Running comprehensive test suite for File Naming Convention Validator")
    print("="*80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAdjectiveDetector,
        TestNamingConventionValidator,
        TestPerformanceRequirements,
        TestJSONReporting,
        TestIntegrationScenarios,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Run performance benchmark
    run_performance_benchmark()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
