# Digital Workshop Project Structure Guide

## Overview

This document provides a comprehensive guide to the Digital Workshop project structure, which has been optimized for maintainability, scalability, and developer productivity following the October 2025 root directory cleanup.

## Directory Structure

```
d:/Digital Workshop/
├── Essential Project Files (30 total)
├── src/                            # Source code
├── tests/                           # Test suite
├── docs/                            # Documentation
├── config/                          # Configuration files
├── samples/                         # Sample files and demos
├── tools/                           # Development tools
├── reports/                         # Generated reports
├── build/                           # Build artifacts
├── archive/                         # Archived temporary files
├── resources/                       # Project resources
├── scripts/                         # Utility scripts
├── specs/                           # Specifications
└── shutdown_analysis_reports/         # Specialized reports
```

## Essential Project Files

The root directory contains only essential project files (30 total):

| File | Purpose | Importance |
|-------|---------|------------|
| [`README.md`](README.md) | Project overview and getting started | Critical |
| [`pyproject.toml`](pyproject.toml) | Python project configuration | Critical |
| [`requirements.txt`](requirements.txt) | Production dependencies | Critical |
| [`requirements_testing.txt`](requirements_testing.txt) | Testing dependencies | Critical |
| [`requirements-conda.yml`](requirements-conda.yml) | Conda environment setup | Critical |
| [`.gitignore`](.gitignore) | Git configuration | Critical |
| [`.pylintrc`](.pylintrc) | Code quality configuration | High |
| [`pytest.ini`](pytest.ini) | Testing configuration | High |
| [`run.py`](run.py) | Application entry point | Critical |
| [`build.py`](build.py) | Build script | High |
| [`package.json`](package.json) | Node.js dependencies | Medium |
| [`package-lock.json`](package-lock.json) | Node.js lock file | Medium |

## Core Directories

### src/ - Source Code

The application source code is organized into logical modules:

```
src/
├── core/                            # Core application logic
│   ├── interfaces/                   # Interface definitions
│   └── services/                     # Service implementations
├── gui/                             # User interface components
│   ├── main_window_components/         # Main window components
│   ├── import_components/             # Import functionality
│   ├── material_components/            # Material management
│   ├── search_components/             # Search functionality
│   ├── theme/                       # Theme management
│   ├── help_system/                  # Help system
│   └── layout/                      # Layout management
├── parsers/                         # File format parsers
├── utils/                           # Utility functions
├── resources/                       # Application resources
│   ├── backgrounds/                 # Background images
│   ├── materials/                   # Material definitions
│   ├── styles/                      # UI styles
│   └── ToolLib/                    # Tool library
└── ui/                             # UI definitions
```

### tests/ - Test Suite

Comprehensive test suite organized by type:

```
tests/
├── unit/                            # Unit tests
├── integration/                      # Integration tests
├── framework/                       # Test framework
├── parsers/                         # Parser tests
├── persistence/                     # Persistence tests
├── themes/                          # Theme tests
├── performance/                     # Performance tests
└── runner/                          # Test runner
```

### docs/ - Documentation

Project documentation organized by purpose:

```
docs/
├── guides/                          # User guides
├── architecture/                     # Architecture documentation
└── reports/                         # Technical reports
```

### config/ - Configuration Files

All configuration files centralized:

```
config/
├── quality_config.yaml              # Quality settings
├── test_framework_config.json         # Test framework config
├── installer.nsi                    # Installer configuration
└── pyinstaller.spec                 # PyInstaller config
```

### samples/ - Sample Files and Demos

Sample files organized by type:

```
samples/
├── code/                            # Code samples
│   ├── sample_large_module.py
│   └── sample_small_module.py
├── reports/                          # Sample reports
└── sample/                           # Sample data
```

### tools/ - Development Tools

Development and maintenance tools:

```
tools/
├── quality/                         # Quality assurance tools
├── analysis/                        # Analysis tools
├── debug/                           # Debug utilities
├── exceptions/                      # Exception tools
├── migration/                       # Migration tools
└── demos/                           # Demo tools
```

### reports/ - Generated Reports

Automatically generated reports organized by type:

```
reports/
├── json/                            # JSON reports
├── html/                            # HTML reports
├── analysis/                        # Analysis files
├── comprehensive/                   # Comprehensive reports
├── performance/                     # Performance data
├── quality/                         # Quality reports
└── test_results/                    # Test results
```

### build/ - Build Artifacts

Build-related files:

```
build/
├── installer/                        # Installation files
└── logs/                            # Build logs
```

### archive/ - Archived Temporary Files

Temporary files moved during cleanup:

```
archive/
├── mon, n, P, validate, quality    # Temporary files
├── -p/                              # Temporary directory
└── .augment/                         # Development augmentation
```

## File Organization Principles

### 1. Essential Files in Root

Only essential project files remain in the root directory:
- Project configuration files
- Dependency definitions
- Entry points and build scripts
- Core documentation

### 2. Logical Categorization

Files are organized by function and purpose:
- **Source code** in `src/`
- **Tests** in `tests/`
- **Documentation** in `docs/`
- **Configuration** in `config/`
- **Tools** in `tools/`

### 3. Separation of Concerns

Clear separation between:
- **Runtime code** vs. **development tools**
- **Source files** vs. **generated files**
- **Configuration** vs. **implementation**
- **Tests** vs. **production code**

## Navigation Guide

### For New Developers

1. **Start with README.md** for project overview
2. **Review docs/architecture/** for system understanding
3. **Examine src/core/** for core logic
4. **Check tests/unit/** for usage examples
5. **Use tools/quality/** for code quality

### For Feature Development

1. **Implement in src/** following existing patterns
2. **Add tests in tests/** appropriate category
3. **Update documentation in docs/**
4. **Run quality tools from tools/quality/**

### For Maintenance

1. **Check build/logs/** for build issues
2. **Review reports/** for analysis results
3. **Use tools/debug/** for troubleshooting
4. **Archive old files in archive/**

## File Naming Conventions

### Source Files
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

### Test Files
- **Unit tests**: `test_<module_name>.py`
- **Integration tests**: `test_<feature>_integration.py`
- **Performance tests**: `test_<feature>_performance.py`

### Documentation Files
- **Guides**: `DESCRIPTIVE_NAME.md`
- **Architecture**: `COMPONENT_NAME.md`
- **Reports**: `report_type_description.md`

## Import Patterns

### Relative Imports
```python
# Within same package
from .module import function

# From parent package
from ..parent_module import Class
```

### Absolute Imports
```python
# From project root
from src.core.services import ModelService
from src.gui.main_window import MainWindow
```

### Test Imports
```python
# Importing modules to test
from src.parsers.stl_parser import STLParser
from src.utils.file_utils import read_file
```

## Configuration Management

### Application Configuration
- **Primary**: [`config/quality_config.yaml`](config/quality_config.yaml)
- **Testing**: [`config/test_framework_config.json`](config/test_framework_config.json)
- **Build**: [`config/pyinstaller.spec`](config/pyinstaller.spec)

### Development Configuration
- **Linting**: [`.pylintrc`](.pylintrc)
- **Testing**: [`pytest.ini`](pytest.ini)
- **Version Control**: [`.gitignore`](.gitignore)

## Build and Deployment

### Build Process
1. **Source**: `src/` directory
2. **Configuration**: [`build.py`](build.py) script
3. **Output**: `build/installer/` directory
4. **Logs**: `build/logs/` directory

### Dependencies
- **Production**: [`requirements.txt`](requirements.txt)
- **Testing**: [`requirements_testing.txt`](requirements_testing.txt)
- **Conda**: [`requirements-conda.yml`](requirements-conda.yml)
- **Node.js**: [`package.json`](package.json)

## Maintenance Guidelines

### Regular Tasks

1. **Weekly**: Review `build/logs/` for issues
2. **Monthly**: Check `reports/quality/` for quality metrics
3. **Quarterly**: Review `archive/` and clean if needed
4. **As needed**: Update `docs/` with new features

### File Organization

1. **New source files**: Add to appropriate `src/` subdirectory
2. **New tests**: Add to appropriate `tests/` subdirectory
3. **New tools**: Add to appropriate `tools/` subdirectory
4. **New documentation**: Add to appropriate `docs/` subdirectory

### Cleanup Procedures

1. **Temporary files**: Move to `archive/`
2. **Old reports**: Archive in `reports/archive/`
3. **Deprecated code**: Document before removal
4. **Build artifacts**: Clean with `python build.py --clean-only`

## Recent Changes

### Root Directory Cleanup (October 2025)

The project underwent a significant reorganization:

- **Reduced root files from 100+ to 30** (70% reduction)
- **Organized files into logical directories**
- **Preserved all functionality**
- **Improved developer experience**

For detailed information, see:
- [`FINAL_CLEANUP_VALIDATION_REPORT.md`](FINAL_CLEANUP_VALIDATION_REPORT.md)
- [`CLEANUP_EXECUTION_REPORT.md`](CLEANUP_EXECUTION_REPORT.md)

## Best Practices

### File Placement
- **Keep root clean** - only essential files
- **Follow existing patterns** - maintain consistency
- **Use appropriate directories** - logical categorization
- **Document new structures** - keep guides updated

### Code Organization
- **Separate concerns** - clear module boundaries
- **Use interfaces** - define contracts
- **Implement tests** - ensure quality
- **Document changes** - maintain clarity

### Development Workflow
- **Follow established patterns** - consistency
- **Use quality tools** - maintain standards
- **Test thoroughly** - ensure reliability
- **Review before commit** - prevent issues

## Troubleshooting

### Common Issues

1. **Import Errors**: Check file locations and import paths
2. **Build Failures**: Review `build/logs/` for details
3. **Test Failures**: Verify test environment setup
4. **Configuration Issues**: Check `config/` files

### Getting Help

1. **Documentation**: Check `docs/` directory
2. **Examples**: Review `samples/` directory
3. **Tools**: Use `tools/debug/` utilities
4. **Logs**: Examine `build/logs/` and `reports/`

## Conclusion

This project structure provides a clean, organized foundation for development, testing, and maintenance. The logical organization improves developer productivity, reduces cognitive load, and enhances maintainability.

For questions or suggestions about the project structure, refer to the development team or create an issue in the project repository.