"""
Unified VTK rendering engine for thumbnails and screenshots.

Provides a shared rendering pipeline to eliminate code duplication
between ThumbnailGenerator and ScreenshotGenerator.
"""

import math
from pathlib import Path
from typing import Tuple, Union

import vtk

from src.core.logging_config import get_logger


class VTKRenderingEngine:
    """
    Unified VTK rendering engine for both thumbnails and screenshots.

    Handles:
    - Offscreen rendering setup
    - Camera configuration with zoom
    - Background plane creation with dynamic sizing
    - Lighting setup
    - Screenshot capture
    """

    def __init__(self, width: int = 1280, height: int = 1280):
        """
        Initialize the rendering engine.

        Args:
            width: Render window width (default 1280 for high quality)
            height: Render window height (default 1280 for high quality)
        """
        self.logger = get_logger(__name__)
        self.width = width
        self.height = height
        self.render_window = None
        self.renderer = None
        self.camera = None

    def setup_render_window(self) -> bool:
        """
        Create and configure offscreen render window.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.render_window = vtk.vtkRenderWindow()
            self.render_window.SetOffScreenRendering(1)
            self.render_window.SetSize(self.width, self.height)

            self.renderer = vtk.vtkRenderer()
            self.render_window.AddRenderer(self.renderer)

            self.camera = self.renderer.GetActiveCamera()

            self.logger.debug("Render window created: %sx{self.height}", self.width)
            return True
        except Exception as e:
            self.logger.error("Failed to setup render window: %s", e)
            return False

    def set_background_color(self, color: Union[str, Tuple[float, float, float]]) -> None:
        """
        Set solid background color.

        Args:
            color: Hex string (e.g., '#FFFFFF') or RGB tuple (0-1)
        """
        try:
            if isinstance(color, str) and color.startswith("#"):
                # Convert hex to RGB
                hex_color = color.lstrip("#")
                r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
                self.renderer.SetBackground(r, g, b)
            elif isinstance(color, (tuple, list)) and len(color) == 3:
                self.renderer.SetBackground(*color)
            else:
                # Professional studio background: dark teal-gray
                self.renderer.SetBackground(0.25, 0.35, 0.40)
        except Exception as e:
            self.logger.error("Failed to set background color: %s", e)
            # Professional studio background: dark teal-gray
            self.renderer.SetBackground(0.25, 0.35, 0.40)

    def set_background_image(self, image_path: str) -> None:
        """
        Set background image with dynamic plane sizing.

        Args:
            image_path: Path to background image file
        """
        try:
            if not Path(image_path).exists():
                self.logger.warning("Background image not found: %s", image_path)
                return

            # Read image
            reader = vtk.vtkPNGReader()
            if image_path.lower().endswith((".jpg", ".jpeg")):
                reader = vtk.vtkJPEGReader()

            reader.SetFileName(image_path)
            reader.Update()

            # Create texture
            texture = vtk.vtkTexture()
            texture.SetInputConnection(reader.GetOutputPort())
            texture.InterpolateOn()
            texture.EdgeClampOn()
            texture.RepeatOn()

            # Calculate dynamic plane size based on camera distance
            cam_pos = self.camera.GetPosition()
            cam_focal = self.camera.GetFocalPoint()

            dx = cam_pos[0] - cam_focal[0]
            dy = cam_pos[1] - cam_focal[1]
            dz = cam_pos[2] - cam_focal[2]
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            scale = max(distance * 2.0, 500.0)

            # Create background plane
            plane = vtk.vtkPlaneSource()
            plane.SetOrigin(-scale, -scale, cam_focal[2] - distance * 1.5)
            plane.SetPoint1(scale, -scale, cam_focal[2] - distance * 1.5)
            plane.SetPoint2(-scale, scale, cam_focal[2] - distance * 1.5)
            plane.SetResolution(1, 1)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(plane.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # Set texture on diffuse property (works better with LightingOff)
            actor.GetProperty().SetTexture("map_d", texture)
            actor.GetProperty().LightingOff()
            actor.GetProperty().SetOpacity(1.0)

            self.renderer.AddActor(actor)
            self.logger.debug("Background image set: %s", image_path)

        except Exception as e:
            self.logger.error("Failed to set background image: %s", e)

    def setup_lighting(self) -> None:
        """Setup professional studio lighting for rendering."""
        try:
            self.renderer.RemoveAllLights()

            # Key light - main directional light from upper right
            key_light = vtk.vtkLight()
            key_light.SetPosition(150, 150, 200)
            key_light.SetIntensity(1.0)
            key_light.SetColor(1.0, 1.0, 1.0)
            key_light.SetLightTypeToSceneLight()
            self.renderer.AddLight(key_light)

            # Fill light - softer light from opposite side
            fill_light = vtk.vtkLight()
            fill_light.SetPosition(-100, -50, 100)
            fill_light.SetIntensity(0.6)
            fill_light.SetColor(0.9, 0.9, 1.0)  # Slight blue tint
            fill_light.SetLightTypeToSceneLight()
            self.renderer.AddLight(fill_light)

            # Rim light - subtle light from behind
            rim_light = vtk.vtkLight()
            rim_light.SetPosition(0, 0, -150)
            rim_light.SetIntensity(0.4)
            rim_light.SetColor(0.8, 0.8, 0.9)
            rim_light.SetLightTypeToSceneLight()
            self.renderer.AddLight(rim_light)

            # Ambient light - subtle overall illumination
            ambient_light = vtk.vtkLight()
            ambient_light.SetLightTypeToHeadlight()
            ambient_light.SetIntensity(0.3)
            ambient_light.SetColor(1.0, 1.0, 1.0)
            self.renderer.AddLight(ambient_light)

            self.logger.debug("Professional studio lighting setup complete")
        except Exception as e:
            self.logger.warning("Failed to setup lighting: %s", e)

    def setup_camera(self, bounds: Tuple[float, ...], zoom_factor: float = 1.0) -> None:
        """
        Setup camera to fit model with optional zoom.

        Args:
            bounds: Model bounds (xmin, xmax, ymin, ymax, zmin, zmax)
            zoom_factor: Camera zoom (>1.0 zooms out, <1.0 zooms in)
        """
        try:
            self.renderer.ResetCamera()
            self.renderer.ResetCameraClippingRange()

            if zoom_factor != 1.0:
                self.camera.Zoom(zoom_factor)

            self.logger.debug("Camera setup complete (zoom: %s)", zoom_factor)
        except Exception as e:
            self.logger.error("Failed to setup camera: %s", e)

    def render(self) -> None:
        """Perform rendering."""
        try:
            self.render_window.Render()
            self.logger.debug("Render complete")
        except Exception as e:
            self.logger.error("Failed to render: %s", e)

    def capture_screenshot(self, output_path: str) -> bool:
        """
        Capture screenshot to file.

        Args:
            output_path: Path to save screenshot

        Returns:
            True if successful, False otherwise
        """
        try:
            window_to_image = vtk.vtkWindowToImageFilter()
            window_to_image.SetInput(self.render_window)
            window_to_image.SetScale(1)
            window_to_image.SetInputBufferTypeToRGB()
            window_to_image.ReadFrontBufferOff()
            window_to_image.Update()

            writer = vtk.vtkPNGWriter()
            writer.SetFileName(str(output_path))
            writer.SetInputConnection(window_to_image.GetOutputPort())
            writer.Write()

            self.logger.debug("Screenshot saved: %s", output_path)
            return True
        except Exception as e:
            self.logger.error("Failed to capture screenshot: %s", e)
            return False

    def cleanup(self) -> None:
        """Cleanup VTK resources."""
        try:
            if self.render_window:
                self.render_window.Finalize()
                self.render_window = None
            self.renderer = None
            self.camera = None
            self.logger.debug("Cleanup complete")
        except Exception as e:
            self.logger.warning("Cleanup error: %s", e)
