#!/usr/bin/env python3
"""
Quality Gate Enforcement System

This module provides a comprehensive quality gate enforcement system that orchestrates
all four testing tools and enforces quality gates based on configurable thresholds.

The system integrates:
1. Code Quality Validator (formatting and linting)
2. Monolithic Detector (architecture analysis)
3. Naming Validator (naming conventions)
4. Unified Test Runner (test execution)

Features:
- Tool orchestration with parallel/sequential execution
- Quality gate evaluation with configurable thresholds
- Unified reporting with JSON, HTML, and console outputs
- CI/CD integration with proper exit codes
- Performance monitoring and optimization
"""

import argparse
import json
import logging
import multiprocessing
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml


@dataclass
class ToolResult:
    """Result from tool execution."""

    tool_name: str
    execution_time: float
    exit_code: int
    success: bool
    output_path: str
    raw_results: Dict[str, Any]
    metrics: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[str]


@dataclass
class QualityGate:
    """Quality gate configuration."""

    name: str
    description: str
    threshold: float
    operator: str
    severity: str
    auto_fix: bool
    enabled: bool


@dataclass
class QualityGateResult:
    """Result from quality gate evaluation."""

    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    severity: str
    violations: List[Dict[str, Any]]
    recommendations: List[str]


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(level: int = logging.INFO):
    """Setup structured logging."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    return logger


class QualityGateEnforcer:
    """Main quality gate enforcement system."""

    def __init__(
        self,
        config_path: str = "quality_config.yaml",
        output_path: str = "reports/quality_gate_report.json",
        parallel_execution: bool = False,
    ):
        """Initialize the quality gate enforcer."""
        self.config_path = Path(config_path)
        self.output_path = output_path
        self.parallel_execution = parallel_execution
        self.project_root = Path.cwd()

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self._load_config()
        self.tools = self.config.get("tools", {})

        # Results storage
        self.results: List[ToolResult] = []
        self.gate_results: List[QualityGateResult] = []

        self.logger.info(
            f"Initialized QualityGateEnforcer with {multiprocessing.cpu_count()} CPU cores"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            # Set defaults if not present
            if "quality_gates" not in config:
                config["quality_gates"] = self._get_default_quality_gates()

            if "tools" not in config:
                config["tools"] = self._get_default_tools()

            if "reporting" not in config:
                config["reporting"] = self._get_default_reporting()

            self.logger.info(f"Loaded configuration from {self.config_path}")
            return config

        except FileNotFoundError:
            self.logger.warning(
                f"Configuration file {self.config_path} not found, using defaults"
            )
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "quality_gates": self._get_default_quality_gates(),
            "tools": self._get_default_tools(),
            "reporting": self._get_default_reporting(),
        }

    def _get_default_quality_gates(self) -> Dict[str, Any]:
        """Get default quality gate configurations."""
        return {
            "monolithic_modules": {
                "name": "Monolithic Modules",
                "description": "No modules over 500 lines of code",
                "threshold": 0,
                "operator": "==",
                "severity": "critical",
                "auto_fix": False,
                "enabled": True,
            },
            "naming_conventions": {
                "name": "Naming Conventions",
                "description": "95% compliance with naming conventions",
                "threshold": 95.0,
                "operator": ">=",
                "severity": "major",
                "auto_fix": False,
                "enabled": True,
            },
            "test_execution": {
                "name": "Test Execution",
                "description": "95% test success rate",
                "threshold": 95.0,
                "operator": ">=",
                "severity": "critical",
                "auto_fix": False,
                "enabled": True,
            },
            "code_quality": {
                "name": "Code Quality",
                "description": "95.56% overall code quality compliance",
                "threshold": 95.56,
                "operator": ">=",
                "severity": "critical",
                "auto_fix": False,
                "enabled": True,
            },
        }

    def _get_default_tools(self) -> Dict[str, Any]:
        """Get default tool configurations."""
        return {
            "code_quality_validator": {
                "command": "python",
                "args": [
                    "code_quality_validator.py",
                    "src/",
                    "--output",
                    "reports/code_quality_report.json",
                ],
                "timeout": 60,
                "enabled": True,
                "output_pattern": "reports/code_quality_report.json",
            },
            "monolithic_detector": {
                "command": "python",
                "args": [
                    "monolithic_detector.py",
                    "src/",
                    "--threshold",
                    "500",
                    "--output",
                    "reports/monolithic_report.json",
                ],
                "timeout": 30,
                "enabled": True,
                "output_pattern": "reports/monolithic_report.json",
            },
            "naming_validator": {
                "command": "python",
                "args": [
                    "naming_validator.py",
                    "src/",
                    "--output",
                    "reports/naming_report.json",
                ],
                "timeout": 30,
                "enabled": True,
                "output_pattern": "reports/naming_report.json",
            },
            "unified_test_runner": {
                "command": "python",
                "args": [
                    "-m",
                    "pytest",
                    "tests/",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=reports/test_report.json",
                ],
                "timeout": 120,
                "enabled": True,
                "output_pattern": "reports/test_report.json",
            },
        }

    def _get_default_reporting(self) -> Dict[str, Any]:
        """Get default reporting configuration."""
        return {
            "formats": ["json", "console"],
            "paths": {
                "json": "reports/quality_gate_report.json",
                "html": "reports/quality_gate_report.html",
                "console": "console",
            },
        }

    def _evaluate_condition(
        self, value: float, threshold: float, operator: str
    ) -> bool:
        """Evaluate a condition based on operator."""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            self.logger.warning(f"Unknown operator: {operator}")
            return False

    def _execute_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> ToolResult:
        """Execute a single tool."""
        start_time = time.time()
        self.logger.info(f"Executing tool: {tool_name}")

        try:
            # Build command
            command = tool_config["command"]
            args = tool_config.get("args", [])
            timeout = tool_config.get("timeout", 300)

            # Execute command
            process = subprocess.Popen(
                [command] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.project_root,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                execution_time = time.time() - start_time

                # Check if tool succeeded
                success = process.returncode == 0
                exit_code = process.returncode

                # Load results if available
                raw_results = {}
                metrics = {}
                violations = []
                recommendations = []

                output_path = tool_config.get("output_pattern", "")
                if output_path and Path(output_path).exists():
                    try:
                        with open(output_path, "r") as f:
                            raw_results = json.load(f)

                        # Extract metrics based on tool type
                        if tool_name == "code_quality_validator":
                            metrics = self._extract_code_quality_metrics(raw_results)
                            violations = self._extract_code_quality_violations(
                                raw_results
                            )
                        elif tool_name == "monolithic_detector":
                            metrics = self._extract_monolithic_metrics(raw_results)
                            violations = self._extract_monolithic_violations(
                                raw_results
                            )
                        elif tool_name == "naming_validator":
                            metrics = self._extract_naming_metrics(raw_results)
                            violations = self._extract_naming_violations(raw_results)
                        elif tool_name == "unified_test_runner":
                            metrics = self._extract_test_metrics(raw_results)
                            violations = self._extract_test_violations(raw_results)

                        recommendations = raw_results.get("recommendations", [])

                    except Exception as e:
                        self.logger.warning(
                            f"Could not load results from {output_path}: {e}"
                        )

                return ToolResult(
                    tool_name=tool_name,
                    execution_time=execution_time,
                    exit_code=exit_code,
                    success=success,
                    output_path=output_path,
                    raw_results=raw_results,
                    metrics=metrics,
                    violations=violations,
                    recommendations=recommendations,
                )

            except subprocess.TimeoutExpired:
                process.kill()
                execution_time = time.time() - start_time
                self.logger.error(f"Tool {tool_name} timed out after {timeout} seconds")
                return ToolResult(
                    tool_name=tool_name,
                    execution_time=execution_time,
                    exit_code=-1,
                    success=False,
                    output_path="",
                    raw_results={},
                    metrics={},
                    violations=[
                        {
                            "severity": "critical",
                            "message": f"Tool execution timed out after {timeout} seconds",
                        }
                    ],
                    recommendations=["Increase timeout or optimize tool execution"],
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult(
                tool_name=tool_name,
                execution_time=execution_time,
                exit_code=-1,
                success=False,
                output_path="",
                raw_results={},
                metrics={},
                violations=[
                    {
                        "severity": "critical",
                        "message": f"Tool execution error: {str(e)}",
                    }
                ],
                recommendations=["Fix tool execution issues"],
            )

    def _extract_code_quality_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from code quality validation results."""
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

    def _extract_code_quality_violations(
        self, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract violations from code quality validation results."""
        violations = []
        issues = results.get("issues", [])

        for issue in issues:
            violations.append(
                {
                    "severity": issue.get("severity", "minor"),
                    "message": issue.get("message", "Unknown issue"),
                    "file": issue.get("file", "unknown"),
                    "line": issue.get("line", 0),
                    "rule": issue.get("rule", "unknown"),
                }
            )

        return violations

    def _extract_monolithic_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from monolithic detection results."""
        summary = results.get("summary", {})
        return {
            "total_files_analyzed": summary.get("total_files_analyzed", 0),
            "monolithic_files_found": summary.get("monolithic_files_found", 0),
            "compliance_percentage": summary.get("compliance_percentage", 100.0),
            "average_lines_of_code": summary.get("average_lines_of_code", 0),
            "max_lines_of_code": summary.get("max_lines_of_code", 0),
        }

    def _extract_monolithic_violations(
        self, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract violations from monolithic detection results."""
        violations = []
        monolithic_files = results.get("monolithic_files", [])

        for file_info in monolithic_files:
            lines_of_code = file_info.get("lines_of_code", 0)
            severity = (
                "critical"
                if lines_of_code > 1000
                else "major" if lines_of_code > 750 else "minor"
            )

            violations.append(
                {
                    "severity": severity,
                    "message": f"Module exceeds {lines_of_code} lines of code",
                    "file": file_info.get("file_path", "unknown"),
                    "lines_of_code": lines_of_code,
                }
            )

        return violations

    def _extract_naming_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from naming validation results."""
        summary = results.get("summary", {})
        return {
            "total_files_validated": summary.get("total_files_validated", 0),
            "violations_found": summary.get("violations_found", 0),
            "compliance_percentage": summary.get("compliance_percentage", 100.0),
            "adjective_violations": summary.get("adjective_violations", 0),
            "convention_violations": summary.get("convention_violations", 0),
        }

    def _extract_naming_violations(
        self, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract violations from naming validation results."""
        violations = []
        violation_list = results.get("violations", [])

        for violation in violation_list:
            violations.append(
                {
                    "severity": violation.get("severity", "minor"),
                    "message": violation.get("message", "Naming violation"),
                    "file": violation.get("file", "unknown"),
                    "violation_type": violation.get("type", "unknown"),
                    "suggested_name": violation.get("suggested_name", ""),
                }
            )

        return violations

    def _extract_test_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from test execution results."""
        summary = results.get("summary", {})
        return {
            "total_tests": summary.get("total_tests", 0),
            "passed_tests": summary.get("passed_tests", 0),
            "failed_tests": summary.get("failed_tests", 0),
            "skipped_tests": summary.get("skipped_tests", 0),
            "success_rate": summary.get("success_rate", 0.0),
            "execution_time": summary.get("execution_time", 0.0),
        }

    def _extract_test_violations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract violations from test execution results."""
        violations = []
        failed_tests = results.get("failed_tests", [])

        for test in failed_tests:
            violations.append(
                {
                    "severity": "critical",
                    "message": f'Test failed: {test.get("error", "Unknown error")}',
                    "test": test.get("test_name", "unknown"),
                    "file": test.get("file", "unknown"),
                    "line": test.get("line", 0),
                }
            )

        return violations

    def _evaluate_quality_gates(self) -> List[QualityGateResult]:
        """Evaluate all quality gates based on tool results."""
        gate_results = []

        for gate_name, gate_config in self.config["quality_gates"].items():
            if not gate_config.get("enabled", True):
                continue

            try:
                # Get the appropriate metric value based on gate type
                metric_value = self._get_metric_value(gate_name)
                threshold = gate_config["threshold"]
                operator = gate_config["operator"]

                # Evaluate the condition
                passed = self._evaluate_condition(metric_value, threshold, operator)

                # Determine severity based on how much the gate failed/passed
                severity = gate_config["severity"]
                if not passed:
                    if operator == ">=":
                        failure_ratio = (
                            (threshold - metric_value) / threshold
                            if threshold > 0
                            else 1.0
                        )
                    elif operator == "<=":
                        failure_ratio = (
                            (metric_value - threshold) / threshold
                            if threshold > 0
                            else 1.0
                        )
                    else:
                        failure_ratio = 0.5

                    if failure_ratio > 0.2:
                        severity = "critical"
                    elif failure_ratio > 0.1:
                        severity = "major"
                    else:
                        severity = "minor"

                # Get violations for this gate
                violations = self._get_gate_violations(gate_name)

                # Generate recommendations
                recommendations = self._generate_gate_recommendations(
                    gate_name, passed, metric_value, threshold
                )

                gate_result = QualityGateResult(
                    gate_name=gate_name,
                    passed=passed,
                    actual_value=metric_value,
                    threshold=threshold,
                    severity=severity,
                    violations=violations,
                    recommendations=recommendations,
                )

                gate_results.append(gate_result)

                self.logger.info(
                    f"Quality gate '{gate_name}': {'PASS' if passed else 'FAIL'} "
                    f"(value: {metric_value}, threshold: {threshold} {operator})"
                )

            except Exception as e:
                self.logger.error(f"Error evaluating quality gate {gate_name}: {e}")
                gate_result = QualityGateResult(
                    gate_name=gate_name,
                    passed=False,
                    actual_value=0.0,
                    threshold=gate_config["threshold"],
                    severity="critical",
                    violations=[
                        {
                            "severity": "critical",
                            "message": f"Gate evaluation error: {str(e)}",
                        }
                    ],
                    recommendations=["Fix gate evaluation issues"],
                )
                gate_results.append(gate_result)

        return gate_results

    def _get_metric_value(self, gate_name: str) -> float:
        """Get the metric value for a specific quality gate."""
        if gate_name == "monolithic_modules":
            # For monolithic modules, we want 0 violations
            for result in self.results:
                if result.tool_name == "monolithic_detector":
                    return result.metrics.get("monolithic_files_found", 0)

        elif gate_name == "naming_conventions":
            # For naming conventions, we want high compliance percentage
            for result in self.results:
                if result.tool_name == "naming_validator":
                    return result.metrics.get("compliance_percentage", 0.0)

        elif gate_name == "test_execution":
            # For test execution, we want high success rate
            for result in self.results:
                if result.tool_name == "unified_test_runner":
                    return result.metrics.get("success_rate", 0.0)

        elif gate_name == "code_quality":
            # For code quality, we want high overall compliance
            for result in self.results:
                if result.tool_name == "code_quality_validator":
                    return result.metrics.get("overall_compliance", 0.0)

        return 0.0

    def _get_gate_violations(self, gate_name: str) -> List[Dict[str, Any]]:
        """Get violations for a specific quality gate."""
        violations = []

        for result in self.results:
            if (
                gate_name == "monolithic_modules"
                and result.tool_name == "monolithic_detector"
            ):
                violations.extend(result.violations)
            elif (
                gate_name == "naming_conventions"
                and result.tool_name == "naming_validator"
            ):
                violations.extend(result.violations)
            elif (
                gate_name == "test_execution"
                and result.tool_name == "unified_test_runner"
            ):
                violations.extend(result.violations)
            elif (
                gate_name == "code_quality"
                and result.tool_name == "code_quality_validator"
            ):
                violations.extend(result.violations)

        return violations

    def _generate_gate_recommendations(
        self, gate_name: str, passed: bool, actual_value: float, threshold: float
    ) -> List[str]:
        """Generate recommendations for a quality gate."""
        recommendations = []

        if not passed:
            if gate_name == "monolithic_modules":
                recommendations.append(
                    "Refactor large modules into smaller, more focused components"
                )
                recommendations.append(
                    "Consider applying the Single Responsibility Principle"
                )
                recommendations.append("Use dependency injection to reduce coupling")

            elif gate_name == "naming_conventions":
                recommendations.append(
                    "Remove descriptive adjectives from file and function names"
                )
                recommendations.append(
                    "Use domain-specific terminology instead of generic adjectives"
                )
                recommendations.append(
                    "Follow consistent naming conventions throughout the codebase"
                )

            elif gate_name == "test_execution":
                recommendations.append("Fix failing tests to improve test success rate")
                recommendations.append(
                    "Add missing test cases for uncovered functionality"
                )
                recommendations.append("Review and update flaky or unreliable tests")

            elif gate_name == "code_quality":
                recommendations.append("Improve code formatting and linting compliance")
                recommendations.append("Address critical and major code quality issues")
                recommendations.append("Consider using automated code formatting tools")
        else:
            recommendations.append(
                f"Excellent! {gate_name} quality gate passed with {actual_value:.2f}"
            )

        return recommendations

    def _generate_unified_report(self) -> Dict[str, Any]:
        """Generate a unified report combining all results."""
        report = {
            "execution_summary": {
                "total_tools": len(self.results),
                "successful_tools": sum(1 for r in self.results if r.success),
                "failed_tools": sum(1 for r in self.results if not r.success),
                "total_execution_time": sum(r.execution_time for r in self.results),
                "timestamp": datetime.now().isoformat(),
            },
            "tool_results": [],
            "quality_gate_results": [],
            "recommendations": [],
            "timestamp": datetime.now().isoformat(),
        }

        # Add tool results
        for result in self.results:
            report["tool_results"].append(
                {
                    "tool_name": result.tool_name,
                    "execution_time": result.execution_time,
                    "exit_code": result.exit_code,
                    "success": result.success,
                    "output_path": result.output_path,
                    "metrics": result.metrics,
                    "violations_count": len(result.violations),
                    "recommendations": result.recommendations,
                }
            )

        # Add quality gate results
        for gate_result in self.gate_results:
            report["quality_gate_results"].append(
                {
                    "gate_name": gate_result.gate_name,
                    "passed": gate_result.passed,
                    "actual_value": gate_result.actual_value,
                    "threshold": gate_result.threshold,
                    "severity": gate_result.severity,
                    "violations_count": len(gate_result.violations),
                    "recommendations": gate_result.recommendations,
                }
            )

        # Add overall recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        for gate_result in self.gate_results:
            all_recommendations.extend(gate_result.recommendations)

        report["recommendations"] = list(set(all_recommendations))  # Remove duplicates

        return report

    def _save_reports(
        self, report: Dict[str, Any], output_path: str, formats: List[str]
    ):
        """Save reports in specified formats."""
        for format_type in formats:
            if format_type == "json":
                json_path = (
                    output_path.replace(".html", ".json")
                    if output_path.endswith(".html")
                    else output_path
                )
                if json_path == "console":
                    json_path = "reports/quality_gate_report.json"

                # Ensure reports directory exists
                Path(json_path).parent.mkdir(parents=True, exist_ok=True)

                with open(json_path, "w") as f:
                    json.dump(report, f, indent=2)
                self.logger.info(f"JSON report saved to {json_path}")

            elif format_type == "html":
                if output_path == "console":
                    html_path = "reports/quality_gate_report.html"
                else:
                    html_path = output_path

                # Ensure reports directory exists
                Path(html_path).parent.mkdir(parents=True, exist_ok=True)

                html_content = self._generate_html_report(report)
                with open(html_path, "w") as f:
                    f.write(html_content)
                self.logger.info(f"HTML report saved to {html_path}")

            elif format_type == "console":
                self._print_console_summary(report)

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate an HTML report from the unified report data."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Gate Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007acc; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; color: #007acc; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .tool-result, .gate-result {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 6px; border-left: 4px solid #ddd; }}
        .tool-result.success {{ border-left-color: #28a745; }}
        .tool-result.failure {{ border-left-color: #dc3545; }}
        .gate-result.pass {{ border-left-color: #28a745; }}
        .gate-result.fail {{ border-left-color: #dc3545; }}
        .status {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .status.pass {{ background-color: #d4edda; color: #155724; }}
        .status.fail {{ background-color: #f8d7da; color: #721c24; }}
        .violations {{ margin-top: 10px; }}
        .violation {{ background-color: #fff3cd; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #ffc107; }}
        .recommendations {{ margin-top: 10px; }}
        .recommendation {{ background-color: #d1ecf1; padding: 8px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #17a2b8; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }}
        .metric {{ background-color: white; padding: 8px; border-radius: 4px; text-align: center; }}
        .metric-value {{ font-weight: bold; color: #007acc; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Quality Gate Enforcement Report</h1>
            <p>Generated on {report['timestamp']}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tools</h3>
                <div class="value">{report['execution_summary']['total_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Successful Tools</h3>
                <div class="value">{report['execution_summary']['successful_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Failed Tools</h3>
                <div class="value">{report['execution_summary']['failed_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Execution Time</h3>
                <div class="value">{report['execution_summary']['total_execution_time']:.2f}s</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Tool Results</h2>
"""

        for tool_result in report["tool_results"]:
            status_class = "success" if tool_result["success"] else "failure"
            status_text = "PASS" if tool_result["success"] else "FAIL"

            html += f"""
            <div class="tool-result {status_class}">
                <h3>{tool_result['tool_name']} <span class="status {status_class.lower()}">{status_text}</span></h3>
                <p><strong>Execution Time:</strong> {tool_result['execution_time']:.2f}s</p>
                <p><strong>Exit Code:</strong> {tool_result['exit_code']}</p>
                <p><strong>Violations:</strong> {tool_result['violations_count']}</p>
                
                {self._generate_metrics_html(tool_result['metrics'])}
                
                {self._generate_violations_html(tool_result.get('violations', []))}
                {self._generate_recommendations_html(tool_result['recommendations'])}
            </div>
"""

        html += """
        </div>
        
        <div class="section">
            <h2>Quality Gate Results</h2>
"""

        for gate_result in report["quality_gate_results"]:
            status_class = "pass" if gate_result["passed"] else "fail"
            status_text = "PASS" if gate_result["passed"] else "FAIL"

            html += f"""
            <div class="gate-result {status_class}">
                <h3>{gate_result['gate_name']} <span class="status {status_class}">{status_text}</span></h3>
                <p><strong>Actual Value:</strong> {gate_result['actual_value']:.2f}</p>
                <p><strong>Threshold:</strong> {gate_result['threshold']:.2f}</p>
                <p><strong>Severity:</strong> {gate_result['severity']}</p>
                <p><strong>Violations:</strong> {gate_result['violations_count']}</p>
                
                {self._generate_violations_html(gate_result.get('violations', []))}
                {self._generate_recommendations_html(gate_result['recommendations'])}
            </div>
"""

        html += """
        </div>
        
        <div class="section">
            <h2>Overall Recommendations</h2>
"""

        for recommendation in report["recommendations"]:
            html += f'<div class="recommendation">{recommendation}</div>'

        html += """
        </div>
    </div>
</body>
</html>
"""

        return html

    def _generate_metrics_html(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML for metrics display."""
        if not metrics:
            return ""

        html = '<div class="metrics">'
        for key, value in metrics.items():
            html += f'<div class="metric"><div class="metric-value">{value}</div><div>{key.replace("_", " ").title()}</div></div>'
        html += "</div>"

        return html

    def _generate_violations_html(self, violations: List[Dict[str, Any]]) -> str:
        """Generate HTML for violations display."""
        if not violations:
            return ""

        html = '<div class="violations"><h4>Violations:</h4>'
        for violation in violations:
            html += f'<div class="violation"><strong>{violation.get("severity", "unknown").upper()}:</strong> {violation.get("message", "Unknown violation")}</div>'
        html += "</div>"

        return html

    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations display."""
        if not recommendations:
            return ""

        html = '<div class="recommendations"><h4>Recommendations:</h4>'
        for recommendation in recommendations:
            html += f'<div class="recommendation">{recommendation}</div>'
        html += "</div>"

        return html

    def _print_console_summary(self, report: Dict[str, Any]):
        """Print a summary to console."""
        print("\n" + "=" * 80)
        print("QUALITY GATE ENFORCEMENT SUMMARY")
        print("=" * 80)
        print(f"Generated: {report['timestamp']}")
        print(f"Total Tools: {report['execution_summary']['total_tools']}")
        print(f"Successful: {report['execution_summary']['successful_tools']}")
        print(f"Failed: {report['execution_summary']['failed_tools']}")
        print(f"Total Time: {report['execution_summary']['total_execution_time']:.2f}s")
        print("\n" + "-" * 80)
        print("TOOL RESULTS")
        print("-" * 80)

        for tool_result in report["tool_results"]:
            status = "PASS" if tool_result["success"] else "FAIL"
            print(
                f"{tool_result['tool_name']:<30} {status:<10} {tool_result['execution_time']:.2f}s"
            )

        print("\n" + "-" * 80)
        print("QUALITY GATE RESULTS")
        print("-" * 80)

        for gate_result in report["quality_gate_results"]:
            status = "PASS" if gate_result["passed"] else "FAIL"
            print(
                f"{gate_result['gate_name']:<30} {status:<10} {gate_result['actual_value']:.2f}/{gate_result['threshold']:.2f}"
            )

        print("\n" + "=" * 80)

    def run_enforcement(self) -> Dict[str, Any]:
        """Run the complete quality gate enforcement process."""
        start_time = time.time()
        self.logger.info("Starting quality gate enforcement process")

        try:
            # Execute all tools
            self.logger.info(
                f"Starting quality gate enforcement with {len(self.tools)} tools"
            )

            for tool_name, tool_config in self.tools.items():
                if not tool_config.get("enabled", True):
                    self.logger.info(f"Skipping disabled tool: {tool_name}")
                    continue

                result = self._execute_tool(tool_name, tool_config)
                self.results.append(result)

                if result.success:
                    self.logger.info(
                        f"Tool {tool_name} completed successfully in {result.execution_time:.2f}s"
                    )
                else:
                    self.logger.warning(
                        f"Tool {tool_name} failed with exit code {result.exit_code}"
                    )

            # Evaluate quality gates
            self.logger.info("Evaluating quality gates")
            self.gate_results = self._evaluate_quality_gates()

            # Generate unified report
            report = self._generate_unified_report()

            # Save reports
            output_formats = self.config.get("reporting", {}).get(
                "formats", ["json", "console"]
            )
            self._save_reports(report, self.output_path, output_formats)

            # Determine overall success
            all_gates_passed = all(result.passed for result in self.gate_results)
            all_tools_succeeded = all(result.success for result in self.results)
            overall_success = all_gates_passed and all_tools_succeeded

            execution_time = time.time() - start_time

            result = {
                "success": overall_success,
                "exit_code": 0 if overall_success else 1,
                "execution_time": execution_time,
                "execution_summary": report["execution_summary"],
                "quality_gate_results": [
                    {
                        "gate_name": r.gate_name,
                        "passed": r.passed,
                        "actual_value": r.actual_value,
                        "threshold": r.threshold,
                        "severity": r.severity,
                    }
                    for r in self.gate_results
                ],
                "tool_results": [
                    {
                        "tool_name": r.tool_name,
                        "success": r.success,
                        "execution_time": r.execution_time,
                        "exit_code": r.exit_code,
                    }
                    for r in self.results
                ],
                "recommendations": report["recommendations"],
            }

            if overall_success:
                self.logger.info(
                    f"Quality gate enforcement completed successfully in {execution_time:.2f}s"
                )
            else:
                self.logger.warning(
                    f"Quality gate enforcement completed with failures in {execution_time:.2f}s"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Quality gate enforcement failed: {e}")
            return {
                "success": False,
                "exit_code": 1,
                "execution_time": execution_time,
                "error": str(e),
                "execution_summary": {
                    "total_tools": len(self.results),
                    "successful_tools": sum(1 for r in self.results if r.success),
                    "failed_tools": sum(1 for r in self.results if not r.success),
                    "total_execution_time": execution_time,
                },
            }


def main():
    """Main entry point for the quality gate enforcer."""
    parser = argparse.ArgumentParser(
        description="Run quality gate enforcement across all testing tools"
    )
    parser.add_argument(
        "--config",
        default="quality_config.yaml",
        help="Path to quality gate configuration file",
    )
    parser.add_argument(
        "--output",
        default="reports/quality_gate_report.json",
        help="Output report file path",
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Execute tools in parallel"
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Execute tools sequentially"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # Create enforcer
    enforcer = QualityGateEnforcer(
        config_path=args.config,
        output_path=args.output,
        parallel_execution=args.parallel or not args.sequential,
    )

    # Run enforcement
    result = enforcer.run_enforcement()

    # Exit with appropriate code
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
