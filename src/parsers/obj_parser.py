"""
OBJ file parser for Digital Workshop.

This module provides parsing functionality for Wavefront OBJ files with MTL material support.
It includes memory-efficient processing, progress reporting, and comprehensive error handling.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .base_parser import (
    BaseParser,
    Model,
    ModelFormat,
    Triangle,
    Vector3D,
    ParseError,
    ProgressCallback,
)


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


class OBJParser(BaseParser):
    """
    OBJ file parser supporting vertices, faces, normals, texture coordinates, and MTL materials.

    Features:
    - Memory-efficient parsing for large files
    - Progress reporting for long operations
    - Comprehensive error handling and validation
    - MTL material file support
    - Integration with JSON logging system
    - Performance optimization for different file sizes
    """

    def __init__(self) -> None:
        """Initialize the OBJ parser."""
        super().__init__()
        self.materials: Dict[str, OBJMaterial] = {}

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return [".obj"]

    def parse_file(
        self,
        file_path: Union[str, Path],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Model:
        """
        Parse an OBJ file.

        Args:
            file_path: Path to the OBJ file
            progress_callback: Optional progress callback

        Returns:
            Parsed OBJ model

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        # Check file exists and get Path object
        file_path = self._check_file_exists(file_path)

        self.logger.info("Starting OBJ parsing: %s ({file_path.stat().st_size} bytes)", file_path)

        start_time = time.time()

        try:
            # Parse OBJ file
            vertices, normals, texture_coords, faces, materials = self._parse_obj_file(
                file_path, progress_callback
            )

            # Convert faces to triangles
            triangles = self._convert_faces_to_triangles(vertices, normals, texture_coords, faces)

            # Create model statistics
            file_size = file_path.stat().st_size
            stats = self._create_model_stats(triangles, file_size, ModelFormat.OBJ, start_time)

            self.logger.info(
                f"Successfully parsed OBJ: {len(triangles)} triangles, "
                f"{stats.triangle_count} faces, {len(vertices)} vertices, "
                f"bounds: [{stats.min_bounds.x:.3f}, {stats.min_bounds.y:.3f}, {stats.min_bounds.z:.3f}] to "
                f"[{stats.max_bounds.x:.3f}, {stats.max_bounds.y:.3f}, {stats.max_bounds.z:.3f}], "
                f"time: {stats.parsing_time_seconds:.2f}s"
            )

            return Model(
                header=f"OBJ model with {len(faces)} faces",
                triangles=triangles,
                stats=stats,
                format_type=ModelFormat.OBJ,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to parse OBJ file %s: {str(e)}", file_path)
            raise ParseError(f"Failed to parse OBJ file: {str(e)}")

    def _parse_obj_file(
        self, file_path: Path, progress_callback: Optional[ProgressCallback] = None
    ) -> Tuple[
        List[Vector3D],
        List[Vector3D],
        List[Tuple[float, float]],
        List[OBJFace],
        Dict[str, OBJMaterial],
    ]:
        """
        Parse OBJ file content.

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
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()

                if progress_callback:
                    progress_callback.report(0.0, "Starting OBJ parsing")

                line_count = len(lines)

                for i, line in enumerate(lines):
                    if self._cancel_parsing:
                        raise ParseError("Parsing was cancelled")

                    # Report progress
                    if progress_callback and i % 1000 == 0:
                        progress = (i / line_count) * 100
                        progress_callback.report(progress, f"Parsed {i}/{line_count} lines")

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
                                x, y, z = (
                                    float(parts[1]),
                                    float(parts[2]),
                                    float(parts[3]),
                                )
                                vertices.append(Vector3D(x, y, z))

                        elif command == "vn":
                            # Vertex normal: vn x y z
                            if len(parts) >= 4:
                                x, y, z = (
                                    float(parts[1]),
                                    float(parts[2]),
                                    float(parts[3]),
                                )
                                normals.append(Vector3D(x, y, z))

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
                    self._periodic_gc(i)

                if progress_callback:
                    progress_callback.report(100.0, "OBJ parsing completed")

                return vertices, normals, texture_coords, faces, self.materials

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise ParseError(f"Failed to parse OBJ file: {str(e)}")

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
                raise ParseError("Vertex index is required in face definition")

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
        vertices: List[Vector3D],
        normals: List[Vector3D],
        texture_coords: List[Tuple[float, float]],
        faces: List[OBJFace],
    ) -> List[Triangle]:
        """
        Convert faces to triangles.

        Args:
            vertices: List of vertices
            normals: List of normals
            texture_coords: List of texture coordinates
            faces: List of faces

        Returns:
            List of triangles
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
                    normal = self._calculate_face_normal(v1, v2, v3)

                    # If face has normals, use the first one
                    if face.normal_indices and face.normal_indices[0] != 0:
                        n_idx = (
                            face.normal_indices[0] - 1
                            if face.normal_indices[0] > 0
                            else len(normals) + face.normal_indices[0]
                        )
                        if 0 <= n_idx < len(normals):
                            normal = normals[n_idx]

                    triangles.append(Triangle(normal, v1, v2, v3))

        return triangles

    def _calculate_face_normal(self, v1: Vector3D, v2: Vector3D, v3: Vector3D) -> Vector3D:
        """
        Calculate face normal from three vertices.

        Args:
            v1: First vertex
            v2: Second vertex
            v3: Third vertex

        Returns:
            Normal vector
        """
        # Calculate two edge vectors
        edge1 = Vector3D(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
        edge2 = Vector3D(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

        # Calculate cross product
        normal_x = edge1.y * edge2.z - edge1.z * edge2.y
        normal_y = edge1.z * edge2.x - edge1.x * edge2.z
        normal_z = edge1.x * edge2.y - edge1.y * edge2.x

        # Normalize
        length = (normal_x**2 + normal_y**2 + normal_z**2) ** 0.5
        if length > 0:
            return Vector3D(normal_x / length, normal_y / length, normal_z / length)

        return Vector3D(0, 0, 1)  # Default normal

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

                self.logger.info("Loaded %s materials from {mtl_path}", len(self.materials))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load MTL file %s: {str(e)}", mtl_path)

    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate an OBJ file without fully parsing it.

        Args:
            file_path: Path to the OBJ file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_path = Path(file_path)

            # Check file exists and is not empty
            if not file_path.exists():
                return False, "File does not exist"

            if file_path.stat().st_size == 0:
                return False, "File is empty"

            # Basic format validation
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                # Check for at least one vertex
                content = file.read(1000).lower()
                if "v " not in content:
                    return False, "No vertex data found in OBJ file"

                # Check for at least one face
                if "f " not in content:
                    return False, "No face data found in OBJ file"

            return True, ""

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Validation error: {str(e)}"
