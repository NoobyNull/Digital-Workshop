# Candy-Cadence Testing Best Practices Guide

## Introduction

This guide provides essential best practices for writing, maintaining, and running tests within the Candy-Cadence project. Following these practices ensures reliable, maintainable, and effective testing.

## Table of Contents

1. [Test Writing Principles](#test-writing-principles)
2. [Test Organization](#test-organization)
3. [Unit Testing Best Practices](#unit-testing-best-practices)
4. [Integration Testing Guidelines](#integration-testing-guidelines)
5. [Performance Testing Standards](#performance-testing-standards)
6. [Memory Leak Testing Protocol](#memory-leak-testing-protocol)
7. [GUI Testing Best Practices](#gui-testing-best-practices)
8. [Test Data Management](#test-data-management)
9. [Quality Assurance Integration](#quality-assurance-integration)
10. [Continuous Testing Guidelines](#continuous-testing-guidelines)
11. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
12. [Review and Maintenance](#review-and-maintenance)

## Test Writing Principles

### 1. The Test Pyramid

Follow the testing pyramid principle:

```
                    /\
                   /  \
                  / E2E \
                 /______\
                /        \
               /  Integration  \
              /________________\
             /                  \
            /    Unit Tests      \
           /______________________\
```

- **70% Unit Tests**: Fast, isolated, focused
- **20% Integration Tests**: Test component interactions
- **10% End-to-End Tests**: Test complete user workflows

### 2. Test First Principles

1. **Write Tests Before Code**: Follow TDD when possible
2. **Tests as Documentation**: Tests should explain behavior
3. **Fail First**: Ensure tests can detect failures
4. **Keep Tests Simple**: Easy to understand and maintain

### 3. Good Test Characteristics

- **F.I.R.S.T Principles**:
  - **Fast**: Tests should run quickly
  - **Independent**: No dependencies between tests
  - **Repeatable**: Consistent results every time
  - **Self-validating**: Clear pass/fail results
  - **Timely**: Written close to the code they test

## Test Organization

### Directory Structure

```
tests/
├── unit_tests/                   # Unit tests
│   ├── parsers/                  # Parser-specific tests
│   ├── services/                 # Service layer tests
│   ├── core/                     # Core functionality tests
│   └── utils/                    # Utility function tests
├── integration_tests/            # Integration tests
│   ├── workflows/                # Complete workflow tests
│   └── api/                      # API integration tests
├── performance_tests/            # Performance benchmarks
├── memory_leak_tests.py          # Memory leak detection
├── gui_tests/                    # UI component tests
├── e2e_tests/                    # End-to-end scenarios
└── fixtures/                     # Shared test fixtures
```

### Naming Conventions

- **Test Files**: `test_<module_or_feature>.py`
- **Test Classes**: `Test<ClassName>`
- **Test Functions**: `test_<behavior_under_test>_<scenario>`
- **Fixtures**: `fixture_<purpose>`

```python
# Good naming examples
def test_stl_parser_parse_valid_file():
    """Test STL parser with valid file."""

def test_model_service_save_with_invalid_path():
    """Test model service error handling with invalid path."""

class TestSTLParser:
    """Tests for STL parser functionality."""
```

## Unit Testing Best Practices

### 1. Test Scope

Unit tests should test one thing at a time:

```python
# Good: Single behavior
def test_parser_extracts_vertices_correctly():
    parser = STLParser()
    model = parser.parse_file("cube.stl")
    assert len(model.vertices) == 8

# Bad: Testing multiple things
def test_parser_parses_and_validates_file():
    # This tests parsing AND validation - split these up
    pass
```

### 2. Test Setup and Teardown

Use fixtures for common setup:

```python
import pytest

@pytest.fixture
def stl_parser():
    """Provide STL parser instance for tests."""
    return STLParser()

@pytest.fixture
def sample_stl_file(tmp_path):
    """Create sample STL file for testing."""
    file_path = tmp_path / "test_cube.stl"
    create_sample_stl_file(file_path)
    return file_path

def test_parser_with_fixtures(stl_parser, sample_stl_file):
    """Test using fixtures for setup."""
    model = stl_parser.parse_file(sample_stl_file)
    assert model is not None
```

### 3. Mocking and Stubbing

Mock external dependencies:

```python
from unittest.mock import Mock, patch

def test_parser_with_file_operations():
    """Test parser with mocked file operations."""
    mock_file = Mock()
    mock_file.read.return_value = "solid cube\nendsolid cube"
    
    parser = STLParser()
    with patch('builtins.open', return_value=mock_file):
        model = parser.parse_file("test.stl")
        assert model is not None
```

### 4. Edge Case Testing

Test boundary conditions:

```python
def test_parser_handles_empty_file():
    """Test parser behavior with empty file."""
    parser = STLParser()
    with pytest.raises(ParserError):
        parser.parse_file("empty.stl")

def test_parser_handles_large_file():
    """Test parser with large file."""
    parser = STLParser()
    large_file = create_large_test_file(1000)  # 1000 triangles
    model = parser.parse_file(large_file)
    assert len(model.triangles) == 1000
```

## Integration Testing Guidelines

### 1. Component Interaction Testing

Test how components work together:

```python
def test_model_loading_pipeline():
    """Test complete model loading workflow."""
    # Setup
    file_detector = FormatDetector()
    parser = STLParser()
    cache = ModelCache()
    
    # Execute workflow
    detected_format = file_detector.detect("test.stl")
    assert detected_format == Format.STL
    
    model = parser.parse_file("test.stl")
    cache.store("test.stl", model)
    
    # Verify
    cached_model = cache.get("test.stl")
    assert cached_model == model
```

### 2. Database Integration Testing

Use test databases for integration tests:

```python
@pytest.fixture
def test_database():
    """Setup test database."""
    db = create_test_database()
    yield db
    db.cleanup()

def test_model_repository_save_and_retrieve(test_database):
    """Test database operations."""
    repo = ModelRepository(test_database)
    
    model_data = {"name": "test", "path": "/test/model.stl"}
    saved_id = repo.save(model_data)
    
    retrieved = repo.get_by_id(saved_id)
    assert retrieved["name"] == "test"
```

### 3. External Service Testing

Test integration with external services:

```python
@patch('src.services.cloud_storage.upload_file')
def test_cloud_backup_integration(mock_upload):
    """Test cloud backup service integration."""
    mock_upload.return_value = {"status": "success"}
    
    backup_service = CloudBackupService()
    result = backup_service.backup_model("test.stl")
    
    assert result.success
    mock_upload.assert_called_once_with("test.stl")
```

## Performance Testing Standards

### 1. Performance Test Structure

```python
import time
import pytest

class TestPerformance:
    """Performance test suite."""
    
    @pytest.mark.performance
    def test_stl_loading_performance(self):
        """Test STL loading meets performance requirements."""
        start_time = time.perf_counter()
        
        parser = STLParser()
        model = parser.parse_file("75mb_test_file.stl")
        
        end_time = time.perf_counter()
        load_time = end_time - start_time
        
        # Performance assertion
        assert load_time < 5.0, f"Load time {load_time}s exceeds 5s threshold"
        
        # Store metrics for trend analysis
        pytest.performance_results["stl_loading"] = {
            "time": load_time,
            "file_size_mb": 75,
            "timestamp": datetime.now().isoformat()
        }
```

### 2. Benchmarking Framework

Use the performance regression framework:

```python
from tests.test_performance_regression_framework import PerformanceRegressionDetector

def test_parsing_benchmark():
    """Benchmark parsing performance with regression detection."""
    detector = PerformanceRegressionDetector()
    
    # Measure performance
    start_time = time.perf_counter()
    result = parse_test_file()
    end_time = time.perf_counter()
    
    execution_time = end_time - start_time
    
    # Check for regressions
    has_regression, regression_amount = detector.check_regression(
        "stl_parsing", execution_time
    )
    
    assert not has_regression, f"Performance regression detected: {regression_amount}s"
    
    # Save baseline for future comparisons
    detector.save_baseline("stl_parsing", execution_time)
```

### 3. Performance Test Data

Use appropriate test data sizes:

- **Small Files**: < 10MB for unit testing
- **Medium Files**: 10-100MB for integration testing
- **Large Files**: 100-500MB for performance testing
- **Stress Files**: > 500MB for stress testing

## Memory Leak Testing Protocol

### 1. Memory Test Structure

Follow the standard memory leak testing pattern:

```python
from tests.memory_leak_tests import MemoryLeakDetector

def test_parser_memory_efficiency():
    """Test parser for memory leaks."""
    detector = MemoryLeakDetector()
    
    # Run memory leak test
    result = detector.test_gpu_parser_memory_leaks()
    
    # Validate results
    assert not result.leak_detected, f"Memory leak detected: {result.recommendations}"
    assert result.leak_confidence > 0.8, "Low confidence in memory test"
    
    # Log results
    print(f"Memory test completed: {result.average_delta:.2f}MB average growth")
```

### 2. Memory Test Best Practices

- **Run 10-20 iterations minimum**
- **Force garbage collection between iterations**
- **Monitor both CPU and GPU memory**
- **Test realistic usage patterns**
- **Document memory usage patterns**

### 3. Memory Test Scenarios

Test these common scenarios:

```python
def test_memory_cleanup_after_parsing():
    """Test memory cleanup after parsing operations."""
    detector = MemoryLeakDetector()
    
    # Test repeated parsing and cleanup
    result = detector._run_memory_leak_test(
        "Parse and Cleanup",
        lambda i: parse_and_cleanup_file(f"test_file_{i}.stl"),
        iterations=15
    )
    
    assert result.average_delta < 1.0  # Less than 1MB growth
```

## GUI Testing Best Practices

### 1. Qt Testing Setup

```python
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
```

### 2. GUI Test Patterns

```python
def test_model_library_file_loading(qapp):
    """Test file loading in model library widget."""
    # Create widget
    widget = ModelLibraryWidget()
    widget.show()
    
    # Simulate file selection
    file_path = "test_files/cube.stl"
    QTest.qWait(100)  # Allow widget to render
    
    # Test file loading
    widget.load_model_file(file_path)
    QTest.qWait(100)  # Wait for loading
    
    # Verify results
    assert widget.get_loaded_model() is not None
    assert widget.get_model_triangle_count() == 12
```

### 3. GUI Interaction Testing

```python
def test_viewer_zoom_functionality():
    """Test 3D viewer zoom functionality."""
    viewer = Viewer3DWidget()
    viewer.load_model("test_cube.stl")
    
    initial_scale = viewer.get_camera_scale()
    
    # Test zoom in
    viewer.zoom_in()
    QTest.qWait(50)
    zoomed_scale = viewer.get_camera_scale()
    
    assert zoomed_scale > initial_scale, "Zoom in should increase scale"
    
    # Test zoom out
    viewer.zoom_out()
    QTest.qWait(50)
    final_scale = viewer.get_camera_scale()
    
    assert final_scale < zoomed_scale, "Zoom out should decrease scale"
```

## Test Data Management

### 1. Test Data Organization

```
tests/test_data/
├── small_files/          # Files < 10MB
│   ├── cube.stl
│   └── simple.obj
├── medium_files/         # Files 10-100MB
│   └── model_50mb.stl
├── large_files/          # Files 100-500MB
│   └── complex_model.stl
└── edge_cases/           # Special test cases
    ├── empty_file.stl
    ├── corrupted_file.stl
    └── binary_file.stl
```

### 2. Test Data Creation

Generate test data programmatically:

```python
def create_test_stl_file(file_path: Path, triangle_count: int = 12):
    """Create test STL file with specified number of triangles."""
    with open(file_path, 'w') as f:
        f.write("solid test_cube\n")
        
        # Generate triangles
        for i in range(triangle_count):
            # Write triangle vertices
            f.write(f"  facet normal 0 0 0\n")
            f.write(f"    outer loop\n")
            f.write(f"      vertex 0 0 0\n")
            f.write(f"      vertex 1 0 0\n")
            f.write(f"      vertex 0 1 0\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        
        f.write("endsolid test_cube\n")

# Use in tests
@pytest.fixture
def large_test_file(tmp_path):
    """Create large test file for performance testing."""
    file_path = tmp_path / "large_model.stl"
    create_test_stl_file(file_path, triangle_count=100000)
    return file_path
```

### 3. Test Data Cleanup

```python
@pytest.fixture
def temp_test_data(tmp_path):
    """Provide temporary test data with cleanup."""
    # Create test files
    files = create_test_data_files(tmp_path)
    
    yield files
    
    # Cleanup after test
    for file_path in files:
        file_path.unlink(missing_ok=True)
```

## Quality Assurance Integration

### 1. Quality Gate Integration

```python
import pytest
from tests.quality_assurance_framework import QualityAssuranceEngine

@pytest.fixture
def qa_engine():
    """Provide QA engine for tests."""
    return QualityAssuranceEngine()

def test_code_quality_requirements(qa_engine):
    """Test that code meets quality requirements."""
    report = qa_engine.run_comprehensive_quality_assessment()
    
    # Check quality gates
    gates_passed, failures = qa_engine.check_quality_gates(report)
    
    if not gates_passed:
        pytest.fail(f"Quality gates failed: {failures}")
    
    # Verify specific metrics
    assert report.test_coverage >= 80.0, "Test coverage below 80%"
    assert report.security_score >= 80.0, "Security score below 80%"
```

### 2. Test Coverage Monitoring

```python
def test_coverage_tracking():
    """Track test coverage for specific modules."""
    # This would integrate with coverage.py
    coverage_data = get_coverage_data()
    
    # Check coverage for critical modules
    critical_modules = ["parsers", "core", "services"]
    
    for module in critical_modules:
        module_coverage = coverage_data.get(module, 0)
        assert module_coverage >= 90.0, f"{module} coverage {module_coverage}% below 90%"
```

## Continuous Testing Guidelines

### 1. Test Scheduling

Configure test execution schedules:

```json
{
  "unit_tests": {
    "schedule": "on_push",
    "timeout_minutes": 30,
    "critical": true,
    "retry_count": 2
  },
  "performance_tests": {
    "schedule": "nightly",
    "timeout_minutes": 120,
    "critical": true,
    "retry_count": 0
  },
  "memory_tests": {
    "schedule": "weekly",
    "timeout_minutes": 60,
    "critical": false,
    "retry_count": 1
  }
}
```

### 2. Alert Configuration

Set up appropriate alerts:

```python
def setup_test_alerts():
    """Configure test failure alerts."""
    alert_config = {
        "critical_failures": {
            "immediate": True,
            "recipients": ["dev-team@company.com"]
        },
        "performance_regressions": {
            "immediate": True,
            "recipients": ["performance-team@company.com"]
        },
        "quality_gate_violations": {
            "immediate": True,
            "recipients": ["qa-team@company.com"]
        }
    }
    
    return alert_config
```

## Common Pitfalls to Avoid

### 1. Test Anti-Patterns

**Don't:**
```python
# Anti-pattern: Testing implementation details
def test_parser_internals():
    parser = STLParser()
    assert parser._buffer_size == 4096

# Anti-pattern: Flaky tests
def test_sometimes_passes():
    if random.random() > 0.5:
        assert True
    else:
        assert False

# Anti-pattern: Long test methods
def test_everything():
    # 200 lines testing multiple things
    pass
```

**Do:**
```python
# Good: Testing behavior
def test_parser_validates_file_format():
    parser = STLParser()
    with pytest.raises(ParserError):
        parser.parse_file("invalid.txt")

# Good: Deterministic tests
def test_file_validation():
    result = validate_file("valid.stl")
    assert result.is_valid

# Good: Focused tests
def test_parser_handles_missing_file():
    with pytest.raises(FileNotFoundError):
        parser.parse_file("nonexistent.stl")
```

### 2. Performance Test Pitfalls

**Avoid:**
- Testing on inconsistent hardware
- Not accounting for system load
- Using unrepresentative test data
- Ignoring warm-up periods

**Follow:**
- Use consistent test environments
- Account for JIT compilation warm-up
- Use realistic test data sizes
- Run multiple iterations and average

### 3. Memory Test Pitfalls

**Avoid:**
- Not forcing garbage collection
- Testing too few iterations
- Ignoring system memory pressure
- Not monitoring GPU memory

**Follow:**
- Force GC between measurements
- Run 10-20+ iterations minimum
- Test under various memory conditions
- Monitor both CPU and GPU memory

## Review and Maintenance

### 1. Code Review Checklist

- [ ] Tests follow naming conventions
- [ ] Tests are isolated and independent
- [ ] Edge cases are covered
- [ ] Performance tests have realistic data
- [ ] Memory tests run sufficient iterations
- [ ] GUI tests handle timing issues
- [ ] Tests are documented appropriately

### 2. Test Maintenance Schedule

**Weekly:**
- Review test execution reports
- Update test data as needed
- Check for flaky tests

**Monthly:**
- Analyze test coverage reports
- Review performance trends
- Update quality thresholds

**Quarterly:**
- Refactor test code
- Review testing strategy
- Update testing documentation

### 3. Quality Metrics Tracking

Monitor these key metrics:

```python
def calculate_test_quality_metrics():
    """Calculate test quality metrics."""
    return {
        "test_coverage": get_coverage_percentage(),
        "test_success_rate": get_success_rate(),
        "test_execution_time": get_avg_execution_time(),
        "performance_regression_count": get_regression_count(),
        "memory_leak_incidents": get_leak_incidents(),
        "quality_score": get_overall_quality_score()
    }
```

## Conclusion

Following these best practices ensures that the Candy-Cadence testing framework remains effective, maintainable, and valuable for the project. Regular review and updates to these practices help the framework evolve with project needs.

### Quick Reference

| Test Type | Execution Command | Duration | Coverage Target |
|-----------|------------------|----------|-----------------|
| Unit Tests | `pytest tests/unit_tests/` | < 5 min | 90%+ |
| Integration | `pytest tests/integration_tests/` | < 15 min | 80%+ |
| Performance | `python tests/test_performance_*.py` | < 30 min | N/A |
| Memory | `python tests/memory_leak_tests.py` | < 15 min | N/A |
| GUI | `pytest tests/gui_tests/` | < 10 min | 70%+ |
| E2E | `pytest tests/e2e_tests/` | < 30 min | N/A |

For questions or suggestions about these practices, please refer to the main testing documentation or contact the development team.