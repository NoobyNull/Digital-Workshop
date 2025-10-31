"""
Quality Assurance Framework for Candy-Cadence Testing System.

This module provides comprehensive quality assurance tools including:
- Code quality metrics and reporting
- Static code analysis integration
- Test coverage reporting and analysis
- Quality gates for CI/CD
- Test result analytics and reporting
- Code review automation tools
- Quality score calculation and tracking
"""

import gc
import json
import os
import re
import sys
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.logging_config import get_logger
from src.core.enhanced_error_handler import EnhancedErrorHandler


@dataclass
class QualityMetric:
    """Individual quality metric result."""
    name: str
    value: float
    threshold: float
    status: str  # "PASS", "WARN", "FAIL"
    description: str
    weight: float = 1.0


@dataclass
class CodeQualityReport:
    """Comprehensive code quality report."""
    timestamp: str
    overall_score: float
    metrics: List[QualityMetric]
    test_coverage: float
    performance_score: float
    reliability_score: float
    maintainability_score: float
    security_score: float
    summary: Dict[str, Any]


@dataclass
class TestCoverageReport:
    """Test coverage analysis report."""
    total_lines: int
    covered_lines: int
    uncovered_lines: int
    coverage_percentage: float
    module_coverage: Dict[str, float]
    missing_coverage: List[str]


class QualityAssuranceEngine:
    """Main quality assurance engine."""
    
    def __init__(self, project_root: str = None):
        """Initialize quality assurance engine."""
        self.logger = get_logger(__name__)
        self.project_root = Path(project_root or Path(__file__).parent.parent)
        self.coverage_file = self.project_root / "coverage.json"
        self.reports_dir = self.project_root / "reports" / "quality"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Quality thresholds
        self.quality_thresholds = {
            "test_coverage_min": 80.0,
            "test_coverage_good": 90.0,
            "code_complexity_max": 10.0,
            "code_duplication_max": 5.0,
            "security_vulnerabilities_max": 0,
            "performance_regression_max": 20.0,
            "memory_leak_tolerance": 1.0  # MB per iteration
        }
        
        # Scoring weights
        self.scoring_weights = {
            "test_coverage": 0.25,
            "code_quality": 0.20,
            "performance": 0.20,
            "reliability": 0.15,
            "maintainability": 0.10,
            "security": 0.10
        }
    
    def run_comprehensive_quality_assessment(self) -> CodeQualityReport:
        """Run comprehensive quality assessment."""
        self.logger.info("Starting comprehensive quality assessment...")
        
        # Collect all quality metrics
        metrics = []
        
        # Test coverage metrics
        coverage_metrics = self._analyze_test_coverage()
        metrics.extend(coverage_metrics)
        
        # Code quality metrics
        code_quality_metrics = self._analyze_code_quality()
        metrics.extend(code_quality_metrics)
        
        # Performance metrics
        performance_metrics = self._analyze_performance_quality()
        metrics.extend(performance_metrics)
        
        # Security metrics
        security_metrics = self._analyze_security_quality()
        metrics.extend(security_metrics)
        
        # Calculate component scores
        test_coverage_score = self._calculate_component_score(
            [m for m in metrics if "coverage" in m.name.lower()],
            "test_coverage"
        )
        
        code_quality_score = self._calculate_component_score(
            [m for m in metrics if m.name.startswith("code_")],
            "code_quality"
        )
        
        performance_score = self._calculate_component_score(
            [m for m in metrics if m.name.startswith("perf_")],
            "performance"
        )
        
        reliability_score = self._calculate_reliability_score(metrics)
        maintainability_score = self._calculate_maintainability_score(metrics)
        security_score = self._calculate_security_score(metrics)
        
        # Calculate overall quality score
        overall_score = (
            test_coverage_score * self.scoring_weights["test_coverage"] +
            code_quality_score * self.scoring_weights["code_quality"] +
            performance_score * self.scoring_weights["performance"] +
            reliability_score * self.scoring_weights["reliability"] +
            maintainability_score * self.scoring_weights["maintainability"] +
            security_score * self.scoring_weights["security"]
        )
        
        # Create comprehensive report
        report = CodeQualityReport(
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            metrics=metrics,
            test_coverage=test_coverage_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            maintainability_score=maintainability_score,
            security_score=security_score,
            summary=self._generate_quality_summary(metrics, overall_score)
        )
        
        # Save report
        self._save_quality_report(report)
        
        self.logger.info(f"Quality assessment completed. Overall score: {overall_score:.1f}/100")
        
        return report
    
    def _analyze_test_coverage(self) -> List[QualityMetric]:
        """Analyze test coverage metrics."""
        metrics = []
        
        try:
            # Run coverage analysis
            coverage_data = self._run_coverage_analysis()
            
            # Overall coverage percentage
            overall_coverage = coverage_data.get("total_coverage", 0.0)
            
            metrics.append(QualityMetric(
                name="test_coverage_overall",
                value=overall_coverage,
                threshold=self.quality_thresholds["test_coverage_min"],
                status="PASS" if overall_coverage >= self.quality_thresholds["test_coverage_min"] 
                      else "FAIL",
                description="Overall test coverage percentage",
                weight=2.0
            ))
            
            # Critical module coverage
            critical_modules = ["parsers", "core", "gui"]
            for module in critical_modules:
                module_coverage = coverage_data.get("module_coverage", {}).get(module, 0.0)
                status = "PASS" if module_coverage >= self.quality_thresholds["test_coverage_min"] else "FAIL"
                
                metrics.append(QualityMetric(
                    name=f"test_coverage_{module}",
                    value=module_coverage,
                    threshold=self.quality_thresholds["test_coverage_min"],
                    status=status,
                    description=f"Test coverage for {module} module",
                    weight=1.5
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to analyze test coverage: {e}")
            metrics.append(QualityMetric(
                name="test_coverage_analysis",
                value=0.0,
                threshold=0.0,
                status="FAIL",
                description=f"Coverage analysis failed: {e}",
                weight=1.0
            ))
        
        return metrics
    
    def _run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis using coverage.py."""
        try:
            # Run tests with coverage
            result = subprocess.run([
                sys.executable, "-m", "coverage", "run", "-m", "pytest", 
                "tests/", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            # Generate coverage report
            report_result = subprocess.run([
                sys.executable, "-m", "coverage", "json", "-o", str(self.coverage_file)
            ], cwd=self.project_root, capture_output=True, text=True)
            
            # Load coverage data
            if self.coverage_file.exists():
                with open(self.coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                # Process coverage data
                total_files = len(coverage_data.get("files", {}))
                total_lines = sum(f.get("summary", {}).get("num_statements", 0) 
                                for f in coverage_data.get("files", {}).values())
                covered_lines = sum(f.get("summary", {}).get("covered_lines", 0) 
                                  for f in coverage_data.get("files", {}).values())
                
                total_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
                
                # Calculate module-level coverage
                module_coverage = {}
                for file_path, file_data in coverage_data.get("files", {}).items():
                    module = file_path.split('/')[0] if '/' in file_path else file_path.split('\\')[0]
                    if module not in module_coverage:
                        module_coverage[module] = []
                    
                    file_coverage = file_data.get("summary", {}).get("percent_covered", 0.0)
                    module_coverage[module].append(file_coverage)
                
                # Average module coverage
                for module in module_coverage:
                    module_coverage[module] = sum(module_coverage[module]) / len(module_coverage[module])
                
                return {
                    "total_coverage": total_coverage,
                    "module_coverage": module_coverage,
                    "files": total_files,
                    "total_lines": total_lines,
                    "covered_lines": covered_lines
                }
            else:
                return {"total_coverage": 0.0, "module_coverage": {}}
                
        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {e}")
            return {"total_coverage": 0.0, "module_coverage": {}}
    
    def _analyze_code_quality(self) -> List[QualityMetric]:
        """Analyze code quality metrics."""
        metrics = []
        
        # Analyze source files
        source_files = list(self.project_root.rglob("*.py"))
        source_files = [f for f in source_files if not f.is_relative_to(self.project_root / "tests")]
        
        if not source_files:
            return [QualityMetric(
                name="code_quality_analysis",
                value=0.0,
                threshold=0.0,
                status="WARN",
                description="No source files found for quality analysis",
                weight=1.0
            )]
        
        # Complexity analysis
        complexity_metrics = self._analyze_complexity(source_files)
        metrics.extend(complexity_metrics)
        
        # Code duplication analysis
        duplication_metrics = self._analyze_code_duplication(source_files)
        metrics.extend(duplication_metrics)
        
        # Style and standards analysis
        style_metrics = self._analyze_code_style(source_files)
        metrics.extend(style_metrics)
        
        return metrics
    
    def _analyze_complexity(self, source_files: List[Path]) -> List[QualityMetric]:
        """Analyze code complexity metrics."""
        metrics = []
        
        try:
            # Simple complexity analysis using AST
            import ast
            
            total_complexity = 0
            file_count = 0
            high_complexity_files = 0
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    # Calculate cyclomatic complexity
                    complexity = self._calculate_cyclomatic_complexity(tree)
                    total_complexity += complexity
                    file_count += 1
                    
                    if complexity > self.quality_thresholds["code_complexity_max"]:
                        high_complexity_files += 1
                        
                except Exception as e:
                    self.logger.warning(f"Failed to analyze complexity for {file_path}: {e}")
            
            if file_count > 0:
                avg_complexity = total_complexity / file_count
                
                metrics.append(QualityMetric(
                    name="code_complexity_avg",
                    value=avg_complexity,
                    threshold=self.quality_thresholds["code_complexity_max"],
                    status="PASS" if avg_complexity <= self.quality_thresholds["code_complexity_max"] else "FAIL",
                    description="Average cyclomatic complexity per file",
                    weight=1.5
                ))
                
                high_complexity_percentage = (high_complexity_files / file_count) * 100
                
                metrics.append(QualityMetric(
                    name="code_complexity_high_files",
                    value=high_complexity_percentage,
                    threshold=10.0,  # Max 10% of files should have high complexity
                    status="PASS" if high_complexity_percentage <= 10.0 else "FAIL",
                    description="Percentage of files with high complexity",
                    weight=1.0
                ))
        
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            metrics.append(QualityMetric(
                name="code_complexity_analysis",
                value=0.0,
                threshold=0.0,
                status="FAIL",
                description=f"Complexity analysis failed: {e}",
                weight=1.0
            ))
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Count decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _analyze_code_duplication(self, source_files: List[Path]) -> List[QualityMetric]:
        """Analyze code duplication."""
        metrics = []
        
        try:
            # Simple duplication detection using content similarity
            file_contents = {}
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_contents[file_path] = content
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_path}: {e}")
            
            # Detect exact duplicates
            content_counts = defaultdict(list)
            for file_path, content in file_contents.items():
                content_counts[content].append(file_path)
            
            duplicates = {content: files for content, files in content_counts.items() 
                         if len(files) > 1}
            
            duplication_percentage = (len(duplicates) / len(file_contents)) * 100 if file_contents else 0
            
            metrics.append(QualityMetric(
                name="code_duplication",
                value=duplication_percentage,
                threshold=self.quality_thresholds["code_duplication_max"],
                status="PASS" if duplication_percentage <= self.quality_thresholds["code_duplication_max"] else "FAIL",
                description="Percentage of duplicated code blocks",
                weight=1.0
            ))
            
        except Exception as e:
            self.logger.error(f"Code duplication analysis failed: {e}")
            metrics.append(QualityMetric(
                name="code_duplication_analysis",
                value=0.0,
                threshold=0.0,
                status="FAIL",
                description=f"Duplication analysis failed: {e}",
                weight=1.0
            ))
        
        return metrics
    
    def _analyze_code_style(self, source_files: List[Path]) -> List[QualityMetric]:
        """Analyze code style and standards compliance."""
        metrics = []
        
        try:
            style_issues = []
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Check for common style issues
                    for i, line in enumerate(lines, 1):
                        line = line.rstrip()
                        
                        # Check for TODO/FIXME comments
                        if re.search(r'#\s*(TODO|FIXME|HACK)', line, re.IGNORECASE):
                            style_issues.append({
                                "file": str(file_path),
                                "line": i,
                                "issue": "TODO/FIXME comment",
                                "severity": "medium"
                            })
                        
                        # Check for long lines
                        if len(line) > 120:
                            style_issues.append({
                                "file": str(file_path),
                                "line": i,
                                "issue": "Line too long",
                                "severity": "low"
                            })
                        
                        # Check for trailing whitespace
                        if line != line.rstrip():
                            style_issues.append({
                                "file": str(file_path),
                                "line": i,
                                "issue": "Trailing whitespace",
                                "severity": "low"
                            })
                
                except Exception as e:
                    self.logger.warning(f"Failed to analyze style for {file_path}: {e}")
            
            # Calculate style score
            total_files = len(source_files)
            issues_per_file = len(style_issues) / total_files if total_files > 0 else 0
            
            # Convert to score (fewer issues = higher score)
            style_score = max(0, 100 - (issues_per_file * 10))
            
            metrics.append(QualityMetric(
                name="code_style_compliance",
                value=style_score,
                threshold=80.0,
                status="PASS" if style_score >= 80.0 else "FAIL",
                description="Code style compliance score",
                weight=1.0
            ))
            
            # Count critical style issues
            critical_issues = [issue for issue in style_issues 
                             if issue.get("severity") == "high"]
            
            metrics.append(QualityMetric(
                name="code_style_critical_issues",
                value=len(critical_issues),
                threshold=0,
                status="PASS" if len(critical_issues) == 0 else "FAIL",
                description="Number of critical style issues",
                weight=1.5
            ))
            
        except Exception as e:
            self.logger.error(f"Code style analysis failed: {e}")
            metrics.append(QualityMetric(
                name="code_style_analysis",
                value=0.0,
                threshold=0.0,
                status="FAIL",
                description=f"Style analysis failed: {e}",
                weight=1.0
            ))
        
        return metrics
    
    def _analyze_performance_quality(self) -> List[QualityMetric]:
        """Analyze performance-related quality metrics."""
        metrics = []
        
        # Load performance test results if available
        performance_reports = list(self.project_root.glob("reports/performance/benchmark_results_*.json"))
        
        if performance_reports:
            latest_report = max(performance_reports, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_report, 'r') as f:
                    perf_data = json.load(f)
                
                summary = perf_data.get("summary", {})
                
                # Performance regression detection
                regressions = summary.get("regressions_detected", 0)
                total_tests = summary.get("total_tests", 1)
                regression_rate = (regressions / total_tests * 100) if total_tests > 0 else 0
                
                metrics.append(QualityMetric(
                    name="perf_regression_rate",
                    value=regression_rate,
                    threshold=self.quality_thresholds["performance_regression_max"],
                    status="PASS" if regression_rate <= self.quality_thresholds["performance_regression_max"] else "FAIL",
                    description="Performance regression detection rate",
                    weight=2.0
                ))
                
                # Average execution time
                avg_execution_time = summary.get("avg_execution_time", 0.0)
                
                metrics.append(QualityMetric(
                    name="perf_avg_execution_time",
                    value=avg_execution_time,
                    threshold=10.0,  # Max 10 seconds average
                    status="PASS" if avg_execution_time <= 10.0 else "FAIL",
                    description="Average test execution time",
                    weight=1.0
                ))
                
                # Memory usage efficiency
                max_memory = summary.get("max_memory_usage", 0.0)
                
                metrics.append(QualityMetric(
                    name="perf_memory_usage",
                    value=max_memory,
                    threshold=500.0,  # Max 500MB
                    status="PASS" if max_memory <= 500.0 else "FAIL",
                    description="Maximum memory usage during tests",
                    weight=1.5
                ))
                
            except Exception as e:
                self.logger.error(f"Performance analysis failed: {e}")
                metrics.append(QualityMetric(
                    name="perf_analysis",
                    value=0.0,
                    threshold=0.0,
                    status="FAIL",
                    description=f"Performance analysis failed: {e}",
                    weight=1.0
                ))
        else:
            # No performance data available
            metrics.append(QualityMetric(
                name="perf_data_available",
                value=0.0,
                threshold=1.0,
                status="WARN",
                description="No performance test data available",
                weight=0.5
            ))
        
        return metrics
    
    def _analyze_security_quality(self) -> List[QualityMetric]:
        """Analyze security-related quality metrics."""
        metrics = []
        
        try:
            security_issues = []
            
            # Scan for potential security issues in source files
            source_files = list(self.project_root.rglob("*.py"))
            source_files = [f for f in source_files if not f.is_relative_to(self.project_root / "tests")]
            
            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for common security issues
                    patterns = [
                        (r'eval\s*\(', "Use of eval() function"),
                        (r'exec\s*\(', "Use of exec() function"),
                        (r'os\.system\s*\(', "Use of os.system()"),
                        (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Shell=True in subprocess"),
                        (r'pickle\.load[s]?\s*\(', "Use of pickle.load()"),
                        (r'yaml\.load\s*\(', "Use of yaml.load()"),
                    ]
                    
                    for pattern, description in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            security_issues.append({
                                "file": str(file_path),
                                "issue": description,
                                "severity": "high"
                            })
                
                except Exception as e:
                    self.logger.warning(f"Failed to analyze security in {file_path}: {e}")
            
            # Count high-severity security issues
            high_severity_issues = [issue for issue in security_issues 
                                  if issue.get("severity") == "high"]
            
            metrics.append(QualityMetric(
                name="security_high_severity_issues",
                value=len(high_severity_issues),
                threshold=self.quality_thresholds["security_vulnerabilities_max"],
                status="PASS" if len(high_severity_issues) <= self.quality_thresholds["security_vulnerabilities_max"] else "FAIL",
                description="Number of high-severity security issues",
                weight=2.0
            ))
            
            # Security scan coverage
            scanned_files = len(source_files)
            metrics.append(QualityMetric(
                name="security_scan_coverage",
                value=scanned_files,
                threshold=1.0,
                status="PASS" if scanned_files > 0 else "FAIL",
                description="Number of files scanned for security issues",
                weight=0.5
            ))
            
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            metrics.append(QualityMetric(
                name="security_analysis",
                value=0.0,
                threshold=0.0,
                status="FAIL",
                description=f"Security analysis failed: {e}",
                weight=1.0
            ))
        
        return metrics
    
    def _calculate_component_score(self, metrics: List[QualityMetric], component_name: str) -> float:
        """Calculate component score from metrics."""
        if not metrics:
            return 0.0
        
        total_weight = sum(m.weight for m in metrics)
        if total_weight == 0:
            return 0.0
        
        weighted_score = 0.0
        
        for metric in metrics:
            # Convert metric status to score (100 for PASS, 50 for WARN, 0 for FAIL)
            if metric.status == "PASS":
                metric_score = 100.0
            elif metric.status == "WARN":
                metric_score = 50.0
            else:  # FAIL
                metric_score = 0.0
            
            weighted_score += metric_score * metric.weight
        
        return weighted_score / total_weight
    
    def _calculate_reliability_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate reliability score."""
        # Focus on test success rates and error handling
        reliability_metrics = [
            m for m in metrics 
            if any(keyword in m.name.lower() for keyword in ["test_", "coverage", "failure"])
        ]
        
        return self._calculate_component_score(reliability_metrics, "reliability")
    
    def _calculate_maintainability_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate maintainability score."""
        # Focus on code quality metrics
        maintainability_metrics = [
            m for m in metrics 
            if any(keyword in m.name.lower() for keyword in ["complexity", "duplication", "style"])
        ]
        
        return self._calculate_component_score(maintainability_metrics, "maintainability")
    
    def _calculate_security_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate security score."""
        security_metrics = [m for m in metrics if m.name.startswith("security_")]
        return self._calculate_component_score(security_metrics, "security")
    
    def _generate_quality_summary(self, metrics: List[QualityMetric], overall_score: float) -> Dict[str, Any]:
        """Generate quality assessment summary."""
        total_metrics = len(metrics)
        passed_metrics = len([m for m in metrics if m.status == "PASS"])
        failed_metrics = len([m for m in metrics if m.status == "FAIL"])
        warning_metrics = len([m for m in metrics if m.status == "WARN"])
        
        # Identify critical issues
        critical_issues = [m for m in metrics if m.status == "FAIL" and m.weight >= 1.5]
        
        # Generate recommendations
        recommendations = []
        
        if overall_score < 70:
            recommendations.append("Overall quality score is below acceptable threshold")
        
        if failed_metrics > 0:
            recommendations.append(f"Address {failed_metrics} failed quality metrics")
        
        if any(m.name.startswith("test_coverage") and m.status == "FAIL" for m in metrics):
            recommendations.append("Improve test coverage to meet minimum requirements")
        
        if any(m.name.startswith("perf_") and m.status == "FAIL" for m in metrics):
            recommendations.append("Address performance issues and regressions")
        
        if any(m.name.startswith("security_") and m.status == "FAIL" for m in metrics):
            recommendations.append("Fix security vulnerabilities immediately")
        
        return {
            "total_metrics": total_metrics,
            "passed_metrics": passed_metrics,
            "failed_metrics": failed_metrics,
            "warning_metrics": warning_metrics,
            "success_rate": (passed_metrics / total_metrics * 100) if total_metrics > 0 else 0,
            "critical_issues": len(critical_issues),
            "critical_issues_details": [m.description for m in critical_issues],
            "recommendations": recommendations,
            "quality_grade": self._calculate_quality_grade(overall_score)
        }
    
    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate quality grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _save_quality_report(self, report: CodeQualityReport):
        """Save quality report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"quality_report_{timestamp}.json"
        
        try:
            # Convert report to dict for JSON serialization
            report_dict = {
                "timestamp": report.timestamp,
                "overall_score": report.overall_score,
                "metrics": [asdict(m) for m in report.metrics],
                "test_coverage": report.test_coverage,
                "performance_score": report.performance_score,
                "reliability_score": report.reliability_score,
                "maintainability_score": report.maintainability_score,
                "security_score": report.security_score,
                "summary": report.summary
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_dict, f, indent=2)
            
            self.logger.info(f"Quality report saved to {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save quality report: {e}")
    
    def check_quality_gates(self, report: CodeQualityReport) -> Tuple[bool, List[str]]:
        """
        Check if quality gates are satisfied.
        
        Returns:
            Tuple of (gates_passed, list_of_failures)
        """
        failures = []
        
        # Overall quality score gate
        if report.overall_score < 70.0:
            failures.append(f"Overall quality score {report.overall_score:.1f} below minimum threshold 70.0")
        
        # Test coverage gate
        if report.test_coverage < self.quality_thresholds["test_coverage_min"]:
            failures.append(f"Test coverage {report.test_coverage:.1f}% below minimum threshold {self.quality_thresholds['test_coverage_min']}%")
        
        # Security gate
        if report.security_score < 80.0:
            failures.append(f"Security score {report.security_score:.1f} below minimum threshold 80.0")
        
        # Performance gate
        if report.performance_score < 60.0:
            failures.append(f"Performance score {report.performance_score:.1f} below minimum threshold 60.0")
        
        # Critical failures
        critical_failures = [m for m in report.metrics if m.status == "FAIL" and m.weight >= 2.0]
        if critical_failures:
            failures.append(f"Critical quality failures detected: {len(critical_failures)}")
        
        gates_passed = len(failures) == 0
        
        return gates_passed, failures


class QualityAssuranceReporter:
    """Generate human-readable quality assurance reports."""
    
    def __init__(self, qa_engine: QualityAssuranceEngine):
        """Initialize reporter."""
        self.qa_engine = qa_engine
    
    def generate_markdown_report(self, report: CodeQualityReport) -> str:
        """Generate markdown-formatted quality report."""
        lines = []
        
        # Header
        lines.append("# Candy-Cadence Quality Assurance Report")
        lines.append("")
        lines.append(f"**Generated:** {report.timestamp}")
        lines.append(f"**Overall Score:** {report.overall_score:.1f}/100 ({report.summary['quality_grade']})")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        summary = report.summary
        lines.append(f"- **Total Metrics:** {summary['total_metrics']}")
        lines.append(f"- **Passed:** {summary['passed_metrics']} ({summary['success_rate']:.1f}%)")
        lines.append(f"- **Failed:** {summary['failed_metrics']}")
        lines.append(f"- **Warnings:** {summary['warning_metrics']}")
        lines.append(f"- **Critical Issues:** {summary['critical_issues']}")
        lines.append("")
        
        # Component Scores
        lines.append("## Component Scores")
        lines.append("")
        lines.append(f"- **Test Coverage:** {report.test_coverage:.1f}/100")
        lines.append(f"- **Performance:** {report.performance_score:.1f}/100")
        lines.append(f"- **Reliability:** {report.reliability_score:.1f}/100")
        lines.append(f"- **Maintainability:** {report.maintainability_score:.1f}/100")
        lines.append(f"- **Security:** {report.security_score:.1f}/100")
        lines.append("")
        
        # Detailed Metrics
        lines.append("## Detailed Metrics")
        lines.append("")
        lines.append("| Metric | Value | Threshold | Status | Weight |")
        lines.append("|--------|-------|-----------|---------|--------|")
        
        for metric in report.metrics:
            status_icon = "✅" if metric.status == "PASS" else "⚠️" if metric.status == "WARN" else "❌"
            lines.append(f"| {metric.name} | {metric.value:.1f} | {metric.threshold:.1f} | {status_icon} {metric.status} | {metric.weight:.1f} |")
        
        lines.append("")
        
        # Recommendations
        if report.summary['recommendations']:
            lines.append("## Recommendations")
            lines.append("")
            for rec in report.summary['recommendations']:
                lines.append(f"- {rec}")
            lines.append("")
        
        # Critical Issues
        if report.summary['critical_issues_details']:
            lines.append("## Critical Issues")
            lines.append("")
            for issue in report.summary['critical_issues_details']:
                lines.append(f"- {issue}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_html_report(self, report: CodeQualityReport) -> str:
        """Generate HTML-formatted quality report."""
        # Simple HTML report generation
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Candy-Cadence Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .score {{ font-size: 2em; font-weight: bold; color: {'green' if report.overall_score >= 70 else 'red'}; }}
        .metric {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .pass {{ border-left-color: green; background-color: #f0fff0; }}
        .warn {{ border-left-color: orange; background-color: #fff8dc; }}
        .fail {{ border-left-color: red; background-color: #fff0f0; }}
        .component {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Candy-Cadence Quality Assurance Report</h1>
        <p>Generated: {report.timestamp}</p>
        <p class="score">Overall Score: {report.overall_score:.1f}/100 ({report.summary['quality_grade']})</p>
    </div>
    
    <div class="component">
        <h2>Component Scores</h2>
        <p>Test Coverage: {report.test_coverage:.1f}/100</p>
        <p>Performance: {report.performance_score:.1f}/100</p>
        <p>Reliability: {report.reliability_score:.1f}/100</p>
        <p>Maintainability: {report.maintainability_score:.1f}/100</p>
        <p>Security: {report.security_score:.1f}/100</p>
    </div>
    
    <div class="component">
        <h2>Detailed Metrics</h2>
"""
        
        for metric in report.metrics:
            css_class = metric.status.lower()
            html += f"""
        <div class="metric {css_class}">
            <strong>{metric.name}</strong><br>
            Value: {metric.value:.1f} | Threshold: {metric.threshold:.1f} | Status: {metric.status}<br>
            {metric.description}
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html


if __name__ == '__main__':
    # Run quality assurance assessment
    qa_engine = QualityAssuranceEngine()
    report = qa_engine.run_comprehensive_quality_assessment()
    
    # Check quality gates
    gates_passed, failures = qa_engine.check_quality_gates(report)
    
    # Generate reports
    reporter = QualityAssuranceReporter(qa_engine)
    
    markdown_report = reporter.generate_markdown_report(report)
    html_report = reporter.generate_html_report(report)
    
    # Save reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with open(f"quality_report_{timestamp}.md", 'w') as f:
        f.write(markdown_report)
    
    with open(f"quality_report_{timestamp}.html", 'w') as f:
        f.write(html_report)
    
    print("="*60)
    print("QUALITY ASSURANCE ASSESSMENT COMPLETE")
    print("="*60)
    print(f"Overall Score: {report.overall_score:.1f}/100")
    print(f"Quality Grade: {report.summary['quality_grade']}")
    print(f"Quality Gates: {'PASSED' if gates_passed else 'FAILED'}")
    
    if failures:
        print("\nQuality Gate Failures:")
        for failure in failures:
            print(f"  - {failure}")
    
    print(f"\nReports generated:")
    print(f"  - quality_report_{timestamp}.md")
    print(f"  - quality_report_{timestamp}.html")
    
    # Exit with appropriate code
    exit(0 if gates_passed else 1)