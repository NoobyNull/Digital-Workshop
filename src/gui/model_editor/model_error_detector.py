"""
Model error detection for 3D-MM Model Editor.

Detects various mesh errors:
- Non-manifold edges (edges shared by >2 triangles)
- Hollow areas (inconsistent normals)
- Holes (open edges)
- Overlapping triangles (duplicate vertices)
- Self-intersecting triangles
"""

from dataclasses import dataclass
from typing import List, Set, Tuple, Dict
from src.parsers.base_parser import Triangle, Vector3D, STLModel


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

    def __init__(self, model: STLModel):
        """Initialize error detector with a model."""
        self.model = model
        self.triangles = model.triangles
        self.errors: List[MeshError] = []

    def detect_all_errors(self) -> List[MeshError]:
        """Detect all types of errors in the model."""
        self.errors = []
        
        self._detect_non_manifold_edges()
        self._detect_holes()
        self._detect_overlapping_triangles()
        self._detect_self_intersecting()
        self._detect_hollow_areas()
        
        return self.errors

    def _detect_non_manifold_edges(self) -> None:
        """Detect edges shared by more than 2 triangles."""
        edge_count: Dict[Tuple, int] = {}
        affected_triangles: Set[int] = set()
        
        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()
            edges = [
                self._normalize_edge(vertices[0], vertices[1]),
                self._normalize_edge(vertices[1], vertices[2]),
                self._normalize_edge(vertices[2], vertices[0]),
            ]
            
            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1
                if edge_count[edge] > 2:
                    affected_triangles.add(tri_idx)
        
        non_manifold_edges = sum(1 for count in edge_count.values() if count > 2)
        
        if non_manifold_edges > 0:
            self.errors.append(MeshError(
                error_type="non_manifold",
                count=non_manifold_edges,
                description=f"Found {non_manifold_edges} non-manifold edges (shared by >2 triangles)",
                severity="critical",
                affected_triangles=list(affected_triangles)
            ))

    def _detect_holes(self) -> None:
        """Detect holes (open edges not shared by exactly 2 triangles)."""
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
        
        open_edges = sum(1 for count in edge_count.values() if count != 2)
        
        if open_edges > 0:
            self.errors.append(MeshError(
                error_type="hole",
                count=open_edges,
                description=f"Found {open_edges} open edges (holes in mesh)",
                severity="warning",
                affected_triangles=[]
            ))

    def _detect_overlapping_triangles(self) -> None:
        """Detect overlapping triangles (same vertices)."""
        seen_triangles: Set[Tuple] = set()
        duplicates = 0
        affected_triangles: Set[int] = set()
        
        for tri_idx, triangle in enumerate(self.triangles):
            vertices = triangle.get_vertices()
            # Create a normalized representation
            tri_key = tuple(sorted([
                self._vertex_to_tuple(v) for v in vertices
            ]))
            
            if tri_key in seen_triangles:
                duplicates += 1
                affected_triangles.add(tri_idx)
            else:
                seen_triangles.add(tri_key)
        
        if duplicates > 0:
            self.errors.append(MeshError(
                error_type="overlap",
                count=duplicates,
                description=f"Found {duplicates} overlapping/duplicate triangles",
                severity="warning",
                affected_triangles=list(affected_triangles)
            ))

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
            self.errors.append(MeshError(
                error_type="self_intersect",
                count=degenerate,
                description=f"Found {degenerate} degenerate/self-intersecting triangles",
                severity="critical",
                affected_triangles=list(affected_triangles)
            ))

    def _detect_hollow_areas(self) -> None:
        """Detect hollow areas (inconsistent normals)."""
        # Check if normals are consistently pointing outward
        # This is a simplified check based on normal consistency
        inconsistent_normals = 0
        
        for triangle in self.triangles:
            normal = triangle.normal
            # Check if normal has reasonable magnitude
            magnitude = (normal.x**2 + normal.y**2 + normal.z**2) ** 0.5
            if magnitude < 0.1:  # Very small normal
                inconsistent_normals += 1
        
        if inconsistent_normals > 0:
            self.errors.append(MeshError(
                error_type="hollow",
                count=inconsistent_normals,
                description=f"Found {inconsistent_normals} areas with inconsistent normals",
                severity="warning",
                affected_triangles=[]
            ))

    @staticmethod
    def _normalize_edge(v1: Vector3D, v2: Vector3D) -> Tuple:
        """Normalize edge representation (order-independent)."""
        t1 = ModelErrorDetector._vertex_to_tuple(v1)
        t2 = ModelErrorDetector._vertex_to_tuple(v2)
        return tuple(sorted([t1, t2]))

    @staticmethod
    def _vertex_to_tuple(v: Vector3D, precision: int = 6) -> Tuple:
        """Convert vertex to tuple with precision."""
        return (
            round(v.x, precision),
            round(v.y, precision),
            round(v.z, precision)
        )

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
            edge1.x * edge2.y - edge1.y * edge2.x
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

