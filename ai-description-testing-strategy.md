# AI Description Service Testing Strategy

## Overview

This document outlines a comprehensive testing strategy for the integrated AI description service feature, ensuring reliability, performance, and security.

## Testing Framework

### Testing Levels

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Service interaction testing
3. **UI Tests** - User interface functionality
4. **Performance Tests** - Load and stress testing
5. **Security Tests** - API key and data security
6. **End-to-End Tests** - Complete workflow testing

## Unit Tests

### AI Description Service Tests

```python
# tests/test_ai_description_service.py
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.gui.services.ai_description_service import AIDescriptionService

class TestAIDescriptionService:
    """Test cases for AI Description Service."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config = {
            "ai_description": {
                "enabled": True,
                "default_provider": "openai",
                "providers": {
                    "openai": {
                        "api_key": "test-key",
                        "model": "gpt-4-vision-preview"
                    }
                }
            }
        }
        manager = Mock()
        manager.get.return_value = config["ai_description"]
        return manager
    
    @pytest.fixture
    def ai_service(self, mock_config_manager):
        """Create AI service instance for testing."""
        with patch('src.gui.services.ai_description_service.OpenAIProvider'):
            return AIDescriptionService(mock_config_manager)
    
    def test_service_initialization(self, ai_service):
        """Test service initialization."""
        assert ai_service.enabled is True
        assert ai_service.default_provider == "openai"
        assert len(ai_service.providers) > 0
    
    def test_is_available(self, ai_service):
        """Test service availability check."""
        # Mock provider configuration
        with patch.object(ai_service.providers['OpenAI'], 'is_configured', return_value=True):
            assert ai_service.is_available() is True
        
        with patch.object(ai_service.providers['OpenAI'], 'is_configured', return_value=False):
            assert ai_service.is_available() is False
    
    def test_get_available_providers(self, ai_service):
        """Test getting available providers."""
        with patch.object(ai_service.providers['OpenAI'], 'is_configured', return_value=True):
            providers = ai_service.get_available_providers()
            assert "OpenAI" in providers
    
    @pytest.fixture
    def test_image(self):
        """Create a test image file."""
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # Write minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'\x00\x00\x00\rIHDR')
            f.write(b'\x00\x00\x00\x01\x00\x00\x00\x01')
            f.write(b'\x08\x02\x00\x00\x00\x90wS\xde')
            f.write(b'\x00\x00\x00\x0cIDATx\x9cc')
            f.write(b'\xf8\x00\x00\x00\x01\x00\x01')
            f.write(b'\x00\x00\x00\x00IEND\xaeB`\x82')
            return f.name
    
    def test_generate_description(self, ai_service, test_image):
        """Test description generation."""
        # Mock provider response
        mock_result = {
            "title": "Test Image",
            "description": "A test image for validation",
            "metadata_keywords": ["test", "image", "validation"]
        }
        
        with patch.object(ai_service.providers['OpenAI'], 'analyze_image', return_value=mock_result):
            result = ai_service.generate_description(test_image, "OpenAI")
            
            assert result["title"] == "Test Image"
            assert result["description"] == "A test image for validation"
            assert "test" in result["metadata_keywords"]
    
    def test_cache_functionality(self, ai_service, test_image):
        """Test caching functionality."""
        mock_result = {"title": "Cached Result", "description": "Cached", "metadata_keywords": []}
        
        with patch.object(ai_service.providers['OpenAI'], 'analyze_image', return_value=mock_result):
            # First call should hit the provider
            result1 = ai_service.generate_description(test_image, "OpenAI")
            
            # Second call should use cache
            result2 = ai_service.generate_description(test_image, "OpenAI")
            
            assert result1 == result2
    
    def test_batch_processing(self, ai_service):
        """Test batch processing."""
        image_paths = ["image1.png", "image2.png", "image3.png"]
        mock_results = [
            {"title": "Image 1", "description": "Description 1", "metadata_keywords": []},
            {"title": "Image 2", "description": "Description 2", "metadata_keywords": []},
            {"title": "Image 3", "description": "Description 3", "metadata_keywords": []}
        ]
        
        with patch.object(ai_service.providers['OpenAI'], 'analyze_image', side_effect=mock_results):
            batch_id = ai_service.batch_generate(image_paths, "OpenAI")
            assert batch_id.startswith("batch_")
```

### Provider Tests

```python
# tests/test_providers.py
import pytest
from unittest.mock import Mock, patch

# Import providers (assuming they're copied to the main project)
from src.gui.services.providers.openai_provider import OpenAIProvider
from src.gui.services.providers.anthropic_provider import AnthropicProvider

class TestOpenAIProvider:
    """Test OpenAI provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4-vision-preview"
    
    def test_is_configured(self):
        """Test configuration check."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.is_configured() is True
        
        provider = OpenAIProvider()
        assert provider.is_configured() is False
    
    @pytest.mark.integration
    def test_analyze_image(self):
        """Test image analysis (requires valid API key)."""
        # Skip if no API key available
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key available")
        
        provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.png') as f:
            # Simple PNG file
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82')
            f.flush()
            
            result = provider.analyze_image(f.name)
            assert "title" in result
            assert "description" in result
            assert "metadata_keywords" in result
```

## Integration Tests

### Service Integration Tests

```python
# tests/test_ai_service_integration.py
import pytest
from unittest.mock import Mock, patch

from src.gui.services.ai_description_service import AIDescriptionService
from src.gui.ai_components.ai_description_widget import AIDescriptionWidget

class TestAIServiceIntegration:
    """Test AI service integration with UI components."""
    
    @pytest.fixture
    def integrated_setup(self):
        """Setup integrated components."""
        config_manager = Mock()
        config_manager.get.return_value = {
            "enabled": True,
            "default_provider": "openai",
            "providers": {"openai": {"api_key": "test"}}
        }
        
        ai_service = AIDescriptionService(config_manager)
        widget = AIDescriptionWidget(ai_service)
        
        return ai_service, widget
    
    def test_service_widget_integration(self, integrated_setup):
        """Test service and widget integration."""
        ai_service, widget = integrated_setup
        
        # Test widget can access service
        assert widget.ai_service is ai_service
        
        # Test service signals connect to widget
        assert hasattr(ai_service, 'description_generated')
        assert hasattr(ai_service, 'error_occurred')
    
    def test_batch_processing_integration(self, integrated_setup):
        """Test batch processing integration."""
        ai_service, widget = integrated_setup
        
        image_paths = ["img1.png", "img2.png"]
        results = []
        errors = []
        
        def callback(result_list, error_list):
            results.extend(result_list)
            errors.extend(error_list)
        
        with patch.object(ai_service, 'generate_description') as mock_gen:
            mock_gen.return_value = {"title": "Test", "description": "Test desc", "metadata_keywords": []}
            
            batch_id = ai_service.batch_generate(image_paths, callback=callback)
            assert batch_id is not None
```

## UI Tests

### Widget Functionality Tests

```python
# tests/test_ai_widget_ui.py
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from unittest.mock import Mock

from src.gui.services.ai_description_service import AIDescriptionService
from src.gui.ai_components.ai_description_widget import AIDescriptionWidget

@pytest.fixture
def qapp():
    """Qt Application fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def ai_widget(qapp):
    """Create AI widget for testing."""
    mock_service = Mock()
    mock_service.get_available_providers.return_value = ["OpenAI", "Anthropic"]
    mock_service.default_provider = "OpenAI"
    
    widget = AIDescriptionWidget(mock_service)
    return widget

def test_widget_initialization(ai_widget):
    """Test widget initializes correctly."""
    assert ai_widget is not None
    assert ai_widget.provider_combo.count() > 0

def test_image_selection(ai_widget, qapp):
    """Test image selection functionality."""
    # Mock file dialog
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
        mock_dialog.return_value = ("test_image.png", "")
        
        QTest.mouseClick(ai_widget.select_image_button, Qt.LeftButton)
        
        assert ai_widget.current_image_path == "test_image.png"
        assert ai_widget.image_path_label.text() == "test_image.png"

def test_generate_button_state(ai_widget):
    """Test generate button state management."""
    # Initially disabled (no image)
    assert not ai_widget.generate_button.isEnabled()
    
    # Set image
    ai_widget.set_image("test.png")
    assert ai_widget.generate_button.isEnabled()
```

## Performance Tests

### Load Testing

```python
# tests/test_ai_performance.py
import pytest
import time
import psutil
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from src.gui.services.ai_description_service import AIDescriptionService

class TestAIPerformance:
    """Performance tests for AI service."""
    
    @pytest.mark.performance
    def test_single_description_performance(self):
        """Test performance of single description generation."""
        mock_service = Mock()
        mock_service.generate_description.return_value = {
            "title": "Performance Test",
            "description": "Test description",
            "metadata_keywords": []
        }
        
        start_time = time.time()
        result = mock_service.generate_description("test.png", "OpenAI")
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        assert result is not None
    
    @pytest.mark.performance
    def test_batch_processing_performance(self):
        """Test performance of batch processing."""
        mock_service = Mock()
        mock_service.generate_description.return_value = {
            "title": "Batch Test",
            "description": "Batch description",
            "metadata_keywords": []
        }
        
        image_count = 10
        start_time = time.time()
        
        # Simulate batch processing
        for i in range(image_count):
            mock_service.generate_description(f"image_{i}.png", "OpenAI")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should be faster per image due to parallel processing
        assert execution_time < 30.0  # Total batch should complete within 30 seconds
    
    @pytest.mark.performance
    def test_memory_usage_stability(self):
        """Test memory usage stability during operation."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        mock_service = Mock()
        mock_service.generate_description.return_value = {
            "title": "Memory Test",
            "description": "Memory test description",
            "metadata_keywords": ["test"] * 100  # Large keyword list
        }
        
        # Generate many descriptions
        for i in range(100):
            mock_service.generate_description(f"image_{i}.png", "OpenAI")
        
        # Check memory hasn't grown significantly
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Should not consume more than 100MB
        assert memory_growth < 100 * 1024 * 1024
```

## Security Tests

### API Key Security

```python
# tests/test_ai_security.py
import pytest
import json
import tempfile
from pathlib import Path

from src.gui.services.ai_description_service import AIDescriptionService

class TestAISecurity:
    """Security tests for AI service."""
    
    def test_api_key_not_in_logs(self, caplog):
        """Test that API keys are not logged."""
        mock_config = Mock()
        mock_config.get.return_value = {
            "enabled": True,
            "providers": {
                "openai": {
                    "api_key": "sk-1234567890abcdef",
                    "model": "gpt-4-vision-preview"
                }
            }
        }
        
        service = AIDescriptionService(mock_config)
        
        # Try to generate description
        with patch.object(service.providers['OpenAI'], 'analyze_image') as mock_analyze:
            mock_analyze.return_value = {"title": "Test", "description": "Test", "metadata_keywords": []}
            
            try:
                service.generate_description("test.png", "OpenAI")
            except Exception:
                pass  # Ignore errors, just check logs
        
        # Check logs don't contain API key
        log_text = caplog.text.lower()
        assert "sk-1234567890abcdef" not in log_text
    
    def test_cache_security(self):
        """Test that cached responses don't expose sensitive data."""
        # This would test that cached responses don't include API keys
        # or other sensitive information
        pass
    
    def test_configuration_encryption(self):
        """Test configuration data encryption."""
        # Test that sensitive configuration is properly encrypted
        pass
```

## End-to-End Tests

### Complete Workflow Tests

```python
# tests/test_ai_e2e.py
import pytest
import tempfile
from pathlib import Path

from src.gui.services.ai_description_service import AIDescriptionService
from src.gui.ai_components.ai_description_widget import AIDescriptionWidget

class TestAIE2E:
    """End-to-end tests for AI description workflow."""
    
    @pytest.mark.e2e
    def test_complete_description_workflow(self):
        """Test complete description generation workflow."""
        # 1. Initialize service with configuration
        config_manager = Mock()
        config_manager.get.return_value = {
            "enabled": True,
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "test-key",
                    "model": "gpt-4-vision-preview"
                }
            }
        }
        
        ai_service = AIDescriptionService(config_manager)
        
        # 2. Create test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_image_path = f.name
        
        # 3. Mock AI provider response
        with patch.object(ai_service.providers['OpenAI'], 'analyze_image') as mock_analyze:
            mock_analyze.return_value = {
                "title": "E2E Test Image",
                "description": "This is an end-to-end test of the AI description service.",
                "metadata_keywords": ["test", "e2e", "integration"]
            }
            
            # 4. Generate description
            result = ai_service.generate_description(test_image_path, "OpenAI")
            
            # 5. Verify result structure
            assert "title" in result
            assert "description" in result
            assert "metadata_keywords" in result
            assert isinstance(result["metadata_keywords"], list)
    
    @pytest.mark.e2e
    def test_batch_description_workflow(self):
        """Test batch description generation workflow."""
        # Similar to above but for batch processing
        pass
```

## Test Configuration

### Pytest Configuration

```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    ui: UI tests
    performance: Performance tests
    security: Security tests
    e2e: End-to-end tests
    slow: Slow running tests
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Environment Configuration

```bash
# tests/conftest.py
import os
import pytest

# Test environment variables
os.environ["TEST_MODE"] = "true"

@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "openai_api_key": os.getenv("TEST_OPENAI_API_KEY", "test-key"),
        "anthropic_api_key": os.getenv("TEST_ANTHROPIC_API_KEY", "test-key"),
        "cache_dir": "/tmp/ai_test_cache"
    }
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ai-description-tests.yml
name: AI Description Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: |
        pytest tests/test_ai_description_service.py -v
    
    - name: Run integration tests
      run: |
        pytest tests/test_ai_service_integration.py -v -m integration
    
    - name: Run performance tests
      run: |
        pytest tests/test_ai_performance.py -v -m performance --benchmark-only
    
    - name: Run security tests
      run: |
        pytest tests/test_ai_security.py -v -m security
    
    - name: Generate coverage report
      run: |
        coverage report --include="src/gui/services/ai_description_service.py"
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## Test Data Management

### Test Images

```python
# tests/test_data/__init__.py
import os
from pathlib import Path

# Test image directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_IMAGES = {
    "simple": TEST_DATA_DIR / "simple.png",
    "complex": TEST_DATA_DIR / "complex.png",
    "invalid": TEST_DATA_DIR / "invalid.txt"
}

def get_test_image(name):
    """Get path to test image."""
    return TEST_IMAGES[name]
```

## Test Reporting

### Coverage Reporting

```python
# tests/test_coverage.py
import pytest
import coverage

# Coverage configuration
cov = coverage.Coverage(source=['src/gui/services/ai_description_service.py'])
cov.start()

# Run tests
pytest.main([__file__])

# Generate report
cov.stop()
cov.save()
cov.report(show_missing=True)
cov.html_report(directory='coverage_html')
```

## Performance Monitoring

### Benchmarking

```python
# tests/test_benchmarks.py
import pytest
import time
from unittest.mock import Mock

from src.gui.services.ai_description_service import AIDescriptionService

@pytest.mark.benchmark
def test_description_generation_benchmark(benchmark):
    """Benchmark description generation."""
    service = Mock()
    service.generate_description.return_value = {
        "title": "Benchmark Test",
        "description": "Benchmark description",
        "metadata_keywords": []
    }
    
    result = benchmark(service.generate_description, "test.png", "OpenAI")
    assert result is not None
```

## Success Criteria

### Test Coverage Goals

- **Unit Test Coverage**: >90%
- **Integration Test Coverage**: >80%
- **UI Test Coverage**: >70%
- **Performance Test Coverage**: All critical paths
- **Security Test Coverage**: All security-sensitive operations

### Performance Benchmarks

- Single description generation: <10 seconds
- Batch processing (10 images): <60 seconds
- Memory usage: <200MB per 100 operations
- Cache hit rate: >70% for repeated images

### Quality Gates

- All unit tests must pass
- Integration tests must pass
- No critical security vulnerabilities
- Performance benchmarks must be met
- Memory leak tests must pass

## Maintenance

### Test Updates

- Update tests when adding new AI providers
- Update tests when changing API interfaces
- Update performance benchmarks as models improve
- Regular review of test coverage metrics

### Test Data Management

- Regular cleanup of test cache directories
- Update test images as needed
- Monitor and fix flaky tests
- Maintain test data for new provider types