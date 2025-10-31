# Candy-Cadence Developer Guide

## Overview

This comprehensive guide provides developers with everything needed to understand, set up, and contribute to the Candy-Cadence project. It covers development environment setup, coding standards, architecture patterns, and procedures for extending the system.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Architecture Patterns](#architecture-patterns)
6. [Extending the System](#extending-the-system)
7. [Testing Guidelines](#testing-guidelines)
8. [Debugging](#debugging)
9. [Performance Guidelines](#performance-guidelines)
10. [API Reference](#api-reference)
11. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

#### Required Software
- **Python 3.8-3.12** (64-bit)
- **Git** for version control
- **Visual Studio Code** (recommended) or PyCharm
- **Inno Setup** (for building installers)

#### Optional Tools
- **Docker** (for containerized development)
- **GitHub Desktop** (for Git GUI)
- **Windows Terminal** (enhanced command line)

### Initial Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd candy-cadence
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### 4. Verify Installation
```bash
# Run basic tests
python -m pytest tests/ -v

# Run the application
python src/main.py
```

### Development Tools Configuration

#### Visual Studio Code Setup
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/build": true,
        "**/dist": true
    }
}
```

#### Recommended Extensions
- Python
- Pylance
- Python Docstring Generator
- GitLens
- Error Lens
- Todo Highlight

### Environment Variables

Create `.env` file in project root:
```bash
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG

# Database settings
DATABASE_PATH=./data/candy_cadence.db

# Performance settings
MAX_CACHE_SIZE=100
ENABLE_GPU_ACCELERATION=True

# Testing settings
TEST_DATABASE_PATH=./tests/test_data/test.db
```

## Project Structure

### Directory Layout

```
candy-cadence/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── interfaces/           # Abstract interfaces
│   │   ├── services/             # Service implementations
│   │   ├── models/               # Data models
│   │   └── exceptions.py         # Custom exceptions
│   ├── gui/                      # User interface
│   │   ├── components/           # UI components
│   │   ├── dialogs/              # Dialog windows
│   │   └── widgets/              # Custom widgets
│   ├── parsers/                  # File format parsers
│   │   ├── base_parser.py        # Abstract base parser
│   │   ├── stl_parser.py         # STL parser
│   │   ├── obj_parser.py         # OBJ parser
│   │   ├── threemf_parser.py     # 3MF parser
│   │   └── step_parser.py        # STEP parser
│   ├── database/                 # Database layer
│   │   ├── repositories/         # Repository implementations
│   │   ├── migrations/           # Database migrations
│   │   └── database_manager.py   # Database manager
│   ├── utils/                    # Utility functions
│   │   ├── file_utils.py         # File operations
│   │   ├── geometry_utils.py     # 3D geometry utilities
│   │   └── logging_utils.py      # Logging utilities
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── unit_tests/               # Unit tests
│   ├── integration_tests/        # Integration tests
│   ├── performance_tests/        # Performance tests
│   ├── gui_tests/                # GUI tests
│   └── test_data/                # Test data files
├── docs/                         # Documentation
│   ├── architecture/             # Architecture docs
│   ├── developer/                # Developer docs
│   ├── user/                     # User documentation
│   └── api/                      # API documentation
├── resources/                    # Application resources
│   ├── icons/                    # Icon files
│   ├── styles/                   # CSS stylesheets
│   └── themes/                   # Theme definitions
├── installer/                    # Installation scripts
├── scripts/                      # Build and utility scripts
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── setup.py                      # Package configuration
├── pyinstaller.spec              # PyInstaller configuration
└── README.md                     # Project overview
```

### Key Files

#### Core Files
- `src/main.py`: Application entry point
- `src/core/interfaces/`: Abstract base classes and interfaces
- `src/core/services/`: Service implementations
- `src/gui/main_window.py`: Main application window

#### Configuration Files
- `pyinstaller.spec`: Executable build configuration
- `.pylintrc`: Code quality configuration
- `pytest.ini`: Testing configuration
- `setup.py`: Package metadata and configuration

## Development Workflow

### Branch Strategy

We use a Git Flow branching strategy:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: New features (`feature/add-stl-parser`)
- **bugfix/**: Bug fixes (`bugfix/fix-memory-leak`)
- **hotfix/**: Critical production fixes (`hotfix/security-patch`)

### Development Process

#### 1. Feature Development
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Develop your feature
# ... make changes ...

# Run tests
python -m pytest tests/ -v

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push and create PR
git push origin feature/your-feature-name
```

#### 2. Code Review Process
1. Create Pull Request to `develop` branch
2. Ensure all CI checks pass
3. Request code review from team members
4. Address review comments
5. Merge after approval

#### 3. Release Process
```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version numbers
# ... update version files ...

# Run full test suite
python -m pytest tests/ -v --cov=src

# Create release PR to main
# ... merge to main ...

# Tag release
git tag v1.2.0
git push origin v1.2.0
```

### Commit Message Convention

We follow the Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Examples:
```bash
feat(parser): add support for PLY file format
fix(gui): resolve memory leak in model viewer
docs(api): update ModelService documentation
test(parser): add unit tests for STL parser
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

#### Code Formatting
- **Line Length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Single quotes for strings, double quotes when needed
- **Trailing Commas**: Always use trailing commas in multi-line structures

#### Naming Conventions
```python
# Classes: PascalCase
class ModelService:
    pass

# Functions and variables: snake_case
def load_model():
    model_data = {}

# Constants: UPPERCASE
MAX_CACHE_SIZE = 100

# Private methods: leading underscore
def _internal_method(self):
    pass

# Protected attributes: leading underscore
self._protected_attr = value
```

#### Import Organization
```python
# Standard library imports
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget
import numpy as np

# Local application imports
from src.core.interfaces import IService
from src.core.models import Model
from .models import ModelData
from .utils import helper_function
```

### Type Hints

All functions must include type hints:

```python
from typing import Dict, List, Optional, Union
from pathlib import Path

def load_model(
    self, 
    file_path: Path, 
    progress_callback: Optional[callable] = None
) -> bool:
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

#### Docstring Format
We use Google-style docstrings:

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

#### Module Documentation
```python
"""Module for 3D model parsing functionality.

This module provides classes and functions for parsing various 3D model
file formats including STL, OBJ, and 3MF files.

Classes:
    BaseParser: Abstract base class for all parsers
    STLParser: STL file format parser
    OBJParser: OBJ file format parser

Example:
    >>> parser = STLParser()
    >>> model = parser.parse_file(Path("model.stl"))
    >>> print(f"Loaded model with {len(model.vertices)} vertices")
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)
```

## Architecture Patterns

### Interface-Based Design

All major components use interfaces for loose coupling:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

class IModelService(ABC):
    """Interface for model management services."""
    
    @abstractmethod
    def load_model(self, file_path: Path) -> bool:
        """Load a 3D model from file."""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        pass
    
    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a loaded model by ID."""
        pass
```

### Dependency Injection

Dependencies are injected through constructors:

```python
class ModelService(IModelService):
    """Service for managing 3D model operations."""
    
    def __init__(
        self,
        model_repository: IModelRepository,
        metadata_repository: IMetadataRepository,
        parser_registry: Dict[str, IParser],
        format_detector: IFormatDetector,
        cache: IModelCache
    ) -> None:
        # Dependency injection
        self._model_repository = model_repository
        self._metadata_repository = metadata_repository
        self._parser_registry = parser_registry
        self._format_detector = format_detector
        self._cache = cache
        self._logger = logging.getLogger(__name__)
```

### Repository Pattern

Data access is abstracted through repositories:

```python
class ModelRepository(IModelRepository):
    """Repository for model data operations."""
    
    def __init__(self, database: IDatabase) -> None:
        self._database = database
        self._logger = logging.getLogger(__name__)
    
    def create(self, model_data: Dict[str, Any]) -> str:
        """Create a new model record."""
        try:
            model_id = self._database.insert('models', model_data)
            self._logger.info(f"Created model record: {model_id}")
            return model_id
        except Exception as e:
            self._logger.error(f"Failed to create model: {e}")
            raise
```

### Factory Pattern

Object creation is centralized through factories:

```python
class ParserFactory:
    """Factory for creating parser instances."""
    
    _parsers = {
        'stl': STLParser,
        'obj': OBJParser,
        '3mf': ThreemfParser,
        'step': StepParser
    }
    
    @classmethod
    def create_parser(cls, file_format: str) -> IParser:
        """Create a parser for the specified format."""
        parser_class = cls._parsers.get(file_format.lower())
        if parser_class is None:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        return parser_class()
```

## Extending the System

### Adding New File Format Support

#### 1. Create Parser Class
```python
from src.parsers.base_parser import BaseParser
from src.core.interfaces import IParser
from typing import Any, Dict

class NewFormatParser(BaseParser, IParser):
    """Parser for new 3D file format."""
    
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.newfmt']
    
    @property
    def supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ['newfmt']
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle the given file."""
        return file_path.suffix.lower() in self._supported_extensions
    
    def parse(self, file_path: Path, progress_callback: Optional[callable] = None) -> Any:
        """Parse a new format file."""
        try:
            self._logger.info(f"Parsing new format file: {file_path}")
            
            # Implement parsing logic here
            with open(file_path, 'rb') as f:
                data = self._read_file_data(f)
            
            model = self._convert_to_model(data)
            
            if progress_callback:
                progress_callback(100.0)
            
            self._logger.info(f"Successfully parsed file: {file_path}")
            return model
            
        except Exception as e:
            self._logger.error(f"Failed to parse file {file_path}: {e}")
            raise ParseError(f"Failed to parse new format file: {e}")
    
    def _read_file_data(self, file_handle) -> bytes:
        """Read file data."""
        # Implement file reading logic
        return file_handle.read()
    
    def _convert_to_model(self, data: bytes) -> Model:
        """Convert raw data to Model object."""
        # Implement data conversion logic
        return Model(vertices=[], triangles=[], metadata={})
```

#### 2. Register Parser
Update `src/parsers/parser_registry.py`:
```python
from .new_format_parser import NewFormatParser

class ParserRegistry:
    """Registry for all available parsers."""
    
    def __init__(self) -> None:
        self._parsers = {
            'stl': STLParser(),
            'obj': OBJParser(),
            '3mf': ThreemfParser(),
            'step': StepParser(),
            'newfmt': NewFormatParser()  # Add new parser
        }
    
    def get_parser(self, file_format: str) -> IParser:
        """Get parser for specified format."""
        parser = self._parsers.get(file_format.lower())
        if parser is None:
            raise ValueError(f"No parser available for format: {file_format}")
        return parser
```

#### 3. Update Format Detector
Update `src/parsers/format_detector.py`:
```python
class FormatDetector:
    """Detects file formats based on file extensions and content."""
    
    def detect_format(self, file_path: Path) -> str:
        """Detect file format."""
        extension = file_path.suffix.lower()
        
        format_mapping = {
            '.stl': 'stl',
            '.obj': 'obj',
            '.3mf': '3mf',
            '.step': 'step',
            '.stp': 'step',
            '.newfmt': 'newfmt'  # Add new format
        }
        
        return format_mapping.get(extension, 'unknown')
```

### Adding New Service

#### 1. Define Interface
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IExportService(ABC):
    """Interface for model export services."""
    
    @abstractmethod
    def export_model(self, model_id: str, export_path: Path, format: str) -> bool:
        """Export model to specified format."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        pass
```

#### 2. Implement Service
```python
class ExportService(IExportService):
    """Service for exporting models to various formats."""
    
    def __init__(
        self,
        model_repository: IModelRepository,
        parser_registry: IParserRegistry
    ) -> None:
        self._model_repository = model_repository
        self._parser_registry = parser_registry
        self._logger = logging.getLogger(__name__)
    
    def export_model(self, model_id: str, export_path: Path, format: str) -> bool:
        """Export model to specified format."""
        try:
            # Get model data
            model = self._model_repository.get(model_id)
            if model is None:
                raise ValueError(f"Model not found: {model_id}")
            
            # Get appropriate parser
            parser = self._parser_registry.get_parser(format)
            
            # Export model
            parser.export(model, export_path)
            
            self._logger.info(f"Exported model {model_id} to {export_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to export model {model_id}: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ['stl', 'obj', '3mf']
```

### Adding New GUI Component

#### 1. Create Widget Class
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

class ModelInfoWidget(QWidget):
    """Widget for displaying model information."""
    
    model_changed = Signal(str)  # Emitted when model changes
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._model_id = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        self._title_label = QLabel("Model Information")
        self._info_label = QLabel("No model loaded")
        
        layout.addWidget(self._title_label)
        layout.addWidget(self._info_label)
    
    def set_model(self, model_id: str, model_info: Dict[str, Any]) -> None:
        """Set the model to display information for."""
        self._model_id = model_id
        
        info_text = f"""
        <h3>Model: {model_info.get('name', 'Unknown')}</h3>
        <p><b>Vertices:</b> {model_info.get('vertex_count', 0)}</p>
        <p><b>Triangles:</b> {model_info.get('triangle_count', 0)}</p>
        <p><b>File Size:</b> {model_info.get('file_size', 0)} bytes</p>
        """
        
        self._info_label.setText(info_text)
        self.model_changed.emit(model_id)
```

#### 2. Integrate with Main Window
```python
# In main_window.py
from src.gui.widgets.model_info_widget import ModelInfoWidget

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Add model info widget
        self._model_info_widget = ModelInfoWidget()
        layout.addWidget(self._model_info_widget)
        
        # Add other widgets...
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._model_info_widget.model_changed.connect(self._on_model_changed)
```

## Testing Guidelines

### Test Structure

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

class TestModelService:
    """Test suite for ModelService."""
    
    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.repository = Mock(spec=IModelRepository)
        self.service = ModelService(
            model_repository=self.repository,
            metadata_repository=Mock(),
            parser_registry={},
            format_detector=Mock()
        )
    
    def test_load_model_success(self) -> None:
        """Test successful model loading."""
        # Arrange
        file_path = Path("test_model.stl")
        expected_model = Model(id="test_id", data="test_data")
        
        # Act
        result = self.service.load_model(file_path)
        
        # Assert
        assert result is True
        self.repository.create.assert_called_once()
    
    def test_load_model_file_not_found(self) -> None:
        """Test handling of missing file."""
        # Arrange
        file_path = Path("nonexistent.stl")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.service.load_model(file_path)
```

#### Integration Tests
```python
class TestModelWorkflow:
    """Test complete model workflows."""
    
    def test_complete_loading_workflow(self) -> None:
        """Test complete model loading workflow."""
        # Setup test database
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Create services
            database = SQLiteDatabase(db_path)
            repository = ModelRepository(database)
            service = ModelService(
                model_repository=repository,
                metadata_repository=Mock(),
                parser_registry={'stl': STLParser()},
                format_detector=FormatDetector()
            )
            
            # Test workflow
            file_path = Path("test_data/cube.stl")
            result = service.load_model(file_path)
            
            assert result is True
            assert service.get_loaded_models()
```

#### Performance Tests
```python
class TestPerformance:
    """Performance test suite."""
    
    def test_large_file_loading_performance(self) -> None:
        """Test loading performance for large files."""
        file_path = Path("test_data/large_model.stl")
        start_time = time.perf_counter()
        
        service = ModelService(...)
        result = service.load_model(file_path)
        
        end_time = time.perf_counter()
        load_time = end_time - start_time
        
        assert result is True
        assert load_time < 15.0  # Performance requirement
```

### Running Tests

#### All Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit_tests/ -v
python -m pytest tests/integration_tests/ -v
python -m pytest tests/performance_tests/ -v
```

#### Continuous Testing
```bash
# Run tests in watch mode
ptw tests/ -- -v

# Run tests on file changes
python -m pytest tests/ --ff
```

## Debugging

### Logging Configuration

#### Basic Logging Setup
```python
import logging
import json
from datetime import datetime

def setup_logging(log_level: str = "INFO") -> None:
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('candy_cadence.log')
        ]
    )
```

#### Structured Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage
logger = structlog.get_logger()
logger.info("Model loaded", model_id="123", file_path="/path/to/model.stl")
```

### Debugging Techniques

#### Debugging GUI Issues
```python
# Enable Qt debugging
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

# Add debug output to GUI components
class ModelViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setProperty("debug", True)  # Enable debug styling
    
    def paintEvent(self, event):
        if self.property("debug"):
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 1))  # Red border
            painter.drawRect(self.rect())
```

#### Memory Debugging
```python
import tracemalloc
import gc

def start_memory_tracking():
    """Start memory usage tracking."""
    tracemalloc.start()
    
    # Take initial snapshot
    snapshot = tracemalloc.take_snapshot()
    return snapshot

def analyze_memory_usage(snapshot):
    """Analyze memory usage."""
    top_stats = snapshot.statistics('lineno')
    
    print("[ Top 10 memory consumers ]")
    for stat in top_stats[:10]:
        print(stat)
```

### Common Debugging Scenarios

#### Parser Debugging
```python
class DebugSTLParser(STLParser):
    """Debug version of STL parser."""
    
    def parse(self, file_path: Path, progress_callback=None):
        print(f"DEBUG: Starting to parse {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(80)
                print(f"DEBUG: File header: {header[:20]}")
                
                # Continue with parsing...
                
        except Exception as e:
            print(f"DEBUG: Parse error: {e}")
            raise
```

#### Database Debugging
```python
class DebugDatabase(SQLiteDatabase):
    """Debug version of database."""
    
    def execute(self, query: str, params: tuple = None):
        print(f"DEBUG: SQL Query: {query}")
        print(f"DEBUG: Parameters: {params}")
        
        result = super().execute(query, params)
        print(f"DEBUG: Query result: {result}")
        
        return result
```

## Performance Guidelines

### Memory Management

#### Efficient Caching
```python
from functools import lru_cache
from typing import Optional

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

#### Memory Monitoring
```python
import psutil
import threading
import time

class MemoryMonitor:
    """Monitor application memory usage."""
    
    def __init__(self, threshold_mb: int = 1000):
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start memory monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Memory monitoring loop."""
        process = psutil.Process()
        
        while self.monitoring:
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.threshold_mb:
                logging.warning(f"High memory usage: {memory_mb:.1f} MB")
            
            time.sleep(5)  # Check every 5 seconds
```

### Performance Optimization

#### Async Operations
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncModelService:
    """Asynchronous model service."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def load_model_async(self, file_path: Path) -> bool:
        """Load model asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            
            # Run CPU-bound operation in thread pool
            model_data = await loop.run_in_executor(
                self.executor, 
                self._parse_model, 
                file_path
            )
            
            # Store in cache
            await self._cache_model_async(model_data)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            return False
    
    def _parse_model(self, file_path: Path) -> Model:
        """Parse model file (CPU-bound)."""
        # Implementation here
        pass
```

#### Database Optimization
```python
class OptimizedModelRepository(IModelRepository):
    """Optimized model repository."""
    
    def __init__(self, database: IDatabase):
        self._database = database
        self._connection_pool = ConnectionPool(database)
    
    def batch_insert(self, models: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple models efficiently."""
        with self._connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Use transaction for batch insert
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                model_ids = []
                for model_data in models:
                    cursor.execute(
                        "INSERT INTO models (data) VALUES (?)",
                        (json.dumps(model_data),)
                    )
                    model_ids.append(cursor.lastrowid)
                
                cursor.execute("COMMIT")
                return model_ids
                
            except Exception:
                cursor.execute("ROLLBACK")
                raise
```

## API Reference

### Core Interfaces

#### IModelService
```python
class IModelService(ABC):
    """Interface for model management services."""
    
    @abstractmethod
    def load_model(self, file_path: Path, progress_callback: Optional[callable] = None) -> bool:
        """Load a 3D model from file.
        
        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if model was loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            True if model was unloaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a loaded model by ID.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            The model object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs.
        
        Returns:
            List of currently loaded model IDs
        """
        pass
```

#### IParser
```python
class IParser(ABC):
    """Interface for 3D model file parsers."""
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if parser can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def parse(self, file_path: Path, progress_callback: Optional[callable] = None) -> Any:
        """Parse a 3D model file.
        
        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Parsed model data
            
        Raises:
            ParseError: If the file cannot be parsed
            FileNotFoundError: If the file doesn't exist
        """
        pass
    
    @abstractmethod
    def get_model_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic information about the model file.
        
        Args:
            file_path: Path to the model file
            
        Returns:
            Dictionary containing model information
        """
        pass
```

### Service Implementations

#### ModelService
```python
class ModelService(IModelService):
    """Service for managing 3D model operations.
    
    This service provides a high-level interface for loading, unloading,
    and managing 3D models in the application. It handles file parsing,
    caching, and metadata management.
    
    Example:
        >>> service = ModelService(...)
        >>> success = service.load_model(Path("model.stl"))
        >>> if success:
        ...     model = service.get_model("model_id")
    """
    
    def __init__(
        self,
        model_repository: IModelRepository,
        metadata_repository: IMetadataRepository,
        parser_registry: IParserRegistry,
        format_detector: IFormatDetector,
        cache: IModelCache
    ):
        """Initialize the model service.
        
        Args:
            model_repository: Repository for model data
            metadata_repository: Repository for metadata
            parser_registry: Registry of available parsers
            format_detector: File format detector
            cache: Model cache instance
        """
        self._model_repository = model_repository
        self._metadata_repository = metadata_repository
        self._parser_registry = parser_registry
        self._format_detector = format_detector
        self._cache = cache
        self._logger = logging.getLogger(__name__)
```

## Contributing Guidelines

### Getting Started

1. **Fork the Repository**: Create your own fork of the project
2. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Make Changes**: Follow coding standards and add tests
4. **Run Tests**: Ensure all tests pass
5. **Submit PR**: Create pull request with detailed description

### Code Review Process

#### Before Submitting PR
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No pylint warnings
- [ ] Type hints are complete
- [ ] Commit messages follow convention

#### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### Release Process

#### Version Numbering
We follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

#### Release Checklist
- [ ] Update version numbers
- [ ] Update changelog
- [ ] Run full test suite
- [ ] Create release branch
- [ ] Create GitHub release
- [ ] Build and test installer
- [ ] Update documentation

### Communication

#### Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

#### Issue Templates
Use provided templates for:
- Bug reports
- Feature requests
- Documentation improvements
- Performance issues

### Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor appreciation posts

---

## Conclusion

This developer guide provides comprehensive information for contributing to Candy-Cadence. Following these guidelines ensures code quality, maintainability, and consistency across the project.

For questions or suggestions about this guide, please:
1. Check existing documentation
2. Search GitHub issues and discussions
3. Create a new issue with the "question" label
4. Contact the development team

Happy coding!