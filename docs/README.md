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
   python run.py
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

## Documentation

### User Documentation

- **Getting Started**: [`docs/guides/`](docs/guides/)
- **Architecture**: [`docs/architecture/`](docs/architecture/)
- **API Reference**: Inline documentation in source code

### Developer Documentation

- **Development Guidelines**: [`docs/architecture/DEVELOPMENT_GUIDELINES.md`](docs/architecture/DEVELOPMENT_GUIDELINES.md)
- **Project Structure**: See structure section above
- **Testing Guide**: [`tests/README.md`](tests/README.md) (if exists)

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
