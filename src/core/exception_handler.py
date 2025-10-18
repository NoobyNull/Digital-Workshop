#!/usr/bin/env python3
"""
Exception Handler Module

This module contains the ExceptionHandler class responsible for
centralized error handling, global exception hooks, and error dialog management.
"""

import logging
import sys
import traceback
from typing import Optional

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMessageBox, QWidget


class ExceptionHandler:
    """Centralized exception handling for the application."""

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the ExceptionHandler.

        Args:
            parent: Parent widget for error dialogs
        """
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self._original_excepthook = None

    def install_global_handler(self) -> None:
        """Install the global exception hook."""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_hook
        self.logger.info("Global exception handler installed")

    def uninstall_global_handler(self) -> None:
        """Restore the original exception hook."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
            self.logger.info("Global exception handler uninstalled")

    def _global_exception_hook(self, exc_type, exc_value, exc_traceback) -> None:
        """Global exception handler for unhandled exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Log the exception
        self._log_exception(exc_type, exc_value, exc_traceback)

        # Show error dialog if QApplication is available
        if QCoreApplication.instance():
            self._show_error_dialog(exc_type, exc_value, exc_traceback)
        else:
            # Fallback to console output if no QApplication
            self._console_error_output(exc_type, exc_value, exc_traceback)

    def _log_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """Log the exception with structured data.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        self.logger.critical(
            "Unhandled exception",
            extra={
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
                "exception_traceback": "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
            }
        )

    def _show_error_dialog(self, exc_type, exc_value, exc_traceback) -> None:
        """Show an error dialog to the user.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Application Error")
            msg_box.setText("An unexpected error occurred")
            msg_box.setInformativeText(f"Error: {str(exc_value)}")

            # Add detailed traceback
            detailed_text = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            msg_box.setDetailedText(detailed_text)

            # Set parent if available
            if self.parent:
                msg_box.setParent(self.parent)

            msg_box.exec_()
        except RuntimeError as dialog_error:
            # If dialog creation fails, log it
            self.logger.error(
                "Failed to create error dialog: %s", str(dialog_error)
            )
            # Fallback to console
            self._console_error_output(exc_type, exc_value, exc_traceback)

    def _console_error_output(self, exc_type, exc_value, exc_traceback) -> None:
        """Output error to console as fallback.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        print(f"Unhandled {exc_type.__name__}: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    def handle_startup_error(self, error: Exception) -> None:
        """Handle errors that occur during application startup.

        Args:
            error: The exception that occurred during startup
        """
        error_msg = f"Failed to start 3D-MM application: {str(error)}"
        print(error_msg)

        # Try to show a dialog if possible
        try:
            from PySide6.QtWidgets import QApplication
            if not QApplication.instance():
                QApplication([])

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Startup Error")
            msg_box.setText("Application Startup Failed")
            msg_box.setInformativeText(str(error))
            msg_box.exec_()
        except RuntimeError:
            # If even this fails, just print to console
            print("Critical: Failed to show startup error dialog")

    def handle_graceful_shutdown(self, error: Optional[Exception] = None) -> None:
        """Handle graceful shutdown with optional error.

        Args:
            error: Optional exception that caused the shutdown
        """
        if error:
            self.logger.error(
                "Graceful shutdown due to error: %s", str(error)
            )
        else:
            self.logger.info("Graceful shutdown initiated")

        # Cleanup resources here if needed
        self.cleanup()

    def cleanup(self) -> None:
        """Cleanup exception handler resources."""
        self.uninstall_global_handler()
        self.logger.info("Exception handler cleaned up")

    @staticmethod
    def create_and_install(parent: Optional[QWidget] = None) -> "ExceptionHandler":
        """Factory method to create and install an exception handler.

        Args:
            parent: Parent widget for error dialogs

        Returns:
            Configured ExceptionHandler instance
        """
        handler = ExceptionHandler(parent)
        handler.install_global_handler()
        return handler
