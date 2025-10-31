#!/usr/bin/env python3
"""
Dependency Analysis Tool for GUI Layout Refactoring

This tool provides comprehensive dependency mapping for theme-related components
and identifies all hardcoded styles that need to be migrated to qt-material.

Usage:
    python tools/dependency_analysis.py [options]

Options:
    --output FILE    Output file for the analysis report (default: dependency_report.json)
    --format FORMAT  Output format: json, html, markdown (default: json)
    --verbose        Enable verbose logging
    --include-tests  Include test files in analysis
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
class DependencyInfo:
    """Information about a single dependency."""
    file_path: str
    line_number: int
    dependency_type: str  # 'import', 'usage', 'stylesheet'
    context: str
    code_snippet: str


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    theme_manager_imports: List[DependencyInfo]
    theme_manager_usage: List[DependencyInfo]
    stylesheet_calls: List[DependencyInfo]
    hardcoded_colors: List[DependencyInfo]
    theme_related_imports: List[DependencyInfo]
    risk_level: str  # 'high', 'medium', 'low'
    migration_priority: int  # 1-10, higher = more urgent


@dataclass
class AnalysisReport:
    """Complete analysis report."""
    summary: Dict[str, Any]
    files: List[FileAnalysis]
    theme_manager_usage: Dict[str, List[str]]
    stylesheet_usage: Dict[str, List[str]]
    hardcoded_colors: Dict[str, List[str]]
    migration_plan: Dict[str, Any]


class ThemeDependencyAnalyzer:
    """
    Comprehensive analyzer for theme-related dependencies and hardcoded styles.
    """

    def __init__(self, root_path: str = "src", include_tests: bool = False):
        self.root_path = Path(root_path)
        self.include_tests = include_tests
        self.logger = logging.getLogger(__name__)

        # Patterns for different types of dependencies
        self.patterns = {
            'theme_manager_import': re.compile(
                r'^(?:from\s+[\w.]+\s+)?import\s+(?:.*\b)?ThemeManager(?:\b.*)?',
                re.MULTILINE
            ),
            'theme_manager_usage': re.compile(
                r'\bThemeManager\b(?:\.instance\(\)|\.get_instance\(\)|\(\))?',
                re.MULTILINE
            ),
            'stylesheet_call': re.compile(
                r'\.setStyleSheet\(["\']([^"\']+)["\']',
                re.MULTILINE
            ),
            'hardcoded_colors': re.compile(
                r'#[0-9a-fA-F]{6}',
                re.MULTILINE
            ),
            'theme_related_imports': re.compile(
                r'from\s+[\w.]*(?:theme|Theme)(?:[\w.]*\s+import|import\s+[\w\s,]*\b(?:COLORS|ThemeService|ThemeManager|UnifiedThemeManager)\b)',
                re.MULTILINE
            ),
            'qt_material_imports': re.compile(
                r'from\s+[\w.]*(?:qt_material|qt-material)[\w.]*\s+import|import\s+[\w\s,]*\bqt_material\b',
                re.MULTILINE
            )
        }

        # Risk assessment patterns
        self.risk_patterns = {
            'high': [
                r'ThemeManager\.instance\(\)',
                r'setStyleSheet.*#[0-9a-fA-F]{6}',
                r'from.*theme.*import.*ThemeManager',
            ],
            'medium': [
                r'COLORS\.',
                r'setStyleSheet.*\{[^}]*background-color',
                r'from.*theme.*import.*COLORS',
            ],
            'low': [
                r'from.*theme.*import.*UnifiedThemeManager',
                r'qt_material',
                r'ThemeService',
            ]
        }

    def analyze_codebase(self) -> AnalysisReport:
        """Analyze the entire codebase for theme dependencies."""
        self.logger.info(f"Starting dependency analysis in {self.root_path}")

        files_to_analyze = self._get_files_to_analyze()
        self.logger.info(f"Found {len(files_to_analyze)} files to analyze")

        file_analyses = []
        theme_manager_usage = defaultdict(list)
        stylesheet_usage = defaultdict(list)
        hardcoded_colors = defaultdict(list)

        for file_path in files_to_analyze:
            try:
                analysis = self._analyze_file(file_path)
                file_analyses.append(analysis)

                # Aggregate usage patterns
                if analysis.theme_manager_usage:
                    theme_manager_usage[file_path].extend(
                        [info.context for info in analysis.theme_manager_usage]
                    )

                if analysis.stylesheet_calls:
                    stylesheet_usage[file_path].extend(
                        [info.context for info in analysis.stylesheet_calls]
                    )

                if analysis.hardcoded_colors:
                    hardcoded_colors[file_path].extend(
                        [info.context for info in analysis.hardcoded_colors]
                    )

            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                continue

        # Generate migration plan
        migration_plan = self._generate_migration_plan(file_analyses)

        # Create summary
        summary = self._create_summary(file_analyses, theme_manager_usage, stylesheet_usage, hardcoded_colors)

        return AnalysisReport(
            summary=summary,
            files=file_analyses,
            theme_manager_usage=dict(theme_manager_usage),
            stylesheet_usage=dict(stylesheet_usage),
            hardcoded_colors=dict(hardcoded_colors),
            migration_plan=migration_plan
        )

    def _get_files_to_analyze(self) -> List[str]:
        """Get list of Python files to analyze."""
        file_extensions = ['.py']
        exclude_dirs = ['__pycache__', '.git', 'venv', 'env', '.venv', '.env']

        files = []
        for ext in file_extensions:
            for file_path in self.root_path.rglob(f'*{ext}'):
                # Skip excluded directories
                if any(part in exclude_dirs for part in file_path.parts):
                    continue

                # Skip test files unless requested
                if not self.include_tests and 'test' in file_path.name.lower():
                    continue

                files.append(str(file_path.relative_to(self.root_path)))

        return sorted(files)

    def _analyze_file(self, file_path: str) -> FileAnalysis:
        """Analyze a single file for theme dependencies."""
        full_path = self.root_path / file_path

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return self._create_empty_analysis(file_path)

        lines = content.split('\n')

        # Find all dependency types
        theme_manager_imports = self._find_pattern_matches(
            file_path, lines, 'theme_manager_import', 'import'
        )
        theme_manager_usage = self._find_pattern_matches(
            file_path, lines, 'theme_manager_usage', 'usage'
        )
        stylesheet_calls = self._find_stylesheet_calls(file_path, lines)
        hardcoded_colors = self._find_hardcoded_colors(file_path, lines)
        theme_related_imports = self._find_pattern_matches(
            file_path, lines, 'theme_related_imports', 'import'
        )

        # Assess risk level
        risk_level = self._assess_risk_level(
            theme_manager_usage, stylesheet_calls, hardcoded_colors, theme_related_imports
        )

        # Calculate migration priority
        migration_priority = self._calculate_migration_priority(
            risk_level, len(theme_manager_usage), len(stylesheet_calls)
        )

        return FileAnalysis(
            file_path=file_path,
            theme_manager_imports=theme_manager_imports,
            theme_manager_usage=theme_manager_usage,
            stylesheet_calls=stylesheet_calls,
            hardcoded_colors=hardcoded_colors,
            theme_related_imports=theme_related_imports,
            risk_level=risk_level,
            migration_priority=migration_priority
        )

    def _find_pattern_matches(self, file_path: str, lines: List[str], pattern_name: str, dep_type: str) -> List[DependencyInfo]:
        """Find matches for a specific pattern."""
        pattern = self.patterns[pattern_name]
        matches = []

        for line_num, line in enumerate(lines, 1):
            match = pattern.search(line)
            if match:
                matches.append(DependencyInfo(
                    file_path=file_path,
                    line_number=line_num,
                    dependency_type=dep_type,
                    context=line.strip(),
                    code_snippet=self._get_code_snippet(lines, line_num, 2)
                ))

        return matches

    def _find_stylesheet_calls(self, file_path: str, lines: List[str]) -> List[DependencyInfo]:
        """Find setStyleSheet calls with context."""
        matches = []

        for line_num, line in enumerate(lines, 1):
            match = self.patterns['stylesheet_call'].search(line)
            if match:
                # Get more context around the call
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 3)
                context_lines = lines[context_start:context_end]
                context = '\n'.join(context_lines)

                matches.append(DependencyInfo(
                    file_path=file_path,
                    line_number=line_num,
                    dependency_type='stylesheet',
                    context=context,
                    code_snippet=line.strip()
                ))

        return matches

    def _find_hardcoded_colors(self, file_path: str, lines: List[str]) -> List[DependencyInfo]:
        """Find hardcoded color values."""
        matches = []

        for line_num, line in enumerate(lines, 1):
            # Find hex colors
            hex_matches = self.patterns['hardcoded_colors'].findall(line)
            for hex_color in hex_matches:
                # Skip if it's in a comment or string that's not a style
                if self._is_style_related_context(line, hex_color):
                    matches.append(DependencyInfo(
                        file_path=file_path,
                        line_number=line_num,
                        dependency_type='hardcoded_color',
                        context=line.strip(),
                        code_snippet=f"Color: {hex_color}"
                    ))

        return matches

    def _is_style_related_context(self, line: str, hex_color: str) -> bool:
        """Check if hex color is in a style-related context."""
        style_indicators = [
            'background', 'color', 'border', 'setStyleSheet',
            'QWidget', 'QPushButton', 'QLabel', 'QFrame',
            'rgb(', 'rgba(', 'hsl(', 'hsla('
        ]

        line_lower = line.lower()
        return any(indicator in line_lower for indicator in style_indicators)

    def _assess_risk_level(self, theme_usage: List[DependencyInfo], stylesheets: List[DependencyInfo],
                          colors: List[DependencyInfo], imports: List[DependencyInfo]) -> str:
        """Assess the risk level of migrating this file."""
        risk_score = 0

        # High risk indicators
        if any(re.search(pattern, info.context) for info in theme_usage for pattern in self.risk_patterns['high']):
            risk_score += 3

        if any(re.search(pattern, info.context) for info in stylesheets for pattern in self.risk_patterns['high']):
            risk_score += 3

        # Medium risk indicators
        if any(re.search(pattern, info.context) for info in theme_usage + stylesheets for pattern in self.risk_patterns['medium']):
            risk_score += 2

        # Low risk indicators (actually reduce risk)
        if any(re.search(pattern, info.context) for info in imports for pattern in self.risk_patterns['low']):
            risk_score -= 1

        # Determine risk level
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'

    def _calculate_migration_priority(self, risk_level: str, theme_usage_count: int, stylesheet_count: int) -> int:
        """Calculate migration priority (1-10, higher = more urgent)."""
        base_priority = {
            'high': 8,
            'medium': 5,
            'low': 2
        }

        priority = base_priority[risk_level]

        # Increase priority based on usage count
        priority += min(theme_usage_count + stylesheet_count, 4)

        return min(priority, 10)

    def _create_empty_analysis(self, file_path: str) -> FileAnalysis:
        """Create empty analysis for files that couldn't be read."""
        return FileAnalysis(
            file_path=file_path,
            theme_manager_imports=[],
            theme_manager_usage=[],
            stylesheet_calls=[],
            hardcoded_colors=[],
            theme_related_imports=[],
            risk_level='low',
            migration_priority=1
        )

    def _get_code_snippet(self, lines: List[str], line_num: int, context_lines: int) -> str:
        """Get code snippet with context around a line."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])

    def _generate_migration_plan(self, file_analyses: List[FileAnalysis]) -> Dict[str, Any]:
        """Generate a comprehensive migration plan."""
        # Sort files by priority
        sorted_files = sorted(file_analyses, key=lambda x: x.migration_priority, reverse=True)

        # Group by risk level
        high_risk = [f for f in sorted_files if f.risk_level == 'high']
        medium_risk = [f for f in sorted_files if f.risk_level == 'medium']
        low_risk = [f for f in sorted_files if f.risk_level == 'low']

        # Create phases
        phases = {
            'phase_1_critical': high_risk[:5],  # First 5 high-risk files
            'phase_2_high_risk': high_risk[5:],
            'phase_3_medium_risk': medium_risk[:10],  # First 10 medium-risk files
            'phase_4_remaining': medium_risk[10:] + low_risk
        }

        # Generate migration steps for each phase
        migration_steps = {}
        for phase_name, files in phases.items():
            migration_steps[phase_name] = {
                'files': [f.file_path for f in files],
                'estimated_effort': self._estimate_effort(files),
                'risk_level': files[0].risk_level if files else 'none',
                'steps': self._generate_phase_steps(files)
            }

        return {
            'total_files': len(file_analyses),
            'phases': migration_steps,
            'estimated_total_effort': sum(step['estimated_effort'] for step in migration_steps.values()),
            'high_risk_files': len(high_risk),
            'medium_risk_files': len(medium_risk),
            'low_risk_files': len(low_risk)
        }

    def _estimate_effort(self, files: List[FileAnalysis]) -> int:
        """Estimate effort required for a group of files."""
        total_items = sum(
            len(f.theme_manager_usage) + len(f.stylesheet_calls) + len(f.hardcoded_colors)
            for f in files
        )

        if total_items > 50:
            return 8  # high effort
        elif total_items > 20:
            return 5  # medium effort
        else:
            return 2  # low effort

    def _generate_phase_steps(self, files: List[FileAnalysis]) -> List[str]:
        """Generate specific migration steps for a phase."""
        steps = []

        for file_analysis in files:
            if file_analysis.theme_manager_usage:
                steps.append(f"Replace ThemeManager usage in {file_analysis.file_path}")

            if file_analysis.stylesheet_calls:
                steps.append(f"Convert setStyleSheet calls in {file_analysis.file_path}")

            if file_analysis.hardcoded_colors:
                steps.append(f"Replace hardcoded colors in {file_analysis.file_path}")

        return steps

    def _create_summary(self, file_analyses: List[FileAnalysis], theme_usage: Dict,
                       stylesheet_usage: Dict, hardcoded_colors: Dict) -> Dict[str, Any]:
        """Create analysis summary."""
        total_files = len(file_analyses)
        files_with_issues = len([f for f in file_analyses if f.migration_priority > 1])

        # Count different types of issues
        total_theme_manager_usage = sum(len(usage) for usage in theme_usage.values())
        total_stylesheet_calls = sum(len(calls) for calls in stylesheet_usage.values())
        total_hardcoded_colors = sum(len(colors) for colors in hardcoded_colors.values())

        # Risk distribution
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        for analysis in file_analyses:
            risk_counts[analysis.risk_level] += 1

        return {
            'total_files_analyzed': total_files,
            'files_requiring_migration': files_with_issues,
            'total_theme_manager_usage': total_theme_manager_usage,
            'total_stylesheet_calls': total_stylesheet_calls,
            'total_hardcoded_colors': total_hardcoded_colors,
            'risk_distribution': risk_counts,
            'migration_coverage': (files_with_issues / total_files * 100) if total_files > 0 else 0
        }


def main():
    """Main entry point for the dependency analysis tool."""
    parser = argparse.ArgumentParser(description='Theme Dependency Analysis Tool')
    parser.add_argument('--output', '-o', default='dependency_report.json',
                       help='Output file for the analysis report')
    parser.add_argument('--format', '-f', choices=['json', 'html', 'markdown'],
                       default='json', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--include-tests', action='store_true',
                       help='Include test files in analysis')
    parser.add_argument('--root-path', default='src',
                       help='Root path to analyze (default: src)')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run analysis
    analyzer = ThemeDependencyAnalyzer(args.root_path, args.include_tests)
    report = analyzer.analyze_codebase()

    # Output report
    if args.format == 'json':
        with open(args.output, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
    elif args.format == 'html':
        _output_html_report(report, args.output)
    elif args.format == 'markdown':
        _output_markdown_report(report, args.output)

    # Print summary to console
    print(f"\n{'='*60}")
    print("DEPENDENCY ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Files analyzed: {report.summary['total_files_analyzed']}")
    print(f"Files requiring migration: {report.summary['files_requiring_migration']}")
    print(f"ThemeManager usage: {report.summary['total_theme_manager_usage']}")
    print(f"setStyleSheet calls: {report.summary['total_stylesheet_calls']}")
    print(f"Hardcoded colors: {report.summary['total_hardcoded_colors']}")
    print(f"High risk files: {report.summary['risk_distribution']['high']}")
    print(f"Medium risk files: {report.summary['risk_distribution']['medium']}")
    print(f"Low risk files: {report.summary['risk_distribution']['low']}")
    print(f"Migration coverage: {report.summary['migration_coverage']:.1f}%")
    print(f"\nReport saved to: {args.output}")
    print(f"{'='*60}")


def _output_html_report(report: AnalysisReport, output_file: str):
    """Output analysis report in HTML format."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Theme Dependency Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .file {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
            .high-risk {{ border-left: 5px solid #ff4444; }}
            .medium-risk {{ border-left: 5px solid #ffaa00; }}
            .low-risk {{ border-left: 5px solid #44aa44; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4fd; }}
        </style>
    </head>
    <body>
        <h1>Theme Dependency Analysis Report</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">Files Analyzed: {report.summary['total_files_analyzed']}</div>
            <div class="metric">Files Requiring Migration: {report.summary['files_requiring_migration']}</div>
            <div class="metric">ThemeManager Usage: {report.summary['total_theme_manager_usage']}</div>
            <div class="metric">setStyleSheet Calls: {report.summary['total_stylesheet_calls']}</div>
            <div class="metric">Hardcoded Colors: {report.summary['total_hardcoded_colors']}</div>
        </div>

        <h2>Risk Distribution</h2>
        <div class="metric">High Risk: {report.summary['risk_distribution']['high']}</div>
        <div class="metric">Medium Risk: {report.summary['risk_distribution']['medium']}</div>
        <div class="metric">Low Risk: {report.summary['risk_distribution']['low']}</div>

        <h2>Files Requiring Migration</h2>
        {''.join(_format_file_html(f) for f in report.files if f.migration_priority > 1)}
    </body>
    </html>
    """

    with open(output_file, 'w') as f:
        f.write(html)


def _format_file_html(file_analysis: FileAnalysis) -> str:
    """Format a single file analysis as HTML."""
    risk_class = file_analysis.risk_level.replace(' ', '-')

    return f"""
    <div class="file {risk_class}">
        <h3>{file_analysis.file_path}</h3>
        <p><strong>Risk:</strong> {file_analysis.risk_level} | <strong>Priority:</strong> {file_analysis.migration_priority}</p>
        {f'<p><strong>ThemeManager Usage:</strong> {len(file_analysis.theme_manager_usage)}</p>' if file_analysis.theme_manager_usage else ''}
        {f'<p><strong>setStyleSheet Calls:</strong> {len(file_analysis.stylesheet_calls)}</p>' if file_analysis.stylesheet_calls else ''}
        {f'<p><strong>Hardcoded Colors:</strong> {len(file_analysis.hardcoded_colors)}</p>' if file_analysis.hardcoded_colors else ''}
    </div>
    """


def _output_markdown_report(report: AnalysisReport, output_file: str):
    """Output analysis report in Markdown format."""
    markdown = f"""
# Theme Dependency Analysis Report

## Summary

- **Files Analyzed:** {report.summary['total_files_analyzed']}
- **Files Requiring Migration:** {report.summary['files_requiring_migration']}
- **ThemeManager Usage:** {report.summary['total_theme_manager_usage']}
- **setStyleSheet Calls:** {report.summary['total_stylesheet_calls']}
- **Hardcoded Colors:** {report.summary['total_hardcoded_colors']}
- **Migration Coverage:** {report.summary['migration_coverage']:.1f}%

## Risk Distribution

- **High Risk:** {report.summary['risk_distribution']['high']}
- **Medium Risk:** {report.summary['risk_distribution']['medium']}
- **Low Risk:** {report.summary['risk_distribution']['low']}

## Files Requiring Migration

"""

    for file_analysis in report.files:
        if file_analysis.migration_priority > 1:
            markdown += f"""
### {file_analysis.file_path}

- **Risk Level:** {file_analysis.risk_level}
- **Migration Priority:** {file_analysis.migration_priority}/10
{f'- **ThemeManager Usage:** {len(file_analysis.theme_manager_usage)}' if file_analysis.theme_manager_usage else ''}
{f'- **setStyleSheet Calls:** {len(file_analysis.stylesheet_calls)}' if file_analysis.stylesheet_calls else ''}
{f'- **Hardcoded Colors:** {len(file_analysis.hardcoded_colors)}' if file_analysis.hardcoded_colors else ''}

"""

    with open(output_file, 'w') as f:
        f.write(markdown)


if __name__ == '__main__':
    main()