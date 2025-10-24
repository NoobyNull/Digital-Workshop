#!/usr/bin/env python3
"""
Test Script for Phase 0 Tools

This script validates that all Phase 0 tools are working correctly and can
be used for the GUI Layout Refactoring project.

Usage:
    python tools/test_phase0_tools.py [options]

Options:
    --verbose    Enable verbose output
    --quick      Run quick validation tests only
"""

import os
import sys
import json
import subprocess
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Phase0ToolsTester:
    """
    Test suite for Phase 0 tools validation.
    """

    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.test_dir = Path("tests/phase0_validation")
        self.test_dir.mkdir(exist_ok=True)

        # Tools to test
        self.tools = [
            {
                'name': 'dependency_analysis',
                'script': 'tools/dependency_analysis.py',
                'test_args': ['--output', 'test_dependency.json', '--format', 'json'],
                'expected_outputs': ['test_dependency.json']
            },
            {
                'name': 'stylesheet_detector',
                'script': 'tools/stylesheet_detector.py',
                'test_args': ['--output', 'test_stylesheet.json', '--format', 'json', '--min-risk', 'low'],
                'expected_outputs': ['test_stylesheet.json']
            },
            {
                'name': 'migration_utils',
                'script': 'tools/migration_utils.py',
                'test_args': ['validate-migration', '--output', 'test_migration.json'],
                'expected_outputs': ['test_migration.json']
            }
        ]

    def run_tests(self) -> dict:
        """
        Run all validation tests.

        Returns:
            Test results summary
        """
        logger.info("Starting Phase 0 tools validation")

        results = {
            'total_tests': len(self.tools),
            'passed_tests': 0,
            'failed_tests': 0,
            'tool_results': {}
        }

        for tool in self.tools:
            try:
                logger.info(f"Testing {tool['name']}...")
                result = self._test_tool(tool)
                results['tool_results'][tool['name']] = result

                if result['success']:
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1

            except Exception as e:
                logger.error(f"Test failed for {tool['name']}: {e}")
                results['tool_results'][tool['name']] = {
                    'success': False,
                    'error': str(e)
                }
                results['failed_tests'] += 1

        # Generate test report
        self._generate_test_report(results)

        logger.info(f"Phase 0 tools validation complete: {results['passed_tests']}/{results['total_tests']} passed")
        return results

    def _test_tool(self, tool: dict) -> dict:
        """Test a specific tool."""
        result = {
            'success': False,
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'outputs_exist': [],
            'execution_time': 0
        }

        import time
        start_time = time.time()

        try:
            # Build command
            cmd = [sys.executable, tool['script']] + tool['test_args']

            # Run tool
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            result['returncode'] = process.returncode
            result['stdout'] = process.stdout
            result['stderr'] = process.stderr

            # Check if tool executed successfully
            if process.returncode == 0:
                result['success'] = True

                # Check if expected outputs exist
                for expected_output in tool['expected_outputs']:
                    output_path = self.test_dir / expected_output
                    if output_path.exists():
                        result['outputs_exist'].append(expected_output)
                    else:
                        result['success'] = False
                        result['error'] = f"Expected output not found: {expected_output}"

            else:
                result['error'] = f"Tool returned non-zero exit code: {process.returncode}"

        except subprocess.TimeoutExpired:
            result['error'] = "Tool execution timed out"
        except Exception as e:
            result['error'] = f"Tool execution failed: {e}"

        result['execution_time'] = time.time() - start_time
        return result

    def _generate_test_report(self, results: dict) -> None:
        """Generate test report."""
        report_path = self.test_dir / "phase0_tools_test_report.json"

        report = {
            'test_info': {
                'timestamp': self._get_timestamp(),
                'test_directory': str(self.test_dir),
                'verbose': self.verbose,
                'quick': self.quick
            },
            'results': results,
            'summary': {
                'success_rate': results['passed_tests'] / results['total_tests'] if results['total_tests'] > 0 else 0,
                'total_execution_time': sum(
                    tool_result.get('execution_time', 0)
                    for tool_result in results['tool_results'].values()
                )
            }
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary to console
        self._print_test_summary(results)

    def _print_test_summary(self, results: dict) -> None:
        """Print test summary to console."""
        print(f"\n{'='*60}")
        print("PHASE 0 TOOLS VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Total Tools: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Success Rate: {results['passed_tests'] / results['total_tests'] * 100:.1f}%")
        # Tool details
        print("\nTool Results:")
Tool Results:")
        for tool_name, tool_result in results['tool_results'].items():
            status = "✓ PASS" if tool_result['success'] else "✗ FAIL"
            print(f"  {tool_name}: {status} ({tool_result.get('execution_time', 0):.2f}s)")

            if not tool_result['success']:
                error = tool_result.get('error', 'Unknown error')
                print(f"    Error: {error}")

        print(f"\nTest Report: {self.test_dir}/phase0_tools_test_report.json")
        print(f"{'='*60}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point for Phase 0 tools testing."""

    import argparse

    parser = argparse.ArgumentParser(description='Phase 0 Tools Validation')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick validation tests only')

    args = parser.parse_args()

    # Run tests
    tester = Phase0ToolsTester(verbose=args.verbose, quick=args.quick)
    results = tester.run_tests()

    # Exit with appropriate code
    if results['failed_tests'] > 0:
        print(f"\n{results['failed_tests']} tools failed validation. Check the test report for details.")
        sys.exit(1)
    else:
        print("\nAll Phase 0 tools passed validation!")
        sys.exit(0)


if __name__ == '__main__':
    main()