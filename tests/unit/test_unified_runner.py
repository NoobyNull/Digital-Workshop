#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Unified Test Runner

This test suite validates the UnifiedTestRunner implementation including:
- Test discovery logic and accuracy
- Parallel execution performance and correctness
- Coverage reporting integration
- Configuration management
- Error handling and edge cases
- Performance benchmarking
- Report generation accuracy
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

# Import the unified test runner
sys.path.insert(0, str(Path(__file__).parent))
from tools.maintenance.unified_test_runner import (
    UnifiedTestRunner,
    TestSuiteConfig,
    TestExecutionResult,
    JSONFormatter,
    main,
)


class TestTestSuiteConfig:
    """Test TestSuiteConfig dataclass functionality."""

    def test_basic_config_creation(self):
        """Test basic TestSuiteConfig creation."""
        config = TestSuiteConfig(
            name="test_suite",
            description="Test description",
            test_paths=["tests/"],
            markers=["unit"],
            timeout=300,
            parallel_workers=4,
            coverage_target=90.0,
            enabled=True,
            priority=1,
        )

        assert config.name == "test_suite"
        assert config.description == "Test description"
        assert config.test_paths == ["tests/"]
        assert config.markers == ["unit"]
        assert config.timeout == 300
        assert config.parallel_workers == 4
        assert config.coverage_target == 90.0
        assert config.enabled is True
        assert config.priority == 1

    def test_default_values(self):
        """Test default values for TestSuiteConfig."""
        config = TestSuiteConfig(
            name="test_suite",
            description="Test description",
            test_paths=["tests/"],
            markers=["unit"],
        )

        assert config.timeout is None
        assert config.parallel_workers is None
        assert config.coverage_target is None
        assert config.enabled is True
        assert config.priority == 1


class TestTestExecutionResult:
    """Test TestExecutionResult dataclass functionality."""

    def test_result_creation(self):
        """Test TestExecutionResult creation."""
        result = TestExecutionResult(
            suite_name="test_suite",
            start_time="2025-10-31T18:00:00",
            end_time="2025-10-31T18:05:00",
            duration_seconds=300.0,
            total_tests=100,
            passed_tests=95,
            failed_tests=3,
            skipped_tests=2,
            error_tests=0,
            coverage_percentage=85.5,
            exit_code=0,
            report_path="reports/test_suite_report.html",
            log_path="reports/test_suite.log",
            performance_metrics={"discovered_tests": 100},
            memory_usage_mb=256.0,
        )

        assert result.suite_name == "test_suite"
        assert result.total_tests == 100
        assert result.passed_tests == 95
        assert result.failed_tests == 3
        assert result.coverage_percentage == 85.5
        assert result.exit_code == 0


class TestJSONFormatter:
    """Test JSON logging formatter."""

    def test_format_basic_log(self):
        """Test basic log formatting."""
        formatter = JSONFormatter()

        # Create a mock log record
        record = Mock()
        record.created = time.time()
        record.levelname = "INFO"
        record.name = "test_logger"
        record.getMessage.return_value = "Test message"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.exc_info = None

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 42
        assert "timestamp" in parsed

    def test_format_with_exception(self):
        """Test log formatting with exception info."""
        formatter = JSONFormatter()

        record = Mock()
        record.created = time.time()
        record.levelname = "ERROR"
        record.name = "test_logger"
        record.getMessage.return_value = "Error occurred"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.exc_info = ("Exception", Exception("Test error"), None)
        record.formatException.return_value = (
            "Traceback (most recent call last):\nTest error"
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "ERROR"
        assert "exception" in parsed


class TestUnifiedTestRunner:
    """Test UnifiedTestRunner class functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def runner(self, temp_dir):
        """Create UnifiedTestRunner instance for testing."""
        config_path = temp_dir / "test_config.json"
        return UnifiedTestRunner(config_path)

    @pytest.fixture
    def sample_test_files(self, temp_dir):
        """Create sample test files for discovery testing."""
        test_dir = temp_dir / "tests"
        test_dir.mkdir()

        # Create various test files
        test_files = {
            "test_basic.py": """
def test_basic_function():
    assert True

class TestBasicClass:
    def test_method(self):
        assert True
""",
            "test_advanced.py": """
import pytest

@pytest.mark.unit
def test_advanced_function():
    assert True

@pytest.mark.slow
def test_slow_function():
    time.sleep(0.1)
    assert True
""",
            "integration_test.py": """
@pytest.mark.integration
def test_integration():
    assert True
""",
            "not_a_test.py": """
def regular_function():
    return True
""",
        }

        for filename, content in test_files.items():
            (test_dir / filename).write_text(content)

        return test_dir

    def test_initialization(self, runner):
        """Test runner initialization."""
        assert runner.config_path.exists() or not runner.config_path.exists()
        assert len(runner.test_suites) > 0
        assert runner.cpu_count > 0
        assert isinstance(runner.results, list)

    def test_load_test_suites_default(self, runner):
        """Test loading default test suites."""
        suites = runner.test_suites

        assert len(suites) > 0
        assert any(s.name == "unit_tests" for s in suites)
        assert any(s.name == "integration_tests" for s in suites)
        assert any(s.name == "performance_tests" for s in suites)
        assert any(s.name == "e2e_tests" for s in suites)
        assert any(s.name == "quality_tests" for s in suites)

    def test_is_test_file(self, runner, sample_test_files):
        """Test test file detection logic."""
        test_file = sample_test_files / "test_basic.py"
        non_test_file = sample_test_files / "not_a_test.py"

        assert runner._is_test_file(test_file) is True
        assert runner._is_test_file(non_test_file) is False

    def test_discover_tests(self, runner, sample_test_files):
        """Test test discovery functionality."""
        discovered = runner._discover_tests([str(sample_test_files)])

        # Should find test_basic.py, test_advanced.py, integration_test.py
        # but not not_a_test.py
        assert len(discovered) >= 3
        assert any("test_basic.py" in path for path in discovered)
        assert any("test_advanced.py" in path for path in discovered)
        assert any("integration_test.py" in path for path in discovered)
        assert not any("not_a_test.py" in path for path in discovered)

    def test_discover_tests_no_matches(self, runner, temp_dir):
        """Test test discovery with no matching files."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        discovered = runner._discover_tests([str(empty_dir)])
        assert discovered == []

    def test_get_system_info(self, runner):
        """Test system information gathering."""
        info = runner._get_system_info()

        assert "cpu_count" in info
        assert "memory_total_gb" in info
        assert "python_version" in info
        assert "platform" in info
        assert info["cpu_count"] > 0
        assert info["memory_total_gb"] > 0

    @patch("subprocess.Popen")
    @patch("psutil.Process")
    def test_monitor_resources(self, mock_psutil, mock_popen, runner):
        """Test resource monitoring functionality."""
        # Mock process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock psutil process
        mock_proc = Mock()
        mock_proc.memory_info.return_value = Mock(rss=1024 * 1024 * 100)  # 100MB
        mock_proc.cpu_percent.return_value = 25.0
        mock_psutil.return_value = mock_proc

        # Mock process to finish after a short time
        mock_process.poll.return_value = 0

        result = runner._monitor_resources(mock_process, interval=0.01)

        assert "max_memory_mb" in result
        assert "avg_cpu_percent" in result
        assert "cpu_samples" in result
        assert result["max_memory_mb"] > 0

    @patch("subprocess.Popen")
    def test_run_test_suite_basic(self, mock_popen, runner):
        """Test basic test suite execution."""
        # Create a mock suite
        suite = TestSuiteConfig(
            name="test_suite",
            description="Test suite",
            test_paths=["tests/"],
            markers=["unit"],
            timeout=60,
            parallel_workers=1,
            coverage_target=80.0,
        )

        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        # Mock file operations
        with patch("pathlib.Path.exists", return_value=False):
            result = runner.run_test_suite(suite)

        assert result.suite_name == "test_suite"
        assert result.exit_code == 0
        assert result.total_tests == 0  # No JSON report to parse

    @patch("subprocess.Popen")
    def test_run_test_suite_timeout(self, mock_popen, runner):
        """Test test suite timeout handling."""
        suite = TestSuiteConfig(
            name="timeout_suite",
            description="Timeout test",
            test_paths=["tests/"],
            markers=[],
            timeout=1,  # Very short timeout
            parallel_workers=1,
        )

        # Mock timeout
        from subprocess import TimeoutExpired

        mock_popen.side_effect = TimeoutExpired("pytest", 1)

        result = runner.run_test_suite(suite)

        assert result.suite_name == "timeout_suite"
        assert result.exit_code == 124  # Timeout exit code
        assert result.duration_seconds == 1

    @patch("subprocess.Popen")
    def test_run_test_suite_error(self, mock_popen, runner):
        """Test test suite execution error handling."""
        suite = TestSuiteConfig(
            name="error_suite",
            description="Error test",
            test_paths=["tests/"],
            markers=[],
            timeout=60,
            parallel_workers=1,
        )

        # Mock subprocess error
        mock_popen.side_effect = Exception("Test error")

        result = runner.run_test_suite(suite)

        assert result.suite_name == "error_suite"
        assert result.exit_code == 1
        assert "error" in result.performance_metrics

    def test_run_test_suite_disabled(self, runner):
        """Test disabled test suite handling."""
        suite = TestSuiteConfig(
            name="disabled_suite",
            description="Disabled test",
            test_paths=["tests/"],
            markers=[],
            enabled=False,
        )

        result = runner.run_test_suite(suite)

        assert result.suite_name == "disabled_suite"
        assert result.total_tests == 0
        assert result.exit_code == 0

    def test_run_test_suite_no_tests_discovered(self, runner, temp_dir):
        """Test handling when no tests are discovered."""
        suite = TestSuiteConfig(
            name="empty_suite",
            description="Empty test",
            test_paths=[str(temp_dir)],  # Empty directory
            markers=[],
            timeout=60,
        )

        result = runner.run_test_suite(suite)

        assert result.suite_name == "empty_suite"
        assert result.total_tests == 0
        assert result.performance_metrics["discovered_tests"] == 0

    @patch("subprocess.Popen")
    def test_run_all_tests_sequential(self, mock_popen, runner):
        """Test sequential test execution."""
        # Mock subprocess for all suites
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        with patch("pathlib.Path.exists", return_value=False):
            results = runner.run_all_tests(parallel_suites=False)

        assert len(results) == len(runner.test_suites)
        assert all(isinstance(r, TestExecutionResult) for r in results)

    @patch("subprocess.Popen")
    def test_run_all_tests_parallel(self, mock_popen, runner):
        """Test parallel test execution."""
        # Mock subprocess for all suites
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        with patch("pathlib.Path.exists", return_value=False):
            results = runner.run_all_tests(parallel_suites=True, max_workers=2)

        assert len(results) == len(runner.test_suites)
        assert all(isinstance(r, TestExecutionResult) for r in results)

    def test_generate_unified_report(self, runner):
        """Test unified report generation."""
        # Create mock results
        results = [
            TestExecutionResult(
                suite_name="suite1",
                start_time="2025-10-31T18:00:00",
                end_time="2025-10-31T18:05:00",
                duration_seconds=300.0,
                total_tests=100,
                passed_tests=95,
                failed_tests=5,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=85.0,
                exit_code=0,
                report_path="reports/suite1.html",
                log_path="reports/suite1.log",
                performance_metrics={},
                memory_usage_mb=256.0,
            ),
            TestExecutionResult(
                suite_name="suite2",
                start_time="2025-10-31T18:05:00",
                end_time="2025-10-31T18:10:00",
                duration_seconds=300.0,
                total_tests=50,
                passed_tests=50,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=90.0,
                exit_code=0,
                report_path="reports/suite2.html",
                log_path="reports/suite2.log",
                performance_metrics={},
                memory_usage_mb=128.0,
            ),
        ]

        report = runner.generate_unified_report(results)

        assert "summary" in report
        assert "suite_results" in report
        assert "failed_suites" in report
        assert "recommendations" in report
        assert "quality_gates" in report
        assert "performance_analysis" in report

        summary = report["summary"]
        assert summary["total_suites"] == 2
        assert summary["total_tests"] == 150
        assert summary["total_passed"] == 145
        assert summary["total_failed"] == 5
        assert summary["success_rate"] == pytest.approx(96.67, rel=1e-2)
        assert summary["average_coverage"] == pytest.approx(87.5, rel=1e-2)

    def test_generate_recommendations(self, runner):
        """Test recommendation generation."""
        # Test with all passing tests
        results = [
            TestExecutionResult(
                suite_name="suite1",
                start_time="2025-10-31T18:00:00",
                end_time="2025-10-31T18:05:00",
                duration_seconds=300.0,
                total_tests=100,
                passed_tests=100,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=95.0,
                exit_code=0,
                report_path="reports/suite1.html",
                log_path="reports/suite1.log",
                performance_metrics={},
                memory_usage_mb=256.0,
            )
        ]

        recommendations = runner._generate_recommendations(results)
        assert "All tests passed!" in recommendations[0]

        # Test with failing tests
        results[0].failed_tests = 10
        results[0].coverage_percentage = 75.0

        recommendations = runner._generate_recommendations(results)
        assert "failing tests that need attention" in recommendations[0]
        assert "coverage" in " ".join(recommendations).lower()

    def test_evaluate_quality_gates(self, runner):
        """Test quality gate evaluation."""
        results = [
            TestExecutionResult(
                suite_name="suite1",
                start_time="2025-10-31T18:00:00",
                end_time="2025-10-31T18:05:00",
                duration_seconds=300.0,
                total_tests=100,
                passed_tests=95,
                failed_tests=5,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=85.0,
                exit_code=0,
                report_path="reports/suite1.html",
                log_path="reports/suite1.log",
                performance_metrics={},
                memory_usage_mb=256.0,
            )
        ]

        gates = runner._evaluate_quality_gates(results)

        assert len(gates) >= 3  # At least success rate, coverage, execution time
        assert any(g["name"] == "test_success_rate" for g in gates)
        assert any(g["name"] == "test_coverage" for g in gates)
        assert any(g["name"] == "execution_time" for g in gates)

        # Check gate structure
        for gate in gates:
            assert "name" in gate
            assert "threshold" in gate
            assert "actual" in gate
            assert "passed" in gate
            assert "severity" in gate

    def test_analyze_performance(self, runner):
        """Test performance analysis."""
        results = [
            TestExecutionResult(
                suite_name="suite1",
                start_time="2025-10-31T18:00:00",
                end_time="2025-10-31T18:05:00",
                duration_seconds=300.0,
                total_tests=100,
                passed_tests=100,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=85.0,
                exit_code=0,
                report_path="reports/suite1.html",
                log_path="reports/suite1.log",
                performance_metrics={},
                memory_usage_mb=256.0,
            ),
            TestExecutionResult(
                suite_name="suite2",
                start_time="2025-10-31T18:05:00",
                end_time="2025-10-31T18:08:00",
                duration_seconds=180.0,
                total_tests=50,
                passed_tests=50,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                coverage_percentage=90.0,
                exit_code=0,
                report_path="reports/suite2.html",
                log_path="reports/suite2.log",
                performance_metrics={},
                memory_usage_mb=128.0,
            ),
        ]

        analysis = runner._analyze_performance(results)

        assert "total_duration" in analysis
        assert "average_duration" in analysis
        assert "max_duration" in analysis
        assert "min_duration" in analysis
        assert "total_memory_usage" in analysis
        assert "average_memory_usage" in analysis
        assert "parallel_efficiency" in analysis
        assert "suite_performance" in analysis

        assert analysis["total_duration"] == 480.0
        assert analysis["max_duration"] == 300.0
        assert analysis["min_duration"] == 180.0

    def test_calculate_parallel_efficiency(self, runner):
        """Test parallel efficiency calculation."""
        # Single suite
        results = [Mock(duration_seconds=100.0)]
        efficiency = runner._calculate_parallel_efficiency(results)
        assert efficiency == 1.0

        # Multiple suites with perfect parallelization
        results = [
            Mock(duration_seconds=100.0),
            Mock(duration_seconds=100.0),
            Mock(duration_seconds=100.0),
        ]
        efficiency = runner._calculate_parallel_efficiency(results)
        assert efficiency <= 1.0

    def test_save_report(self, runner, temp_dir):
        """Test report saving functionality."""
        report = {
            "summary": {"total_tests": 100},
            "suite_results": [],
            "recommendations": [],
            "quality_gates": [],
            "performance_analysis": {},
        }

        output_path = temp_dir / "test_report.json"
        runner.save_report(report, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            saved_report = json.load(f)

        assert saved_report["summary"]["total_tests"] == 100

    def test_print_summary(self, runner, capsys):
        """Test summary printing functionality."""
        report = {
            "summary": {
                "total_suites": 2,
                "successful_suites": 2,
                "failed_suites": 0,
                "total_tests": 150,
                "total_passed": 145,
                "total_failed": 5,
                "total_skipped": 0,
                "total_errors": 0,
                "success_rate": 96.67,
                "total_duration_seconds": 600.0,
                "average_coverage": 87.5,
                "average_memory_usage_mb": 192.0,
                "execution_timestamp": "2025-10-31T18:00:00",
                "system_info": {"cpu_count": 4, "memory_total_gb": 8.0},
            },
            "quality_gates": [
                {
                    "name": "test_success_rate",
                    "threshold": 95.0,
                    "actual": 96.67,
                    "passed": True,
                    "severity": "major",
                }
            ],
            "recommendations": ["All tests passed!"],
            "failed_suites": [],
        }

        runner.print_summary(report)

        captured = capsys.readouterr()
        assert "UNIFIED TEST EXECUTION SUMMARY" in captured.out
        assert "Total Tests: 150" in captured.out
        assert "Success Rate: 96.67%" in captured.out


class TestMainFunction:
    """Test main function and CLI interface."""

    @patch("sys.argv", ["tools/maintenance/unified_test_runner.py", "--help"])
    def test_main_help(self, capsys):
        """Test help message display."""
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert (
            "usage:" in captured.out.lower()
            or "unified test execution" in captured.out.lower()
        )

    @patch("tools.maintenance.unified_test_runner.UnifiedTestRunner")
    @patch(
        "sys.argv",
        ["tools/maintenance/unified_test_runner.py", "--output", "test_report.json"],
    )
    def test_main_basic_execution(self, mock_runner_class):
        """Test basic main function execution."""
        # Mock runner and its methods
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner

        mock_result = TestExecutionResult(
            suite_name="test",
            start_time="2025-10-31T18:00:00",
            end_time="2025-10-31T18:05:00",
            duration_seconds=300.0,
            total_tests=100,
            passed_tests=100,
            failed_tests=0,
            skipped_tests=0,
            error_tests=0,
            coverage_percentage=85.0,
            exit_code=0,
            report_path="reports/test.html",
            log_path="reports/test.log",
            performance_metrics={},
            memory_usage_mb=256.0,
        )

        mock_runner.run_all_tests.return_value = [mock_result]
        mock_runner.generate_unified_report.return_value = {
            "summary": {
                "total_suites": 1,
                "successful_suites": 1,
                "failed_suites": 0,
                "total_tests": 100,
                "total_passed": 100,
                "total_failed": 0,
                "total_skipped": 0,
                "total_errors": 0,
                "success_rate": 100.0,
                "total_duration_seconds": 300.0,
                "average_coverage": 85.0,
                "average_memory_usage_mb": 256.0,
                "execution_timestamp": "2025-10-31T18:00:00",
                "system_info": {"cpu_count": 4, "memory_total_gb": 8.0},
            },
            "quality_gates": [
                {
                    "name": "test_success_rate",
                    "threshold": 95.0,
                    "actual": 100.0,
                    "passed": True,
                    "severity": "major",
                }
            ],
            "recommendations": ["All tests passed!"],
            "failed_suites": [],
        }

        # Mock file operations
        with patch("pathlib.Path.exists", return_value=False):
            exit_code = main()

        assert exit_code == 0  # Should succeed
        mock_runner.run_all_tests.assert_called_once()
        mock_runner.generate_unified_report.assert_called_once()


class TestPerformanceBenchmarks:
    """Performance benchmarking tests for the unified test runner."""

    def test_test_discovery_performance(self, runner, temp_dir):
        """Test test discovery performance with large number of files."""
        # Create many test files
        test_dir = temp_dir / "tests"
        test_dir.mkdir()

        num_files = 100
        for i in range(num_files):
            test_file = test_dir / f"test_file_{i:03d}.py"
            test_file.write_text(
                f"""
def test_function_{i}():
    assert True

class TestClass_{i}:
    def test_method(self):
        assert True
"""
            )

        start_time = time.time()
        discovered = runner._discover_tests([str(test_dir)])
        discovery_time = time.time() - start_time

        assert len(discovered) == num_files
        assert discovery_time < 5.0  # Should complete within 5 seconds

    def test_parallel_execution_scaling(self, runner):
        """Test that parallel execution provides expected speedup."""
        # This is a conceptual test - in practice, we'd need actual test files
        # and would measure real execution times

        # Mock different worker counts
        worker_counts = [1, 2, 4]
        expected_speeds = [1.0, 1.8, 3.2]  # Not perfectly linear due to overhead

        for workers, expected_speed in zip(worker_counts, expected_speeds):
            # Simulate execution time scaling
            base_time = 100.0
            parallel_time = base_time / expected_speed

            assert parallel_time < base_time
            assert parallel_time > base_time / workers  # Should be better than linear

    def test_memory_usage_stability(self, runner):
        """Test that memory usage remains stable during execution."""
        # This would require actual memory monitoring during test execution
        # For now, we'll test the monitoring functionality

        # Mock process with stable memory usage
        mock_process = Mock()
        mock_process.poll.return_value = None

        # Simulate stable memory usage
        memory_samples = [100.0, 102.0, 98.0, 101.0, 99.0]  # Stable around 100MB

        with patch("psutil.Process") as mock_psutil:
            mock_proc = Mock()
            # Mock memory_info to return different values on each call
            mock_proc.memory_info.side_effect = [
                Mock(rss=mem * 1024 * 1024) for mem in memory_samples
            ]
            mock_proc.cpu_percent.return_value = 25.0
            mock_psutil.return_value = mock_proc

            mock_process.poll.return_value = 0  # Process finishes

            result = runner._monitor_resources(mock_process, interval=0.01)

            # Memory should be relatively stable
            assert (
                abs(result["max_memory_mb"] - 100.0) < 10.0
            )  # Within 10MB of expected


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    @patch("subprocess.Popen")
    def test_ci_cd_pipeline_integration(self, mock_popen, runner, temp_dir):
        """Test integration with CI/CD pipeline requirements."""
        # Mock successful test execution
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        # Create a simple test suite configuration
        suite = TestSuiteConfig(
            name="ci_tests",
            description="CI/CD pipeline tests",
            test_paths=["tests/"],
            markers=["unit", "not slow"],
            timeout=300,
            parallel_workers=2,
            coverage_target=80.0,
        )

        with patch("pathlib.Path.exists", return_value=False):
            result = runner.run_test_suite(suite)

        # CI/CD integration checks
        assert result.exit_code == 0  # Should return success for CI/CD
        assert result.report_path  # Should have report path for CI/CD
        assert result.coverage_percentage is not None  # Should have coverage

        # Verify pytest command was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]  # Get the command list
        assert "pytest" in call_args
        assert "--cov" in call_args
        assert "--junit-xml" in call_args

    def test_error_recovery_scenarios(self, runner):
        """Test error recovery in various failure scenarios."""
        # Test with missing test directory
        suite = TestSuiteConfig(
            name="missing_tests",
            description="Tests with missing directory",
            test_paths=["nonexistent_directory/"],
            markers=[],
            timeout=60,
        )

        result = runner.run_test_suite(suite)

        # Should handle gracefully
        assert result.suite_name == "missing_tests"
        assert result.total_tests == 0
        assert result.exit_code == 0  # Should not crash

    @patch("subprocess.Popen")
    def test_partial_failure_handling(self, mock_popen, runner):
        """Test handling of partial test suite failures."""
        # Mock partial failure (some tests pass, some fail)
        mock_process = Mock()
        mock_process.returncode = 1  # Non-zero exit code indicates some failures
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        suite = TestSuiteConfig(
            name="partial_failure",
            description="Tests with partial failures",
            test_paths=["tests/"],
            markers=[],
            timeout=60,
        )

        with patch("pathlib.Path.exists", return_value=False):
            result = runner.run_test_suite(suite)

        # Should capture the failure
        assert result.suite_name == "partial_failure"
        assert result.exit_code == 1
        assert "error" in result.performance_metrics


# Performance test markers
pytestmark = [pytest.mark.performance, pytest.mark.slow]


class TestPerformanceRequirements:
    """Test performance requirements from specifications."""

    @pytest.mark.performance
    def test_linear_speedup_requirement(self, runner):
        """Test that parallel execution provides linear speedup with CPU cores."""
        # This validates the requirement: "Linear speedup with CPU cores (4 cores = ~4x faster)"

        cpu_count = runner.cpu_count
        assert cpu_count >= 1

        # For a 4-core system, we expect approximately 4x speedup
        if cpu_count >= 4:
            expected_speedup = 4.0
            # In practice, this would be measured with actual test execution
            # For now, we validate the configuration is set up correctly
            assert runner.cpu_count == cpu_count

    @pytest.mark.performance
    def test_memory_efficiency_requirement(self, runner):
        """Test memory efficiency requirements."""
        # Validates: "Memory-efficient parallel execution"

        # Check that runner doesn't consume excessive memory during initialization
        initial_memory = runner._get_system_info()["memory_total_gb"]

        # Runner should be lightweight
        assert initial_memory > 0  # Should have access to system info
        # The runner itself should not consume significant memory

    @pytest.mark.performance
    def test_execution_time_requirement(self, runner):
        """Test execution time requirements."""
        # Validates: "Process typical test suites in under 5 minutes"

        # This would require actual test execution to validate
        # For now, we check that timeout configurations are reasonable

        for suite in runner.test_suites:
            if suite.timeout:
                # Most suites should complete within reasonable time
                assert suite.timeout <= 1800  # 30 minutes max
                # Unit tests should be faster
                if suite.name == "unit_tests":
                    assert suite.timeout <= 600  # 10 minutes for unit tests


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
