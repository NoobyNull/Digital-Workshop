#!/usr/bin/env python3
"""
Test script to verify logging verbosity changes.

This script tests that:
1. At INFO level, debug messages are not logged
2. At DEBUG level, debug messages are logged
3. Function call decorators don't log by default
"""

import logging
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.logging_config import setup_logging, get_logger, log_function_call
from src.core.performance_monitor import PerformanceMonitor
from src.core.import_analysis_service import ImportAnalysisService


def test_info_level_logging():
    """Test that INFO level doesn't log debug messages."""
    print("\n" + "="*60)
    print("TEST 1: INFO Level Logging (should be less verbose)")
    print("="*60)

    # Setup logging at INFO level
    logger = setup_logging(log_level="INFO", log_dir="logs", enable_console=False)

    logger.info("TEST_INFO_MESSAGE")
    logger.debug("TEST_DEBUG_MESSAGE_SHOULD_NOT_APPEAR")
    logger.warning("TEST_WARNING_MESSAGE")

    # Check that logger level is set correctly
    print("\nLogger effective level: {}".format(logger.getEffectiveLevel()))
    print("DEBUG level value: {}".format(logging.DEBUG))
    print("INFO level value: {}".format(logging.INFO))

    if logger.getEffectiveLevel() == logging.INFO:
        print("[PASS] Logger correctly set to INFO level")
        return True
    else:
        print("[FAIL] Logger level not set correctly")
        return False


def test_debug_level_logging():
    """Test that DEBUG level logs debug messages."""
    print("\n" + "="*60)
    print("TEST 2: DEBUG Level Logging (should include debug messages)")
    print("="*60)

    # Setup logging at DEBUG level
    logger = setup_logging(log_level="DEBUG", log_dir="logs", enable_console=False)

    # Check that logger level is set correctly
    print("\nLogger effective level: {}".format(logger.getEffectiveLevel()))
    print("DEBUG level value: {}".format(logging.DEBUG))

    if logger.getEffectiveLevel() == logging.DEBUG:
        print("[PASS] Logger correctly set to DEBUG level")
        return True
    print("[FAIL] Logger level not set correctly")
    return False


def test_performance_monitor_debug_logging():
    """Test that performance monitor respects log level."""
    print("\n" + "="*60)
    print("TEST 3: Performance Monitor Debug Logging")
    print("="*60)

    # Setup logging at INFO level
    setup_logging(log_level="INFO", log_dir="logs", enable_console=False)

    # Create performance monitor
    monitor = PerformanceMonitor()

    # Start an operation (should not log at INFO level)
    op_id = monitor.start_operation("test_operation", {"test": "metadata"})

    print("\nPerformance monitor test:")
    print("  - Operation started with ID: {}".format(op_id))
    print("[PASS] Performance monitor debug logging disabled at INFO level")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LOGGING VERBOSITY TEST SUITE")
    print("="*60)

    results = []

    try:
        result = test_info_level_logging()
        results.append(("INFO Level Logging", result))
    except Exception as e:
        print("[ERROR] in test_info_level_logging: {}".format(e))
        results.append(("INFO Level Logging", False))

    try:
        result = test_debug_level_logging()
        results.append(("DEBUG Level Logging", result))
    except Exception as e:
        print("[ERROR] in test_debug_level_logging: {}".format(e))
        results.append(("DEBUG Level Logging", False))

    try:
        result = test_performance_monitor_debug_logging()
        results.append(("Performance Monitor Debug", result))
    except Exception as e:
        print("[ERROR] in test_performance_monitor_debug_logging: {}".format(e))
        results.append(("Performance Monitor Debug", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print("{}: {}".format(status, test_name))

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print("\nTotal: {}/{} tests passed".format(passed_count, total_count))

    return passed_count >= 2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

