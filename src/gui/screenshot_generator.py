"""
Screenshot generator for 3D models with applied materials.

This module provides functionality to capture screenshots of 3D models
with materials applied, suitable for use as thumbnails in the model library.
"""

import tempfile
from pathlib import Path
from typing import Optional, Tuple

import vtk
from vtk.util import numpy_support as vtk_np
from PIL import Image
import numpy as np

from src.core.logging_config import get_logger
from src.parsers.stl_parser import STLParser, STLModel
from src.core.data_structures import ModelFormat


class ScreenshotGenerator:
    """Generate screenshots of 3D models with applied materials."""

    def __init__(
        self,
        width: int = 256,
        height: int = 256,
        background_image: Optional[str] = None,
        material_name: Optional[str] = None
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
        self,
        model_path: str,
        output_path: Optional[str] = None,
        material_manager=None,
        material_name: Optional[str] = None
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
        try:
            # Create off-screen render window
            render_window = vtk.vtkRenderWindow()
            render_window.SetSize(self.width, self.height)
            render_window.SetOffScreenRendering(True)

            # Create renderer
            renderer = vtk.vtkRenderer()
            render_window.AddRenderer(renderer)

            # Set background (image or color)
            self._set_background(renderer)

            # Load model
            model = self._load_model(model_path)
            if not model:
                self.logger.error(f"Failed to load model: {model_path}")
                return None

            # Create actor
            actor = self._create_actor_from_model(model)
            if not actor:
                self.logger.error(f"Failed to create actor for model: {model_path}")
                return None

            renderer.AddActor(actor)

            # Apply material if provided
            # Use default material from settings if not explicitly provided
            mat_to_apply = material_name or self.default_material_name
            if material_manager and mat_to_apply:
                try:
                    material_manager.apply_material_to_actor(actor, mat_to_apply)
                    self.logger.debug(f"Applied material '{mat_to_apply}' to screenshot")
                except Exception as e:
                    self.logger.warning(f"Failed to apply material: {e}")

            # Setup lighting
            self._setup_lighting(renderer)

            # Setup camera
            renderer.ResetCamera()
            renderer.ResetCameraClippingRange()

            # Render
            render_window.Render()

            # Capture screenshot
            screenshot_path = output_path or self._get_temp_screenshot_path()
            success = self._save_screenshot(render_window, screenshot_path)

            # Cleanup
            render_window.Finalize()

            if success:
                self.logger.info(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                self.logger.error(f"Failed to save screenshot to {screenshot_path}")
                return None

        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}", exc_info=True)
            return None

    def _load_model(self, model_path: str) -> Optional[STLModel]:
        """Load a model from file."""
        try:
            parser = STLParser()
            model = parser.parse(model_path)
            return model
        except Exception as e:
            self.logger.error(f"Failed to load model {model_path}: {e}")
            return None

    def _create_actor_from_model(self, model: STLModel) -> Optional[vtk.vtkActor]:
        """Create a VTK actor from a model."""
        try:
            # Create polydata from model
            points = vtk.vtkPoints()
            cells = vtk.vtkCellArray()

            for triangle in model.triangles:
                cell = vtk.vtkTriangle()
                for i, vertex_idx in enumerate(triangle.vertex_indices):
                    vertex = model.vertices[vertex_idx]
                    points.InsertNextPoint(vertex.x, vertex.y, vertex.z)
                    cell.GetPointIds().SetId(i, points.GetNumberOfPoints() - 1)
                cells.InsertNextCell(cell)

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(cells)

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.7, 0.7, 0.7)

            return actor
        except Exception as e:
            self.logger.error(f"Failed to create actor: {e}")
            return None

    def _setup_lighting(self, renderer: vtk.vtkRenderer) -> None:
        """Setup lighting for the scene."""
        try:
            # Main light
            light1 = vtk.vtkLight()
            light1.SetPosition(100, 100, 100)
            light1.SetIntensity(0.8)
            renderer.AddLight(light1)

            # Fill light
            light2 = vtk.vtkLight()
            light2.SetPosition(-100, -100, 100)
            light2.SetIntensity(0.5)
            renderer.AddLight(light2)
        except Exception as e:
            self.logger.warning(f"Failed to setup lighting: {e}")

    def _set_background(self, renderer: vtk.vtkRenderer) -> None:
        """Set background from image file or default color."""
        try:
            if self.background_image and Path(self.background_image).exists():
                # Load background image
                img = Image.open(self.background_image)
                img_array = np.array(img)

                # Create VTK image data
                vtk_img = vtk.vtkImageData()
                vtk_img.SetDimensions(img_array.shape[1], img_array.shape[0], 1)

                # Convert to VTK format
                depth_array = vtk_np.numpy_to_vtk(
                    img_array.reshape(-1, 3), deep=True
                )
                depth_array.SetNumberOfComponents(3)
                vtk_img.GetPointData().SetScalars(depth_array)

                # Create texture
                texture = vtk.vtkTexture()
                texture.SetInputData(vtk_img)

                # Set as background
                renderer.SetBackgroundTexture(texture)
                renderer.TexturedBackgroundOn()
                self.logger.debug(f"Set background image: {self.background_image}")
            else:
                # Use default light gray background
                renderer.SetBackground(0.95, 0.95, 0.95)
                self.logger.debug("Using default background color")
        except Exception as e:
            self.logger.warning(f"Failed to set background: {e}")
            # Fallback to default
            renderer.SetBackground(0.95, 0.95, 0.95)

    def _save_screenshot(self, render_window: vtk.vtkRenderWindow, output_path: str) -> bool:
        """Save screenshot to file."""
        try:
            # Use VTK's window-to-image filter
            w2if = vtk.vtkWindowToImageFilter()
            w2if.SetInput(render_window)
            w2if.Update()

            # Convert to PIL Image
            data = w2if.GetOutput()
            width, height = data.GetDimensions()[:2]

            # Get image data as numpy array
            img_array = vtk_np.vtk_to_numpy(data.GetPointData().GetScalars())
            img_array = img_array.reshape((height, width, 3))

            # Create PIL Image and save
            img = Image.fromarray(img_array.astype('uint8'), 'RGB')
            img.save(output_path)

            return True
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return False

    def _get_temp_screenshot_path(self) -> str:
        """Get a temporary file path for screenshot."""
        temp_dir = Path(tempfile.gettempdir()) / "3dmm_screenshots"
        temp_dir.mkdir(exist_ok=True)
        return str(temp_dir / f"screenshot_{id(self)}.png")

