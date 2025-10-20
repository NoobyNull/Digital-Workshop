"""
Model rendering for 3D viewer.

Handles model geometry creation, rendering modes, and actor management.
"""

from enum import Enum
from typing import Optional

import vtk
from vtk.util import numpy_support as vtk_np

from src.core.logging_config import get_logger, log_function_call
from src.core.data_structures import Model
from src.parsers.stl_parser import STLModel


logger = get_logger(__name__)


class RenderMode(Enum):
    """Rendering modes for the 3D viewer."""
    SOLID = "solid"
    WIREFRAME = "wireframe"
    POINTS = "points"


class ModelRenderer:
    """Handles model rendering and geometry creation."""

    def __init__(self, renderer):
        """
        Initialize model renderer.

        Args:
            renderer: VTK renderer
        """
        self.renderer = renderer
        self.actor = None
        self.render_mode = RenderMode.SOLID

    @log_function_call(logger)
    def create_vtk_polydata(self, model: STLModel) -> vtk.vtkPolyData:
        """
        Create VTK polydata from STL model.

        Args:
            model: The STL model to convert

        Returns:
            vtk.vtkPolyData with the model geometry
        """
        logger.info(f"Creating VTK polydata for {len(model.triangles)} triangles")

        # Create points
        points = vtk.vtkPoints()

        # Create triangles
        triangles = vtk.vtkCellArray()

        # Create normals
        normals = vtk.vtkFloatArray()
        normals.SetNumberOfComponents(3)
        normals.SetName("Normals")

        # Process each triangle
        for triangle in model.triangles:
            # Add vertices
            point_id1 = points.InsertNextPoint(
                triangle.vertex1.x, triangle.vertex1.y, triangle.vertex1.z
            )
            point_id2 = points.InsertNextPoint(
                triangle.vertex2.x, triangle.vertex2.y, triangle.vertex2.z
            )
            point_id3 = points.InsertNextPoint(
                triangle.vertex3.x, triangle.vertex3.y, triangle.vertex3.z
            )

            # Add triangle
            triangle_cell = vtk.vtkTriangle()
            triangle_cell.GetPointIds().SetId(0, point_id1)
            triangle_cell.GetPointIds().SetId(1, point_id2)
            triangle_cell.GetPointIds().SetId(2, point_id3)
            triangles.InsertNextCell(triangle_cell)

            # Add normals
            normal = [triangle.normal.x, triangle.normal.y, triangle.normal.z]
            normals.InsertNextTuple(normal)
            normals.InsertNextTuple(normal)
            normals.InsertNextTuple(normal)

        # Create polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(triangles)
        polydata.GetPointData().SetNormals(normals)

        # Generate UV coordinates
        self._generate_uv_coordinates(polydata)

        return polydata

    @log_function_call(logger)
    def create_vtk_polydata_from_arrays(self, model: Model) -> vtk.vtkPolyData:
        """
        Create VTK polydata from NumPy arrays on the Model.

        Args:
            model: Model with vertex and normal arrays

        Returns:
            vtk.vtkPolyData with the model geometry
        """
        try:
            if not hasattr(model, "is_array_based") or not model.is_array_based():
                return self.create_vtk_polydata(model)  # type: ignore[arg-type]

            import numpy as _np

            vertex_array = model.vertex_array  # type: ignore[assignment]
            normal_array = model.normal_array  # type: ignore[assignment]

            if vertex_array is None or normal_array is None:
                return self.create_vtk_polydata(model)  # type: ignore[arg-type]

            total_vertices = int(vertex_array.shape[0])
            if total_vertices % 3 != 0:
                logger.warning("Vertex array length is not multiple of 3; falling back")
                return self.create_vtk_polydata(model)  # type: ignore[arg-type]

            # Create points from vertex array
            points = vtk.vtkPoints()
            points_vtk = vtk_np.numpy_to_vtk(vertex_array, deep=True)
            points.SetData(points_vtk)

            # Create triangles
            triangles = vtk.vtkCellArray()
            num_triangles = total_vertices // 3

            for i in range(num_triangles):
                triangle = vtk.vtkTriangle()
                triangle.GetPointIds().SetId(0, i * 3)
                triangle.GetPointIds().SetId(1, i * 3 + 1)
                triangle.GetPointIds().SetId(2, i * 3 + 2)
                triangles.InsertNextCell(triangle)

            # Create polydata
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(triangles)

            # Add normals
            normals_vtk = vtk_np.numpy_to_vtk(normal_array, deep=True)
            normals_vtk.SetNumberOfComponents(3)
            normals_vtk.SetName("Normals")
            polydata.GetPointData().SetNormals(normals_vtk)

            # Generate UV coordinates
            self._generate_uv_coordinates(polydata)

            return polydata

        except Exception as e:
            logger.error(f"Failed to create polydata from arrays: {e}", exc_info=True)
            raise

    def _generate_uv_coordinates(self, polydata: vtk.vtkPolyData) -> None:
        """
        Generate UV coordinates for polydata using planar projection.

        Args:
            polydata: The VTK polydata to add UV coordinates to
        """
        try:
            import numpy as np

            points = polydata.GetPoints()
            if not points:
                logger.warning("No points found for UV coordinate generation")
                return

            num_points = points.GetNumberOfPoints()
            logger.debug(f"Generating UV coordinates for {num_points} points")

            # Find bounds
            bounds = polydata.GetBounds()
            if not bounds or len(bounds) < 6:
                logger.warning("Invalid bounds for UV coordinate generation")
                return

            x_min, x_max, y_min, y_max, z_min, z_max = bounds
            x_range = max(x_max - x_min, 0.0001)
            y_range = max(y_max - y_min, 0.0001)

            # Extract points as NumPy array
            points_array = vtk_np.vtk_to_numpy(points.GetData())

            # Vectorized UV calculation
            u_coords = (points_array[:, 0] - x_min) / x_range
            v_coords = (points_array[:, 1] - y_min) / y_range

            # Stack coordinates
            uv_array = np.column_stack((u_coords, v_coords)).astype(np.float32)

            # Convert to VTK
            uv_vtk = vtk_np.numpy_to_vtk(uv_array, deep=True)
            uv_vtk.SetNumberOfComponents(2)
            uv_vtk.SetName("TCoords")

            # Add to polydata
            polydata.GetPointData().SetTCoords(uv_vtk)
            logger.debug(f"Generated {num_points} UV coordinates")

        except Exception as e:
            logger.error(f"Failed to generate UV coordinates: {e}", exc_info=True)

    def set_render_mode(self, mode: RenderMode) -> None:
        """
        Set the rendering mode.

        Args:
            mode: The render mode to apply
        """
        self.render_mode = mode
        self._apply_render_mode()

    def _apply_render_mode(self) -> None:
        """Apply the current render mode to the actor."""
        if not self.actor:
            return

        prop = self.actor.GetProperty()

        if self.render_mode == RenderMode.SOLID:
            prop.SetRepresentationToSurface()
        elif self.render_mode == RenderMode.WIREFRAME:
            prop.SetRepresentationToWireframe()
        elif self.render_mode == RenderMode.POINTS:
            prop.SetRepresentationToPoints()

        logger.debug(f"Render mode set to {self.render_mode.value}")

    def load_model(self, polydata: vtk.vtkPolyData) -> None:
        """
        Load a model into the renderer.

        Args:
            polydata: The VTK polydata to render
        """
        # Remove existing actor
        if self.actor and self.renderer:
            self.renderer.RemoveActor(self.actor)

        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        # Create actor
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)

        # Set material properties for proper lighting
        prop = self.actor.GetProperty()
        prop.SetColor(0.8, 0.8, 0.8)
        prop.SetAmbient(0.3)      # Ambient lighting
        prop.SetDiffuse(0.7)      # Diffuse lighting
        prop.SetSpecular(0.4)     # Specular highlights
        prop.SetSpecularPower(20) # Shininess
        prop.LightingOn()         # Enable lighting calculations

        # Apply render mode
        self._apply_render_mode()

        # Add to renderer
        self.renderer.AddActor(self.actor)

        logger.info("Model loaded into renderer")

    def remove_model(self) -> None:
        """Remove the current model from the renderer."""
        if self.actor and self.renderer:
            self.renderer.RemoveActor(self.actor)
            self.actor = None
            logger.info("Model removed from renderer")

    def get_actor(self) -> Optional[vtk.vtkActor]:
        """Get the current actor."""
        return self.actor

