#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It initializes the application and starts the main event loop.
"""

import sys
import os
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QStandardPaths, QDir, Qt

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logging_config import setup_logging
from core.settings_migration import migrate_on_startup
from gui.main_window import MainWindow
from gui.theme import load_theme_from_settings


def setup_directories():
    """Create necessary directories for the application."""
    app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    app_dirs = [
        app_data_path,
        os.path.join(app_data_path, "models"),
        os.path.join(app_data_path, "logs"),
        os.path.join(app_data_path, "temp"),
    ]
    
    for dir_path in app_dirs:
        QDir().mkpath(dir_path)


def main():
    """Main function to start the 3D-MM application."""
    try:
        # Set up application information
        QApplication.setApplicationName("3D-MM")
        QApplication.setApplicationVersion("1.0.0")
        QApplication.setOrganizationName("3D-MM Development Team")
        QApplication.setOrganizationDomain("3dmm.local")
        
        # Set up high DPI support for better display on modern screens
        # Note: These are deprecated in PySide6 but kept for compatibility
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting 3D-MM application")
        
        # Create QApplication with error handling
        app = QApplication(sys.argv)
        
        # Set up exception handling
        sys.excepthook = _exception_hook
        
        # Set up necessary directories
        setup_directories()
        logger.debug("Application directories created")
        
        # Check for and perform settings migration if needed
        logger.debug("Checking for settings migration")
        if not migrate_on_startup():
            logger.warning("Settings migration failed or incomplete")
        
        # Load theme settings before creating windows
        load_theme_from_settings()
        
        # Create and show main window
        logger.debug("Creating main window")
        main_window = MainWindow()
        
        # Connect signals for logging
        main_window.model_loaded.connect(lambda path: logger.info(f"Model loaded: {path}"))
        main_window.model_selected.connect(lambda id: logger.info(f"Model selected: {id}"))
        
        # Show the window
        main_window.show()
        logger.info("Main window displayed")
        
        # Start the event loop
        logger.info("Application event loop started")
        exit_code = app.exec()
        
        # Log application shutdown
        logger.info(f"Application exiting with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        # Handle any exceptions during startup
        print(f"Failed to start 3D-MM application: {str(e)}")
        sys.exit(1)


def _exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler for unhandled exceptions."""
    import traceback
    
    # Log the exception
    logger = logging.getLogger(__name__)
    logger.critical(
        "Unhandled exception",
        extra={
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
            "exception_traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        }
    )
    
    # Show error dialog
    from PySide6.QtWidgets import QMessageBox
    from PySide6.QtCore import QCoreApplication
    
    if QCoreApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("An unexpected error occurred")
        msg.setInformativeText(f"Error: {str(exc_value)}")
        msg.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        msg.exec_()


if __name__ == "__main__":
    main()