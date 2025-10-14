"""
UI Loader utility module for 3D-MM application.

This module provides functions for loading .ui files and creating UI components
from Qt Designer files, with proper error handling and logging support.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from PySide6.QtCore import QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import QApplication

from core.logging_config import get_logger

# Type variable for generic widget types
T = TypeVar('T', bound=QObject)


class UILoadError(Exception):
    """Exception raised when UI file loading fails."""
    pass


class CustomUiLoader(QUiLoader):
    """
    Custom UI loader that supports widget creation with proper error handling.
    
    Extends QUiLoader to provide better error handling and logging for UI file loading.
    """
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the custom UI loader.
        
        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
    
    def createWidget(self, className: str, parent: Optional[QObject] = None, name: str = "") -> Optional[QWidget]:
        """
        Create a widget with custom error handling.
        
        Args:
            className: Name of the widget class to create
            parent: Parent widget (optional)
            name: Object name for the widget (optional)
            
        Returns:
            Created widget or None if creation failed
        """
        try:
            widget = super().createWidget(className, parent, name)
            if widget is None:
                self.logger.warning(f"Failed to create widget of class: {className}")
            return widget
        except Exception as e:
            self.logger.error(f"Error creating widget {className}: {str(e)}")
            return None


def get_ui_file_path(ui_file_name: str) -> Path:
    """
    Get the absolute path to a UI file in the src/ui directory.
    
    Args:
        ui_file_name: Name of the UI file (e.g., "main_window.ui")
        
    Returns:
        Absolute path to the UI file
        
    Raises:
        UILoadError: If the UI file doesn't exist
    """
    # Get the directory where this module is located
    ui_dir = Path(__file__).parent
    
    # Construct the full path to the UI file
    ui_file_path = ui_dir / ui_file_name
    
    # Check if the file exists
    if not ui_file_path.exists():
        raise UILoadError(f"UI file not found: {ui_file_path}")
    
    return ui_file_path


def load_ui(ui_file_name: str, parent: Optional[QObject] = None, custom_widgets: Optional[dict] = None) -> Optional[QObject]:
    """
    Load a UI file and return the created widget.
    
    Args:
        ui_file_name: Name of the UI file (e.g., "main_window.ui")
        parent: Parent QObject for the loaded UI (optional)
        custom_widgets: Dictionary of custom widget classes to register (optional)
        
    Returns:
        Loaded widget or None if loading failed
        
    Raises:
        UILoadError: If the UI file cannot be loaded
    """
    logger = get_logger(__name__)
    logger.debug(f"Loading UI file: {ui_file_name}")
    
    try:
        # Get the path to the UI file
        ui_file_path = get_ui_file_path(ui_file_name)
        
        # Create a custom loader
        loader = CustomUiLoader(parent)
        
        # Register custom widgets if provided
        if custom_widgets:
            for widget_name, widget_class in custom_widgets.items():
                loader.registerCustomWidget(widget_name, widget_class)
                logger.debug(f"Registered custom widget: {widget_name}")
        
        # Load the UI file
        widget = loader.load(ui_file_path, parent)
        
        if widget is None:
            raise UILoadError(f"Failed to load UI from file: {ui_file_path}")
        
        logger.info(f"Successfully loaded UI file: {ui_file_name}")
        return widget
        
    except Exception as e:
        error_msg = f"Error loading UI file {ui_file_name}: {str(e)}"
        logger.error(error_msg)
        raise UILoadError(error_msg) from e


def load_ui_with_type(ui_file_name: str, widget_type: Type[T], parent: Optional[QObject] = None) -> Optional[T]:
    """
    Load a UI file and return it as a specific widget type.
    
    Args:
        ui_file_name: Name of the UI file (e.g., "main_window.ui")
        widget_type: Expected widget type (e.g., QMainWindow)
        parent: Parent QObject for the loaded UI (optional)
        
    Returns:
        Loaded widget as the specified type or None if loading failed
        
    Raises:
        UILoadError: If the UI file cannot be loaded or is not of the expected type
    """
    logger = get_logger(__name__)
    logger.debug(f"Loading UI file with type {widget_type.__name__}: {ui_file_name}")
    
    try:
        # Get the path to the UI file
        ui_file_path = get_ui_file_path(ui_file_name)
        
        # Create a custom loader
        loader = CustomUiLoader(parent)
        
        # Load the UI file
        widget = loader.load(ui_file_path, parent)
        
        if widget is None:
            return None
        
        # Check if the widget is of the expected type
        if not isinstance(widget, widget_type):
            error_msg = f"UI file {ui_file_name} loaded as {type(widget).__name__}, expected {widget_type.__name__}"
            logger.error(error_msg)
            raise UILoadError(error_msg)
        
        return widget
        
    except Exception as e:
        error_msg = f"Error loading UI file {ui_file_name} as {widget_type.__name__}: {str(e)}"
        logger.error(error_msg)
        raise UILoadError(error_msg) from e


def safe_load_ui(ui_file_name: str, parent: Optional[QObject] = None, fallback_widget: Optional[QWidget] = None) -> Optional[QWidget]:
    """
    Load a UI file with fallback handling.
    
    This function attempts to load a UI file and returns a fallback widget
    if loading fails, ensuring the application can continue running.
    
    Args:
        ui_file_name: Name of the UI file (e.g., "main_window.ui")
        parent: Parent QObject for the loaded UI (optional)
        fallback_widget: Widget to return if loading fails (optional)
        
    Returns:
        Loaded widget or fallback widget if loading failed
    """
    logger = get_logger(__name__)
    
    try:
        return load_ui(ui_file_name, parent)
    except UILoadError as e:
        logger.warning(f"Failed to load UI file {ui_file_name}, using fallback: {str(e)}")
        return fallback_widget


def validate_ui_file(ui_file_name: str) -> bool:
    """
    Validate that a UI file exists and is readable.
    
    Args:
        ui_file_name: Name of the UI file to validate
        
    Returns:
        True if the UI file is valid, False otherwise
    """
    logger = get_logger(__name__)
    
    try:
        ui_file_path = get_ui_file_path(ui_file_name)
        
        # Try to read the file
        with open(ui_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic validation - check if it contains expected UI elements
        if '<?xml version="1.0" encoding="UTF-8"?>' not in content:
            logger.warning(f"UI file {ui_file_name} may not be a valid Qt UI file")
            return False
        
        if '<ui version="4.0">' not in content:
            logger.warning(f"UI file {ui_file_name} may not be a valid Qt UI file (version 4.0)")
            return False
        
        logger.debug(f"UI file {ui_file_name} is valid")
        return True
        
    except Exception as e:
        logger.error(f"Error validating UI file {ui_file_name}: {str(e)}")
        return False


def get_available_ui_files() -> list[str]:
    """
    Get a list of all available UI files in the src/ui directory.
    
    Returns:
        List of UI file names
    """
    logger = get_logger(__name__)
    
    try:
        ui_dir = Path(__file__).parent
        ui_files = list(ui_dir.glob("*.ui"))
        file_names = [f.name for f in ui_files]
        
        logger.debug(f"Found {len(file_names)} UI files: {', '.join(file_names)}")
        return file_names
        
    except Exception as e:
        logger.error(f"Error getting UI file list: {str(e)}")
        return []