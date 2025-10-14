"""
Test script for the JSON logging system with rotation.

This script tests the logging functionality, verifies JSON format,
checks log rotation behavior, and performs memory leak testing.
"""

import gc
import json
import os
import psutil
import time
from pathlib import Path
import sys

# Set console encoding to UTF-8 to handle unicode characters
if sys.platform == "win32":
    import locale
    import codecs
    # Try to set console to UTF-8
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except:
        pass  # If it fails, continue with default encoding

# Add the src directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the logging module directly to avoid import issues with missing modules
import core.logging_config
from core.logging_config import setup_logging, get_logger, log_function_call


def test_json_format():
    """Test that log entries are properly formatted as JSON."""
    print("Testing JSON log format...")
    
    # Set up logging with a test directory
    test_log_dir = "test_logs"
    logger = setup_logging(log_level="DEBUG", log_dir=test_log_dir, enable_console=False)
    
    # Log messages at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        logger.exception("This is an exception message")
    
    # Close the logger to flush all logs
    for handler in logger.handlers:
        handler.close()
    
    # Check that log files were created
    log_dir = Path(test_log_dir)
    log_files = list(log_dir.glob("Log - *.txt"))
    
    if not log_files:
        print("ERROR: No log files were created")
        return False
    
    # Read and verify the log file content
    with open(log_files[0], 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                try:
                    log_entry = json.loads(line)
                    
                    # Verify required fields are present
                    required_fields = ["timestamp", "level", "logger", "function", "line", "message"]
                    for field in required_fields:
                        if field not in log_entry:
                            print(f"ERROR: Missing required field '{field}' in log entry")
                            return False
                    
                    print(f"[OK] Valid JSON log entry: {log_entry['level']} - {log_entry['message']}")
                    
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid JSON in log line: {line}")
                    return False
    
    # Clean up test logs
    for log_file in log_files:
        log_file.unlink()
    log_dir.rmdir()
    
    print("[OK] JSON format test passed")
    return True


def test_log_rotation():
    """Test that log rotation works correctly."""
    print("\nTesting log rotation...")
    
    # Set up logging with small file size to trigger rotation
    test_log_dir = "test_logs_rotation"
    logger = setup_logging(
        log_level="DEBUG",
        log_dir=test_log_dir,
        enable_console=False,
        max_bytes=500,  # Very small size to trigger rotation quickly
        backup_count=3
    )
    
    # Generate enough log messages to trigger rotation
    # Use a long message to ensure we hit the size limit quickly
    long_message = "x" * 200  # 200 character message
    for i in range(10):
        logger.info(f"This is test message number {i}: {long_message}")
        # Force flush after each message
        for handler in logger.handlers:
            handler.flush()
    
    # Close the logger to flush all logs
    for handler in logger.handlers:
        handler.close()
    
    # Check that multiple log files were created
    log_dir = Path(test_log_dir)
    log_files = list(log_dir.glob("Log - *.txt"))
    
    if len(log_files) < 2:
        print(f"ERROR: Expected at least 2 log files due to rotation, got {len(log_files)}")
        # Print debug info
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"  Log file: {log_file.name} ({size} bytes)")
        return False
    
    print(f"[OK] Log rotation created {len(log_files)} log files")
    
    # Verify backup count is respected
    if len(log_files) > 3:
        print(f"WARNING: More log files than expected backup count: {len(log_files)} > 3")
    
    # Clean up test logs
    for log_file in log_files:
        log_file.unlink()
    log_dir.rmdir()
    
    print("[OK] Log rotation test passed")
    return True


def test_memory_leaks():
    """Test for memory leaks during repeated logging operations."""
    print("\nTesting for memory leaks...")
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    print(f"Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB")
    
    # Set up logging
    test_log_dir = "test_logs_memory"
    logger = setup_logging(
        log_level="INFO", 
        log_dir=test_log_dir, 
        enable_console=False,
        max_bytes=1024*1024,  # 1MB
        backup_count=5
    )
    
    # Perform logging operations multiple times
    for iteration in range(20):
        # Log various messages
        logger.info(f"Memory test iteration {iteration}")
        logger.debug(f"Debug message for iteration {iteration}")
        logger.warning(f"Warning message for iteration {iteration}")
        
        # Log with extra data
        logger.info(
            f"Data message for iteration {iteration}",
            extra={"iteration": iteration, "data": "x" * 100}
        )
        
        # Force garbage collection
        if iteration % 5 == 0:
            gc.collect()
            
        # Check memory usage
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        print(f"Iteration {iteration}: Memory usage: {current_memory / 1024 / 1024:.2f} MB "
              f"(increase: {memory_increase / 1024 / 1024:.2f} MB)")
        
        # If memory increase is significant, there might be a leak
        if memory_increase > 50 * 1024 * 1024:  # 50MB threshold
            print(f"WARNING: Potential memory leak detected at iteration {iteration}")
    
    # Close the logger
    for handler in logger.handlers:
        handler.close()
    
    # Final memory check
    final_memory = process.memory_info().rss
    total_increase = final_memory - initial_memory
    
    print(f"Final memory usage: {final_memory / 1024 / 1024:.2f} MB")
    print(f"Total memory increase: {total_increase / 1024 / 1024:.2f} MB")
    
    # Clean up test logs
    log_dir = Path(test_log_dir)
    log_files = list(log_dir.glob("Log - *.txt"))
    for log_file in log_files:
        log_file.unlink()
    log_dir.rmdir()
    
    # Check if memory increase is acceptable
    if total_increase < 20 * 1024 * 1024:  # 20MB threshold
        print("[OK] Memory leak test passed - memory usage is stable")
        return True
    else:
        print(f"WARNING: Memory increased by {total_increase / 1024 / 1024:.2f} MB")
        return False


@log_function_call(get_logger("test"))
def test_function_logging(a, b):
    """Test function to verify the log_function_call decorator."""
    return a + b


def test_function_decorator():
    """Test the log_function_call decorator."""
    print("\nTesting function call logging decorator...")
    
    # Set up logging
    test_log_dir = "test_logs_decorator"
    logger = setup_logging(
        log_level="DEBUG", 
        log_dir=test_log_dir, 
        enable_console=False
    )
    
    # Call the decorated function
    result = test_function_logging(5, 10)
    print(f"Function result: {result}")
    
    # Close the logger
    for handler in logger.handlers:
        handler.close()
    
    # Check log file for function call entries
    log_dir = Path(test_log_dir)
    log_files = list(log_dir.glob("Log - *.txt"))
    
    if not log_files:
        print("ERROR: No log files were created for decorator test")
        return False
    
    # Read and verify the log file content
    function_calls = 0
    with open(log_files[0], 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    log_entry = json.loads(line)
                    # Check for both the original function field and custom_function field
                    function_name = log_entry.get("function") or log_entry.get("custom_function")
                    if function_name == "test_function_logging":
                        function_calls += 1
                        print(f"[OK] Found function call log: {log_entry['message']}")
                except json.JSONDecodeError:
                    pass
    
    # Clean up test logs
    for log_file in log_files:
        log_file.unlink()
    log_dir.rmdir()
    
    if function_calls >= 1:  # At least one log entry means the decorator is working
        print("[OK] Function decorator test passed")
        return True
    else:
        print(f"ERROR: Expected at least 1 function call log, got {function_calls}")
        return False


def main():
    """Run all logging tests."""
    print("Starting 3D-MM Logging System Tests\n")
    
    tests = [
        test_json_format,
        test_log_rotation,
        test_memory_leaks,
        test_function_decorator
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("[OK] All tests passed - logging system is working correctly")
        return True
    else:
        print("[FAIL] Some tests failed - logging system needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)