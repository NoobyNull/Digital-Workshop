"""
Trimesh-based fast model loader with VTK fallback.

This module provides ultra-fast model loading using Trimesh library,
with automatic fallback to the existing VTK-based parsers if Trimesh
is not available or fails to load a model.

Trimesh is significantly faster than VTK for loading 3D models (up to 1000x),
while maintaining compatibility with all existing Digital Workshop features.
"""

import time
from pathlib import Path
from typing import Optional
import numpy as np

from src.core.logging_config import get_logger
from src.core.data_structures import Model, ModelStats, Vector3D, ModelFormat, LoadingState
from src.parsers.base_parser import ProgressCallback

logger = get_logger(__name__)


class TrimeshLoader:
    """
    Fast model loader using Trimesh with VTK fallback.

    This loader attempts to use Trimesh for fast loading, and falls back
    to the existing parser system if Trimesh is unavailable or fails.
    """

    def __init__(self):
        """Initialize the Trimesh loader."""
        self.logger = get_logger(__name__)
        self._trimesh_available = None
        self._trimesh = None
        self._check_trimesh_availability()

    def _check_trimesh_availability(self) -> bool:
        """
        Check if Trimesh is available and cache the result.

        Returns:
            True if Trimesh is available, False otherwise
        """
        if self._trimesh_available is not None:
            return self._trimesh_available

        try:
            import trimesh

            self._trimesh = trimesh
            self._trimesh_available = True
            self.logger.info("Trimesh library available - fast loading enabled")
            return True
        except ImportError:
            self._trimesh_available = False
            self.logger.info("Trimesh library not available - using fallback parsers")
            return False

    def is_trimesh_available(self) -> bool:
        """Check if Trimesh is available."""
        return self._trimesh_available or False

    def load_model(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> Optional[Model]:
        """
        Load a 3D model using Trimesh with fallback to existing parsers.

        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates

        Returns:
            Model object with geometry and statistics, or None on failure
        """
        path = Path(file_path)

        if not path.exists():
            self.logger.error("File not found: %s", file_path)
            return None

        # Report initial progress
        if progress_callback:
            progress_callback.report(0.0, "Initializing model loader...")

        # Try Trimesh first if available
        if self.is_trimesh_available():
            try:
                model = self._load_with_trimesh(file_path, progress_callback)
                if model is not None:
                    self.logger.info("Successfully loaded model with Trimesh: %s", path.name)
                    return model
                else:
                    self.logger.warning("Trimesh returned None, falling back to standard parser")
            except Exception as e:
                self.logger.warning(
                    "Trimesh loading failed (%s), falling back to standard parser: %s",
                    type(e).__name__,
                    str(e),
                )

        # Fallback: return None to let the calling code use the standard parser
        self.logger.info("Using standard parser for: %s", path.name)
        return None

    def _load_with_trimesh(
        self, file_path: str, progress_callback: Optional[ProgressCallback] = None
    ) -> Optional[Model]:
        """
        Load model using Trimesh library.

        Args:
            file_path: Path to the model file
            progress_callback: Optional callback for progress updates

        Returns:
            Model object or None on failure
        """
        if not self._trimesh:
            return None

        path = Path(file_path)
        start_time = time.time()

        try:
            if progress_callback:
                progress_callback.report(10.0, "Loading with Trimesh...")

            # Load mesh with Trimesh
            mesh = self._trimesh.load(str(path))

            if progress_callback:
                progress_callback.report(50.0, "Processing geometry...")

            # Handle scene vs single mesh
            if isinstance(mesh, self._trimesh.Scene):
                # Combine all geometries in the scene
                mesh = mesh.dump(concatenate=True)

            # Ensure we have a valid mesh
            if not hasattr(mesh, "vertices") or not hasattr(mesh, "faces"):
                self.logger.warning("Trimesh loaded object has no vertices or faces")
                return None

            # Get vertices and faces as numpy arrays
            vertices = np.array(mesh.vertices, dtype=np.float32)
            faces = np.array(mesh.faces, dtype=np.int32)

            if progress_callback:
                progress_callback.report(70.0, "Computing normals...")

            # Get or compute normals
            if hasattr(mesh, "vertex_normals") and mesh.vertex_normals is not None:
                vertex_normals = np.array(mesh.vertex_normals, dtype=np.float32)
            else:
                # Compute face normals and convert to vertex normals
                mesh.fix_normals()
                vertex_normals = np.array(mesh.vertex_normals, dtype=np.float32)

            if progress_callback:
                progress_callback.report(85.0, "Creating model structure...")

            # Convert to triangle-based format for compatibility
            # Create vertex array: (num_faces * 3, 3) - each triangle has 3 vertices
            num_faces = faces.shape[0]
            vertex_array = np.zeros((num_faces * 3, 3), dtype=np.float32)
            normal_array = np.zeros((num_faces * 3, 3), dtype=np.float32)

            for i, face in enumerate(faces):
                vertex_array[i * 3 : (i + 1) * 3] = vertices[face]
                normal_array[i * 3 : (i + 1) * 3] = vertex_normals[face]

            # Compute bounds
            min_bounds = Vector3D(
                x=float(vertices[:, 0].min()),
                y=float(vertices[:, 1].min()),
                z=float(vertices[:, 2].min()),
            )
            max_bounds = Vector3D(
                x=float(vertices[:, 0].max()),
                y=float(vertices[:, 1].max()),
                z=float(vertices[:, 2].max()),
            )

            # Get file size
            file_size = path.stat().st_size

            # Detect format
            suffix = path.suffix.lower()
            format_map = {
                ".stl": ModelFormat.STL,
                ".obj": ModelFormat.OBJ,
                ".3mf": ModelFormat.THREE_MF,
                # Note: PLY, OFF, GLB, GLTF not in ModelFormat enum yet
                # These will use ModelFormat.UNKNOWN
            }
            format_type = format_map.get(suffix, ModelFormat.UNKNOWN)

            # Calculate parsing time
            parsing_time = time.time() - start_time

            # Create statistics
            stats = ModelStats(
                vertex_count=len(vertices),
                triangle_count=num_faces,
                min_bounds=min_bounds,
                max_bounds=max_bounds,
                file_size_bytes=file_size,
                format_type=format_type,
                parsing_time_seconds=parsing_time,
            )

            if progress_callback:
                progress_callback.report(95.0, "Finalizing model...")

            # Create Model with array-based geometry
            model = Model(
                header=f"Trimesh: {path.name}",
                triangles=[],  # Empty - using array-based geometry
                stats=stats,
                format_type=format_type,
                loading_state=LoadingState.ARRAY_GEOMETRY,
                file_path=str(file_path),
                vertex_array=vertex_array,
                normal_array=normal_array,
            )

            if progress_callback:
                progress_callback.report(100.0, "Model loaded successfully")

            self.logger.info(
                "Trimesh loaded %s: %d triangles in %.3fs", path.name, num_faces, parsing_time
            )

            return model

        except Exception as e:
            self.logger.error("Trimesh loading failed: %s", str(e), exc_info=True)
            return None


# Singleton instance
_trimesh_loader_instance = None


def get_trimesh_loader() -> TrimeshLoader:
    """Get the singleton TrimeshLoader instance."""
    global _trimesh_loader_instance
    if _trimesh_loader_instance is None:
        _trimesh_loader_instance = TrimeshLoader()
    return _trimesh_loader_instance
