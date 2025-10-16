#!/usr/bin/env python3
"""
Unit tests for Application module.

This module tests the Application class functionality including
initialization, component coordination, and lifecycle management.
"""

import unittest
import sys
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

from src.core.application import Application
from src.core.application_config import ApplicationConfig


class TestApplication(unittest.TestCase):
    """Test cases for Application class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Ensure QApplication exists for tests
        if not QCoreApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QCoreApplication.instance()
        
        self.config = ApplicationConfig.get_default()
    
    def test_initialization_with_default_config(self):
        """Test that Application initializes with default config."""
        app = Application()
        self.assertEqual(app.config.name, "3D-MM")
        self.assertFalse(app._is_initialized)
        self.assertFalse(app._is_running)
        self.assertIsNone(app.qt_app)
        self.assertIsNone(app.main_window)
    
    def test_initialization_with_custom_config(self):
        """Test that Application initializes with custom config."""
        custom_config = ApplicationConfig(name="Test-App", version="2.0.0")
        app = Application(custom_config)
        self.assertEqual(app.config.name, "Test-App")
        self.assertEqual(app.config.version, "2.0.0")
    
    @patch('src.core.application.SystemInitializer')
    @patch('src.core.application.ExceptionHandler')
    @patch('src.core.application.ApplicationBootstrap')
    @patch('src.core.application.MainWindow')
    @patch('src.core.application.QApplication')
    def test_successful_initialization(self, mock_qt_app, mock_main_window, 
                                       mock_bootstrap, mock_exception_handler, 
                                       mock_system_initializer):
        """Test successful application initialization."""
        # Setup mocks
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = True
        mock_system_initializer.return_value = mock_sys_init
        
        mock_exc_handler = Mock()
        mock_exc_handler.create_and_install.return_value = mock_exc_handler
        mock_exception_handler.create_and_install.return_value = mock_exc_handler
        
        mock_boot = Mock()
        mock_boot.bootstrap_services.return_value = True
        mock_bootstrap.return_value = mock_boot
        
        mock_window = Mock()
        mock_main_window.return_value = mock_window
        
        # Create and initialize application
        app = Application(self.config)
        result = app.initialize()
        
        # Verify initialization was successful
        self.assertTrue(result)
        self.assertTrue(app._is_initialized)
        self.assertEqual(app.qt_app, mock_qt_instance)
        self.assertEqual(app.main_window, mock_window)
        
        # Verify components were initialized
        mock_system_initializer.assert_called_once_with(self.config)
        mock_sys_init.initialize.assert_called_once()
        mock_exception_handler.create_and_install.assert_called_once()
        mock_bootstrap.assert_called_once_with(self.config)
        mock_boot.bootstrap_services.assert_called_once()
        mock_main_window.assert_called_once()
    
    @patch('src.core.application.SystemInitializer')
    @patch('src.core.application.QApplication')
    def test_initialization_failure_on_system_init(self, mock_qt_app, mock_system_initializer):
        """Test initialization failure when system initialization fails."""
        # Setup mocks
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = False
        mock_system_initializer.return_value = mock_sys_init
        
        # Create and initialize application
        app = Application(self.config)
        result = app.initialize()
        
        # Verify initialization failed
        self.assertFalse(result)
        self.assertFalse(app._is_initialized)
    
    def test_run_without_initialization(self):
        """Test that running without initialization returns error."""
        app = Application(self.config)
        result = app.run()
        self.assertEqual(result, 1)
    
    def test_already_initialized(self):
        """Test that initializing already initialized app returns True."""
        app = Application(self.config)
        app._is_initialized = True
        result = app.initialize()
        self.assertTrue(result)
    
    def test_already_running(self):
        """Test that running already running app returns 0."""
        app = Application(self.config)
        app._is_initialized = True
        app._is_running = True
        app.qt_app = Mock()
        result = app.run()
        self.assertEqual(result, 0)
    
    @patch('src.core.application.QApplication')
    def test_shutdown(self, mock_qt_app):
        """Test application shutdown."""
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        app = Application(self.config)
        app.qt_app = mock_qt_instance
        app.shutdown(5)
        
        # Verify exit was called with correct code
        mock_qt_instance.exit.assert_called_once_with(5)
    
    @patch('src.core.application.SystemInitializer')
    @patch('src.core.application.ExceptionHandler')
    @patch('src.core.application.ApplicationBootstrap')
    @patch('src.core.application.MainWindow')
    @patch('src.core.application.QApplication')
    def test_cleanup(self, mock_qt_app, mock_main_window, mock_bootstrap, 
                    mock_exception_handler, mock_system_initializer):
        """Test application cleanup."""
        # Setup mocks
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = True
        mock_system_initializer.return_value = mock_sys_init
        
        mock_exc_handler = Mock()
        mock_exc_handler.create_and_install.return_value = mock_exc_handler
        mock_exception_handler.create_and_install.return_value = mock_exc_handler
        
        mock_boot = Mock()
        mock_boot.bootstrap_services.return_value = True
        mock_bootstrap.return_value = mock_boot
        
        mock_window = Mock()
        mock_main_window.return_value = mock_window
        
        # Create, initialize, and cleanup application
        app = Application(self.config)
        app.initialize()
        app.cleanup()
        
        # Verify cleanup was performed
        mock_window.close.assert_called_once()
        mock_boot.cleanup.assert_called_once()
        mock_exc_handler.cleanup.assert_called_once()
        self.assertIsNone(app.main_window)
        self.assertIsNone(app.bootstrap)
        self.assertIsNone(app.exception_handler)
        self.assertFalse(app._is_initialized)
    
    def test_get_system_info(self):
        """Test getting system information."""
        app = Application(self.config)
        info = app.get_system_info()
        
        # Verify basic info is present
        self.assertEqual(info["application_name"], "3D-MM")
        self.assertEqual(info["application_version"], "1.0.0")
        self.assertFalse(info["initialized"])
        self.assertFalse(info["running"])
    
    @patch('src.core.application.ApplicationBootstrap')
    def test_get_system_info_with_bootstrap(self, mock_bootstrap):
        """Test getting system info with bootstrap info."""
        mock_boot = Mock()
        mock_boot.get_system_info.return_value = {
            "hardware_acceleration_enabled": True,
            "theme_loaded": True,
            "settings_migrated": True
        }
        mock_bootstrap.return_value = mock_boot
        
        app = Application(self.config)
        app.bootstrap = mock_boot
        info = app.get_system_info()
        
        # Verify bootstrap info is included
        self.assertTrue(info["hardware_acceleration_enabled"])
    
    @patch('src.core.application.QApplication')
    def test_create_qt_application_success(self, mock_qt_app):
        """Test successful QApplication creation."""
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        app = Application(self.config)
        result = app._create_qt_application([])  # pylint: disable=protected-access
        
        self.assertTrue(result)
        self.assertEqual(app.qt_app, mock_qt_instance)
        self.assertIsNotNone(app.logger)
        mock_qt_app.assert_called_once_with([])
    
    @patch('src.core.application.QApplication')
    def test_create_qt_application_failure(self, mock_qt_app):
        """Test QApplication creation failure."""
        mock_qt_app.side_effect = RuntimeError("Failed to create QApplication")
        
        app = Application(self.config)
        result = app._create_qt_application([])  # pylint: disable=protected-access
        
        self.assertFalse(result)
        self.assertIsNone(app.qt_app)
    
    @patch('src.core.application.SystemInitializer')
    def test_initialize_system_success(self, mock_system_initializer):
        """Test successful system initialization."""
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = True
        mock_system_initializer.return_value = mock_sys_init
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._initialize_system()  # pylint: disable=protected-access
        
        self.assertTrue(result)
        self.assertEqual(app.system_initializer, mock_sys_init)
        mock_system_initializer.assert_called_once_with(self.config)
        mock_sys_init.initialize.assert_called_once()
    
    @patch('src.core.application.SystemInitializer')
    def test_initialize_system_failure(self, mock_system_initializer):
        """Test system initialization failure."""
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = False
        mock_system_initializer.return_value = mock_sys_init
        
        app = Application(self.config)
        result = app._initialize_system()  # pylint: disable=protected-access
        
        self.assertFalse(result)
    
    @patch('src.core.application.ExceptionHandler')
    def test_install_exception_handler_success(self, mock_exception_handler):
        """Test successful exception handler installation."""
        mock_exc_handler = Mock()
        mock_exc_handler.create_and_install.return_value = mock_exc_handler
        mock_exception_handler.create_and_install.return_value = mock_exc_handler
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._install_exception_handler()  # pylint: disable=protected-access
        
        self.assertTrue(result)
        self.assertEqual(app.exception_handler, mock_exc_handler)
        mock_exception_handler.create_and_install.assert_called_once()
    
    @patch('src.core.application.ExceptionHandler')
    def test_install_exception_handler_failure(self, mock_exception_handler):
        """Test exception handler installation failure."""
        mock_exc_handler = Mock()
        mock_exc_handler.create_and_install.side_effect = RuntimeError("Failed to install")
        mock_exception_handler.create_and_install.side_effect = RuntimeError("Failed to install")
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._install_exception_handler()  # pylint: disable=protected-access
        
        self.assertFalse(result)
    
    @patch('src.core.application.ApplicationBootstrap')
    def test_bootstrap_services_success(self, mock_bootstrap):
        """Test successful service bootstrapping."""
        mock_boot = Mock()
        mock_boot.bootstrap_services.return_value = True
        mock_bootstrap.return_value = mock_boot
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._bootstrap_services()  # pylint: disable=protected-access
        
        self.assertTrue(result)
        self.assertEqual(app.bootstrap, mock_boot)
        mock_bootstrap.assert_called_once_with(self.config)
        mock_boot.bootstrap_services.assert_called_once()
    
    @patch('src.core.application.ApplicationBootstrap')
    def test_bootstrap_services_failure(self, mock_bootstrap):
        """Test service bootstrapping failure."""
        mock_boot = Mock()
        mock_boot.bootstrap_services.return_value = False
        mock_bootstrap.return_value = mock_boot
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._bootstrap_services()  # pylint: disable=protected-access
        
        self.assertFalse(result)
    
    @patch('src.core.application.MainWindow')
    def test_create_main_window_success(self, mock_main_window):
        """Test successful main window creation."""
        mock_window = Mock()
        mock_main_window.return_value = mock_window
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._create_main_window()  # pylint: disable=protected-access
        
        self.assertTrue(result)
        self.assertEqual(app.main_window, mock_window)
        mock_main_window.assert_called_once()
    
    @patch('src.core.application.MainWindow')
    def test_create_main_window_failure(self, mock_main_window):
        """Test main window creation failure."""
        mock_main_window.side_effect = RuntimeError("Failed to create window")
        
        app = Application(self.config)
        app.logger = Mock()
        result = app._create_main_window()  # pylint: disable=protected-access
        
        self.assertFalse(result)
        self.assertIsNone(app.main_window)
    
    @patch('src.core.application.MainWindow')
    def test_connect_signals(self, mock_main_window):
        """Test signal connection."""
        mock_window = Mock()
        mock_window.model_loaded = Mock()
        mock_window.model_selected = Mock()
        mock_main_window.return_value = mock_window
        
        app = Application(self.config)
        app.logger = Mock()
        app.main_window = mock_window
        app._connect_signals()  # pylint: disable=protected-access
        
        # Verify closeEvent was set
        self.assertIsNotNone(mock_window.closeEvent)
    
    def test_on_main_window_close(self):
        """Test main window close event handling."""
        app = Application(self.config)
        app.logger = Mock()
        app.cleanup = Mock()
        
        mock_event = Mock()
        app._on_main_window_close(mock_event)  # pylint: disable=protected-access
        
        app.cleanup.assert_called_once()
        mock_event.accept.assert_called_once()
    
    @patch('src.core.application.QApplication')
    def test_run_with_full_event_loop(self, mock_qt_app):
        """Test running the application with full event loop."""
        mock_qt_instance = Mock()
        mock_qt_instance.exec.return_value = 0
        mock_qt_app.return_value = mock_qt_instance
        
        mock_window = Mock()
        
        app = Application(self.config)
        app.logger = Mock()
        app.qt_app = mock_qt_instance
        app.main_window = mock_window
        app._is_initialized = True  # pylint: disable=protected-access
        
        result = app.run()
        
        self.assertEqual(result, 0)
        mock_window.show.assert_called_once()
        mock_qt_instance.exec.assert_called_once()
        self.assertFalse(app._is_running)  # pylint: disable=protected-access
    
    @patch('src.core.application.QApplication')
    def test_run_with_runtime_error(self, mock_qt_app):
        """Test run method with runtime error."""
        mock_qt_instance = Mock()
        mock_qt_instance.exec.side_effect = RuntimeError("Event loop error")
        mock_qt_app.return_value = mock_qt_instance
        
        app = Application(self.config)
        app.logger = Mock()
        app.qt_app = mock_qt_instance
        app._is_initialized = True  # pylint: disable=protected-access
        
        result = app.run()
        
        self.assertEqual(result, 1)
        self.assertFalse(app._is_running)  # pylint: disable=protected-access
    
    @patch('src.core.application.SystemInitializer')
    def test_cleanup_with_system_initializer(self, mock_system_initializer):
        """Test cleanup with system initializer."""
        mock_sys_init = Mock()
        mock_sys_init.initialize.return_value = True
        mock_system_initializer.return_value = mock_sys_init
        
        mock_window = Mock()
        mock_boot = Mock()
        mock_exc_handler = Mock()
        
        app = Application(self.config)
        app.logger = Mock()
        app.system_initializer = mock_sys_init
        app.main_window = mock_window
        app.bootstrap = mock_boot
        app.exception_handler = mock_exc_handler
        app._is_initialized = True  # pylint: disable=protected-access
        
        app.cleanup()
        
        mock_window.close.assert_called_once()
        mock_boot.cleanup.assert_called_once()
        mock_exc_handler.cleanup.assert_called_once()
        mock_sys_init.cleanup_temp_files.assert_called_once()
        self.assertIsNone(app.main_window)
        self.assertIsNone(app.bootstrap)
        self.assertIsNone(app.exception_handler)
        self.assertIsNone(app.system_initializer)
        self.assertFalse(app._is_initialized)  # pylint: disable=protected-access
    
    @patch('src.core.application.SystemInitializer')
    @patch('src.core.application.QApplication')
    def test_initialization_with_runtime_error(self, mock_qt_app, mock_system_initializer):
        """Test initialization with runtime error."""
        mock_qt_instance = Mock()
        mock_qt_app.return_value = mock_qt_instance
        
        mock_sys_init = Mock()
        mock_sys_init.initialize.side_effect = RuntimeError("System initialization failed")
        mock_system_initializer.return_value = mock_sys_init
        
        app = Application(self.config)
        result = app.initialize()
        
        # Verify initialization failed
        self.assertFalse(result)
        self.assertFalse(app._is_initialized)  # pylint: disable=protected-access


if __name__ == "__main__":
    unittest.main()