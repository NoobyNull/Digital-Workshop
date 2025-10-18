#!/usr/bin/env python
"""
Enhanced Master Test Runner with Detailed Reporting

Runs all tests and generates:
- Console output with color-coded results
- JSON report for CI/CD integration
- HTML report for visual inspection
- Performance metrics

Usage:
    python run_all_tests_detailed.py                    # Run all tests
    python run_all_tests_detailed.py --json report.json # Save JSON report
    python run_all_tests_detailed.py --html report.html # Generate HTML report
"""

import sys
import os
import unittest
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class ColorCodes:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class DetailedTestRunner:
    """Enhanced test runner with detailed reporting."""
    
    def __init__(self):
        self.results = defaultdict(list)
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
    
    def run_all_tests(self) -> Tuple[bool, Dict]:
        """Run all tests and return success status and results."""
        self.start_time = time.time()
        
        self._print_header()
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load all test modules
        loaded_count = 0
        for test_file in self.test_files:
            try:
                module = __import__(f"tests.{test_file}", fromlist=[test_file])
                module_tests = loader.loadTestsFromModule(module)
                suite.addTests(module_tests)
                loaded_count += 1
                print(f"{ColorCodes.GREEN}✓{ColorCodes.RESET} Loaded {test_file}")
            except Exception as e:
                print(f"{ColorCodes.RED}✗{ColorCodes.RESET} Failed to load {test_file}: {str(e)[:50]}")
        
        print(f"\n{ColorCodes.BLUE}Running {suite.countTestCases()} tests...{ColorCodes.RESET}\n")
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.end_time = time.time()
        
        # Generate reports
        report = self._generate_report(result)
        
        return result.wasSuccessful(), report
    
    def _print_header(self) -> None:
        """Print header."""
        print("\n" + "="*80)
        print(f"{ColorCodes.BOLD}CANDY-CADENCE MASTER TEST SUITE{ColorCodes.RESET}")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Test Files: {len(self.test_files)}")
        print("="*80 + "\n")
    
    def _generate_report(self, result: unittest.TestResult) -> Dict:
        """Generate comprehensive report."""
        duration = self.end_time - self.start_time
        
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        passed = total_tests - failures - errors - skipped
        
        # Print summary
        print("\n" + "="*80)
        print(f"{ColorCodes.BOLD}TEST SUMMARY{ColorCodes.RESET}")
        print("="*80)
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"  {ColorCodes.GREEN}✓ Passed:  {passed}{ColorCodes.RESET} ({self._percentage(passed, total_tests)}%)")
        print(f"  {ColorCodes.RED}✗ Failed:  {failures}{ColorCodes.RESET} ({self._percentage(failures, total_tests)}%)")
        print(f"  {ColorCodes.YELLOW}⚠ Errors:  {errors}{ColorCodes.RESET} ({self._percentage(errors, total_tests)}%)")
        print(f"  {ColorCodes.BLUE}⊘ Skipped: {skipped}{ColorCodes.RESET} ({self._percentage(skipped, total_tests)}%)")
        
        print(f"\nDuration: {duration:.2f}s (avg: {duration/total_tests:.3f}s per test)")
        
        # Print failures
        if result.failures:
            print("\n" + "-"*80)
            print(f"{ColorCodes.RED}FAILURES ({len(result.failures)}){ColorCodes.RESET}")
            print("-"*80)
            for test, traceback in result.failures:
                print(f"\n{ColorCodes.RED}✗ {test}{ColorCodes.RESET}")
                lines = traceback.split('\n')
                for line in lines[:10]:
                    print(f"  {line}")
                if len(lines) > 10:
                    print(f"  ... ({len(lines)-10} more lines)")
        
        # Print errors
        if result.errors:
            print("\n" + "-"*80)
            print(f"{ColorCodes.YELLOW}ERRORS ({len(result.errors)}){ColorCodes.RESET}")
            print("-"*80)
            for test, traceback in result.errors:
                print(f"\n{ColorCodes.YELLOW}⚠ {test}{ColorCodes.RESET}")
                lines = traceback.split('\n')
                for line in lines[:10]:
                    print(f"  {line}")
                if len(lines) > 10:
                    print(f"  ... ({len(lines)-10} more lines)")
        
        # Print skipped
        if result.skipped:
            print("\n" + "-"*80)
            print(f"{ColorCodes.BLUE}SKIPPED ({len(result.skipped)}){ColorCodes.RESET}")
            print("-"*80)
            for test, reason in result.skipped:
                print(f"\n{ColorCodes.BLUE}⊘ {test}{ColorCodes.RESET}")
                print(f"  Reason: {reason}")
        
        # Final status
        print("\n" + "="*80)
        if result.wasSuccessful():
            print(f"{ColorCodes.GREEN}{ColorCodes.BOLD}✓ ALL TESTS PASSED!{ColorCodes.RESET}")
        else:
            print(f"{ColorCodes.RED}{ColorCodes.BOLD}✗ SOME TESTS FAILED{ColorCodes.RESET}")
        print("="*80 + "\n")
        
        # Build report dict
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration": round(duration, 2),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "skipped": skipped,
            "success": result.wasSuccessful(),
            "failures": [
                {"test": str(test), "message": traceback[:200]}
                for test, traceback in result.failures
            ],
            "errors": [
                {"test": str(test), "message": traceback[:200]}
                for test, traceback in result.errors
            ],
            "skipped": [
                {"test": str(test), "reason": reason}
                for test, reason in result.skipped
            ]
        }
        
        return report
    
    def save_json_report(self, report: Dict, filename: str) -> None:
        """Save report as JSON."""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ JSON report saved to {filename}")
    
    def save_html_report(self, report: Dict, filename: str) -> None:
        """Save report as HTML."""
        html = self._generate_html(report)
        with open(filename, 'w') as f:
            f.write(html)
        print(f"✓ HTML report saved to {filename}")
    
    def _generate_html(self, report: Dict) -> str:
        """Generate HTML report."""
        passed_pct = int((report['passed'] / report['total_tests'] * 100)) if report['total_tests'] > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - Candy-Cadence</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #333; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .stat {{ display: inline-block; margin-right: 30px; }}
        .passed {{ color: green; font-weight: bold; }}
        .failed {{ color: red; font-weight: bold; }}
        .error {{ color: orange; font-weight: bold; }}
        .skipped {{ color: blue; font-weight: bold; }}
        .progress-bar {{ width: 100%; height: 30px; background: #ddd; border-radius: 5px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: green; width: {passed_pct}%; }}
        .details {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .test-item {{ padding: 10px; margin: 10px 0; border-left: 4px solid #ddd; }}
        .test-item.fail {{ border-left-color: red; }}
        .test-item.error {{ border-left-color: orange; }}
        .test-item.skip {{ border-left-color: blue; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Candy-Cadence Test Report</h1>
        <p>Generated: {report['timestamp']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stat"><span class="passed">{report['passed']}</span> Passed</div>
        <div class="stat"><span class="failed">{report['failed']}</span> Failed</div>
        <div class="stat"><span class="error">{report['errors']}</span> Errors</div>
        <div class="stat"><span class="skipped">{report['skipped']}</span> Skipped</div>
        <div class="stat">Total: {report['total_tests']}</div>
        <div class="stat">Duration: {report['duration']}s</div>
        
        <h3>Pass Rate</h3>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p>{passed_pct}% tests passed</p>
    </div>
    
    <div class="details">
        <h2>Status: {'✓ PASSED' if report['success'] else '✗ FAILED'}</h2>
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def _percentage(value: int, total: int) -> int:
        """Calculate percentage."""
        return int((value / total * 100)) if total > 0 else 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master Test Runner")
    parser.add_argument("--json", help="Save JSON report")
    parser.add_argument("--html", help="Save HTML report")
    
    args = parser.parse_args()
    
    runner = DetailedTestRunner()
    success, report = runner.run_all_tests()
    
    if args.json:
        runner.save_json_report(report, args.json)
    
    if args.html:
        runner.save_html_report(report, args.html)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

