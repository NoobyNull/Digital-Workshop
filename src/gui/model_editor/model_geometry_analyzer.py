"""
Model Geometry Analyzer - Analyzes model structure and detects hollow sides.

Provides functionality for:
- Triangle, edge, and face parsing
- Hollow side detection
- Z-up orientation analysis
- Model integrity verification
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math

from src.core.logging_config import get_logger
from src.core.data_structures import Triangle, Vector3D
from src.parsers.stl_parser import STLModel


logger = get_logger(__name__)


@dataclass
class Face:
    """Represents a face of the model."""
    triangles: List[Triangle]
    normal: Vector3D
    center: Vector3D
    area: float
    is_hollow: bool = False


class ModelGeometryAnalyzer:
    """Analyzes model geometry to detect orientation and hollow sides."""

    def __init__(self, model: STLModel):
        """
        Initialize analyzer with a model.

        Args:
            model: STLModel to analyze
        """
        self.model = model
        self.logger = logger
        self.triangles = model.triangles
        self.faces: List[Face] = []
        self._analyze_model()

    def _analyze_model(self) -> None:
        """Analyze model structure."""
        try:
            self._group_triangles_into_faces()
            self._detect_hollow_faces()
            self.logger.info(f"Analyzed model: {len(self.faces)} faces, {len(self.triangles)} triangles")
        except Exception as e:
            self.logger.error(f"Failed to analyze model: {e}")

    def _group_triangles_into_faces(self) -> None:
        """Group triangles into faces based on normal direction."""
        if not self.triangles:
            return

        # Group triangles by similar normal direction (within 15 degrees)
        face_groups: Dict[int, List[Triangle]] = {}
        normal_threshold = 0.25  # cos(75 degrees)

        for triangle in self.triangles:
            normal = triangle.normal
            found_group = False

            for group_id, group_triangles in face_groups.items():
                if group_triangles:
                    ref_normal = group_triangles[0].normal
                    # Calculate dot product
                    dot = (normal.x * ref_normal.x + 
                           normal.y * ref_normal.y + 
                           normal.z * ref_normal.z)
                    
                    if dot > normal_threshold:
                        group_triangles.append(triangle)
                        found_group = True
                        break

            if not found_group:
                face_groups[len(face_groups)] = [triangle]

        # Convert groups to Face objects
        for triangles in face_groups.values():
            if triangles:
                face = self._create_face(triangles)
                self.faces.append(face)

    def _create_face(self, triangles: List[Triangle]) -> Face:
        """Create a Face object from triangles."""
        # Use first triangle's normal
        normal = triangles[0].normal
        
        # Calculate center
        all_vertices = []
        for tri in triangles:
            all_vertices.extend(tri.get_vertices())
        
        if all_vertices:
            center_x = sum(v.x for v in all_vertices) / len(all_vertices)
            center_y = sum(v.y for v in all_vertices) / len(all_vertices)
            center_z = sum(v.z for v in all_vertices) / len(all_vertices)
            center = Vector3D(center_x, center_y, center_z)
        else:
            center = Vector3D(0, 0, 0)

        # Calculate area
        area = sum(self._triangle_area(tri) for tri in triangles)

        return Face(triangles=triangles, normal=normal, center=center, area=area)

    def _triangle_area(self, triangle: Triangle) -> float:
        """Calculate triangle area using cross product."""
        v1 = triangle.v1
        v2 = triangle.v2
        v3 = triangle.v3

        # Vectors from v1 to v2 and v1 to v3
        a = Vector3D(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
        b = Vector3D(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

        # Cross product
        cross = Vector3D(
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x
        )

        # Magnitude
        magnitude = math.sqrt(cross.x**2 + cross.y**2 + cross.z**2)
        return magnitude / 2.0

    def _detect_hollow_faces(self) -> None:
        """Detect which faces are hollow (open)."""
        # A face is hollow if it has edges that are not shared with other triangles
        edge_count: Dict[Tuple, int] = {}

        for triangle in self.triangles:
            edges = [
                (triangle.v1, triangle.v2),
                (triangle.v2, triangle.v3),
                (triangle.v3, triangle.v1),
            ]

            for edge in edges:
                # Normalize edge (smaller vertex first)
                v1, v2 = edge
                key = tuple(sorted([
                    (v1.x, v1.y, v1.z),
                    (v2.x, v2.y, v2.z)
                ]))
                edge_count[key] = edge_count.get(key, 0) + 1

        # Mark faces with unshared edges as hollow
        for face in self.faces:
            unshared_edges = 0
            for triangle in face.triangles:
                edges = [
                    (triangle.v1, triangle.v2),
                    (triangle.v2, triangle.v3),
                    (triangle.v3, triangle.v1),
                ]
                for edge in edges:
                    v1, v2 = edge
                    key = tuple(sorted([
                        (v1.x, v1.y, v1.z),
                        (v2.x, v2.y, v2.z)
                    ]))
                    if edge_count.get(key, 0) == 1:
                        unshared_edges += 1

            face.is_hollow = unshared_edges > 0

    def get_hollow_faces(self) -> List[Face]:
        """Get all hollow faces."""
        return [f for f in self.faces if f.is_hollow]

    def get_most_descriptive_face(self) -> Optional[Face]:
        """Get the face with the largest area (most descriptive)."""
        if not self.faces:
            return None
        return max(self.faces, key=lambda f: f.area)

    def get_z_up_recommendation(self) -> Tuple[str, float]:
        """
        Get recommendation for Z-up orientation.

        Returns:
            Tuple of (axis, rotation_degrees) to achieve Z-up
        """
        # Find the most descriptive face
        descriptive_face = self.get_most_descriptive_face()
        if not descriptive_face:
            return ("Z", 0)

        normal = descriptive_face.normal
        
        # Calculate angle from Z-axis
        z_angle = math.acos(min(1.0, max(-1.0, normal.z)))
        
        # If already pointing up, no rotation needed
        if z_angle < math.radians(15):
            return ("Z", 0)

        # Recommend rotation to align with Z-axis
        # This is a simplified recommendation
        return ("Z", 90)

