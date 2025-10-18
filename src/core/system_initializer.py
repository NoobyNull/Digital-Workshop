#!/usr/bin/env python3
"""
System Initializer Module

This module contains the SystemInitializer class responsible for
setting up the application environment, directories, and logging.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QStandardPaths, QDir
from PySide6.QtWidgets import QApplication

from .application_config import ApplicationConfig
from .logging_config import setup_logging


class SystemInitializer:
    """Handles system-level initialization for the application."""

    def __init__(self, config: ApplicationConfig):
        """Initialize the SystemInitializer with application configuration.

        Args:
            config: Application configuration instance
        """
        self.config = config
        self.logger: Optional[logging.Logger] = None

    def initialize(self) -> bool:
        """Perform all system initialization steps.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self._setup_application_metadata()
            self._setup_high_dpi_support()
            self._setup_logging()
            self._create_directories()
            self.logger.info("System initialization completed successfully")
            return True
        except RuntimeError as e:
            print(f"System initialization failed: {str(e)}")
            return False

    def _setup_application_metadata(self) -> None:
        """Set application metadata in QApplication."""
        QApplication.setApplicationName(self.config.name)
        QApplication.setApplicationVersion(self.config.version)
        QApplication.setOrganizationName(self.config.organization_name)
        QApplication.setOrganizationDomain(self.config.organization_domain)

    def _setup_high_dpi_support(self) -> None:
        """Enable high DPI support for better display on modern screens."""
        if self.config.enable_high_dpi:
            # Note: These are deprecated in PySide6 but kept for compatibility
            from PySide6.QtCore import Qt
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    def _setup_logging(self) -> None:
        """Initialize the logging system."""
        # Get the app data path for logs
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        log_dir = os.path.join(app_data_path, "logs")

        if self.config.enable_file_logging:
            setup_logging(
                log_level=self.config.log_level,
                log_dir=log_dir,
                enable_console=True
            )
        else:
            setup_logging(
                log_level=self.config.log_level,
                log_dir=log_dir,
                enable_console=True
            )

        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging system initialized")

    def _create_directories(self) -> None:
        """Create necessary directories for the application."""
        app_data_path = QStandardPaths.writableLocation(
            QStandardPaths.AppDataLocation
        )

        # Define required directories
        app_dirs = [
            app_data_path,
            os.path.join(app_data_path, "models"),
            os.path.join(app_data_path, "logs"),
            os.path.join(app_data_path, "temp"),
            os.path.join(app_data_path, "cache"),
            os.path.join(app_data_path, "themes"),
        ]

        # Create directories
        for dir_path in app_dirs:
            if QDir().mkpath(dir_path):
                self.logger.debug("Created directory: %s", dir_path)
            else:
                self.logger.debug("Directory already exists: %s", dir_path)

        self.logger.debug("Application directories created")

    def get_app_data_path(self) -> Path:
        """Get the application data directory path.

        Returns:
            Path to the application data directory
        """
        return Path(
            QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        )

    def get_cache_path(self) -> Path:
        """Get the cache directory path.

        Returns:
            Path to the cache directory
        """
        return self.get_app_data_path() / "cache"

    def get_logs_path(self) -> Path:
        """Get the logs directory path.

        Returns:
            Path to the logs directory
        """
        return self.get_app_data_path() / "logs"

    def get_models_path(self) -> Path:
        """Get the models directory path.

        Returns:
            Path to the models directory
        """
        return self.get_app_data_path() / "models"

    def get_temp_path(self) -> Path:
        """Get the temporary directory path.

        Returns:
            Path to the temporary directory
        """
        return self.get_app_data_path() / "temp"

    def cleanup_temp_files(self) -> None:
        """Clean up temporary files on startup."""
        temp_path = self.get_temp_path()
        if temp_path.exists():
            try:
                import time

                # Remove old temp files (older than 1 day)
                import time
                current_time = time.time()
                one_day_ago = current_time - 86400  # 24 hours in seconds

                for file_path in temp_path.glob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < one_day_ago:
                        try:
                            file_path.unlink()
                            self.logger.debug("Removed old temp file: %s", file_path)
                        except OSError as e:
                            self.logger.warning("Failed to remove temp file %s: %s", file_path, e)

                self.logger.info("Temporary file cleanup completed")
            except OSError as e:
                self.logger.warning("Failed to cleanup temp files: %s", e)
