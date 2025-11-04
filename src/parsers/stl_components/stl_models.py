"""
STL data models and exceptions.

Provides data structures for STL parsing and custom exceptions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from src.parsers.base_parser import (
    Triangle,
    Vector3D,
    ModelStats,
    ParseError,
    ProgressCallback,
)


class STLFormat(Enum):
    """STL file format types."""

    BINARY = "binary"
    ASCII = "ascii"
    UNKNOWN = "unknown"


@dataclass
class STLModel:
    """Complete 3D model representation with geometry and statistics."""

    header: str
    triangles: List[Triangle]
    stats: ModelStats

    def get_vertices(self) -> List[Vector3D]:
        """Get all unique vertices from all triangles."""
        vertices = []
        for triangle in self.triangles:
            vertices.extend(triangle.get_vertices())
        return vertices

    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        return (
            len(self.header.encode("utf-8"))
            + len(self.triangles) * (50 + 4 * 9)  # Rough estimate
            + 100  # Stats and other data
        )


class STLParseError(ParseError):
    """Custom exception for STL parsing errors."""


class STLProgressCallback(ProgressCallback):
    """Callback interface for progress reporting during parsing."""
