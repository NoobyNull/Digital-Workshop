"""
STL Format Detection Module

This module provides format detection functionality for STL files,
determining whether a file is binary or ASCII format.

Single Responsibility: STL format detection and validation.
"""

import struct
from enum import Enum
from pathlib import Path
from typing import Optional

from src.core.interfaces.parser_interfaces import ParseError


class STLFormat(Enum):
    """STL file format types."""

    BINARY = "binary"
    ASCII = "ascii"
    UNKNOWN = "unknown"


class STLFormatError(ParseError):
    """Custom exception for STL format detection errors."""


class STLFormatDetector:
    """
    Detects STL file format (binary vs ASCII).

    Features:
    - Reliable binary/ASCII detection
    - File size validation
    - Header analysis
    - Triangle count verification
    """

    # Binary STL format constants
    BINARY_HEADER_SIZE = 80
    BINARY_TRIANGLE_COUNT_SIZE = 4
    BINARY_TRIANGLE_SIZE = (
        50  # 12 bytes for normal + 36 bytes for vertices + 2 bytes for attribute
    )

    @classmethod
    def detect_format(cls, file_path: Path) -> STLFormat:
        """
        Detect whether an STL file is binary or ASCII format.

        Args:
            file_path: Path to the STL file

        Returns:
            Detected STL format

        Raises:
            STLFormatError: If format cannot be determined
        """
        try:
            with open(file_path, "rb") as file:
                # Read first 80 bytes (header) and check for ASCII indicators
                header = file.read(cls.BINARY_HEADER_SIZE)

                # Check if header contains ASCII indicators
                header_text = header.decode("utf-8", errors="ignore").lower()
                if "solid" in header_text and header_text.count("\x00") < 5:
                    # Likely ASCII, but verify by checking for "facet normal" keyword
                    file.seek(0)
                    first_line = (
                        file.readline().decode("utf-8", errors="ignore").strip()
                    )
                    if first_line.lower().startswith("solid"):
                        return STLFormat.ASCII

                # Check if it's valid binary by attempting to read triangle count
                file.seek(cls.BINARY_HEADER_SIZE)
                count_bytes = file.read(cls.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) == cls.BINARY_TRIANGLE_COUNT_SIZE:
                    triangle_count = struct.unpack("<I", count_bytes)[0]

                    # Verify file size matches expected binary format size
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    expected_size = (
                        cls.BINARY_HEADER_SIZE
                        + cls.BINARY_TRIANGLE_COUNT_SIZE
                        + (triangle_count * cls.BINARY_TRIANGLE_SIZE)
                    )

                    if file_size == expected_size:
                        return STLFormat.BINARY

                return STLFormat.UNKNOWN

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise STLFormatError(f"Failed to detect STL format: {str(e)}") from e

    @classmethod
    def is_binary(cls, file_path: Path) -> bool:
        """
        Check if an STL file is in binary format.

        Args:
            file_path: Path to the STL file

        Returns:
            True if binary format, False otherwise
        """
        return cls.detect_format(file_path) == STLFormat.BINARY

    @classmethod
    def is_ascii(cls, file_path: Path) -> bool:
        """
        Check if an STL file is in ASCII format.

        Args:
            file_path: Path to the STL file

        Returns:
            True if ASCII format, False otherwise
        """
        return cls.detect_format(file_path) == STLFormat.ASCII

    @classmethod
    def get_triangle_count(
        cls, file_path: Path, format_type: Optional[STLFormat] = None
    ) -> int:
        """
        Get triangle count from STL file without loading full geometry.

        Args:
            file_path: Path to the STL file
            format_type: Optional pre-detected format type

        Returns:
            Triangle count

        Raises:
            STLFormatError: If format cannot be determined or count cannot be read
        """
        if format_type is None:
            format_type = cls.detect_format(file_path)

        if format_type == STLFormat.BINARY:
            return cls._get_binary_triangle_count(file_path)
        if format_type == STLFormat.ASCII:
            return cls._get_ascii_triangle_count(file_path)
        raise STLFormatError("Unable to determine STL format")

    @classmethod
    def _get_binary_triangle_count(cls, file_path: Path) -> int:
        """
        Get triangle count from binary STL.

        Args:
            file_path: Path to the binary STL file

        Returns:
            Triangle count

        Raises:
            STLFormatError: If count cannot be read
        """
        try:
            with open(file_path, "rb") as file:
                # Skip header
                file.seek(cls.BINARY_HEADER_SIZE)

                # Read triangle count
                count_bytes = file.read(cls.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) != cls.BINARY_TRIANGLE_COUNT_SIZE:
                    raise STLFormatError(
                        "Invalid binary STL: cannot read triangle count"
                    )

                triangle_count = struct.unpack("<I", count_bytes)[0]
                return triangle_count

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise STLFormatError(
                f"Failed to read binary triangle count: {str(e)}"
            ) from e

    @classmethod
    def _get_ascii_triangle_count(cls, file_path: Path) -> int:
        """
        Get triangle count from ASCII STL.

        Args:
            file_path: Path to the ASCII STL file

        Returns:
            Triangle count

        Raises:
            STLFormatError: If count cannot be determined
        """
        try:
            triangle_count = 0

            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    if line.strip().lower().startswith("facet normal"):
                        triangle_count += 1

            return triangle_count

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise STLFormatError(
                f"Failed to read ASCII triangle count: {str(e)}"
            ) from e
