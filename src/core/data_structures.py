"""
Shared data structures for 3D-MM application.

This module contains the core data structures that are shared across different
components of the application, including parsers, cache, and GUI components.
By centralizing these structures, we avoid circular import dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union


class ModelFormat(Enum):
    """3D model file format types."""
    STL = "stl"
    OBJ = "obj"
    THREE_MF = "3mf"
    STEP = "step"
    UNKNOWN = "unknown"


@dataclass
class Vector3D:
    """3D vector representation for vertices, normals, etc."""
    x: float
    y: float
    z: float
    
    def __iter__(self):
        """Allow unpacking as tuple."""
        return iter((self.x, self.y, self.z))
    
    def __getitem__(self, index):
        """Allow indexing like tuple."""
        return [self.x, self.y, self.z][index]


@dataclass
class Triangle:
    """Triangle representation with normal and three vertices."""
    normal: Vector3D
    vertex1: Vector3D
    vertex2: Vector3D
    vertex3: Vector3D
    attribute_byte_count: int = 0
    
    def get_vertices(self) -> List[Vector3D]:
        """Get all vertices as a list."""
        return [self.vertex1, self.vertex2, self.vertex3]


@dataclass
class ModelStats:
    """Statistical information about a 3D model."""
    vertex_count: int
    triangle_count: int
    min_bounds: Vector3D
    max_bounds: Vector3D
    file_size_bytes: int
    format_type: ModelFormat
    parsing_time_seconds: float
    
    def get_dimensions(self) -> Tuple[float, float, float]:
        """Get model dimensions (width, height, depth)."""
        return (
            self.max_bounds.x - self.min_bounds.x,
            self.max_bounds.y - self.min_bounds.y,
            self.max_bounds.z - self.min_bounds.z
        )


class LoadingState(Enum):
    """Loading states for progressive model loading."""
    METADATA_ONLY = "metadata_only"
    LOW_RES_GEOMETRY = "low_res_geometry"
    FULL_GEOMETRY = "full_geometry"


@dataclass
class Model:
    """Complete 3D model representation with geometry and statistics."""
    header: str
    triangles: List[Triangle]
    stats: ModelStats
    format_type: ModelFormat
    loading_state: LoadingState = LoadingState.FULL_GEOMETRY
    file_path: Optional[str] = None
    
    def get_vertices(self) -> List[Vector3D]:
        """Get all unique vertices from all triangles."""
        vertices = []
        for triangle in self.triangles:
            vertices.extend(triangle.get_vertices())
        return vertices
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        return (
            len(self.header.encode('utf-8')) +
            len(self.triangles) * (50 + 4 * 9) +  # Rough estimate
            100  # Stats and other data
        )
    
    def is_fully_loaded(self) -> bool:
        """Check if model is fully loaded."""
        return self.loading_state == LoadingState.FULL_GEOMETRY
    
    def needs_geometry_loading(self) -> bool:
        """Check if model geometry needs to be loaded."""
        return self.loading_state == LoadingState.METADATA_ONLY