#!/usr/bin/env python3
"""
Code Formatting and Linting Validator

Provides comprehensive code quality validation using Black and Pylint
with automated fixes and compliance scoring.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class FormattingResult:
    """Results from Black formatting validation."""

    file_path: str
    was_formatted: bool
    original_size: int
    formatted_size: int
    changes_made: List[str]
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class LintingIssue:
    """Individual linting issue from Pylint."""

    file_path: str
    line_number: int
    column: int
    issue_type: str  # error, warning, refactor, convention
    symbol: str
    message: str
    confidence: str


@dataclass
class LintingResult:
    """Results from Pylint analysis."""

    file_path: str
    overall_score: float
    issues: List[LintingIssue]
    rating: str  # Excellent, Good, Acceptable, Poor
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class ComplianceResult:
    """Overall compliance result."""

    target_compliance: float
    actual_compliance: float
    formatting_score: float
    linting_score: float
    overall_score: float
    passed: bool
    violations: List[str]
    recommendations: List[str]


class CodeQualityValidator:
    """Main validator for code formatting and linting."""

    def __init__(self, target_compliance: float = 95.56):
        self.target_compliance = target_compliance
        self.black_config = self._get_black_config()
        self.pylint_config = self._get_pylint_config()

    def _get_black_config(self) -> Dict[str, Any]:
        """Get Black configuration."""
        return {
            "line_length": 88,
            "target_version": ["py38"],
            "include": "\\.pyi?$",
            "extend_exclude": """
            /(
              # directories
              \\.eggs
              | \\.git
              | \\.hg
              | \\.mypy_cache
              | \\.tox
              | \\.venv
              | build
              | dist
            )/
            """,
        }

    def _get_pylint_config(self) -> Dict[str, Any]:
        """Get Pylint configuration."""
        return {
            "max_line_length": 88,
            "disable": [
                "C0114",  # missing-module-docstring
                "C0115",  # missing-class-docstring
                "C0116",  # missing-function-docstring
                "R0903",  # too-few-public-methods
                "R0913",  # too-many-arguments
                "W0613",  # unused-argument
                "W0622",  # redefined-builtin
            ],
            "enable": [
                "E",  # errors
                "W",  # warnings
                "F",  # fatal
                "I",  # info
                "C",  # convention
                "R",  # refactor
            ],
        }

    def format_with_black(
        self, file_path: Path, fix_mode: bool = True
    ) -> FormattingResult:
        """
        Format a file with Black.

        Args:
            file_path: Path to the file to format
            fix_mode: Whether to apply fixes or just check

        Returns:
            FormattingResult with formatting details
        """
        start_time = time.time()

        try:
            # Get original file size
            original_size = file_path.stat().st_size if file_path.exists() else 0

            # Build Black command
            cmd = ["python", "-m", "black"]

            if fix_mode:
                cmd.append("--fix")
            else:
                cmd.append("--check")

            cmd.extend(
                [
                    "--line-length",
                    str(self.black_config["line_length"]),
                    "--target-version",
                    self.black_config["target_version"][0],
                    str(file_path),
                ]
            )

            # Execute Black
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            processing_time = time.time() - start_time

            # Get formatted file size
            formatted_size = file_path.stat().st_size if file_path.exists() else 0

            # Determine if changes were made
            was_formatted = (
                result.returncode != 0
                if not fix_mode
                else len(result.stdout.strip()) > 0
            )

            # Parse changes made
            changes_made = []
            if was_formatted and fix_mode:
                changes_made = ["code formatting applied"]

            return FormattingResult(
                file_path=str(file_path),
                was_formatted=was_formatted,
                original_size=original_size,
                formatted_size=formatted_size,
                changes_made=changes_made,
                processing_time=processing_time,
            )

        except subprocess.TimeoutExpired:
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=False,
                original_size=0,
                formatted_size=0,
                changes_made=[],
                processing_time=30.0,
                error_message="Formatting timeout",
            )
        except Exception as e:
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=False,
                original_size=0,
                formatted_size=0,
                changes_made=[],
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    def lint_with_pylint(self, file_path: Path) -> LintingResult:
        """
        Lint a file with Pylint.

        Args:
            file_path: Path to the file to lint

        Returns:
            LintingResult with linting details
        """
        start_time = time.time()

        try:
            # Create temporary pylintrc if needed
            pylintrc_path = self._create_pylint_config()

            # Build Pylint command
            cmd = [
                "python",
                "-m",
                "pylint",
                "--rcfile",
                str(pylintrc_path),
                "--output-format",
                "json",
                "--score",
                "yes",
                str(file_path),
            ]

            # Execute Pylint
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            processing_time = time.time() - start_time

            # Parse JSON output
            issues = []
            overall_score = 10.0  # Default perfect score

            if result.stdout.strip():
                try:
                    pylint_output = json.loads(result.stdout)

                    for issue_data in pylint_output:
                        issue = LintingIssue(
                            file_path=issue_data.get("path", str(file_path)),
                            line_number=issue_data.get("line", 0),
                            column=issue_data.get("column", 0),
                            issue_type=issue_data.get("type", "unknown"),
                            symbol=issue_data.get("symbol", ""),
                            message=issue_data.get("message", ""),
                            confidence=issue_data.get("confidence", "HIGH"),
                        )
                        issues.append(issue)

                    # Extract overall score from stderr
                    if result.stderr:
                        import re

                        score_match = re.search(r"rated at ([0-9.]+)/10", result.stderr)
                        if score_match:
                            overall_score = float(score_match.group(1))

                except json.JSONDecodeError:
                    logger.warning(
                        f"Failed to parse Pylint JSON output for {file_path}"
                    )

            # Determine rating
            if overall_score >= 9.0:
                rating = "Excellent"
            elif overall_score >= 7.5:
                rating = "Good"
            elif overall_score >= 6.0:
                rating = "Acceptable"
            else:
                rating = "Poor"

            return LintingResult(
                file_path=str(file_path),
                overall_score=overall_score,
                issues=issues,
                rating=rating,
                processing_time=processing_time,
            )

        except subprocess.TimeoutExpired:
            return LintingResult(
                file_path=str(file_path),
                overall_score=0.0,
                issues=[],
                rating="Poor",
                processing_time=60.0,
                error_message="Linting timeout",
            )
        except Exception as e:
            return LintingResult(
                file_path=str(file_path),
                overall_score=0.0,
                issues=[],
                rating="Poor",
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    def _create_pylint_config(self) -> Path:
        """Create temporary Pylint configuration file."""
        pylintrc_content = f"""
[MASTER]
max-line-length={self.pylint_config['max_line_length']}

[MESSAGES CONTROL]
disable={','.join(self.pylint_config['disable'])}

[FORMAT]
max-line-length={self.pylint_config['max_line_length']}
"""

        pylintrc_path = Path(tempfile.gettempdir()) / "temp_pylintrc"
        with open(pylintrc_path, "w") as f:
            f.write(pylintrc_content)

        return pylintrc_path

    def validate_file(
        self, file_path: Path, fix_formatting: bool = True
    ) -> Tuple[FormattingResult, LintingResult]:
        """
        Validate a single file for formatting and linting.

        Args:
            file_path: Path to the file to validate
            fix_formatting: Whether to apply formatting fixes

        Returns:
            Tuple of (FormattingResult, LintingResult)
        """
        logger.info(f"Validating {file_path}")

        # Format with Black first
        formatting_result = self.format_with_black(file_path, fix_formatting)

        # Then lint with Pylint
        linting_result = self.lint_with_pylint(file_path)

        return formatting_result, linting_result

    def validate_directory(
        self, root_path: Path, fix_formatting: bool = True
    ) -> List[Tuple[FormattingResult, LintingResult]]:
        """
        Validate all Python files in a directory.

        Args:
            root_path: Root directory to validate
            fix_formatting: Whether to apply formatting fixes

        Returns:
            List of (FormattingResult, LintingResult) tuples
        """
        # Find all Python files
        python_files = list(root_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to validate")

        results = []
        for file_path in python_files:
            try:
                result = self.validate_file(file_path, fix_formatting)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to validate {file_path}: {e}")
                # Create error results
                error_formatting = FormattingResult(
                    file_path=str(file_path),
                    was_formatted=False,
                    original_size=0,
                    formatted_size=0,
                    changes_made=[],
                    processing_time=0.0,
                    error_message=str(e),
                )
                error_linting = LintingResult(
                    file_path=str(file_path),
                    overall_score=0.0,
                    issues=[],
                    rating="Poor",
                    processing_time=0.0,
                    error_message=str(e),
                )
                results.append((error_formatting, error_linting))

        return results

    def calculate_compliance(
        self, results: List[Tuple[FormattingResult, LintingResult]]
    ) -> ComplianceResult:
        """
        Calculate overall compliance score.

        Args:
            results: List of validation results

        Returns:
            ComplianceResult with overall compliance details
        """
        if not results:
            return ComplianceResult(
                target_compliance=self.target_compliance,
                actual_compliance=0.0,
                formatting_score=0.0,
                linting_score=0.0,
                overall_score=0.0,
                passed=False,
                violations=["No files to validate"],
                recommendations=["Add Python files to validate"],
            )

        # Calculate formatting score
        formatting_scores = []
        for formatting_result, _ in results:
            if formatting_result.error_message:
                formatting_scores.append(0.0)
            else:
                # Score based on whether file needed formatting
                score = 100.0 if not formatting_result.was_formatted else 85.0
                formatting_scores.append(score)

        formatting_score = sum(formatting_scores) / len(formatting_scores)

        # Calculate linting score
        linting_scores = []
        total_issues = 0
        critical_issues = 0

        for _, linting_result in results:
            if linting_result.error_message:
                linting_scores.append(0.0)
            else:
                # Convert Pylint 10-point scale to 100-point scale
                score = linting_result.overall_score * 10.0
                linting_scores.append(score)

                # Count issues
                total_issues += len(linting_result.issues)
                critical_issues += len(
                    [i for i in linting_result.issues if i.issue_type == "error"]
                )

        linting_score = sum(linting_scores) / len(linting_scores)

        # Calculate overall score (weighted average)
        overall_score = formatting_score * 0.3 + linting_score * 0.7

        # Determine compliance
        actual_compliance = overall_score
        passed = actual_compliance >= self.target_compliance

        # Generate violations and recommendations
        violations = []
        recommendations = []

        if not passed:
            violations.append(
                f"Compliance {actual_compliance:.2f}% is below target {self.target_compliance}%"
            )

        if formatting_score < 90.0:
            violations.append(f"Formatting score {formatting_score:.2f}% is below 90%")
            recommendations.append("Run Black formatter to fix formatting issues")

        if linting_score < 90.0:
            violations.append(f"Linting score {linting_score:.2f}% is below 90%")
            recommendations.append("Address Pylint warnings and errors")

        if critical_issues > 0:
            violations.append(f"Found {critical_issues} critical linting errors")
            recommendations.append("Fix critical errors immediately")

        if total_issues > len(results) * 5:  # More than 5 issues per file on average
            recommendations.append(
                "High number of issues detected. Consider code review"
            )

        if not recommendations:
            recommendations.append("Code quality is excellent! Keep up the good work.")

        return ComplianceResult(
            target_compliance=self.target_compliance,
            actual_compliance=actual_compliance,
            formatting_score=formatting_score,
            linting_score=linting_score,
            overall_score=overall_score,
            passed=passed,
            violations=violations,
            recommendations=recommendations,
        )

    def generate_report(
        self,
        results: List[Tuple[FormattingResult, LintingResult]],
        compliance: ComplianceResult,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.

        Args:
            results: List of validation results
            compliance: Overall compliance result

        Returns:
            Dictionary containing the validation report
        """
        # Aggregate statistics
        total_files = len(results)
        files_with_formatting_issues = sum(1 for f, _ in results if f.was_formatted)
        files_with_linting_errors = sum(1 for _, l in results if l.overall_score < 7.0)

        # Group issues by type
        issues_by_type = {}
        for _, linting_result in results:
            for issue in linting_result.issues:
                issue_type = issue.issue_type
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = []
                issues_by_type[issue_type].append(
                    {
                        "file": issue.file_path,
                        "line": issue.line_number,
                        "message": issue.message,
                        "symbol": issue.symbol,
                    }
                )

        # Calculate processing statistics
        total_processing_time = sum(
            f.processing_time + l.processing_time for f, l in results
        )
        avg_processing_time = (
            total_processing_time / total_files if total_files > 0 else 0
        )

        report = {
            "summary": {
                "total_files_analyzed": total_files,
                "files_with_formatting_issues": files_with_formatting_issues,
                "files_with_linting_errors": files_with_linting_errors,
                "compliance_percentage": compliance.actual_compliance,
                "target_compliance": compliance.target_compliance,
                "passed": compliance.passed,
                "total_processing_time": total_processing_time,
                "average_processing_time": avg_processing_time,
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "scores": {
                "formatting_score": compliance.formatting_score,
                "linting_score": compliance.linting_score,
                "overall_score": compliance.overall_score,
            },
            "issues_by_type": issues_by_type,
            "violations": compliance.violations,
            "recommendations": compliance.recommendations,
            "detailed_results": [
                {
                    "file_path": f.file_path,
                    "formatting": asdict(f),
                    "linting": asdict(l),
                }
                for f, l in results
            ],
        }

        return report

    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save validation report to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to {output_path}")


def main():
    """Main entry point for code quality validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate code formatting and linting with automated fixes"
    )
    parser.add_argument("path", help="Directory or file path to validate")
    parser.add_argument(
        "--target-compliance",
        type=float,
        default=95.56,
        help="Target compliance percentage (default: 95.56)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/formatting_linting_report.json",
        help="Output report file path",
    )
    parser.add_argument(
        "--fix-formatting",
        action="store_true",
        help="Apply formatting fixes automatically",
    )
    parser.add_argument(
        "--no-fix", action="store_true", help="Check only, do not apply fixes"
    )

    args = parser.parse_args()

    # Initialize validator
    validator = CodeQualityValidator(target_compliance=args.target_compliance)

    # Validate target path
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"Path does not exist: {target_path}")
        sys.exit(1)

    logger.info(f"Starting code quality validation of {target_path}")

    # Determine fix mode
    fix_formatting = args.fix_formatting and not args.no_fix

    if target_path.is_file():
        # Single file validation
        formatting_result, linting_result = validator.validate_file(
            target_path, fix_formatting
        )
        results = [(formatting_result, linting_result)]
    else:
        # Directory validation
        results = validator.validate_directory(target_path, fix_formatting)

    # Calculate compliance
    compliance = validator.calculate_compliance(results)

    # Generate and save report
    report = validator.generate_report(results, compliance)
    validator.save_report(report, Path(args.output))

    # Print summary
    print(f"\n=== Code Quality Validation Summary ===")
    print(f"Files analyzed: {report['summary']['total_files_analyzed']}")
    print(
        f"Files with formatting issues: {report['summary']['files_with_formatting_issues']}"
    )
    print(
        f"Files with linting errors: {report['summary']['files_with_linting_errors']}"
    )
    print(f"Overall compliance: {report['summary']['compliance_percentage']:.2f}%")
    print(f"Target compliance: {report['summary']['target_compliance']:.2f}%")
    print(f"Status: {'PASS' if report['summary']['passed'] else 'FAIL'}")

    print(f"\nScores:")
    print(f"  Formatting: {report['scores']['formatting_score']:.2f}%")
    print(f"  Linting: {report['scores']['linting_score']:.2f}%")
    print(f"  Overall: {report['scores']['overall_score']:.2f}%")

    if report["violations"]:
        print(f"\nViolations:")
        for violation in report["violations"]:
            print(f"  - {violation}")

    if report["recommendations"]:
        print(f"\nRecommendations:")
        for recommendation in report["recommendations"]:
            print(f"  - {recommendation}")

    # Show top issue types
    if report["issues_by_type"]:
        print(f"\nTop issue types:")
        for issue_type, issues in list(report["issues_by_type"].items())[:5]:
            print(f"  - {issue_type}: {len(issues)} issues")

    return 0 if compliance.passed else 1


if __name__ == "__main__":
    sys.exit(main())
