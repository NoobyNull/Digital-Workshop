# Test Plan: Unified Test Execution

**Date**: 2025-10-31 | **Status**: Ready for Implementation | **Phase**: Phase 1

## Objective

Create a unified test execution system that runs all available tests as one comprehensive test suite, providing centralized reporting, parallel execution, and integration with CI/CD pipelines for complete application validation.

## Approach

### Technical Implementation Strategy

1. **Pytest Configuration**: Leverage pytest's powerful test discovery and configuration system
2. **Parallel Execution**: Use pytest-xdist for concurrent test execution across multiple cores
3. **Test Discovery**: Implement intelligent test discovery that automatically finds and categorizes tests
4. **Unified Reporting**: Generate comprehensive reports combining all test categories
5. **Integration with Data Model**: Map results to TestSuite and TestExecution entities

### Tools and Libraries

- **pytest**: Primary testing framework with extensive plugin ecosystem
- **pytest-xdist**: For parallel test execution
- **pytest-cov**: For coverage reporting
- **pytest-html**: For HTML report generation
- **pytest-json-report**: For JSON report generation
- **pytest-timeout**: For test timeout management
- **pytest-mock**: For mocking support
- **allure-pytest**: For advanced reporting (optional)

## Test Cases

### Test Case 1: Basic Test Discovery
**Objective**: Verify that all tests are discovered and can be executed

**Setup**:
```python
# Create test files in various locations
tests/test_basic_functionality.py
tests/unit/test_parsers.py
tests/integration/test_workflows.py
tests/performance/test_benchmarks.py
src/tests/test_core_modules.py
```

**Expected Results**:
- All test files discovered automatically
- Tests categorized by type (unit, integration, performance)
- Total test count matches expected number

### Test Case 2: Parallel Execution Performance
**Objective**: Validate parallel execution efficiency and correctness

**Setup**:
- Create 100+ test cases across multiple categories
- Run with different worker counts (1, 2, 4, 8)
- Measure execution time and resource usage

**Expected Results**:
- Linear speedup with worker count (up to CPU cores)
- No test interference or race conditions
- Consistent results across multiple runs

### Test Case 3: Test Categorization and Filtering
**Objective**: Ensure tests can be filtered and categorized correctly

**Setup**:
```python
# Mark tests with categories
@pytest.mark.unit
def test_parser_functionality():
    pass

@pytest.mark.integration
def test_workflow_integration():
    pass

@pytest.mark.performance
def test_load_performance():
    pass

@pytest.mark.slow
def test_large_dataset():
    pass
```

**Expected Results**:
- Tests can be filtered by markers
- Category-specific test suites work correctly
- Fast/slow test separation functions properly

### Test Case 4: Coverage Integration
**Objective**: Verify comprehensive coverage reporting across all test types

**Setup**:
- Run all tests with coverage enabled
- Include all source directories
- Generate coverage reports

**Expected Results**:
- Overall coverage > 80%
- Per-module coverage breakdown
- Coverage reports in multiple formats (HTML, XML, JSON)

### Test Case 5: Failure Handling and Reporting
**Objective**: Ensure robust failure handling and detailed reporting

**Setup**:
- Create tests with various failure types (assertion errors, exceptions, timeouts)
- Include both expected and unexpected failures

**Expected Results**:
- Detailed failure messages with context
- Stack traces preserved
- Test execution continues after non-critical failures
- Comprehensive failure summary in reports

## Implementation Code

### Core Unified Test Runner

```python
#!/usr/bin/env python3
"""
Unified Test Execution System

Provides centralized test execution, reporting, and analysis
for comprehensive application validation.
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pytest
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestSuiteConfig:
    """Configuration for a test suite."""
    name: str
    description: str
    test_paths: List[str]
    markers: List[str]
    timeout: Optional[int] = None
    parallel_workers: Optional[int] = None
    coverage_target: Optional[float] = None
    enabled: bool = True

@dataclass
class TestExecutionResult:
    """Results from test execution."""
    suite_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    coverage_percentage: Optional[float]
    exit_code: int
    report_path: str
    log_path: str

class UnifiedTestRunner:
    """Main runner for unified test execution."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("unified_test_config.json")
        self.test_suites = self._load_test_suites()
        self.results: List[TestExecutionResult] = []
        
    def _load_test_suites(self) -> List[TestSuiteConfig]:
        """Load test suite configurations."""
        default_suites = [
            TestSuiteConfig(
                name="unit_tests",
                description="Unit tests for individual components",
                test_paths=["tests/unit/", "src/**/test_*.py"],
                markers=["unit", "not slow"],
                timeout=300,
                parallel_workers=4,
                coverage_target=90.0
            ),
            TestSuiteConfig(
                name="integration_tests",
                description="Integration tests for component interactions",
                test_paths=["tests/integration/", "tests/test_*_integration.py"],
                markers=["integration"],
                timeout=600,
                parallel_workers=2,
                coverage_target=80.0
            ),
            TestSuiteConfig(
                name="performance_tests",
                description="Performance and load tests",
                test_paths=["tests/performance/", "tests/test_*_performance.py"],
                markers=["performance", "benchmark"],
                timeout=1200,
                parallel_workers=1,
                coverage_target=None
            ),
            TestSuiteConfig(
                name="e2e_tests",
                description="End-to-end workflow tests",
                test_paths=["tests/e2e/", "tests/test_*_workflow.py"],
                markers=["e2e", "workflow"],
                timeout=900,
                parallel_workers=1,
                coverage_target=70.0
            ),
            TestSuiteConfig(
                name="quality_tests",
                description="Code quality and linting tests",
                test_paths=["tests/quality/", "tests/test_*_quality.py"],
                markers=["quality", "lint", "format"],
                timeout=300,
                parallel_workers=2,
                coverage_target=None
            )
        ]
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                # Load custom configurations (implementation would parse JSON)
                return default_suites  # For now, return defaults
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        
        return default_suites
    
    def run_test_suite(self, suite: TestSuiteConfig) -> TestExecutionResult:
        """
        Execute a single test suite.
        
        Args:
            suite: TestSuiteConfig to execute
            
        Returns:
            TestExecutionResult with execution details
        """
        if not suite.enabled:
            logger.info(f"Skipping disabled suite: {suite.name}")
            return TestExecutionResult(
                suite_name=suite.name,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=0.0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=None,
                exit_code=0,
                report_path="",
                log_path=""
            )
        
        logger.info(f"Starting test suite: {suite.name}")
        start_time = time.time()
        
        # Prepare output paths
        reports_dir = Path("reports/unified_tests")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / f"{suite.name}_report.html"
        json_report_path = reports_dir / f"{suite.name}_report.json"
        log_path = reports_dir / f"{suite.name}.log"
        coverage_path = reports_dir / f"{suite.name}_coverage.xml"
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            "--verbose",
            "--tb=short",
            f"--html={report_path}",
            f"--json-report", f"--json-report-file={json_report_path}",
            f"--cov-report=xml:{coverage_path}",
            f"--cov-report=html:{reports_dir}/{suite.name}_coverage_html",
            f"--junit-xml={reports_dir}/{suite.name}_junit.xml",
            f"--log-file={log_path}",
            f"--log-level=INFO"
        ]
        
        # Add test paths
        cmd.extend(suite.test_paths)
        
        # Add markers if specified
        if suite.markers:
            marker_expr = " and ".join(suite.markers)
            cmd.extend(["-m", marker_expr])
        
        # Add timeout
        if suite.timeout:
            cmd.extend(["--timeout", str(suite.timeout)])
        
        # Add parallel execution
        if suite.parallel_workers and suite.parallel_workers > 1:
            cmd.extend(["-n", str(suite.parallel_workers)])
        
        # Add coverage if target specified
        if suite.coverage_target:
            cmd.extend(["--cov=src", "--cov-fail-under", str(suite.coverage_target)])
        
        # Execute tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite.timeout or 3600  # Default 1 hour timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results from JSON report
            coverage_percentage = None
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                    
                    summary = json_report.get('summary', {})
                    total_tests = summary.get('total', 0)
                    passed_tests = summary.get('passed', 0)
                    failed_tests = summary.get('failed', 0)
                    skipped_tests = summary.get('skipped', 0)
                    error_tests = summary.get('error', 0)
                    
                    # Extract coverage from pytest-cov output
                    if coverage_path.exists():
                        # Parse XML coverage report
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(coverage_path)
                        root = tree.getroot()
                        coverage_percentage = float(root.attrib.get('line-rate', 0)) * 100
                    
                except Exception as e:
                    logger.warning(f"Failed to parse JSON report: {e}")
                    # Fallback to basic parsing
                    total_tests = passed_tests = failed_tests = skipped_tests = error_tests = 0
            
            return TestExecutionResult(
                suite_name=suite.name,
                start_time=datetime.fromtimestamp(start_time).isoformat(),
                end_time=datetime.fromtimestamp(end_time).isoformat(),
                duration_seconds=duration,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                error_tests=error_tests,
                coverage_percentage=coverage_percentage,
                exit_code=result.returncode,
                report_path=str(report_path),
                log_path=str(log_path)
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite.name} timed out after {suite.timeout} seconds")
            return TestExecutionResult(
                suite_name=suite.name,
                start_time=datetime.fromtimestamp(start_time).isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=suite.timeout,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=None,
                exit_code=124,  # Timeout exit code
                report_path=str(report_path),
                log_path=str(log_path)
            )
        except Exception as e:
            logger.error(f"Failed to execute test suite {suite.name}: {e}")
            return TestExecutionResult(
                suite_name=suite.name,
                start_time=datetime.fromtimestamp(start_time).isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=None,
                exit_code=1,
                report_path=str(report_path),
                log_path=str(log_path)
            )
    
    def run_all_tests(self, parallel_suites: bool = False) -> List[TestExecutionResult]:
        """
        Execute all test suites.
        
        Args:
            parallel_suites: Whether to run suites in parallel
            
        Returns:
            List of TestExecutionResult objects
        """
        logger.info(f"Starting unified test execution with {len(self.test_suites)} suites")
        
        if parallel_suites:
            # Run suites in parallel (advanced implementation would use ThreadPoolExecutor)
            results = []
            for suite in self.test_suites:
                result = self.run_test_suite(suite)
                results.append(result)
        else:
            # Run suites sequentially
            results = []
            for suite in self.test_suites:
                result = self.run_test_suite(suite)
                results.append(result)
        
        self.results = results
        return results
    
    def generate_unified_report(self, results: List[TestExecutionResult]) -> Dict[str, Any]:
        """
        Generate a comprehensive report combining all test results.
        
        Args:
            results: List of TestExecutionResult objects
            
        Returns:
            Dictionary containing the unified report
        """
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        total_skipped = sum(r.skipped_tests for r in results)
        total_errors = sum(r.error_tests for r in results)
        total_duration = sum(r.duration_seconds for r in results)
        
        # Calculate overall success rate
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate average coverage
        coverage_values = [r.coverage_percentage for r in results if r.coverage_percentage is not None]
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else None
        
        # Identify failed suites
        failed_suites = [r for r in results if r.exit_code != 0]
        
        report = {
            'summary': {
                'total_suites': len(results),
                'successful_suites': len(results) - len(failed_suites),
                'failed_suites': len(failed_suites),
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_skipped': total_skipped,
                'total_errors': total_errors,
                'success_rate': success_rate,
                'total_duration_seconds': total_duration,
                'average_coverage': avg_coverage,
                'execution_timestamp': datetime.now().isoformat()
            },
            'suite_results': [asdict(result) for result in results],
            'failed_suites': [
                {
                    'name': result.suite_name,
                    'exit_code': result.exit_code,
                    'failed_tests': result.failed_tests,
                    'error_tests': result.error_tests,
                    'duration': result.duration_seconds
                }
                for result in failed_suites
            ],
            'recommendations': self._generate_recommendations(results),
            'quality_gates': self._evaluate_quality_gates(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: List[TestExecutionResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        total_tests = sum(r.total_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        
        if total_failed == 0:
            recommendations.append("All tests passed! Excellent work maintaining code quality.")
        else:
            recommendations.append(f"Found {total_failed} failing tests that need attention.")
            
            # Analyze failure patterns
            failed_suites = [r for r in results if r.failed_tests > 0]
            if len(failed_suites) > len(results) * 0.5:
                recommendations.append("More than half of test suites have failures. Consider systematic fixes.")
            
            # Check for timeout issues
            timeout_suites = [r for r in results if r.exit_code == 124]
            if timeout_suites:
                recommendations.append("Some tests are timing out. Consider optimizing slow tests or increasing timeouts.")
        
        # Coverage recommendations
        coverage_values = [r.coverage_percentage for r in results if r.coverage_percentage is not None]
        if coverage_values:
            avg_coverage = sum(coverage_values) / len(coverage_values)
            if avg_coverage < 80:
                recommendations.append(f"Average coverage {avg_coverage:.1f}% is below 80%. Add more tests.")
            elif avg_coverage < 90:
                recommendations.append(f"Average coverage {avg_coverage:.1f}% could be improved to 90%.")
        
        return recommendations
    
    def _evaluate_quality_gates(self, results: List[TestExecutionResult]) -> List[Dict[str, Any]]:
        """Evaluate quality gates based on test results."""
        gates = []
        
        # Success rate gate
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        gates.append({
            'name': 'test_success_rate',
            'threshold': 95.0,
            'actual': success_rate,
            'passed': success_rate >= 95.0,
            'severity': 'critical' if success_rate < 90 else 'major'
        })
        
        # Coverage gate
        coverage_values = [r.coverage_percentage for r in results if r.coverage_percentage is not None]
        if coverage_values:
            avg_coverage = sum(coverage_values) / len(coverage_values)
            gates.append({
                'name': 'test_coverage',
                'threshold': 80.0,
                'actual': avg_coverage,
                'passed': avg_coverage >= 80.0,
                'severity': 'major' if avg_coverage < 70 else 'minor'
            })
        
        # Execution time gate
        total_duration = sum(r.duration_seconds for r in results)
        max_duration = 1800  # 30 minutes
        gates.append({
            'name': 'execution_time',
            'threshold': max_duration,
            'actual': total_duration,
            'passed': total_duration <= max_duration,
            'severity': 'minor'
        })
        
        return gates
    
    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save unified report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Unified report saved to {output_path}")

def main():
    """Main entry point for unified test execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run unified test execution across all test suites'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='unified_test_config.json',
        help='Path to test configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports/unified_test_report.json',
        help='Output report file path'
    )
    parser.add_argument(
        '--parallel-suites',
        action='store_true',
        help='Run test suites in parallel'
    )
    parser.add_argument(
        '--suite',
        type=str,
        action='append',
        help='Specific suite to run (can be used multiple times)'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first suite failure'
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = UnifiedTestRunner(Path(args.config))
    
    # Filter suites if specified
    if args.suite:
        runner.test_suites = [s for s in runner.test_suites if s.name in args.suite]
    
    logger.info(f"Running {len(runner.test_suites)} test suites")
    
    # Execute tests
    results = runner.run_all_tests(parallel_suites=args.parallel_suites)
    
    # Generate and save report
    report = runner.generate_unified_report(results)
    runner.save_report(report, Path(args.output))
    
    # Print summary
    print(f"\n=== Unified Test Execution Summary ===")
    print(f"Suites executed: {report['summary']['total_suites']}")
    print(f"Successful suites: {report['summary']['successful_suites']}")
    print(f"Failed suites: {report['summary']['failed_suites']}")
    print(f"Total tests: {report['summary']['total_tests']}")
    print(f"Passed tests: {report['summary']['total_passed']}")
    print(f"Failed tests: {report['summary']['total_failed']}")
    print(f"Success rate: {report['summary']['success_rate']:.2f}%")
    print(f"Total duration: {report['summary']['total_duration_seconds']:.2f} seconds")
    
    if report['summary']['average_coverage']:
        print(f"Average coverage: {report['summary']['average_coverage']:.2f}%")
    
    if report['failed_suites']:
        print(f"\nFailed suites:")
        for suite in report['failed_suites']:
            print(f"  - {suite['name']}: {suite['failed_tests']} failures")
    
    # Check quality gates
    failed_gates = [g for g in report['quality_gates'] if not g['passed']]
    if failed_gates:
        print(f"\nQuality gate violations:")
        for gate in failed_gates:
            print(f"  - {gate['name']}: {gate['actual']:.2f} (threshold: {gate['threshold']})")
    
    # Return appropriate exit code
    overall_success = (
        report['summary']['failed_suites'] == 0 and
        all(gate['passed'] for gate in report['quality_gates'])
    )
    
    return 0 if overall_success else 1

if __name__ == '__main__':
    sys.exit(main())
```

### Pytest Configuration File

```ini
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:reports/coverage_html
    --cov-report=xml:reports/coverage.xml
    --junit-xml=reports/junit.xml
    --html=reports/pytest_report.html
    --self-contained-html

testpaths = tests src

python_files = test_*.py *_test.py

python_classes = Test*

python_functions = test_*

markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interactions
    performance: Performance and load tests
    e2e: End-to-end workflow tests
    quality: Code quality and linting tests
    slow: Tests that take longer than 5 seconds
    fast: Tests that complete quickly
    network: Tests that require network access
    database: Tests that require database access
    gui: Tests that require GUI components

filterwarnings =
    ignore::UserWarning
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

timeout = 300

log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

log_file = reports/pytest.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d %(funcName)s(): %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
```

## Success Criteria

### Functional Requirements
- [ ] Automatically discover and execute all tests in the codebase
- [ ] Support parallel execution across multiple CPU cores
- [ ] Generate comprehensive reports in multiple formats (HTML, JSON, XML)
- [ ] Provide detailed failure analysis and recommendations
- [ ] Support test categorization and filtering
- [ ] Integrate with coverage reporting tools

### Performance Requirements
- [ ] Execute typical test suite (< 500 tests) in under 10 minutes
- [ ] Parallel execution provides linear speedup up to CPU core count
- [ ] Memory usage stays below 1GB during execution
- [ ] Support test timeouts to prevent hanging

### Quality Requirements
- [ ] 100% test discovery accuracy (no missed or false tests)
- [ ] Consistent results across multiple execution runs
- [ ] Proper isolation between test suites
- [ ] Detailed error reporting with context

### Integration Requirements
- [ ] Generate TestSuite and TestExecution entities for data model
- [ ] Support CI/CD pipeline integration via exit codes
- [ ] Provide JSON output for programmatic consumption
- [ ] Integrate with QualityGate system for automated enforcement

## Integration

### CI/CD Pipeline Integration

```yaml
# .github/workflows/unified-tests.yml
name: Unified Test Execution

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unified-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-xdist pytest-cov pytest-html pytest-json-report
        pip install -r requirements.txt
    
    - name: Run Unified Tests
      run: |
        python tools/unified_test_runner.py \
          --output reports/unified_test_report.json \
          --parallel-suites
    
    - name: Upload Test Reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports-python-${{ matrix.python-version }}
        path: reports/
    
    - name: Check Test Results
      run: |
        python -c "
        import json
        with open('reports/unified_test_report.json') as f:
            report = json.load(f)
        
        success_rate = report['summary']['success_rate']
        if success_rate < 95.0:
            print(f'Test success rate {success_rate:.2f}% is below 95% threshold!')
            exit(1)
        print(f'Test success rate {success_rate:.2f}% meets threshold.')
        "
```

### Quality Gate Integration

```python
# Integration with QualityGate system
class UnifiedTestQualityGate:
    """Quality gate for unified test execution."""
    
    def __init__(self, min_success_rate: float = 95.0, min_coverage: float = 80.0):
        self.min_success_rate = min_success_rate
        self.min_coverage = min_coverage
        self.gate_id = "unified-tests"
    
    def evaluate(self, execution_results: List[TestExecutionResult]) -> QualityGateResult:
        """Evaluate if the test execution passes quality gates."""
        total_tests = sum(r.total_tests for r in execution_results)
        total_passed = sum(r.passed_tests for r in execution_results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        coverage_values = [r.coverage_percentage for r in execution_results if r.coverage_percentage is not None]
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0
        
        return QualityGateResult(
            gate_id=self.gate_id,
            passed=success_rate >= self.min_success_rate and avg_coverage >= self.min_coverage,
            violations=[],
            compliance_rate=min(success_rate, avg_coverage)
        )
```

### Test Report Aggregation

```python
def aggregate_test_reports(report_dir: Path) -> Dict[str, Any]:
    """Aggregate multiple test reports into a single comprehensive report."""
    reports = []
    
    for report_file in report_dir.glob("*_report.json"):
        try:
            with open(report_file) as f:
                reports.append(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load report {report_file}: {e}")
    
    # Combine and analyze reports
    combined = {
        'total_reports': len(reports),
        'execution_dates': [r.get('summary', {}).get('execution_timestamp') for r in reports],
        'success_rates': [r.get('summary', {}).get('success_rate', 0) for r in reports],
        'coverage_rates': [r.get('summary', {}).get('average_coverage', 0) for r in reports]
    }
    
    return combined
```

---

**Test Plan Status**: ✅ Complete  
**Ready for Implementation**: ✅ Yes  
**Next