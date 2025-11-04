# Digital Workshop - Developer Guide

## 🎯 Purpose

This guide provides comprehensive information for developers working on Digital Workshop, including setup, architecture, coding standards, and development workflows.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8-3.12** (64-bit)
- **Git** for version control
- **pip** or **conda** for package management
- **Visual Studio Code** or similar IDE

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd digital-workshop
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python run.py
   ```

---

## 📁 Project Structure

```
digital-workshop/
├── src/
│   ├── core/                 # Core application logic
│   │   ├── application.py
│   │   ├── database/         # Database layer
│   │   ├── logging_config.py
│   │   └── ...
│   ├── gui/                  # User interface
│   │   ├── main_window.py
│   │   ├── widgets/
│   │   └── ...
│   ├── parsers/              # File format parsers
│   │   ├── stl_parser.py
│   │   ├── obj_parser.py
│   │   └── ...
│   ├── utils/                # Utility functions
│   │   ├── file_operations.py
│   │   └── ...
│   ├── installer/            # Installation system
│   │   ├── modes/
│   │   ├── managers/
│   │   └── ...
│   └── main.py               # Application entry point
├── tests/                    # Unit and integration tests
├── config/                   # Configuration files
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
├── build.py                  # Build script
└── run.py                    # Quick start script
```

---

## 💻 Development Workflow

### 1. Creating a New Feature

**Step 1: Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

**Step 2: Implement Feature**
- Follow coding standards (see LINTING_STANDARDS.md)
- Write unit tests
- Update documentation

**Step 3: Run Tests**
```bash
python -m pytest tests/ -v
```

**Step 4: Commit Changes**
```bash
git add .
git commit -m "feat: description of your feature"
```

**Step 5: Create Pull Request**
- Push to remote
- Create PR with description
- Request review

### 2. Fixing a Bug

**Step 1: Create Bug Fix Branch**
```bash
git checkout -b bugfix/bug-description
```

**Step 2: Write Test for Bug**
- Create test that reproduces bug
- Verify test fails

**Step 3: Fix Bug**
- Implement fix
- Verify test passes

**Step 4: Run Full Test Suite**
```bash
python -m pytest tests/ -v
```

**Step 5: Commit and Push**
```bash
git add .
git commit -m "fix: description of bug fix"
git push origin bugfix/bug-description
```

---

## 🧪 Testing

### Running Tests

**All Tests**
```bash
python -m pytest tests/ -v
```

**Specific Test File**
```bash
python -m pytest tests/test_installer.py -v
```

**Specific Test**
```bash
python -m pytest tests/test_installer.py::TestInstaller::test_full_install -v
```

**With Coverage**
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

**Test Structure**
```python
import pytest
from src.module import MyClass

class TestMyClass:
    def setup_method(self):
        """Setup before each test"""
        self.obj = MyClass()
    
    def test_feature(self):
        """Test description"""
        result = self.obj.method()
        assert result == expected_value
    
    def teardown_method(self):
        """Cleanup after each test"""
        pass
```

---

## 📝 Coding Standards

### Python Style
- **PEP 8** compliance
- **Type Hints** for all functions
- **Docstrings** for all classes and functions
- **Logging** instead of print statements

### Naming Conventions
- **Classes**: PascalCase (e.g., `DatabaseManager`)
- **Functions**: snake_case (e.g., `get_project_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_FILE_SIZE`)
- **Private**: Leading underscore (e.g., `_internal_method`)

### Code Quality
- **Linting**: Run `pylint` before committing
- **Formatting**: Use `black` for code formatting
- **Type Checking**: Use `mypy` for type validation
- **Complexity**: Keep functions focused and simple

### Logging
```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Use lazy % formatting
logger.info("Processing file: %s", filename)
logger.error("Error occurred: %s", str(error))
logger.debug("Debug info: %s", debug_data)
```

---

## 🗄️ Database Development

### Adding a New Table

1. **Create Migration**
   ```python
   # In src/core/database/migrations/
   def migrate_up(conn):
       cursor = conn.cursor()
       cursor.execute("""
           CREATE TABLE new_table (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
       """)
       conn.commit()
   ```

2. **Create Repository**
   ```python
   # In src/core/database/repositories/
   class NewTableRepository:
       def __init__(self, get_connection):
           self.get_connection = get_connection
       
       def create(self, data):
           with self.get_connection() as conn:
               cursor = conn.cursor()
               cursor.execute("INSERT INTO new_table ...")
               conn.commit()
   ```

3. **Update DatabaseManager**
   ```python
   self._new_table_repo = NewTableRepository(self._db_ops.get_connection)
   ```

---

## 🎨 GUI Development

### Creating a New Widget

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

class MyWidget(QWidget):
    """Custom widget for specific functionality"""
    
    # Define signals
    data_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Create UI components"""
        layout = QVBoxLayout()
        self.button = QPushButton("Click Me")
        layout.addWidget(self.button)
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect signals and slots"""
        self.button.clicked.connect(self.on_button_clicked)
    
    def on_button_clicked(self):
        """Handle button click"""
        self.data_changed.emit("Button clicked")
```

---

## 🔧 Common Development Tasks

### Adding a New File Parser

1. Create parser class in `src/parsers/`
2. Implement `parse()` method
3. Add to parser registry
4. Write tests
5. Update documentation

### Adding a New Installation Mode

1. Create mode class in `src/installer/modes/`
2. Implement `execute()` method
3. Add to installer registry
4. Write tests
5. Update documentation

### Adding a New Database Repository

1. Create repository class in `src/core/database/repositories/`
2. Implement CRUD methods
3. Add to DatabaseManager
4. Write tests
5. Update documentation

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Using Python Debugger
```python
import pdb
pdb.set_trace()  # Breakpoint
```

### Using IDE Debugger
- Set breakpoints in IDE
- Run with debugger
- Step through code

---

## 📚 Documentation

### Code Documentation
- **Docstrings**: Describe what, why, and how
- **Comments**: Explain complex logic
- **Type Hints**: Document parameter and return types
- **Examples**: Show usage examples

### Updating Documentation
1. Update relevant .md files
2. Update DOCUMENTATION_INDEX.md if needed
3. Verify links work
4. Commit with documentation changes

---

## 🚀 Performance Optimization

### Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Optimization
- Use generators for large datasets
- Clean up resources properly
- Avoid circular references
- Profile memory usage

---

## 🔐 Security Considerations

### Input Validation
- Validate all user input
- Sanitize file paths
- Check file types
- Verify data integrity

### Secure Coding
- Use parameterized queries
- Avoid hardcoded secrets
- Use secure random generation
- Implement proper error handling

---

## 📞 Getting Help

- **Documentation**: See docs/ folder
- **Code Examples**: Check tests/ folder
- **Architecture**: See SYSTEM_ARCHITECTURE.md
- **Standards**: See LINTING_STANDARDS.md

---

## ✅ Development Checklist

Before committing code:
- [ ] Code follows standards
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No linting errors
- [ ] No type errors
- [ ] Logging implemented
- [ ] Error handling complete
- [ ] Performance acceptable

---

## 🎓 Learning Resources

- **Python**: https://docs.python.org/3/
- **PySide6**: https://doc.qt.io/qtforpython/
- **VTK**: https://vtk.org/documentation/
- **SQLite**: https://www.sqlite.org/docs.html
- **Git**: https://git-scm.com/doc

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Current

