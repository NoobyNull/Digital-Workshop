#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It uses the new modular Application class for initialization and execution.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.application import Application
from core.application_config import ApplicationConfig
from core.exception_handler import ExceptionHandler


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


if __name__ == "__main__":
    sys.exit(main())