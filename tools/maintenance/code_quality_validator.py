"""Code formatting and linting orchestration helpers."""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass
class FormattingResult:
    file_path: str
    was_formatted: bool
    original_size: int
    formatted_size: int
    changes_made: List[str]
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class LintingIssue:
    file_path: str
    line_number: int
    column: int
    issue_type: str
    symbol: str
    message: str
    confidence: str


@dataclass
class LintingResult:
    file_path: str
    overall_score: float
    issues: List[LintingIssue]
    rating: str
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class ComplianceResult:
    formatting_score: float
    linting_score: float
    overall_score: float
    actual_compliance: float
    passed: bool
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CodeQualityValidator:
    """Coordinates Black + Pylint execution and calculates weighted compliance."""

    def __init__(self, target_compliance: float = 95.56) -> None:
        self.target_compliance = target_compliance
        self.black_timeout = 60
        self.pylint_timeout = 120
        self._format_weight = 0.3
        self._lint_weight = 0.7

    # ------------------------------------------------------------------ config
    @staticmethod
    def _get_black_config() -> dict:
        return {
            "line_length": 88,
            "target_version": ["py38", "py39", "py310", "py311", "py312"],
            "include": r"\.pyi?$",
            "extend_exclude": r"/(\.eggs|\.git|\.mypy_cache|\.pytest_cache|build|dist)/",
        }

    @staticmethod
    def _get_pylint_config() -> dict:
        return {
            "max_line_length": 88,
            "disable": [
                "C0114",
                "C0115",
                "C0116",
                "R0903",
                "R0913",
                "W0613",
            ],
            "enable": ["E", "W", "F"],
        }

    # ----------------------------------------------------------------- helpers
    def format_with_black(self, file_path: Path, fix_mode: bool = True) -> FormattingResult:
        file_path = Path(file_path)
        original_size = file_path.stat().st_size if file_path.exists() else 0
        start = time.perf_counter()
        cmd = ["black", str(file_path)]
        if not fix_mode:
            cmd.append("--check")
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.black_timeout,
            )
            duration = time.perf_counter() - start
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            combined = "\n".join([stdout, stderr]).lower()
            was_formatted = False
            if fix_mode:
                was_formatted = "reformatted" in combined
            else:
                was_formatted = completed.returncode != 0

            formatted_size = file_path.stat().st_size if file_path.exists() else original_size
            changes = []
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=was_formatted,
                original_size=original_size,
                formatted_size=formatted_size,
                changes_made=changes,
                processing_time=duration,
            )
        except subprocess.TimeoutExpired as exc:
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=False,
                original_size=original_size,
                formatted_size=original_size,
                changes_made=[],
                processing_time=float(exc.timeout or self.black_timeout),
                error_message="Formatting timeout",
            )

    def lint_with_pylint(self, file_path: Path) -> LintingResult:
        file_path = Path(file_path)
        start = time.perf_counter()
        cmd = [
            "pylint",
            str(file_path),
            "--output-format=json",
            "--score=y",
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.pylint_timeout,
            )
            duration = time.perf_counter() - start
            stdout = completed.stdout or "[]"
            stderr = completed.stderr or ""
            score_match = re.search(r"rated at ([0-9.]+)/10", stderr)
            score = float(score_match.group(1)) if score_match else 0.0
            issues_data = json.loads(stdout or "[]")
            issues: List[LintingIssue] = []
            for issue in issues_data:
                issues.append(
                    LintingIssue(
                        file_path=str(issue.get("path", file_path)),
                        line_number=int(issue.get("line", 0)),
                        column=int(issue.get("column", 0)),
                        issue_type=issue.get("type", "info"),
                        symbol=issue.get("symbol", ""),
                        message=issue.get("message", ""),
                        confidence=str(issue.get("confidence", "")),
                    )
                )

            rating = self._classify_rating(score)
            return LintingResult(
                file_path=str(file_path),
                overall_score=score,
                issues=issues,
                rating=rating,
                processing_time=duration,
            )
        except subprocess.TimeoutExpired as exc:
            return LintingResult(
                file_path=str(file_path),
                overall_score=0.0,
                issues=[],
                rating="Poor",
                processing_time=float(exc.timeout or self.pylint_timeout),
                error_message="Linting timeout",
            )

    # ------------------------------------------------------------- aggregation
    def validate_file(self, file_path: Path, fix_mode: bool = True) -> Tuple[FormattingResult, LintingResult]:
        formatting = self.format_with_black(file_path, fix_mode=fix_mode)
        linting = self.lint_with_pylint(file_path)
        return formatting, linting

    def validate_directory(self, directory: Path, fix_mode: bool = True):
        directory = Path(directory)
        results = []
        for python_file in sorted(self._iter_python_files(directory)):
            results.append(self.validate_file(python_file, fix_mode=fix_mode))
        return results

    def calculate_compliance(self, results: Sequence[Tuple[FormattingResult, LintingResult]]) -> ComplianceResult:
        if not results:
            return ComplianceResult(
                formatting_score=0.0,
                linting_score=0.0,
                overall_score=0.0,
                actual_compliance=0.0,
                passed=False,
                violations=["No files to validate"],
                recommendations=["Add Python files to the target directory."],
            )

        formatted_files = sum(1 for fmt, _ in results if fmt.was_formatted)
        formatting_score = max(0.0, 100.0 - 15.0 * formatted_files)

        lint_scores = [lint.overall_score for _, lint in results]
        linting_score = mean(lint_scores) * 10 if lint_scores else 0.0

        overall = formatting_score * self._format_weight + linting_score * self._lint_weight
        passed = overall >= self.target_compliance
        violations: List[str] = []
        recommendations: List[str] = []
        if not passed:
            violations.append(
                f"Overall compliance {overall:.2f}% is below target {self.target_compliance:.2f}%."
            )
            if formatted_files:
                recommendations.append("Commit formatted changes before re-running validation.")
            if linting_score < self.target_compliance:
                recommendations.append("Increase linting score by addressing warnings/errors.")

        return ComplianceResult(
            formatting_score=formatting_score,
            linting_score=linting_score,
            overall_score=overall,
            actual_compliance=overall,
            passed=passed,
            violations=violations,
            recommendations=recommendations,
        )

    def generate_report(
        self,
        results: Sequence[Tuple[FormattingResult, LintingResult]],
        compliance: ComplianceResult,
    ) -> dict:
        total_files = len(results)
        formatting_issues = sum(1 for fmt, _ in results if fmt.was_formatted)
        linting_errors = sum(1 for _, lint in results if any(issue.issue_type == "error" for issue in lint.issues))
        issues_by_type = {}
        for _, lint in results:
            for issue in lint.issues:
                issues_by_type.setdefault(issue.issue_type, 0)
                issues_by_type[issue.issue_type] += 1

        detailed = []
        for fmt, lint in results:
            detailed.append(
                {
                    "file": fmt.file_path,
                    "formatting": {
                        "was_formatted": fmt.was_formatted,
                        "error": fmt.error_message,
                        "processing_time": fmt.processing_time,
                    },
                    "linting": {
                        "score": lint.overall_score,
                        "rating": lint.rating,
                        "issues": [issue.__dict__ for issue in lint.issues],
                        "error": lint.error_message,
                    },
                }
            )

        summary = {
            "total_files_analyzed": total_files,
            "files_with_formatting_issues": formatting_issues,
            "files_with_linting_errors": linting_errors,
            "compliance_passed": compliance.passed,
        }
        scores = {
            "formatting_score": compliance.formatting_score,
            "linting_score": compliance.linting_score,
            "overall_score": compliance.overall_score,
        }
        report = {
            "summary": summary,
            "scores": scores,
            "issues_by_type": issues_by_type,
            "violations": compliance.violations,
            "recommendations": compliance.recommendations,
            "detailed_results": detailed,
        }
        return report

    @staticmethod
    def save_report(report: dict, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    # ----------------------------------------------------------------- helpers
    def _iter_python_files(self, directory: Path) -> Iterable[Path]:
        if directory.is_file():
            yield directory
            return
        for path in sorted(directory.rglob("*.py")):
            if path.is_file():
                yield path

    @staticmethod
    def _classify_rating(score: float) -> str:
        if score >= 9.0:
            return "Excellent"
        if score >= 7.5:
            return "Good"
        if score >= 6.0:
            return "Acceptable"
        return "Poor"

