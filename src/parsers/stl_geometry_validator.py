"""
STL Geometry Validation Module

This module provides geometry validation and statistics functionality for STL files.

Single Responsibility: STL geometry validation and statistical analysis.
"""

import math
import struct
from pathlib import Path
from typing import Any, Dict

from src.core.interfaces.parser_interfaces import ParseError
from src.parsers.stl_format_detector import STLFormat, STLFormatDetector, STLFormatError


class STLGeometryError(ParseError):
    """Custom exception for STL geometry validation errors."""


class STLGeometryValidator:
    """
    Validates STL geometry and provides statistical analysis.

    Features:
    - Geometry validation (degenerate triangles, etc.)
    - Statistical analysis (vertex count, bounds, etc.)
    - Format-agnostic validation
    - Efficient sampling for large files
    """

    # Binary STL format constants (inherited from detector)
    BINARY_HEADER_SIZE = STLFormatDetector.BINARY_HEADER_SIZE
    BINARY_TRIANGLE_COUNT_SIZE = STLFormatDetector.BINARY_TRIANGLE_COUNT_SIZE
    BINARY_TRIANGLE_SIZE = STLFormatDetector.BINARY_TRIANGLE_SIZE

    @classmethod
    def validate_geometry(cls, file_path: Path) -> Dict[str, Any]:
        """
        Validate STL geometry.

        Args:
            file_path: Path to the STL file

        Returns:
            Dictionary containing validation results with keys:
            - is_valid: bool
            - issues: List[str]
            - statistics: Dict[str, Any]

        Raises:
            STLGeometryError: If validation fails critically
        """
        try:
            # Detect format
            format_type = STLFormatDetector.detect_format(file_path)

            if format_type == STLFormat.UNKNOWN:
                return {
                    "is_valid": False,
                    "issues": ["Unable to determine STL format"],
                    "statistics": {},
                }

            issues = []
            stats = {}

            if format_type == STLFormat.BINARY:
                binary_results = cls._validate_binary_geometry(file_path)
                issues.extend(binary_results["issues"])
                stats.update(binary_results["statistics"])

            elif format_type == STLFormat.ASCII:
                ascii_results = cls._validate_ascii_geometry(file_path)
                issues.extend(ascii_results["issues"])
                stats.update(ascii_results["statistics"])

            return {"is_valid": len(issues) == 0, "issues": issues, "statistics": stats}

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "statistics": {},
            }

    @classmethod
    def _validate_binary_geometry(cls, file_path: Path) -> Dict[str, Any]:
        """
        Validate binary STL geometry by sampling.

        Args:
            file_path: Path to the binary STL file

        Returns:
            Dictionary with issues and statistics
        """
        issues = []
        stats = {}

        try:
            with open(file_path, "rb") as file:
                file.seek(cls.BINARY_HEADER_SIZE + cls.BINARY_TRIANGLE_COUNT_SIZE)

                # Read first triangle
                triangle_data = file.read(cls.BINARY_TRIANGLE_SIZE)
                if len(triangle_data) == cls.BINARY_TRIANGLE_SIZE:
                    values = struct.unpack("<ffffffffffffH", triangle_data)

                    # Check for degenerate triangles
                    v1 = [values[3], values[4], values[5]]
                    v2 = [values[6], values[7], values[8]]
                    v3 = [values[9], values[10], values[11]]

                    # Calculate triangle area
                    area = cls._calculate_triangle_area(v1, v2, v3)

                    if area < 1e-10:
                        issues.append("Degenerate triangles detected")

                    stats["sample_triangle_area"] = area

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            issues.append(f"Binary validation error: {str(e)}")

        return {"issues": issues, "statistics": stats}

    @classmethod
    def _validate_ascii_geometry(cls, file_path: Path) -> Dict[str, Any]:
        """
        Validate ASCII STL geometry by sampling.

        Args:
            file_path: Path to the ASCII STL file

        Returns:
            Dictionary with issues and statistics
        """
        issues = []
        stats = {}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                first_line = file.readline().strip().lower()
                if not first_line.startswith("solid"):
                    issues.append("Invalid ASCII STL header")

                # Check for basic triangle structure
                content = file.read(500).lower()
                if "facet normal" not in content or "vertex" not in content:
                    issues.append("No valid triangle data found")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            issues.append(f"ASCII validation error: {str(e)}")

        return {"issues": issues, "statistics": stats}

    @classmethod
    def _calculate_triangle_area(cls, v1: list, v2: list, v3: list) -> float:
        """
        Calculate the area of a triangle given three vertices.

        Args:
            v1, v2, v3: Triangle vertices as [x, y, z] lists

        Returns:
            Triangle area
        """
        # Cross product magnitude / 2
        area = 0.5 * math.sqrt(
            ((v2[0] - v1[0]) * (v3[1] - v1[1]) - (v3[0] - v1[0]) * (v2[1] - v1[1])) ** 2
            + ((v2[1] - v1[1]) * (v3[2] - v1[2]) - (v3[1] - v1[1]) * (v2[2] - v1[2])) ** 2
            + ((v2[2] - v1[2]) * (v3[0] - v1[0]) - (v3[2] - v1[2]) * (v2[0] - v1[0])) ** 2
        )
        return area

    @classmethod
    def get_geometry_stats(cls, file_path: Path) -> Dict[str, Any]:
        """
        Get geometry statistics for an STL file.

        Args:
            file_path: Path to the STL file

        Returns:
            Dictionary containing geometric statistics

        Raises:
            STLGeometryError: If statistics cannot be computed
        """
        try:
            # Detect format and get triangle count
            format_type = STLFormatDetector.detect_format(file_path)
            triangle_count = STLFormatDetector.get_triangle_count(file_path, format_type)

            # Basic statistics
            stats = {
                "vertex_count": triangle_count * 3,
                "face_count": triangle_count,
                "edge_count": triangle_count * 3,  # Approximation
                "component_count": 1,  # Assume single component for now
                "degeneracy_count": 0,  # Would need full parse to determine
                "manifold": True,  # Assume manifold for STL files
                "format": format_type.value,
            }

            return stats

        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            STLFormatError,
        ) as e:
            raise STLGeometryError(f"Failed to get geometry stats: {str(e)}") from e
