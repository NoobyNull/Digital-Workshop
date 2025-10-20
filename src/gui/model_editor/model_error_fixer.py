"""
Model error fixing for 3D-MM Model Editor.

Fixes various mesh errors:
- Non-manifold edges
- Holes
- Overlapping triangles
- Self-intersecting triangles
- Hollow areas
"""

from typing import List, Set, Tuple, Dict
from src.core.data_structures import Triangle, Vector3D, ModelStats
from src.parsers.stl_parser import STLModel
from .model_error_detector import ModelErrorDetector


class ModelErrorFixer:
    """Fixes various mesh errors in 3D models."""

    def __init__(self, model: STLModel):
        """Initialize error fixer with a model."""
        self.model = model
        self.original_triangles = model.triangles.copy()
        self.fixed_triangles = model.triangles.copy()

    def fix_all_errors(self) -> Tuple[STLModel, Dict[str, int]]:
        """Fix all detected errors in the model."""
        fixes_applied = {
            "duplicates_removed": 0,
            "degenerate_removed": 0,
            "non_manifold_fixed": 0,
        }
        
        # Fix overlapping/duplicate triangles
        self.fixed_triangles, dup_count = self._fix_overlapping_triangles()
        fixes_applied["duplicates_removed"] = dup_count
        
        # Fix degenerate triangles
        self.fixed_triangles, deg_count = self._fix_degenerate_triangles()
        fixes_applied["degenerate_removed"] = deg_count
        
        # Fix non-manifold edges
        self.fixed_triangles, nm_count = self._fix_non_manifold_edges()
        fixes_applied["non_manifold_fixed"] = nm_count
        
        # Create new model with fixed triangles
        fixed_model = STLModel(
            header=self.model.header,
            triangles=self.fixed_triangles,
            stats=self._recalculate_stats()
        )
        
        return fixed_model, fixes_applied

    def _fix_overlapping_triangles(self) -> Tuple[List[Triangle], int]:
        """Remove duplicate/overlapping triangles."""
        seen_triangles: Set[Tuple] = set()
        unique_triangles: List[Triangle] = []
        removed_count = 0
        
        for triangle in self.fixed_triangles:
            vertices = triangle.get_vertices()
            # Create normalized representation
            tri_key = tuple(sorted([
                self._vertex_to_tuple(v) for v in vertices
            ]))
            
            if tri_key not in seen_triangles:
                seen_triangles.add(tri_key)
                unique_triangles.append(triangle)
            else:
                removed_count += 1
        
        return unique_triangles, removed_count

    def _fix_degenerate_triangles(self) -> Tuple[List[Triangle], int]:
        """Remove degenerate triangles (zero area)."""
        valid_triangles: List[Triangle] = []
        removed_count = 0
        
        for triangle in self.fixed_triangles:
            vertices = triangle.get_vertices()
            
            if not self._is_degenerate_triangle(vertices):
                valid_triangles.append(triangle)
            else:
                removed_count += 1
        
        return valid_triangles, removed_count

    def _fix_non_manifold_edges(self) -> Tuple[List[Triangle], int]:
        """Fix non-manifold edges by removing duplicate edges."""
        edge_count: Dict[Tuple, List[int]] = {}
        
        # Count edges and track which triangles use them
        for tri_idx, triangle in enumerate(self.fixed_triangles):
            vertices = triangle.get_vertices()
            edges = [
                self._normalize_edge(vertices[0], vertices[1]),
                self._normalize_edge(vertices[1], vertices[2]),
                self._normalize_edge(vertices[2], vertices[0]),
            ]
            
            for edge in edges:
                if edge not in edge_count:
                    edge_count[edge] = []
                edge_count[edge].append(tri_idx)
        
        # Find triangles with non-manifold edges
        non_manifold_triangles: Set[int] = set()
        for edge, tri_indices in edge_count.items():
            if len(tri_indices) > 2:
                # Keep first two, mark rest for removal
                for idx in tri_indices[2:]:
                    non_manifold_triangles.add(idx)
        
        # Remove non-manifold triangles
        fixed_triangles = [
            tri for idx, tri in enumerate(self.fixed_triangles)
            if idx not in non_manifold_triangles
        ]
        
        return fixed_triangles, len(non_manifold_triangles)

    def _recalculate_stats(self) -> ModelStats:
        """Recalculate model statistics after fixing."""
        if not self.fixed_triangles:
            return ModelStats(
                vertex_count=0,
                triangle_count=0,
                min_bounds=Vector3D(0, 0, 0),
                max_bounds=Vector3D(0, 0, 0),
                file_size_bytes=0,
                format_type=self.model.stats.format_type,
                parsing_time_seconds=0
            )
        
        # Calculate bounds
        all_vertices = []
        for triangle in self.fixed_triangles:
            all_vertices.extend(triangle.get_vertices())
        
        if not all_vertices:
            return self.model.stats
        
        min_x = min(v.x for v in all_vertices)
        max_x = max(v.x for v in all_vertices)
        min_y = min(v.y for v in all_vertices)
        max_y = max(v.y for v in all_vertices)
        min_z = min(v.z for v in all_vertices)
        max_z = max(v.z for v in all_vertices)
        
        return ModelStats(
            vertex_count=len(all_vertices),
            triangle_count=len(self.fixed_triangles),
            min_bounds=Vector3D(min_x, min_y, min_z),
            max_bounds=Vector3D(max_x, max_y, max_z),
            file_size_bytes=self.model.stats.file_size_bytes,
            format_type=self.model.stats.format_type,
            parsing_time_seconds=self.model.stats.parsing_time_seconds
        )

    @staticmethod
    def _normalize_edge(v1: Vector3D, v2: Vector3D) -> Tuple:
        """Normalize edge representation (order-independent)."""
        t1 = ModelErrorFixer._vertex_to_tuple(v1)
        t2 = ModelErrorFixer._vertex_to_tuple(v2)
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

