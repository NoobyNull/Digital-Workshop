"""Parser interfaces for 3D model file parsing.

This module defines the abstract base classes for 3D model file parsers
used throughout the Candy-Cadence application.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class ModelFormat(Enum):
    """Enumeration of supported 3D model file formats."""

    STL = "stl"
    OBJ = "obj"
    THREE_MF = "3mf"
    STEP = "step"
    PLY = "ply"
    X3D = "x3d"


class ParseError(Exception):
    """Raised when model file parsing fails."""

    pass


class FileNotSupportedError(ParseError):
    """Raised when file format is not supported."""

    pass


class IParser(ABC):
    """Interface for 3D model file parsers."""

    @property
    @abstractmethod
    def supported_formats(self) -> List[ModelFormat]:
        """Get list of supported file formats.

        Returns:
            List of ModelFormat enums this parser supports
        """
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if parser can handle the file format, False otherwise
        """
        pass

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Dict[str, Any]:
        """Parse a 3D model file.

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
        pass

    @abstractmethod
    def get_model_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic information about the model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing basic model information:
            - format: ModelFormat enum
            - vertex_count: Number of vertices
            - face_count: Number of faces/triangles
            - file_size: File size in bytes
            - bounding_box: Tuple of (min_x, min_y, min_z, max_x, max_y, max_z)
            - has_materials: Boolean indicating if materials are present
            - has_textures: Boolean indicating if textures are present

        Raises:
            FileNotSupportedError: If file format is not supported
            ParseError: If analysis fails
        """
        pass

    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """Validate that a file can be parsed without errors.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid and can be parsed, False otherwise
        """
        pass

    @abstractmethod
    def get_parser_info(self) -> Dict[str, str]:
        """Get information about the parser implementation.

        Returns:
            Dictionary containing parser information:
            - name: Parser name
            - version: Parser version
            - author: Parser author
            - description: Parser description
        """
        pass


class IFormatDetector(ABC):
    """Interface for detecting 3D model file formats."""

    @abstractmethod
    def detect_format(self, file_path: Path) -> Optional[ModelFormat]:
        """Detect the format of a 3D model file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            ModelFormat enum if format is detected, None otherwise
        """
        pass

    @abstractmethod
    def get_format_confidence(self, file_path: Path) -> float:
        """Get confidence level for format detection.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Confidence level between 0.0 and 1.0
        """
        pass

    @abstractmethod
    def get_all_possible_formats(self) -> List[ModelFormat]:
        """Get list of all formats that can be detected.

        Returns:
            List of all detectable ModelFormat enums
        """
        pass


class IStreamingParser(ABC):
    """Interface for parsers that support streaming/progressive parsing."""

    @abstractmethod
    def parse_stream(self, file_path: Path, chunk_size: int = 8192) -> Any:
        """Parse a file using streaming/chunked approach.

        Args:
            file_path: Path to the model file to parse
            chunk_size: Size of chunks to read in bytes

        Returns:
            Iterator that yields parsed chunks/segments
        """
        pass

    @abstractmethod
    def can_parse_incremental(self) -> bool:
        """Check if parser supports incremental parsing.

        Returns:
            True if incremental parsing is supported, False otherwise
        """
        pass

    @abstractmethod
    def get_incremental_progress(self) -> float:
        """Get current progress of incremental parsing.

        Returns:
            Progress value between 0.0 and 1.0
        """
        pass


class IProgressiveParser(IParser, IStreamingParser):
    """Combined interface for parsers that support both regular and progressive parsing."""

    def can_parse_incremental(self) -> bool:
        """Check if parser supports incremental parsing.

        Returns:
            True if incremental parsing is supported, False otherwise
        """
        pass

    def get_incremental_progress(self) -> float:
        """Get current progress of incremental parsing.

        Returns:
            Progress value between 0.0 and 1.0
        """
        pass


class IValidationParser(ABC):
    """Interface for parsers that support detailed validation."""

    @abstractmethod
    def validate_geometry(self, file_path: Path) -> Dict[str, Any]:
        """Validate the geometric integrity of a model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing validation results:
            - is_valid: Boolean indicating if geometry is valid
            - issues: List of validation issues found
            - statistics: Geometric statistics

        Raises:
            FileNotSupportedError: If file format is not supported
            ParseError: If validation fails
        """
        pass

    @abstractmethod
    def get_geometry_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed geometric statistics for a model file.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing geometric statistics:
            - vertex_count: Number of vertices
            - face_count: Number of faces
            - edge_count: Number of edges
            - component_count: Number of connected components
            - degeneracy_count: Number of degenerate faces
            - manifold: Boolean indicating if mesh is manifold

        Raises:
            FileNotSupportedError: If file format is not supported
            ParseError: If analysis fails
        """
        pass
