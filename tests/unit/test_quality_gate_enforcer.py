#!/usr/bin/env python3
"""
Unit tests for the Quality Gate Enforcement System

This test suite validates all functionality of the quality gate enforcement system,
including tool orchestration, quality gate evaluation, result aggregation,
and reporting capabilities.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

# Import the quality gate enforcer
from quality_gate_enforcer import (
    QualityGateEnforcer,
    ToolResult,
    QualityGate,
    QualityGateResult,
    JSONFormatter
)


class TestJSONFormatter(unittest.TestCase):
    """Test the custom JSON formatter for logging."""
    
    def setUp(self):
        self.formatter = JSONFormatter()
    
    def test_format_basic_log_entry(self):
        """Test basic log entry formatting."""
        record = Mock()
        record.created = 1609459200.0  # 2021-01-01 00:00:00 UTC
        record.levelname = "INFO"
        record.name = "test_logger"
        record.getMessage.return_value = "Test message"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.exc_info = None
        
        result = self.formatter.format(record)
        log_entry = json.loads(result)
        
        self.assertEqual(log_entry['timestamp'], "2021-01-01T00:00:00")
        self.assertEqual(log_entry['level'], "INFO")
        self.assertEqual(log_entry['logger'], "test_logger")
        self.assertEqual(log_entry['message'], "Test message")
        self.assertEqual(log_entry['module'], "test_module")
        self.assertEqual(log_entry['function'], "test_function")
        self.assertEqual(log_entry['line'], 42)


class TestToolResult(unittest.TestCase):
    """Test the ToolResult dataclass."""
    
    def test_tool_result_creation(self):
        """Test creating a ToolResult instance."""
        result = ToolResult(
            tool_name="test_tool",
            execution_time=1.5,
            exit_code=0,
            success=True,
            output_path="/tmp/test.json",
            raw_results={"status": "ok"},
            metrics={"score": 95.0},
            violations=[],
            recommendations=["Run successfully"]
        )
        
        self.assertEqual(result.tool_name, "test_tool")
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.success)
        self.assertEqual(result.output_path, "/tmp/test.json")
        self.assertEqual(result.raw_results["status"], "ok")
        self.assertEqual(result.metrics["score"], 95.0)
        self.assertEqual(result.recommendations, ["Run successfully"])


class TestQualityGate(unittest.TestCase):
    """Test the QualityGate dataclass."""
    
    def test_quality_gate_creation(self):
        """Test creating a QualityGate instance."""
        gate = QualityGate(
            name="Test Gate",
            description="Test quality gate",
            threshold=95.0,
            operator=">=",
            severity="major",
            auto_fix=False,
            enabled=True
        )
        
        self.assertEqual(gate.name, "Test Gate")
        self.assertEqual(gate.description, "Test quality gate")
        self.assertEqual(gate.threshold, 95.0)
        self.assertEqual(gate.operator, ">=")
        self.assertEqual(gate.severity, "major")
        self.assertFalse(gate.auto_fix)
        self.assertTrue(gate.enabled)


class TestQualityGateResult(unittest.TestCase):
    """Test the QualityGateResult dataclass."""
    
    def test_quality_gate_result_creation(self):
        """Test creating a QualityGateResult instance."""
        result = QualityGateResult(
            gate_name="Test Gate",
            passed=True,
            actual_value=96.0,
            threshold=95.0,
            severity="major",
            violations=[],
            recommendations=["Good job"]
        )
        
        self.assertEqual(result.gate_name, "Test Gate")
        self.assertTrue(result.passed)
        self.assertEqual(result.actual_value, 96.0)
        self.assertEqual(result.threshold, 95.0)
        self.assertEqual(result.severity, "major")
        self.assertEqual(result.recommendations, ["Good job"])


class TestQualityGateEnforcer(unittest.TestCase):
    """Test the main QualityGateEnforcer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        self.enforcer = QualityGateEnforcer(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test enforcer initialization."""
        self.assertIsInstance(self.enforcer, QualityGateEnforcer)
        self.assertEqual(self.enforcer.config_path, self.config_path)
        self.assertIsNotNone(self.enforcer.config)
        self.assertIsNotNone(self.enforcer.tools)
        self.assertEqual(len(self.enforcer.results), 0)
        self.assertEqual(len(self.enforcer.gate_results), 0)
    
    def test_load_config_with_defaults(self):
        """Test loading configuration with defaults."""
        config = self.enforcer._load_config()
        
        # Check that default quality gates are loaded
        self.assertIn('quality_gates', config)
        self.assertIn('monolithic_modules', config['quality_gates'])
        self.assertIn('naming_conventions', config['quality_gates'])
        self.assertIn('test_execution', config['quality_gates'])
        self.assertIn('code_quality', config['quality_gates'])
        
        # Check that default tools are loaded
        self.assertIn('tools', config)
        self.assertIn('code_quality_validator', config['tools'])
        self.assertIn('monolithic_detector', config['tools'])
        self.assertIn('naming_validator', config['tools'])
        self.assertIn('unified_test_runner', config['tools'])
    
    def test_evaluate_condition(self):
        """Test condition evaluation."""
        # Test greater than or equal
        self.assertTrue(self.enforcer._evaluate_condition(95.0, 95.0, '>='))
        self.assertTrue(self.enforcer._evaluate_condition(96.0, 95.0, '>='))
        self.assertFalse(self.enforcer._evaluate_condition(94.0, 95.0, '>='))
        
        # Test less than or equal
        self.assertTrue(self.enforcer._evaluate_condition(95.0, 95.0, '<='))
        self.assertTrue(self.enforcer._evaluate_condition(94.0, 95.0, '<='))
        self.assertFalse(self.enforcer._evaluate_condition(96.0, 95.0, '<='))
        
        # Test equality
        self.assertTrue(self.enforcer._evaluate_condition(95.0, 95.0, '=='))
        self.assertFalse(self.enforcer._evaluate_condition(96.0, 95.0, '=='))
        
        # Test not equal
        self.assertTrue(self.enforcer._evaluate_condition(96.0, 95.0, '!='))
        self.assertFalse(self.enforcer._evaluate_condition(95.0, 95.0, '!='))
        
        # Test unknown operator
        self.assertFalse(self.enforcer._evaluate_condition(95.0, 95.0, 'invalid'))
    
    def test_extract_code_quality_metrics(self):
        """Test extraction of code quality metrics."""
        results = {
            'summary': {
                'compliance_percentage': 95.5,
                'formatting_score': 98.0,
                'linting_score': 93.0,
                'total_issues': 5,
                'critical_issues': 1,
                'major_issues': 2,
                'minor_issues': 2
            }
        }
        
        metrics = self.enforcer._extract_code_quality_metrics(results)
        
        self.assertEqual(metrics['overall_compliance'], 95.5)
        self.assertEqual(metrics['formatting_score'], 98.0)
        self.assertEqual(metrics['linting_score'], 93.0)
        self.assertEqual(metrics['total_issues'], 5)
        self.assertEqual(metrics['critical_issues'], 1)
        self.assertEqual(metrics['major_issues'], 2)
        self.assertEqual(metrics['minor_issues'], 2)
    
    def test_extract_monolithic_metrics(self):
        """Test extraction of monolithic detector metrics."""
        results = {
            'summary': {
                'total_files_analyzed': 100,
                'monolithic_files_found': 2,
                'compliance_percentage': 98.0,
                'average_lines_of_code': 150,
                'max_lines_of_code': 600
            }
        }
        
        metrics = self.enforcer._extract_monolithic_metrics(results)
        
        self.assertEqual(metrics['total_files_analyzed'], 100)
        self.assertEqual(metrics['monolithic_files_found'], 2)
        self.assertEqual(metrics['compliance_percentage'], 98.0)
        self.assertEqual(metrics['average_lines_of_code'], 150)
        self.assertEqual(metrics['max_lines_of_code'], 600)
    
    def test_extract_naming_metrics(self):
        """Test extraction of naming validator metrics."""
        results = {
            'summary': {
                'total_files_validated': 50,
                'violations_found': 3,
                'compliance_percentage': 94.0,
                'adjective_violations': 2,
                'convention_violations': 1
            }
        }
        
        metrics = self.enforcer._extract_naming_metrics(results)
        
        self.assertEqual(metrics['total_files_validated'], 50)
        self.assertEqual(metrics['violations_found'], 3)
        self.assertEqual(metrics['compliance_percentage'], 94.0)
        self.assertEqual(metrics['adjective_violations'], 2)
        self.assertEqual(metrics['convention_violations'], 1)
    
    def test_extract_test_metrics(self):
        """Test extraction of test execution metrics."""
        results = {
            'summary': {
                'total_tests': 100,
                'passed_tests': 95,
                'failed_tests': 3,
                'skipped_tests': 2,
                'success_rate': 95.0,
                'execution_time': 45.5
            }
        }
        
        metrics = self.enforcer._extract_test_metrics(results)
        
        self.assertEqual(metrics['total_tests'], 100)
        self.assertEqual(metrics['passed_tests'], 95)
        self.assertEqual(metrics['failed_tests'], 3)
        self.assertEqual(metrics['skipped_tests'], 2)
        self.assertEqual(metrics['success_rate'], 95.0)
        self.assertEqual(metrics['execution_time'], 45.5)
    
    def test_evaluate_quality_gates(self):
        """Test quality gate evaluation."""
        # Mock tool results
        self.enforcer.results = [
            ToolResult(
                tool_name="code_quality_validator",
                execution_time=10.0,
                exit_code=0,
                success=True,
                output_path="",
                raw_results={},
                metrics={"overall_compliance": 96.0},
                violations=[],
                recommendations=[]
            ),
            ToolResult(
                tool_name="monolithic_detector",
                execution_time=5.0,
                exit_code=0,
                success=True,
                output_path="",
                raw_results={},
                metrics={"monolithic_files_found": 0},
                violations=[],
                recommendations=[]
            )
        ]
        
        gate_results = self.enforcer._evaluate_quality_gates()
        
        self.assertEqual(len(gate_results), 4)  # All quality gates
        
        # Check code quality gate
        code_quality_gate = next(g for g in gate_results if g.gate_name == "code_quality")
        self.assertTrue(code_quality_gate.passed)
        self.assertEqual(code_quality_gate.actual_value, 96.0)
        
        # Check monolithic modules gate
        monolithic_gate = next(g for g in gate_results if g.gate_name == "monolithic_modules")
        self.assertTrue(monolithic_gate.passed)
        self.assertEqual(monolithic_gate.actual_value, 0)
    
    @patch('subprocess.Popen')
    def test_execute_tool_success(self, mock_popen):
        """Test successful tool execution."""
        # Mock successful subprocess
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Mock file exists check
        with patch('pathlib.Path.exists', return_value=False):
            tool_config = {
                'command': 'echo',
                'args': ['test'],
                'timeout': 30,
                'output_pattern': ''
            }
            
            result = self.enforcer._execute_tool('test_tool', tool_config)
            
            self.assertTrue(result.success)
            self.assertEqual(result.exit_code, 0)
            self.assertGreater(result.execution_time, 0)
            self.assertEqual(result.tool_name, 'test_tool')
    
    @patch('subprocess.Popen')
    def test_execute_tool_failure(self, mock_popen):
        """Test failed tool execution."""
        # Mock failed subprocess
        mock_process = Mock()
        mock_process.communicate.return_value = ("error", "")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        tool_config = {
            'command': 'false',  # Command that always fails
            'args': [],
            'timeout': 30,
            'output_pattern': ''
        }
        
        result = self.enforcer._execute_tool('failing_tool', tool_config)
        
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertGreater(result.execution_time, 0)
        self.assertEqual(result.tool_name, 'failing_tool')


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "integration_test_config.yaml"
        
        # Create test configuration
        test_config = {
            'quality_gates': {
                'test_gate': {
                    'name': 'Test Gate',
                    'description': 'Test quality gate',
                    'threshold': 50.0,
                    'operator': '>=',
                    'severity': 'major',
                    'auto_fix': False,
                    'enabled': True
                }
            },
            'tools': {
                'test_tool': {
                    'command': 'echo',
                    'args': ['test'],
                    'timeout': 5,
                    'enabled': True,
                    'output_pattern': ''
                }
            },
            'reporting': {
                'formats': ['json', 'console']
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.Popen')
    def test_full_enforcement_cycle(self, mock_popen):
        """Test complete enforcement cycle."""
        # Mock successful tool execution
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        enforcer = QualityGateEnforcer(
            config_path=str(self.config_path),
            output_path=str(Path(self.temp_dir) / "report.json"),
            parallel_execution=False
        )
        
        result = enforcer.run_enforcement()
        
        self.assertIn('success', result)
        self.assertIn('execution_time', result)
        self.assertIn('execution_summary', result)
        self.assertIsInstance(result['execution_summary']['total_tools'], int)
        self.assertIsInstance(result['execution_summary']['successful_tools'], int)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestJSONFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestToolResult))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityGate))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityGateResult))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityGateEnforcer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)