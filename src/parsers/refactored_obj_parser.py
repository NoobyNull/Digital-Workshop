"""
Refactored OBJ Parser for Candy-Cadence

This module provides a refactored OBJ parser implementation that follows the IParser interface
with enhanced performance, streaming support, and consistent error handling.

Key Features:
- Implements IParser interface for consistency
- Supports OBJ format with MTL material files
- Streaming support for large files
- Progressive loading capabilities
- Memory-efficient processing
- Comprehensive error handling and logging
"""

import time
import gc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from src.parsers.refactored_base_parser import (
    RefactoredBaseParser,
    StreamingProgressCallback,
)
from src.core.interfaces.parser_interfaces import (
    ModelFormat,
    ParseError,
)
from src.core.logging_config import get_logger


class OBJParseError(ParseError):
    """Custom exception for OBJ parsing errors."""


@dataclass
class OBJMaterial:
    """Material definition from MTL file."""

    name: str
    ambient: Tuple[float, float, float] = (0.2, 0.2, 0.2)
    diffuse: Tuple[float, float, float] = (0.8, 0.8, 0.8)
    specular: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    specular_exponent: float = 0.0
    optical_density: float = 1.0
    dissolve: float = 1.0
    illumination_model: int = 2
    ambient_map: str = ""
    diffuse_map: str = ""
    specular_map: str = ""
    exponent_map: str = ""
    dissolve_map: str = ""
    bump_map: str = ""
    displacement_map: str = ""
    decal_map: str = ""
    anti_aliasing: str = ""


@dataclass
class OBJFace:
    """Face definition with vertex, texture, and normal indices."""

    vertex_indices: List[int]
    texture_indices: List[int]
    normal_indices: List[int]
    material_name: str = ""


@dataclass
class OBJVertex:
    """Vertex definition with position, normal, and texture coordinates."""

    position: Tuple[float, float, float]
    normal: Optional[Tuple[float, float, float]] = None
    texture: Optional[Tuple[float, float]] = None


class RefactoredOBJParser(RefactoredBaseParser):
    """
    Refactored OBJ parser implementing IParser interface with enhanced features.

    Features:
    - Supports OBJ format with MTL material files
    - Streaming support for large files
    - Progressive loading capabilities
    - Memory-efficient processing
    - Comprehensive error handling and logging
    """

    def __init__(self) -> None:
        """Initialize the refactored OBJ parser."""
        super().__init__(parser_name="OBJ", supported_formats=[ModelFormat.OBJ])
        self.logger = get_logger(self.__class__.__name__)
        self.materials: Dict[str, OBJMaterial] = {}

    def _parse_file_internal(
        self,
        file_path: Path,
        progress_callback: Optional[StreamingProgressCallback] = None,
    ) -> Dict[str, Any]:
        """
        Internal method to parse an OBJ file.

        Args:
            file_path: Path to the OBJ file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data

        Raises:
            OBJParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        self.logger.info("Starting OBJ parsing: %s", file_path)

        try:
            # Parse OBJ file
            vertices, normals, texture_coords, faces, materials = self._parse_obj_file(
                file_path, progress_callback
            )

            # Convert faces to triangles
            triangles = self._convert_faces_to_triangles(
                vertices, normals, texture_coords, faces
            )

            # Create result dictionary
            parsing_time = time.time()
            file_size = file_path.stat().st_size

            result = {
                "header": f"OBJ model with {len(faces)} faces",
                "triangles": triangles,
                "format": ModelFormat.OBJ,
                "materials": materials,
                "stats": {
                    "vertex_count": len(vertices),
                    "triangle_count": len(triangles),
                    "face_count": len(faces),
                    "material_count": len(materials),
                    "file_size_bytes": file_size,
                    "parsing_time_seconds": parsing_time,
                },
            }

            self._update_progress(100.0, "OBJ parsing completed", progress_callback)

            self.logger.info(
                f"Successfully parsed OBJ: {len(triangles)} triangles, "
                f"{len(faces)} faces, {len(vertices)} vertices, "
                f"{len(materials)} materials, time: {parsing_time:.2f}s"
            )

            return result

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to parse OBJ file %s: {str(e)}", file_path)
            raise

    def _parse_obj_file(
        self,
        file_path: Path,
        progress_callback: Optional[StreamingProgressCallback] = None,
    ) -> Tuple[
        List[OBJVertex],
        List[Tuple[float, float, float]],
        List[Tuple[float, float]],
        List[OBJFace],
        Dict[str, OBJMaterial],
    ]:
        """
        Parse OBJ file content with streaming support.

        Args:
            file_path: Path to the OBJ file
            progress_callback: Optional progress callback

        Returns:
            Tuple of (vertices, normals, texture_coords, faces, materials)
        """
        vertices = []
        normals = []
        texture_coords = []
        faces = []

        current_material = ""

        try:
            file_size = file_path.stat().st_size
            self._update_progress(5.0, "Reading OBJ file...", progress_callback)

            # Decide parsing strategy based on file size
            if file_size > 50 * 1024 * 1024:  # 50MB threshold
                return self._parse_obj_file_streaming(file_path, progress_callback)
            else:
                return self._parse_obj_file_standard(file_path, progress_callback)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error parsing OBJ file: %s", str(e))
            raise OBJParseError(f"Failed to parse OBJ file: {str(e)}")

    def _parse_obj_file_standard(
        self,
        file_path: Path,
        progress_callback: Optional[StreamingProgressCallback] = None,
    ) -> Tuple[
        List[OBJVertex],
        List[Tuple[float, float, float]],
        List[Tuple[float, float]],
        List[OBJFace],
        Dict[str, OBJMaterial],
    ]:
        """Standard parsing for smaller OBJ files."""
        vertices = []
        normals = []
        texture_coords = []
        faces = []

        current_material = ""

        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()

            if progress_callback:
                progress_callback.report(10.0, "Starting OBJ parsing")

            line_count = len(lines)

            for i, line in enumerate(lines):
                self._check_cancellation()

                # Report progress
                if progress_callback and i % 1000 == 0:
                    progress = 10.0 + (i / line_count) * 80.0
                    self._update_progress(
                        progress, f"Parsed {i}/{line_count} lines", progress_callback
                    )

                # Strip comments and whitespace
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Split line into parts
                parts = line.split()
                if not parts:
                    continue

                command = parts[0].lower()

                try:
                    if command == "v":
                        # Vertex: v x y z [w]
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            vertices.append(OBJVertex(position=(x, y, z)))

                    elif command == "vn":
                        # Vertex normal: vn x y z
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            normals.append((x, y, z))

                    elif command == "vt":
                        # Texture coordinate: vt u [v] [w]
                        if len(parts) >= 2:
                            u = float(parts[1])
                            v = float(parts[2]) if len(parts) > 2 else 0.0
                            texture_coords.append((u, v))

                    elif command == "f":
                        # Face: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3 ...
                        face = self._parse_face(parts[1:], current_material)
                        faces.append(face)

                    elif command == "usemtl":
                        # Use material: usemtl material_name
                        if len(parts) >= 2:
                            current_material = parts[1]

                    elif command == "mtllib":
                        # Material library: mtllib filename.mtl
                        if len(parts) >= 2:
                            mtl_file = parts[1]
                            self._load_mtl_file(file_path.parent / mtl_file)

                except (ValueError, IndexError) as e:
                    self.logger.warning("Invalid line %s: {line} - {str(e)}", i + 1)
                    continue

                # Periodic garbage collection
                if i % 10000 == 0 and i > 0:
                    gc.collect()

            if progress_callback:
                self._update_progress(95.0, "Finalizing OBJ parsing", progress_callback)

            return vertices, normals, texture_coords, faces, self.materials

    def _parse_obj_file_streaming(
        self,
        file_path: Path,
        progress_callback: Optional[StreamingProgressCallback] = None,
    ) -> Tuple[
        List[OBJVertex],
        List[Tuple[float, float, float]],
        List[Tuple[float, float]],
        List[OBJFace],
        Dict[str, OBJMaterial],
    ]:
        """Streaming parsing for large OBJ files."""
        vertices = []
        normals = []
        texture_coords = []
        faces = []

        current_material = ""

        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            line_count = 0
            processed_lines = 0

            # First pass: count lines for progress reporting
            for _ in file:
                line_count += 1

            file.seek(0)  # Reset to beginning

            self._update_progress(
                10.0, f"Streaming parse of {line_count} lines", progress_callback
            )

            for line in file:
                self._check_cancellation()

                processed_lines += 1

                # Report progress
                if processed_lines % 5000 == 0:
                    progress = 10.0 + (processed_lines / line_count) * 80.0
                    self._update_progress(
                        progress,
                        f"Processed {processed_lines}/{line_count} lines",
                        progress_callback,
                    )

                # Strip comments and whitespace
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Split line into parts
                parts = line.split()
                if not parts:
                    continue

                command = parts[0].lower()

                try:
                    if command == "v":
                        # Vertex: v x y z [w]
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            vertices.append(OBJVertex(position=(x, y, z)))

                    elif command == "vn":
                        # Vertex normal: vn x y z
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            normals.append((x, y, z))

                    elif command == "vt":
                        # Texture coordinate: vt u [v] [w]
                        if len(parts) >= 2:
                            u = float(parts[1])
                            v = float(parts[2]) if len(parts) > 2 else 0.0
                            texture_coords.append((u, v))

                    elif command == "f":
                        # Face: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3 ...
                        face = self._parse_face(parts[1:], current_material)
                        faces.append(face)

                    elif command == "usemtl":
                        # Use material: usemtl material_name
                        if len(parts) >= 2:
                            current_material = parts[1]

                    elif command == "mtllib":
                        # Material library: mtllib filename.mtl
                        if len(parts) >= 2:
                            mtl_file = parts[1]
                            self._load_mtl_file(file_path.parent / mtl_file)

                except (ValueError, IndexError) as e:
                    self.logger.warning(
                        "Invalid line %s: {line} - {str(e)}", processed_lines
                    )
                    continue

                # Periodic garbage collection for large files
                if processed_lines % 20000 == 0:
                    gc.collect()

            self._update_progress(
                95.0, "Finalizing streaming OBJ parse", progress_callback
            )

            return vertices, normals, texture_coords, faces, self.materials

    def _parse_face(self, face_parts: List[str], material_name: str) -> OBJFace:
        """
        Parse face definition.

        Args:
            face_parts: Face definition parts
            material_name: Current material name

        Returns:
            OBJFace object
        """
        vertex_indices = []
        texture_indices = []
        normal_indices = []

        for part in face_parts:
            # Parse vertex/texture/normal indices
            # Formats: v, v/vt, v//vn, v/vt/vn
            indices = part.split("/")

            # Vertex index (required)
            if indices[0]:
                vertex_indices.append(int(indices[0]))
            else:
                raise OBJParseError("Vertex index is required in face definition")

            # Texture index (optional)
            if len(indices) > 1 and indices[1]:
                texture_indices.append(int(indices[1]))
            else:
                texture_indices.append(0)  # 0 means no texture coordinate

            # Normal index (optional)
            if len(indices) > 2 and indices[2]:
                normal_indices.append(int(indices[2]))
            else:
                normal_indices.append(0)  # 0 means no normal

        return OBJFace(
            vertex_indices=vertex_indices,
            texture_indices=texture_indices,
            normal_indices=normal_indices,
            material_name=material_name,
        )

    def _convert_faces_to_triangles(
        self,
        vertices: List[OBJVertex],
        normals: List[Tuple[float, float, float]],
        texture_coords: List[Tuple[float, float]],
        faces: List[OBJFace],
    ) -> List[Dict[str, Any]]:
        """
        Convert faces to triangles.

        Args:
            vertices: List of vertices
            normals: List of normals
            texture_coords: List of texture coordinates
            faces: List of faces

        Returns:
            List of triangle dictionaries
        """
        triangles = []

        for face in faces:
            # Convert face to triangles (triangulation)
            if len(face.vertex_indices) < 3:
                continue  # Skip invalid faces

            # For faces with more than 3 vertices, create a triangle fan
            for i in range(1, len(face.vertex_indices) - 1):
                # Get vertices
                v1_idx = (
                    face.vertex_indices[0] - 1
                    if face.vertex_indices[0] > 0
                    else len(vertices) + face.vertex_indices[0]
                )
                v2_idx = (
                    face.vertex_indices[i] - 1
                    if face.vertex_indices[i] > 0
                    else len(vertices) + face.vertex_indices[i]
                )
                v3_idx = (
                    face.vertex_indices[i + 1] - 1
                    if face.vertex_indices[i + 1] > 0
                    else len(vertices) + face.vertex_indices[i + 1]
                )

                if (
                    0 <= v1_idx < len(vertices)
                    and 0 <= v2_idx < len(vertices)
                    and 0 <= v3_idx < len(vertices)
                ):
                    v1 = vertices[v1_idx]
                    v2 = vertices[v2_idx]
                    v3 = vertices[v3_idx]

                    # Calculate normal if not provided
                    normal = self._calculate_face_normal(
                        v1.position, v2.position, v3.position
                    )

                    # If face has normals, use the first one
                    if face.normal_indices and face.normal_indices[0] != 0:
                        n_idx = (
                            face.normal_indices[0] - 1
                            if face.normal_indices[0] > 0
                            else len(normals) + face.normal_indices[0]
                        )
                        if 0 <= n_idx < len(normals):
                            normal = normals[n_idx]

                    triangle = {
                        "normal": normal,
                        "vertices": [v1.position, v2.position, v3.position],
                        "material_name": face.material_name,
                    }
                    triangles.append(triangle)

        return triangles

    def _calculate_face_normal(
        self,
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
        v3: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """
        Calculate face normal from three vertices.

        Args:
            v1: First vertex position
            v2: Second vertex position
            v3: Third vertex position

        Returns:
            Normal vector tuple
        """
        # Calculate two edge vectors
        edge1 = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
        edge2 = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])

        # Calculate cross product
        normal_x = edge1[1] * edge2[2] - edge1[2] * edge2[1]
        normal_y = edge1[2] * edge2[0] - edge1[0] * edge2[2]
        normal_z = edge1[0] * edge2[1] - edge1[1] * edge2[0]

        # Normalize
        length = (normal_x**2 + normal_y**2 + normal_z**2) ** 0.5
        if length > 0:
            return (normal_x / length, normal_y / length, normal_z / length)

        return (0, 0, 1)  # Default normal

    def _load_mtl_file(self, mtl_path: Path) -> None:
        """
        Load MTL material file.

        Args:
            mtl_path: Path to the MTL file
        """
        if not mtl_path.exists():
            self.logger.warning("MTL file not found: %s", mtl_path)
            return

        try:
            with open(mtl_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()

                current_material = None

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    command = parts[0].lower()

                    if command == "newmtl":
                        # New material: newmtl material_name
                        if len(parts) >= 2:
                            material_name = parts[1]
                            current_material = OBJMaterial(name=material_name)
                            self.materials[material_name] = current_material

                    elif current_material is not None:
                        try:
                            if command == "ka":
                                # Ambient color: ka r g b
                                if len(parts) >= 4:
                                    current_material.ambient = (
                                        float(parts[1]),
                                        float(parts[2]),
                                        float(parts[3]),
                                    )

                            elif command == "kd":
                                # Diffuse color: kd r g b
                                if len(parts) >= 4:
                                    current_material.diffuse = (
                                        float(parts[1]),
                                        float(parts[2]),
                                        float(parts[3]),
                                    )

                            elif command == "ks":
                                # Specular color: ks r g b
                                if len(parts) >= 4:
                                    current_material.specular = (
                                        float(parts[1]),
                                        float(parts[2]),
                                        float(parts[3]),
                                    )

                            elif command == "ns":
                                # Specular exponent: ns value
                                if len(parts) >= 2:
                                    current_material.specular_exponent = float(parts[1])

                            elif command == "ni":
                                # Optical density: ni value
                                if len(parts) >= 2:
                                    current_material.optical_density = float(parts[1])

                            elif command == "d":
                                # Dissolve: d value
                                if len(parts) >= 2:
                                    current_material.dissolve = float(parts[1])

                            elif command == "tr":
                                # Transparency: tr value (inverse of dissolve)
                                if len(parts) >= 2:
                                    current_material.dissolve = 1.0 - float(parts[1])

                            elif command == "illum":
                                # Illumination model: illum value
                                if len(parts) >= 2:
                                    current_material.illumination_model = int(parts[1])

                            elif command == "map_ka":
                                # Ambient texture map: map_ka filename
                                if len(parts) >= 2:
                                    current_material.ambient_map = parts[1]

                            elif command == "map_kd":
                                # Diffuse texture map: map_kd filename
                                if len(parts) >= 2:
                                    current_material.diffuse_map = parts[1]

                            elif command == "map_ks":
                                # Specular texture map: map_ks filename
                                if len(parts) >= 2:
                                    current_material.specular_map = parts[1]

                            elif command == "map_ns":
                                # Specular exponent map: map_ns filename
                                if len(parts) >= 2:
                                    current_material.exponent_map = parts[1]

                            elif command == "map_d":
                                # Dissolve map: map_d filename
                                if len(parts) >= 2:
                                    current_material.dissolve_map = parts[1]

                            elif command == "map_bump" or command == "bump":
                                # Bump map: map_bump filename
                                if len(parts) >= 2:
                                    current_material.bump_map = parts[1]

                            elif command == "disp":
                                # Displacement map: disp filename
                                if len(parts) >= 2:
                                    current_material.displacement_map = parts[1]

                            elif command == "decal":
                                # Decal map: decal filename
                                if len(parts) >= 2:
                                    current_material.decal_map = parts[1]

                        except (ValueError, IndexError) as e:
                            self.logger.warning("Invalid MTL line: %s - {str(e)}", line)
                            continue

                self.logger.info(
                    "Loaded %s materials from {mtl_path}", len(self.materials)
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load MTL file %s: {str(e)}", mtl_path)

    def _validate_geometry_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry validation.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing validation results
        """
        try:
            # Basic validation first
            if not self._validate_file_internal(file_path):
                return {
                    "is_valid": False,
                    "issues": ["File format validation failed"],
                    "statistics": {},
                }

            issues = []
            stats = {}

            # Sample first few lines to check structure
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read(1000).lower()

                # Check for basic OBJ structure
                if "v " not in content:
                    issues.append("No vertex data found in OBJ file")

                if "f " not in content:
                    issues.append("No face data found in OBJ file")

                # Check for common issues
                if "mtllib" in content and not any(
                    line.strip().lower().startswith("mtllib")
                    for line in file.readlines()
                ):
                    issues.append("MTL library referenced but file may be missing")

            return {"is_valid": len(issues) == 0, "issues": issues, "statistics": stats}

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating OBJ geometry: %s", str(e))
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "statistics": {},
            }

    def _get_geometry_stats_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry statistics.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing geometric statistics
        """
        try:
            vertex_count = 0
            face_count = 0
            normal_count = 0
            texture_count = 0

            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    line = line.strip().lower()
                    if line.startswith("v "):
                        vertex_count += 1
                    elif line.startswith("f "):
                        face_count += 1
                    elif line.startswith("vn "):
                        normal_count += 1
                    elif line.startswith("vt "):
                        texture_count += 1

            # Basic statistics
            stats = {
                "vertex_count": vertex_count,
                "face_count": face_count,
                "edge_count": face_count * 3,  # Approximation
                "component_count": 1,  # Assume single component for now
                "degeneracy_count": 0,  # Would need full parse to determine
                "manifold": True,  # Assume manifold for OBJ files
                "normal_count": normal_count,
                "texture_count": texture_count,
            }

            return stats

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting OBJ geometry stats: %s", str(e))
            raise ParseError(f"Failed to get geometry stats: {str(e)}")

    def get_parser_info(self) -> Dict[str, str]:
        """
        Get information about the parser implementation.

        Returns:
            Dictionary containing parser information
        """
        return {
            "name": "Refactored OBJ Parser",
            "version": "2.0.0",
            "author": "Candy-Cadence Development Team",
            "description": "Enhanced OBJ parser with streaming support, MTL material support, and improved error handling",
        }

    def _get_model_info_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method to get model information.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing model information
        """
        try:
            vertex_count = 0
            face_count = 0
            material_count = 0

            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    line = line.strip().lower()
                    if line.startswith("v "):
                        vertex_count += 1
                    elif line.startswith("f "):
                        face_count += 1
                    elif line.startswith("usemtl"):
                        material_count += 1

            return {
                "vertex_count": vertex_count,
                "face_count": face_count,
                "material_count": material_count,
                "has_normals": False,  # Would need full parse to determine
                "has_textures": False,  # Would need full parse to determine
                "complexity": (
                    "high"
                    if face_count > 10000
                    else "medium" if face_count > 1000 else "low"
                ),
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting OBJ model info: %s", str(e))
            return {
                "vertex_count": 0,
                "face_count": 0,
                "material_count": 0,
                "has_normals": False,
                "has_textures": False,
                "complexity": "unknown",
            }

    def _validate_file_internal(self, file_path: Path) -> bool:
        """
        Internal method to validate file format.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                # Read first few lines to check structure
                content = file.read(500).lower()

                # Check for basic OBJ structure
                has_vertices = "v " in content
                has_faces = "f " in content

                if not has_vertices and not has_faces:
                    return False

                # Additional validation could be added here
                return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Error validating OBJ file %s: {str(e)}", file_path)
            return False

    def _parse_stream_internal(self, file_path: Path) -> Iterator[Any]:
        """
        Internal method for streaming parsing.

        Args:
            file_path: Path to the model file

        Returns:
            Iterator yielding parsed chunks
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                vertices = []
                faces = []

                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    command = parts[0].lower()

                    if command == "v":
                        # Yield vertex data
                        if len(parts) >= 4:
                            vertex_data = {
                                "type": "vertex",
                                "x": float(parts[1]),
                                "y": float(parts[2]),
                                "z": float(parts[3]),
                            }
                            vertices.append(vertex_data)
                            yield vertex_data

                    elif command == "f":
                        # Yield face data (simplified)
                        if len(parts) >= 4:
                            face_indices = []
                            for part in parts[1:]:
                                # Simple vertex index extraction
                                idx = part.split("/")[0]
                                if idx:
                                    face_indices.append(int(idx))

                            if len(face_indices) >= 3:
                                face_data = {
                                    "type": "face",
                                    "vertices": face_indices,
                                    "triangle_count": len(face_indices) - 2,
                                }
                                faces.append(face_data)
                                yield face_data

                    elif command == "usemtl":
                        # Yield material change
                        if len(parts) >= 2:
                            material_data = {"type": "material", "name": parts[1]}
                            yield material_data

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error in OBJ streaming parse: %s", str(e))
            raise ParseError(f"Streaming failed: {str(e)}")


# Alias for backward compatibility
OBJParser = RefactoredOBJParser
