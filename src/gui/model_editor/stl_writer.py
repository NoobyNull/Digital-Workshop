"""
STL File Writer - Save edited models to STL format.

Supports:
- Binary STL format
- ASCII STL format
- Preserves model integrity
"""

import struct
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from src.parsers.stl_parser import STLModel


logger = get_logger(__name__)


class STLWriter:
    """Writes STL models to file in binary or ASCII format."""

    @staticmethod
    def write_binary(model: STLModel, output_path: str) -> bool:
        """
        Write model to binary STL file.

        Args:
            model: STLModel to write
            output_path: Path to output file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                # Write header (80 bytes)
                header = model.header.encode('utf-8')[:80]
                header = header.ljust(80, b'\x00')
                f.write(header)

                # Write triangle count
                triangle_count = len(model.triangles)
                f.write(struct.pack('<I', triangle_count))

                # Write triangles
                for triangle in model.triangles:
                    # Normal vector (3 floats)
                    f.write(struct.pack('<fff', triangle.normal.x, triangle.normal.y, triangle.normal.z))

                    # Vertices (3 vertices × 3 floats each)
                    f.write(struct.pack('<fff', triangle.v1.x, triangle.v1.y, triangle.v1.z))
                    f.write(struct.pack('<fff', triangle.v2.x, triangle.v2.y, triangle.v2.z))
                    f.write(struct.pack('<fff', triangle.v3.x, triangle.v3.y, triangle.v3.z))

                    # Attribute byte count (2 bytes)
                    f.write(struct.pack('<H', triangle.attribute_byte_count))

            logger.info(f"Wrote binary STL with {triangle_count} triangles to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write binary STL: {e}")
            return False

    @staticmethod
    def write_ascii(model: STLModel, output_path: str) -> bool:
        """
        Write model to ASCII STL file.

        Args:
            model: STLModel to write
            output_path: Path to output file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                # Write header
                f.write(f"solid {model.header}\n")

                # Write triangles
                for triangle in model.triangles:
                    f.write(f"  facet normal {triangle.normal.x:.6e} {triangle.normal.y:.6e} {triangle.normal.z:.6e}\n")
                    f.write("    outer loop\n")
                    f.write(f"      vertex {triangle.v1.x:.6e} {triangle.v1.y:.6e} {triangle.v1.z:.6e}\n")
                    f.write(f"      vertex {triangle.v2.x:.6e} {triangle.v2.y:.6e} {triangle.v2.z:.6e}\n")
                    f.write(f"      vertex {triangle.v3.x:.6e} {triangle.v3.y:.6e} {triangle.v3.z:.6e}\n")
                    f.write("    endloop\n")
                    f.write("  endfacet\n")

                f.write(f"endsolid {model.header}\n")

            logger.info(f"Wrote ASCII STL with {len(model.triangles)} triangles to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write ASCII STL: {e}")
            return False

    @staticmethod
    def write(model: STLModel, output_path: str, binary: bool = True) -> bool:
        """
        Write model to STL file.

        Args:
            model: STLModel to write
            output_path: Path to output file
            binary: If True, write binary format; if False, write ASCII

        Returns:
            True if successful, False otherwise
        """
        if binary:
            return STLWriter.write_binary(model, output_path)
        else:
            return STLWriter.write_ascii(model, output_path)

