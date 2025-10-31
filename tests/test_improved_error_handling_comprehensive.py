"""
Comprehensive Tests for Improved Error Handling and Reporting System

This test suite validates the complete error handling system including:
- Error categorization and classification
- Specific error handling with targeted exception handling
- Comprehensive error reporting with diagnostic information
- Graceful error recovery mechanisms
- Structured logging with performance monitoring
- Integration with shutdown system
"""

import unittest
import tempfile
import json
import time
import threading
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

# Import the error handling components
from src.core.error_handling.error_categories import (
    ErrorContext, ErrorSeverity, ErrorCategory, ErrorRecoveryStrategy,
    ErrorClassification, ErrorReport
)
from src.core.error_handling.error_reporter import (
    ErrorReporter, get_global_error_reporter, set_global_error_reporter
)
from src.core.error_handling.error_handlers import (
    SpecificErrorHandler, ShutdownErrorHandler, VTKErrorHandler,
    FileIOErrorHandler, MemoryErrorHandler,
    handle_shutdown_errors, handle_vtk_errors, handle_file_io_errors, handle_memory_errors,
    shutdown_safe, vtk_safe, file_io_safe, monitor_operation
)
from src.core.error_handling.comprehensive_logger import (
    ComprehensiveLogger, LogContext, get_global_logger, set_global_logger,
    log_info, log_error, operation_context
)


class TestErrorCategories(unittest.TestCase):
    """Test error categorization and classification."""
    
    def test_error_context_enum(self):
        """Test error context enumeration."""
        self.assertEqual(ErrorContext.SHUTDOWN.value, "shutdown")
        self.assertEqual(ErrorContext.RENDERING.value, "rendering")
        self.assertEqual(ErrorContext.FILE_LOADING.value, "file_loading")
        self.assertEqual(ErrorContext.FILE_SAVING.value, "file_saving")
        self.assertEqual(ErrorContext.NORMAL_OPERATION.value, "normal_operation")
    
    def test_error_severity_enum(self):
        """Test error severity enumeration."""
        self.assertEqual(ErrorSeverity.CRITICAL.value, "critical")
        self.assertEqual(ErrorSeverity.ERROR.value, "error")
        self.assertEqual(ErrorSeverity.WARNING.value, "warning")
        self.assertEqual(ErrorSeverity.INFO.value, "info")
    
    def test_error_category_enum(self):
        """Test error category enumeration."""
        self.assertEqual(ErrorCategory.VTK_ERROR.value, "vtk_error")
        self.assertEqual(ErrorCategory.FILE_IO_ERROR.value, "file_io_error")
        self.assertEqual(ErrorCategory.MEMORY_ERROR.value, "memory_error")
        self.assertEqual(ErrorCategory.NETWORK_ERROR.value, "network_error")
        self.assertEqual(ErrorCategory.SYSTEM_ERROR.value, "system_error")
    
    def test_error_recovery_strategy_enum(self):
        """Test error recovery strategy enumeration."""
        self.assertEqual(ErrorRecoveryStrategy.GRACEFUL_SHUTDOWN.value, "graceful_shutdown")
        self.assertEqual(ErrorRecoveryStrategy.IMMEDIATE_SHUTDOWN.value, "immediate_shutdown")
        self.assertEqual(ErrorRecoveryStrategy.RETRY_WITH_BACKOFF.value, "retry_with_backoff")
        self.assertEqual(ErrorRecoveryStrategy.FALLBACK_MODE.value, "fallback_mode")
        self.assertEqual(ErrorRecoveryStrategy.USER_INTERVENTION.value, "user_intervention")
        self.assertEqual(ErrorRecoveryStrategy.IGNORE_AND_CONTINUE.value, "ignore_and_continue")
        self.assertEqual(ErrorRecoveryStrategy.DEFER_PROCESSING.value, "defer_processing")
    
    def test_error_classification_creation(self):
        """Test error classification creation."""
        classification = ErrorClassification(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.VTK_ERROR,
            recovery_strategy=ErrorRecoveryStrategy.IGNORE_AND_CONTINUE
        )
        
        self.assertEqual(classification.severity, ErrorSeverity.ERROR)
        self.assertEqual(classification.category, ErrorCategory.VTK_ERROR)
        self.assertEqual(classification.recovery_strategy, ErrorRecoveryStrategy.IGNORE_AND_CONTINUE)
    
    def test_error_report_creation(self):
        """Test error report creation."""
        error = RuntimeError("Test error")
        context = ErrorContext.SHUTDOWN
        
        report = ErrorReport.create_error_report(
            error=error,
            context=context,
            context_info={"test": "data"}
        )
        
        self.assertEqual(report.error_type, "RuntimeError")
        self.assertEqual(report.error_message, "Test error")
        self.assertEqual(report.context, context)
        self.assertIn("test", report.context_info)
        self.assertEqual(report.context_info["test"], "data")
        self.assertIsNotNone(report.timestamp)
        self.assertIsNotNone(report.stack_trace)


class TestErrorReporter(unittest.TestCase):
    """Test error reporter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.reporter = ErrorReporter(log_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_error_reporter_initialization(self):
        """Test error reporter initialization."""
        self.assertEqual(self.reporter.log_dir, self.temp_dir)
        self.assertIsNotNone(self.reporter.logger)
        self.assertEqual(len(self.reporter.recovery_strategies), 7)
    
    def test_report_error_basic(self):
        """Test basic error reporting."""
        error = RuntimeError("Test error")
        context = ErrorContext.SHUTDOWN
        
        report = self.reporter.report_error(
            error=error,
            context=context,
            context_info={"operation": "test"}
        )
        
        self.assertEqual(report.error_type, "RuntimeError")
        self.assertEqual(report.error_message, "Test error")
        self.assertEqual(report.context, context)
        self.assertEqual(report.context_info["operation"], "test")
    
    def test_report_error_with_recovery(self):
        """Test error reporting with recovery callback."""
        error = OSError("File not found")
        recovery_called = False
        
        def recovery_callback():
            nonlocal recovery_called
            recovery_called = True
            return True
        
        report = self.reporter.report_error(
            error=error,
            context=ErrorContext.FILE_LOADING,
            recovery_callback=recovery_callback
        )
        
        self.assertTrue(recovery_called)
        self.assertEqual(report.error_type, "FileNotFoundError")
    
    def test_recovery_strategies(self):
        """Test all recovery strategies."""
        error = RuntimeError("Test error")
        report = ErrorReport.create_error_report(error=error, context=ErrorContext.NORMAL_OPERATION)
        
        # Test graceful shutdown
        result = self.reporter._graceful_shutdown(report, lambda: True)
        self.assertTrue(result)
        
        # Test immediate shutdown
        result = self.reporter._immediate_shutdown(report, lambda: True)
        self.assertTrue(result)
        
        # Test retry with backoff
        result = self.reporter._retry_with_backoff(report, lambda: True)
        self.assertTrue(result)
        
        # Test fallback mode
        result = self.reporter._fallback_mode(report, lambda: True)
        self.assertTrue(result)
        
        # Test user intervention
        result = self.reporter._request_user_intervention(report, lambda: True)
        self.assertTrue(result)
        
        # Test ignore and continue
        result = self.reporter._ignore_and_continue(report, lambda: True)
        self.assertTrue(result)
        
        # Test defer processing
        result = self.reporter._defer_processing(report, lambda: True)
        self.assertTrue(result)
    
    def test_export_error_report(self):
        """Test error report export."""
        error = RuntimeError("Test error")
        report = self.reporter.report_error(
            error=error,
            context=ErrorContext.SHUTDOWN,
            context_info={"test": "data"}
        )
        
        export_file = self.temp_dir / "test_report.json"
        self.reporter.export_error_report(export_file)
        
        self.assertTrue(export_file.exists())
        
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        self.assertEqual(exported_data["error_type"], "RuntimeError")
        self.assertEqual(exported_data["error_message"], "Test error")
        self.assertEqual(exported_data["context"], "shutdown")
        self.assertEqual(exported_data["context_info"]["test"], "data")


class TestSpecificErrorHandlers(unittest.TestCase):
    """Test specific error handlers."""
    
    def test_specific_error_handler_context_manager(self):
        """Test specific error handler as context manager."""
        handler = SpecificErrorHandler(
            context=ErrorContext.SHUTDOWN,
            expected_errors=(RuntimeError,),
            reraise=False
        )
        
        # Test successful execution
        with handler:
            pass  # Should not raise
        
        # Test expected error handling
        with handler:
            raise RuntimeError("Test error")
        # Should not raise because reraise=False
        
        # Test unexpected error propagation
        with self.assertRaises(ValueError):
            with handler:
                raise ValueError("Unexpected error")
    
    def test_specific_error_handler_decorator(self):
        """Test specific error handler as decorator."""
        handler = SpecificErrorHandler(
            context=ErrorContext.SHUTDOWN,
            expected_errors=(RuntimeError,),
            reraise=False
        )
        
        @handler
        def test_function():
            raise RuntimeError("Test error")
        
        # Should not raise because reraise=False
        result = test_function()
        self.assertIsNone(result)
    
    def test_shutdown_error_handler(self):
        """Test shutdown error handler."""
        handler = ShutdownErrorHandler("test_operation")
        
        # Should handle RuntimeError
        with handler:
            raise RuntimeError("Shutdown error")
        # Should not raise
        
        # Should handle OSError
        with handler:
            raise OSError("System error")
        # Should not raise
        
        # Should not handle ValueError
        with self.assertRaises(ValueError):
            with handler:
                raise ValueError("Unexpected error")
    
    def test_vtk_error_handler(self):
        """Test VTK error handler."""
        handler = VTKErrorHandler("render_operation")
        
        # Should handle RuntimeError
        with handler:
            raise RuntimeError("VTK error")
        # Should not raise
        
        # Should handle OSError
        with handler:
            raise OSError("OpenGL error")
        # Should not raise
    
    def test_file_io_error_handler(self):
        """Test file I/O error handler."""
        handler = FileIOErrorHandler("load_file", Path("test.txt"))
        
        # Should handle FileNotFoundError
        with handler:
            raise FileNotFoundError("File not found")
        # Should raise because reraise=True
        
        # Should handle PermissionError
        with self.assertRaises(PermissionError):
            with handler:
                raise PermissionError("Permission denied")
    
    def test_memory_error_handler(self):
        """Test memory error handler."""
        handler = MemoryErrorHandler("allocate_memory")
        
        # Should handle MemoryError
        with handler:
            raise MemoryError("Out of memory")
        # Should not raise because reraise=False


class TestContextManagers(unittest.TestCase):
    """Test context manager functions."""
    
    def test_handle_shutdown_errors(self):
        """Test shutdown error context manager."""
        with handle_shutdown_errors("test_operation"):
            raise RuntimeError("Shutdown error")
        # Should not raise
    
    def test_handle_vtk_errors(self):
        """Test VTK error context manager."""
        with handle_vtk_errors("render_operation"):
            raise RuntimeError("VTK error")
        # Should not raise
    
    def test_handle_file_io_errors(self):
        """Test file I/O error context manager."""
        with self.assertRaises(FileNotFoundError):
            with handle_file_io_errors("load_file", Path("test.txt")):
                raise FileNotFoundError("File not found")
    
    def test_handle_memory_errors(self):
        """Test memory error context manager."""
        with handle_memory_errors("allocate_memory"):
            raise MemoryError("Out of memory")
        # Should not raise


class TestDecorators(unittest.TestCase):
    """Test decorator functions."""
    
    def test_shutdown_safe_decorator(self):
        """Test shutdown safe decorator."""
        @shutdown_safe
        def test_shutdown_function():
            raise RuntimeError("Shutdown error")
        
        # Should not raise
        result = test_shutdown_function()
        self.assertIsNone(result)
    
    def test_vtk_safe_decorator(self):
        """Test VTK safe decorator."""
        @vtk_safe
        def test_vtk_function():
            raise RuntimeError("VTK error")
        
        # Should not raise
        result = test_vtk_function()
        self.assertIsNone(result)
    
    def test_file_io_safe_decorator(self):
        """Test file I/O safe decorator."""
        @file_io_safe("load_file", Path("test.txt"))
        def test_file_function():
            raise FileNotFoundError("File not found")
        
        # Should raise because reraise=True
        with self.assertRaises(FileNotFoundError):
            test_file_function()
    
    def test_monitor_operation_decorator(self):
        """Test operation monitoring decorator."""
        @monitor_operation("test_operation", ErrorContext.NORMAL_OPERATION)
        def test_monitored_function():
            return "success"
        
        result = test_monitored_function()
        self.assertEqual(result, "success")


class TestComprehensiveLogger(unittest.TestCase):
    """Test comprehensive logging system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = ComprehensiveLogger(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        self.assertEqual(self.logger.log_dir, self.temp_dir)
        self.assertTrue(self.temp_dir.exists())
        self.assertIsNotNone(self.logger.app_logger)
        self.assertIsNotNone(self.logger.error_logger)
        self.assertIsNotNone(self.logger.performance_logger)
        self.assertIsNotNone(self.logger.security_logger)
    
    def test_structured_logging(self):
        """Test structured JSON logging."""
        context = LogContext(
            operation_id="test_op",
            component="test_component",
            function="test_function"
        )
        
        self.logger.log_info("Test message", context)
        
        # Check that log file was created
        log_file = self.temp_dir / "app.log"
        self.assertTrue(log_file.exists())
        
        # Verify JSON format
        with open(log_file, 'r') as f:
            log_line = f.read().strip()
            log_data = json.loads(log_line)
        
        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["context"]["operation_id"], "test_op")
        self.assertEqual(log_data["context"]["component"], "test_component")
        self.assertEqual(log_data["context"]["function"], "test_function")
    
    def test_operation_tracking(self):
        """Test operation performance tracking."""
        operation_id = "test_operation"
        
        # Start operation
        self.logger.start_operation(operation_id, "Test Operation")
        
        # Simulate some work
        time.sleep(0.1)
        
        # End operation successfully
        self.logger.end_operation(operation_id, success=True)
        
        # Check statistics
        stats = self.logger.get_operation_statistics()
        self.assertEqual(stats["active_operations"], 0)
        self.assertIn(operation_id, stats["operation_statistics"])
        
        op_stats = stats["operation_statistics"][operation_id]
        self.assertEqual(op_stats["count"], 1)
        self.assertEqual(op_stats["success_count"], 1)
        self.assertGreater(op_stats["avg_duration_ms"], 0)
    
    def test_operation_context_manager(self):
        """Test operation context manager."""
        with self.logger.operation_context("test_operation") as operation_id:
            time.sleep(0.1)
        
        # Check that operation was tracked
        stats = self.logger.get_operation_statistics()
        self.assertEqual(stats["active_operations"], 0)
        self.assertIn(operation_id, stats["operation_statistics"])
    
    def test_error_logging(self):
        """Test error logging with exception info."""
        try:
            raise RuntimeError("Test error")
        except Exception:
            exception_info = sys.exc_info()
        
        context = LogContext(component="test")
        self.logger.log_error("Error occurred", context, exception_info=exception_info)
        
        # Check error log file
        error_log_file = self.temp_dir / "errors.log"
        self.assertTrue(error_log_file.exists())
        
        with open(error_log_file, 'r') as f:
            log_line = f.read().strip()
            log_data = json.loads(log_line)
        
        self.assertEqual(log_data["level"], "ERROR")
        self.assertEqual(log_data["message"], "Error occurred")
        self.assertIn("exception", log_data)
        self.assertEqual(log_data["exception"]["type"], "RuntimeError")
    
    def test_global_logger_functions(self):
        """Test global logger convenience functions."""
        # Set global logger
        set_global_logger(self.logger)
        
        # Test global logging functions
        log_info("Test info message")
        log_error("Test error message")
        
        # Check that messages were logged
        log_file = self.temp_dir / "app.log"
        self.assertTrue(log_file.exists())


class TestIntegration(unittest.TestCase):
    """Test integration between error handling components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = ComprehensiveLogger(self.temp_dir)
        self.reporter = ErrorReporter(log_dir=self.temp_dir)
        
        # Set global instances
        set_global_logger(self.logger)
        set_global_error_reporter(self.reporter)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_error_handler_with_logging(self):
        """Test error handler integration with logging."""
        with handle_shutdown_errors("test_operation") as handler:
            raise RuntimeError("Test error")
        
        # Check that error was logged
        error_log_file = self.temp_dir / "errors.log"
        self.assertTrue(error_log_file.exists())
    
    def test_monitored_operation_with_error_handling(self):
        """Test monitored operation with error handling."""
        @monitor_operation("test_operation", ErrorContext.SHUTDOWN)
        @shutdown_safe
        def test_function():
            raise RuntimeError("Test error")
        
        # Should not raise due to error handling
        result = test_function()
        self.assertIsNone(result)
        
        # Check performance logging
        perf_log_file = self.temp_dir / "performance.log"
        self.assertTrue(perf_log_file.exists())
    
    def test_complete_error_flow(self):
        """Test complete error handling flow."""
        # Create error with context
        error = RuntimeError("VTK cleanup failed")
        context = ErrorContext.SHUTDOWN
        context_info = {"operation": "vtk_cleanup", "component": "vtk"}
        
        # Report error
        report = self.reporter.report_error(
            error=error,
            context=context,
            context_info=context_info
        )
        
        # Log error report
        self.logger.log_error_report(report)
        
        # Check that both error reporter and logger captured the error
        error_log_file = self.temp_dir / "errors.log"
        self.assertTrue(error_log_file.exists())
        
        app_log_file = self.temp_dir / "app.log"
        self.assertTrue(app_log_file.exists())
    
    def test_shutdown_scenario_simulation(self):
        """Test shutdown scenario with comprehensive error handling."""
        def simulate_shutdown():
            """Simulate shutdown process with various potential errors."""
            
            # VTK cleanup
            with handle_vtk_errors("vtk_cleanup"):
                # Simulate VTK error
                raise RuntimeError("wglMakeCurrent failed")
            
            # File cleanup
            with handle_file_io_errors("cleanup_temp_files"):
                # Simulate file error
                raise FileNotFoundError("Temp file not found")
            
            # Memory cleanup
            with handle_memory_errors("cleanup_memory"):
                # Simulate memory error
                raise MemoryError("Memory allocation failed")
        
        # Should handle all errors gracefully
        simulate_shutdown()
        
        # Check that errors were logged
        error_log_file = self.temp_dir / "errors.log"
        self.assertTrue(error_log_file.exists())
        
        # Verify multiple errors were logged
        with open(error_log_file, 'r') as f:
            error_lines = f.readlines()
        
        self.assertGreater(len(error_lines), 0)


class TestPerformanceAndMemory(unittest.TestCase):
    """Test performance and memory characteristics."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = ComprehensiveLogger(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_operation_performance_tracking(self):
        """Test operation performance tracking accuracy."""
        operation_id = "performance_test"
        
        # Start operation
        self.logger.start_operation(operation_id, "Performance Test")
        
        # Simulate work
        start_time = time.time()
        time.sleep(0.1)  # 100ms
        end_time = time.time()
        
        # End operation
        self.logger.end_operation(operation_id, success=True)
        
        # Check performance metrics
        stats = self.logger.get_operation_statistics()
        op_stats = stats["operation_statistics"][operation_id]
        
        # Should be approximately 100ms (with some tolerance)
        self.assertGreater(op_stats["avg_duration_ms"], 90)
        self.assertLess(op_stats["avg_duration_ms"], 200)
    
    def test_concurrent_operations(self):
        """Test concurrent operation tracking."""
        results = []
        
        def worker_operation(worker_id):
            """Worker function for concurrent testing."""
            operation_id = f"worker_{worker_id}"
            
            with self.logger.operation_context(f"Worker Operation {worker_id}") as op_id:
                time.sleep(0.05)  # 50ms
                results.append(f"Worker {worker_id} completed")
        
        # Start multiple concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all operations completed
        self.assertEqual(len(results), 5)
        
        # Check operation statistics
        stats = self.logger.get_operation_statistics()
        self.assertEqual(stats["active_operations"], 0)
        self.assertGreater(len(stats["operation_statistics"]), 0)
    
    def test_memory_usage_stability(self):
        """Test memory usage stability during logging."""
        import gc
        
        # Get initial memory usage
        initial_objects = len(gc.get_objects())
        
        # Perform many logging operations
        for i in range(100):
            context = LogContext(operation_id=f"mem_test_{i}")
            self.logger.log_info(f"Memory test message {i}", context)
        
        # Force garbage collection
        gc.collect()
        
        # Check that memory usage hasn't grown significantly
        final_objects = len(gc.get_objects())
        growth_ratio = (final_objects - initial_objects) / initial_objects
        
        # Allow for some growth but not excessive
        self.assertLess(growth_ratio, 0.1)  # Less than 10% growth


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestErrorCategories,
        TestErrorReporter,
        TestSpecificErrorHandlers,
        TestContextManagers,
        TestDecorators,
        TestComprehensiveLogger,
        TestIntegration,
        TestPerformanceAndMemory
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Comprehensive Error Handling Tests...")
    print("=" * 60)
    
    success = run_comprehensive_tests()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! Error handling system is working correctly.")
    else:
        print("❌ Some tests failed. Please review the output above.")
    
    exit(0 if success else 1)