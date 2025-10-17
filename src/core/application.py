#!/usr/bin/env python3
"""
Application Module

This module contains the Application class that encapsulates
the application lifecycle management and coordinates all components.
"""

import logging
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from .application_config import ApplicationConfig
from .application_bootstrap import ApplicationBootstrap
from .exception_handler import ExceptionHandler
from .system_initializer import SystemInitializer
from src.gui.main_window import MainWindow


class Application:
    """Main application class that manages the application lifecycle."""
    
    def __init__(self, config: Optional[ApplicationConfig] = None):
        """Initialize the Application with optional configuration.
        
        Args:
            config: Application configuration, uses default if None
        """
        self.config = config or ApplicationConfig.get_default()
        self.logger: Optional[logging.Logger] = None
        self.qt_app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.exception_handler: Optional[ExceptionHandler] = None
        self.system_initializer: Optional[SystemInitializer] = None
        self.bootstrap: Optional[ApplicationBootstrap] = None
        self._is_initialized = False
        self._is_running = False
    
    def initialize(self, argv: Optional[list] = None) -> bool:
        """Initialize the application and all its components.
        
        Args:
            argv: Command line arguments, uses sys.argv if None
            
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._is_initialized:
            if self.logger:
                self.logger.warning("Application already initialized")
            return True
        
        try:
            # Create QApplication first
            if not self._create_qt_application(argv or sys.argv):
                return False
            
            # Initialize system components
            if not self._initialize_system():
                return False
            
            # Install exception handler
            if not self._install_exception_handler():
                return False
            
            # Bootstrap application services
            if not self._bootstrap_services():
                return False
            
            # Create main window
            if not self._create_main_window():
                return False
            
            # Connect signals
            self._connect_signals()
            
            self._is_initialized = True
            self.logger.info("Application initialization completed successfully")
            return True
            
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Application initialization failed: %s", str(e))
            else:
                print(f"Application initialization failed: {str(e)}")
            return False
    
    def run(self) -> int:
        """Run the application event loop.
        
        Returns:
            Exit code from the application
        """
        if not self._is_initialized:
            if self.logger:
                self.logger.error("Cannot run uninitialized application")
            else:
                print("Cannot run uninitialized application")
            return 1
        
        if self._is_running:
            if self.logger:
                self.logger.warning("Application is already running")
            return 0
        
        try:
            self._is_running = True
            
            # Show the main window
            if self.main_window:
                self.main_window.show()
                self.logger.info("Main window displayed")
            
            # Start the event loop
            self.logger.info("Application event loop started")
            exit_code = self.qt_app.exec()
            
            # Log application shutdown
            self.logger.info("Application exiting with code: %d", exit_code)
            return exit_code
            
        except RuntimeError as e:
            self.logger.error("Application runtime error: %s", str(e))
            return 1
        finally:
            self._is_running = False
            self.cleanup()
    
    def shutdown(self, exit_code: int = 0) -> None:
        """Shutdown the application gracefully.
        
        Args:
            exit_code: Exit code to return
        """
        if self.qt_app:
            self.qt_app.exit(exit_code)
    
    def cleanup(self) -> None:
        """Cleanup application resources."""
        if not self._is_initialized:
            return
        
        try:
            # Cleanup main window
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            # Cleanup bootstrap
            if self.bootstrap:
                self.bootstrap.cleanup()
                self.bootstrap = None
            
            # Cleanup exception handler
            if self.exception_handler:
                self.exception_handler.cleanup()
                self.exception_handler = None
            
            # Cleanup system initializer
            if self.system_initializer:
                self.system_initializer.cleanup_temp_files()
                self.system_initializer = None
            
            self._is_initialized = False
            if self.logger:
                self.logger.info("Application cleanup completed")
            
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Error during cleanup: %s", str(e))
    
    def _create_qt_application(self, argv: list) -> bool:
        """Create the QApplication instance.
        
        Args:
            argv: Command line arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.qt_app = QApplication(argv)
            self.logger = logging.getLogger(__name__)
            self.logger.info("QApplication created")
            return True
        except RuntimeError as e:
            print(f"Failed to create QApplication: {str(e)}")
            return False
    
    def _initialize_system(self) -> bool:
        """Initialize system components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.system_initializer = SystemInitializer(self.config)
            if not self.system_initializer.initialize():
                return False
            self.logger = logging.getLogger(__name__)
            return True
        except RuntimeError as e:
            print(f"System initialization failed: {str(e)}")
            return False
    
    def _install_exception_handler(self) -> bool:
        """Install the global exception handler.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.exception_handler = ExceptionHandler.create_and_install()
            if self.logger:
                self.logger.info("Exception handler installed")
            return True
        except Exception as e:  # Catch all exceptions, not just RuntimeError
            if self.logger:
                self.logger.error("Failed to install exception handler: %s", str(e))
            return False
    
    def _bootstrap_services(self) -> bool:
        """Bootstrap application services.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.bootstrap = ApplicationBootstrap(self.config)
            if not self.bootstrap.bootstrap_services():
                return False
            if self.logger:
                self.logger.info("Application services bootstrapped")
            return True
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Service bootstrap failed: %s", str(e))
            return False
    
    def _create_main_window(self) -> bool:
        """Create the main application window.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.main_window = MainWindow()
            if self.logger:
                self.logger.info("Main window created")
            return True
        except RuntimeError as e:
            if self.logger:
                self.logger.error("Failed to create main window: %s", str(e))
            return False
    
    def _connect_signals(self) -> None:
        """Connect application signals."""
        if self.main_window:
            # Connect main window signals for logging
            self.main_window.model_loaded.connect(
                lambda path: self.logger.info("Model loaded: %s", path)
            )
            self.main_window.model_selected.connect(
                lambda model_id: self.logger.info("Model selected: %d", model_id)
            )
            
            # Connect window close signal
            self.main_window.closeEvent = self._on_main_window_close
    
    def _on_main_window_close(self, event) -> None:
        """Handle main window close event.
        
        Args:
            event: Close event
        """
        if self.logger:
            self.logger.info("Main window close event received")
        self.cleanup()
        event.accept()
    
    def get_system_info(self) -> dict:
        """Get information about the application system.
        
        Returns:
            Dictionary containing system information
        """
        info = {
            "application_name": self.config.name,
            "application_version": self.config.get_full_version_string(),
            "initialized": self._is_initialized,
            "running": self._is_running,
        }
        
        if self.bootstrap:
            info.update(self.bootstrap.get_system_info())
        
        return info