"""
STL format detection.

Detects whether an STL file is binary or ASCII format.
"""

import struct
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from .stl_models import STLFormat, STLParseError


class STLFormatDetector:
    """Detects STL file format (binary vs ASCII)."""

    # Binary STL format constants
    BINARY_HEADER_SIZE = 80
    BINARY_TRIANGLE_COUNT_SIZE = 4
    BINARY_TRIANGLE_SIZE = 50

    def __init__(self):
        """Initialize the format detector."""
        self.logger = get_logger("parsers.stl")

    def detect_format(self, file_path: Path) -> STLFormat:
        """
        Detect whether an STL file is binary or ASCII format.

        Args:
            file_path: Path to the STL file

        Returns:
            Detected STL format

        Raises:
            STLParseError: If format cannot be determined
        """
        try:
            with open(file_path, "rb") as file:
                # Read first 80 bytes (header) and check for ASCII indicators
                header = file.read(self.BINARY_HEADER_SIZE)

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
                file.seek(self.BINARY_HEADER_SIZE)
                count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) == self.BINARY_TRIANGLE_COUNT_SIZE:
                    triangle_count = struct.unpack("<I", count_bytes)[0]

                    # Verify file size matches expected binary format size
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    expected_size = (
                        self.BINARY_HEADER_SIZE
                        + self.BINARY_TRIANGLE_COUNT_SIZE
                        + (triangle_count * self.BINARY_TRIANGLE_SIZE)
                    )

                    if file_size == expected_size:
                        return STLFormat.BINARY

                return STLFormat.UNKNOWN

        except Exception as e:
            self.logger.error(f"Error detecting STL format: {str(e)}")
            raise STLParseError(f"Failed to detect STL format: {str(e)}")
