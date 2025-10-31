# Development Guidelines

## Overview

This document provides comprehensive guidelines for developing and maintaining the Candy-Cadence application. These guidelines ensure code quality, maintainability, and consistency across the codebase.

## Code Organization Principles

### Module Structure

Each module should follow this structure:

```
module_name/
├── __init__.py           # Module initialization and exports
├── interfaces.py         # Abstract base classes and interfaces
├── implementations/      # Concrete implementations
│   ├── __init__.py
│   ├── service.py       # Main service implementation
│   ├── repository.py    # Data access implementation
│   └── utils.py         # Helper functions
├── models/              # Data models and structures
│   ├── __init__.py
│   └── entities.py      # Data entities
└── tests/               # Module-specific tests
    ├── __init__.py
    ├── test_service.py
    └── test_repository.py
```

### File Naming Conventions

- **Modules**: lowercase with underscores (`model_service.py`)
- **Classes**: PascalCase (`ModelService`)
- **Functions**: lowercase with underscores (`load_model()`)
- **Constants**: UPPERCASE (`MAX_CACHE_SIZE`)
- **Private members**: prefix with underscore (`_internal_method()`)

### Import Organization

```python
# Standard library imports
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

# Local application imports
from src.core.interfaces import IService
from src.core.models import Model
from .models import ModelData
from .utils import helper_function
```

## Code Quality Standards

### Type Hints

All functions must include type hints:

```python
def load_model(self, file_path: Path, progress_callback: Optional[callable] = None) -> bool:
    """Load a 3D model from file.
    
    Args:
        file_path: Path to the model file
        progress_callback: Optional callback for progress updates
        
    Returns:
        True if model was loaded successfully, False otherwise
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ParseError: If the file format is invalid
    """
    pass
```

### Documentation Standards

#### Function Documentation

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Brief description of what the function does.

    Detailed description of the function's purpose, behavior,
    and any important considerations.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of the return value

    Raises:
        ExceptionType: When and why this exception is raised

    Example:
        >>> result = function_name("value1", "value2")
        >>> print(result)
        expected_output
    """
    pass
```

#### Class Documentation

```python
class ModelService:
    """Service for managing 3D model operations.

    This class provides a high-level interface for loading, unloading,
    and managing 3D models in the application. It handles file parsing,
    caching, and metadata management.

    Attributes:
        cache: The model cache instance
        parsers: Dictionary of available file parsers

    Example:
        >>> service = ModelService()
        >>> success = service.load_model(Path("model.stl"))
        >>> if success:
        ...     print("Model loaded successfully")
    """
    pass
```

### Error Handling

#### Exception Hierarchy

```python
class CandyCadenceError(Exception):
    """Base exception for all Candy-Cadence errors."""
    pass

class ModelError(CandyCadenceError):
    """Base exception for model-related errors."""
    pass

class ParseError(ModelError):
    """Raised when model file parsing fails."""
    pass

class FileNotSupportedError(ModelError):
    """Raised when file format is not supported."""
    pass

class DatabaseError(CandyCadenceError):
    """Base exception for database-related errors."""
    pass
```

#### Error Handling Pattern

```python
def load_model(self, file_path: Path) -> bool:
    """Load a model with proper error handling."""
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        parser = self._get_parser(file_path)
        if parser is None:
            raise FileNotSupportedError(f"Unsupported file format: {file_path.suffix}")
        
        model_data = parser.parse(file_path)
        self._cache.store(model_data)
        
        self.logger.info(f"Successfully loaded model: {file_path}")
        return True
        
    except FileNotFoundError as e:
        self.logger.error(f"File not found: {e}")
        return False
    except FileNotSupportedError as e:
        self.logger.error(f"Unsupported file format: {e}")
        return False
    except ParseError as e:
        self.logger.error(f"Failed to parse model file: {e}")
        return False
    except Exception as e:
        self.logger.exception(f"Unexpected error loading model: {e}")
        return False
```

### Logging Standards

#### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened, but the software is still working
- **ERROR**: A serious problem occurred
- **CRITICAL**: A very serious error occurred

#### Log Format

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        """Setup JSON-formatted handler."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self.logger.info(message, extra={'structured_data': kwargs})
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with exception details."""
        if error:
            kwargs['exception'] = str(error)
            kwargs['exception_type'] = type(error).__name__
        self.logger.error(message, extra={'structured_data': kwargs})
```

## Architecture Guidelines

### Dependency Injection

Use dependency injection to reduce coupling:

```python
from abc import ABC, abstractmethod
from typing import Protocol

class IModelRepository(Protocol):
    """Protocol for model repository operations."""
    
    def get(self, model_id: str) -> Optional[Model]:
        ...

class ModelService:
    """Service with dependency injection."""
    
    def __init__(self, repository: IModelRepository):
        self._repository = repository
    
    def get_model(self, model_id: str) -> Optional[Model]:
        return self._repository.get(model_id)
```

### Interface Segregation

Create focused interfaces:

```python
# Good: Focused interface
class IModelLoader(ABC):
    @abstractmethod
    def load_model(self, file_path: Path) -> Model:
        pass

# Avoid: Bloated interface
class IModelManager(ABC):
    @abstractmethod
    def load_model(self, file_path: Path) -> Model:
        pass
    
    @abstractmethod
    def save_model(self, model: Model, file_path: Path) -> bool:
        pass
    
    @abstractmethod
    def delete_model(self, model_id: str) -> bool:
        pass
    
    @abstractmethod
    def search_models(self, query: str) -> List[Model]:
        pass
```

### Single Responsibility Principle

Each class should have one reason to change:

```python
# Good: Focused responsibility
class ModelParser:
    """Parse 3D model files."""
    pass

class ModelValidator:
    """Validate model data."""
    pass

class ModelCache:
    """Cache model data."""
    pass

# Avoid: Multiple responsibilities
class ModelManager:
    """Parse, validate, cache, and manage models."""
    pass
```

## Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

class TestModelService:
    """Test suite for ModelService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.repository = Mock(spec=IModelRepository)
        self.service = ModelService(self.repository)
    
    def test_load_model_success(self):
        """Test successful model loading."""
        # Arrange
        file_path = Path("test_model.stl")
        expected_model = Model(id="test_id", data="test_data")
        self.repository.get.return_value = None
        self.repository.create.return_value = "test_id"
        
        # Act
        result = self.service.load_model(file_path)
        
        # Assert
        assert result is True
        self.repository.create.assert_called_once()
    
    def test_load_model_file_not_found(self):
        """Test handling of missing file."""
        # Arrange
        file_path = Path("nonexistent.stl")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.service.load_model(file_path)
    
    @patch('src.core.model_cache.get_model_cache')
    def test_load_model_with_cache(self, mock_cache):
        """Test model loading with cache."""
        # Test implementation
        pass
```

### Test Naming

- Use descriptive test names: `test_load_model_success` not `test_load`
- Follow the pattern: `test_[method]_[scenario]_[expected_result]`
- Group related tests in test classes

### Mock Guidelines

- Mock at the interface level, not implementation
- Use specific mock specs: `Mock(spec=IModelRepository)`
- Mock external dependencies (file system, network, database)
- Don't mock simple data structures or value objects

## Performance Guidelines

### Memory Management

```python
class ModelCache:
    """Memory-efficient model cache."""
    
    def __init__(self, max_size: int = 100):
        self._cache = {}
        self._max_size = max_size
        self._access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with LRU eviction."""
        if key in self._cache:
            # Update access order
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Put item in cache with size management."""
        if len(self._cache) >= self._max_size:
            # Evict least recently used
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = value
        self._access_order.append(key)
```

### Async Operations

```python
import asyncio
from typing import Coroutine

class AsyncModelService:
    """Asynchronous model service."""
    
    async def load_model_async(self, file_path: Path) -> bool:
        """Load model asynchronously."""
        try:
            # Run CPU-bound operation in thread pool
            loop = asyncio.get_event_loop()
            model_data = await loop.run_in_executor(
                None, self._parse_model, file_path
            )
            
            # Run I/O operation
            await self._cache.store_async(model_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def _parse_model(self, file_path: Path) -> Model:
        """Parse model file (CPU-bound)."""
        # Implementation
        pass
```

## Security Guidelines

### Input Validation

```python
from pathlib import Path
import os

def validate_file_path(file_path: str) -> Path:
    """Validate and sanitize file path."""
    try:
        path = Path(file_path).resolve()
        
        # Check if path is within allowed directory
        allowed_dir = Path("/safe/directory").resolve()
        if not str(path).startswith(str(allowed_dir)):
            raise ValueError("File path outside allowed directory")
        
        # Check file extension
        allowed_extensions = {'.stl', '.obj', '.3mf'}
        if path.suffix.lower() not in allowed_extensions:
            raise ValueError(f"Unsupported file extension: {path.suffix}")
        
        return path
        
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {e}")
```

### Error Information Disclosure

```python
# Bad: Exposing sensitive information
try:
    risky_operation()
except Exception as e:
    logger.error(f"Database error: {e}")  # Might expose connection strings

# Good: Sanitized error messages
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed due to internal error")
    # Log detailed error separately for debugging
    logger.debug(f"Detailed error: {e}", exc_info=True)
```

## Documentation Guidelines

### API Documentation

- Document all public interfaces
- Include usage examples
- Specify parameter types and return values
- Document exceptions that may be raised

### Architecture Documentation

- Keep architecture diagrams up to date
- Document design decisions and rationale
- Include migration guides for breaking changes
- Maintain changelog

### Code Comments

```python
def complex_algorithm(data: List[int]) -> List[int]:
    """Implement complex sorting algorithm.
    
    This function uses a hybrid approach combining quicksort
    and insertion sort for optimal performance on different
    data sizes.
    """
    # Use insertion sort for small arrays (less than 10 elements)
    # as it has lower overhead for small datasets
    if len(data) < 10:
        return insertion_sort(data)
    
    # Use quicksort for larger arrays
    return quick_sort(data)
```

## Review Process

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All functions have type hints
- [ ] Documentation is complete and accurate
- [ ] Error handling is appropriate
- [ ] Logging is implemented correctly
- [ ] Tests are included and passing
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Architecture principles followed

### Pull Request Guidelines

- Keep PRs focused on a single feature/fix
- Include comprehensive description
- Add tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass

## Continuous Integration

### Automated Checks

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run linting
        run: |
          pylint src/
          mypy src/
      - name: Run tests
        run: |
          pytest tests/ --cov=src/
      - name: Run security checks
        run: |
          bandit -r src/
          safety check
```

### Quality Gates

- All tests must pass
- Code coverage must be above 80%
- No pylint warnings (score > 9.0)
- No mypy errors
- No security vulnerabilities
- Performance benchmarks must pass

## Conclusion

These guidelines ensure consistent, high-quality code that is maintainable, testable, and secure. Following these practices will help the team deliver reliable software efficiently.

For questions or suggestions about these guidelines, please discuss with the development team and update this document as needed.