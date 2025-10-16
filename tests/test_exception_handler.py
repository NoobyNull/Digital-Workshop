#!/usr/bin/env python3
"""
Unit tests for ExceptionHandler module.

This module tests the ExceptionHandler class functionality including
global exception hook installation, error dialog handling, and logging.
"""

import unittest
import logging
import sys
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QCoreApplication

from src.core.exception_handler import ExceptionHandler


class TestExceptionHandler(unittest.TestCase):
    """Test cases for ExceptionHandler class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Ensure QApplication exists for tests
        if not QCoreApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QCoreApplication.instance()
        
        self.config = Mock()
        self.exception_handler = ExceptionHandler()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original exception hook if it was changed
        if hasattr(self, '_original_excepthook'):
            sys.excepthook = self._original_excepthook
    
    def test_initialization(self):
        """Test that ExceptionHandler initializes correctly."""
        handler = ExceptionHandler()
        self.assertIsNone(handler.parent)
        self.assertIsInstance(handler.logger, logging.Logger)
        self.assertIsNone(handler._original_excepthook)
    
    def test_install_global_handler(self):
        """Test that global exception handler is installed correctly."""
        handler = ExceptionHandler()
        original_hook = sys.excepthook
        
        handler.install_global_handler()
        
        # Exception hook should be changed
        self.assertNotEqual(sys.excepthook, original_hook)
        self.assertEqual(sys.excepthook, handler._global_exception_hook)
        self.assertEqual(handler._original_excepthook, original_hook)
        
        # Restore for cleanup
        handler.uninstall_global_handler()
    
    def test_uninstall_global_handler(self):
        """Test that global exception handler is uninstalled correctly."""
        handler = ExceptionHandler()
        original_hook = sys.excepthook
        
        handler.install_global_handler()
        handler.uninstall_global_handler()
        
        # Exception hook should be restored
        self.assertEqual(sys.excepthook, original_hook)
    
    @patch('src.core.exception_handler.logging.getLogger')
    def test_log_exception(self, mock_get_logger):
        """Test that exceptions are logged correctly."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ExceptionHandler()
        
        # Create a test exception
        try:
            raise ValueError("Test error")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Call the log method
            handler._log_exception(exc_type, exc_value, exc_traceback)
            
            # Verify logging was called
            mock_logger.critical.assert_called_once()
            args, kwargs = mock_logger.critical.call_args
            self.assertEqual(args[0], "Unhandled exception")
            self.assertIn("exception_type", kwargs["extra"])
            self.assertEqual(kwargs["extra"]["exception_type"], "ValueError")
    
    @patch('src.core.exception_handler.QMessageBox')
    @patch('src.core.exception_handler.logging.getLogger')
    def test_show_error_dialog(self, mock_get_logger, mock_message_box):
        """Test that error dialog is shown correctly."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_msg_box = Mock()
        mock_message_box.return_value = mock_msg_box
        
        handler = ExceptionHandler()
        
        # Create a test exception
        try:
            raise ValueError("Test error")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Call the dialog method
            handler._show_error_dialog(exc_type, exc_value, exc_traceback)
            
            # Verify dialog was created and configured
            mock_message_box.assert_called_once()
            mock_msg_box.setIcon.assert_called_once_with(QMessageBox.Critical)
            mock_msg_box.setWindowTitle.assert_called_once_with("Application Error")
            mock_msg_box.setText.assert_called_once_with("An unexpected error occurred")
            mock_msg_box.setInformativeText.assert_called_once_with("Error: Test error")
            mock_msg_box.exec_.assert_called_once()
    
    @patch('src.core.exception_handler.QMessageBox')
    @patch('src.core.exception_handler.logging.getLogger')
    def test_dialog_error_handling(self, mock_get_logger, mock_message_box):
        """Test that dialog creation errors are handled gracefully."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_message_box.side_effect = RuntimeError("Dialog error")
        
        handler = ExceptionHandler()
        
        # Mock console output method
        handler._console_error_output = Mock()
        
        # Create a test exception
        try:
            raise ValueError("Test error")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Call the dialog method
            handler._show_error_dialog(exc_type, exc_value, exc_traceback)
            
            # Verify fallback to console output
            handler._console_error_output.assert_called_once_with(
                exc_type, exc_value, exc_traceback
            )
    
    @patch('builtins.print')
    def test_console_error_output(self, mock_print):
        """Test that console error output works correctly."""
        handler = ExceptionHandler()
        
        # Create a test exception
        try:
            raise ValueError("Test error")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Call the console method
            handler._console_error_output(exc_type, exc_value, exc_traceback)
            
            # Verify print was called
            mock_print.assert_called()
            calls = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("ValueError" in call for call in calls))
            self.assertTrue(any("Test error" in call for call in calls))
    
    @patch('src.core.exception_handler.QMessageBox')
    def test_startup_error_handling(self, mock_message_box):
        """Test that startup errors are handled correctly."""
        mock_msg_box = Mock()
        mock_message_box.return_value = mock_msg_box
        
        handler = ExceptionHandler()
        
        # Create a test exception
        test_error = RuntimeError("Startup failed")
        
        # Call the startup error handler
        with patch('builtins.print') as mock_print:
            handler.handle_startup_error(test_error)
        
        # Verify error was printed and dialog shown
        mock_print.assert_called_with("Failed to start 3D-MM application: Startup failed")
        mock_msg_box.exec_.assert_called_once()
    
    @patch('src.core.exception_handler.logging.getLogger')
    def test_graceful_shutdown_with_error(self, mock_get_logger):
        """Test graceful shutdown with error."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ExceptionHandler()
        test_error = RuntimeError("Shutdown error")
        
        handler.handle_graceful_shutdown(test_error)
        
        # Verify error was logged
        mock_logger.error.assert_called_once_with(
            "Graceful shutdown due to error: %s", str(test_error)
        )
    
    @patch('src.core.exception_handler.logging.getLogger')
    def test_cleanup(self, mock_get_logger):
        """Test that cleanup works correctly."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ExceptionHandler()
        original_hook = sys.excepthook
        handler._original_excepthook = original_hook
        
        handler.cleanup()
        
        # Verify exception hook was restored
        self.assertEqual(sys.excepthook, original_hook)
        mock_logger.info.assert_called_with("Exception handler cleaned up")
    
    def test_create_and_install_factory(self):
        """Test the factory method for creating and installing."""
        original_hook = sys.excepthook
        
        handler = ExceptionHandler.create_and_install()
        
        # Verify handler was created and installed
        self.assertIsInstance(handler, ExceptionHandler)
        self.assertNotEqual(sys.excepthook, original_hook)
        
        # Cleanup
        handler.uninstall_global_handler()


if __name__ == "__main__":
    unittest.main()