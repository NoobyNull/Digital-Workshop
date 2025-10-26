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

        # Load grid, ground, and gradient settings from QSettings with fallback to config
        try:
            from PySide6.QtCore import QSettings
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Grid settings - load from QSettings with fallback to config
            self.grid_visible = settings.value("viewer/grid_visible", config.grid_visible, type=bool)
            self.grid_color = settings.value("viewer/grid_color", config.grid_color, type=str)
            self.grid_size = settings.value("viewer/grid_size", config.grid_size, type=float)

            # Ground settings
            self.ground_visible = settings.value("viewer/ground_visible", config.ground_visible, type=bool)
            self.ground_color = settings.value("viewer/ground_color", config.ground_color, type=str)
            self.ground_offset = settings.value("viewer/ground_offset", config.ground_offset, type=float)

            # Gradient settings - load from QSettings with fallback to config
            self.gradient_top_color = settings.value("viewer/gradient_top_color", config.gradient_top_color, type=str)
            self.gradient_bottom_color = settings.value("viewer/gradient_bottom_color", config.gradient_bottom_color, type=str)
            self.enable_gradient = settings.value("viewer/enable_gradient", config.enable_gradient, type=bool)
        except Exception as e:
            logger.warning(f"Failed to load grid/ground/gradient settings from QSettings: {e}")
            self.grid_visible = True
            self.grid_color = "#CCCCCC"
            self.grid_size = 10.0
            self.ground_visible = True
            self.ground_color = "#999999"
            self.ground_offset = 0.5

            # Default gradient settings
            self.gradient_top_color = "#4A6FA5"
            self.gradient_bottom_color = "#1E3A5F"
            self.enable_gradient = True

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
        
        # Configure gradient based on settings
        if self.enable_gradient:
            self.renderer.GradientBackgroundOn()
            
            # Convert hex colors to RGB tuples
            top_rgb = self._hex_to_rgb(self.gradient_top_color)
            bottom_rgb = self._hex_to_rgb(self.gradient_bottom_color)
            
            self.renderer.SetBackground2(*top_rgb)    # Top of gradient
            self.renderer.SetBackground(*bottom_rgb)  # Bottom of gradient
            
            logger.debug(f"Applied gradient background: top={self.gradient_top_color}, bottom={self.gradient_bottom_color}")
        else:
            self.renderer.GradientBackgroundOff()
            # Use solid background color from theme
            bg_rgb = vtk_rgb('canvas_bg')
            self.renderer.SetBackground(*bg_rgb)
            logger.debug(f"Applied solid background color: {bg_rgb}")

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
        """Set up grid and ground plane using config settings."""
        try:
            logger.info(f"Creating initial grid and ground with grid_visible={self.grid_visible}, ground_visible={self.ground_visible}")
            self.update_grid(radius=100.0, center_x=0.0, center_y=0.0)
            self.create_ground_plane(radius=100.0, center_x=0.0, center_y=0.0)

            if self.grid_actor:
                self.grid_actor.SetVisibility(self.grid_visible)
                logger.info(f"Grid actor visibility set to {self.grid_visible}")
            if self.ground_actor:
                self.ground_actor.SetVisibility(self.ground_visible)
                logger.info(f"Ground actor visibility set to {self.ground_visible}")
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

    def toggle_ground_plane(self) -> None:
        """Toggle ground plane visibility."""
        self.ground_visible = not self.ground_visible
        if self.ground_actor:
            self.ground_actor.SetVisibility(self.ground_visible)
            logger.debug(f"Ground plane visibility toggled to {self.ground_visible}")

    def update_grid(self, radius: float, center_x: float = 0.0, center_y: float = 0.0) -> None:
        """Update grid visualization using config settings."""
        # Remove existing grid if present
        if self.grid_actor and self.renderer:
            self.renderer.RemoveActor(self.grid_actor)

        # Create grid source
        grid_source = vtk.vtkPlaneSource()
        grid_source.SetOrigin(-radius + center_x, -radius + center_y, 0)
        grid_source.SetPoint1(radius + center_x, -radius + center_y, 0)
        grid_source.SetPoint2(-radius + center_x, radius + center_y, 0)
        grid_source.SetXResolution(int(self.grid_size))
        grid_source.SetYResolution(int(self.grid_size))

        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(grid_source.GetOutputPort())

        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(mapper)

        # Apply grid color from config
        grid_rgb = self._hex_to_rgb(self.grid_color)
        self.grid_actor.GetProperty().SetColor(*grid_rgb)
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
        """Create ground plane using config settings."""
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

        # Apply ground color from config
        ground_rgb = self._hex_to_rgb(self.ground_color)
        self.ground_actor.GetProperty().SetColor(*ground_rgb)
        self.ground_actor.GetProperty().SetOpacity(0.3)
        self.ground_actor.SetVisibility(self.ground_visible)

        self.renderer.AddActor(self.ground_actor)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def render(self) -> None:
        """Trigger a render with enhanced error handling."""
        if self.render_window:
            try:
                # Use fallback renderer for safe rendering
                from src.gui.vtk import get_vtk_fallback_renderer
                fallback_renderer = get_vtk_fallback_renderer()

                success = fallback_renderer.render_with_fallback(self.render_window)
                if not success:
                    logger.debug("Fallback render failed, continuing anyway")

            except Exception as e:
                logger.debug(f"Render error: {e}")
                # Continue silently - errors are handled by the fallback renderer

    def reset_camera(self) -> None:
        """Reset camera to default position."""
        if self.renderer:
            self.renderer.ResetCamera()
            self.render()

    def cleanup(self) -> None:
        """Clean up VTK resources using enhanced error handling."""
        try:
            logger.info("Cleaning up VTK scene resources with enhanced error handling")

            # Use the cleanup coordinator for proper cleanup sequence
            from src.gui.vtk import get_vtk_cleanup_coordinator

            cleanup_coordinator = get_vtk_cleanup_coordinator()

            # Coordinate cleanup using the enhanced system
            # Resources are already registered in viewer_widget_facade, so just coordinate cleanup
            cleanup_success = cleanup_coordinator.coordinate_cleanup(
                render_window=self.render_window,
                renderer=self.renderer,
                interactor=self.interactor
            )

            if cleanup_success:
                logger.info("Enhanced VTK scene cleanup completed successfully")
            else:
                logger.info("Enhanced VTK scene cleanup completed with context loss (normal)")

            # Clear local references
            self.grid_actor = None
            self.ground_actor = None
            self.camera_widget = None
            self.marker = None
            self.interactor = None
            self.render_window = None
            self.renderer = None

        except Exception as e:
            logger.warning(f"Error during enhanced VTK cleanup: {e}")
            # Fallback to basic cleanup
            self._basic_cleanup()

    def _basic_cleanup(self) -> None:
        """Basic cleanup fallback if enhanced cleanup fails."""
        try:
            logger.info("Performing basic VTK cleanup fallback")

            # Basic cleanup operations
            try:
                if self.render_window:
                    self.render_window.Finalize()
            except Exception as e:
                logger.debug(f"Basic render window cleanup error: {e}")

            try:
                if self.interactor:
                    self.interactor.TerminateApp()
            except Exception as e:
                logger.debug(f"Basic interactor cleanup error: {e}")

            try:
                if self.renderer:
                    self.renderer.RemoveAllViewProps()
            except Exception as e:
                logger.debug(f"Basic renderer cleanup error: {e}")

            # Clear references
            self.grid_actor = None
            self.ground_actor = None
            self.camera_widget = None
            self.marker = None
            self.interactor = None
            self.render_window = None
            self.renderer = None

            logger.info("Basic VTK cleanup completed")

        except Exception as e:
            logger.error(f"Error during basic cleanup: {e}")

    def reload_settings_from_qsettings(self) -> None:
        """
        Reload all viewer settings from QSettings and apply them.
        Called when preferences are changed.
        """
        try:
            from PySide6.QtCore import QSettings
            from src.core.application_config import ApplicationConfig
            
            config = ApplicationConfig.get_default()
            settings = QSettings()
            
            # Reload grid settings
            self.grid_visible = settings.value("viewer/grid_visible", config.grid_visible, type=bool)
            self.grid_color = settings.value("viewer/grid_color", config.grid_color, type=str)
            self.grid_size = settings.value("viewer/grid_size", config.grid_size, type=float)
            
            # Reload ground settings
            self.ground_visible = settings.value("viewer/ground_visible", config.ground_visible, type=bool)
            self.ground_color = settings.value("viewer/ground_color", config.ground_color, type=str)
            self.ground_offset = settings.value("viewer/ground_offset", config.ground_offset, type=float)
            
            # Reload gradient settings
            self.gradient_top_color = settings.value("viewer/gradient_top_color", config.gradient_top_color, type=str)
            self.gradient_bottom_color = settings.value("viewer/gradient_bottom_color", config.gradient_bottom_color, type=str)
            self.enable_gradient = settings.value("viewer/enable_gradient", config.enable_gradient, type=bool)
            
            # Apply gradient changes
            self.update_gradient_colors()
            
            # Apply grid/ground changes
            if self.grid_actor:
                self.grid_actor.SetVisibility(self.grid_visible)
                grid_rgb = self._hex_to_rgb(self.grid_color)
                self.grid_actor.GetProperty().SetColor(*grid_rgb)
            
            if self.ground_actor:
                self.ground_actor.SetVisibility(self.ground_visible)
                ground_rgb = self._hex_to_rgb(self.ground_color)
                self.ground_actor.GetProperty().SetColor(*ground_rgb)
            
            self.render()
            logger.info("Viewer settings reloaded from QSettings and applied")
            
        except Exception as e:
            logger.error(f"Failed to reload settings from QSettings: {e}", exc_info=True)
    
    def update_gradient_colors(self, top_color: str = None, bottom_color: str = None, enable_gradient: bool = None) -> None:
        """
        Update the background gradient colors and settings.
        
        Args:
            top_color: Hex color string for top of gradient (optional)
            bottom_color: Hex color string for bottom of gradient (optional)
            enable_gradient: Whether to enable gradient background (optional)
        """
        try:
            # Update settings if provided
            if top_color is not None:
                self.gradient_top_color = top_color
            if bottom_color is not None:
                self.gradient_bottom_color = bottom_color
            if enable_gradient is not None:
                self.enable_gradient = enable_gradient
            
            # Reconfigure renderer background
            if self.enable_gradient:
                self.renderer.GradientBackgroundOn()
                
                # Convert hex colors to RGB tuples
                top_rgb = self._hex_to_rgb(self.gradient_top_color)
                bottom_rgb = self._hex_to_rgb(self.gradient_bottom_color)
                
                self.renderer.SetBackground2(*top_rgb)
                self.renderer.SetBackground(*bottom_rgb)
                
                logger.info(f"Updated gradient background: top={self.gradient_top_color}, bottom={self.gradient_bottom_color}")
            else:
                self.renderer.GradientBackgroundOff()
                # Use solid background color from theme
                bg_rgb = vtk_rgb('canvas_bg')
                self.renderer.SetBackground(*bg_rgb)
                logger.info("Updated to solid background color")
            
            # Trigger re-render
            self.render()
            
        except Exception as e:
            logger.error(f"Failed to update gradient colors: {e}", exc_info=True)

