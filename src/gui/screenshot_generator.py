"""
Screenshot generator for 3D models with applied materials.

This module provides functionality to capture screenshots of 3D models
with materials applied, suitable for use as thumbnails in the model library.
"""

import tempfile
from pathlib import Path
from typing import Optional

import vtk
from vtk.util import numpy_support as vtk_np

from src.core.logging_config import get_logger
from src.core.vtk_rendering_engine import VTKRenderingEngine
from src.parsers.stl_parser import STLParser, STLModel


class ScreenshotGenerator:
    """Generate screenshots of 3D models with applied materials."""

    def __init__(
        """TODO: Add docstring."""
        self,
        width: int = 256,
        height: int = 256,
        background_image: Optional[str] = None,
        material_name: Optional[str] = None,
    ):
        """
        Initialize the screenshot generator.

        Args:
            width: Screenshot width in pixels
            height: Screenshot height in pixels
            background_image: Path to background image file
            material_name: Name of material to apply to all models
        """
        self.logger = get_logger(__name__)
        self.width = width
        self.height = height
        self.background_image = background_image
        self.default_material_name = material_name

    def capture_model_screenshot(
        """TODO: Add docstring."""
        self,
        model_path: str,
        output_path: Optional[str] = None,
        material_manager=None,
        material_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Capture a screenshot of a 3D model.

        Args:
            model_path: Path to the model file
            output_path: Path to save the screenshot (if None, uses temp file)
            material_manager: MaterialManager instance for applying materials
            material_name: Name of material to apply (optional)

        Returns:
            Path to the saved screenshot, or None if failed
        """
        engine = None
        try:
            self.logger.info("Starting screenshot generation for: %s", model_path)

            # Create rendering engine
            engine = VTKRenderingEngine(width=self.width, height=self.height)
            if not engine.setup_render_window():
                return None

            # Load model
            self.logger.info("Loading model...")
            model = self._load_model(model_path)
            if not model:
                self.logger.error("Failed to load model: %s", model_path)
                return None

            self.logger.info(
                f"Model loaded: {len(model.triangles)} triangles, stats: {model.stats}"
            )

            # Create actor
            self.logger.info("Creating actor from model...")
            actor = self._create_actor_from_model(model)
            if not actor:
                self.logger.error("Failed to create actor for model: %s", model_path)
                return None

            self.logger.info("Actor created successfully: %s", actor)
            engine.renderer.AddActor(actor)

            # Apply material if provided
            mat_to_apply = material_name or self.default_material_name
            if material_manager and mat_to_apply:
                try:
                    self.logger.info(f"Applying material '{mat_to_apply}' to actor...")
                    success = material_manager.apply_material_to_actor(actor, mat_to_apply)
                    if success:
                        self.logger.info(
                            f"Successfully applied material '{mat_to_apply}' to screenshot"
                        )

                        # Force mapper update to ensure texture is visible
                        mapper = actor.GetMapper()
                        if mapper:
                            self.logger.debug(
                                "Forcing mapper update to ensure UV coordinates are recognized"
                            )
                            input_data = mapper.GetInput()
                            if input_data:
                                mapper.SetInputData(input_data)
                                self.logger.debug("Mapper updated with latest data")
                    else:
                        self.logger.warning(f"Failed to apply material '{mat_to_apply}'")
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.warning("Failed to apply material: %s", e)

            # Setup lighting and camera
            engine.setup_lighting()
            bounds = engine.renderer.ComputeVisiblePropBounds()
            engine.setup_camera(bounds, zoom_factor=1.05)

            # Set background (image or color)
            if self.background_image and Path(self.background_image).exists():
                engine.set_background_image(self.background_image)
            else:
                engine.set_background_color((0.95, 0.95, 0.95))

            # Log camera position and bounds
            self.logger.debug("Camera position: %s", engine.camera.GetPosition())
            self.logger.debug("Camera focal point: %s", engine.camera.GetFocalPoint())
            self.logger.debug("Camera view up: %s", engine.camera.GetViewUp())
            self.logger.debug("Renderer visible bounds: %s", bounds)

            # Double render to ensure material/texture is fully applied
            self.logger.info("Performing initial render...")
            engine.render()
            self.logger.info("Initial render completed")

            # Additional render pass to ensure texture mapping is fully processed
            self.logger.info("Performing texture mapping render pass...")
            engine.render()
            self.logger.info("Texture mapping render completed")

            # Capture screenshot
            screenshot_path = output_path or self._get_temp_screenshot_path()
            success = engine.capture_screenshot(screenshot_path)

            if success:
                self.logger.info("Screenshot saved: %s", screenshot_path)
                return screenshot_path
            else:
                self.logger.error("Failed to save screenshot to %s", screenshot_path)
                return None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error capturing screenshot: %s", e, exc_info=True)
            return None
        finally:
            if engine:
                engine.cleanup()

    def _load_model(self, model_path: str) -> Optional[STLModel]:
        """Load a model from file."""
        try:
            parser = STLParser()
            # Force full geometry loading for screenshots (disable lazy loading)
            model = parser.parse_file(model_path, lazy_loading=False)
            return model
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load model %s: {e}", model_path)
            return None

    def _create_actor_from_model(self, model: STLModel) -> Optional[vtk.vtkActor]:
        """Create a VTK actor from a model."""
        try:
            self.logger.info("Creating actor from model with %s triangles", len(model.triangles))

            # Check if model is array-based (using the same logic as ModelRenderer)
            if hasattr(model, "is_array_based") and model.is_array_based():
                self.logger.info("Using array-based model creation")
                return self._create_actor_from_arrays(model)
            else:
                self.logger.info("Using triangle-based model creation")
                return self._create_actor_from_triangles(model)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to create actor: %s", e, exc_info=True)
            return None

    def _create_actor_from_triangles(self, model: STLModel) -> Optional[vtk.vtkActor]:
        """Create a VTK actor from triangle-based model."""
        try:
            self.logger.info("Creating actor from %s triangles", len(model.triangles))

            # Create polydata from model (following the working ModelRenderer pattern)
            points = vtk.vtkPoints()
            cells = vtk.vtkCellArray()

            # Create normals array (crucial for lighting)
            normals = vtk.vtkFloatArray()
            normals.SetNumberOfComponents(3)
            normals.SetName("Normals")

            self.logger.debug("Processing %s triangles...", len(model.triangles))
            for i, triangle in enumerate(model.triangles):
                if i % 1000 == 0:  # Log progress for large models
                    self.logger.debug("Processing triangle %s/{len(model.triangles)}", i)

                try:
                    # Add vertices using direct access (following working pattern)
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
                    cells.InsertNextCell(triangle_cell)

                    # Add normals (crucial for proper lighting)
                    normal = [triangle.normal.x, triangle.normal.y, triangle.normal.z]
                    normals.InsertNextTuple(normal)
                    normals.InsertNextTuple(normal)
                    normals.InsertNextTuple(normal)

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as tri_error:
                    self.logger.warning("Error processing triangle %s: {tri_error}", i)
                    continue

            point_count = points.GetNumberOfPoints()
            cell_count = cells.GetNumberOfCells()
            self.logger.info("Created polydata: %s points, {cell_count} cells", point_count)

            if point_count == 0 or cell_count == 0:
                self.logger.error("No points or cells created - model may be empty or invalid")
                return None

            # Create polydata with points, cells, and normals
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(cells)
            polydata.GetPointData().SetNormals(normals)

            # No need to call Update() on vtkPolyData - it's not an algorithm
            self.logger.debug("Polydata bounds: %s", polydata.GetBounds())

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # Set proper material properties (following working ModelRenderer pattern)
            prop = actor.GetProperty()
            prop.SetColor(0.8, 0.8, 0.8)  # Light gray
            prop.SetAmbient(0.3)  # Ambient lighting
            prop.SetDiffuse(0.7)  # Diffuse lighting
            prop.SetSpecular(0.4)  # Specular highlights
            prop.SetSpecularPower(20)  # Shininess
            prop.LightingOn()  # Enable lighting calculations

            self.logger.info("Actor created successfully with bounds: %s", actor.GetBounds())
            return actor
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to create actor from triangles: %s", e, exc_info=True)
            return None

    def _create_actor_from_arrays(self, model: STLModel) -> Optional[vtk.vtkActor]:
        """Create a VTK actor from array-based model (following ModelRenderer pattern)."""
        try:
            if not hasattr(model, "is_array_based") or not model.is_array_based():
                self.logger.warning("Model is not array-based, falling back to triangle creation")
                return self._create_actor_from_triangles(model)

            vertex_array = getattr(model, "vertex_array", None)
            normal_array = getattr(model, "normal_array", None)

            if vertex_array is None or normal_array is None:
                self.logger.warning(
                    "Missing vertex or normal arrays, falling back to triangle creation"
                )
                return self._create_actor_from_triangles(model)

            total_vertices = int(vertex_array.shape[0])
            if total_vertices % 3 != 0:
                self.logger.warning("Vertex array length is not multiple of 3; falling back")
                return self._create_actor_from_triangles(model)

            self.logger.info("Creating actor from arrays: %s vertices", total_vertices)

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

            self.logger.info(
                f"Created array-based polydata: {points.GetNumberOfPoints()} points, {triangles.GetNumberOfCells()} cells"
            )

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # Set proper material properties (following working ModelRenderer pattern)
            prop = actor.GetProperty()
            prop.SetColor(0.8, 0.8, 0.8)  # Light gray
            prop.SetAmbient(0.3)  # Ambient lighting
            prop.SetDiffuse(0.7)  # Diffuse lighting
            prop.SetSpecular(0.4)  # Specular highlights
            prop.SetSpecularPower(20)  # Shininess
            prop.LightingOn()  # Enable lighting calculations

            self.logger.info(
                f"Array-based actor created successfully with bounds: {actor.GetBounds()}"
            )
            return actor
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to create actor from arrays: %s", e, exc_info=True)
            return None

    def _get_temp_screenshot_path(self) -> str:
        """Get a temporary file path for screenshot."""
        temp_dir = Path(tempfile.gettempdir()) / "3dmm_screenshots"
        temp_dir.mkdir(exist_ok=True)
        return str(temp_dir / f"screenshot_{id(self)}.png")
