# Candy-Cadence Testing Framework Documentation

## Overview

This document provides comprehensive documentation for the Candy-Cadence testing and quality assurance framework. The framework ensures code quality, reliability, and maintainability through systematic testing approaches.

## Table of Contents

1. [Framework Architecture](#framework-architecture)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Configuration](#test-configuration)
5. [Performance Testing](#performance-testing)
6. [Quality Assurance](#quality-assurance)
7. [Continuous Testing](#continuous-testing)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)

## Framework Architecture

### Core Components

The testing framework consists of several interconnected components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Framework                        │
├─────────────────────────────────────────────────────────────┤
│  Unit Tests    │  Integration Tests  │  End-to-End Tests   │
├─────────────────────────────────────────────────────────────┤
│  Performance Tests      │  Memory Leak Tests               │
├─────────────────────────────────────────────────────────────┤
│  Quality Assurance      │  Continuous Monitoring           │
├─────────────────────────────────────────────────────────────┤
│  Test Coverage         │  Static Analysis                 │
└─────────────────────────────────────────────────────────────┘
```

### Test Structure

```
tests/
├── conftest.py                 # Pytest configuration
├── unit_tests/                 # Unit test modules
│   ├── test_parsers/          # Parser function tests
│   ├── test_services/         # Service layer tests
│   └── test_core/             # Core functionality tests
├── integration_tests/         # Integration test modules
├── performance_tests/         # Performance benchmarking
├── memory_leak_tests.py       # Memory leak detection
├── gui_tests/                 # UI component tests
├── e2e_tests/                 # End-to-end scenarios
├── quality_assurance_framework.py  # QA tools
├── performance_regression_framework.py  # Performance testing
├── continuous_testing_framework.py  # Continuous monitoring
└── sample_files/              # Test data and samples
```

## Test Categories

### 1. Unit Tests
- **Purpose**: Test individual functions and methods in isolation
- **Location**: `tests/unit_tests/`
- **Requirements**: 90%+ coverage for critical modules
- **Execution**: `pytest tests/unit_tests/ -v`

#### Parser Tests
```python
# Example parser test structure
def test_stl_parser_basic_parsing():
    """Test basic STL file parsing functionality."""
    parser = STLParser()
    model = parser.parse_file("test_cube.stl")
    
    assert model is not None
    assert len(model.vertices) == 8
    assert len(model.triangles) == 12
```

### 2. Integration Tests
- **Purpose**: Test component interactions and workflows
- **Location**: `tests/integration_tests/`
- **Requirements**: All major workflows must be tested
- **Execution**: `pytest tests/integration_tests/ -v`

#### Workflow Tests
```python
# Example integration test
def test_complete_loading_workflow():
    """Test complete model loading workflow."""
    # Test file detection → parsing → caching → rendering pipeline
    result = load_and_render_model("test_model.stl")
    
    assert result.success
    assert result.render_time < 5.0  # Performance requirement
    assert result.memory_usage < 500  # Memory requirement
```

### 3. Performance Tests
- **Purpose**: Validate performance requirements and detect regressions
- **Location**: `tests/test_performance_regression_framework.py`
- **Targets**:
  - Files < 100MB: < 5 seconds
  - Files 100-500MB: < 15 seconds  
  - Files > 500MB: < 30 seconds
- **Execution**: `python tests/test_performance_regression_framework.py`

#### Performance Benchmarks
```python
# Example performance test
def test_stl_loading_performance():
    """Test STL loading meets performance requirements."""
    file_size = 75  # MB
    start_time = time.perf_counter()
    
    model = load_stl_file("test_75mb.stl")
    end_time = time.perf_counter()
    
    load_time = end_time - start_time
    assert load_time < 5.0  # Performance target
```

### 4. Memory Leak Tests
- **Purpose**: Detect memory leaks during repeated operations
- **Location**: `tests/memory_leak_tests.py`
- **Requirements**: Run 10-20 iterations minimum
- **Tolerance**: < 1MB increase per iteration
- **Execution**: `python tests/memory_leak_tests.py`

#### Memory Monitoring
```python
# Example memory test
def test_memory_efficiency():
    """Test memory efficiency over multiple operations."""
    initial_memory = get_current_memory_mb()
    
    for i in range(15):  # Minimum iterations
        perform_operation()
        gc.collect()
    
    final_memory = get_current_memory_mb()
    memory_growth = final_memory - initial_memory
    
    assert memory_growth < 1.0  # 1MB tolerance
```

### 5. GUI Tests
- **Purpose**: Test user interface components and interactions
- **Location**: `tests/gui_tests/`
- **Framework**: PyQt/PySide testing utilities
- **Execution**: `pytest tests/gui_tests/ -v`

#### UI Component Tests
```python
# Example GUI test
def test_model_library_ui():
    """Test model library user interface."""
    app = QApplication([])
    
    widget = ModelLibraryWidget()
    assert widget.isVisible()
    
    # Test file loading
    widget.load_model("test_file.stl")
    assert widget.get_loaded_model() is not None
```

### 6. End-to-End Tests
- **Purpose**: Test complete user workflows
- **Location**: `tests/test_end_to_end_workflows_complete.py`
- **Requirements**: Simulate real user scenarios
- **Execution**: `pytest tests/test_end_to_end_workflows_complete.py -v`

## Running Tests

### Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit_tests/ -v
pytest tests/integration_tests/ -v
pytest tests/performance_tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run memory leak tests
python tests/memory_leak_tests.py

# Run performance tests
python tests/test_performance_regression_framework.py

# Run quality assurance
python tests/quality_assurance_framework.py

# Run continuous monitoring
python tests/continuous_testing_framework.py
```

### Test Configuration

#### Pytest Configuration (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    memory: Memory leak tests
    gui: GUI tests
    e2e: End-to-end tests
```

#### Environment Variables
```bash
# Test environment configuration
export PYTEST_TIMEOUT=300
export TEST_DATA_DIR=tests/test_data
export PERFORMANCE_TESTS=1
export MEMORY_TESTS=1
export COVERAGE_THRESHOLD=80
```

## Performance Testing

### Performance Targets

| File Size | Load Time Target | Memory Target |
|-----------|------------------|---------------|
| < 100MB   | < 5 seconds      | < 100MB       |
| 100-500MB | < 15 seconds     | < 500MB       |
| > 500MB   | < 30 seconds     | < 1GB         |

### Performance Regression Detection

The framework automatically detects performance regressions:

```python
# Automatic regression detection
def test_performance_regression():
    current_time = measure_operation()
    
    # Compare against baseline
    regression_detected = check_regression("operation_name", current_time)
    
    assert not regression_detected, "Performance regression detected!"
```

### Memory Performance

- **Memory Usage**: Monitored during all operations
- **Memory Leaks**: Detected through repeated operation testing
- **Garbage Collection**: Tested for proper cleanup

## Quality Assurance

### Quality Metrics

The framework calculates comprehensive quality scores:

- **Test Coverage**: 80% minimum, 90% target
- **Code Complexity**: < 10 cyclomatic complexity
- **Code Duplication**: < 5%
- **Performance Score**: Based on regression detection
- **Security Score**: Based on static analysis

### Quality Gates

Quality gates enforce minimum standards:

```python
# Quality gate check
def check_quality_gates():
    qa_engine = QualityAssuranceEngine()
    report = qa_engine.run_comprehensive_quality_assessment()
    
    gates_passed, failures = qa_engine.check_quality_gates(report)
    
    if not gates_passed:
        raise QualityGateError(f"Quality gates failed: {failures}")
```

### Static Code Analysis

- **Complexity Analysis**: Cyclomatic complexity measurement
- **Style Checking**: PEP 8 compliance
- **Security Scanning**: Vulnerability detection
- **Dependency Analysis**: License and security checks

## Continuous Testing

### Automated Scheduling

Tests run automatically based on configuration:

```json
{
  "unit_tests": {
    "schedule": "hourly",
    "timeout_minutes": 30,
    "critical": true,
    "quality_gates": {
      "test_coverage": 80.0,
      "failure_rate": 5.0
    }
  },
  "performance_tests": {
    "schedule": "daily",
    "timeout_minutes": 120,
    "critical": true,
    "quality_gates": {
      "regression_rate": 10.0,
      "memory_leaks": 1.0
    }
  }
}
```

### Monitoring and Alerts

- **Test Failures**: Immediate notifications for critical tests
- **Performance Regressions**: Alerts when performance degrades
- **Quality Gate Violations**: Notifications for quality issues
- **Email Notifications**: Configurable alert recipients

### Test Analytics

Track test trends and performance over time:

- **Success Rates**: Monitor test pass/fail rates
- **Execution Times**: Track performance trends
- **Regression Detection**: Identify performance degradation
- **Quality Trends**: Monitor overall code quality

## Troubleshooting

### Common Issues

#### 1. Memory Leak Detection Failures
```
Symptom: Memory usage continuously increases
Diagnosis: Check for circular references, unclosed resources
Solution: Review memory leak test output for specific components
```

#### 2. Performance Regression Detection
```
Symptom: Tests fail due to performance regression
Diagnosis: Compare current vs baseline execution times
Solution: Investigate recent code changes for performance impact
```

#### 3. Test Coverage Gaps
```
Symptom: Low test coverage percentage
Diagnosis: Identify untested code paths
Solution: Add unit tests for uncovered functions
```

#### 4. GUI Test Failures
```
Symptom: GUI tests fail intermittently
Diagnosis: Check for timing issues, widget state problems
Solution: Add waits, improve synchronization
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Enable debug logging
export PYTHONPATH=tests:$PYTHONPATH
python -m pytest tests/ -v -s --log-level=DEBUG
```

### Test Data Issues

- **Missing Test Files**: Ensure test data is properly created
- **Corrupted Data**: Regenerate test sample files
- **Permission Issues**: Check file access permissions

## Best Practices

### Writing Tests

1. **Test Organization**
   - Group related tests in classes
   - Use descriptive test names
   - Follow naming conventions: `test_<functionality>_<scenario>`

2. **Test Isolation**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Clean up resources after tests

3. **Assertions**
   - Use specific assertions (`assertEqual`, `assertIn`)
   - Provide meaningful failure messages
   - Test both positive and negative cases

4. **Performance Considerations**
   - Mock expensive operations
   - Use appropriate test data sizes
   - Set reasonable timeouts

### Test Maintenance

1. **Regular Updates**
   - Keep tests aligned with code changes
   - Update test data as needed
   - Review and refactor test code

2. **Quality Monitoring**
   - Monitor test coverage regularly
   - Track test execution times
   - Watch for flaky tests

3. **Documentation**
   - Document complex test scenarios
   - Keep README files updated
   - Document troubleshooting steps

### CI/CD Integration

1. **Pipeline Stages**
   ```yaml
   stages:
     - unit_tests
     - integration_tests
     - performance_tests
     - quality_assurance
     - deployment
   ```

2. **Quality Gates**
   - Block deployment on quality gate failures
   - Require minimum test coverage
   - Enforce performance targets

3. **Notifications**
   - Alert on test failures
   - Report quality metrics
   - Notify on regression detection

## API Reference

### Testing Framework Classes

#### MemoryLeakDetector
```python
class MemoryLeakDetector:
    def run_comprehensive_memory_tests(self) -> Dict[str, MemoryLeakResult]
    def test_gpu_parser_memory_leaks(self) -> MemoryLeakResult
    def test_file_chunker_memory_leaks(self) -> MemoryLeakResult
```

#### PerformanceRegressionDetector
```python
class PerformanceRegressionDetector:
    def check_regression(self, test_name: str, current_time: float) -> Tuple[bool, float]
    def save_baseline(self, test_name: str, execution_time: float)
```

#### QualityAssuranceEngine
```python
class QualityAssuranceEngine:
    def run_comprehensive_quality_assessment(self) -> CodeQualityReport
    def check_quality_gates(self, report: CodeQualityReport) -> Tuple[bool, List[str]]
```

#### ContinuousTestScheduler
```python
class ContinuousTestScheduler:
    def start_scheduler(self)
    def stop_scheduler(self)
    def get_test_status(self) -> Dict[str, Any]
```

### Test Result Classes

#### MemoryLeakResult
```python
@dataclass
class MemoryLeakResult:
    test_name: str
    iterations: int
    memory_deltas_mb: List[float]
    average_delta: float
    standard_deviation: float
    trend_slope: float
    leak_detected: bool
    leak_confidence: float
    recommendations: List[str]
```

#### PerformanceResult
```python
@dataclass
class PerformanceResult:
    test_name: str
    execution_time: float
    memory_used_mb: float
    file_size_mb: float
    triangle_count: int
    vertex_count: int
    success: bool
    regression_detected: bool
```

#### CodeQualityReport
```python
@dataclass
class CodeQualityReport:
    timestamp: str
    overall_score: float
    metrics: List[QualityMetric]
    test_coverage: float
    performance_score: float
    reliability_score: float
    maintainability_score: float
    security_score: float
```

### Configuration Files

#### Test Suite Configuration
```json
{
  "unit_tests": {
    "name": "unit_tests",
    "test_patterns": ["test_*.py"],
    "schedule": "hourly",
    "timeout_minutes": 30,
    "critical": true,
    "retry_count": 2,
    "environment_vars": {},
    "quality_gates": {
      "test_coverage": 80.0,
      "failure_rate": 5.0
    }
  }
}
```

#### Email Configuration
```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your_email@gmail.com",
  "password": "app_password",
  "recipients": ["team@company.com"],
  "alerts_only": true
}
```

---

## Support and Contribution

For questions, issues, or contributions to the testing framework:

1. **Documentation**: Check this guide and inline code documentation
2. **Issues**: Report bugs or feature requests through the project issue tracker
3. **Contributions**: Follow the project's contribution guidelines
4. **Support**: Contact the development team for framework-specific questions

This testing framework is designed to grow with the project. Regular updates and improvements ensure it remains effective and maintainable.