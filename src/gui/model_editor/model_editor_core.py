"""
Model Editor Core - VTK-based model editing and transformation.

Provides functionality for:
- Model rotation (90-degree increments on X, Y, Z axes)
- Model transformation and manipulation
- Hollow model detection and solid plane generation
- Model verification and integrity checking
"""

from enum import Enum
from typing import Tuple
import math

import vtk

from src.core.logging_config import get_logger
from src.core.data_structures import Triangle, Vector3D
from src.parsers.stl_parser import STLModel
from .model_geometry_analyzer import ModelGeometryAnalyzer


logger = get_logger(__name__)


class RotationAxis(Enum):
    """Rotation axes for model transformation."""

    X = "X"
    Y = "Y"
    Z = "Z"


class ModelEditor:
    """VTK-based model editor for rotation and transformation."""

    def __init__(self, model: STLModel) -> None:
        """
        Initialize model editor.

        Args:
            model: STLModel to edit
        """
        self.original_model = model
        self.current_model = model
        self.analyzer = ModelGeometryAnalyzer(model)
        self.logger = logger
        self.rotation_history: list = []
        self.total_rotation = {"X": 0, "Y": 0, "Z": 0}

    def rotate_model(self, axis: RotationAxis, degrees: float) -> STLModel:
        """
        Rotate model by specified degrees around axis.

        Args:
            axis: Rotation axis (X, Y, or Z)
            degrees: Rotation angle in degrees (should be multiple of 90)

        Returns:
            Rotated STLModel
        """
        try:
            # Normalize to 90-degree increments
            normalized_degrees = round(degrees / 90) * 90

            # Create VTK transformation
            transform = vtk.vtkTransform()

            if axis == RotationAxis.X:
                transform.RotateX(normalized_degrees)
            elif axis == RotationAxis.Y:
                transform.RotateY(normalized_degrees)
            elif axis == RotationAxis.Z:
                transform.RotateZ(normalized_degrees)

            # Apply transformation to all triangles
            rotated_triangles = []
            for triangle in self.current_model.triangles:
                rotated_tri = self._transform_triangle(triangle, transform)
                rotated_triangles.append(rotated_tri)

            # Create new model with rotated triangles
            self.current_model = STLModel(
                header=self.current_model.header,
                triangles=rotated_triangles,
                stats=self.current_model.stats,
            )

            # Track rotation
            self.total_rotation[axis.value] += normalized_degrees
            self.rotation_history.append((axis.value, normalized_degrees))

            self.logger.info(
                "Rotated model %s° around {axis.value} axis", normalized_degrees
            )
            return self.current_model

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to rotate model: %s", e)
            return self.current_model

    def _transform_triangle(
        self, triangle: Triangle, transform: vtk.vtkTransform
    ) -> Triangle:
        """Transform a triangle using VTK transformation."""
        # Transform normal
        normal_point = [triangle.normal.x, triangle.normal.y, triangle.normal.z, 0]
        transformed_normal = transform.TransformVector(normal_point)
        new_normal = Vector3D(
            transformed_normal[0], transformed_normal[1], transformed_normal[2]
        )

        # Transform vertices
        v1_point = [triangle.v1.x, triangle.v1.y, triangle.v1.z, 1]
        v2_point = [triangle.v2.x, triangle.v2.y, triangle.v2.z, 1]
        v3_point = [triangle.v3.x, triangle.v3.y, triangle.v3.z, 1]

        transformed_v1 = transform.TransformPoint(v1_point)
        transformed_v2 = transform.TransformPoint(v2_point)
        transformed_v3 = transform.TransformPoint(v3_point)

        new_v1 = Vector3D(transformed_v1[0], transformed_v1[1], transformed_v1[2])
        new_v2 = Vector3D(transformed_v2[0], transformed_v2[1], transformed_v2[2])
        new_v3 = Vector3D(transformed_v3[0], transformed_v3[1], transformed_v3[2])

        return Triangle(
            new_normal, new_v1, new_v2, new_v3, triangle.attribute_byte_count
        )

    def add_solid_plane_at_z_zero(self) -> STLModel:
        """
        Add a solid plane at Z=0 to close hollow models.

        Returns:
            Modified STLModel with solid plane
        """
        try:
            # Find all triangles with Z < 0 (bottom side)
            bottom_triangles = [
                t
                for t in self.current_model.triangles
                if min(t.v1.z, t.v2.z, t.v3.z) < 0
            ]

            if not bottom_triangles:
                self.logger.warning("No triangles found below Z=0")
                return self.current_model

            # Find bounds
            all_x = []
            all_y = []
            for tri in bottom_triangles:
                all_x.extend([tri.v1.x, tri.v2.x, tri.v3.x])
                all_y.extend([tri.v1.y, tri.v2.y, tri.v3.y])

            if not all_x or not all_y:
                return self.current_model

            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

            # Create plane triangles at Z=0
            plane_triangles = self._create_plane_triangles(min_x, max_x, min_y, max_y)

            # Add plane triangles to model
            new_triangles = self.current_model.triangles + plane_triangles
            self.current_model = STLModel(
                header=self.current_model.header,
                triangles=new_triangles,
                stats=self.current_model.stats,
            )

            self.logger.info(
                "Added solid plane with %s triangles", len(plane_triangles)
            )
            return self.current_model

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add solid plane: %s", e)
            return self.current_model

    def _create_plane_triangles(
        self, min_x: float, max_x: float, min_y: float, max_y: float
    ) -> list:
        """Create triangles for a plane at Z=0."""
        # Create 4 corners
        v1 = Vector3D(min_x, min_y, 0)
        v2 = Vector3D(max_x, min_y, 0)
        v3 = Vector3D(max_x, max_y, 0)
        v4 = Vector3D(min_x, max_y, 0)

        # Normal pointing up (positive Z)
        normal = Vector3D(0, 0, 1)

        # Create two triangles to form a rectangle
        tri1 = Triangle(normal, v1, v2, v3, 0)
        tri2 = Triangle(normal, v1, v3, v4, 0)

        return [tri1, tri2]

    def reset_to_original(self) -> STLModel:
        """Reset model to original state."""
        self.current_model = self.original_model
        self.rotation_history.clear()
        self.total_rotation = {"X": 0, "Y": 0, "Z": 0}
        self.logger.info("Model reset to original state")
        return self.current_model

    def get_rotation_summary(self) -> str:
        """Get summary of applied rotations."""
        return f"X: {self.total_rotation['X']}°, Y: {self.total_rotation['Y']}°, Z: {self.total_rotation['Z']}°"

    def verify_model_integrity(self) -> Tuple[bool, str]:
        """
        Verify model integrity.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not self.current_model.triangles:
                return False, "Model has no triangles"

            # Check for degenerate triangles
            degenerate_count = 0
            for tri in self.current_model.triangles:
                if self._is_degenerate_triangle(tri):
                    degenerate_count += 1

            if degenerate_count > 0:
                return False, f"Model has {degenerate_count} degenerate triangles"

            return True, "Model integrity verified"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Verification failed: {e}"

    def _is_degenerate_triangle(self, triangle: Triangle) -> bool:
        """Check if triangle is degenerate (zero area)."""
        # Calculate area using cross product
        a = (
            triangle.v2.x - triangle.v1.x,
            triangle.v2.y - triangle.v1.y,
            triangle.v2.z - triangle.v1.z,
        )
        b = (
            triangle.v3.x - triangle.v1.x,
            triangle.v3.y - triangle.v1.y,
            triangle.v3.z - triangle.v1.z,
        )

        cross = (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

        magnitude = math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)
        return magnitude < 1e-6
