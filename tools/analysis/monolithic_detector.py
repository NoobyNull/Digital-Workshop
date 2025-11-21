#!/usr/bin/env python3
"""
Monolithic Module Detection Tool

Analyzes Python source code to identify modules exceeding
the specified line count threshold.
"""

import ast
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ModuleMetrics:
    """Metrics for a single module analysis."""

    path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    docstring_lines: int
    blank_lines: int
    is_monolithic: bool
    severity: str
    timestamp: str


class MonolithicDetector:
    """Main detector class for monolithic module identification."""

    def __init__(self, threshold: int = 500, max_workers: int = 4):
        self.threshold = threshold
        self.max_workers = max_workers
        self.results: List[ModuleMetrics] = []

    def count_lines_accurate(self, file_path: Path) -> Dict[str, int]:
        """
        Accurately count different types of lines in a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary with line counts by type
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST to get accurate line counts
            tree = ast.parse(content, filename=str(file_path))

            # Count lines using AST nodes
            code_lines = set()
            docstring_lines = set()

            for node in ast.walk(tree):
                if hasattr(node, "lineno"):
                    code_lines.add(node.lineno)

                # Check for docstrings
                if (
                    isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module))
                    and node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    docstring_start = node.body[0].lineno
                    docstring_end = node.body[0].end_lineno or docstring_start
                    docstring_lines.update(range(docstring_start, docstring_end + 1))

            total_lines = len(content.splitlines())
            blank_lines = sum(1 for line in content.splitlines() if line.strip() == "")

            # Count comment lines (lines starting with #)
            comment_lines = 0
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") and i not in code_lines:
                    comment_lines += 1

            actual_code_lines = len(code_lines) - len(docstring_lines)

            return {
                "total_lines": total_lines,
                "code_lines": actual_code_lines,
                "comment_lines": comment_lines,
                "docstring_lines": len(docstring_lines),
                "blank_lines": blank_lines,
            }

        except Exception as e:
            logger.error("Error analyzing %s: %s", file_path, e)
            return {
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "docstring_lines": 0,
                "blank_lines": 0,
            }

    def analyze_file(self, file_path: Path) -> ModuleMetrics:
        """
        Analyze a single Python file for monolithic patterns.

        Args:
            file_path: Path to the Python file

        Returns:
            ModuleMetrics object with analysis results
        """
        logger.info("Analyzing %s", file_path)

        line_counts = self.count_lines_accurate(file_path)
        code_lines = line_counts["code_lines"]

        # Determine severity based on how much threshold is exceeded
        if code_lines > self.threshold:
            excess_ratio = code_lines / self.threshold
            if excess_ratio > 2.0:
                severity = "critical"
            elif excess_ratio > 1.5:
                severity = "major"
            else:
                severity = "minor"
        else:
            severity = "none"

        return ModuleMetrics(
            path=str(file_path),
            total_lines=line_counts["total_lines"],
            code_lines=code_lines,
            comment_lines=line_counts["comment_lines"],
            docstring_lines=line_counts["docstring_lines"],
            blank_lines=line_counts["blank_lines"],
            is_monolithic=code_lines > self.threshold,
            severity=severity,
            timestamp=__import__("datetime").datetime.now().isoformat(),
        )

    def scan_directory(self, root_path: Path) -> List[ModuleMetrics]:
        """
        Recursively scan directory for Python files and analyze them.

        Args:
            root_path: Root directory to scan

        Returns:
            List of ModuleMetrics for all analyzed files
        """
        python_files = list(root_path.rglob("*.py"))
        logger.info("Found %d Python files to analyze", len(python_files))

        results = []

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.analyze_file, file_path): file_path
                for file_path in python_files
            }

            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error("Failed to analyze %s: %s", file_path, e)

        return results

    def generate_report(self, results: List[ModuleMetrics]) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.

        Args:
            results: List of ModuleMetrics objects

        Returns:
            Dictionary containing the analysis report
        """
        total_files = len(results)
        monolithic_files = [r for r in results if r.is_monolithic]

        report = {
            "summary": {
                "total_files_analyzed": total_files,
                "monolithic_files_found": len(monolithic_files),
                "compliance_rate": (
                    ((total_files - len(monolithic_files)) / total_files * 100)
                    if total_files > 0
                    else 100
                ),
                "threshold": self.threshold,
                "analysis_timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "violations": [
                {
                    "path": result.path,
                    "code_lines": result.code_lines,
                    "severity": result.severity,
                    "excess_lines": result.code_lines - self.threshold,
                }
                for result in monolithic_files
            ],
            "detailed_results": [asdict(result) for result in results],
        }

        return report

    def save_report(self, report: Dict[str, Any], output_path: Path):
        """
        Save analysis report to JSON file.

        Args:
            report: Analysis report dictionary
            output_path: Path to save the report
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("Report saved to %s", output_path)


def main():
    """Main entry point for the monolithic detection tool."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect monolithic Python modules exceeding line thresholds"
    )
    parser.add_argument("path", help="Directory or file path to analyze")
    parser.add_argument(
        "--threshold", type=int, default=500, help="Line count threshold (default: 500)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="monolithic_analysis_report.json",
        help="Output report file path",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker threads (default: 4)"
    )

    args = parser.parse_args()

    # Initialize detector
    detector = MonolithicDetector(threshold=args.threshold, max_workers=args.workers)

    # Analyze target path
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error("Path does not exist: %s", target_path)
        sys.exit(1)

    logger.info("Starting monolithic analysis of %s", target_path)

    if target_path.is_file():
        results = [detector.analyze_file(target_path)]
    else:
        results = detector.scan_directory(target_path)

    # Generate and save report
    report = detector.generate_report(results)
    detector.save_report(report, Path(args.output))

    # Print summary
    print("\n=== Monolithic Module Detection Summary ===")
    print(f"Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Monolithic files found: {report['summary']['monolithic_files_found']}")
    print(f"Compliance rate: {report['summary']['compliance_rate']:.2f}%")

    if report["violations"]:
        print("\nViolations found:")
        for violation in report["violations"]:
            print(
                f"  - {violation['path']}: {violation['code_lines']} lines "
                f"({violation['severity']} severity)"
            )

    return 0 if report["summary"]["monolithic_files_found"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
