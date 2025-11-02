# Digital Workshop - Master Reference Guide

*Consolidated documentation for the Digital Workshop 3D modeling application*

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Development Guidelines](#development-guidelines)
4. [Testing Framework](#testing-framework)
5. [Performance Requirements](#performance-requirements)
6. [Quality Standards](#quality-standards)
7. [System Requirements](#system-requirements)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Recent Changes](#recent-changes)

---

## Project Overview

**Digital Workshop** is a comprehensive 3D modeling application built with Python, PySide6, and VTK for CAD/CAM workflows.

### Core Features
- 3D model viewing and manipulation
- File format support (STL, OBJ, STEP, 3MF)
- Material management
- Cost estimation
- Theme system with professional themes
- Comprehensive error handling and logging

### Key Components
- **Core Engine**: Application logic, services, and data management
- **GUI Layer**: PySide6-based user interface with VTK integration
- **Parser System**: Multi-format 3D file parsing with progressive loading
- **Database Layer**: SQLite-based metadata and model management
- **Testing Framework**: Comprehensive unit and integration testing

---

## Architecture Summary

### Core Architecture
```
src/
├── core/           # Business logic and services
│   ├── services/   # Application services
│   ├── database/   # Data access layer
│   ├── cleanup/    # Resource management
│   └── error_handling/  # Error management
├── gui/            # User interface components
│   ├── theme/      # Theme management
│   ├── vtk/        # VTK integration
│   └── services/   # UI services
├── parsers/        # File format parsers
└── utils/          # Utility functions
```

### Design Patterns
- **Service Layer Pattern**: Business logic separation
- **Repository Pattern**: Data access abstraction
- **Interface Segregation**: Clean API contracts
- **Observer Pattern**: Event handling
- **Factory Pattern**: Object creation

### Key Interfaces
- `IModelService`: Model management operations
- `IViewerService`: 3D visualization services
- `IParserService`: File parsing operations
- `IRepository`: Data access operations

---

## Development Guidelines

### Code Quality Standards
- **Logging**: All modules must create proper JSON logs
- **Error Handling**: Comprehensive error handling with meaningful messages
- **Documentation**: Inline documentation for all public functions
- **Testing**: Unit tests for all parser functions, integration tests for workflows

### Commit Standards
- Use atomic commits: each commit represents a single logical change
- Commit messages must summarize what and why, referencing files affected
- No generic "misc" or "fix" messages

### Performance Guidelines
- **Load Times**: < 5s for files < 100MB, < 15s for 100-500MB, < 30s for > 500MB
- **Memory Usage**: Maximum 2GB for typical usage, no memory leaks
- **Frame Rate**: Minimum 30 FPS during model interaction

### Security Practices
- Never hard-code secrets, credentials, or sensitive user data
- Remove any credentials found in code immediately and log the action
- Follow secure coding practices for data handling

---

## Testing Framework

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for workflows
└── comprehensive/  # End-to-end testing
```

### Testing Requirements
- **Unit Tests**: All parser functions must have unit tests
- **Integration Tests**: Complete workflow testing
- **Memory Leak Testing**: Verify no leaks during repeated operations
- **Performance Benchmarking**: Load time validation

### Quality Gates
- All tests must pass before integration
- Memory usage must remain stable during stress testing
- Performance targets must be verified
- Documentation must be complete and accurate

---

## Performance Requirements

### Load Time Targets
- **Small Files** (< 100MB): < 5 seconds
- **Medium Files** (100-500MB): < 15 seconds  
- **Large Files** (> 500MB): < 30 seconds

### Memory Management
- **Maximum Usage**: 2GB for typical usage
- **Model Cache**: Adaptive based on available RAM
- **Texture Memory**: Optimized for GPU capabilities
- **No Memory Leaks**: Stable usage during stress testing

### Responsiveness Requirements
- Interface remains responsive during file loading
- Progress feedback for all long operations
- Cancellation support for lengthy operations
- Smooth interaction during model manipulation

### Frame Rate Requirements
- **Minimum**: 30 FPS during model interaction
- **Consistent**: Across different model sizes
- **Adaptive**: Based on system capabilities
- **VSync**: Enabled for tear-free rendering

---

## Quality Standards

### Code Quality Requirements
- **Logging Standards**: All modules create proper JSON logs
- **Testing Requirements**: Unit and integration tests mandatory
- **Documentation Requirements**: Inline docs and module-level docstrings
- **Performance Testing**: Load testing for all features

### Development Process Standards
- **Code Review**: All code must pass review before integration
- **Debugging Standards**: Comprehensive error handling and logging
- **Quality Gates**: Tests, performance, and documentation validation

### Error Handling Standards
- Every error condition triggers a log entry with troubleshooting detail
- Never suppress errors without clear explanation
- Provide meaningful error messages to users and developers
- Graceful degradation for unsupported features

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 7 SP1 (64-bit)
- **CPU**: Intel Core i3-3220 (Ivy Bridge) or equivalent
- **GPU**: Intel HD Graphics 4000 or equivalent
- **RAM**: 4GB
- **Storage**: 100MB free space

### Recommended Requirements
- **OS**: Windows 10/11 (64-bit)
- **CPU**: Intel Core i5-3470 or equivalent
- **GPU**: NVIDIA GeForce GTX 1050 or equivalent
- **RAM**: 8GB
- **Storage**: 500MB free space (SSD recommended)

### Software Dependencies
- **Required**: Python 3.8-3.12 (64-bit), PySide6 6.0.0+, VTK 9.2.0+, SQLite 3.0+
- **Optional**: NumPy 1.24.0+, lxml 4.6.0+

### Graphics API Support
- **OpenGL**: 3.3 Core Profile minimum
- **DirectX**: 11.0 minimum (via ANGLE fallback)
- **Fallback**: Qt software rasterizer (limited performance)

---

## Troubleshooting Guide

### Common Issues

#### Application Won't Start
1. Check Python version (3.8-3.12 required)
2. Verify all dependencies are installed
3. Check system requirements
4. Review error logs in application directory

#### Performance Issues
1. Check available RAM and GPU memory
2. Verify graphics drivers are up to date
3. Reduce model complexity if needed
4. Enable progressive loading for large files

#### File Loading Problems
1. Verify file format is supported
2. Check file permissions
3. Ensure sufficient disk space
4. Review parsing error logs

#### Memory Issues
1. Close other memory-intensive applications
2. Enable memory optimization features
3. Use smaller model files for testing
4. Monitor memory usage during operations

### Error Categories
- **File Errors**: Unsupported formats, corrupted files, permission issues
- **System Errors**: Insufficient resources, driver issues, compatibility problems
- **Application Errors**: Configuration issues, database problems, service failures

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DIGITAL_WORKSHOP_DEBUG=1
```

---

## Recent Changes

### Major Refactoring (October 2025)
- **Consolidated Documentation**: Reduced 100+ individual files to this master reference
- **Improved Architecture**: Enhanced service layer and interface segregation
- **Better Error Handling**: Comprehensive error management system
- **Performance Optimizations**: Progressive loading and memory management
- **Testing Framework**: Unified testing approach with quality gates

### Key Improvements
- **Unified Cleanup System**: Better resource management and cleanup
- **Enhanced Theme System**: Professional themes with consistent application
- **Database Layer Refactoring**: Improved data access and performance
- **Parser System Overhaul**: Better file format support and error handling
- **CI/CD Integration**: Automated testing and deployment workflows

### Code Quality Enhancements
- **Linting Protection**: Comprehensive code style enforcement
- **Quality Gates**: Automated validation before integration
- **Documentation Standards**: Consistent documentation requirements
- **Security Practices**: Enhanced security and credential management

---

## Support and Maintenance

### Getting Help
1. Check this master reference guide first
2. Review application logs for specific errors
3. Consult the troubleshooting section
4. Check system requirements and compatibility

### Contributing
1. Follow development guidelines and quality standards
2. Ensure all tests pass before submitting
3. Update documentation as needed
4. Follow commit message standards

### Maintenance Schedule
- **Daily**: Automated testing and quality checks
- **Weekly**: Performance monitoring and optimization
- **Monthly**: Dependency updates and security reviews
- **Quarterly**: Major feature updates and architecture reviews

---

*This master reference consolidates all essential project documentation. Individual report files have been removed to reduce bloat and improve maintainability.*