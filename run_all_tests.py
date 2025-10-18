#!/usr/bin/env python
"""
Master Test Runner for Candy-Cadence Application

Runs all tests in the test suite and provides comprehensive feedback.
Generates a detailed report with individual test results and summary statistics.

Usage:
    python run_all_tests.py                    # Run all tests
    python run_all_tests.py --verbose          # Run with verbose output
    python run_all_tests.py --failfast         # Stop on first failure
    python run_all_tests.py --pattern test_*   # Run specific pattern
"""

import sys
import os
import unittest
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    """Container for individual test results."""
    
    def __init__(self, test_name: str, module_name: str):
        self.test_name = test_name
        self.module_name = module_name
        self.status = "PENDING"
        self.duration = 0.0
        self.error_message = ""
        self.error_type = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test": self.test_name,
            "module": self.module_name,
            "status": self.status,
            "duration": round(self.duration, 3),
            "error_type": self.error_type,
            "error_message": self.error_message[:200] if self.error_message else ""
        }


class MasterTestRunner:
    """Master test runner that executes all tests and provides feedback."""
    
    def __init__(self, verbose: bool = False, failfast: bool = False):
        self.verbose = verbose
        self.failfast = failfast
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        self.test_files = [
            "test_application",
            "test_application_config",
            "test_database",
            "test_database_performance_benchmark",
            "test_exception_handler",
            "test_format_detector",
            "test_lighting_complete",
            "test_lighting_final",
            "test_lighting_functionality",
            "test_lighting_simple",
            "test_logging",
            "test_meshlib_viewer",
            "test_metadata_editor",
            "test_model_library",
            "test_model_library_ui",
            "test_mtl_debug",
            "test_obj_parser",
            "test_packaging",
            "test_performance_optimization",
            "test_search_engine",
            "test_step_parser",
            "test_stl_parser",
            "test_threemf_parser",
            "test_viewer_3d",
            "test_viewer_widget",
        ]
    
    def run_all_tests(self) -> bool:
        """Run all tests and return True if all passed."""
        self.start_time = time.time()
        print("\n" + "="*80)
        print("CANDY-CADENCE MASTER TEST SUITE")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.test_files)}")
        print("="*80 + "\n")
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load all test modules
        for test_file in self.test_files:
            try:
                module = __import__(f"tests.{test_file}", fromlist=[test_file])
                module_tests = loader.loadTestsFromModule(module)
                suite.addTests(module_tests)
                if self.verbose:
                    print(f"✓ Loaded {test_file}")
            except Exception as e:
                print(f"✗ Failed to load {test_file}: {e}")
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=2 if self.verbose else 1,
            failfast=self.failfast
        )
        result = runner.run(suite)
        
        self.end_time = time.time()
        
        # Generate report
        self._generate_report(result)
        
        return result.wasSuccessful()
    
    def _generate_report(self, result: unittest.TestResult) -> None:
        """Generate comprehensive test report."""
        duration = self.end_time - self.start_time
        
        print("\n" + "="*80)
        print("TEST SUMMARY REPORT")
        print("="*80)
        
        # Statistics
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        passed = total_tests - failures - errors - skipped
        
        print(f"\nTotal Tests Run: {total_tests}")
        print(f"  ✓ Passed:  {passed} ({self._percentage(passed, total_tests)}%)")
        print(f"  ✗ Failed:  {failures} ({self._percentage(failures, total_tests)}%)")
        print(f"  ⚠ Errors:  {errors} ({self._percentage(errors, total_tests)}%)")
        print(f"  ⊘ Skipped: {skipped} ({self._percentage(skipped, total_tests)}%)")
        
        print(f"\nTotal Duration: {duration:.2f} seconds")
        print(f"Average per Test: {duration/total_tests:.3f} seconds")
        
        # Failures
        if result.failures:
            print("\n" + "-"*80)
            print("FAILURES")
            print("-"*80)
            for test, traceback in result.failures:
                print(f"\n✗ {test}")
                print(f"  {traceback[:500]}")
        
        # Errors
        if result.errors:
            print("\n" + "-"*80)
            print("ERRORS")
            print("-"*80)
            for test, traceback in result.errors:
                print(f"\n⚠ {test}")
                print(f"  {traceback[:500]}")
        
        # Skipped
        if result.skipped:
            print("\n" + "-"*80)
            print("SKIPPED")
            print("-"*80)
            for test, reason in result.skipped:
                print(f"\n⊘ {test}")
                print(f"  Reason: {reason}")
        
        # Final status
        print("\n" + "="*80)
        if result.wasSuccessful():
            print("✓ ALL TESTS PASSED!")
        else:
            print("✗ SOME TESTS FAILED")
        print("="*80 + "\n")
    
    @staticmethod
    def _percentage(value: int, total: int) -> int:
        """Calculate percentage."""
        return int((value / total * 100)) if total > 0 else 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Master Test Runner for Candy-Cadence"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--failfast", "-f",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    runner = MasterTestRunner(
        verbose=args.verbose,
        failfast=args.failfast
    )
    
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

