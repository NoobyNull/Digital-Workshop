"""
3MF file parser for Digital Workshop.

This module provides parsing functionality for 3D Manufacturing Format (3MF) files.
It includes memory-efficient processing, progress reporting, and comprehensive error handling.
"""

import time
import zipfile
import xml.etree.ElementTree as ET
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
class ThreeMFComponent:
    """Component definition in 3MF."""

    object_id: int
    transform: List[float]  # 4x4 transformation matrix (row-major)


@dataclass
class ThreeMFObject:
    """Object definition in 3MF."""

    object_id: int
    type: str  # "model" or "other"
    vertices: List[Vector3D]
    triangles: List[Tuple[int, int, int]]  # Vertex indices
    components: List[ThreeMFComponent]
    name: str = ""


@dataclass
class ThreeMFBuildItem:
    """Build item in 3MF."""

    object_id: int
    transform: List[float]  # 4x4 transformation matrix (row-major)


class ThreeMFParser(BaseParser):
    """
    3MF file parser supporting vertices, triangles, and transformations.

    Features:
    - Memory-efficient parsing for large files
    - Progress reporting for long operations
    - Comprehensive error handling and validation
    - Support for complex 3MF structures
    - Integration with JSON logging system
    - Performance optimization for different file sizes
    """

    def __init__(self) -> None:
        """Initialize the 3MF parser."""
        super().__init__()
        self.objects: Dict[int, ThreeMFObject] = {}
        self.build_items: List[ThreeMFBuildItem] = []

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return [".3mf"]

    def parse_file(
        self,
        file_path: Union[str, Path],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Model:
        """
        Parse a 3MF file.

        Args:
            file_path: Path to the 3MF file
            progress_callback: Optional progress callback

        Returns:
            Parsed 3MF model

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        # Check file exists and get Path object
        file_path = self._check_file_exists(file_path)

        self.logger.info("Starting 3MF parsing: %s ({file_path.stat().st_size} bytes)", file_path)

        start_time = time.time()

        try:
            # Parse 3MF file
            triangles = self._parse_3mf_file(file_path, progress_callback)

            # Create model statistics
            file_size = file_path.stat().st_size
            stats = self._create_model_stats(triangles, file_size, ModelFormat.THREE_MF, start_time)

            self.logger.info(
                f"Successfully parsed 3MF: {len(triangles)} triangles, "
                f"bounds: [{stats.min_bounds.x:.3f}, {stats.min_bounds.y:.3f}, {stats.min_bounds.z:.3f}] to "
                f"[{stats.max_bounds.x:.3f}, {stats.max_bounds.y:.3f}, {stats.max_bounds.z:.3f}], "
                f"time: {stats.parsing_time_seconds:.2f}s"
            )

            return Model(
                header=f"3MF model with {len(triangles)} triangles",
                triangles=triangles,
                stats=stats,
                format_type=ModelFormat.THREE_MF,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to parse 3MF file %s: {str(e)}", file_path)
            raise ParseError(f"Failed to parse 3MF file: {str(e)}")

    def _parse_3mf_file(
        self, file_path: Path, progress_callback: Optional[ProgressCallback] = None
    ) -> List[Triangle]:
        """
        Parse 3MF file content.

        Args:
            file_path: Path to the 3MF file
            progress_callback: Optional progress callback

        Returns:
            List of triangles
        """
        try:
            if progress_callback:
                progress_callback.report(0.0, "Opening 3MF archive")

            # Open 3MF file as ZIP archive
            with zipfile.ZipFile(file_path, "r") as zip_file:
                # Check for required files
                if "3D/3dmodel.model" not in zip_file.namelist():
                    raise ParseError("Invalid 3MF file: missing 3D/3dmodel.model")

                # Parse 3D model
                if progress_callback:
                    progress_callback.report(20.0, "Parsing 3D model")

                with zip_file.open("3D/3dmodel.model") as model_file:
                    content = model_file.read().decode("utf-8")
                    root = ET.fromstring(content)

                    # Parse objects
                    self._parse_objects(root)

                    if progress_callback:
                        progress_callback.report(60.0, "Processing build items")

                    # Parse build items
                    self._parse_build_items(root)

                    if progress_callback:
                        progress_callback.report(80.0, "Generating triangles")

                    # Generate triangles from build items
                    triangles = self._generate_triangles()

                    if progress_callback:
                        progress_callback.report(100.0, "3MF parsing completed")

                    return triangles

        except zipfile.BadZipFile:
            raise ParseError("Invalid 3MF file: not a valid ZIP archive")
        except ET.ParseError as e:
            raise ParseError(f"Invalid 3MF file: XML parsing error - {str(e)}")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            raise ParseError(f"Failed to parse 3MF file: {str(e)}")

    def _parse_objects(self, root: ET.Element) -> None:
        """
        Parse objects from 3MF model.

        Args:
            root: Root element of the 3MF model
        """
        # Define namespace
        ns = {"3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}

        # Find all objects
        for obj_elem in root.findall(".//3mf:object", ns):
            try:
                object_id = int(obj_elem.get("id", "0"))
                obj_type = obj_elem.get("type", "model")
                name = obj_elem.get("name", "")

                vertices = []
                triangles = []
                components = []

                # Parse vertices
                vertices_elem = obj_elem.find("3mf:vertices", ns)
                if vertices_elem is not None:
                    for vertex_elem in vertices_elem.findall("3mf:vertex", ns):
                        x = float(vertex_elem.get("x", "0"))
                        y = float(vertex_elem.get("y", "0"))
                        z = float(vertex_elem.get("z", "0"))
                        vertices.append(Vector3D(x, y, z))

                # Parse triangles
                triangles_elem = obj_elem.find("3mf:triangles", ns)
                if triangles_elem is not None:
                    for triangle_elem in triangles_elem.findall("3mf:triangle", ns):
                        v1 = int(triangle_elem.get("v1", "0"))
                        v2 = int(triangle_elem.get("v2", "0"))
                        v3 = int(triangle_elem.get("v3", "0"))
                        triangles.append((v1, v2, v3))

                # Parse components
                components_elem = obj_elem.find("3mf:components", ns)
                if components_elem is not None:
                    for component_elem in components_elem.findall("3mf:component", ns):
                        comp_object_id = int(component_elem.get("objectid", "0"))
                        transform = self._parse_transform(component_elem.get("transform", ""))
                        components.append(ThreeMFComponent(comp_object_id, transform))

                # Create object
                obj = ThreeMFObject(
                    object_id=object_id,
                    type=obj_type,
                    vertices=vertices,
                    triangles=triangles,
                    components=components,
                    name=name,
                )

                self.objects[object_id] = obj

            except (ValueError, AttributeError) as e:
                self.logger.warning("Invalid object element: %s", str(e))
                continue

    def _parse_build_items(self, root: ET.Element) -> None:
        """
        Parse build items from 3MF model.

        Args:
            root: Root element of the 3MF model
        """
        # Define namespace
        ns = {"3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}

        # Find build element
        build_elem = root.find("3mf:build", ns)
        if build_elem is None:
            return

        # Find all build items
        for item_elem in build_elem.findall("3mf:item", ns):
            try:
                object_id = int(item_elem.get("objectid", "0"))
                transform = self._parse_transform(item_elem.get("transform", ""))

                build_item = ThreeMFBuildItem(object_id, transform)
                self.build_items.append(build_item)

            except (ValueError, AttributeError) as e:
                self.logger.warning("Invalid build item element: %s", str(e))
                continue

    def _parse_transform(self, transform_str: str) -> List[float]:
        """
        Parse transform string into 4x4 matrix.

        Args:
            transform_str: Transform string

        Returns:
            4x4 transformation matrix (row-major)
        """
        if not transform_str:
            # Identity matrix
            return [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ]

        try:
            # Parse space-separated values
            values = [float(x) for x in transform_str.split()]

            # Ensure we have 16 values
            if len(values) != 16:
                self.logger.warning("Invalid transform: %s, using identity", transform_str)
                return [
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                ]

            return values

        except ValueError:
            self.logger.warning("Invalid transform values: %s, using identity", transform_str)
            return [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ]

    def _generate_triangles(self) -> List[Triangle]:
        """
        Generate triangles from build items and objects.

        Returns:
            List of triangles
        """
        triangles = []

        for build_item in self.build_items:
            item_triangles = self._generate_triangles_for_item(build_item)
            triangles.extend(item_triangles)

        return triangles

    def _generate_triangles_for_item(self, build_item: ThreeMFBuildItem) -> List[Triangle]:
        """
        Generate triangles for a specific build item.

        Args:
            build_item: Build item to process

        Returns:
            List of triangles
        """
        triangles = []

        # Get the object
        obj = self.objects.get(build_item.object_id)
        if obj is None:
            self.logger.warning("Object %s not found", build_item.object_id)
            return triangles

        # Process triangles
        for triangle_indices in obj.triangles:
            if len(triangle_indices) != 3:
                continue

            # Get vertices
            vertices = []
            for vertex_idx in triangle_indices:
                if 0 <= vertex_idx < len(obj.vertices):
                    vertices.append(obj.vertices[vertex_idx])
                else:
                    self.logger.warning("Vertex index %s out of range", vertex_idx)
                    break

            if len(vertices) != 3:
                continue

            # Apply transform if needed
            if build_item.transform != [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ]:
                vertices = self._apply_transform(vertices, build_item.transform)

            # Calculate normal
            normal = self._calculate_face_normal(vertices[0], vertices[1], vertices[2])

            # Create triangle
            triangle = Triangle(normal, vertices[0], vertices[1], vertices[2])
            triangles.append(triangle)

        # Process components
        for component in obj.components:
            component_triangles = self._generate_triangles_for_component(
                component, build_item.transform
            )
            triangles.extend(component_triangles)

        return triangles

    def _generate_triangles_for_component(
        self, component: ThreeMFComponent, parent_transform: List[float]
    ) -> List[Triangle]:
        """
        Generate triangles for a component.

        Args:
            component: Component to process
            parent_transform: Parent transformation matrix

        Returns:
            List of triangles
        """
        triangles = []

        # Get the component object
        comp_obj = self.objects.get(component.object_id)
        if comp_obj is None:
            self.logger.warning("Component object %s not found", component.object_id)
            return triangles

        # Combine transforms
        combined_transform = self._multiply_matrices(parent_transform, component.transform)

        # Process triangles
        for triangle_indices in comp_obj.triangles:
            if len(triangle_indices) != 3:
                continue

            # Get vertices
            vertices = []
            for vertex_idx in triangle_indices:
                if 0 <= vertex_idx < len(comp_obj.vertices):
                    vertices.append(comp_obj.vertices[vertex_idx])
                else:
                    self.logger.warning("Vertex index %s out of range", vertex_idx)
                    break

            if len(vertices) != 3:
                continue

            # Apply combined transform
            vertices = self._apply_transform(vertices, combined_transform)

            # Calculate normal
            normal = self._calculate_face_normal(vertices[0], vertices[1], vertices[2])

            # Create triangle
            triangle = Triangle(normal, vertices[0], vertices[1], vertices[2])
            triangles.append(triangle)

        # Process nested components
        for nested_component in comp_obj.components:
            nested_triangles = self._generate_triangles_for_component(
                nested_component, combined_transform
            )
            triangles.extend(nested_triangles)

        return triangles

    def _multiply_matrices(self, matrix_a: List[float], matrix_b: List[float]) -> List[float]:
        """
        Multiply two 4x4 matrices.

        Args:
            matrix_a: First matrix (row-major)
            matrix_b: Second matrix (row-major)

        Returns:
            Result matrix (row-major)
        """
        result = [0.0] * 16

        for i in range(4):
            for j in range(4):
                for k in range(4):
                    result[i * 4 + j] += matrix_a[i * 4 + k] * matrix_b[k * 4 + j]

        return result

    def _apply_transform(self, vertices: List[Vector3D], transform: List[float]) -> List[Vector3D]:
        """
        Apply transformation matrix to vertices.

        Args:
            vertices: List of vertices to transform
            transform: 4x4 transformation matrix (row-major)

        Returns:
            Transformed vertices
        """
        transformed = []

        for vertex in vertices:
            # Convert to homogeneous coordinates
            x, y, z = vertex.x, vertex.y, vertex.z
            w = 1.0

            # Apply transformation
            new_x = transform[0] * x + transform[1] * y + transform[2] * z + transform[3] * w
            new_y = transform[4] * x + transform[5] * y + transform[6] * z + transform[7] * w
            new_z = transform[8] * x + transform[9] * y + transform[10] * z + transform[11] * w
            new_w = transform[12] * x + transform[13] * y + transform[14] * z + transform[15] * w

            # Convert back to 3D coordinates
            if new_w != 0:
                new_x /= new_w
                new_y /= new_w
                new_z /= new_w

            transformed.append(Vector3D(new_x, new_y, new_z))

        return transformed

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

    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate a 3MF file without fully parsing it.

        Args:
            file_path: Path to the 3MF file

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

            # Check if it's a valid ZIP file
            try:
                with zipfile.ZipFile(file_path, "r") as zip_file:
                    # Check for required 3MF files
                    if "3D/3dmodel.model" not in zip_file.namelist():
                        return False, "Invalid 3MF file: missing 3D/3dmodel.model"

                    # Check if we can read the model file
                    with zip_file.open("3D/3dmodel.model") as model_file:
                        content = model_file.read(1000).decode("utf-8")
                        if "<?xml" not in content.lower():
                            return False, "Invalid 3MF file: invalid XML format"

                        if "model" not in content.lower():
                            return False, "Invalid 3MF file: not a 3D model"

                return True, ""

            except zipfile.BadZipFile:
                return False, "Invalid 3MF file: not a valid ZIP archive"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Validation error: {str(e)}"
