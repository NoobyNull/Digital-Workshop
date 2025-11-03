# Code Refactoring Guide

## Overview

This guide provides step-by-step instructions for refactoring large modules into smaller, more maintainable components.

---

## Phase 1: Quick Wins (2-3 hours)

### 1.1 Fix Unused Imports

**File**: `src/core/centralized_logging_service.py`

**Current Issues**:
```python
import json  # Unused
import os  # Unused
import sys  # Unused
import traceback  # Unused
from pathlib import Path  # Unused
from .enhanced_error_handler import ErrorContext, ErrorCategory, ErrorSeverity  # Unused
from .exceptions import CandyCadenceException, get_user_friendly_message, ...  # Unused
```

**Action**:
1. Remove all unused imports
2. Keep only imports actually used in the module
3. Run: `python -m autoflake --remove-all-unused-imports --in-place src/core/centralized_logging_service.py`

### 1.2 Fix Whitespace Issues

**Command**:
```bash
# Remove trailing whitespace
python -c "
import re
from pathlib import Path

for py_file in Path('src').rglob('*.py'):
    content = py_file.read_text(encoding='utf-8', errors='ignore')
    # Remove trailing whitespace
    content = re.sub(r'[ \t]+\n', '\n', content)
    # Ensure file ends with newline
    if content and not content.endswith('\n'):
        content += '\n'
    py_file.write_text(content, encoding='utf-8')
    print(f'Fixed: {py_file}')
"
```

### 1.3 Fix pyproject.toml

**Current**:
```toml
[tool.black]
line-length = 120
target-version = ['py312']
```

**Issue**: Unescaped backslashes in paths

**Fix**:
```toml
[tool.black]
line-length = 120
target-version = ['py312']
# Use forward slashes or raw strings
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
)/
'''
```

---

## Phase 2: Formatting (1-2 hours)

### 2.1 Run Black Formatter

```bash
# Format all Python files
python -m black src --line-length=120

# Check what would change
python -m black src --line-length=120 --check --diff
```

### 2.2 Fix Import Ordering

```bash
# Use isort to organize imports
python -m isort src --profile black --line-length 120
```

### 2.3 Fix Docstrings

**Issues**:
- Missing periods in first line (D400)
- Incorrect imperative mood (D401)
- Missing blank line after class docstring (D204)

**Example Fix**:
```python
# Before
class MyClass:
    """This is my class"""
    def method(self):
        """Returns something"""
        pass

# After
class MyClass:
    """This is my class."""

    def method(self):
        """Return something."""
        pass
```

**Command**:
```bash
python -m docformatter --in-place --recursive src
```

---

## Phase 3: Refactor Large Modules (20-30 hours)

### 3.1 Refactor preferences.py (2415 lines)

**Current Structure**:
```
src/gui/preferences.py (2415 lines)
├── PreferencesDialog class
├── Multiple tab implementations
├── Settings management
└── Validation logic
```

**Target Structure**:
```
src/gui/preferences/
├── __init__.py
├── preferences_dialog.py (300 lines)
├── tabs/
│   ├── __init__.py
│   ├── general_tab.py (250 lines)
│   ├── appearance_tab.py (300 lines)
│   ├── ai_tab.py (250 lines)
│   ├── advanced_tab.py (200 lines)
│   └── base_tab.py (100 lines)
├── models/
│   ├── __init__.py
│   ├── preference_model.py (150 lines)
│   └── settings_manager.py (200 lines)
└── validators/
    ├── __init__.py
    └── preference_validator.py (150 lines)
```

**Steps**:
1. Create `src/gui/preferences/` directory
2. Extract each tab into separate file
3. Create base tab class for common functionality
4. Extract settings management to separate module
5. Update imports in main_window.py
6. Run tests to verify

### 3.2 Refactor main_window.py (2398 lines)

**Current Structure**:
```
src/gui/main_window.py (2398 lines)
├── MainWindow class
├── Menu setup
├── Toolbar setup
├── Dock widgets
└── Event handlers
```

**Target Structure**:
```
src/gui/main_window/
├── __init__.py
├── main_window.py (400 lines - core)
├── menu_manager.py (already exists)
├── toolbar_manager.py (200 lines)
├── dock_manager.py (300 lines)
├── event_handlers.py (200 lines)
└── docks/
    ├── __init__.py
    ├── model_library_dock.py (300 lines)
    ├── properties_dock.py (250 lines)
    ├── metadata_dock.py (200 lines)
    └── base_dock.py (100 lines)
```

**Steps**:
1. Create `src/gui/main_window/` directory
2. Move menu_manager.py into directory
3. Extract toolbar setup to toolbar_manager.py
4. Extract dock setup to dock_manager.py
5. Extract event handlers to event_handlers.py
6. Create base dock class
7. Extract each dock widget
8. Update imports
9. Run tests

### 3.3 Refactor model_library.py (1818 lines)

**Target Structure**:
```
src/gui/model_library/
├── __init__.py
├── model_library_widget.py (400 lines)
├── search_manager.py (250 lines)
├── filter_manager.py (200 lines)
├── tree_manager.py (300 lines)
├── context_menu.py (150 lines)
└── models/
    ├── __init__.py
    └── library_model.py (200 lines)
```

---

## Phase 4: Type Hints (5-10 hours)

### 4.1 Add Type Hints

```bash
# Check current type hint coverage
python -m mypy src --strict --no-error-summary 2>&1 | grep -c "error:"

# Add type hints incrementally
# Start with public APIs
```

**Example**:
```python
# Before
def load_model(path):
    """Load a 3D model from file."""
    pass

# After
from pathlib import Path
from typing import Optional
from src.core.data_structures import Model

def load_model(path: Path) -> Optional[Model]:
    """Load a 3D model from file.
    
    Args:
        path: Path to the model file
        
    Returns:
        Loaded model or None if loading failed
    """
    pass
```

---

## Phase 5: Testing (5-10 hours)

### 5.1 Update Tests

```bash
# Run tests after refactoring
python -m pytest tests -v --tb=short

# Check coverage
python -m pytest tests --cov=src --cov-report=html
```

### 5.2 Add Tests for New Modules

- Test each extracted module independently
- Test integration between modules
- Verify no functionality lost

---

## Automation Scripts

### Script 1: Fix All Formatting

```bash
#!/bin/bash
# fix_formatting.sh

echo "Fixing formatting..."

# Remove trailing whitespace
python -c "
import re
from pathlib import Path
for py_file in Path('src').rglob('*.py'):
    content = py_file.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'[ \t]+\n', '\n', content)
    if content and not content.endswith('\n'):
        content += '\n'
    py_file.write_text(content, encoding='utf-8')
"

# Format with black
python -m black src --line-length=120

# Sort imports
python -m isort src --profile black --line-length 120

# Fix docstrings
python -m docformatter --in-place --recursive src

# Remove unused imports
python -m autoflake --remove-all-unused-imports --in-place --recursive src

echo "Done!"
```

### Script 2: Check Code Quality

```bash
#!/bin/bash
# check_quality.sh

echo "Checking code quality..."

# Lint
python -m flake8 src --max-line-length=120

# Type check
python -m mypy src --ignore-missing-imports

# Test
python -m pytest tests -v --tb=short

echo "Done!"
```

---

## Checklist

### Before Refactoring
- [ ] All tests passing
- [ ] Code committed to git
- [ ] Create feature branch

### During Refactoring
- [ ] Extract one module at a time
- [ ] Run tests after each extraction
- [ ] Update imports
- [ ] Update documentation

### After Refactoring
- [ ] All tests passing
- [ ] Code review
- [ ] Update documentation
- [ ] Merge to main branch

---

## Timeline

| Phase | Task | Hours | Status |
|-------|------|-------|--------|
| 1 | Quick wins | 2-3 | Ready |
| 2 | Formatting | 1-2 | Ready |
| 3 | Refactor preferences.py | 8-10 | Planned |
| 3 | Refactor main_window.py | 8-10 | Planned |
| 3 | Refactor model_library.py | 6-8 | Planned |
| 4 | Type hints | 5-10 | Planned |
| 5 | Testing | 5-10 | Planned |
| **Total** | | **40-60** | |

---

## Success Criteria

- ✅ All modules < 500 lines
- ✅ All tests passing
- ✅ Code coverage > 80%
- ✅ No linting errors
- ✅ Type hints on all public APIs
- ✅ Documentation updated

