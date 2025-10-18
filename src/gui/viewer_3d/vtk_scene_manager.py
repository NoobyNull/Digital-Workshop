"""
VTK scene management for 3D viewer.

Handles VTK renderer, render window, interactor, and scene elements
like grid, ground plane, and orientation widget.
"""

import multiprocessing as _mp
from typing import Optional

import vtk

from src.core.logging_config import get_logger, log_function_call
from src.gui.theme import vtk_rgb


logger = get_logger(__name__)


class VTKSceneManager:
    """Manages VTK scene setup and configuration."""

    def __init__(self, vtk_widget):
        """
        Initialize VTK scene manager.

        Args:
            vtk_widget: QVTKRenderWindowInteractor widget
        """
        self.vtk_widget = vtk_widget
        self.renderer = None
        self.render_window = None
        self.interactor = None
        self.camera_widget = None
        self.marker = None
        self.grid_actor = None
        self.ground_actor = None
        self.grid_visible = True

    @log_function_call(logger)
    def setup_scene(self) -> None:
        """Set up the VTK scene with renderer and interactor."""
        self._setup_renderer()
        self._setup_render_window()
        self._setup_interactor()
        self._setup_orientation_widget()
        self._setup_grid_and_ground()
        self._setup_camera()
        logger.debug("VTK scene setup completed")

    def _setup_renderer(self) -> None:
        """Set up the VTK renderer with lighting."""
        self.renderer = vtk.vtkRenderer()
        self.renderer.GradientBackgroundOn()

        bg_rgb = vtk_rgb('canvas_bg')
        top_color = (
            max(0, bg_rgb[0] - 0.15),
            max(0, bg_rgb[1] - 0.15),
            max(0, bg_rgb[2] - 0.15)
        )
        self.renderer.SetBackground2(*top_color)
        self.renderer.SetBackground(*bg_rgb)

        # Configure multi-threading
        try:
            threads = max(2, (_mp.cpu_count() or 2))
            vtk.vtkMultiThreader.SetGlobalDefaultNumberOfThreads(threads)
            if hasattr(vtk, "vtkSMPTools"):
                try:
                    vtk.vtkSMPTools.SetNumberOfThreads(threads)
                except Exception:
                    pass
            logger.info(f"VTK thread count set to {threads}")
        except Exception:
            pass

        # Add lighting
        light1 = vtk.vtkLight()
        light1.SetPosition(100, 100, 100)
        light1.SetIntensity(0.8)
        light1.SetColor(*vtk_rgb('light_color'))
        self.renderer.AddLight(light1)

        light2 = vtk.vtkLight()
        light2.SetPosition(-100, -100, 100)
        light2.SetIntensity(0.5)
        light2.SetColor(*vtk_rgb('light_color'))
        self.renderer.AddLight(light2)

    def _setup_render_window(self) -> None:
        """Set up the render window."""
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)

    def _setup_interactor(self) -> None:
        """Set up the interactor with trackball camera style."""
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        try:
            style = vtk.vtkInteractorStyleTrackballCamera()
            style.SetMotionFactor(8.0)
            self.interactor.SetInteractorStyle(style)

            try:
                self.interactor.SetDesiredUpdateRate(60.0)
                self.interactor.SetStillUpdateRate(10.0)
            except Exception:
                pass

            logger.debug("VTK interactor style set to TrackballCamera")
        except Exception:
            pass

    def _setup_orientation_widget(self) -> None:
        """Set up the camera orientation widget."""
        try:
            if hasattr(vtk, "vtkCameraOrientationWidget"):
                self.camera_widget = vtk.vtkCameraOrientationWidget()
                self.camera_widget.SetInteractor(self.interactor)
                self.camera_widget.SetParentRenderer(self.renderer)

                try:
                    self.camera_widget.SetViewportCorner(
                        vtk.vtkCameraOrientationWidget.UpperRight
                    )
                except Exception:
                    pass

                try:
                    self.camera_widget.SetEnableInteractivity(True)
                except Exception:
                    pass

                try:
                    self.camera_widget.SetEnabled(1)
                except Exception:
                    self.camera_widget.On()
            else:
                self._setup_fallback_orientation_widget()
        except Exception:
            pass

    def _setup_fallback_orientation_widget(self) -> None:
        """Set up fallback orientation widget using annotated cube."""
        try:
            cube = vtk.vtkAnnotatedCubeActor()

            try:
                cube.SetFaceText(0, "X+")
                cube.SetFaceText(1, "X-")
                cube.SetFaceText(2, "Y+")
                cube.SetFaceText(3, "Y-")
                cube.SetFaceText(4, "Z+")
                cube.SetFaceText(5, "Z-")
            except Exception:
                pass

            try:
                c = vtk_rgb('edge_color')
                cube.GetTextEdgesProperty().SetColor(*c)
                cube.GetXPlusFaceProperty().SetColor(0.85, 0.25, 0.25)
                cube.GetXMinusFaceProperty().SetColor(0.60, 0.15, 0.15)
                cube.GetYPlusFaceProperty().SetColor(0.25, 0.85, 0.25)
                cube.GetYMinusFaceProperty().SetColor(0.15, 0.60, 0.15)
                cube.GetZPlusFaceProperty().SetColor(0.25, 0.25, 0.85)
                cube.GetZMinusFaceProperty().SetColor(0.15, 0.15, 0.60)
            except Exception:
                pass

            self.marker = vtk.vtkOrientationMarkerWidget()
            self.marker.SetOrientationMarker(cube)
            self.marker.SetInteractor(self.interactor)
            self.marker.SetEnabled(1)
            self.marker.InteractiveOn()
            self.marker.SetViewport(0.8, 0.8, 1.0, 1.0)
        except Exception:
            pass

    def _setup_grid_and_ground(self) -> None:
        """Set up grid and ground plane."""
        try:
            logger.info(f"Creating initial grid and ground with grid_visible={self.grid_visible}")
            self.grid_visible = True
            self.update_grid(radius=100.0, center_x=0.0, center_y=0.0)
            self.create_ground_plane(radius=100.0, center_x=0.0, center_y=0.0)

            if self.grid_actor:
                self.grid_actor.SetVisibility(True)
                logger.info("Grid actor visibility set to True")
            if self.ground_actor:
                self.ground_actor.SetVisibility(True)
                logger.info("Ground actor visibility set to True")
        except Exception as e:
            logger.error(f"Failed to create initial grid/ground: {e}", exc_info=True)

    def _setup_camera(self) -> None:
        """Set up default camera."""
        self.renderer.ResetCamera()
        self.interactor.Initialize()

    def toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self.grid_visible = not self.grid_visible
        if self.grid_actor:
            self.grid_actor.SetVisibility(self.grid_visible)
            logger.debug(f"Grid visibility toggled to {self.grid_visible}")

    def update_grid(self, radius: float, center_x: float = 0.0, center_y: float = 0.0) -> None:
        """Update grid visualization."""
        # Remove existing grid if present
        if self.grid_actor and self.renderer:
            self.renderer.RemoveActor(self.grid_actor)

        # Create grid source
        grid_source = vtk.vtkPlaneSource()
        grid_source.SetOrigin(-radius + center_x, -radius + center_y, 0)
        grid_source.SetPoint1(radius + center_x, -radius + center_y, 0)
        grid_source.SetPoint2(-radius + center_x, radius + center_y, 0)
        grid_source.SetXResolution(20)
        grid_source.SetYResolution(20)

        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(grid_source.GetOutputPort())

        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(mapper)
        self.grid_actor.GetProperty().SetColor(*vtk_rgb('grid_color'))
        self.grid_actor.GetProperty().SetRepresentationToWireframe()
        self.grid_actor.SetVisibility(self.grid_visible)

        self.renderer.AddActor(self.grid_actor)

    def create_ground_plane(
        self,
        radius: float,
        center_x: float = 0.0,
        center_y: float = 0.0,
        z_position: float = -0.1
    ) -> None:
        """Create ground plane."""
        # Remove existing ground if present
        if self.ground_actor and self.renderer:
            self.renderer.RemoveActor(self.ground_actor)

        # Create ground plane source
        ground_source = vtk.vtkPlaneSource()
        ground_source.SetOrigin(-radius + center_x, -radius + center_y, z_position)
        ground_source.SetPoint1(radius + center_x, -radius + center_y, z_position)
        ground_source.SetPoint2(-radius + center_x, radius + center_y, z_position)

        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(ground_source.GetOutputPort())

        self.ground_actor = vtk.vtkActor()
        self.ground_actor.SetMapper(mapper)
        self.ground_actor.GetProperty().SetColor(*vtk_rgb('ground_color'))
        self.ground_actor.GetProperty().SetOpacity(0.3)

        self.renderer.AddActor(self.ground_actor)

    def render(self) -> None:
        """Trigger a render."""
        if self.render_window:
            self.render_window.Render()

    def reset_camera(self) -> None:
        """Reset camera to default position."""
        if self.renderer:
            self.renderer.ResetCamera()
            self.render()

