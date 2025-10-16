# Application Architecture

## Overview

The 3D Model Manager application has been refactored from a monolithic structure to a modular, well-organized architecture. This document explains the new application architecture and its components.

## Architecture Diagram

```
┌─────────────────┐
│     main.py     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Application   │
└─────────┬───────┘
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
┌───────┬───────┬───────┐
│Config │Bootstrap│System │
│       │         │Init   │
└───────┴───────┴───────┘
          │
          ▼
┌─────────────────┐
│ ExceptionHandler│
└─────────────────┘
```

## Core Components

### 1. Application (`src/core/application.py`)

The main Application class encapsulates the application lifecycle and coordinates all components. It handles:

- Application initialization and shutdown
- Component coordination and dependency management
- Main window creation and event loop management
- Error handling and graceful shutdown

**Key Methods:**
- `initialize()` - Initialize all application components
- `run()` - Start the application event loop
- `shutdown()` - Gracefully shutdown the application
- `cleanup()` - Clean up resources

### 2. ApplicationConfig (`src/core/application_config.py`)

Centralized application configuration and metadata using a dataclass. It provides:

- Application identity information (name, version, organization)
- Feature flags and configuration options
- Resource limits and UI defaults
- Immutable configuration with factory methods

**Usage Example:**
```python
config = ApplicationConfig.get_default()
custom_config = ApplicationConfig(name="Custom-App", version="2.0.0")
```

### 3. SystemInitializer (`src/core/system_initializer.py`)

Handles system-level initialization including:

- Application metadata setup in QApplication
- High DPI support configuration
- Logging system initialization
- Directory creation and management
- Temporary file cleanup

**Key Features:**
- Creates necessary application directories
- Configures logging with JSON formatting
- Sets up application-wide Qt attributes

### 4. ApplicationBootstrap (`src/core/application_bootstrap.py`)

Manages the initialization of application services in the correct order:

- Settings migration
- Theme system loading
- Hardware acceleration detection and setup
- Service initialization coordination

**Benefits:**
- Ensures proper initialization order
- Handles service dependencies
- Provides graceful fallback for optional services

### 5. ExceptionHandler (`src/core/exception_handler.py`)

Centralized error handling system with:

- Global exception hook installation
- Structured error logging
- User-friendly error dialogs
- Startup error handling
- Graceful shutdown support

**Features:**
- JSON-formatted error logs with detailed context
- Error dialogs with detailed traceback information
- Fallback console output for critical errors

## Main Entry Point

The refactored `main.py` is now much cleaner and simpler:

```python
def main():
    """Main function to start the 3D-MM application."""
    # Create application configuration
    config = ApplicationConfig.get_default()
    
    # Create exception handler for startup errors
    exception_handler = ExceptionHandler()
    
    try:
        # Create and initialize application
        app = Application(config)
        
        if not app.initialize():
            print("Failed to initialize application")
            return 1
        
        # Run the application
        exit_code = app.run()
        return exit_code
        
    except RuntimeError as e:
        # Handle any exceptions during startup
        exception_handler.handle_startup_error(e)
        return 1
```

## Benefits of the New Architecture

### 1. Single Responsibility Principle
Each class has a single, well-defined responsibility:
- `Application`: Lifecycle management
- `ApplicationConfig`: Configuration management
- `SystemInitializer`: System setup
- `ApplicationBootstrap`: Service initialization
- `ExceptionHandler`: Error handling

### 2. Improved Testability
The modular structure makes testing easier:
- Each component can be tested in isolation
- Mock objects can be easily injected
- Dependencies are explicit and manageable

### 3. Better Maintainability
Changes to specific functionality are isolated:
- Configuration changes only affect `ApplicationConfig`
- System setup changes only affect `SystemInitializer`
- Error handling changes only affect `ExceptionHandler`

### 4. Enhanced Reusability
Components can be reused in different contexts:
- `ApplicationConfig` can be used in CLI tools
- `ExceptionHandler` can be used in utilities
- `SystemInitializer` can be used in tests

### 5. Clearer Dependencies
The architecture shows explicit dependencies:
- `Application` depends on all other components
- Components are loosely coupled
- Dependency injection is used where appropriate

## Testing

The new architecture includes comprehensive unit tests:

- `tests/test_application_config.py` - Tests configuration functionality
- `tests/test_exception_handler.py` - Tests error handling
- `tests/test_application.py` - Tests application lifecycle

## Migration Guide

If you're migrating from the old architecture:

1. **Configuration**: Use `ApplicationConfig` instead of hardcoded values
2. **System Setup**: Use `SystemInitializer` for directory and logging setup
3. **Error Handling**: Use `ExceptionHandler` for consistent error management
4. **Service Initialization**: Use `ApplicationBootstrap` for service setup

## Future Enhancements

The new architecture enables easier implementation of:

- Plugin system
- Multiple configuration sources
- Service registry
- Advanced logging configuration
- Performance monitoring integration