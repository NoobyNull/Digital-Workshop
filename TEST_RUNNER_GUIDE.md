# Master Test Runner Guide

## Overview

The Candy-Cadence project includes two master test runners that execute all tests in the test suite and provide comprehensive feedback.

---

## Test Runners

### 1. **run_all_tests.py** - Basic Master Test Runner

Simple, lightweight test runner with essential reporting.

**Features:**
- ✅ Runs all 25 test files
- ✅ Provides pass/fail/error/skip statistics
- ✅ Shows individual test failures and errors
- ✅ Calculates performance metrics
- ✅ Command-line options for control

**Usage:**
```bash
# Run all tests
python run_all_tests.py

# Verbose output
python run_all_tests.py --verbose

# Stop on first failure
python run_all_tests.py --failfast

# Combine options
python run_all_tests.py --verbose --failfast
```

**Output:**
```
================================================================================
CANDY-CADENCE MASTER TEST SUITE
================================================================================
Start Time: 2025-10-18 14:30:45
Total Tests: 25
================================================================================

✓ Loaded test_application
✓ Loaded test_database
...

================================================================================
TEST SUMMARY REPORT
================================================================================

Total Tests Run: 156
  ✓ Passed:  150 (96%)
  ✗ Failed:  3 (2%)
  ⚠ Errors:  2 (1%)
  ⊘ Skipped: 1 (1%)

Total Duration: 45.23 seconds
Average per Test: 0.290 seconds

================================================================================
✓ ALL TESTS PASSED!
================================================================================
```

---

### 2. **run_all_tests_detailed.py** - Enhanced Test Runner

Advanced test runner with detailed reporting and multiple output formats.

**Features:**
- ✅ Color-coded console output
- ✅ Detailed failure/error information
- ✅ JSON report generation
- ✅ HTML report generation
- ✅ Performance metrics
- ✅ CI/CD integration ready

**Usage:**
```bash
# Run all tests with detailed output
python run_all_tests_detailed.py

# Generate JSON report
python run_all_tests_detailed.py --json test_report.json

# Generate HTML report
python run_all_tests_detailed.py --html test_report.html

# Generate both reports
python run_all_tests_detailed.py --json report.json --html report.html
```

**Output:**
```
================================================================================
CANDY-CADENCE MASTER TEST SUITE
================================================================================
Start Time: 2025-10-18 14:30:45
Total Test Files: 25
================================================================================

✓ Loaded test_application
✓ Loaded test_database
...

Running 156 tests...

================================================================================
TEST SUMMARY
================================================================================

Total Tests: 156
  ✓ Passed:  150 (96%)
  ✗ Failed:  3 (2%)
  ⚠ Errors:  2 (1%)
  ⊘ Skipped: 1 (1%)

Duration: 45.23s (avg: 0.290s per test)

================================================================================
✓ ALL TESTS PASSED!
================================================================================

✓ JSON report saved to test_report.json
✓ HTML report saved to test_report.html
```

---

## Test Files Included

The master test runners execute the following 25 test files:

1. **test_application.py** - Application initialization and startup
2. **test_application_config.py** - Configuration management
3. **test_database.py** - Database operations
4. **test_database_performance_benchmark.py** - Database performance
5. **test_exception_handler.py** - Exception handling
6. **test_format_detector.py** - File format detection
7. **test_lighting_complete.py** - Lighting system (complete)
8. **test_lighting_final.py** - Lighting system (final)
9. **test_lighting_functionality.py** - Lighting functionality
10. **test_lighting_simple.py** - Lighting system (simple)
11. **test_logging.py** - Logging system
12. **test_meshlib_viewer.py** - Mesh library viewer
13. **test_metadata_editor.py** - Metadata editor
14. **test_model_library.py** - Model library
15. **test_model_library_ui.py** - Model library UI
16. **test_mtl_debug.py** - MTL file debugging
17. **test_obj_parser.py** - OBJ file parser
18. **test_packaging.py** - Application packaging
19. **test_performance_optimization.py** - Performance optimization
20. **test_search_engine.py** - Search functionality
21. **test_step_parser.py** - STEP file parser
22. **test_stl_parser.py** - STL file parser
23. **test_threemf_parser.py** - 3MF file parser
24. **test_viewer_3d.py** - 3D viewer
25. **test_viewer_widget.py** - Viewer widget

---

## Report Formats

### JSON Report

Structured data for CI/CD integration:

```json
{
  "timestamp": "2025-10-18T14:30:45.123456",
  "duration": 45.23,
  "total_tests": 156,
  "passed": 150,
  "failed": 3,
  "errors": 2,
  "skipped": 1,
  "success": true,
  "failures": [
    {
      "test": "test_database.TestDatabase.test_connection",
      "message": "Connection timeout after 30 seconds"
    }
  ],
  "errors": [
    {
      "test": "test_viewer_3d.TestViewer.test_render",
      "message": "ImportError: No module named 'PyQt3D'"
    }
  ],
  "skipped": [
    {
      "test": "test_packaging.TestPackaging.test_build",
      "reason": "Requires Windows environment"
    }
  ]
}
```

### HTML Report

Visual report with charts and statistics (opens in browser).

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python run_all_tests_detailed.py --json report.json
      - uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: report.json
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'tests'"

**Solution:** Run from project root directory:
```bash
cd /path/to/Candy-Cadence
python run_all_tests.py
```

### Issue: "No tests found"

**Solution:** Ensure test files exist in `tests/` directory:
```bash
ls tests/test_*.py
```

### Issue: "ImportError: No module named 'src'"

**Solution:** Ensure project root is in Python path (already handled by runners).

---

## Performance Tips

1. **Run specific tests** - Modify `test_files` list in runner
2. **Use --failfast** - Stop on first failure to save time
3. **Parallel execution** - Use pytest with `-n` flag:
   ```bash
   pytest tests/ -n auto
   ```

---

## Exit Codes

- **0** - All tests passed
- **1** - One or more tests failed

---

## Next Steps

1. **Run basic tests:** `python run_all_tests.py`
2. **Generate reports:** `python run_all_tests_detailed.py --json report.json --html report.html`
3. **Review failures:** Check JSON report or HTML report
4. **Fix issues:** Address failing tests
5. **Re-run:** Verify fixes with `python run_all_tests.py`

---

**Status**: ✅ **MASTER TEST RUNNERS READY**

