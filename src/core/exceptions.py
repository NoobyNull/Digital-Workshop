"""Comprehensive Exception Hierarchies for Candy-Cadence

This module provides a standardized exception hierarchy for the Candy-Cadence application,
ensuring consistent error handling across all modules.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path


class CandyCadenceException(Exception):
    """Base exception for all Candy-Cadence application errors."""
    
    def __init__(self, message: str, user_message: str = None, recovery_suggestions: List[str] = None, **kwargs):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.recovery_suggestions = recovery_suggestions or []
        self.context = kwargs
        self.error_code = kwargs.get('error_code', 'UNKNOWN_ERROR')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'user_message': self.user_message,
            'recovery_suggestions': self.recovery_suggestions,
            'error_code': self.error_code,
            'context': self.context
        }


# ===== PARSING EXCEPTIONS =====

class ParsingException(CandyCadenceException):
    """Base exception for all parsing-related errors."""
    
    def __init__(self, message: str, file_path: str = None, format_type: str = None, **kwargs):
        user_message = "The file format is not supported or the file is corrupted."
        recovery_suggestions = [
            "Check if the file format is supported",
            "Verify the file is not corrupted",
            "Try converting the file to a supported format"
        ]
        
        context = {
            'file_path': file_path,
            'format_type': format_type,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# Alias for backward compatibility
ParsingError = ParsingException


class UnsupportedFormatError(ParsingException):
    """Raised when a file format is not supported by the parser."""
    
    def __init__(self, file_path: str, format_type: str, supported_formats: List[str] = None, **kwargs):
        message = f"Unsupported format '{format_type}' for file: {file_path}"
        user_message = f"The file format '{format_type}' is not supported."
        
        if supported_formats:
            user_message += f" Supported formats: {', '.join(supported_formats)}"
        
        recovery_suggestions = [
            f"Convert the file to a supported format: {', '.join(supported_formats) if supported_formats else 'STL, OBJ, STEP, 3MF'}",
            "Check if the file extension matches the actual format",
            "Try opening the file with a different application to verify it"
        ]
        
        context = {
            'file_path': file_path,
            'format_type': format_type,
            'supported_formats': supported_formats,
            'error_code': 'UNSUPPORTED_FORMAT',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class CorruptedFileError(ParsingException):
    """Raised when a file appears to be corrupted or malformed."""
    
    def __init__(self, file_path: str, format_type: str, corruption_details: str = None, **kwargs):
        message = f"Corrupted file detected: {file_path}"
        if corruption_details:
            message += f" Details: {corruption_details}"
        
        user_message = "The file appears to be corrupted or malformed."
        
        recovery_suggestions = [
            "Try downloading the file again if it was downloaded from the internet",
            "Check if the file was transferred correctly",
            "Try opening the file with a different application",
            "Contact the file's creator if possible"
        ]
        
        context = {
            'file_path': file_path,
            'format_type': format_type,
            'corruption_details': corruption_details,
            'error_code': 'CORRUPTED_FILE',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== DATABASE EXCEPTIONS =====

class DatabaseException(CandyCadenceException):
    """Base exception for all database-related errors."""
    
    def __init__(self, message: str, operation: str = None, table_name: str = None, **kwargs):
        user_message = "A database operation failed. Your data may be temporarily unavailable."
        recovery_suggestions = [
            "Check database connection",
            "Verify database file permissions",
            "Restart the application",
            "Check available disk space"
        ]
        
        context = {
            'operation': operation,
            'table_name': table_name,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails."""
    
    def __init__(self, database_path: str, connection_details: str = None, **kwargs):
        message = f"Database connection failed for: {database_path}"
        if connection_details:
            message += f" Details: {connection_details}"
        
        user_message = "Unable to connect to the database. The application data may be temporarily unavailable."
        
        recovery_suggestions = [
            "Check if the database file exists and is accessible",
            "Verify file permissions on the database directory",
            "Ensure no other application is using the database",
            "Restart the application"
        ]
        
        context = {
            'database_path': database_path,
            'connection_details': connection_details,
            'error_code': 'DATABASE_CONNECTION_ERROR',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== FILE SYSTEM EXCEPTIONS =====

class FileSystemException(CandyCadenceException):
    """Base exception for all file system-related errors."""
    
    def __init__(self, message: str, file_path: str = None, operation: str = None, **kwargs):
        user_message = "A file operation failed. Please check file permissions and paths."
        recovery_suggestions = [
            "Check file path and permissions",
            "Verify the file exists",
            "Try running as administrator",
            "Check available disk space"
        ]
        
        context = {
            'file_path': file_path,
            'operation': operation,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# Alias for backward compatibility
FileSystemError = FileSystemException


class FileNotFoundException(FileSystemException):
    """Raised when a required file is not found."""
    
    def __init__(self, file_path: str, search_locations: List[str] = None, **kwargs):
        message = f"File not found: {file_path}"
        user_message = f"The file '{Path(file_path).name}' could not be found."
        
        if search_locations:
            user_message += f" Searched in: {', '.join(search_locations)}"
        
        recovery_suggestions = [
            "Verify the file path is correct",
            "Check if the file was moved or deleted",
            "Search for the file in different locations",
            "Restore the file from backup if available"
        ]
        
        context = {
            'file_path': file_path,
            'search_locations': search_locations,
            'error_code': 'FILE_NOT_FOUND',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== VALIDATION EXCEPTIONS =====

class ValidationException(CandyCadenceException):
    """Base exception for all validation-related errors."""
    
    def __init__(self, message: str, field_name: str = None, value: Any = None, **kwargs):
        user_message = "Data validation failed. Please check the input values."
        recovery_suggestions = [
            "Check the format of input data",
            "Verify all required fields are provided",
            "Ensure values are within acceptable ranges"
        ]
        
        context = {
            'field_name': field_name,
            'value': value,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# Alias for backward compatibility
ValidationError = ValidationException


# ===== MEMORY EXCEPTIONS =====

class MemoryException(CandyCadenceException):
    """Base exception for all memory-related errors."""
    
    def __init__(self, message: str, operation: str = None, memory_usage: int = None, **kwargs):
        user_message = "The application ran out of memory. Try closing other applications."
        recovery_suggestions = [
            "Close other applications",
            "Restart the application",
            "Use smaller files",
            "Check available RAM"
        ]
        
        context = {
            'operation': operation,
            'memory_usage': memory_usage,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class OutOfMemoryError(MemoryException):
    """Raised when the application runs out of memory."""
    
    def __init__(self, operation: str, memory_usage: int, available_memory: int = None, **kwargs):
        message = f"Out of memory during {operation}. Usage: {memory_usage} bytes"
        if available_memory:
            message += f", Available: {available_memory} bytes"
        
        user_message = "The application has run out of memory and cannot continue this operation."
        
        recovery_suggestions = [
            "Close other applications to free up memory",
            "Restart the application",
            "Use smaller files or reduce batch sizes",
            "Consider upgrading your system's RAM"
        ]
        
        context = {
            'operation': operation,
            'memory_usage': memory_usage,
            'available_memory': available_memory,
            'error_code': 'OUT_OF_MEMORY',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== CONFIGURATION EXCEPTIONS =====

class ConfigurationException(CandyCadenceException):
    """Base exception for all configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None, config_source: str = None, **kwargs):
        user_message = "A configuration error occurred. Some features may not work correctly."
        recovery_suggestions = [
            "Reset to default settings",
            "Check configuration file",
            "Reinstall the application",
            "Contact support"
        ]
        
        context = {
            'config_key': config_key,
            'config_source': config_source,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class InvalidConfigurationException(ConfigurationException):
    """Raised when configuration values are invalid."""
    
    def __init__(self, config_key: str, config_value: Any, expected_type: str = None, **kwargs):
        message = f"Invalid configuration value for {config_key}: {config_value}"
        if expected_type:
            message += f" (expected type: {expected_type})"
        
        user_message = f"The configuration setting '{config_key}' has an invalid value."
        
        recovery_suggestions = [
            "Check the configuration file for syntax errors",
            "Reset the setting to its default value",
            "Consult the documentation for valid values",
            "Restore configuration from a backup"
        ]
        
        context = {
            'config_key': config_key,
            'config_value': config_value,
            'expected_type': expected_type,
            'error_code': 'INVALID_CONFIGURATION',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== PERFORMANCE EXCEPTIONS =====

class PerformanceException(CandyCadenceException):
    """Base exception for all performance-related issues."""
    
    def __init__(self, message: str, operation: str = None, duration: float = None, **kwargs):
        user_message = "A performance issue was detected. The operation may take longer than expected."
        recovery_suggestions = [
            "Close other applications",
            "Use smaller files",
            "Wait for operation to complete",
            "Restart the application"
        ]
        
        context = {
            'operation': operation,
            'duration': duration,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class TimeoutException(PerformanceException):
    """Raised when an operation takes too long."""
    
    def __init__(self, operation: str, timeout_duration: float, actual_duration: float = None, **kwargs):
        message = f"Operation '{operation}' timed out after {timeout_duration} seconds"
        if actual_duration:
            message += f" (actual duration: {actual_duration} seconds)"
        
        user_message = f"The operation '{operation}' is taking longer than expected and has been cancelled."
        
        recovery_suggestions = [
            "Try the operation again with smaller data",
            "Close other applications to free up resources",
            "Check system performance and available memory",
            "Consider breaking the operation into smaller parts"
        ]
        
        context = {
            'operation': operation,
            'timeout_duration': timeout_duration,
            'actual_duration': actual_duration,
            'error_code': 'TIMEOUT_ERROR',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# ===== UI EXCEPTIONS =====

class UIException(CandyCadenceException):
    """Base exception for all user interface-related errors."""
    
    def __init__(self, message: str, ui_component: str = None, **kwargs):
        user_message = "A user interface error occurred. The application will continue to function."
        recovery_suggestions = [
            "Restart the application",
            "Try different theme",
            "Check display settings",
            "Update graphics drivers"
        ]
        
        context = {
            'ui_component': ui_component,
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


class WidgetException(UIException):
    """Raised when a UI widget encounters an error."""
    
    def __init__(self, widget_type: str, operation: str, widget_details: str = None, **kwargs):
        message = f"Widget error in {widget_type} during {operation}"
        if widget_details:
            message += f": {widget_details}"
        
        user_message = f"A user interface component encountered an error."
        
        recovery_suggestions = [
            "Try refreshing the interface",
            "Restart the affected dialog or window",
            "Check if the issue persists after restart",
            "Try using a different theme"
        ]
        
        context = {
            'widget_type': widget_type,
            'operation': operation,
            'widget_details': widget_details,
            'error_code': 'WIDGET_ERROR',
            **kwargs
        }
        
        super().__init__(message, user_message, recovery_suggestions, **context)


# Exception mapping for easy lookup
EXCEPTION_MAPPING = {
    'UNSUPPORTED_FORMAT': UnsupportedFormatError,
    'CORRUPTED_FILE': CorruptedFileError,
    'DATABASE_CONNECTION_ERROR': DatabaseConnectionError,
    'FILE_NOT_FOUND': FileNotFoundException,
    'OUT_OF_MEMORY': OutOfMemoryError,
    'INVALID_CONFIGURATION': InvalidConfigurationException,
    'TIMEOUT_ERROR': TimeoutException,
    'WIDGET_ERROR': WidgetException,
}


def create_exception_from_code(error_code: str, *args, **kwargs) -> CandyCadenceException:
    """Create an exception instance from an error code."""
    exception_class = EXCEPTION_MAPPING.get(error_code, CandyCadenceException)
    return exception_class(*args, **kwargs)


def is_retryable_exception(exception: Exception) -> bool:
    """Check if an exception is retryable."""
    retryable_exceptions = (
        DatabaseConnectionError,
        TimeoutException,
    )
    
    return isinstance(exception, retryable_exceptions)


def get_user_friendly_message(exception: Exception) -> str:
    """Get a user-friendly message from an exception."""
    if hasattr(exception, 'user_message'):
        return exception.user_message
    elif hasattr(exception, 'message'):
        return exception.message
    else:
        return str(exception)


def get_recovery_suggestions(exception: Exception) -> List[str]:
    """Get recovery suggestions from an exception."""
    if hasattr(exception, 'recovery_suggestions'):
        return exception.recovery_suggestions
    else:
        return [
            "Restart the application",
            "Check the application logs for more details",
            "Contact support if the problem persists"
        ]