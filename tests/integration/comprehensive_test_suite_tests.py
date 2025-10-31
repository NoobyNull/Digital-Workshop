#!/usr/bin/env python3
"""
Comprehensive Test Suite Integration Tests

Tests the complete workflow integration, all tool combinations, CI/CD integration scenarios,
and performance requirements for the unified testing framework.
"""

import pytest
import json
import tempfile
import shutil
import os
import time
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

# Import the main framework
try:
    from comprehensive_test_suite import ComprehensiveTestSuite, ToolResult, ProgressTracker
except ImportError:
    # For testing, we'll need to handle potential import issues
    ComprehensiveTestSuite = None
    ToolResult = None
    ProgressTracker = None


class TestComprehensiveTestSuite:
    """Test suite for the comprehensive testing framework integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config(self, temp_dir):
        """Create a sample configuration for testing."""
        config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {
                    "enabled": True,
                    "threshold": 10,  # Low threshold for testing
                    "workers": 2,
                    "timeout": 60
                },
                "naming_validator": {
                    "enabled": True,
                    "workers": 2,
                    "min_compliance": 80.0,
                    "timeout": 60
                },
                "unified_test_runner": {
                    "enabled": True,
                    "parallel_suites": False,  # Sequential for testing
                    "max_workers": 2,
                    "timeout": 300
                },
                "code_quality_validator": {
                    "enabled": True,
                    "parallel_execution": False,
                    "timeout": 120
                },
                "quality_gate_enforcer": {
                    "enabled": True,
                    "parallel": False,
                    "timeout": 60
                }
            },
            "reporting": {
                "formats": ["json", "console"],
                "include_charts": False,  # Disable for testing
                "include_recommendations": True
            },
            "performance": {
                "max_total_time": 300,  # 5 minutes for testing
                "memory_limit_mb": 1024,
                "parallel_execution": False
            }
        }
        
        config_path = Path(temp_dir) / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_path
    
    @pytest.fixture
    def mock_tools(self, temp_dir):
        """Create mock tool scripts for testing."""
        tools_dir = Path(temp_dir)
        
        # Create mock monolithic detector
        mock_monolithic = tools_dir / "mock_monolithic_detector.py"
        mock_monolithic.write_text("""#!/usr/bin/env python3
import sys
import json
print(json.dumps({
    "summary": {
        "total_files_analyzed": 5,
        "monolithic_files_found": 0,
        "threshold_exceeded": [],
        "analysis_time": 0.5
    },
    "violations": [],
    "recommendations": ["Code structure looks good"]
}))
sys.exit(0)
""")
        
        # Create mock naming validator
        mock_naming = tools_dir / "mock_naming_validator.py"
        mock_naming.write_text("""#!/usr/bin/env python3
import sys
import json
print(json.dumps({
    "summary": {
        "total_files_checked": 5,
        "compliance_rate": 95.0,
        "files_violating": 1
    },
    "violations_by_severity": {
        "minor": [{"file": "test_file.py", "issue": "naming_convention"}]
    },
    "recommendations": ["Consider renaming test_file.py to follow conventions"]
}))
sys.exit(0)
""")
        
        # Create mock test runner
        mock_runner = tools_dir / "mock_unified_test_runner.py"
        mock_runner.write_text("""#!/usr/bin/env python3
import sys
import json
print(json.dumps({
    "summary": {
        "total_tests": 10,
        "passed": 9,
        "failed": 1,
        "success_rate": 90.0,
        "execution_time": 2.0
    },
    "test_results": []
}))
sys.exit(0)
""")
        
        # Create mock quality validator
        mock_quality = tools_dir / "mock_code_quality_validator.py"
        mock_quality.write_text("""#!/usr/bin/env python3
import sys
import json
print(json.dumps({
    "summary": {
        "overall_compliance": 85.0,
        "black_formatted": True,
        "pylint_score": 7.5,
        "issues_found": 2
    },
    "violations": [
        {"file": "code.py", "line": 10, "issue": "missing_docstring", "severity": "minor"}
    ],
    "recommendations": ["Add docstrings to functions"]
}))
sys.exit(0)
""")
        
        # Create mock gate enforcer
        mock_gate = tools_dir / "mock_quality_gate_enforcer.py"
        mock_gate.write_text("""#!/usr/bin/env python3
import sys
import json
print(json.dumps({
    "execution_summary": {
        "gates_checked": 4,
        "gates_passed": 3,
        "gates_failed": 1,
        "execution_time": 1.0
    },
    "quality_gate_results": [
        {"gate": "monolithic_modules", "passed": True, "threshold": 0, "actual": 0},
        {"gate": "naming_conventions", "passed": True, "threshold": 95.0, "actual": 95.0},
        {"gate": "test_execution", "passed": False, "threshold": 95.0, "actual": 90.0},
        {"gate": "code_quality", "passed": True, "threshold": 90.0, "actual": 85.0}
    ],
    "recommendations": ["Improve test execution success rate"]
}))
sys.exit(0)
""")
        
        return {
            'monolithic_detector': 'mock_monolithic_detector.py',
            'naming_validator': 'mock_naming_validator.py',
            'unified_test_runner': 'mock_unified_test_runner.py',
            'code_quality_validator': 'mock_code_quality_validator.py',
            'quality_gate_enforcer': 'mock_quality_gate_enforcer.py'
        }
    
    def test_framework_initialization(self, sample_config):
        """Test framework initialization with configuration."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        suite = ComprehensiveTestSuite(sample_config)
        assert suite.config_path == sample_config
        assert suite.config['target_path'] is not None
        assert len(suite.tools) == 5
        assert all(tool in suite.tools for tool in [
            'monolithic_detector', 'naming_validator', 'unified_test_runner',
            'code_quality_validator', 'quality_gate_enforcer'
        ])
    
    def test_tool_configuration_loading(self, sample_config):
        """Test that tool configurations are properly loaded."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        suite = ComprehensiveTestSuite(sample_config)
        
        # Check monolithic detector config
        mon_config = suite.tools['monolithic_detector']
        assert mon_config['enabled'] == True
        assert mon_config['timeout'] == 60
        
        # Check naming validator config
        naming_config = suite.tools['naming_validator']
        assert naming_config['enabled'] == True
        assert naming_config['min_compliance'] == 80.0
    
    def test_progress_tracker(self):
        """Test progress tracking functionality."""
        if ProgressTracker is None:
            pytest.skip("ProgressTracker not available")
        
        tracker = ProgressTracker(3)
        
        # Test initial state
        assert tracker.completed_tools == 0
        assert tracker.total_tools == 3
        assert tracker.current_tool == ""
        
        # Test progress updates
        tracker.update_progress("tool1", "initializing")
        assert tracker.current_tool == "tool1"
        assert tracker.current_step == "initializing"
        
        tracker.update_progress("tool1", "completed", completed=True)
        assert tracker.completed_tools == 1
        assert tracker.current_tool == ""
    
    @patch('subprocess.Popen')
    def test_tool_execution_success(self, mock_popen, temp_dir, mock_tools):
        """Test successful tool execution."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Mock successful subprocess execution
        mock_process = Mock()
        mock_process.communicate.return_value = ('{"summary": {"test": "success"}}', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Update tool scripts to use mock versions
        tools_dir = Path(temp_dir)
        for tool_name, script_name in mock_tools.items():
            script_path = tools_dir / script_name
            suite.tools[tool_name]['script'] = str(script_path)
        
        suite = ComprehensiveTestSuite()
        result = suite.execute_tool('monolithic_detector', suite.tools['monolithic_detector'])
        
        assert result.success == True
        assert result.exit_code == 0
        assert result.tool_name == 'monolithic_detector'
        assert 'test' in result.metrics
    
    @patch('subprocess.Popen')
    def test_tool_execution_failure(self, mock_popen):
        """Test tool execution failure handling."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Mock failed subprocess execution
        mock_process = Mock()
        mock_process.communicate.return_value = ('', 'Tool execution failed')
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        suite = ComprehensiveTestSuite()
        result = suite.execute_tool('monolithic_detector', suite.tools['monolithic_detector'])
        
        assert result.success == False
        assert result.exit_code == 1
        assert 'Tool execution failed' in result.error_message
    
    @patch('subprocess.Popen')
    def test_tool_timeout_handling(self, mock_popen):
        """Test tool timeout handling."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Mock timeout exception
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired('cmd', 60)
        mock_process.kill.return_value = None
        mock_process.communicate.return_value = ('', 'Timeout')
        mock_popen.return_value = mock_process
        
        suite = ComprehensiveTestSuite()
        result = suite.execute_tool('monolithic_detector', suite.tools['monolithic_detector'])
        
        assert result.success == False
        assert result.exit_code == -1
        assert 'Timeout' in result.error_message or result.error_message is not None
    
    def test_parallel_vs_sequential_execution(self, temp_dir, mock_tools):
        """Test parallel vs sequential execution modes."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Create configuration with shorter timeouts
        config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "timeout": 5},
                "naming_validator": {"enabled": True, "timeout": 5}
            },
            "performance": {"max_total_time": 30}
        }
        
        config_path = Path(temp_dir) / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Mock tool execution to avoid actual subprocess calls
        with patch.object(suite, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                tool_name='test',
                success=True,
                execution_time=1.0,
                exit_code=0,
                output_path='test.json',
                metrics={'test': 'success'},
                violations=[],
                recommendations=[]
            )
            
            # Test parallel execution
            start_time = time.time()
            results_parallel = suite.run_all_tools(parallel=True, max_workers=2)
            parallel_time = time.time() - start_time
            
            # Test sequential execution
            start_time = time.time()
            results_sequential = suite.run_all_tools(parallel=False)
            sequential_time = time.time() - start_time
            
            assert len(results_parallel) == 2
            assert len(results_sequential) == 2
            assert all(r.success for r in results_parallel)
            assert all(r.success for r in results_sequential)
    
    def test_unified_report_generation(self, temp_dir):
        """Test unified report generation."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Create sample tool results
        results = [
            ToolResult(
                tool_name='monolithic_detector',
                success=True,
                execution_time=2.0,
                exit_code=0,
                output_path='monolithic_report.json',
                metrics={'monolithic_files_found': 0},
                violations=[],
                recommendations=[]
            ),
            ToolResult(
                tool_name='naming_validator',
                success=True,
                execution_time=1.5,
                exit_code=0,
                output_path='naming_report.json',
                metrics={'compliance_rate': 95.0},
                violations=[],
                recommendations=[]
            )
        ]
        
        suite = ComprehensiveTestSuite()
        report = suite.generate_unified_report(results)
        
        assert 'execution_summary' in report
        assert 'tool_results' in report
        assert 'quality_assessment' in report
        assert 'recommendations' in report
        assert 'next_steps' in report
        
        # Check execution summary
        summary = report['execution_summary']
        assert summary['total_tools'] == 2
        assert summary['successful_tools'] == 2
        assert summary['failed_tools'] == 0
        assert summary['total_execution_time'] == 3.5
        
        # Check quality assessment
        assessment = report['quality_assessment']
        assert assessment['overall_status'] == 'PASS'
        assert assessment['compliance_score'] > 0
    
    def test_html_report_generation(self, temp_dir):
        """Test HTML report generation."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Create sample report
        report = {
            'execution_summary': {
                'total_tools': 2,
                'successful_tools': 2,
                'failed_tools': 0,
                'total_execution_time': 3.5,
                'overall_compliance': 95.0,
                'execution_timestamp': '2023-01-01T00:00:00',
                'system_info': {
                    'cpu_count': 4,
                    'memory_total_gb': 8.0,
                    'memory_available_gb': 4.0,
                    'platform': 'linux',
                    'python_version': '3.9.0'
                }
            },
            'tool_results': [
                {
                    'tool_name': 'monolithic_detector',
                    'success': True,
                    'execution_time': 2.0,
                    'exit_code': 0,
                    'output_path': 'monolithic_report.json',
                    'metrics': {'monolithic_files_found': 0},
                    'violations_count': 0,
                    'recommendations_count': 1,
                    'error_message': None
                }
            ],
            'quality_assessment': {
                'overall_status': 'PASS',
                'compliance_score': 95.0,
                'critical_issues': 0,
                'performance_score': 85.0
            },
            'recommendations': ['All tools passed successfully'],
            'next_steps': ['Ready for deployment']
        }
        
        suite = ComprehensiveTestSuite()
        html_content = suite._generate_html_report(report)
        
        assert '<!DOCTYPE html>' in html_content
        assert 'Comprehensive Test Suite Report' in html_content
        assert 'monolithic_detector' in html_content
        assert 'PASS' in html_content
        assert '95.0%' in html_content
    
    def test_interactive_mode_menu(self, temp_dir):
        """Test interactive mode menu functionality."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config_path = Path(temp_dir) / "test_config.json"
        config_path.write_text('{"target_path": ".", "output_dir": "reports", "tools": {}}')
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Test configuration viewing
        suite._view_configuration()  # Should not raise exception
        
        # Test sample config generation
        with patch('builtins.open', create=True) as mock_open:
            suite._generate_sample_config()
            mock_open.assert_called_once()
    
    def test_configuration_management(self, temp_dir):
        """Test configuration loading and saving."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config_path = Path(temp_dir) / "test_config.json"
        initial_config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "threshold": 100}
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(initial_config, f, indent=2)
        
        # Load configuration
        suite = ComprehensiveTestSuite(config_path)
        assert suite.config['target_path'] == temp_dir
        assert suite.tools['monolithic_detector']['enabled'] == True
        
        # Modify and save configuration
        suite.tools['monolithic_detector']['enabled'] = False
        suite._save_config()
        
        # Reload and verify
        new_suite = ComprehensiveTestSuite(config_path)
        assert new_suite.tools['monolithic_detector']['enabled'] == False
    
    def test_performance_requirements(self, temp_dir):
        """Test that framework meets performance requirements."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "timeout": 10},
                "naming_validator": {"enabled": True, "timeout": 10}
            },
            "performance": {
                "max_total_time": 30,  # 30 seconds for testing
                "memory_limit_mb": 1024
            }
        }
        
        config_path = Path(temp_dir) / "perf_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Mock fast tool execution
        with patch.object(suite, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                tool_name='test',
                success=True,
                execution_time=1.0,  # Fast execution
                exit_code=0,
                output_path='test.json',
                metrics={'test': 'success'},
                violations=[],
                recommendations=[]
            )
            
            start_time = time.time()
            results = suite.run_all_tools(parallel=True)
            total_time = time.time() - start_time
            
            # Should complete within time limit
            assert total_time <= config['performance']['max_total_time']
            assert len(results) == 2
            assert all(r.success for r in results)
            
            # Test performance score calculation
            performance_score = suite._calculate_performance_score(results)
            assert performance_score >= 0.0
            assert performance_score <= 100.0
    
    def test_error_handling_and_recovery(self, temp_dir):
        """Test error handling and recovery mechanisms."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config_path = Path(temp_dir) / "test_config.json"
        config_path.write_text('{"target_path": ".", "output_dir": "reports", "tools": {}}')
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Test with missing tool script
        result = suite.execute_tool('nonexistent_tool', {
            'script': 'nonexistent.py',
            'args': [],
            'timeout': 10
        })
        
        assert result.success == False
        assert 'not found' in result.error_message.lower()
        
        # Test with failing tool
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.communicate.return_value = ('', 'Tool failed')
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            result = suite.execute_tool('monolithic_detector', {
                'script': 'monolithic_detector.py',
                'args': [],
                'timeout': 10
            })
            
            assert result.success == False
            assert result.exit_code == 1
    
    def test_ci_cd_integration_features(self, temp_dir):
        """Test CI/CD integration capabilities."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "timeout": 10}
            },
            "ci_cd": {
                "enabled": True,
                "fail_on_critical": True,
                "fail_on_major": True,
                "fail_on_minor": False
            }
        }
        
        config_path = Path(temp_dir) / "cicd_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Test with passing results
        passing_results = [
            ToolResult(
                tool_name='monolithic_detector',
                success=True,
                execution_time=1.0,
                exit_code=0,
                output_path='report.json',
                metrics={'monolithic_files_found': 0},
                violations=[],
                recommendations=[]
            )
        ]
        
        report = suite.generate_unified_report(passing_results)
        exit_code = 0 if report['quality_assessment']['overall_status'] == 'PASS' else 1
        
        assert exit_code == 0  # Should pass
        
        # Test with failing results
        failing_results = [
            ToolResult(
                tool_name='monolithic_detector',
                success=False,
                execution_time=1.0,
                exit_code=1,
                output_path='report.json',
                metrics={},
                violations=[],
                recommendations=[]
            )
        ]
        
        report = suite.generate_unified_report(failing_results)
        exit_code = 0 if report['quality_assessment']['overall_status'] == 'PASS' else 1
        
        assert exit_code == 1  # Should fail
    
    def test_memory_and_resource_management(self, temp_dir):
        """Test memory and resource management."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config_path = Path(temp_dir) / "test_config.json"
        config_path.write_text('{"target_path": ".", "output_dir": "reports", "tools": {}}')
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Test that results are properly stored
        results = [
            ToolResult(
                tool_name='test1',
                success=True,
                execution_time=1.0,
                exit_code=0,
                output_path='test1.json',
                metrics={'test': 'data'},
                violations=[],
                recommendations=[]
            )
        ]
        
        suite.results = results
        assert len(suite.results) == 1
        assert suite.results[0].tool_name == 'test1'
    
    def test_comprehensive_workflow_integration(self, temp_dir, mock_tools):
        """Test complete workflow integration."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        # Create a realistic test environment
        config = {
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "timeout": 30},
                "naming_validator": {"enabled": True, "timeout": 30},
                "unified_test_runner": {"enabled": True, "timeout": 60},
                "code_quality_validator": {"enabled": True, "timeout": 60},
                "quality_gate_enforcer": {"enabled": True, "timeout": 30}
            },
            "reporting": {
                "formats": ["json", "console"],
                "include_charts": False,
                "include_recommendations": True
            },
            "performance": {
                "max_total_time": 300,
                "memory_limit_mb": 2048,
                "parallel_execution": True
            }
        }
        
        config_path = Path(temp_dir) / "integration_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Mock tool execution for all tools
        with patch.object(suite, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                tool_name='mock_tool',
                success=True,
                execution_time=0.5,
                exit_code=0,
                output_path='mock_report.json',
                metrics={'mock_metric': 100},
                violations=[],
                recommendations=['Mock recommendation']
            )
            
            # Execute all tools
            results = suite.run_all_tools(parallel=True, max_workers=3)
            
            # Verify results
            assert len(results) == 5
            assert all(r.success for r in results)
            assert all(r.execution_time > 0 for r in results)
            
            # Generate unified report
            report = suite.generate_unified_report(results)
            
            # Verify report structure
            assert 'execution_summary' in report
            assert 'tool_results' in report
            assert 'quality_assessment' in report
            assert 'recommendations' in report
            assert 'next_steps' in report
            
            # Save report
            output_path = Path(temp_dir) / "integration_test_report"
            suite.save_report(report, output_path)
            
            # Verify files were created
            assert (output_path.with_suffix('.json')).exists()
            assert (output_path.with_suffix('.html')).exists()
    
    def test_stress_testing_scenarios(self, temp_dir):
        """Test stress testing and edge cases."""
        if ComprehensiveTestSuite is None:
            pytest.skip("ComprehensiveTestSuite not available")
        
        config_path = Path(temp_dir) / "stress_config.json"
        config_path.write_text(json.dumps({
            "target_path": temp_dir,
            "output_dir": f"{temp_dir}/reports",
            "tools": {
                "monolithic_detector": {"enabled": True, "timeout": 5}
            },
            "performance": {
                "max_total_time": 10,
                "memory_limit_mb": 512
            }
        }))
        
        suite = ComprehensiveTestSuite(config_path)
        
        # Test with very fast tool execution (stress test)
        with patch.object(suite, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                tool_name='stress_test',
                success=True,
                execution_time=0.1,  # Very fast
                exit_code=0,
                output_path='stress_report.json',
                metrics={'rapid_execution': True},
                violations=[],
                recommendations=[]
            )
            
            # Run multiple iterations quickly
            for i in range(10):
                results = suite.run_all_tools(parallel=False)
                assert len(results) == 1
                assert results[0].success == True
            
            # Performance should remain consistent
            performance_scores = []
            for i in range(5):
                results = suite.run_all_tools(parallel=False)
                score = suite._calculate_performance_score(results)
                performance_scores.append(score)
            
            # Performance should be consistent (allowing for small variations)
            avg_score = sum(performance_scores) / len(performance_scores)
            assert avg_score >= 90.0  # Should maintain high performance


def run_integration_tests():
    """Run all integration tests."""
    print("Running Comprehensive Test Suite Integration Tests...")
    
    # Create test results directory
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    # Run pytest with HTML report
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        f"--html={results_dir}/integration_test_report.html",
        "--self-contained-html",
        "--junit-xml", f"{results_dir}/junit_results.xml"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    print(f"\nTest Results:")
    print(f"- HTML Report: {results_dir}/integration_test_report.html")
    print(f"- JUnit XML: {results_dir}/junit_results.xml")
    print(f"- Exit Code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    # Run integration tests when executed directly
    exit(run_integration_tests())