#!/usr/bin/env python3
"""
Automated setStyleSheet() Detection Tool

This tool scans the codebase for hardcoded styles in setStyleSheet() calls
and provides detailed analysis for migration to qt-material.

Usage:
    python tools/stylesheet_detector.py [options]

Options:
    --output FILE    Output file for the analysis report (default: stylesheet_report.json)
    --format FORMAT  Output format: json, html, markdown (default: json)
    --verbose        Enable verbose logging
    --include-tests  Include test files in analysis
    --min-risk LEVEL Only show files with minimum risk level (low, medium, high)
"""

import os
import re
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class StyleSheetCall:
    """Information about a setStyleSheet() call."""

    file_path: str
    line_number: int
    stylesheet_content: str
    context: str
    risk_level: str
    migration_suggestion: str
    hardcoded_colors: List[str]
    qt_properties: List[str]


@dataclass
class StyleAnalysis:
    """Analysis results for a single file."""

    file_path: str
    total_calls: int
    high_risk_calls: int
    medium_risk_calls: int
    low_risk_calls: int
    calls: List[StyleSheetCall]
    overall_risk: str
    migration_priority: int


@dataclass
class DetectionReport:
    """Complete detection report."""

    summary: Dict[str, Any]
    files: List[StyleAnalysis]
    risk_distribution: Dict[str, int]
    common_patterns: Dict[str, int]
    migration_recommendations: List[str]


class StyleSheetDetector:
    """
    Advanced detector for hardcoded styles in setStyleSheet() calls.
    """

    def __init__(
        self, root_path: str = "src", include_tests: bool = False, min_risk: str = "low"
    ):
        self.root_path = Path(root_path)
        self.include_tests = include_tests
        self.min_risk = min_risk
        self.logger = logging.getLogger(__name__)

        # Regex patterns for different types of stylesheet content
        self.patterns = {
            "stylesheet_call": re.compile(
                r'\.setStyleSheet\(["\']([^"\']+)["\']', re.MULTILINE | re.DOTALL
            ),
            "hardcoded_colors": re.compile(r"#[0-9a-fA-F]{3,8}"),
            "qt_properties": re.compile(r"Q[A-Z][A-Za-z]*\s*\{[^}]*\}"),
            "complex_styles": re.compile(r"\{[^}]*\{[^}]*\}[^}]*\}"),  # Nested braces
            "inline_styles": re.compile(
                r"background-color|color|border|padding|margin"
            ),
            "dynamic_values": re.compile(r"\{[^}]*\}"),  # Template variables
        }

        # Risk assessment criteria
        self.risk_criteria = {
            "high": {
                "hardcoded_colors": 3,  # 3+ hardcoded colors
                "complex_styles": True,  # Complex nested styles
                "no_variables": True,  # No template variables
            },
            "medium": {
                "hardcoded_colors": 1,  # 1+ hardcoded colors
                "inline_styles": True,  # Inline style properties
            },
            "low": {
                "dynamic_values": True,  # Uses template variables
                "qt_material": True,  # Already using qt-material
            },
        }

    def analyze_codebase(self) -> DetectionReport:
        """Analyze the entire codebase for setStyleSheet() calls."""
        self.logger.info(f"Starting stylesheet detection in {self.root_path}")

        files_to_analyze = self._get_files_to_analyze()
        self.logger.info(f"Found {len(files_to_analyze)} files to analyze")

        file_analyses = []
        risk_distribution = {"high": 0, "medium": 0, "low": 0}
        common_patterns = defaultdict(int)

        for file_path in files_to_analyze:
            try:
                analysis = self._analyze_file(file_path)
                if self._should_include_analysis(analysis):
                    file_analyses.append(analysis)
                    risk_distribution[analysis.overall_risk] += 1

                    # Track common patterns
                    for call in analysis.calls:
                        for color in call.hardcoded_colors:
                            common_patterns[color] += 1

            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                continue

        # Generate recommendations
        recommendations = self._generate_recommendations(file_analyses, common_patterns)

        # Create summary
        summary = self._create_summary(
            file_analyses, risk_distribution, common_patterns
        )

        return DetectionReport(
            summary=summary,
            files=file_analyses,
            risk_distribution=risk_distribution,
            common_patterns=dict(common_patterns),
            migration_recommendations=recommendations,
        )

    def _get_files_to_analyze(self) -> List[str]:
        """Get list of Python files to analyze."""
        file_extensions = [".py"]
        exclude_dirs = ["__pycache__", ".git", "venv", "env", ".venv", ".env"]

        files = []
        for ext in file_extensions:
            for file_path in self.root_path.rglob(f"*{ext}"):
                # Skip excluded directories
                if any(part in exclude_dirs for part in file_path.parts):
                    continue

                # Skip test files unless requested
                if not self.include_tests and "test" in file_path.name.lower():
                    continue

                files.append(str(file_path.relative_to(self.root_path)))

        return sorted(files)

    def _analyze_file(self, file_path: str) -> StyleAnalysis:
        """Analyze a single file for setStyleSheet() calls."""
        full_path = self.root_path / file_path

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return self._create_empty_analysis(file_path)

        lines = content.split("\n")
        calls = self._find_stylesheet_calls(file_path, lines)

        # Categorize calls by risk
        high_risk_calls = [c for c in calls if c.risk_level == "high"]
        medium_risk_calls = [c for c in calls if c.risk_level == "medium"]
        low_risk_calls = [c for c in calls if c.risk_level == "low"]

        # Determine overall risk
        overall_risk = self._determine_overall_risk(
            high_risk_calls, medium_risk_calls, low_risk_calls
        )

        # Calculate migration priority
        migration_priority = self._calculate_migration_priority(overall_risk, calls)

        return StyleAnalysis(
            file_path=file_path,
            total_calls=len(calls),
            high_risk_calls=len(high_risk_calls),
            medium_risk_calls=len(medium_risk_calls),
            low_risk_calls=len(low_risk_calls),
            calls=calls,
            overall_risk=overall_risk,
            migration_priority=migration_priority,
        )

    def _find_stylesheet_calls(
        self, file_path: str, lines: List[str]
    ) -> List[StyleSheetCall]:
        """Find and analyze all setStyleSheet() calls in a file."""
        calls = []

        for line_num, line in enumerate(lines, 1):
            match = self.patterns["stylesheet_call"].search(line)
            if match:
                stylesheet_content = match.group(1)
                call = self._analyze_stylesheet_call(
                    file_path, line_num, stylesheet_content, lines
                )
                calls.append(call)

        return calls

    def _analyze_stylesheet_call(
        self, file_path: str, line_num: int, stylesheet_content: str, lines: List[str]
    ) -> StyleSheetCall:
        """Analyze a single setStyleSheet() call."""

        # Get context around the call
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 3)
        context_lines = lines[context_start:context_end]
        context = "\n".join(context_lines)

        # Extract hardcoded colors
        hardcoded_colors = self.patterns["hardcoded_colors"].findall(stylesheet_content)

        # Extract Qt properties
        qt_properties = self.patterns["qt_properties"].findall(stylesheet_content)

        # Assess risk level
        risk_level = self._assess_call_risk(
            stylesheet_content, hardcoded_colors, qt_properties
        )

        # Generate migration suggestion
        migration_suggestion = self._generate_migration_suggestion(
            stylesheet_content, hardcoded_colors, qt_properties, risk_level
        )

        return StyleSheetCall(
            file_path=file_path,
            line_number=line_num,
            stylesheet_content=stylesheet_content,
            context=context,
            risk_level=risk_level,
            migration_suggestion=migration_suggestion,
            hardcoded_colors=hardcoded_colors,
            qt_properties=qt_properties,
        )

    def _assess_call_risk(
        self,
        stylesheet_content: str,
        hardcoded_colors: List[str],
        qt_properties: List[str],
    ) -> str:
        """Assess the risk level of a stylesheet call."""

        # Check for high-risk patterns
        if (
            len(hardcoded_colors) >= 3
            or self.patterns["complex_styles"].search(stylesheet_content)
            or (
                self.patterns["inline_styles"].search(stylesheet_content)
                and not self.patterns["dynamic_values"].search(stylesheet_content)
            )
        ):
            return "high"

        # Check for medium-risk patterns
        if len(hardcoded_colors) >= 1 or self.patterns["inline_styles"].search(
            stylesheet_content
        ):
            return "medium"

        # Check for low-risk patterns (already using qt-material or variables)
        if (
            self.patterns["dynamic_values"].search(stylesheet_content)
            or "qt_material" in stylesheet_content.lower()
            or "COLORS." in stylesheet_content
        ):
            return "low"

        return "medium"  # Default to medium

    def _generate_migration_suggestion(
        self,
        stylesheet_content: str,
        hardcoded_colors: List[str],
        qt_properties: List[str],
        risk_level: str,
    ) -> str:
        """Generate migration suggestion for a stylesheet call."""

        suggestions = []

        if hardcoded_colors:
            suggestions.append(
                f"Replace {len(hardcoded_colors)} hardcoded colors with qt-material theme colors"
            )

        if self.patterns["inline_styles"].search(stylesheet_content):
            suggestions.append("Convert inline styles to qt-material theme properties")

        if self.patterns["complex_styles"].search(stylesheet_content):
            suggestions.append(
                "Break down complex nested styles into simpler qt-material components"
            )

        if not self.patterns["dynamic_values"].search(stylesheet_content):
            suggestions.append(
                "Use qt-material color variables instead of hardcoded values"
            )

        if risk_level == "high":
            suggestions.insert(
                0, "HIGH PRIORITY: This stylesheet needs immediate migration"
            )

        return (
            "; ".join(suggestions)
            if suggestions
            else "Review for potential qt-material integration"
        )

    def _determine_overall_risk(
        self,
        high_risk_calls: List[StyleSheetCall],
        medium_risk_calls: List[StyleSheetCall],
        low_risk_calls: List[StyleSheetCall],
    ) -> str:
        """Determine overall risk level for a file."""

        if high_risk_calls:
            return "high"
        elif medium_risk_calls:
            return "medium"
        elif low_risk_calls:
            return "low"
        else:
            return "low"

    def _calculate_migration_priority(
        self, overall_risk: str, calls: List[StyleSheetCall]
    ) -> int:
        """Calculate migration priority (1-10, higher = more urgent)."""

        base_priority = {"high": 8, "medium": 5, "low": 2}
        priority = base_priority[overall_risk]

        # Increase priority based on number of calls
        priority += min(len(calls), 3)

        # Increase priority for files with many hardcoded colors
        total_colors = sum(len(call.hardcoded_colors) for call in calls)
        priority += min(total_colors, 3)

        return min(priority, 10)

    def _should_include_analysis(self, analysis: StyleAnalysis) -> bool:
        """Check if analysis should be included based on minimum risk level."""

        risk_levels = {"low": 1, "medium": 2, "high": 3}
        min_level = risk_levels.get(self.min_risk, 1)
        current_level = risk_levels.get(analysis.overall_risk, 1)

        return current_level >= min_level

    def _create_empty_analysis(self, file_path: str) -> StyleAnalysis:
        """Create empty analysis for files that couldn't be read."""

        return StyleAnalysis(
            file_path=file_path,
            total_calls=0,
            high_risk_calls=0,
            medium_risk_calls=0,
            low_risk_calls=0,
            calls=[],
            overall_risk="low",
            migration_priority=1,
        )

    def _generate_recommendations(
        self, file_analyses: List[StyleAnalysis], common_patterns: Dict[str, int]
    ) -> List[str]:
        """Generate migration recommendations."""

        recommendations = []

        # General recommendations
        high_risk_files = [f for f in file_analyses if f.overall_risk == "high"]
        if high_risk_files:
            recommendations.append(
                f"Migrate {len(high_risk_files)} high-risk files first to prevent system instability"
            )

        # Color recommendations
        if common_patterns:
            most_common_colors = sorted(
                common_patterns.items(), key=lambda x: x[1], reverse=True
            )[:5]
            recommendations.append(
                f"Replace common colors {', '.join([color for color, _ in most_common_colors])} "
                "with qt-material theme colors"
            )

        # Pattern-based recommendations
        total_calls = sum(f.total_calls for f in file_analyses)
        if total_calls > 20:
            recommendations.append(
                "Consider batch migration of similar stylesheet patterns"
            )

        recommendations.extend(
            [
                "Use UnifiedThemeManager for dynamic theme application",
                "Replace hardcoded colors with theme color variables",
                "Test visual appearance after each migration step",
                "Update documentation to reflect new theming approach",
            ]
        )

        return recommendations

    def _create_summary(
        self,
        file_analyses: List[StyleAnalysis],
        risk_distribution: Dict[str, int],
        common_patterns: Dict[str, int],
    ) -> Dict[str, Any]:
        """Create analysis summary."""

        total_files = len(file_analyses)
        total_calls = sum(f.total_calls for f in file_analyses)
        total_high_risk = sum(f.high_risk_calls for f in file_analyses)
        total_medium_risk = sum(f.medium_risk_calls for f in file_analyses)
        total_low_risk = sum(f.low_risk_calls for f in file_analyses)

        # Calculate averages
        avg_calls_per_file = total_calls / total_files if total_files > 0 else 0
        avg_risk_score = (
            (
                risk_distribution["high"] * 3
                + risk_distribution["medium"] * 2
                + risk_distribution["low"] * 1
            )
            / total_files
            if total_files > 0
            else 0
        )

        return {
            "total_files_analyzed": total_files,
            "total_stylesheet_calls": total_calls,
            "average_calls_per_file": avg_calls_per_file,
            "high_risk_calls": total_high_risk,
            "medium_risk_calls": total_medium_risk,
            "low_risk_calls": total_low_risk,
            "average_risk_score": avg_risk_score,
            "most_common_colors": sorted(
                common_patterns.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }


def main():
    """Main entry point for the stylesheet detection tool."""

    parser = argparse.ArgumentParser(description="setStyleSheet() Detection Tool")
    parser.add_argument(
        "--output",
        "-o",
        default="stylesheet_report.json",
        help="Output file for the analysis report",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis"
    )
    parser.add_argument(
        "--min-risk",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum risk level to include",
    )
    parser.add_argument(
        "--root-path", default="src", help="Root path to analyze (default: src)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Run analysis
    detector = StyleSheetDetector(args.root_path, args.include_tests, args.min_risk)
    report = detector.analyze_codebase()

    # Output report
    if args.format == "json":
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)
    elif args.format == "html":
        _output_html_report(report, args.output)
    elif args.format == "markdown":
        _output_markdown_report(report, args.output)

    # Print summary to console
    print(f"\n{'='*60}")
    print("STYLESHEET DETECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Files analyzed: {report.summary['total_files_analyzed']}")
    print(f"Total setStyleSheet() calls: {report.summary['total_stylesheet_calls']}")
    print(f"Average calls per file: {report.summary['average_calls_per_file']:.1f}")
    print(f"High risk calls: {report.summary['high_risk_calls']}")
    print(f"Medium risk calls: {report.summary['medium_risk_calls']}")
    print(f"Low risk calls: {report.summary['low_risk_calls']}")
    print(
        f"Risk distribution: High={report.risk_distribution['high']}, "
        f"Medium={report.risk_distribution['medium']}, Low={report.risk_distribution['low']}"
    )

    if report.summary["most_common_colors"]:
        print(f"\nMost common hardcoded colors:")
        for color, count in report.summary["most_common_colors"][:5]:
            print(f"  {color}: {count} occurrences")

    print(f"\nReport saved to: {args.output}")
    print(f"{'='*60}")


def _output_html_report(report: DetectionReport, output_file: str):
    """Output detection report in HTML format."""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>setStyleSheet() Detection Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .file {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
            .call {{ background: #f9f9f9; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .high-risk {{ border-left: 5px solid #ff4444; }}
            .medium-risk {{ border-left: 5px solid #ffaa00; }}
            .low-risk {{ border-left: 5px solid #44aa44; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4fd; }}
        </style>
    </head>
    <body>
        <h1>setStyleSheet() Detection Report</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">Files Analyzed: {report.summary['total_files_analyzed']}</div>
            <div class="metric">Total Calls: {report.summary['total_stylesheet_calls']}</div>
            <div class="metric">High Risk: {report.summary['high_risk_calls']}</div>
            <div class="metric">Medium Risk: {report.summary['medium_risk_calls']}</div>
            <div class="metric">Low Risk: {report.summary['low_risk_calls']}</div>
        </div>

        <h2>Risk Distribution</h2>
        <div class="metric">High Risk Files: {report.risk_distribution['high']}</div>
        <div class="metric">Medium Risk Files: {report.risk_distribution['medium']}</div>
        <div class="metric">Low Risk Files: {report.risk_distribution['low']}</div>

        <h2>Files Requiring Migration</h2>
        {''.join(_format_file_html(f) for f in report.files)}
    </body>
    </html>
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)


def _format_file_html(file_analysis: StyleAnalysis) -> str:
    """Format a single file analysis as HTML."""

    risk_class = file_analysis.overall_risk.replace(" ", "-")

    calls_html = ""
    for call in file_analysis.calls:
        calls_html += f"""
        <div class="call {call.risk_level}-risk">
            <strong>Line {call.line_number}:</strong> {call.migration_suggestion}<br>
            <small>Colors: {', '.join(call.hardcoded_colors) if call.hardcoded_colors else 'None'}</small>
        </div>
        """

    return f"""
    <div class="file {risk_class}">
        <h3>{file_analysis.file_path}</h3>
        <p><strong>Risk:</strong> {file_analysis.overall_risk} |
           <strong>Priority:</strong> {file_analysis.migration_priority} |
           <strong>Calls:</strong> {file_analysis.total_calls}</p>
        {calls_html}
    </div>
    """


def _output_markdown_report(report: DetectionReport, output_file: str):
    """Output detection report in Markdown format."""

    markdown = f"""
# setStyleSheet() Detection Report

## Summary

- **Files Analyzed:** {report.summary['total_files_analyzed']}
- **Total setStyleSheet() Calls:** {report.summary['total_stylesheet_calls']}
- **Average Calls per File:** {report.summary['average_calls_per_file']:.1f}
- **High Risk Calls:** {report.summary['high_risk_calls']}
- **Medium Risk Calls:** {report.summary['medium_risk_calls']}
- **Low Risk Calls:** {report.summary['low_risk_calls']}

## Risk Distribution

- **High Risk Files:** {report.risk_distribution['high']}
- **Medium Risk Files:** {report.risk_distribution['medium']}
- **Low Risk Files:** {report.risk_distribution['low']}

## Most Common Hardcoded Colors

"""

    for color, count in report.summary["most_common_colors"]:
        markdown += f"- `{color}`: {count} occurrences\n"

    markdown += "\n## Files Requiring Migration\n\n"

    for file_analysis in report.files:
        markdown += f"""
### {file_analysis.file_path}

- **Risk Level:** {file_analysis.overall_risk}
- **Migration Priority:** {file_analysis.migration_priority}/10
- **Total Calls:** {file_analysis.total_calls}
- **High Risk Calls:** {file_analysis.high_risk_calls}
- **Medium Risk Calls:** {file_analysis.medium_risk_calls}
- **Low Risk Calls:** {file_analysis.low_risk_calls}

"""

        for call in file_analysis.calls:
            markdown += f"""
**Line {call.line_number}:** {call.migration_suggestion}
- Hardcoded colors: {', '.join(call.hardcoded_colors) if call.hardcoded_colors else 'None'}
- Qt properties: {len(call.qt_properties)}

"""

    markdown += "\n## Migration Recommendations\n\n"

    for recommendation in report.migration_recommendations:
        markdown += f"- {recommendation}\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)


if __name__ == "__main__":
    main()
