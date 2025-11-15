# Digital Workshop

A comprehensive 3D modeling and CNC workflow application designed for woodworkers, makers, and digital fabricators.

## Overview

Digital Workshop is a powerful desktop application that provides tools for 3D model viewing, manipulation, and CNC preparation. It supports multiple file formats, advanced visualization, and integrated workflow management for digital fabrication projects.

## Quick Start

### Prerequisites

- **Python 3.8-3.12** (64-bit)
- **PySide6 6.0.0+**
- **VTK 9.2.0+**
- **SQLite 3.0+**

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd digital-workshop
   ```

2. Install dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Using conda (recommended)
   conda env create -f requirements-conda.yml
   conda activate digital-workshop
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

The Digital Workshop project follows a clean, organized structure designed for maintainability and scalability:

```
d:/Digital Workshop/
├── Essential Project Files
│   ├── README.md                    # This file
│   ├── pyproject.toml               # Python project configuration
│   ├── requirements.txt              # Production dependencies
│   ├── requirements_testing.txt       # Testing dependencies
│   ├── requirements-conda.yml        # Conda environment setup
│   ├── .gitignore                   # Git configuration
│   ├── .pylintrc                   # Code quality configuration
│   ├── pytest.ini                   # Testing configuration
│   ├── run.py                       # Application entry point
│   ├── build.py                     # Build script
│   ├── package.json                 # Node.js dependencies
│   └── package-lock.json            # Node.js lock file
│
├── src/                            # Source code
│   ├── core/                        # Core application logic
│   ├── gui/                         # User interface components
│   ├── parsers/                     # File format parsers
│   ├── utils/                       # Utility functions
│   └── resources/                   # Application resources
│
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   ├── integration/                  # Integration tests
│   ├── framework/                    # Test framework
│   ├── parsers/                     # Parser tests
│   ├── persistence/                 # Persistence tests
│   ├── themes/                      # Theme tests
│   └── performance/                 # Performance tests
│
├── docs/                            # Documentation
│   ├── guides/                      # User guides
│   ├── architecture/                 # Architecture documentation
│   └── reports/                     # Technical reports
│
├── config/                          # Configuration files
│   ├── quality_config.yaml           # Quality settings
│   ├── test_framework_config.json    # Test framework config
│   ├── installer.nsi                # Installer configuration
│   └── pyinstaller.spec             # PyInstaller config
│
├── samples/                         # Sample files and demos
│   ├── code/                        # Code samples
│   ├── reports/                     # Sample reports
│   └── sample/                      # Sample data
│
├── tools/                           # Development tools
│   ├── quality/                     # Quality assurance tools
│   ├── analysis/                    # Analysis tools
│   ├── debug/                       # Debug utilities
│   ├── exceptions/                  # Exception tools
│   ├── migration/                   # Migration tools
│   └── demos/                       # Demo tools
│
├── reports/                         # Generated reports
│   ├── json/                        # JSON reports
│   ├── html/                        # HTML reports
│   ├── analysis/                    # Analysis files
│   ├── comprehensive/                # Comprehensive reports
│   ├── performance/                 # Performance data
│   ├── quality/                     # Quality reports
│   └── test_results/                # Test results
│
├── build/                           # Build artifacts
│   ├── installer/                   # Installation files
│   └── logs/                        # Build logs
│
├── archive/                         # Archived temporary files
│
├── resources/                       # Project resources
│   ├── icons/                       # Application icons
│   └── backgrounds/                 # Background images
│
├── scripts/                         # Utility scripts
├── specs/                           # Specifications
└── shutdown_analysis_reports/         # Specialized reports
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
   ```bash
   pip install -r requirements_testing.txt
   ```

2. Run tests to verify setup:
   ```bash
   pytest tests/
   ```

3. Build the application:
   ```bash
   python build.py
   ```

### Code Quality

The project maintains high code quality standards:

- **Linting**: Configured with `.pylintrc`
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Inline docs and guides in `docs/`
- **Quality Gates**: Automated quality checks in `tools/quality/`

### Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest tests/ --cov=src
```

## Build and Distribution

### Building the Application

```bash
# Standard build
python build.py

# Build without tests
python build.py --no-tests

# Build without installer
python build.py --no-installer

# Clean build only
python build.py --clean-only
```

### Creating Installer

The installer is created automatically during build. For custom installer configuration, see [`config/installer.nsi`](config/installer.nsi).

## Configuration

### Application Configuration

- **Quality Settings**: [`config/quality_config.yaml`](config/quality_config.yaml)
- **Test Framework**: [`config/test_framework_config.json`](config/test_framework_config.json)

### Development Configuration

- **Python Linting**: [`.pylintrc`](.pylintrc)
- **Testing**: [`pytest.ini`](pytest.ini)
- **Git**: [`.gitignore`](.gitignore)

### Logging Configuration

Digital Workshop features a standardized logging system with structured JSON output, rotation, and metadata injection. The logging system is managed by a singleton `LoggingManager` that ensures consistent handler configuration across the entire application.

#### LoggingProfile Configuration

The logging behavior is controlled by a `LoggingProfile` dataclass with the following properties:

- **log_level**: Set the minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: "INFO"
- **enable_console**: Enable console output in addition to file logging. Default: False
- **human_readable**: Use human-readable text format instead of JSON. Default: False
- **log_dir**: Directory for log files (resolved via `path_manager`). Default: App data/logs
- **max_bytes**: Maximum log file size before rotation. Default: 10MB
- **backup_count**: Number of backup files to retain. Default: 5
- **correlation_id**: Optional correlation identifier for request tracking

#### Command Line Flags

The logging system can be configured via command line flags:

```bash
# Set log level
python main.py --log-level DEBUG    # Verbose logging
python main.py --log-level INFO     # Standard logging (default)
python main.py --log-level WARNING  # Minimal logging

# Enable console output
python main.py --log-console        # Show logs in console

# Use human-readable format
python main.py --log-human          # Human-readable instead of JSON

# Combine options
python main.py --debug --log-console --log-human
```

#### Log Output Locations

- **Main Application Logs**: `{app_data}/logs/Log - MMDDYY-HH-MM-SS LEVEL.txt` (timestamp-based rotation)
- **Security Events**: `{app_data}/logs/security.log` (dedicated security audit trail)
- **Performance Metrics**: `{app_data}/logs/performance.log` (performance monitoring data)
- **Errors**: `{app_data}/logs/errors.log` (isolated error tracking)

#### Structured Log Format

When using the default JSON format, each log entry includes:
- timestamp, level, logger name, function, line number
- app version, installation type, process/thread IDs
- correlation ID for request tracking
- Custom fields and exception details when applicable

#### Activity Loggers

Activity loggers provide simplified console output for user-facing operations:
- Always output to stdout regardless of console logging flag
- Use shared formatter/filter for consistency
- Format: `[HH:MM:SS] Message`

#### Programmatic Usage

```python
from src.core.logging_config import get_logger, get_activity_logger, setup_logging

# Get a standard logger
logger = get_logger(__name__)
logger.info("Application operation completed")

# Get an activity logger (always visible to user)
activity_logger = get_activity_logger("Import")
activity_logger.info("Importing model file...")

# Set correlation ID for request tracking
from src.core.logging_config import set_correlation_id
set_correlation_id("request-123")
```

## Documentation

### 🚀 Getting Started
- **[README_MODULAR_INSTALLER.md](README_MODULAR_INSTALLER.md)** - Master index for modular installer system
- **[MODULAR_INSTALLER_START_HERE.md](MODULAR_INSTALLER_START_HERE.md)** - Quick 5-minute overview

### 📦 Modular Installer System
- **[INSTALLER_IMPLEMENTATION.md](INSTALLER_IMPLEMENTATION.md)** - Implementation guide
- **[INSTALLER_MODES_SPECIFICATION.md](INSTALLER_MODES_SPECIFICATION.md)** - 4 installation modes
- **[PER_MODULE_COMPILATION_GUIDE.md](PER_MODULE_COMPILATION_GUIDE.md)** - Per-module compilation
- **[MODULAR_INSTALLER_COMPLETE_PLAN.md](MODULAR_INSTALLER_COMPLETE_PLAN.md)** - Technical plan
- **[MODULAR_INSTALLER_VISUAL_GUIDE.md](MODULAR_INSTALLER_VISUAL_GUIDE.md)** - Visual diagrams

### 🎯 Project Features
- **[DWW_FORMAT_SPECIFICATION.md](DWW_FORMAT_SPECIFICATION.md)** - DWW export format
- **[DWW_USER_GUIDE.md](DWW_USER_GUIDE.md)** - DWW user guide
- **[README_TAB_DATA.md](README_TAB_DATA.md)** - Tab data integration

### 🔒 Security & Standards
- **[SECURITY.md](SECURITY.md)** - Security policies
- **[FILE_TYPE_SECURITY_POLICY.md](FILE_TYPE_SECURITY_POLICY.md)** - File type restrictions
- **[LINTING_STANDARDS.md](LINTING_STANDARDS.md)** - Code standards

### 📁 Documentation Folders
- **[analysis/](analysis/)** - Analysis reports
- **[archive/](archive/)** - Archived documentation
- **[builds/](builds/)** - Build process docs
- **[features/](features/)** - Feature guides
- **[fixes/](fixes/)** - Bug fix documentation
- **[releases/](releases/)** - Release notes
- **[reports/](reports/)** - Technical reports

## Contributing

1. Follow the established code structure and conventions
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all quality checks pass
5. Submit pull requests with clear descriptions

## Performance Requirements

The application meets the following performance targets:

- **Model Loading**: < 5 seconds for files under 100MB
- **Memory Usage**: Stable during repeated operations
- **UI Responsiveness**: Maintained during file operations
- **Frame Rate**: Minimum 30 FPS during model interaction

## System Requirements

### Minimum
- **OS**: Windows 7 SP1 (64-bit)
- **CPU**: Intel Core i3-3220 or equivalent
- **GPU**: Intel HD Graphics 4000 or equivalent
- **RAM**: 4GB
- **Storage**: 100MB free space

### Recommended
- **OS**: Windows 10/11 (64-bit)
- **CPU**: Intel Core i5-3470 or equivalent
- **GPU**: NVIDIA GeForce GTX 1050 or equivalent
- **RAM**: 8GB
- **Storage**: 500MB free space (SSD recommended)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Build Failures**: Check build logs in `build/logs/`
3. **Test Failures**: Verify test environment setup

### Getting Help

- Check documentation in `docs/`
- Review test results in `reports/test_results/`
- Examine build logs in `build/logs/`

## Recent Changes

### Root Directory Cleanup (October 2025)

The project underwent a significant root directory cleanup to improve organization:

- **Reduced root files from 100+ to 30** (70% reduction)
- **Organized files into logical directories**
- **Preserved all functionality**
- **Improved developer experience**

For details, see [`FINAL_CLEANUP_VALIDATION_REPORT.md`](FINAL_CLEANUP_VALIDATION_REPORT.md).

## License

[Add your license information here]

## Contact

[Add contact information here]
