# Code Quality & Linting Standards

This document outlines the code quality standards and linting practices for the Digital Workshop project.

## Overview

We maintain high code quality through automated linting, formatting, and security checks. All code must pass these checks before being merged.

## Tools & Configuration

### 1. **Black** - Code Formatter
- **Purpose**: Automatic code formatting for consistency
- **Line Length**: 100 characters
- **Configuration**: `.pre-commit-config.yaml`
- **Command**: `black --line-length=100 src/`

### 2. **Pylint** - Code Analysis
- **Purpose**: Detect errors, enforce coding standards
- **Minimum Score**: 8.0/10
- **Configuration**: `.pylintrc` (if present)
- **Command**: `pylint src --recursive=y --fail-under=8.0`

### 3. **MyPy** - Type Checking
- **Purpose**: Static type checking for Python
- **Configuration**: `mypy.ini` (if present)
- **Command**: `mypy src --ignore-missing-imports`

### 4. **Bandit** - Security Scanning
- **Purpose**: Identify common security issues
- **Configuration**: `.bandit`
- **Command**: `bandit -r src`

### 5. **Autoflake** - Import Cleanup
- **Purpose**: Remove unused imports automatically
- **Command**: `autoflake --in-place --remove-all-unused-imports --recursive src/`

### 6. **pip-audit** - Dependency Auditing
- **Purpose**: Check for known vulnerabilities in dependencies
- **Command**: `python -m pip_audit`

## Pre-commit Hooks

Pre-commit hooks automatically run linting checks before each commit. To set up:

```bash
pip install pre-commit
pre-commit install
```

Hooks will run on:
- Code formatting (black)
- Import cleanup (autoflake)
- Linting (pylint - errors only)
- Type checking (mypy)
- Security checks (bandit)
- File validation (YAML, JSON, merge conflicts)

## CI/CD Pipeline

GitHub Actions automatically runs linting checks on:
- All pushes to `main` and `develop` branches
- All pull requests

See `.github/workflows/linting.yml` for configuration.

## Common Issues & Fixes

### Line Too Long
**Issue**: Line exceeds 100 characters
**Fix**: Run `black --line-length=100 src/`

### Unused Imports
**Issue**: Import statement not used
**Fix**: Run `autoflake --in-place --remove-all-unused-imports --recursive src/`

### Missing Docstrings
**Issue**: Function/class missing documentation
**Fix**: Add docstring following Google style guide

### Broad Exception Handling
**Issue**: `except Exception as e:` catches too broadly
**Fix**: Catch specific exceptions: `except (OSError, IOError, ValueError) as e:`

### Type Hints
**Issue**: Missing type annotations
**Fix**: Add type hints to function signatures and variables

## Best Practices

1. **Run linting locally before pushing**
   ```bash
   black --line-length=100 src/
   pylint src --recursive=y
   mypy src --ignore-missing-imports
   ```

2. **Use meaningful variable names**
   - Avoid single-letter variables (except in loops)
   - Use descriptive names that indicate purpose

3. **Write docstrings**
   - Use Google style docstrings
   - Include Args, Returns, Raises sections

4. **Handle exceptions specifically**
   - Catch specific exception types
   - Log exceptions with context

5. **Keep functions small**
   - Aim for functions under 50 lines
   - Break complex logic into smaller functions

6. **Use type hints**
   - Add type hints to all function parameters
   - Add return type hints

## Linting Score Targets

- **Current Score**: 8.45/10
- **Target Score**: 8.5+/10
- **Minimum Acceptable**: 8.0/10

## Continuous Improvement

Linting violations are tracked and prioritized:

1. **Critical** (Errors): Must fix before merge
2. **High** (Warnings): Should fix before merge
3. **Medium** (Style): Fix in next refactoring cycle
4. **Low** (Info): Nice to have improvements

## Resources

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pylint Documentation](https://pylint.pycqa.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)

