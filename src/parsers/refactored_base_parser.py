"""
Refactored Base Parser Implementation for Candy-Cadence

This module provides a comprehensive base parser implementation that follows the IParser interface
and includes performance optimizations, streaming support, and consistent error handling.

Key Features:
- Implements IParser interface for consistency
- Streaming support for large files
- Progressive loading capabilities
- Memory-efficient processing
- Comprehensive error handling and logging
- Performance monitoring and optimization
- Caching mechanisms
"""

import time
import gc
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor
import weakref

from src.core.interfaces.parser_interfaces import (
    IParser,
    IStreamingParser,
    IValidationParser,
    ModelFormat,
    ParseError,
    FileNotSupportedError,
)
from src.core.centralized_logging_service import (
    get_logging_service,
)
from src.core.exceptions import (
    ParsingError,
)
from src.core.performance_monitor import get_performance_monitor


class StreamingProgressCallback:
    """Enhanced progress callback for streaming operations."""

    def __init__(self, callback_func: Optional[Callable[[float, str], None]] = None) -> None:
        """TODO: Add docstring."""
        self.callback_func = callback_func
        self.last_report_time = 0
        self.report_interval = 0.05  # Report more frequently for streaming
        self.current_progress = 0.0
        self.current_message = ""
        self._lock = threading.Lock()

    def update(self, progress: float, message: str = "") -> None:
        """Update progress with thread safety."""
        with self._lock:
            self.current_progress = progress
            self.current_message = message

            current_time = time.time()
            if current_time - self.last_report_time >= self.report_interval:
                if self.callback_func:
                    self.callback_func(progress, message)
                self.last_report_time = current_time

    def get_current_progress(self) -> Tuple[float, str]:
        """Get current progress (thread-safe)."""
        with self._lock:
            return self.current_progress, self.current_message


class RefactoredBaseParser(IParser, IStreamingParser, IValidationParser, ABC):
    """
    Refactored base parser implementing IParser interface with enhanced features.

    This class provides:
    - Consistent interface implementation
    - Streaming support for large files
    - Progressive loading capabilities
    - Memory-efficient processing
    - Comprehensive error handling
    - Performance monitoring
    - Caching mechanisms
    """

    def __init__(self, parser_name: str, supported_formats: List[ModelFormat]) -> None:
        """
        Initialize the refactored base parser.

        Args:
            parser_name: Name of the parser
            supported_formats: List of supported ModelFormat enums
        """
        self.parser_name = parser_name
        self._supported_formats = supported_formats

        # Use centralized logging service
        self.logging_service = get_logging_service()
        self.performance_monitor = get_performance_monitor()

        # Cancellation support
        self._cancel_parsing = False
        self._cancel_lock = threading.Lock()

        # Streaming support
        self._streaming_enabled = True
        self._chunk_size = 8192  # 8KB chunks

        # Progressive loading support
        self._progressive_enabled = True
        self._current_progress = 0.0

        # Memory management
        self._memory_threshold = 2 * 1024 * 1024 * 1024  # 2GB
        self._gc_interval = 10000  # Garbage collect every 10k items

        # Caching (using weak references to avoid memory leaks)
        self._cache = weakref.WeakValueDictionary()
        self._cache_lock = threading.RLock()

        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"{parser_name}_")

        # Log parser initialization
        self.logging_service.log_info(
            f"Initialized {self.parser_name} parser",
            parser_name=parser_name,
            supported_formats=[fmt.value for fmt in supported_formats],
            features="streaming, progressive_loading, memory_optimized, error_recovery",
        )

    @property
    def supported_formats(self) -> List[ModelFormat]:
        """Get list of supported file formats."""
        return self._supported_formats.copy()

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if parser can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if parser can handle the file format, False otherwise
        """
        try:
            file_extension = file_path.suffix.lower()
            supported_extensions = [fmt.value for fmt in self._supported_formats]
            return file_extension in supported_extensions
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logging_service.log_warning(
                f"Error checking file format for {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="can_parse",
                error_type=type(e).__name__,
            )
            return False

    def parse(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Parse a 3D model file with enhanced error handling and performance monitoring.

        Args:
            file_path: Path to the model file to parse
            progress_callback: Optional callback for progress updates (0.0 to 1.0)

        Returns:
            Dictionary containing parsed model data

        Raises:
            FileNotSupportedError: If file format is not supported
            ParseError: If parsing fails
            FileNotFoundError: If file does not exist
        """
        # Validate file format
        if not self.can_parse(file_path):
            error = FileNotSupportedError(f"File format not supported by {self.parser_name}")
            self.logging_service.log_error(
                error,
                {
                    "file_path": str(file_path),
                    "parser_name": self.parser_name,
                    "supported_formats": [fmt.value for fmt in self._supported_formats],
                },
            )
            raise error

        # Check file existence
        if not file_path.exists():
            error = FileNotFoundError(f"File not found: {file_path}")
            self.logging_service.log_error(
                error,
                {"file_path": str(file_path), "operation": "file_existence_check"},
            )
            raise error

        # Check cache first
        cache_key = f"{file_path}_{hash(file_path.stat().st_mtime)}"
        with self._cache_lock:
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                self.logging_service.log_info(
                    f"Loaded {file_path} from cache",
                    file_path=str(file_path),
                    cache_key=cache_key,
                    operation="cache_hit",
                )
                return cached_result

        try:
            # Reset cancellation state
            self._reset_cancel_state()

            # Create enhanced progress callback
            streaming_callback = None
            if progress_callback:
                streaming_callback = StreamingProgressCallback(
                    lambda p, m: progress_callback(p / 100.0)  # Convert to 0-1 range
                )

            # Parse the file
            result = self._parse_file_internal(file_path, streaming_callback)

            # Cache the result
            with self._cache_lock:
                self._cache[cache_key] = result

            self.logging_service.log_info(
                f"Successfully parsed {file_path}",
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                parser_name=self.parser_name,
                cache_key=cache_key,
                operation="parse_success",
            )

            return result

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Use standardized error handling
            error_context = {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "parser_name": self.parser_name,
                "operation": "parse_file",
            }

            # Log the error with centralized service
            self.logging_service.log_error(e, error_context)

            # Convert to standardized parsing error
            if not isinstance(e, (ParseError, FileNotSupportedError, FileNotFoundError)):
                raise ParsingError(f"Failed to parse {file_path}: {str(e)}") from e
            else:
                raise
        finally:
            self._cleanup_resources()

    def get_model_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get basic information about the model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing basic model information
        """
        try:
            if not self.can_parse(file_path):
                raise FileNotSupportedError(f"File format not supported by {self.parser_name}")

            # Get file stats
            file_size = file_path.stat().st_size

            # Use lightweight analysis for model info
            info = self._get_model_info_internal(file_path)

            # Add common fields
            info.update(
                {
                    "format": self._get_primary_format(file_path),
                    "file_size": file_size,
                    "parser_name": self.parser_name,
                }
            )

            return info

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_context = {"file_path": str(file_path), "operation": "get_model_info"}
            self.logging_service.log_error(e, error_context)
            raise ParseError(f"Failed to get model info: {str(e)}")

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that a file can be parsed without errors.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid and can be parsed, False otherwise
        """
        try:
            if not self.can_parse(file_path):
                return False

            # Use lightweight validation
            return self._validate_file_internal(file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logging_service.log_warning(
                f"Validation failed for {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="validate_file",
            )
            return False

    def get_parser_info(self) -> Dict[str, str]:
        """
        Get information about the parser implementation.

        Returns:
            Dictionary containing parser information
        """
        return {
            "name": self.parser_name,
            "version": "2.0.0",  # Refactored version
            "author": "Candy-Cadence Parser Team",
            "description": f"Refactored {self.parser_name} parser with streaming and progressive loading support",
            "supported_formats": ", ".join([fmt.value for fmt in self._supported_formats]),
            "features": "streaming, progressive_loading, memory_optimized, error_recovery",
        }

    # Streaming Parser Interface

    def parse_stream(self, file_path: Path, chunk_size: int = 8192) -> Iterator[Any]:
        """
        Parse a file using streaming/chunked approach.

        Args:
            file_path: Path to the model file to parse
            chunk_size: Size of chunks to read in bytes

        Returns:
            Iterator that yields parsed chunks/segments
        """
        if not self._streaming_enabled:
            raise NotImplementedError(f"Streaming not supported by {self.parser_name}")

        self._chunk_size = chunk_size
        return self._parse_stream_internal(file_path)

    def can_parse_incremental(self) -> bool:
        """Check if parser supports incremental parsing."""
        return self._progressive_enabled

    def get_incremental_progress(self) -> float:
        """Get current progress of incremental parsing."""
        return self._current_progress

    # Validation Parser Interface

    def validate_geometry(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate the geometric integrity of a model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing validation results
        """
        try:
            if not self.can_parse(file_path):
                raise FileNotSupportedError(f"File format not supported by {self.parser_name}")

            return self._validate_geometry_internal(file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_context = {
                "file_path": str(file_path),
                "operation": "validate_geometry",
            }
            self.logging_service.log_error(e, error_context)
            raise ParseError(f"Geometry validation failed: {str(e)}")

    def get_geometry_stats(self, file_path: Path) -> Dict[str, Any]:
        """
        Get detailed geometric statistics for a model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing geometric statistics
        """
        try:
            if not self.can_parse(file_path):
                raise FileNotSupportedError(f"File format not supported by {self.parser_name}")

            return self._get_geometry_stats_internal(file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_context = {
                "file_path": str(file_path),
                "operation": "get_geometry_stats",
            }
            self.logging_service.log_error(e, error_context)
            raise ParseError(f"Failed to get geometry stats: {str(e)}")

    # Abstract methods to be implemented by subclasses

    @abstractmethod
    def _parse_file_internal(
        self,
        file_path: Path,
        progress_callback: Optional[StreamingProgressCallback] = None,
    ) -> Dict[str, Any]:
        """
        Internal method to parse a 3D model file.

        Args:
            file_path: Path to the 3D model file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data
        """

    @abstractmethod
    def _get_model_info_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method to get model information.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing model information
        """

    @abstractmethod
    def _validate_file_internal(self, file_path: Path) -> bool:
        """
        Internal method to validate file format.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid, False otherwise
        """

    @abstractmethod
    def _parse_stream_internal(self, file_path: Path) -> Iterator[Any]:
        """
        Internal method for streaming parsing.

        Args:
            file_path: Path to the model file

        Returns:
            Iterator yielding parsed chunks
        """

    @abstractmethod
    def _validate_geometry_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry validation.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing validation results
        """

    @abstractmethod
    def _get_geometry_stats_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry statistics.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing geometry statistics
        """

    # Utility methods

    def _get_primary_format(self, file_path: Path) -> ModelFormat:
        """Get the primary format for a file path."""
        extension = file_path.suffix.lower()
        for fmt in self._supported_formats:
            if fmt.value == extension:
                return fmt
        return self._supported_formats[0]  # Default to first supported format

    def _check_cancellation(self) -> None:
        """Check if parsing should be cancelled."""
        with self._cancel_lock:
            if self._cancel_parsing:
                raise ParseError("Parsing was cancelled")

    def _reset_cancel_state(self) -> None:
        """Reset the cancellation state."""
        with self._cancel_lock:
            self._cancel_parsing = False

    def cancel_parsing(self) -> None:
        """Cancel the current parsing operation."""
        with self._cancel_lock:
            self._cancel_parsing = True
        self.logging_service.log_info("Parsing cancellation requested")

    def _periodic_gc(self, count: int) -> None:
        """
        Perform periodic garbage collection for memory management.

        Args:
            count: Current count of processed items
        """
        if count % self._gc_interval == 0 and count > 0:
            gc.collect()
            self.logging_service.log_debug(f"Performed garbage collection at count {count}")

    def _update_progress(
        self,
        progress: float,
        message: str = "",
        callback: Optional[StreamingProgressCallback] = None,
    ) -> None:
        """
        Update parsing progress.

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
            callback: Progress callback to update
        """
        self._current_progress = progress / 100.0
        if callback:
            callback.update(progress, message)

    def _cleanup_resources(self) -> None:
        """Clean up resources after parsing."""
        try:
            # Force garbage collection
            gc.collect()

            # Reset progress
            self._current_progress = 0.0

            self.logging_service.log_debug("Resources cleaned up after parsing")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logging_service.log_warning(
                f"Error during resource cleanup: {str(e)}",
                operation="cleanup_resources",
            )

    def __del__(self) -> None:
        """Cleanup when parser is destroyed."""
        try:
            if hasattr(self, "_executor"):
                self._executor.shutdown(wait=False)
            self.logging_service.log_debug(f"Destroyed {self.parser_name} parser")
        except Exception:
            pass  # Ignore errors during destruction
