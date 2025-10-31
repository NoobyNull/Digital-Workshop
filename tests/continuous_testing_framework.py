"""
Continuous Testing and Monitoring Framework for Candy-Cadence.

This module provides comprehensive continuous testing capabilities including:
- Automated test execution and scheduling
- Test result monitoring and analytics
- Test failure notifications and alerting
- Continuous integration support
- Test environment management
- Performance regression monitoring
- Quality gate enforcement
"""

import gc
import json
import os
import shutil
import smtplib
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.logging_config import get_logger
from src.core.enhanced_error_handler import EnhancedErrorHandler


@dataclass
class TestSuiteConfig:
    """Configuration for a test suite."""
    name: str
    test_patterns: List[str]  # File patterns to match
    schedule: str  # cron-like schedule or "daily", "hourly", etc.
    timeout_minutes: int
    critical: bool
    retry_count: int
    environment_vars: Dict[str, str]
    quality_gates: Dict[str, float]  # metric_name: threshold


@dataclass
class TestExecution:
    """Single test execution record."""
    timestamp: str
    test_suite: str
    duration_seconds: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    success: bool
    exit_code: int
    output_log: str
    metrics: Dict[str, float]
    regression_detected: bool
    quality_score: float


@dataclass
class MonitoringAlert:
    """Test monitoring alert."""
    alert_id: str
    timestamp: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    test_suite: str
    metric_name: str
    current_value: float
    threshold: float
    message: str
    resolved: bool = False


class ContinuousTestScheduler:
    """Manages scheduling and execution of continuous tests."""
    
    def __init__(self, config_file: str = "continuous_test_config.json"):
        """Initialize continuous test scheduler."""
        self.logger = get_logger(__name__)
        self.config_file = Path(config_file)
        self.execution_history_file = Path("test_execution_history.json")
        self.alerts_file = Path("test_alerts.json")
        
        # Test execution tracking
        self.execution_history = self._load_execution_history()
        self.current_executions = {}  # test_suite -> execution_info
        self.lock = threading.Lock()
        
        # Notification settings
        self.email_config = self._load_email_config()
        
        # Load test suite configurations
        self.test_suites = self._load_test_suite_configs()
        
        # Alert management
        self.active_alerts = self._load_alerts()
        
        # Statistics and analytics
        self.test_analytics = TestAnalytics()
        
        # Start scheduler
        self.scheduler_running = False
        self.scheduler_thread = None
    
    def _load_test_suite_configs(self) -> Dict[str, TestSuiteConfig]:
        """Load test suite configurations."""
        if not self.config_file.exists():
            # Create default configuration
            default_configs = [
                TestSuiteConfig(
                    name="unit_tests",
                    test_patterns=["test_*.py"],
                    schedule="hourly",
                    timeout_minutes=30,
                    critical=True,
                    retry_count=2,
                    environment_vars={"PYTEST_TIMEOUT": "1800"},
                    quality_gates={"test_coverage": 80.0, "failure_rate": 5.0}
                ),
                TestSuiteConfig(
                    name="integration_tests",
                    test_patterns=["test_*_integration.py", "test_*_workflow.py"],
                    schedule="daily",
                    timeout_minutes=60,
                    critical=True,
                    retry_count=1,
                    environment_vars={"INTEGRATION_TESTS": "1"},
                    quality_gates={"execution_time": 3600.0, "memory_usage": 1000.0}
                ),
                TestSuiteConfig(
                    name="performance_tests",
                    test_patterns=["test_performance*.py"],
                    schedule="daily",
                    timeout_minutes=120,
                    critical=True,
                    retry_count=0,
                    environment_vars={"PERFORMANCE_TESTS": "1"},
                    quality_gates={"regression_rate": 10.0, "memory_leaks": 1.0}
                ),
                TestSuiteConfig(
                    name="e2e_tests",
                    test_patterns=["test_end_to_end*.py"],
                    schedule="weekly",
                    timeout_minutes=180,
                    critical=False,
                    retry_count=1,
                    environment_vars={"E2E_TESTS": "1"},
                    quality_gates={"success_rate": 95.0}
                ),
            ]
            
            self._save_test_suite_configs(default_configs)
            return {config.name: config for config in default_configs}
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            return {
                name: TestSuiteConfig(**config) 
                for name, config in config_data.items()
            }
        except Exception as e:
            self.logger.error(f"Failed to load test suite configs: {e}")
            return {}
    
    def _save_test_suite_configs(self, configs: List[TestSuiteConfig]):
        """Save test suite configurations."""
        try:
            config_data = {
                config.name: asdict(config) 
                for config in configs
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save test suite configs: {e}")
    
    def _load_execution_history(self) -> List[TestExecution]:
        """Load execution history from file."""
        if not self.execution_history_file.exists():
            return []
        
        try:
            with open(self.execution_history_file, 'r') as f:
                data = json.load(f)
            
            return [TestExecution(**execution) for execution in data]
        except Exception as e:
            self.logger.error(f"Failed to load execution history: {e}")
            return []
    
    def _save_execution_history(self):
        """Save execution history to file."""
        try:
            with open(self.execution_history_file, 'w') as f:
                json.dump([asdict(exec) for exec in self.execution_history[-1000:]], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save execution history: {e}")
    
    def _load_email_config(self) -> Dict[str, Any]:
        """Load email notification configuration."""
        email_config_file = Path("email_config.json")
        
        if not email_config_file.exists():
            # Default email config (disabled)
            return {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": [],
                "alerts_only": True
            }
        
        try:
            with open(email_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load email config: {e}")
            return {"enabled": False}
    
    def _load_alerts(self) -> List[MonitoringAlert]:
        """Load existing alerts."""
        if not self.alerts_file.exists():
            return []
        
        try:
            with open(self.alerts_file, 'r') as f:
                data = json.load(f)
            
            return [MonitoringAlert(**alert) for alert in data]
        except Exception as e:
            self.logger.error(f"Failed to load alerts: {e}")
            return []
    
    def _save_alerts(self):
        """Save alerts to file."""
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump([asdict(alert) for alert in self.active_alerts[-100:]], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save alerts: {e}")
    
    def start_scheduler(self):
        """Start the continuous testing scheduler."""
        if self.scheduler_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Continuous test scheduler started")
    
    def stop_scheduler(self):
        """Stop the continuous testing scheduler."""
        self.scheduler_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        self.logger.info("Continuous test scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        self.logger.info("Starting scheduler loop")
        
        while self.scheduler_running:
            try:
                # Schedule tests based on their configurations
                for suite_name, config in self.test_suites.items():
                    self._schedule_test_suite(config)
                
                # Run pending tests
                self._run_pending_tests()
                
                # Check for alerts
                self._check_alert_conditions()
                
                # Clean up old history
                self._cleanup_old_history()
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)
    
    def _schedule_test_suite(self, config: TestSuiteConfig):
        """Schedule a test suite for execution."""
        try:
            # Check if it's time to run this test suite
            # This is a simplified scheduling logic
            if config.schedule == "hourly":
                # Run every hour
                self.logger.debug(f"Scheduling {config.name} for hourly execution")
            elif config.schedule == "daily":
                # Run every day at 2 AM
                current_time = datetime.now()
                if current_time.hour == 2 and current_time.minute < 5:
                    self.logger.debug(f"Scheduling {config.name} for daily execution")
            elif config.schedule == "weekly":
                # Run every Sunday at 3 AM
                current_time = datetime.now()
                if current_time.weekday() == 6 and current_time.hour == 3 and current_time.minute < 5:
                    self.logger.debug(f"Scheduling {config.name} for weekly execution")
            
            # Add to pending executions
            with self.lock:
                if config.name not in self.current_executions:
                    self.current_executions[config.name] = {
                        "config": config,
                        "scheduled_time": datetime.now(),
                        "attempts": 0
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to schedule test suite {config.name}: {e}")
    
    def _run_pending_tests(self):
        """Run any pending test suites."""
        with self.lock:
            for suite_name, execution_info in list(self.current_executions.items()):
                config = execution_info["config"]
                
                # Check if we should run this test
                if self._should_run_test(config, execution_info):
                    self._execute_test_suite(suite_name, config)
    
    def _should_run_test(self, config: TestSuiteConfig, execution_info: Dict) -> bool:
        """Check if a test should be run now."""
        scheduled_time = execution_info["scheduled_time"]
        attempts = execution_info["attempts"]
        
        # Check timeout
        elapsed_time = datetime.now() - scheduled_time
        if elapsed_time.total_seconds() > config.timeout_minutes * 60:
            self.logger.warning(f"Test suite {config.name} timed out after {config.timeout_minutes} minutes")
            del self.current_executions[config.name]
            return False
        
        # Check retry logic
        if attempts >= config.retry_count + 1:
            self.logger.warning(f"Test suite {config.name} exceeded retry count")
            del self.current_executions[config.name]
            return False
        
        return True
    
    def _execute_test_suite(self, suite_name: str, config: TestSuiteConfig):
        """Execute a test suite."""
        self.logger.info(f"Starting execution of test suite: {suite_name}")
        
        execution_info = self.current_executions[suite_name]
        execution_info["attempts"] += 1
        execution_info["start_time"] = datetime.now()
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment_vars)
            
            # Run tests
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--timeout", str(config.timeout_minutes * 60),
                "--json-report", "--json-report-file", f"test_results_{suite_name}_{int(time.time())}.json"
            ]
            
            # Add test patterns
            for pattern in config.test_patterns:
                cmd.extend(["-k", pattern])
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.timeout_minutes * 60
            )
            end_time = time.time()
            
            # Parse test results
            execution_result = self._parse_test_results(
                suite_name, result, start_time, end_time, config
            )
            
            # Store execution result
            self.execution_history.append(execution_result)
            self._save_execution_history()
            
            # Update analytics
            self.test_analytics.record_execution(execution_result)
            
            # Check for alerts
            self._check_for_alerts(execution_result, config)
            
            # Send notifications if needed
            if execution_result.success or config.critical:
                self._send_notifications(execution_result, config)
            
            self.logger.info(f"Test suite {suite_name} completed: "
                           f"{execution_result.tests_passed}/{execution_result.tests_run} passed")
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test suite {suite_name} timed out")
            self._create_timeout_alert(suite_name, config)
        
        except Exception as e:
            self.logger.error(f"Test suite {suite_name} failed: {e}")
            self._create_execution_error_alert(suite_name, config, str(e))
        
        finally:
            # Clean up
            if suite_name in self.current_executions:
                del self.current_executions[suite_name]
    
    def _parse_test_results(self, suite_name: str, result: subprocess.CompletedProcess,
                           start_time: float, end_time: float, config: TestSuiteConfig) -> TestExecution:
        """Parse test execution results."""
        try:
            # Parse pytest JSON output if available
            json_files = list(Path(".").glob(f"test_results_{suite_name}_*.json"))
            
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            
            if json_files:
                latest_json = max(json_files, key=lambda f: f.stat().st_mtime)
                with open(latest_json, 'r') as f:
                    json_data = json.load(f)
                
                # Extract test counts from JSON
                summary = json_data.get("summary", {})
                tests_run = summary.get("total", 0)
                tests_passed = summary.get("passed", 0)
                tests_failed = summary.get("failed", 0)
                tests_skipped = summary.get("skipped", 0)
                
                # Clean up JSON file
                latest_json.unlink(missing_ok=True)
            
            # Calculate metrics
            duration = end_time - start_time
            success_rate = (tests_passed / tests_run * 100) if tests_run > 0 else 0
            failure_rate = (tests_failed / tests_run * 100) if tests_run > 0 else 0
            
            # Check for regressions
            regression_detected = self._detect_regressions(suite_name, duration, failure_rate)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                success_rate, duration, regression_detected, config
            )
            
            return TestExecution(
                timestamp=datetime.now().isoformat(),
                test_suite=suite_name,
                duration_seconds=duration,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                success=result.returncode == 0 and tests_failed == 0,
                exit_code=result.returncode,
                output_log=result.stdout + result.stderr,
                metrics={
                    "success_rate": success_rate,
                    "failure_rate": failure_rate,
                    "duration": duration
                },
                regression_detected=regression_detected,
                quality_score=quality_score
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse test results: {e}")
            
            # Return minimal execution result
            return TestExecution(
                timestamp=datetime.now().isoformat(),
                test_suite=suite_name,
                duration_seconds=end_time - start_time,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                success=False,
                exit_code=result.returncode,
                output_log=result.stdout + result.stderr,
                metrics={"error": str(e)},
                regression_detected=False,
                quality_score=0.0
            )
    
    def _detect_regressions(self, suite_name: str, duration: float, failure_rate: float) -> bool:
        """Detect performance or quality regressions."""
        # Get historical data for this suite
        suite_history = [e for e in self.execution_history if e.test_suite == suite_name]
        
        if len(suite_history) < 5:
            return False  # Not enough history
        
        # Check duration regression (20% increase)
        recent_durations = [e.duration_seconds for e in suite_history[-5:]]
        avg_duration = sum(recent_durations) / len(recent_durations)
        
        if duration > avg_duration * 1.2:
            self.logger.warning(f"Duration regression detected in {suite_name}: "
                              f"current={duration:.2f}s, avg={avg_duration:.2f}s")
            return True
        
        # Check failure rate regression (exceeding 5%)
        if failure_rate > 5.0:
            self.logger.warning(f"Failure rate regression detected in {suite_name}: "
                              f"current={failure_rate:.1f}%, threshold=5.0%")
            return True
        
        return False
    
    def _calculate_quality_score(self, success_rate: float, duration: float,
                               regression_detected: bool, config: TestSuiteConfig) -> float:
        """Calculate overall quality score for test execution."""
        score = 0.0
        
        # Success rate contribution (70%)
        score += success_rate * 0.7
        
        # Duration contribution (20%) - penalize slow execution
        max_expected_duration = config.timeout_minutes * 60 * 0.5  # 50% of timeout
        if duration <= max_expected_duration:
            duration_score = 100.0
        else:
            duration_score = max(0, 100 * (1 - (duration - max_expected_duration) / max_expected_duration))
        
        score += duration_score * 0.2
        
        # Regression penalty (10%)
        if regression_detected:
            score -= 10.0
        
        return max(0, score)
    
    def _check_for_alerts(self, execution: TestExecution, config: TestSuiteConfig):
        """Check for alert conditions and create alerts if needed."""
        # Quality gate violations
        for metric_name, threshold in config.quality_gates.items():
            current_value = execution.metrics.get(metric_name, 0.0)
            
            if self._should_create_alert(metric_name, current_value, threshold, config):
                self._create_quality_gate_alert(execution, config, metric_name, current_value, threshold)
        
        # Test failures in critical suites
        if config.critical and not execution.success:
            self._create_failure_alert(execution, config)
    
    def _should_create_alert(self, metric_name: str, current_value: float, 
                           threshold: float, config: TestSuiteConfig) -> bool:
        """Determine if an alert should be created."""
        # Check for metric violations
        if metric_name in ["failure_rate", "execution_time", "memory_usage", "regression_rate"]:
            return current_value > threshold
        elif metric_name in ["success_rate", "test_coverage"]:
            return current_value < threshold
        elif metric_name in ["memory_leaks"]:
            return current_value > threshold  # Memory leaks should be 0
        
        return False
    
    def _create_quality_gate_alert(self, execution: TestExecution, config: TestSuiteConfig,
                                 metric_name: str, current_value: float, threshold: float):
        """Create a quality gate violation alert."""
        severity = "CRITICAL" if config.critical else "HIGH"
        
        alert = MonitoringAlert(
            alert_id=f"quality_gate_{config.name}_{metric_name}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            severity=severity,
            test_suite=config.name,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            message=f"Quality gate violation in {config.name}: {metric_name} = {current_value}, "
                   f"threshold = {threshold}"
        )
        
        self.active_alerts.append(alert)
        self._save_alerts()
        
        self.logger.warning(f"Quality gate alert created: {alert.message}")
    
    def _create_failure_alert(self, execution: TestExecution, config: TestSuiteConfig):
        """Create a test failure alert."""
        alert = MonitoringAlert(
            alert_id=f"failure_{config.name}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            severity="CRITICAL",
            test_suite=config.name,
            metric_name="test_failures",
            current_value=execution.tests_failed,
            threshold=0,
            message=f"Critical test suite failure in {config.name}: "
                   f"{execution.tests_failed} tests failed"
        )
        
        self.active_alerts.append(alert)
        self._save_alerts()
        
        self.logger.error(f"Critical test failure alert created: {alert.message}")
    
    def _create_timeout_alert(self, suite_name: str, config: TestSuiteConfig):
        """Create a timeout alert."""
        alert = MonitoringAlert(
            alert_id=f"timeout_{suite_name}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            severity="HIGH",
            test_suite=suite_name,
            metric_name="execution_timeout",
            current_value=config.timeout_minutes,
            threshold=config.timeout_minutes,
            message=f"Test suite {suite_name} timed out after {config.timeout_minutes} minutes"
        )
        
        self.active_alerts.append(alert)
        self._save_alerts()
        
        self.logger.error(f"Timeout alert created: {alert.message}")
    
    def _create_execution_error_alert(self, suite_name: str, config: TestSuiteConfig, error: str):
        """Create an execution error alert."""
        alert = MonitoringAlert(
            alert_id=f"error_{suite_name}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            severity="HIGH",
            test_suite=suite_name,
            metric_name="execution_error",
            current_value=1.0,
            threshold=0.0,
            message=f"Test suite {suite_name} execution error: {error}"
        )
        
        self.active_alerts.append(alert)
        self._save_alerts()
        
        self.logger.error(f"Execution error alert created: {alert.message}")
    
    def _send_notifications(self, execution: TestExecution, config: TestSuiteConfig):
        """Send notifications for test execution results."""
        if not self.email_config.get("enabled", False):
            return
        
        try:
            # Determine if notification should be sent
            should_notify = (
                not execution.success or  # Always notify on failure
                execution.regression_detected or  # Always notify on regression
                config.critical or  # Always notify on critical suites
                not self.email_config.get("alerts_only", True)  # Notify on all if not alerts-only
            )
            
            if not should_notify:
                return
            
            # Prepare email content
            subject = f"[Candy-Cadence] Test {execution.test_suite} {'FAILED' if not execution.success else 'COMPLETED'}"
            
            body = f"""
Test Suite: {execution.test_suite}
Timestamp: {execution.timestamp}
Status: {'PASS' if execution.success else 'FAIL'}
Duration: {execution.duration_seconds:.2f} seconds

Test Results:
- Tests Run: {execution.tests_run}
- Tests Passed: {execution.tests_passed}
- Tests Failed: {execution.tests_failed}
- Tests Skipped: {execution.tests_skipped}

Metrics:
"""
            
            for metric_name, value in execution.metrics.items():
                body += f"- {metric_name}: {value}\n"
            
            if execution.regression_detected:
                body += f"\n⚠️ REGRESSION DETECTED!\n"
            
            if not execution.success and execution.tests_failed > 0:
                body += f"\n❌ Test failures detected!\n"
            
            # Send email
            self._send_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def _send_email(self, subject: str, body: str):
        """Send email notification."""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config["username"]
            msg['To'] = ", ".join(self.email_config["recipients"])
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def _check_alert_conditions(self):
        """Check if any alert conditions need to be resolved."""
        current_time = datetime.now()
        
        for alert in self.active_alerts:
            if alert.resolved:
                continue
            
            # Auto-resolve alerts after 24 hours
            alert_time = datetime.fromisoformat(alert.timestamp)
            if current_time - alert_time > timedelta(hours=24):
                alert.resolved = True
                self.logger.info(f"Auto-resolved alert: {alert.alert_id}")
        
        self._save_alerts()
    
    def _cleanup_old_history(self):
        """Clean up old execution history."""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        self.execution_history = [
            exec for exec in self.execution_history
            if datetime.fromisoformat(exec.timestamp) > cutoff_date
        ]
    
    def get_test_status(self) -> Dict[str, Any]:
        """Get current test execution status."""
        with self.lock:
            status = {
                "scheduler_running": self.scheduler_running,
                "current_executions": {
                    name: {
                        "config": asdict(info["config"]),
                        "scheduled_time": info["scheduled_time"].isoformat(),
                        "attempts": info["attempts"]
                    }
                    for name, info in self.current_executions.items()
                },
                "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
                "recent_executions": [
                    asdict(exec) for exec in self.execution_history[-10:]
                ]
            }
        
        return status


class TestAnalytics:
    """Analytics and reporting for test execution data."""
    
    def __init__(self):
        """Initialize test analytics."""
        self.logger = get_logger(__name__)
        self.execution_data = deque(maxlen=1000)
    
    def record_execution(self, execution: TestExecution):
        """Record test execution for analytics."""
        self.execution_data.append(execution)
    
    def get_suite_statistics(self, suite_name: str, days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific test suite."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        suite_executions = [
            exec for exec in self.execution_data
            if exec.test_suite == suite_name and 
               datetime.fromisoformat(exec.timestamp) > cutoff_date
        ]
        
        if not suite_executions:
            return {"error": "No executions found"}
        
        # Calculate statistics
        total_executions = len(suite_executions)
        successful_executions = len([e for e in suite_executions if e.success])
        failed_executions = total_executions - successful_executions
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        durations = [e.duration_seconds for e in suite_executions]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        regression_count = len([e for e in suite_executions if e.regression_detected])
        
        return {
            "suite_name": suite_name,
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "regression_count": regression_count,
            "quality_score_avg": sum(e.quality_score for e in suite_executions) / total_executions
        }
    
    def get_trend_analysis(self, suite_name: str, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for test suite performance."""
        # This would implement trend analysis logic
        # For now, return basic trend data
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        suite_executions = [
            exec for exec in self.execution_data
            if exec.test_suite == suite_name and 
               datetime.fromisoformat(exec.timestamp) > cutoff_date
        ]
        
        if len(suite_executions) < 5:
            return {"error": "Insufficient data for trend analysis"}
        
        # Simple trend calculation
        recent_success_rate = sum(1 for e in suite_executions[-10:] if e.success) / min(10, len(suite_executions)) * 100
        older_success_rate = sum(1 for e in suite_executions[-20:-10] if e.success) / min(10, len(suite_executions)-10) * 100
        
        trend = "improving" if recent_success_rate > older_success_rate else "declining" if recent_success_rate < older_success_rate else "stable"
        
        return {
            "suite_name": suite_name,
            "trend": trend,
            "recent_success_rate": recent_success_rate,
            "older_success_rate": older_success_rate,
            "data_points": len(suite_executions)
        }


if __name__ == '__main__':
    # Example usage of continuous testing framework
    
    # Initialize and start scheduler
    scheduler = ContinuousTestScheduler()
    
    print("Starting Continuous Testing Framework...")
    print("Available test suites:")
    for name, config in scheduler.test_suites.items():
        print(f"  - {name}: {config.schedule} ({'critical' if config.critical else 'non-critical'})")
    
    # Start the scheduler
    scheduler.start_scheduler()
    
    try:
        # Keep the scheduler running
        print("Scheduler started. Press Ctrl+C to stop...")
        while True:
            time.sleep(60)
            
            # Print status every 10 minutes
            if int(time.time()) % 600 == 0:
                status = scheduler.get_test_status()
                print(f"Status: {status['active_alerts']} active alerts, "
                     f"{len(status['current_executions'])} running tests")
    
    except KeyboardInterrupt:
        print("Shutting down scheduler...")
        scheduler.stop_scheduler()
        print("Scheduler stopped.")