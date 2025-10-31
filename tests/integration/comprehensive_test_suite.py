#!/usr/bin/env python3
"""
Comprehensive Test Suite - Unified Testing Framework

Integrates all five testing components into a cohesive, user-friendly framework:
1. Monolithic Module Detection
2. File Naming Convention Validation  
3. Unified Test Execution
4. Code Quality Validation
5. Quality Gate Enforcement

Provides both interactive and batch modes with comprehensive reporting.
"""

import argparse
import json
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from a single tool execution."""
    tool_name: str
    success: bool
    execution_time: float
    exit_code: int
    output_path: str
    metrics: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    error_message: Optional[str] = None

@dataclass
class ProgressInfo:
    """Progress information for real-time updates."""
    current_tool: str
    completed_tools: int
    total_tools: int
    current_step: str
    progress_percentage: float
    estimated_time_remaining: float

class ProgressTracker:
    """Tracks and displays real-time progress."""
    
    def __init__(self, total_tools: int):
        self.total_tools = total_tools
        self.completed_tools = 0
        self.start_time = time.time()
        self.current_tool = ""
        self.current_step = ""
        self.lock = threading.Lock()
        
    def update_progress(self, tool_name: str, step: str, completed: bool = False):
        """Update progress information."""
        with self.lock:
            if completed:
                self.completed_tools += 1
                self.current_tool = ""
                self.current_step = ""
            else:
                self.current_tool = tool_name
                self.current_step = step
            
            elapsed_time = time.time() - self.start_time
            if self.completed_tools > 0:
                avg_time_per_tool = elapsed_time / self.completed_tools
                remaining_tools = self.total_tools - self.completed_tools
                estimated_remaining = remaining_tools * avg_time_per_tool
            else:
                estimated_remaining = 0
            
            progress_percentage = (self.completed_tools / self.total_tools) * 100
            
            progress_info = ProgressInfo(
                current_tool=self.current_tool,
                completed_tools=self.completed_tools,
                total_tools=self.total_tools,
                current_step=self.current_step,
                progress_percentage=progress_percentage,
                estimated_time_remaining=estimated_remaining
            )
            
            self._display_progress(progress_info)
    
    def _display_progress(self, progress: ProgressInfo):
        """Display progress information."""
        if progress.current_tool:
            print(f"\r[{progress.completed_tools}/{progress.total_tools}] "
                  f"Running {progress.current_tool}: {progress.current_step} "
                  f"({progress.progress_percentage:.1f}%) "
                  f"ETA: {progress.estimated_time_remaining:.0f}s", end='', flush=True)
        else:
            print(f"\r[{progress.completed_tools}/{progress.total_tools}] "
                  f"Progress: {progress.progress_percentage:.1f}% "
                  f"ETA: {progress.estimated_time_remaining:.0f}s", end='', flush=True)

class ComprehensiveTestSuite:
    """Main unified testing framework orchestrator."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("test_framework_config.json")
        self.config = self._load_config()
        self.progress_tracker = None
        self.results: List[ToolResult] = []
        
        # Tool configurations
        self.tools = {
            'monolithic_detector': {
                'script': 'monolithic_detector.py',
                'enabled': self.config.get('tools', {}).get('monolithic_detector', {}).get('enabled', True),
                'args': self._get_monolithic_args(),
                'timeout': self.config.get('tools', {}).get('monolithic_detector', {}).get('timeout', 300)
            },
            'naming_validator': {
                'script': 'naming_validator.py',
                'enabled': self.config.get('tools', {}).get('naming_validator', {}).get('enabled', True),
                'args': self._get_naming_args(),
                'timeout': self.config.get('tools', {}).get('naming_validator', {}).get('timeout', 300)
            },
            'unified_test_runner': {
                'script': 'unified_test_runner.py',
                'enabled': self.config.get('tools', {}).get('unified_test_runner', {}).get('enabled', True),
                'args': self._get_test_runner_args(),
                'timeout': self.config.get('tools', {}).get('unified_test_runner', {}).get('timeout', 1800)
            },
            'code_quality_validator': {
                'script': 'code_quality_validator.py',
                'enabled': self.config.get('tools', {}).get('code_quality_validator', {}).get('enabled', True),
                'args': self._get_quality_args(),
                'timeout': self.config.get('tools', {}).get('code_quality_validator', {}).get('timeout', 600)
            },
            'quality_gate_enforcer': {
                'script': 'quality_gate_enforcer.py',
                'enabled': self.config.get('tools', {}).get('quality_gate_enforcer', {}).get('enabled', True),
                'args': self._get_gate_args(),
                'timeout': self.config.get('tools', {}).get('quality_gate_enforcer', {}).get('timeout', 300)
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load framework configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "target_path": ".",
            "output_dir": "reports",
            "tools": {
                "monolithic_detector": {
                    "enabled": True,
                    "threshold": 500,
                    "workers": 4,
                    "timeout": 300
                },
                "naming_validator": {
                    "enabled": True,
                    "workers": 4,
                    "min_compliance": 95.0,
                    "timeout": 300
                },
                "unified_test_runner": {
                    "enabled": True,
                    "parallel_suites": True,
                    "max_workers": 4,
                    "timeout": 1800
                },
                "code_quality_validator": {
                    "enabled": True,
                    "parallel_execution": True,
                    "timeout": 600
                },
                "quality_gate_enforcer": {
                    "enabled": True,
                    "parallel": True,
                    "timeout": 300
                }
            },
            "reporting": {
                "formats": ["json", "html", "console"],
                "include_charts": True,
                "include_recommendations": True
            },
            "performance": {
                "max_total_time": 900,  # 15 minutes
                "memory_limit_mb": 2048,
                "parallel_execution": True
            },
            "quality_gates": {
                "monolithic_modules": {"threshold": 0, "severity": "critical"},
                "naming_conventions": {"threshold": 95.0, "severity": "major"},
                "test_execution": {"threshold": 95.0, "severity": "critical"},
                "code_quality": {"threshold": 90.0, "severity": "major"}
            }
        }
    
    def _get_monolithic_args(self) -> List[str]:
        """Get arguments for monolithic detector."""
        tool_config = self.config.get('tools', {}).get('monolithic_detector', {})
        args = [
            self.config['target_path'],
            '--threshold', str(tool_config.get('threshold', 500)),
            '--output', f"{self.config['output_dir']}/monolithic_report.json",
            '--workers', str(tool_config.get('workers', 4))
        ]
        return args
    
    def _get_naming_args(self) -> List[str]:
        """Get arguments for naming validator."""
        tool_config = self.config.get('tools', {}).get('naming_validator', {})
        args = [
            self.config['target_path'],
            '--output', f"{self.config['output_dir']}/naming_report.json",
            '--workers', str(tool_config.get('workers', 4)),
            '--min-compliance', str(tool_config.get('min_compliance', 95.0))
        ]
        return args
    
    def _get_test_runner_args(self) -> List[str]:
        """Get arguments for unified test runner."""
        tool_config = self.config.get('tools', {}).get('unified_test_runner', {})
        args = [
            '--output', f"{self.config['output_dir']}/test_report.json",
            '--max-workers', str(tool_config.get('max_workers', 4))
        ]
        if tool_config.get('parallel_suites', True):
            args.append('--parallel-suites')
        return args
    
    def _get_quality_args(self) -> List[str]:
        """Get arguments for code quality validator."""
        tool_config = self.config.get('tools', {}).get('code_quality_validator', {})
        args = [
            self.config['target_path'],
            '--output', f"{self.config['output_dir']}/quality_report.json"
        ]
        if tool_config.get('parallel_execution', True):
            args.append('--parallel')
        return args
    
    def _get_gate_args(self) -> List[str]:
        """Get arguments for quality gate enforcer."""
        tool_config = self.config.get('tools', {}).get('quality_gate_enforcer', {})
        args = [
            '--output', f"{self.config['output_dir']}/quality_gate_report.json"
        ]
        if tool_config.get('parallel', True):
            args.append('--parallel')
        return args
    
    def execute_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> ToolResult:
        """Execute a single tool with progress tracking."""
        start_time = time.time()
        
        try:
            self.progress_tracker.update_progress(tool_name, "Initializing")
            
            # Check if tool script exists
            script_path = Path(tool_config['script'])
            if not script_path.exists():
                # Try to find in current directory or tools subdirectory
                alt_paths = [
                    Path('.') / tool_config['script'],
                    Path('tools') / tool_config['script'],
                    Path('..') / tool_config['script']
                ]
                script_found = False
                for alt_path in alt_paths:
                    if alt_path.exists():
                        script_path = alt_path
                        script_found = True
                        break
                
                if not script_found:
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        execution_time=time.time() - start_time,
                        exit_code=1,
                        output_path="",
                        metrics={},
                        violations=[],
                        recommendations=[],
                        error_message=f"Tool script not found: {tool_config['script']}"
                    )
            
            self.progress_tracker.update_progress(tool_name, "Executing")
            
            # Execute tool
            cmd = [sys.executable, str(script_path)] + tool_config['args']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            try:
                stdout, stderr = process.communicate(timeout=tool_config['timeout'])
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
            
            execution_time = time.time() - start_time
            
            # Parse output for metrics
            metrics, violations, recommendations = self._parse_tool_output(tool_name, stdout, stderr)
            
            # Determine output path
            output_path = self._get_output_path(tool_name)
            
            success = exit_code == 0
            
            self.progress_tracker.update_progress(tool_name, "Completed", completed=True)
            
            return ToolResult(
                tool_name=tool_name,
                success=success,
                execution_time=execution_time,
                exit_code=exit_code,
                output_path=output_path,
                metrics=metrics,
                violations=violations,
                recommendations=recommendations,
                error_message=stderr if not success else None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.progress_tracker.update_progress(tool_name, "Failed", completed=True)
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                execution_time=execution_time,
                exit_code=1,
                output_path="",
                metrics={},
                violations=[],
                recommendations=[],
                error_message=str(e)
            )
    
    def _parse_tool_output(self, tool_name: str, stdout: str, stderr: str) -> tuple:
        """Parse tool output to extract metrics, violations, and recommendations."""
        metrics = {}
        violations = []
        recommendations = []
        
        try:
            # Try to parse JSON output if available
            if stdout.strip():
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('{'):
                        try:
                            data = json.loads(line)
                            if tool_name == 'monolithic_detector':
                                metrics = data.get('summary', {})
                                violations = data.get('violations', [])
                            elif tool_name == 'naming_validator':
                                metrics = data.get('summary', {})
                                violations = data.get('violations_by_severity', {})
                            elif tool_name == 'unified_test_runner':
                                metrics = data.get('summary', {})
                            elif tool_name == 'code_quality_validator':
                                metrics = data.get('summary', {})
                                violations = data.get('violations', [])
                            elif tool_name == 'quality_gate_enforcer':
                                metrics = data.get('execution_summary', {})
                                violations = data.get('quality_gate_results', [])
                            break
                        except json.JSONDecodeError:
                            continue
            
            # Extract recommendations from stderr or stdout
            if stderr:
                recommendations.extend(stderr.split('\n'))
            if stdout:
                # Look for recommendation patterns
                for line in stdout.split('\n'):
                    if 'recommendation' in line.lower() or 'suggest' in line.lower():
                        recommendations.append(line.strip())
                        
        except Exception as e:
            logger.warning(f"Error parsing output for {tool_name}: {e}")
        
        return metrics, violations, recommendations
    
    def _get_output_path(self, tool_name: str) -> str:
        """Get the expected output path for a tool."""
        output_dir = self.config.get('output_dir', 'reports')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        path_map = {
            'monolithic_detector': f'{output_dir}/monolithic_report.json',
            'naming_validator': f'{output_dir}/naming_report.json',
            'unified_test_runner': f'{output_dir}/test_report.json',
            'code_quality_validator': f'{output_dir}/quality_report.json',
            'quality_gate_enforcer': f'{output_dir}/quality_gate_report.json'
        }
        
        return path_map.get(tool_name, f'{output_dir}/{tool_name}_report.json')
    
    def run_all_tools(self, parallel: bool = True, max_workers: Optional[int] = None) -> List[ToolResult]:
        """Execute all enabled tools."""
        enabled_tools = {name: config for name, config in self.tools.items() if config['enabled']}
        
        if not enabled_tools:
            logger.warning("No tools enabled in configuration")
            return []
        
        self.progress_tracker = ProgressTracker(len(enabled_tools))
        
        logger.info(f"Starting execution of {len(enabled_tools)} tools")
        if parallel:
            logger.info("Running tools in parallel")
        else:
            logger.info("Running tools sequentially")
        
        results = []
        
        if parallel:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=max_workers or len(enabled_tools)) as executor:
                future_to_tool = {
                    executor.submit(self.execute_tool, tool_name, tool_config): tool_name
                    for tool_name, tool_config in enabled_tools.items()
                }
                
                for future in as_completed(future_to_tool):
                    tool_name = future_to_tool[future]
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Tool {tool_name} completed in {result.execution_time:.2f}s")
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed with exception: {e}")
                        results.append(ToolResult(
                            tool_name=tool_name,
                            success=False,
                            execution_time=0,
                            exit_code=1,
                            output_path="",
                            metrics={},
                            violations=[],
                            recommendations=[],
                            error_message=str(e)
                        ))
        else:
            # Sequential execution
            for tool_name, tool_config in enabled_tools.items():
                result = self.execute_tool(tool_name, tool_config)
                results.append(result)
                logger.info(f"Tool {tool_name} completed in {result.execution_time:.2f}s")
        
        print()  # New line after progress display
        self.results = results
        return results
    
    def generate_unified_report(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Generate a comprehensive unified report."""
        total_time = sum(r.execution_time for r in results)
        successful_tools = sum(1 for r in results if r.success)
        failed_tools = len(results) - successful_tools
        
        # Calculate overall compliance
        compliance_scores = []
        for result in results:
            if result.tool_name == 'monolithic_detector':
                # For monolithic, we want 0 violations
                compliance_scores.append(100.0 if result.metrics.get('monolithic_files_found', 0) == 0 else 0.0)
            elif result.tool_name == 'naming_validator':
                compliance_scores.append(result.metrics.get('compliance_rate', 0.0))
            elif result.tool_name == 'unified_test_runner':
                compliance_scores.append(result.metrics.get('success_rate', 0.0))
            elif result.tool_name == 'code_quality_validator':
                compliance_scores.append(result.metrics.get('overall_compliance', 0.0))
            elif result.tool_name == 'quality_gate_enforcer':
                # For quality gates, calculate pass rate
                gate_results = result.violations
                if gate_results:
                    passed_gates = sum(1 for gate in gate_results if gate.get('passed', False))
                    compliance_scores.append((passed_gates / len(gate_results)) * 100)
                else:
                    compliance_scores.append(100.0)
        
        overall_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0
        
        # System information
        system_info = {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'platform': sys.platform,
            'python_version': sys.version.split()[0]
        }
        
        report = {
            'execution_summary': {
                'total_tools': len(results),
                'successful_tools': successful_tools,
                'failed_tools': failed_tools,
                'total_execution_time': total_time,
                'overall_compliance': overall_compliance,
                'execution_timestamp': datetime.now().isoformat(),
                'system_info': system_info
            },
            'tool_results': [
                {
                    'tool_name': r.tool_name,
                    'success': r.success,
                    'execution_time': r.execution_time,
                    'exit_code': r.exit_code,
                    'output_path': r.output_path,
                    'metrics': r.metrics,
                    'violations_count': len(r.violations),
                    'recommendations_count': len(r.recommendations),
                    'error_message': r.error_message
                }
                for r in results
            ],
            'quality_assessment': {
                'overall_status': 'PASS' if overall_compliance >= 90.0 else 'FAIL',
                'compliance_score': overall_compliance,
                'critical_issues': sum(1 for r in results if not r.success),
                'performance_score': self._calculate_performance_score(results)
            },
            'recommendations': self._generate_unified_recommendations(results),
            'next_steps': self._generate_next_steps(results)
        }
        
        return report
    
    def _calculate_performance_score(self, results: List[ToolResult]) -> float:
        """Calculate performance score based on execution times."""
        if not results:
            return 0.0
        
        max_allowed_time = self.config.get('performance', {}).get('max_total_time', 900)
        total_time = sum(r.execution_time for r in results)
        
        if total_time <= max_allowed_time:
            return 100.0
        else:
            # Penalty for exceeding time limit
            penalty = ((total_time - max_allowed_time) / max_allowed_time) * 100
            return max(0.0, 100.0 - penalty)
    
    def _generate_unified_recommendations(self, results: List[ToolResult]) -> List[str]:
        """Generate unified recommendations based on all results."""
        recommendations = []
        
        # Collect all recommendations
        for result in results:
            if result.recommendations:
                recommendations.extend(result.recommendations)
        
        # Add specific recommendations based on failures
        failed_tools = [r for r in results if not r.success]
        if failed_tools:
            recommendations.append(f"Address failures in {len(failed_tools)} tool(s): {', '.join(r.tool_name for r in failed_tools)}")
        
        # Performance recommendations
        total_time = sum(r.execution_time for r in results)
        if total_time > 600:  # 10 minutes
            recommendations.append("Consider running tools in parallel to improve performance")
        
        # Quality recommendations
        compliance_scores = []
        for result in results:
            if result.tool_name == 'naming_validator':
                compliance = result.metrics.get('compliance_rate', 0)
                if compliance < 95:
                    recommendations.append(f"Improve naming convention compliance (currently {compliance:.1f}%)")
            elif result.tool_name == 'monolithic_detector':
                violations = result.metrics.get('monolithic_files_found', 0)
                if violations > 0:
                    recommendations.append(f"Refactor {violations} monolithic modules to improve code organization")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_next_steps(self, results: List[ToolResult]) -> List[str]:
        """Generate next steps based on results."""
        steps = []
        
        failed_tools = [r for r in results if not r.success]
        if failed_tools:
            steps.append("Fix failed tools before proceeding")
            steps.append("Review error messages and tool documentation")
        
        # Check for critical issues
        critical_issues = 0
        for result in results:
            if not result.success:
                critical_issues += 1
            elif result.tool_name == 'monolithic_detector' and result.metrics.get('monolithic_files_found', 0) > 0:
                critical_issues += 1
        
        if critical_issues > 0:
            steps.append("Address critical quality issues before deployment")
        
        if all(r.success for r in results):
            steps.append("All tools passed successfully - ready for deployment")
            steps.append("Consider running additional performance tests")
        
        return steps
    
    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save report in multiple formats."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save HTML report
        if 'html' in self.config.get('reporting', {}).get('formats', []):
            html_path = output_path.with_suffix('.html')
            self._save_html_report(report, html_path)
        
        # Save console summary
        if 'console' in self.config.get('reporting', {}).get('formats', []):
            self._print_console_summary(report)
    
    def _save_html_report(self, report: Dict[str, Any], output_path: Path):
        """Save HTML report with charts and visualizations."""
        html_content = self._generate_html_report(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate comprehensive HTML report."""
        execution_summary = report['execution_summary']
        tool_results = report['tool_results']
        quality_assessment = report['quality_assessment']
        
        # Calculate chart data
        tool_names = [r['tool_name'] for r in tool_results]
        execution_times = [r['execution_time'] for r in tool_results]
        success_status = ['PASS' if r['success'] else 'FAIL' for r in tool_results]
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Test Suite Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; border-bottom: 3px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; color: #007acc; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 16px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .tool-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .tool-card {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #ddd; }}
        .tool-card.success {{ border-left-color: #28a745; }}
        .tool-card.failure {{ border-left-color: #dc3545; }}
        .status {{ display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }}
        .status.pass {{ background-color: #28a745; }}
        .status.fail {{ background-color: #dc3545; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 15px 0; }}
        .metric {{ background-color: white; padding: 10px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-weight: bold; color: #007acc; font-size: 18px; }}
        .chart-container {{ position: relative; height: 400px; margin: 20px 0; }}
        .recommendations {{ background-color: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 5px solid #2196f3; }}
        .recommendation {{ margin: 10px 0; padding: 10px; background-color: white; border-radius: 5px; }}
        .next-steps {{ background-color: #f3e5f5; padding: 20px; border-radius: 8px; border-left: 5px solid #9c27b0; }}
        .step {{ margin: 10px 0; padding: 10px; background-color: white; border-radius: 5px; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #eee; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Comprehensive Test Suite Report</h1>
            <p>Generated on {execution_summary['execution_timestamp']}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tools</h3>
                <div class="value">{execution_summary['total_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Successful</h3>
                <div class="value">{execution_summary['successful_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value">{execution_summary['failed_tools']}</div>
            </div>
            <div class="summary-card">
                <h3>Total Time</h3>
                <div class="value">{execution_summary['total_execution_time']:.1f}s</div>
            </div>
            <div class="summary-card">
                <h3>Compliance</h3>
                <div class="value">{execution_summary['overall_compliance']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Overall Status</h3>
                <div class="value">{quality_assessment['overall_status']}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Tool Execution Results</h2>
            <div class="tool-grid">
"""
        
        for result in tool_results:
            status_class = 'success' if result['success'] else 'failure'
            status_text = 'PASS' if result['success'] else 'FAIL'
            
            html += f"""
                <div class="tool-card {status_class}">
                    <h3>{result['tool_name'].replace('_', ' ').title()}
                        <span class="status {status_text.lower()}">{status_text}</span>
                    </h3>
                    <p><strong>Execution Time:</strong> {result['execution_time']:.2f}s</p>
                    <p><strong>Exit Code:</strong> {result['exit_code']}</p>
                    <p><strong>Violations:</strong> {result['violations_count']}</p>
                    <p><strong>Recommendations:</strong> {result['recommendations_count']}</p>
"""
            
            if result['error_message']:
                html += f'<p><strong>Error:</strong> {result["error_message"]}</p>'
            
            html += "</div>"
        
        html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Performance Analysis</h2>
            <div class="chart-container">
                <canvas id="executionChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <div class="recommendations">
"""
        
        for recommendation in report['recommendations']:
            html += f'<div class="recommendation">• {recommendation}</div>'
        
        html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Next Steps</h2>
            <div class="next-steps">
"""
        
        for step in report['next_steps']:
            html += f'<div class="step">• {step}</div>'
        
        html += f"""
            </div>
        </div>
        
        <div class="section">
            <h2>System Information</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{execution_summary['system_info']['cpu_count']}</div>
                    <div>CPU Cores</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{execution_summary['system_info']['memory_total_gb']:.1f}GB</div>
                    <div>Total Memory</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{execution_summary['system_info']['memory_available_gb']:.1f}GB</div>
                    <div>Available Memory</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{execution_summary['system_info']['platform']}</div>
                    <div>Platform</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{execution_summary['system_info']['python_version']}</div>
                    <div>Python Version</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Execution time chart
        const ctx = document.getElementById('executionChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {tool_names},
                datasets: [{{
                    label: 'Execution Time (seconds)',
                    data: {execution_times},
                    backgroundColor: {success_status}.map(status => status === 'PASS' ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)'),
                    borderColor: {success_status}.map(status => status === 'PASS' ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Time (seconds)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Tools'
                        }}
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Tool Execution Times'
                    }},
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html
    
    def _print_console_summary(self, report: Dict[str, Any]):
        """Print comprehensive console summary."""
        execution_summary = report['execution_summary']
        quality_assessment = report['quality_assessment']
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE EXECUTION SUMMARY")
        print("="*80)
        print(f"Execution Time: {execution_summary['total_execution_time']:.2f}s")
        print(f"Tools Executed: {execution_summary['total_tools']}")
        print(f"Successful: {execution_summary['successful_tools']}")
        print(f"Failed: {execution_summary['failed_tools']}")
        print(f"Overall Compliance: {execution_summary['overall_compliance']:.1f}%")
        print(f"Overall Status: {quality_assessment['overall_status']}")
        print(f"Performance Score: {quality_assessment['performance_score']:.1f}/100")
        
        print("\n" + "-"*80)
        print("TOOL RESULTS:")
        print("-"*80)
        
        for result in report['tool_results']:
            status = "[PASS]" if result['success'] else "[FAIL]"
            print(f"{result['tool_name'].replace('_', ' ').title():<30} {status} ({result['execution_time']:.2f}s)")
            if result['error_message']:
                print(f"  Error: {result['error_message']}")
        
        if report['recommendations']:
            print("\n" + "-"*80)
            print("RECOMMENDATIONS:")
            print("-"*80)
            for rec in report['recommendations']:
                print(f"• {rec}")
        
        if report['next_steps']:
            print("\n" + "-"*80)
            print("NEXT STEPS:")
            print("-"*80)
            for step in report['next_steps']:
                print(f"• {step}")
        
        print("\n" + "="*80)

    def interactive_mode(self):
        """Run framework in interactive mode with menu-driven interface."""
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUITE - INTERACTIVE MODE")
        print("="*60)
        print("Integrated Testing Framework")
        print("Version 1.0.0")
        print()
        
        while True:
            print("\nAvailable Options:")
            print("1. Run all tools (parallel)")
            print("2. Run all tools (sequential)")
            print("3. Configure tools")
            print("4. View configuration")
            print("5. Generate sample config")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                self._run_interactive_parallel()
            elif choice == '2':
                self._run_interactive_sequential()
            elif choice == '3':
                self._configure_tools_interactive()
            elif choice == '4':
                self._view_configuration()
            elif choice == '5':
                self._generate_sample_config()
            elif choice == '6':
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")
    
    def _run_interactive_parallel(self):
        """Run tools in parallel with interactive feedback."""
        print("\nRunning all tools in parallel...")
        output_path = Path(self.config['output_dir']) / "comprehensive_report"
        
        try:
            results = self.run_all_tools(parallel=True)
            report = self.generate_unified_report(results)
            self.save_report(report, output_path)
            
            print(f"\nReport saved to: {output_path}.json and {output_path}.html")
            
            # Ask if user wants to see summary
            show_summary = input("Show console summary? (y/n): ").strip().lower() == 'y'
            if show_summary:
                self._print_console_summary(report)
                
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            print(f"Error: {e}")
    
    def _run_interactive_sequential(self):
        """Run tools sequentially with interactive feedback."""
        print("\nRunning all tools sequentially...")
        output_path = Path(self.config['output_dir']) / "comprehensive_report"
        
        try:
            results = self.run_all_tools(parallel=False)
            report = self.generate_unified_report(results)
            self.save_report(report, output_path)
            
            print(f"\nReport saved to: {output_path}.json and {output_path}.html")
            
            # Ask if user wants to see summary
            show_summary = input("Show console summary? (y/n): ").strip().lower() == 'y'
            if show_summary:
                self._print_console_summary(report)
                
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            print(f"Error: {e}")
    
    def _configure_tools_interactive(self):
        """Interactive tool configuration."""
        print("\nTool Configuration")
        print("-" * 30)
        
        for tool_name, tool_config in self.tools.items():
            print(f"\n{tool_name.replace('_', ' ').title()}:")
            current_enabled = tool_config.get('enabled', True)
            print(f"  Enabled: {current_enabled} (y/n)")
            
            new_enabled = input(f"  Change enabled status? (current: {current_enabled}): ").strip().lower()
            if new_enabled in ['y', 'n']:
                tool_config['enabled'] = new_enabled == 'y'
            
            if tool_name == 'monolithic_detector':
                threshold = input(f"  Threshold (current: {tool_config.get('threshold', 500)}): ").strip()
                if threshold.isdigit():
                    tool_config['threshold'] = int(threshold)
            elif tool_name == 'naming_validator':
                min_compliance = input(f"  Min compliance % (current: {tool_config.get('min_compliance', 95.0)}): ").strip()
                if min_compliance.replace('.', '').isdigit():
                    tool_config['min_compliance'] = float(min_compliance)
        
        # Save configuration
        self._save_config()
        print("\nConfiguration saved.")
    
    def _view_configuration(self):
        """Display current configuration."""
        print("\nCurrent Configuration:")
        print("-" * 30)
        print(json.dumps(self.config, indent=2))
    
    def _generate_sample_config(self):
        """Generate a sample configuration file."""
        sample_path = Path("test_framework_config.sample.json")
        with open(sample_path, 'w') as f:
            json.dump(self._get_default_config(), f, indent=2)
        print(f"Sample configuration saved to: {sample_path}")
    
    def _save_config(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

def main():
    """Main entry point for the comprehensive test suite."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Suite - Unified Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python comprehensive_test_suite.py --interactive
  python comprehensive_test_suite.py --output my_report.json
  python comprehensive_test_suite.py --parallel --config custom_config.json
  python comprehensive_test_suite.py --sequential --target src/
        """
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode with menu-driven interface'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tools in parallel (default)'
    )
    
    parser.add_argument(
        '--sequential', '-s',
        action='store_true',
        help='Run tools sequentially'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='reports/comprehensive_report',
        help='Output report path (without extension)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='test_framework_config.json',
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--target', '-t',
        type=str,
        default='.',
        help='Target directory to analyze'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        help='Maximum number of worker threads for parallel execution'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize framework
        config_path = Path(args.config)
        suite = ComprehensiveTestSuite(config_path)
        
        # Override target directory if specified
        if args.target != '.':
            suite.config['target_path'] = args.target
        
        if args.interactive:
            # Run in interactive mode
            suite.interactive_mode()
        else:
            # Run in batch mode
            output_path = Path(args.output)
            
            print("Comprehensive Test Suite - Batch Mode")
            print(f"Target: {suite.config['target_path']}")
            print(f"Output: {output_path}")
            print(f"Parallel: {not args.sequential}")
            print()
            
            # Execute all tools
            results = suite.run_all_tools(
                parallel=not args.sequential,
                max_workers=args.max_workers
            )
            
            # Generate and save report
            report = suite.generate_unified_report(results)
            suite.save_report(report, output_path)
            
            # Print summary
            suite._print_console_summary(report)
            
            # Exit with appropriate code
            overall_status = report['quality_assessment']['overall_status']
            exit_code = 0 if overall_status == 'PASS' else 1
            
            print(f"\nExiting with status: {overall_status} (exit code: {exit_code})")
            return exit_code
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())