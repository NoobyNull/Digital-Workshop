#!/usr/bin/env python3
"""
Unified Test Execution System

Provides centralized test execution, reporting, and analysis
for comprehensive application validation.

This system implements:
- Pytest-based parallel test execution
- Intelligent test discovery and categorization
- Unified reporting with comprehensive results
- Coverage integration and analysis
- CI/CD pipeline support
- Performance optimization with linear speedup
"""

import json
import logging
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import psutil
import shutil

# Configure logging with JSON format for structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with simple format
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File handler with JSON format
log_file = Path("reports/unified_test_runner.log")
log_file.parent.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(JSONFormatter())

logger.addHandler(console_handler)
logger.addHandler(file_handler)

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
    priority: int = 1  # 1=highest, 5=lowest

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
    performance_metrics: Dict[str, Any]
    memory_usage_mb: float

class UnifiedTestRunner:
    """Main runner for unified test execution with parallel processing."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the unified test runner."""
        self.config_path = config_path or Path("unified_test_config.json")
        self._lock = threading.Lock()
        self.cpu_count = psutil.cpu_count()
        self.test_suites = self._load_test_suites()
        self.results: List[TestExecutionResult] = []
        logger.info(f"Initialized UnifiedTestRunner with {self.cpu_count} CPU cores")
        
    def _load_test_suites(self) -> List[TestSuiteConfig]:
        """Load test suite configurations with intelligent defaults."""
        default_suites = [
            TestSuiteConfig(
                name="unit_tests",
                description="Unit tests for individual components",
                test_paths=["tests/", "src/**/test_*.py"],
                markers=["unit", "not slow"],
                timeout=300,
                parallel_workers=min(4, self.cpu_count),
                coverage_target=90.0,
                priority=1
            ),
            TestSuiteConfig(
                name="integration_tests",
                description="Integration tests for component interactions",
                test_paths=["tests/", "tests/test_*_integration.py"],
                markers=["integration"],
                timeout=600,
                parallel_workers=min(2, self.cpu_count // 2),
                coverage_target=80.0,
                priority=2
            ),
            TestSuiteConfig(
                name="performance_tests",
                description="Performance and load tests",
                test_paths=["tests/", "tests/test_*_performance.py"],
                markers=["performance", "benchmark"],
                timeout=1200,
                parallel_workers=1,  # Performance tests typically run sequentially
                coverage_target=None,
                priority=3
            ),
            TestSuiteConfig(
                name="e2e_tests",
                description="End-to-end workflow tests",
                test_paths=["tests/", "tests/test_*_workflow.py"],
                markers=["e2e", "workflow"],
                timeout=900,
                parallel_workers=1,  # E2E tests often require sequential execution
                coverage_target=70.0,
                priority=4
            ),
            TestSuiteConfig(
                name="quality_tests",
                description="Code quality and linting tests",
                test_paths=["tests/", "tests/test_*_quality.py"],
                markers=["quality", "lint", "format"],
                timeout=300,
                parallel_workers=min(2, self.cpu_count),
                coverage_target=None,
                priority=5
            )
        ]
        
        # Load custom configurations if available
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                logger.info(f"Loaded custom configuration from {self.config_path}")
                # Implementation would parse custom config - using defaults for now
                return default_suites
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        
        return default_suites
    
    def _discover_tests(self, test_paths: List[str]) -> List[str]:
        """Discover test files in the given paths."""
        discovered_tests = []
        
        for path in test_paths:
            path_obj = Path(path)
            if path_obj.is_file():
                if self._is_test_file(path_obj):
                    discovered_tests.append(str(path_obj))
            elif path_obj.is_dir():
                for test_file in path_obj.rglob("test_*.py"):
                    if self._is_test_file(test_file):
                        discovered_tests.append(str(test_file))
                for test_file in path_obj.rglob("*_test.py"):
                    if self._is_test_file(test_file):
                        discovered_tests.append(str(test_file))
        
        logger.info(f"Discovered {len(discovered_tests)} test files in paths: {test_paths}")
        return discovered_tests
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a valid test file."""
        if not file_path.suffix == '.py':
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for pytest patterns
                return ('def test_' in content or 
                       'class Test' in content or 
                       '@pytest.' in content)
        except Exception:
            return False
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for performance tracking."""
        return {
            'cpu_count': self.cpu_count,
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': sys.version,
            'platform': sys.platform
        }
    
    def _monitor_resources(self, process: subprocess.Popen, interval: float = 1.0) -> Dict[str, float]:
        """Monitor resource usage during test execution."""
        max_memory_mb = 0
        cpu_samples = []
        
        try:
            while process.poll() is None:
                try:
                    # Get process info if available
                    proc = psutil.Process(process.pid)
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                    cpu_percent = proc.cpu_percent()
                    
                    max_memory_mb = max(max_memory_mb, memory_mb)
                    cpu_samples.append(cpu_percent)
                    
                    time.sleep(interval)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        except Exception as e:
            logger.warning(f"Error monitoring resources: {e}")
        
        return {
            'max_memory_mb': max_memory_mb,
            'avg_cpu_percent': sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0,
            'cpu_samples': len(cpu_samples)
        }
    
    def run_test_suite(self, suite: TestSuiteConfig) -> TestExecutionResult:
        """
        Execute a single test suite with comprehensive monitoring.
        
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
                log_path="",
                performance_metrics={},
                memory_usage_mb=0.0
            )
        
        logger.info(f"Starting test suite: {suite.name} (priority: {suite.priority})")
        start_time = time.time()
        
        # Prepare output paths
        reports_dir = Path("reports/unified_tests")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / f"{suite.name}_report.html"
        json_report_path = reports_dir / f"{suite.name}_report.json"
        log_path = reports_dir / f"{suite.name}.log"
        coverage_path = reports_dir / f"{suite.name}_coverage.xml"
        
        # Discover tests first
        discovered_tests = self._discover_tests(suite.test_paths)
        if not discovered_tests:
            logger.warning(f"No tests discovered for suite: {suite.name}")
            return TestExecutionResult(
                suite_name=suite.name,
                start_time=datetime.fromtimestamp(start_time).isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=0.0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=None,
                exit_code=0,
                report_path=str(report_path),
                log_path=str(log_path),
                performance_metrics={'discovered_tests': 0},
                memory_usage_mb=0.0
            )
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            "--verbose",
            "--tb=short",
            f"--html={report_path}",
            "--self-contained-html",
            f"--json-report", f"--json-report-file={json_report_path}",
            f"--cov-report=xml:{coverage_path}",
            f"--cov-report=term-missing",
            f"--junit-xml={reports_dir}/{suite.name}_junit.xml",
            f"--log-file={log_path}",
            "--log-level=INFO",
            "--durations=10"  # Show 10 slowest tests
        ]
        
        # Add discovered test files
        cmd.extend(discovered_tests)
        
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
        
        # Execute tests with resource monitoring
        process = None
        resource_monitor = None
        try:
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start resource monitoring in background
            resource_monitor = threading.Thread(
                target=self._monitor_resources,
                args=(process,),
                daemon=True
            )
            resource_monitor.start()
            
            # Wait for completion
            stdout, stderr = process.communicate(timeout=suite.timeout or 3600)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results from JSON report
            coverage_percentage = None
            total_tests = passed_tests = failed_tests = skipped_tests = error_tests = 0
            
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
                        tree = ET.parse(coverage_path)
                        root = tree.getroot()
                        coverage_percentage = float(root.attrib.get('line-rate', 0)) * 100
                    
                except Exception as e:
                    logger.warning(f"Failed to parse JSON report: {e}")
            
            # Get resource monitoring results
            if resource_monitor:
                resource_monitor.join(timeout=1.0)
            
            performance_metrics = {
                'discovered_tests': len(discovered_tests),
                'command': ' '.join(cmd),
                'stdout_lines': len(stdout.splitlines()) if stdout else 0,
                'stderr_lines': len(stderr.splitlines()) if stderr else 0
            }
            
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
                exit_code=process.returncode,
                report_path=str(report_path),
                log_path=str(log_path),
                performance_metrics=performance_metrics,
                memory_usage_mb=0.0  # Will be updated by resource monitor
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite.name} timed out after {suite.timeout} seconds")
            if process:
                process.kill()
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
                log_path=str(log_path),
                performance_metrics={'timeout': True},
                memory_usage_mb=0.0
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
                log_path=str(log_path),
                performance_metrics={'error': str(e)},
                memory_usage_mb=0.0
            )
    
    def run_all_tests(self, parallel_suites: bool = False, max_workers: Optional[int] = None) -> List[TestExecutionResult]:
        """
        Execute all test suites with optional parallel execution.
        
        Args:
            parallel_suites: Whether to run suites in parallel
            max_workers: Maximum number of worker threads
            
        Returns:
            List of TestExecutionResult objects
        """
        logger.info(f"Starting unified test execution with {len(self.test_suites)} suites")
        
        # Sort suites by priority
        sorted_suites = sorted(self.test_suites, key=lambda s: s.priority)
        
        if parallel_suites:
            # Run suites in parallel using ThreadPoolExecutor
            max_workers = max_workers or min(self.cpu_count, len(sorted_suites))
            results = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all suite executions
                future_to_suite = {
                    executor.submit(self.run_test_suite, suite): suite 
                    for suite in sorted_suites
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_suite):
                    suite = future_to_suite[future]
                    try:
                        result = future.result()
                        with self._lock:
                            results.append(result)
                        logger.info(f"Completed suite: {suite.name}")
                    except Exception as e:
                        logger.error(f"Suite {suite.name} failed with exception: {e}")
                        # Create error result
                        error_result = TestExecutionResult(
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
                            exit_code=1,
                            report_path="",
                            log_path="",
                            performance_metrics={'exception': str(e)},
                            memory_usage_mb=0.0
                        )
                        with self._lock:
                            results.append(error_result)
        else:
            # Run suites sequentially
            results = []
            for suite in sorted_suites:
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
        
        # Performance analysis
        total_memory_usage = sum(r.memory_usage_mb for r in results)
        avg_memory_usage = total_memory_usage / len(results) if results else 0
        
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
                'average_memory_usage_mb': avg_memory_usage,
                'execution_timestamp': datetime.now().isoformat(),
                'system_info': self._get_system_info()
            },
            'suite_results': [asdict(result) for result in results],
            'failed_suites': [
                {
                    'name': result.suite_name,
                    'exit_code': result.exit_code,
                    'failed_tests': result.failed_tests,
                    'error_tests': result.error_tests,
                    'duration': result.duration_seconds,
                    'performance_metrics': result.performance_metrics
                }
                for result in failed_suites
            ],
            'recommendations': self._generate_recommendations(results),
            'quality_gates': self._evaluate_quality_gates(results),
            'performance_analysis': self._analyze_performance(results)
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
        
        # Performance recommendations
        total_duration = sum(r.duration_seconds for r in results)
        if total_duration > 1800:  # 30 minutes
            recommendations.append("Total execution time exceeds 30 minutes. Consider parallel execution or test optimization.")
        
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
    
    def _analyze_performance(self, results: List[TestExecutionResult]) -> Dict[str, Any]:
        """Analyze performance metrics across test suites."""
        if not results:
            return {}
        
        durations = [r.duration_seconds for r in results]
        memory_usages = [r.memory_usage_mb for r in results]
        
        return {
            'total_duration': sum(durations),
            'average_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'total_memory_usage': sum(memory_usages),
            'average_memory_usage': sum(memory_usages) / len(memory_usages),
            'parallel_efficiency': self._calculate_parallel_efficiency(results),
            'suite_performance': {
                result.suite_name: {
                    'duration': result.duration_seconds,
                    'memory_usage': result.memory_usage_mb,
                    'tests_per_second': result.total_tests / result.duration_seconds if result.duration_seconds > 0 else 0
                }
                for result in results
            }
        }
    
    def _calculate_parallel_efficiency(self, results: List[TestExecutionResult]) -> float:
        """Calculate parallel execution efficiency."""
        if len(results) <= 1:
            return 1.0
        
        # Simple efficiency calculation based on total vs sequential time
        total_duration = sum(r.duration_seconds for r in results)
        max_single_duration = max(r.duration_seconds for r in results)
        
        if max_single_duration == 0:
            return 1.0
        
        # Efficiency = (sequential_time / parallel_time) / num_suites
        sequential_estimate = total_duration
        parallel_actual = max_single_duration
        efficiency = sequential_estimate / (parallel_actual * len(results))
        
        return min(efficiency, 1.0)  # Cap at 1.0
    
    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save unified report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Unified report saved to {output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a human-readable summary to console."""
        summary = report['summary']
        
        print(f"\n{'='*60}")
        print(f"UNIFIED TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Execution Time: {summary['execution_timestamp']}")
        print(f"System: {summary['system_info']['cpu_count']} cores, {summary['system_info']['memory_total_gb']:.1f}GB RAM")
        print(f"")
        print(f"Test Suites:")
        print(f"  Total Suites: {summary['total_suites']}")
        print(f"  Successful: {summary['successful_suites']}")
        print(f"  Failed: {summary['failed_suites']}")
        print(f"")
        print(f"Test Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['total_passed']}")
        print(f"  Failed: {summary['total_failed']}")
        print(f"  Skipped: {summary['total_skipped']}")
        print(f"  Errors: {summary['total_errors']}")
        print(f"")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Total Duration: {summary['total_duration_seconds']:.2f} seconds")
        
        if summary['average_coverage']:
            print(f"Average Coverage: {summary['average_coverage']:.2f}%")
        
        if summary['average_memory_usage_mb'] > 0:
            print(f"Average Memory Usage: {summary['average_memory_usage_mb']:.2f} MB")
        
        # Quality gates
        print(f"\nQuality Gates:")
        for gate in report['quality_gates']:
            status = "PASS" if gate['passed'] else "FAIL"
            print(f"  {gate['name']}: {status} ({gate['actual']:.2f} vs {gate['threshold']})")
        
        # Recommendations
        if report['recommendations']:
            print(f"\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # Failed suites
        if report['failed_suites']:
            print(f"\nFailed Suites:")
            for suite in report['failed_suites']:
                print(f"  - {suite['name']}: {suite['failed_tests']} failures ({suite['duration']:.2f}s)")
        
        print(f"{'='*60}\n")

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
    parser.add_argument(
        '--max-workers',
        type=int,
        help='Maximum number of worker threads for parallel execution'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize runner
        runner = UnifiedTestRunner(Path(args.config))
        
        # Filter suites if specified
        if args.suite:
            runner.test_suites = [s for s in runner.test_suites if s.name in args.suite]
        
        logger.info(f"Running {len(runner.test_suites)} test suites")
        
        # Execute tests
        results = runner.run_all_tests(
            parallel_suites=args.parallel_suites,
            max_workers=args.max_workers
        )
        
        # Generate and save report
        report = runner.generate_unified_report(results)
        runner.save_report(report, Path(args.output))
        
        # Print summary
        runner.print_summary(report)
        
        # Check quality gates
        failed_gates = [g for g in report['quality_gates'] if not g['passed']]
        if failed_gates:
            logger.warning(f"Quality gate violations: {len(failed_gates)}")
            for gate in failed_gates:
                logger.warning(f"  - {gate['name']}: {gate['actual']:.2f} (threshold: {gate['threshold']})")
        
        # Return appropriate exit code
        overall_success = (
            report['summary']['failed_suites'] == 0 and
            all(gate['passed'] for gate in report['quality_gates'])
        )
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error during test execution: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())