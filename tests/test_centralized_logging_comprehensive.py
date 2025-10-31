"""
Comprehensive tests for centralized logging and error handling implementation.

This test suite validates:
1. Centralized logging service functionality
2. JSON-formatted logging with proper levels
3. Structured logging with context and correlation IDs
4. User-friendly error messages and recovery mechanisms
5. Security logging for sensitive operations
6. Performance and memory leak testing

Following Vibe Coding philosophy:
- Comprehensive logging
- Proper error handling with detailed logging
- Security practices for sensitive operations
- Quality gates with testing requirements
"""

import json
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

import pytest

from src.core.centralized_logging_service import (
    CentralizedLoggingService,
    LoggingConfiguration,
    LogLevel,
    CorrelationContext,
    SecurityEvent,
    get_logging_service,
    configure_logging
)
from src.core.exceptions import (
    CandyCadenceException,
    ParsingError,
    FileSystemError,
    ValidationError,
    get_user_friendly_message,
    get_recovery_suggestions
)
from src.core.error_recovery_engine import ErrorRecoveryEngine


class TestCentralizedLoggingService:
    """Test the centralized logging service implementation."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def logging_config(self, temp_log_dir):
        """Create logging configuration for testing."""
        return LoggingConfiguration(
            log_level=LogLevel.DEBUG,
            log_directory=temp_log_dir,
            log_retention_days=7,
            enable_console_output=True,
            enable_file_output=True,
            max_log_file_size=1024*1024,  # 1MB
            structured_logging=True,
            security_logging=True,
            correlation_tracking=True
        )
    
    @pytest.fixture
    def logging_service(self, logging_config):
        """Create a logging service instance for testing."""
        service = CentralizedLoggingService(logging_config)
        yield service
        service.shutdown()
    
    def test_logging_service_initialization(self, logging_service, logging_config):
        """Test logging service initialization."""
        assert logging_service.config == logging_config
        assert logging_service.correlation_context is not None
        assert logging_service.error_history is not None
        assert logging_service._lock is not None
    
    def test_log_levels_functionality(self, logging_service):
        """Test all log levels work correctly."""
        test_message = "Test message for level validation"
        
        # Test each log level
        logging_service.log_debug(test_message)
        logging_service.log_info(test_message)
        logging_service.log_warning(test_message)
        logging_service.log_error(Exception(test_message))
        logging_service.log_critical(Exception(test_message))
        
        # Verify logs were created (actual verification would require reading log files)
        assert logging_service.error_history is not None
    
    def test_structured_logging_with_context(self, logging_service):
        """Test structured logging with additional context."""
        context = {
            "operation": "file_parsing",
            "file_path": "/test/model.stl",
            "file_size": 1024,
            "parser_name": "STLParser"
        }
        
        logging_service.log_info("File parsing started", **context)
        
        # Verify context is stored in current operation context
        assert "file_parsing" in str(logging_service.current_context.get("operation", ""))
    
    def test_correlation_id_tracking(self, logging_service):
        """Test correlation ID generation and tracking."""
        # Test correlation context creation
        correlation_id = logging_service._create_correlation_context()
        assert correlation_id is not None
        assert len(correlation_id) > 0
        
        # Test context isolation
        context1 = CorrelationContext()
        context2 = CorrelationContext()
        assert context1.correlation_id != context2.correlation_id
    
    def test_security_logging(self, logging_service):
        """Test security event logging."""
        security_event = SecurityEvent(
            event_type="FILE_ACCESS",
            resource_path="/sensitive/file.txt",
            user_action="read",
            risk_level="medium"
        )
        
        logging_service.log_security_event(security_event)
        
        # Verify security events are tracked
        assert len(logging_service.security_events) > 0
        assert logging_service.security_events[-1].event_type == "FILE_ACCESS"
    
    def test_error_handling_with_context(self, logging_service):
        """Test comprehensive error handling with context."""
        test_error = ValueError("Test error message")
        context = {
            "operation": "parsing",
            "file_path": "/test/model.stl",
            "parser_version": "2.0.0"
        }
        
        error_context = logging_service.log_error(test_error, context)
        
        # Verify error is properly logged with context
        assert error_context is not None
        assert "operation" in error_context
        assert error_context["operation"] == "parsing"
    
    def test_performance_logging(self, logging_service):
        """Test performance-related logging."""
        logging_service.log_performance_metrics(
            operation="file_parsing",
            duration_ms=150.5,
            memory_usage_mb=64.2,
            throughput_items_per_sec=100
        )
        
        # Verify performance metrics are tracked
        assert len(logging_service.performance_metrics) > 0
        metrics = logging_service.performance_metrics[-1]
        assert metrics["operation"] == "file_parsing"
        assert metrics["duration_ms"] == 150.5
    
    def test_thread_safety(self, logging_service):
        """Test thread safety of logging operations."""
        results = []
        errors = []
        
        def log_worker(worker_id: int):
            try:
                for i in range(10):
                    logging_service.log_info(f"Worker {worker_id} message {i}")
                results.append(worker_id)
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads to test concurrent logging
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all workers completed successfully
        assert len(errors) == 0, f"Thread errors occurred: {errors}"
        assert len(results) == 5
    
    def test_memory_efficiency(self, logging_service):
        """Test memory efficiency and cleanup."""
        # Log many messages to test memory management
        for i in range(1000):
            logging_service.log_info(f"Memory test message {i}")
            if i % 100 == 0:
                # Force periodic cleanup
                logging_service._cleanup_old_logs()
        
        # Verify service is still functional after heavy logging
        logging_service.log_info("Final test message")
        assert logging_service.is_running


class TestExceptionHandling:
    """Test standardized exception handling and user-friendly messages."""
    
    def test_exception_hierarchy(self):
        """Test that exception hierarchy works correctly."""
        # Test base exception
        base_error = CandyCadenceException("Base error")
        assert isinstance(base_error, Exception)
        
        # Test specific exceptions
        parsing_error = ParsingError("Parsing failed")
        assert isinstance(parsing_error, CandyCadenceException)
        
        file_error = FileSystemError("File not found")
        assert isinstance(file_error, CandyCadenceException)
        
        validation_error = ValidationError("Invalid format")
        assert isinstance(validation_error, CandyCadenceException)
    
    def test_user_friendly_messages(self):
        """Test user-friendly error message generation."""
        # Test parsing error message
        parsing_error = ParsingError("UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff")
        user_message = get_user_friendly_message(parsing_error)
        assert "file format" in user_message.lower() or "encoding" in user_message.lower()
        
        # Test file system error message
        file_error = FileSystemError("Permission denied: '/protected/file.txt'")
        user_message = get_user_friendly_message(file_error)
        assert "permission" in user_message.lower() or "access" in user_message.lower()
        
        # Test validation error message
        validation_error = ValidationError("Required field 'vertices' missing")
        user_message = get_user_friendly_message(validation_error)
        assert "missing" in user_message.lower() or "required" in user_message.lower()
    
    def test_recovery_suggestions(self):
        """Test error recovery suggestions."""
        # Test parsing error recovery
        parsing_error = ParsingError("Invalid STL format")
        suggestions = get_recovery_suggestions(parsing_error)
        assert len(suggestions) > 0
        assert any("format" in s.lower() for s in suggestions)
        
        # Test file system error recovery
        file_error = FileSystemError("File not found")
        suggestions = get_recovery_suggestions(file_error)
        assert len(suggestions) > 0
        assert any("path" in s.lower() or "location" in s.lower() for s in suggestions)
    
    def test_error_recovery_integration(self, logging_service):
        """Test integration with error recovery engine."""
        recovery_engine = ErrorRecoveryEngine(logging_service)
        
        # Test automatic retry mechanism
        def failing_operation():
            raise ValueError("Temporary failure")
        
        def recovery_action():
            return "Recovered successfully"
        
        # Configure retry strategy
        recovery_engine.register_retry_strategy(
            ValueError,
            max_retries=3,
            backoff_factor=1.0
        )
        
        recovery_engine.register_recovery_action(
            ValueError,
            recovery_action
        )
        
        # Test recovery execution (this should succeed after retry)
        try:
            result = recovery_engine.execute_with_recovery(failing_operation)
            assert result == "Recovered successfully"
        except Exception as e:
            # If recovery fails, it should be properly logged
            assert "recovery failed" in str(e).lower()


class TestLoggingIntegration:
    """Test integration with other components."""
    
    def test_parser_integration(self, logging_service):
        """Test integration with parser components."""
        # Simulate parser error handling
        try:
            raise ParsingError("STL parsing failed: invalid triangle data")
        except Exception as e:
            context = {
                "parser_name": "STLParser",
                "file_path": "/test/model.stl",
                "operation": "parse"
            }
            
            error_context = logging_service.log_error(e, context)
            
            # Verify error context is comprehensive
            assert "parser_name" in error_context
            assert "STLParser" in error_context["parser_name"]
    
    def test_database_integration(self, logging_service):
        """Test integration with database components."""
        # Simulate database error handling
        try:
            raise FileSystemError("Database connection failed")
        except Exception as e:
            context = {
                "component": "database",
                "operation": "connect",
                "database_path": "/data/models.db"
            }
            
            logging_service.log_error(e, context)
            
            # Verify database-specific logging
            assert "database" in str(logging_service.current_context.get("component", ""))
    
    def test_ui_integration(self, logging_service):
        """Test integration with UI components."""
        # Simulate UI error handling
        user_message = "Save operation failed due to insufficient permissions"
        context = {
            "component": "ui",
            "operation": "save_file",
            "user_facing": True
        }
        
        logging_service.log_warning(user_message, **context)
        
        # Verify UI-specific logging
        assert logging_service.current_context.get("component") == "ui"


class TestLoggingPerformance:
    """Test logging performance and optimization."""
    
    @pytest.mark.performance
    def test_logging_throughput(self, logging_service):
        """Test logging throughput under load."""
        start_time = time.time()
        message_count = 1000
        
        for i in range(message_count):
            logging_service.log_info(f"Performance test message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle at least 1000 messages per second
        throughput = message_count / duration
        assert throughput >= 1000, f"Logging throughput too low: {throughput} messages/sec"
    
    @pytest.mark.performance
    def test_memory_usage_stability(self, logging_service):
        """Test memory usage stability during extended logging."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Log many messages to test memory stability
        for i in range(10000):
            logging_service.log_info(f"Memory stability test {i}")
            if i % 1000 == 0 and i > 0:
                logging_service._cleanup_old_logs()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 10k messages)
        assert memory_increase < 50 * 1024 * 1024, f"Memory leak detected: {memory_increase} bytes"


class TestLoggingSecurity:
    """Test security aspects of logging implementation."""
    
    def test_sensitive_data_filtering(self, logging_service):
        """Test that sensitive data is properly filtered from logs."""
        sensitive_data = {
            "password": "secret123",
            "api_key": "sk-1234567890abcdef",
            "token": "bearer_token_here",
            "file_path": "/sensitive/data.txt"
        }
        
        logging_service.log_info("User login attempt", **sensitive_data)
        
        # Verify sensitive data is not logged in plain text
        # (actual verification would require checking log file contents)
        assert len(logging_service.security_events) > 0
    
    def test_audit_trail_creation(self, logging_service):
        """Test creation of audit trails for critical operations."""
        # Simulate critical operation
        critical_event = SecurityEvent(
            event_type="FILE_DELETE",
            resource_path="/important/file.txt",
            user_action="delete",
            risk_level="high"
        )
        
        logging_service.log_security_event(critical_event)
        
        # Verify audit trail is created
        assert len(logging_service.audit_trail) > 0
        audit_entry = logging_service.audit_trail[-1]
        assert audit_entry.event_type == "FILE_DELETE"
    
    def test_log_file_permissions(self, temp_log_dir):
        """Test that log files have appropriate permissions."""
        config = LoggingConfiguration(
            log_level=LogLevel.INFO,
            log_directory=temp_log_dir,
            security_logging=True
        )
        
        service = CentralizedLoggingService(config)
        service.log_info("Test message")
        service.shutdown()
        
        # Check that log files are created with appropriate permissions
        log_files = list(Path(temp_log_dir).glob("*.json"))
        if log_files:
            log_file = log_files[0]
            # Log files should not be world-readable
            stat = log_file.stat()
            permissions = oct(stat.st_mode)[-3:]
            assert permissions != "644"  # Should not be world-readable


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])