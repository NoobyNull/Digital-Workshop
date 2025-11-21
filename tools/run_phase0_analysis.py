#!/usr/bin/env python3
"""
Phase 0 Analysis Runner

This script runs the complete Phase 0 analysis suite and generates comprehensive
reports for the GUI Layout Refactoring project.

Usage:
    python tools/run_phase0_analysis.py [options]

Options:
    --output-dir DIR    Output directory for all reports (default: phase0_reports)
    --include-tests     Include test files in analysis
    --verbose          Enable verbose logging
    --dry-run          Show what would be run without executing
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Phase0AnalysisRunner:
    """
    Runner for the complete Phase 0 analysis suite.
    """

    def __init__(
        self,
        output_dir: str = "phase0_reports",
        include_tests: bool = False,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.include_tests = include_tests
        self.verbose = verbose
        self.dry_run = dry_run

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Tool configurations
        self.tools = {
            "dependency_analysis": {
                "script": "tools/dependency_analysis.py",
                "outputs": ["dependency_report.json", "dependency_report.html"],
                "args": ["--format", "json", "--format", "html"],
            },
            "stylesheet_detector": {
                "script": "tools/stylesheet_detector.py",
                "outputs": ["stylesheet_report.json", "stylesheet_report.html"],
                "args": [
                    "--format",
                    "json",
                    "--format",
                    "html",
                    "--min-risk",
                    "medium",
                ],
            },
            "migration_utils": {
                "script": "tools/migration_utils.py",
                "outputs": ["migration_report.json"],
                "args": ["generate-report", "--format", "json"],
            },
            "visual_regression_tester": {
                "script": "tools/visual_regression_tester.py",
                "outputs": ["visual_regression_report.html"],
                "args": [
                    "--generate-baselines",
                    "--output",
                    "visual_regression_report.html",
                ],
            },
        }

        if include_tests:
            for tool in self.tools.values():
                tool["args"].extend(["--include-tests"])

        if verbose:
            for tool in self.tools.values():
                tool["args"].extend(["--verbose"])

    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run the complete Phase 0 analysis suite.

        Returns:
            Summary of all analysis results
        """
        logger.info("Starting Phase 0 complete analysis")

        results = {}
        execution_order = [
            "dependency_analysis",
            "stylesheet_detector",
            "migration_utils",
            "visual_regression_tester",
        ]

        for tool_name in execution_order:
            try:
                logger.info(f"Running {tool_name}...")
                result = self._run_tool(tool_name)
                results[tool_name] = result
            except Exception as e:
                logger.error(f"Failed to run {tool_name}: {e}")
                results[tool_name] = {"error": str(e), "success": False}

        # Generate summary report
        summary = self._generate_summary_report(results)

        # Save summary
        summary_path = self.output_dir / "phase0_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Phase 0 analysis complete. Summary saved to {summary_path}")
        return summary

    def _run_tool(self, tool_name: str) -> Dict[str, Any]:
        """Run a specific analysis tool."""
        tool_config = self.tools[tool_name]

        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": f"python {tool_config['script']} {' '.join(tool_config['args'])}",
                "outputs": [
                    str(self.output_dir / output) for output in tool_config["outputs"]
                ],
            }

        # Build command
        cmd = [sys.executable, tool_config["script"]] + tool_config["args"]
        for i, arg in enumerate(tool_config["args"]):
            if arg in ["--output", "-o"]:
                # Override output path to use our output directory
                cmd[i + 1] = str(self.output_dir / tool_config["outputs"][0])

        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
            "outputs": [
                str(self.output_dir / output) for output in tool_config["outputs"]
            ],
        }

    def _generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary report."""

        # Collect all output files
        all_outputs = []
        for tool_result in results.values():
            if tool_result.get("success") and not tool_result.get("dry_run"):
                all_outputs.extend(tool_result.get("outputs", []))

        # Analyze results
        successful_tools = [
            name for name, result in results.items() if result.get("success")
        ]
        failed_tools = [
            name for name, result in results.items() if not result.get("success")
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(results)

        summary = {
            "execution_info": {
                "timestamp": self._get_timestamp(),
                "output_directory": str(self.output_dir),
                "include_tests": self.include_tests,
                "verbose": self.verbose,
                "dry_run": self.dry_run,
            },
            "results": results,
            "summary": {
                "total_tools": len(self.tools),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "success_rate": (
                    len(successful_tools) / len(self.tools) if self.tools else 0
                ),
                "output_files": all_outputs,
            },
            "recommendations": recommendations,
            "next_steps": [
                "Review dependency analysis report for migration planning",
                "Examine stylesheet detection results for hardcoded style patterns",
                "Use migration utilities to update imports and styles",
                "Run visual regression tests to establish baselines",
                "Begin phased migration starting with high-risk files",
            ],
        }

        return summary

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Check dependency analysis
        if "dependency_analysis" in results:
            dep_result = results["dependency_analysis"]
            if dep_result.get("success") and not dep_result.get("dry_run"):
                try:
                    with open(self.output_dir / "dependency_report.json") as f:
                        dep_data = json.load(f)

                    high_risk = dep_data["summary"]["risk_distribution"]["high"]
                    if high_risk > 0:
                        recommendations.append(
                            f"Migrate {high_risk} high-risk files first"
                        )
                except Exception:
                    pass

        # Check stylesheet detection
        if "stylesheet_detector" in results:
            style_result = results["stylesheet_detector"]
            if style_result.get("success") and not style_result.get("dry_run"):
                try:
                    with open(self.output_dir / "stylesheet_report.json") as f:
                        style_data = json.load(f)

                    total_calls = style_data["summary"]["total_stylesheet_calls"]
                    if total_calls > 0:
                        recommendations.append(
                            f"Convert {total_calls} setStyleSheet() calls to qt-material"
                        )
                except Exception:
                    pass

        # Check migration validation
        if "migration_utils" in results:
            mig_result = results["migration_utils"]
            if mig_result.get("success") and not mig_result.get("dry_run"):
                try:
                    with open(self.output_dir / "migration_report.json") as f:
                        mig_data = json.load(f)

                    completeness = mig_data["summary"]["migration_completeness"]
                    recommendations.append(
                        f"Achieve {100 - completeness:.1f}% migration completeness"
                    )
                except Exception:
                    pass

        # General recommendations
        recommendations.extend(
            [
                "Set up visual regression testing baselines before making changes",
                "Create backup of current codebase before migration",
                "Test theme functionality after each migration phase",
                "Update documentation to reflect new qt-material usage patterns",
            ]
        )

        return recommendations

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print analysis summary to console."""
        print(f"\n{'='*60}")
        print("PHASE 0 ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Output Directory: {summary['execution_info']['output_directory']}")
        print(f"Success Rate: {summary['summary']['success_rate']:.1%}")
        print(
            f"Successful Tools: {summary['summary']['successful_tools']}/{summary['summary']['total_tools']}"
        )

        if summary["summary"]["failed_tools"] > 0:
            print(f"Failed Tools: {', '.join(summary['summary']['failed_tools'])}")

        print(f"\nOutput Files:")
        for output_file in summary["summary"]["output_files"]:
            print(f"  - {output_file}")

        print(f"\nRecommendations:")
        for i, rec in enumerate(summary["recommendations"][:5], 1):
            print(f"  {i}. {rec}")

        print(f"\nNext Steps:")
        for i, step in enumerate(summary["next_steps"][:3], 1):
            print(f"  {i}. {step}")

        print(f"\nSummary Report: {self.output_dir}/phase0_summary.json")
        print(f"{'='*60}")


def main():
    """Main entry point for Phase 0 analysis runner."""

    parser = argparse.ArgumentParser(description="Phase 0 Analysis Runner")
    parser.add_argument(
        "--output-dir",
        default="phase0_reports",
        help="Output directory for all reports",
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )

    args = parser.parse_args()

    # Initialize and run analysis
    runner = Phase0AnalysisRunner(
        output_dir=args.output_dir,
        include_tests=args.include_tests,
        verbose=args.verbose,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("DRY RUN - Showing what would be executed:")
        print(f"Output Directory: {args.output_dir}")
        for tool_name, tool_config in runner.tools.items():
            print(f"\n{tool_name}:")
            print(
                f"  Command: python {tool_config['script']} {' '.join(tool_config['args'])}"
            )
            print(
                f"  Outputs: {[str(runner.output_dir / output) for output in tool_config['outputs']]}"
            )
        return

    # Run complete analysis
    summary = runner.run_complete_analysis()

    # Print summary
    runner.print_summary(summary)


if __name__ == "__main__":
    main()
