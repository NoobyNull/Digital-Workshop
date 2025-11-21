"""Quality gate enforcement utilities used by the automated QA suite."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class JSONFormatter:
    """Lightweight JSON formatter for structured logging."""

    def format(self, record) -> str:  # pragma: no cover - simple serialization
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


@dataclass
class ToolResult:
    tool_name: str
    execution_time: float
    exit_code: int
    success: bool
    output_path: str
    raw_results: Dict
    metrics: Dict
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QualityGate:
    name: str
    description: str
    threshold: float
    operator: str
    severity: str
    auto_fix: bool = False
    enabled: bool = True


@dataclass
class QualityGateResult:
    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    severity: str
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class QualityGateEnforcer:
    """Coordinates external tooling and evaluates quality gates."""

    def __init__(
        self,
        config_path: Path,
        output_path: Optional[str] = None,
        parallel_execution: bool = False,
    ) -> None:
        self.config_path = Path(config_path)
        self.output_path = Path(output_path) if output_path else None
        self.parallel_execution = parallel_execution
        self.config = self._load_config()
        self.tools = self.config.get("tools", {})
        self.quality_gates = self.config.get("quality_gates", {})
        self.reporting = self.config.get("reporting", {})
        self.results: List[ToolResult] = []
        self.gate_results: List[QualityGateResult] = []

    # --------------------------------------------------------------------- load
    def _load_config(self) -> dict:
        config = self._default_config()
        if self.config_path.exists():
            try:
                loaded = yaml.safe_load(self.config_path.read_text()) or {}
                config.update(loaded)
            except yaml.YAMLError:
                pass
        return config

    @staticmethod
    def _default_config() -> dict:
        return {
            "quality_gates": {
                "code_quality": {
                    "name": "Code Quality",
                    "description": "Overall code quality compliance",
                    "threshold": 95.0,
                    "operator": ">=",
                    "severity": "major",
                    "auto_fix": False,
                    "enabled": True,
                },
                "monolithic_modules": {
                    "name": "Monolithic Modules",
                    "description": "Maximum allowed monolithic modules",
                    "threshold": 0,
                    "operator": "<=",
                    "severity": "major",
                    "auto_fix": False,
                    "enabled": True,
                },
                "naming_conventions": {
                    "name": "Naming Conventions",
                    "description": "Filename hygiene compliance",
                    "threshold": 90.0,
                    "operator": ">=",
                    "severity": "minor",
                    "auto_fix": False,
                    "enabled": True,
                },
                "test_execution": {
                    "name": "Test Execution",
                    "description": "Automated test success rate",
                    "threshold": 90.0,
                    "operator": ">=",
                    "severity": "critical",
                    "auto_fix": False,
                    "enabled": True,
                },
            },
            "tools": {
                "code_quality_validator": {
                    "command": "python",
                    "args": ["-m", "tools.maintenance.code_quality_validator"],
                    "enabled": False,
                },
                "monolithic_detector": {
                    "command": "python",
                    "args": ["-m", "tools.maintenance.monolithic_detector"],
                    "enabled": False,
                },
                "naming_validator": {
                    "command": "python",
                    "args": ["-m", "tools.maintenance.naming_validator"],
                    "enabled": False,
                },
                "unified_test_runner": {
                    "command": "python",
                    "args": ["-m", "tools.maintenance.unified_test_runner"],
                    "enabled": False,
                },
            },
            "reporting": {"formats": ["console"]},
        }

    # ---------------------------------------------------------------- utilities
    @staticmethod
    def _evaluate_condition(actual: float, threshold: float, operator: str) -> bool:
        if operator == ">=":
            return actual >= threshold
        if operator == "<=":
            return actual <= threshold
        if operator == "==":
            return actual == threshold
        if operator == "!=":
            return actual != threshold
        if operator == ">":
            return actual > threshold
        if operator == "<":
            return actual < threshold
        return False

    @staticmethod
    def _extract_code_quality_metrics(results: Dict) -> Dict:
        summary = results.get("summary", {})
        return {
            "overall_compliance": summary.get("compliance_percentage", 0.0),
            "formatting_score": summary.get("formatting_score", 0.0),
            "linting_score": summary.get("linting_score", 0.0),
            "total_issues": summary.get("total_issues", 0),
            "critical_issues": summary.get("critical_issues", 0),
            "major_issues": summary.get("major_issues", 0),
            "minor_issues": summary.get("minor_issues", 0),
        }

    @staticmethod
    def _extract_monolithic_metrics(results: Dict) -> Dict:
        summary = results.get("summary", {})
        return {
            "total_files_analyzed": summary.get("total_files_analyzed", 0),
            "monolithic_files_found": summary.get("monolithic_files_found", 0),
            "compliance_percentage": summary.get("compliance_percentage", 0.0),
            "average_lines_of_code": summary.get("average_lines_of_code", 0),
            "max_lines_of_code": summary.get("max_lines_of_code", 0),
        }

    @staticmethod
    def _extract_naming_metrics(results: Dict) -> Dict:
        summary = results.get("summary", {})
        return {
            "total_files_validated": summary.get("total_files_validated", 0),
            "violations_found": summary.get("violations_found", 0),
            "compliance_percentage": summary.get("compliance_percentage", 0.0),
            "adjective_violations": summary.get("adjective_violations", 0),
            "convention_violations": summary.get("convention_violations", 0),
        }

    @staticmethod
    def _extract_test_metrics(results: Dict) -> Dict:
        summary = results.get("summary", {})
        return {
            "total_tests": summary.get("total_tests", 0),
            "passed_tests": summary.get("passed_tests", 0),
            "failed_tests": summary.get("failed_tests", 0),
            "skipped_tests": summary.get("skipped_tests", 0),
            "success_rate": summary.get("success_rate", 0.0),
            "execution_time": summary.get("execution_time", 0.0),
        }

    # ---------------------------------------------------------------- execution
    def _execute_tool(self, tool_name: str, tool_config: Dict) -> ToolResult:
        command = [tool_config.get("command", "echo")]
        command.extend(tool_config.get("args", []))
        timeout = tool_config.get("timeout", 60)
        output_pattern = tool_config.get("output_pattern", "")
        start = time.perf_counter()
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
        except Exception as exc:  # pragma: no cover - defensive
            duration = time.perf_counter() - start
            return ToolResult(
                tool_name=tool_name,
                execution_time=duration,
                exit_code=1,
                success=False,
                output_path="",
                raw_results={"error": str(exc)},
                metrics={},
                violations=[],
                recommendations=[f"{tool_name} failed: {exc}"],
            )

        duration = time.perf_counter() - start
        raw = {"stdout": stdout, "stderr": stderr, "pattern": output_pattern}
        metrics = self._parse_tool_output(tool_name, raw)
        return ToolResult(
            tool_name=tool_name,
            execution_time=duration,
            exit_code=exit_code,
            success=exit_code == 0,
            output_path="",
            raw_results=raw,
            metrics=metrics,
            violations=[],
            recommendations=[],
        )

    def _parse_tool_output(self, tool_name: str, raw_results: Dict) -> Dict:
        if "summary" in raw_results:
            summary_wrapper = {"summary": raw_results["summary"]}
        else:
            summary_wrapper = {}
        if tool_name == "code_quality_validator":
            return self._extract_code_quality_metrics(summary_wrapper)
        if tool_name == "monolithic_detector":
            return self._extract_monolithic_metrics(summary_wrapper)
        if tool_name == "naming_validator":
            return self._extract_naming_metrics(summary_wrapper)
        if tool_name == "unified_test_runner":
            return self._extract_test_metrics(summary_wrapper)
        return {}

    def _evaluate_quality_gates(self) -> List[QualityGateResult]:
        gate_results: List[QualityGateResult] = []
        metrics_map = {result.tool_name: result.metrics for result in self.results}
        for gate_name, gate_conf in self.quality_gates.items():
            if not gate_conf.get("enabled", True):
                continue
            actual = self._resolve_gate_value(gate_name, metrics_map)
            threshold = gate_conf.get("threshold", 0.0)
            operator = gate_conf.get("operator", ">=")
            passed = self._evaluate_condition(actual, threshold, operator)
            gate_results.append(
                QualityGateResult(
                    gate_name=gate_name,
                    passed=passed,
                    actual_value=actual,
                    threshold=threshold,
                    severity=gate_conf.get("severity", "minor"),
                )
            )
        return gate_results

    def _resolve_gate_value(
        self, gate_name: str, metrics_map: Dict[str, Dict]
    ) -> float:
        if gate_name == "code_quality":
            return metrics_map.get("code_quality_validator", {}).get(
                "overall_compliance", 0.0
            )
        if gate_name == "monolithic_modules":
            return metrics_map.get("monolithic_detector", {}).get(
                "monolithic_files_found", 0
            )
        if gate_name == "naming_conventions":
            return metrics_map.get("naming_validator", {}).get(
                "compliance_percentage", 0.0
            )
        if gate_name == "test_execution":
            return metrics_map.get("unified_test_runner", {}).get("success_rate", 0.0)
        return 0.0

    def run_enforcement(self) -> Dict:
        start = time.perf_counter()
        for tool_name, tool_config in self.tools.items():
            if not tool_config.get("enabled", True):
                continue
            result = self._execute_tool(tool_name, tool_config)
            self.results.append(result)

        self.gate_results = self._evaluate_quality_gates()
        elapsed = time.perf_counter() - start
        summary = self._build_execution_summary()
        report = {
            "success": all(result.success for result in self.results),
            "execution_time": elapsed,
            "execution_summary": summary,
            "quality_gates": [asdict(gate) for gate in self.gate_results],
        }
        if self.output_path:
            self._write_report(report)
        return report

    def _build_execution_summary(self) -> Dict:
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        total_time = sum(r.execution_time for r in self.results)
        return {
            "total_tools": total,
            "successful_tools": successful,
            "failed_tools": failed,
            "total_execution_time": total_time,
        }

    def _write_report(self, report: Dict) -> None:
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text(json.dumps(report, indent=2))
        except OSError:  # pragma: no cover - best effort
            pass
