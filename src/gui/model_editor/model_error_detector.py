"""
Model error detection for Digital Workshop Model Editor.

Detects various mesh errors:
- Non-manifold edges (edges shared by >2 triangles)
- Hollow areas (inconsistent normals)
- Holes (open edges)
- Overlapping triangles (duplicate vertices)
- Self-intersecting triangles
"""

from dataclasses import dataclass
from typing import List, Set, Tuple, Dict
from src.core.data_structures import Vector3D
from src.parsers.stl_parser import STLModel


@dataclass
class MeshError:
    """Represents a detected mesh error."""

    error_type: str  # "non_manifold", "hollow", "hole", "overlap", "self_intersect"
    count: int
    description: str
    severity: str  # "critical", "warning", "info"
    affected_triangles: List[int] = None  # Triangle indices


class ModelErrorDetector:
    """Detects various mesh errors in 3D models."""

    def __init__(self, model: STLModel) -> None:
        """Initialize error detector with a model."""
        self.model = model
        self.triangles = model.triangles
        self.errors: List[MeshError] = []

    def detect_all_errors(self) -> List[MeshError]:
        """Detect all types of errors in the model."""
        self.errors = []

        # Ensure triangles is a list (handle numpy arrays or other types)
        if self.triangles is None:
            return self.errors

        try:
            # Convert to list if needed
            if not isinstance(self.triangles, list):
                self.triangles = list(self.triangles)
        except (TypeError, ValueError):
            return self.errors

        if not self.triangles:
            return self.errors

        self._detect_non_manifold_edges()
        self._detect_holes()
        self._detect_overlapping_triangles()
        self._detect_self_intersecting()
        self._detect_hollow_areas()

        return self.errors

    def _detect_non_manifold_edges(self) -> None:
        """Detect edges shared by more than 2 triangles."""
        edge_triangles: Dict[Tuple, List[int]] = {}

        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()
            edges = [
                self._normalize_edge(vertices[0], vertices[1]),
                self._normalize_edge(vertices[1], vertices[2]),
                self._normalize_edge(vertices[2], vertices[0]),
            ]

            for edge in edges:
                if edge not in edge_triangles:
                    edge_triangles[edge] = []
                edge_triangles[edge].append(tri_idx)

        # Find edges shared by more than 2 triangles
        non_manifold_edges = []
        affected_triangles: Set[int] = set()

        for edge, tri_list in edge_triangles.items():
            if len(tri_list) > 2:
                non_manifold_edges.append(edge)
                affected_triangles.update(tri_list)

        if non_manifold_edges:
            self.errors.append(
                MeshError(
                    error_type="non_manifold",
                    count=len(non_manifold_edges),
                    description=f"Found {len(non_manifold_edges)} non-manifold edges (shared by >2 triangles)",
                    severity="critical",
                    affected_triangles=list(affected_triangles),
                )
            )

    def _detect_holes(self) -> None:
        """Detect holes (open edges shared by only 1 triangle)."""
        edge_count: Dict[Tuple, int] = {}

        for triangle in self.triangles:
            vertices = triangle.get_vertices()
            edges = [
                self._normalize_edge(vertices[0], vertices[1]),
                self._normalize_edge(vertices[1], vertices[2]),
                self._normalize_edge(vertices[2], vertices[0]),
            ]

            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1

        # Holes are edges shared by only 1 triangle (open edges)
        open_edges = [edge for edge, count in edge_count.items() if count == 1]

        if open_edges:
            self.errors.append(
                MeshError(
                    error_type="hole",
                    count=len(open_edges),
                    description=f"Found {len(open_edges)} open edges (holes in mesh)",
                    severity="critical",
                    affected_triangles=[],
                )
            )

    def _detect_overlapping_triangles(self) -> None:
        """Detect overlapping/duplicate triangles (exact same vertices)."""
        seen_triangles: Dict[Tuple, int] = {}
        duplicates = 0
        affected_triangles: Set[int] = set()

        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()
            # Create a normalized representation (sorted vertices)
            tri_key = tuple(sorted([self._vertex_to_tuple(v) for v in vertices]))

            if tri_key in seen_triangles:
                duplicates += 1
                affected_triangles.add(tri_idx)
                affected_triangles.add(seen_triangles[tri_key])
            else:
                seen_triangles[tri_key] = tri_idx

        if duplicates > 0:
            self.errors.append(
                MeshError(
                    error_type="overlap",
                    count=duplicates,
                    description=f"Found {duplicates} duplicate triangles with identical vertices",
                    severity="warning",
                    affected_triangles=list(affected_triangles),
                )
            )

    def _detect_self_intersecting(self) -> None:
        """Detect self-intersecting triangles (basic check)."""
        degenerate = 0
        affected_triangles: Set[int] = set()

        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()

            # Check if triangle is degenerate (area ~0)
            if self._is_degenerate_triangle(vertices):
                degenerate += 1
                affected_triangles.add(tri_idx)

        if degenerate > 0:
            self.errors.append(
                MeshError(
                    error_type="self_intersect",
                    count=degenerate,
                    description=f"Found {degenerate} degenerate/self-intersecting triangles",
                    severity="critical",
                    affected_triangles=list(affected_triangles),
                )
            )

    def _detect_hollow_areas(self) -> None:
        """Detect hollow areas (faces with inconsistent normals or inward-facing)."""
        # Calculate model center
        if not self.triangles:
            return

        all_vertices = []
        for triangle in self.triangles:
            all_vertices.extend(triangle.get_vertices())

        if not all_vertices:
            return

        center_x = sum(v.x for v in all_vertices) / len(all_vertices)
        center_y = sum(v.y for v in all_vertices) / len(all_vertices)
        center_z = sum(v.z for v in all_vertices) / len(all_vertices)
        center = Vector3D(center_x, center_y, center_z)

        # Check for inward-facing normals
        inward_facing = 0
        affected_triangles: Set[int] = set()

        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()
            # Calculate triangle center
            tri_center_x = sum(v.x for v in vertices) / 3
            tri_center_y = sum(v.y for v in vertices) / 3
            tri_center_z = sum(v.z for v in vertices) / 3

            # Vector from model center to triangle center
            to_tri = Vector3D(
                tri_center_x - center.x,
                tri_center_y - center.y,
                tri_center_z - center.z,
            )

            # Dot product with normal
            dot = (
                triangle.normal.x * to_tri.x
                + triangle.normal.y * to_tri.y
                + triangle.normal.z * to_tri.z
            )

            # If dot product is negative, normal points inward (hollow)
            if dot < 0:
                inward_facing += 1
                affected_triangles.add(tri_idx)

        if inward_facing > 0:
            self.errors.append(
                MeshError(
                    error_type="hollow",
                    count=inward_facing,
                    description=f"Found {inward_facing} inward-facing normals (hollow areas)",
                    severity="warning",
                    affected_triangles=list(affected_triangles),
                )
            )

    @staticmethod
    def _normalize_edge(v1: Vector3D, v2: Vector3D) -> Tuple:
        """Normalize edge representation (order-independent)."""
        t1 = ModelErrorDetector._vertex_to_tuple(v1)
        t2 = ModelErrorDetector._vertex_to_tuple(v2)
        return tuple(sorted([t1, t2]))

    @staticmethod
    def _vertex_to_tuple(v: Vector3D, precision: int = 6) -> Tuple:
        """Convert vertex to tuple with precision."""
        return (round(v.x, precision), round(v.y, precision), round(v.z, precision))

    @staticmethod
    def _is_degenerate_triangle(vertices: List[Vector3D]) -> bool:
        """Check if triangle is degenerate (area ~0)."""
        if len(vertices) != 3:
            return True

        v1, v2, v3 = vertices

        # Calculate cross product
        edge1 = Vector3D(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
        edge2 = Vector3D(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

        cross = Vector3D(
            edge1.y * edge2.z - edge1.z * edge2.y,
            edge1.z * edge2.x - edge1.x * edge2.z,
            edge1.x * edge2.y - edge1.y * edge2.x,
        )

        magnitude = (cross.x**2 + cross.y**2 + cross.z**2) ** 0.5
        return magnitude < 1e-6

    def get_error_summary(self) -> str:
        """Get a human-readable summary of all errors."""
        if not self.errors:
            return "No errors detected. Model is valid."

        summary = f"Found {len(self.errors)} error type(s):\n\n"
        for error in self.errors:
            summary += f"• {error.description}\n"

        return summary
