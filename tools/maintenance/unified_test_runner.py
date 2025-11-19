"""Utility class for orchestrating pytest executions from CI or local workflows."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import psutil

# --------------------------------------------------------------------- models


@dataclass
class TestSuiteConfig:
    name: str
    description: str
    test_paths: List[str]
    markers: List[str]
    timeout: Optional[int] = None
    parallel_workers: Optional[int] = None
    coverage_target: Optional[float] = None
    enabled: bool = True
    priority: int = 1


@dataclass
class TestExecutionResult:
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
    performance_metrics: Dict[str, float]
    memory_usage_mb: float


class JSONFormatter:
    """Logging formatter that serializes records to JSON."""

    def format(self, record) -> str:  # pragma: no cover - trivial structure
        payload = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = record.formatException(record.exc_info)
        return json.dumps(payload)


# --------------------------------------------------------------------- runner


class UnifiedTestRunner:
    """High-level orchestration around pytest for CI and developer workflows."""

    def __init__(self, config_path: Optional[Path] = None, test_suites: Optional[List[TestSuiteConfig]] = None) -> None:
        import logging

        self.config_path = Path(config_path or "unified_runner_config.json")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.cpu_count = os.cpu_count() or 1
        self.logger = logging.getLogger("UnifiedTestRunner")
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.test_suites = test_suites or self._load_default_suites()
        self.results: List[TestExecutionResult] = []

    # --------------------------------------------------------------- utilities
    def _load_default_suites(self) -> List[TestSuiteConfig]:
        return [
            TestSuiteConfig(
                name="unit_tests",
                description="Fast local unit suite",
                test_paths=["tests/unit"],
                markers=["unit"],
                timeout=600,
                parallel_workers=1,
                coverage_target=85.0,
                priority=1,
            ),
            TestSuiteConfig(
                name="integration_tests",
                description="Integration flows",
                test_paths=["tests/integration"],
                markers=["integration"],
                timeout=1200,
                parallel_workers=2,
                coverage_target=75.0,
                priority=2,
            ),
            TestSuiteConfig(
                name="performance_tests",
                description="Performance benchmarks",
                test_paths=["tests/performance"],
                markers=["performance"],
                timeout=1800,
                parallel_workers=2,
                enabled=True,
                priority=3,
            ),
            TestSuiteConfig(
                name="e2e_tests",
                description="End-to-end validations",
                test_paths=["tests/e2e"],
                markers=["e2e"],
                timeout=1800,
                parallel_workers=2,
                enabled=True,
                priority=4,
            ),
            TestSuiteConfig(
                name="quality_tests",
                description="Linters and quality gates",
                test_paths=["tests/quality"],
                markers=["quality"],
                timeout=1200,
                parallel_workers=1,
                coverage_target=80.0,
                enabled=True,
                priority=5,
            ),
        ]

    # -------------------------------------------------------------------------
    def _is_test_file(self, path: Path) -> bool:
        name = path.name
        if path.suffix != ".py":
            return False
        if name.startswith("test_"):
            return True
        if name.endswith("_test.py"):
            stem = name[: -len("_test.py")]
            return "_" not in stem
        return False

    def _discover_tests(self, paths: Iterable[str]) -> List[str]:
        discovered: List[str] = []
        for entry in paths:
            base = Path(entry)
            if base.is_file() and self._is_test_file(base):
                discovered.append(str(base))
            elif base.is_dir():
                for candidate in base.rglob("*.py"):
                    if self._is_test_file(candidate):
                        discovered.append(str(candidate))
        return sorted(set(discovered))

    def _get_system_info(self) -> dict:
        virtual_mem = psutil.virtual_memory()
        return {
            "cpu_count": self.cpu_count,
            "memory_total_gb": round(virtual_mem.total / (1024**3), 2),
            "python_version": sys.version,
            "platform": platform.platform(),
        }

    def _monitor_resources(self, process: subprocess.Popen, interval: float = 0.25) -> dict:
        try:
            ps_proc = psutil.Process(getattr(process, "pid", None))
        except (psutil.Error, TypeError):
            return {"max_memory_mb": 0.0, "avg_cpu_percent": 0.0, "cpu_samples": 0}
        max_memory = 0.0
        cpu_samples: List[float] = []
        while True:
            if process.poll() is not None:
                try:
                    max_memory = max(max_memory, ps_proc.memory_info().rss / (1024 * 1024))
                except psutil.Error:
                    pass
                break
            try:
                mem = ps_proc.memory_info().rss / (1024 * 1024)
                max_memory = max(max_memory, mem)
                cpu_samples.append(ps_proc.cpu_percent(interval=interval))
            except psutil.Error:
                break
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
        return {"max_memory_mb": max_memory, "avg_cpu_percent": avg_cpu, "cpu_samples": len(cpu_samples)}

    def _build_report_paths(self, suite: TestSuiteConfig) -> Dict[str, Path]:
        reports_dir = self.config_path.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        junit = reports_dir / f"{suite.name}_junit.xml"
        return {"junit": junit, "log": reports_dir / f"{suite.name}.log"}

    def _build_pytest_command(self, suite: TestSuiteConfig, report_path: Path, discovered: Sequence[str]) -> List[str]:
        cmd = ["pytest", "-q"]
        if suite.markers:
            cmd.extend(["-m", " and ".join(suite.markers)])
        cmd.extend(discovered)
        cmd.extend(["--junit-xml", str(report_path)])
        if suite.coverage_target is not None:
            cmd.extend(["--cov", "src", "--cov-report=term"])
        return cmd

    def _parse_junit_results(self, report_path: Path) -> Dict[str, int]:
        if not report_path.exists():
            return {"total": 0, "failures": 0, "errors": 0, "skipped": 0}
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(report_path)
            root = tree.getroot()
            total = int(root.attrib.get("tests", 0))
            failures = int(root.attrib.get("failures", 0))
            errors = int(root.attrib.get("errors", 0))
            skipped = int(root.attrib.get("skipped", 0))
            return {"total": total, "failures": failures, "errors": errors, "skipped": skipped}
        except Exception:
            return {"total": 0, "failures": 0, "errors": 0, "skipped": 0}

    # --------------------------------------------------------------- execution
    def run_test_suite(self, suite: TestSuiteConfig) -> TestExecutionResult:
        start_time = datetime.utcnow()
        if not suite.enabled:
            return self._result_from_summary(
                suite,
                start_time,
                duration=0.0,
                exit_code=0,
                metrics={"discovered_tests": 0},
                stats={"total": 0, "failures": 0, "errors": 0, "skipped": 0},
                coverage=suite.coverage_target,
                memory=0.0,
            )

        discovered = self._discover_tests(suite.test_paths)
        if not discovered:
            return self._result_from_summary(
                suite,
                start_time,
                duration=0.0,
                exit_code=0,
                metrics={"discovered_tests": 0},
                stats={"total": 0, "failures": 0, "errors": 0, "skipped": 0},
                coverage=suite.coverage_target,
                memory=0.0,
            )

        report_paths = self._build_report_paths(suite)
        cmd = self._build_pytest_command(suite, report_paths["junit"], discovered)
        duration = 0.0
        metrics = {"discovered_tests": float(len(discovered))}
        memory_usage = 0.0
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            duration = float(exc.timeout or 0.0)
            return self._result_from_summary(
                suite,
                start_time,
                duration=duration,
                exit_code=124,
                metrics={"discovered_tests": float(len(discovered)), "error": "Launch timed out"},
                stats={"total": 0, "failures": 0, "errors": 0, "skipped": 0},
                coverage=suite.coverage_target,
                memory=0.0,
            )
        except Exception as exc:
            return self._result_from_summary(
                suite,
                start_time,
                duration=0.0,
                exit_code=1,
                metrics={"discovered_tests": float(len(discovered)), "error": str(exc)},
                stats={"total": 0, "failures": 0, "errors": 0, "skipped": 0},
                coverage=suite.coverage_target,
                memory=0.0,
            )

        monitor_info = self._monitor_resources(process)
        memory_usage = monitor_info.get("max_memory_mb", 0.0)
        metrics.update(monitor_info)
        timer_start = time.perf_counter()
        try:
            stdout, stderr = process.communicate(timeout=suite.timeout)
            self._write_log(report_paths["log"], stdout, stderr)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self._write_log(report_paths["log"], stdout, stderr)
            exit_code = 124

        duration = time.perf_counter() - timer_start
        stats = self._parse_junit_results(report_paths["junit"])
        coverage = suite.coverage_target if suite.coverage_target is not None else 0.0
        if exit_code != 0:
            metrics["error"] = f"Test suite exited with code {exit_code}"
        result = self._result_from_summary(
            suite,
            start_time,
            duration=duration,
            exit_code=exit_code,
            metrics=metrics,
            stats=stats,
            coverage=coverage,
            memory=memory_usage,
            report_path=report_paths["junit"],
            log_path=report_paths["log"],
        )
        self.results.append(result)
        return result

    def _result_from_summary(
        self,
        suite: TestSuiteConfig,
        start_time: datetime,
        *,
        duration: float,
        exit_code: int,
        metrics: Dict[str, float],
        stats: Dict[str, int],
        coverage: Optional[float],
        memory: float,
        report_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
    ) -> TestExecutionResult:
        total = stats.get("total", 0)
        failures = stats.get("failures", 0)
        errors = stats.get("errors", 0)
        skipped = stats.get("skipped", 0)
        passed = total - failures - errors - skipped
        return TestExecutionResult(
            suite_name=suite.name,
            start_time=start_time.isoformat(),
            end_time=datetime.utcnow().isoformat(),
            duration_seconds=duration,
            total_tests=total,
            passed_tests=max(0, passed),
            failed_tests=failures,
            skipped_tests=skipped,
            error_tests=errors,
            coverage_percentage=coverage,
            exit_code=exit_code,
            report_path=str(report_path or ""),
            log_path=str(log_path or ""),
            performance_metrics=metrics,
            memory_usage_mb=memory,
        )

    def _write_log(self, path: Path, stdout: str, stderr: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            if stdout:
                handle.write(stdout)
            if stderr:
                handle.write("\n")
                handle.write(stderr)

    # ------------------------------------------------------------- entrypoints
    def run_all_tests(self, parallel_suites: bool = False, max_workers: Optional[int] = None) -> List[TestExecutionResult]:
        suites = sorted(self.test_suites, key=lambda s: s.priority)
        if not parallel_suites:
            return [self.run_test_suite(suite) for suite in suites]

        results: List[TestExecutionResult] = []
        worker_count = max_workers or min(len(suites), self.cpu_count)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for result in executor.map(self.run_test_suite, suites):
                results.append(result)
        return results

    def generate_unified_report(self, results: Sequence[TestExecutionResult]) -> dict:
        summary = {
            "total_suites": len(results),
            "successful_suites": sum(1 for r in results if r.exit_code == 0),
            "failed_suites": sum(1 for r in results if r.exit_code != 0),
            "total_tests": sum(r.total_tests for r in results),
            "total_passed": sum(r.passed_tests for r in results),
            "total_failed": sum(r.failed_tests for r in results),
            "total_skipped": sum(r.skipped_tests for r in results),
            "total_errors": sum(r.error_tests for r in results),
            "success_rate": round(
                (sum(r.passed_tests for r in results) / max(1, sum(r.total_tests for r in results))) * 100, 2
            )
            if results
            else 100.0,
            "average_coverage": round(
                sum((r.coverage_percentage or 0) for r in results) / max(1, len(results)), 2
            )
            if results
            else 0.0,
            "total_duration_seconds": sum(r.duration_seconds for r in results),
            "average_memory_usage_mb": round(sum(r.memory_usage_mb for r in results) / max(1, len(results)), 2),
            "execution_timestamp": datetime.utcnow().isoformat(),
            "system_info": self._get_system_info(),
        }
        report = {
            "summary": summary,
            "suite_results": [asdict(r) for r in results],
            "failed_suites": [r.suite_name for r in results if r.exit_code != 0],
            "recommendations": self._generate_recommendations(results),
            "quality_gates": self._evaluate_quality_gates(results),
            "performance_analysis": self._analyze_performance(results),
        }
        return report

    def save_report(self, report: dict, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    def print_summary(self, report: dict) -> None:
        """Pretty-print a short summary for console diagnostics."""

        summary = report.get("summary", {})
        quality = report.get("quality_gates", [])
        recommendations = report.get("recommendations", [])

        lines = [
            "UNIFIED TEST EXECUTION SUMMARY",
            f" Suites: {summary.get('total_suites', 0)}",
            f" Success Rate: {summary.get('success_rate', 0):.2f}%",
            f" Total Tests: {summary.get('total_tests', 0)} "
            f"(passed: {summary.get('total_passed', 0)}, failed: {summary.get('total_failed', 0)})",
        ]

        if quality:
            passed = sum(1 for gate in quality if gate.get("passed"))
            lines.append(f" Quality gates passed: {passed}/{len(quality)}")

        if recommendations:
            lines.append(" Recommendations:")
            lines.extend(f"  - {rec}" for rec in recommendations)

        print("\n".join(lines))

    # ------------------------------------------------------ report subhelpers
    def _generate_recommendations(self, results: Sequence[TestExecutionResult]) -> List[str]:
        if not results:
            return ["No test suites executed."]
        failed = [r for r in results if r.exit_code != 0 or r.failed_tests or r.error_tests]
        if not failed:
            return ["All tests passed! Maintain current coverage and keep CI green."]
        recs = [f"{len(failed)} suites have failing tests that need attention."]
        if any((r.coverage_percentage or 0) < 80 for r in results):
            recs.append("Increase test coverage above 80% on critical suites.")
        return recs

    def _evaluate_quality_gates(self, results: Sequence[TestExecutionResult]) -> List[dict]:
        gates = []
        if not results:
            return gates
        total_tests = sum(r.total_tests for r in results)
        passed = sum(r.passed_tests for r in results)
        success_rate = (passed / total_tests * 100) if total_tests else 100.0
        gates.append(
            {
                "name": "test_success_rate",
                "threshold": 95.0,
                "actual": round(success_rate, 2),
                "passed": success_rate >= 95.0,
                "severity": "major",
            }
        )
        avg_coverage = (
            sum((r.coverage_percentage or 0) for r in results) / len(results) if results else 0.0
        )
        gates.append(
            {
                "name": "test_coverage",
                "threshold": 85.0,
                "actual": round(avg_coverage, 2),
                "passed": avg_coverage >= 85.0,
                "severity": "major",
            }
        )
        total_duration = sum(r.duration_seconds for r in results)
        gates.append(
            {
                "name": "execution_time",
                "threshold": 3600.0,
                "actual": round(total_duration, 2),
                "passed": total_duration <= 3600.0,
                "severity": "minor",
            }
        )
        return gates

    def _analyze_performance(self, results: Sequence[TestExecutionResult]) -> dict:
        if not results:
            return {
                "total_duration": 0.0,
                "average_duration": 0.0,
                "max_duration": 0.0,
                "min_duration": 0.0,
                "total_memory_usage": 0.0,
                "average_memory_usage": 0.0,
                "parallel_efficiency": 1.0,
                "suite_performance": [],
            }
        durations = [r.duration_seconds for r in results]
        memory = [r.memory_usage_mb for r in results]
        return {
            "total_duration": sum(durations),
            "average_duration": sum(durations) / len(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "total_memory_usage": sum(memory),
            "average_memory_usage": sum(memory) / len(memory),
            "parallel_efficiency": self._calculate_parallel_efficiency(results),
            "suite_performance": [
                {"suite": r.suite_name, "duration": r.duration_seconds, "memory_mb": r.memory_usage_mb}
                for r in results
            ],
        }

    def _calculate_parallel_efficiency(self, results: Sequence[TestExecutionResult]) -> float:
        if not results:
            return 1.0
        if len(results) == 1:
            return 1.0
        total_sequential_time = sum(r.duration_seconds for r in results)
        longest = max(r.duration_seconds for r in results)
        efficiency = total_sequential_time / (longest * len(results))
        return round(efficiency, 2)


# --------------------------------------------------------------------- cli


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Unified pytest runner")
    parser.add_argument("--output", type=str, default="unified_test_report.json", help="Report file path")
    parser.add_argument("--parallel", action="store_true", help="Run suites in parallel")
    args = parser.parse_args(list(argv) if argv is not None else None)

    runner = UnifiedTestRunner()
    results = runner.run_all_tests(parallel_suites=args.parallel)
    report = runner.generate_unified_report(results)
    runner.save_report(report, Path(args.output))
    return 0 if all(result.exit_code == 0 for result in results) else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
