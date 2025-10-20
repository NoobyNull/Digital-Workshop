"""
Camera control for 3D viewer.

Handles camera positioning, view management, and orientation preservation.
"""

import math
from typing import Optional, Tuple

import vtk

from src.core.logging_config import get_logger, log_function_call
from src.parsers.stl_parser import STLModel


logger = get_logger(__name__)


class CameraController:
    """Manages camera positioning and view control."""

    def __init__(self, renderer, render_window):
        """
        Initialize camera controller.

        Args:
            renderer: VTK renderer
            render_window: VTK render window
        """
        self.renderer = renderer
        self.render_window = render_window

        # Load camera settings from config
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()
            self.mouse_sensitivity = config.mouse_sensitivity
            self.fps_limit = config.fps_limit
            self.zoom_speed = config.zoom_speed
            self.pan_speed = config.pan_speed
            self.auto_fit_on_load = config.auto_fit_on_load
        except Exception as e:
            logger.warning(f"Failed to load camera settings from config: {e}")
            self.mouse_sensitivity = 1.0
            self.fps_limit = 0
            self.zoom_speed = 1.0
            self.pan_speed = 1.0
            self.auto_fit_on_load = True

    @log_function_call(logger)
    def fit_camera_to_model(
        self,
        model: STLModel,
        actor: Optional[vtk.vtkActor],
        update_grid_callback=None,
        update_ground_callback=None
    ) -> None:
        """
        Fit camera to model bounds.

        Args:
            model: The model to fit
            actor: The VTK actor
            update_grid_callback: Optional callback to update grid
            update_ground_callback: Optional callback to update ground
        """
        try:
            if not model or not actor:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.render_window.Render()
                logger.debug("Camera reset (no actor)")
                return

            # Get bounds
            bounds = actor.GetBounds()
            if not bounds:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.render_window.Render()
                logger.debug("Camera reset (no bounds)")
                return

            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            cx = (xmin + xmax) * 0.5
            cy = (ymin + ymax) * 0.5
            cz = (zmin + zmax) * 0.5

            # Calculate radius
            dx = max(1e-6, xmax - xmin)
            dy = max(1e-6, ymax - ymin)
            dz = max(1e-6, zmax - zmin)
            diag = (dx * dx + dy * dy + dz * dz) ** 0.5
            radius = max(1e-3, 0.5 * diag)

            # Update grid and ground
            if update_grid_callback:
                update_grid_callback(radius, center_x=cx, center_y=cy)
            if update_ground_callback:
                ground_z = zmin - 0.5
                update_ground_callback(radius, center_x=cx, center_y=cy, z_position=ground_z)

            # Set camera
            cam = self.renderer.GetActiveCamera()
            if cam is None:
                cam = vtk.vtkCamera()
                self.renderer.SetActiveCamera(cam)

            distance = max(1.0, radius * 2.2)
            cam.SetFocalPoint(cx, cy, cz)
            cam.SetPosition(cx, cy, cz + distance)
            cam.SetViewUp(0.0, 1.0, 0.0)

            # Set clipping range
            try:
                near = max(0.001, distance - (radius * 4.0))
                far = distance + (radius * 4.0)
                if far <= near:
                    far = near * 10.0
                cam.SetClippingRange(near, far)
            except Exception:
                pass

            try:
                self.renderer.ResetCameraClippingRange()
            except Exception:
                pass

            try:
                self.render_window.Render()
            except Exception:
                pass

            logger.debug(
                f"Camera fitted to model: center=({cx:.3f},{cy:.3f},{cz:.3f}) "
                f"radius={radius:.3f} distance={distance:.3f}"
            )

        except Exception as e:
            logger.warning(f"Fallback camera reset due to error: {e}")
            try:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.render_window.Render()
            except Exception:
                pass

    @log_function_call(logger)
    def fit_camera_preserving_orientation(
        self,
        model: STLModel,
        actor: Optional[vtk.vtkActor]
    ) -> None:
        """
        Fit camera to model while preserving orientation.

        Args:
            model: The model to fit
            actor: The VTK actor
        """
        try:
            if not model or not actor:
                logger.debug("No model or actor for orientation-preserving fit")
                return

            camera = self.renderer.GetActiveCamera()
            if not camera:
                logger.debug("No camera for orientation-preserving fit")
                return

            # Get bounds
            bounds = actor.GetBounds()
            if not bounds:
                logger.debug("No bounds for orientation-preserving fit")
                return

            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            cx = (xmin + xmax) * 0.5
            cy = (ymin + ymax) * 0.5
            cz = (zmin + zmax) * 0.5

            # Calculate radius
            dx = max(1e-6, xmax - xmin)
            dy = max(1e-6, ymax - ymin)
            dz = max(1e-6, zmax - zmin)
            diag = (dx * dx + dy * dy + dz * dz) ** 0.5
            radius = max(1e-3, 0.5 * diag)

            # Get current orientation
            current_pos = camera.GetPosition()
            current_focal = camera.GetFocalPoint()
            current_view_up = camera.GetViewUp()

            # Calculate view direction
            view_dir_x = current_focal[0] - current_pos[0]
            view_dir_y = current_focal[1] - current_pos[1]
            view_dir_z = current_focal[2] - current_pos[2]

            # Normalize
            view_length = (view_dir_x**2 + view_dir_y**2 + view_dir_z**2) ** 0.5
            if view_length < 1e-6:
                logger.debug("Invalid view direction")
                return

            view_dir_x /= view_length
            view_dir_y /= view_length
            view_dir_z /= view_length

            # Calculate required distance
            fov_rad = math.radians(30.0)
            required_distance = radius / math.tan(fov_rad / 2.0)
            required_distance *= 1.2

            # Calculate new position
            new_pos_x = cx - (view_dir_x * required_distance)
            new_pos_y = cy - (view_dir_y * required_distance)
            new_pos_z = cz - (view_dir_z * required_distance)

            # Update camera
            camera.SetFocalPoint(cx, cy, cz)
            camera.SetPosition(new_pos_x, new_pos_y, new_pos_z)
            camera.SetViewUp(current_view_up[0], current_view_up[1], current_view_up[2])

            # Update clipping range
            try:
                near = max(0.001, required_distance - (radius * 4.0))
                far = required_distance + (radius * 4.0)
                if far <= near:
                    far = near * 10.0
                camera.SetClippingRange(near, far)
                self.renderer.ResetCameraClippingRange()
            except Exception:
                pass

            try:
                self.render_window.Render()
            except Exception:
                pass

            logger.debug(
                f"Camera fitted preserving orientation: center=({cx:.3f},{cy:.3f},{cz:.3f}) "
                f"radius={radius:.3f} distance={required_distance:.3f}"
            )

        except Exception as e:
            logger.error(f"Failed to fit camera preserving orientation: {e}")
            try:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.render_window.Render()
            except Exception:
                pass

    def reset_view(self) -> None:
        """Reset camera to default view."""
        try:
            self.renderer.ResetCamera()
            self.render_window.Render()
            logger.debug("Camera view reset")
        except Exception as e:
            logger.error(f"Failed to reset view: {e}")

    def rotate_around_view_axis(self, degrees: float) -> None:
        """
        Rotate view around the view axis.

        Args:
            degrees: Degrees to rotate (positive = clockwise)
        """
        try:
            camera = self.renderer.GetActiveCamera()
            if not camera:
                return

            # Get current camera state
            pos = camera.GetPosition()
            focal = camera.GetFocalPoint()
            view_up = camera.GetViewUp()

            # Calculate view direction
            view_x = focal[0] - pos[0]
            view_y = focal[1] - pos[1]
            view_z = focal[2] - pos[2]

            # Rotate view_up around view direction
            angle_rad = math.radians(degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            # Rodrigues' rotation formula
            k_dot_v = (view_x * view_up[0] + view_y * view_up[1] + view_z * view_up[2])
            k_norm = (view_x**2 + view_y**2 + view_z**2) ** 0.5

            if k_norm < 1e-6:
                return

            k_x = view_x / k_norm
            k_y = view_y / k_norm
            k_z = view_z / k_norm

            new_up_x = (
                view_up[0] * cos_a +
                (k_y * view_up[2] - k_z * view_up[1]) * sin_a +
                k_x * k_dot_v * (1 - cos_a)
            )
            new_up_y = (
                view_up[1] * cos_a +
                (k_z * view_up[0] - k_x * view_up[2]) * sin_a +
                k_y * k_dot_v * (1 - cos_a)
            )
            new_up_z = (
                view_up[2] * cos_a +
                (k_x * view_up[1] - k_y * view_up[0]) * sin_a +
                k_z * k_dot_v * (1 - cos_a)
            )

            camera.SetViewUp(new_up_x, new_up_y, new_up_z)
            self.render_window.Render()

            logger.debug(f"View rotated by {degrees} degrees")

        except Exception as e:
            logger.error(f"Failed to rotate view: {e}")

