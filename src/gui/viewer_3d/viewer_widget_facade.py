"""
Refactored VTK-based 3D viewer widget facade.

Integrates modular components (scene manager, renderer, camera, etc.)
while maintaining backward compatibility with the original API.
"""

import gc
import math
import time
from typing import Optional, Any

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget

import vtk

from src.core.logging_config import get_logger, log_function_call
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.stl_parser import STLModel
from src.core.data_structures import Model, LoadingState, Triangle, Vector3D
from src.gui.theme import vtk_rgb
from src.gui.material_picker_widget import MaterialPickerWidget

from .vtk_scene_manager import VTKSceneManager
from .model_renderer import ModelRenderer, RenderMode
from .camera_controller import CameraController
from .performance_tracker import PerformanceTracker
from .viewer_ui_manager import ViewerUIManager


logger = get_logger(__name__)


class Viewer3DWidget(QWidget):
    """
    Refactored 3D viewer widget using VTK with modular architecture.

    Integrates:
    - VTKSceneManager: Scene setup and management
    - ModelRenderer: Model geometry and rendering
    - CameraController: Camera positioning and view control
    - PerformanceTracker: FPS and performance monitoring
    - ViewerUIManager: UI layout and controls
    """

    # Signals for UI integration
    model_loaded = Signal(str)
    render_mode_changed = Signal(str)
    performance_updated = Signal(float)
    loading_progress_updated = Signal(float, str)
    lighting_panel_requested = Signal()
    material_selected = Signal(str)
    save_view_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the 3D viewer widget."""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.logger.info("Initializing refactored VTK-based 3D viewer widget")

        # State
        self.current_model = None
        self.loading_in_progress = False

        # Performance settings
        self.adaptive_quality = True
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
        self.max_triangles_for_full_quality = 100000

        # Initialize modules
        self._init_ui()
        self._init_modules()
        self._setup_performance_monitoring()

        # Update performance settings
        perf_profile = self.performance_monitor.get_performance_profile()
        self.max_triangles_for_full_quality = perf_profile.max_triangles_for_full_quality
        self.adaptive_quality = perf_profile.adaptive_quality_enabled

        self.logger.info("VTK-based 3D viewer widget initialized successfully")

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.ui_manager = ViewerUIManager(self)
        self.ui_manager.setup_ui(
            on_solid_clicked=lambda: self._set_render_mode(RenderMode.SOLID),
            on_material_clicked=self._open_material_picker,
            on_lighting_clicked=self._open_lighting_panel,
            on_grid_clicked=self._toggle_grid,
            on_reset_clicked=self.reset_view,
            on_save_view_clicked=self._save_view_requested,
            on_rotate_ccw_clicked=lambda: self._rotate_around_view_axis(90),
            on_rotate_cw_clicked=lambda: self._rotate_around_view_axis(-90),
            on_set_z_up_clicked=self._set_z_up,
        )

    def _init_modules(self) -> None:
        """Initialize modular components."""
        self.vtk_widget = self.ui_manager.get_vtk_widget()

        # Scene manager
        self.scene_manager = VTKSceneManager(self.vtk_widget)
        self.scene_manager.setup_scene()

        # Model renderer
        self.renderer = self.scene_manager.renderer
        self.model_renderer = ModelRenderer(self.renderer)

        # Camera controller
        self.render_window = self.scene_manager.render_window
        self.camera_controller = CameraController(self.renderer, self.render_window)

        # Expose commonly used attributes
        self.interactor = self.scene_manager.interactor
        self.grid_actor = self.scene_manager.grid_actor
        self.ground_actor = self.scene_manager.ground_actor
        self.actor = self.model_renderer.actor
        self.grid_visible = self.scene_manager.grid_visible

        # Expose for backward compatibility
        self.camera = self.renderer.GetActiveCamera()
        self.render_mode = RenderMode.SOLID

    def _setup_performance_monitoring(self) -> None:
        """Set up performance monitoring."""
        self.perf_tracker = PerformanceTracker(
            update_callback=self._on_performance_update
        )
        self.perf_tracker.start()

    def _on_performance_update(self, fps: float) -> None:
        """Handle performance update."""
        self.performance_updated.emit(fps)

    def _set_render_mode(self, mode: RenderMode) -> None:
        """Set rendering mode."""
        self.render_mode = mode
        self.model_renderer.set_render_mode(mode)
        self.render_mode_changed.emit(mode.value)
        self.scene_manager.render()

    def set_render_mode(self, name: str) -> None:
        """Public interface for setting render mode."""
        try:
            mode = RenderMode[name.upper()]
            self._set_render_mode(mode)
        except (KeyError, ValueError):
            self.logger.warning(f"Invalid render mode: {name}")

    def _toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self.scene_manager.toggle_grid()
        self.grid_visible = self.scene_manager.grid_visible
        self.scene_manager.render()

    def _rotate_around_view_axis(self, degrees: float) -> None:
        """Rotate view around axis."""
        self.camera_controller.rotate_around_view_axis(degrees)

    def load_model(self, model: Model) -> bool:
        """Load a model into the viewer."""
        try:
            self.logger.info(f"Loading model with {model.stats.triangle_count} triangles")

            # Remove existing model
            self.model_renderer.remove_model()

            # Store reference
            self.current_model = model

            # Create polydata
            if hasattr(model, "is_array_based") and model.is_array_based():
                polydata = self.model_renderer.create_vtk_polydata_from_arrays(model)
            else:
                polydata = self.model_renderer.create_vtk_polydata(model)  # type: ignore

            # Load into renderer
            self.model_renderer.load_model(polydata)
            self.actor = self.model_renderer.get_actor()

            # Fit camera
            self.camera_controller.fit_camera_to_model(
                model,
                self.actor,
                update_grid_callback=self.scene_manager.update_grid,
                update_ground_callback=self.scene_manager.create_ground_plane,
            )

            # Emit signal
            self.model_loaded.emit(model.filename if hasattr(model, "filename") else "Model")

            self.logger.info("Model loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}", exc_info=True)
            return False

    def clear_scene(self) -> None:
        """Clear the scene."""
        self.model_renderer.remove_model()
        self.current_model = None
        self.scene_manager.render()

    def reset_view(self) -> None:
        """Reset camera view."""
        if self.current_model and self.actor:
            self.camera_controller.fit_camera_to_model(
                self.current_model,
                self.actor,
                update_grid_callback=self.scene_manager.update_grid,
                update_ground_callback=self.scene_manager.create_ground_plane,
            )
        else:
            self.camera_controller.reset_view()

    def get_model_info(self) -> Optional[dict]:
        """Get current model information."""
        if not self.current_model:
            return None

        return {
            "filename": getattr(self.current_model, "filename", "Unknown"),
            "triangle_count": self.current_model.stats.triangle_count,
            "bounds": self.actor.GetBounds() if self.actor else None,
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        self.perf_tracker.cleanup()
        self.model_renderer.remove_model()
        gc.collect()
        self.logger.info("Viewer cleanup completed")

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)

    def apply_theme(self) -> None:
        """Apply theme styling."""
        self.ui_manager.apply_theme()

    def _set_z_up(self) -> None:
        """Set Z-axis pointing up by rotating the model."""
        try:
            if not self.current_model or not self.actor:
                self.logger.warning("No model loaded to set Z-up")
                return

            # Get camera's current view direction
            camera = self.renderer.GetActiveCamera()
            if not camera:
                return

            # Get camera position and focal point
            cam_pos = camera.GetPosition()
            focal_point = camera.GetFocalPoint()

            # Calculate view direction (from camera to focal point)
            view_x = focal_point[0] - cam_pos[0]
            view_y = focal_point[1] - cam_pos[1]
            view_z = focal_point[2] - cam_pos[2]

            # Normalize view direction
            view_length = (view_x**2 + view_y**2 + view_z**2) ** 0.5
            if view_length < 1e-6:
                return

            view_x /= view_length
            view_y /= view_length
            view_z /= view_length

            # Get camera's up vector
            view_up = camera.GetViewUp()

            # Calculate right vector (cross product of view_up and view direction)
            right_x = view_up[1] * view_z - view_up[2] * view_y
            right_y = view_up[2] * view_x - view_up[0] * view_z
            right_z = view_up[0] * view_y - view_up[1] * view_x

            # Normalize right vector
            right_length = (right_x**2 + right_y**2 + right_z**2) ** 0.5
            if right_length < 1e-6:
                return

            right_x /= right_length
            right_y /= right_length
            right_z /= right_length

            # Create rotation matrix to align current view_up with Z-axis (0, 0, 1)
            # We need to rotate the model so that what's currently "up" becomes Z-up

            # Calculate rotation axis and angle
            # Current up vector should become (0, 0, 1)
            target_z = (0, 0, 1)

            # Rotation axis is perpendicular to both current up and target
            axis_x = view_up[1] * target_z[2] - view_up[2] * target_z[1]
            axis_y = view_up[2] * target_z[0] - view_up[0] * target_z[2]
            axis_z = view_up[0] * target_z[1] - view_up[1] * target_z[0]

            axis_length = (axis_x**2 + axis_y**2 + axis_z**2) ** 0.5

            if axis_length < 1e-6:
                # Already aligned or opposite
                dot = view_up[0] * target_z[0] + view_up[1] * target_z[1] + view_up[2] * target_z[2]
                if dot > 0.99:
                    self.logger.info("Model is already Z-up")
                    return
                else:
                    # Opposite direction, rotate 180 degrees around right vector
                    axis_x, axis_y, axis_z = right_x, right_y, right_z
                    angle = 180.0
            else:
                # Normalize axis
                axis_x /= axis_length
                axis_y /= axis_length
                axis_z /= axis_length

                # Calculate angle
                dot = view_up[0] * target_z[0] + view_up[1] * target_z[1] + view_up[2] * target_z[2]
                dot = max(-1.0, min(1.0, dot))
                angle = math.degrees(math.acos(dot))

            # Create VTK transform
            transform = vtk.vtkTransform()
            transform.RotateWXYZ(angle, axis_x, axis_y, axis_z)

            # Apply transformation to all triangles
            rotated_triangles = []
            for triangle in self.current_model.triangles:
                # Transform normal
                normal = triangle.normal
                normal_pt = vtk.vtkPoints()
                normal_pt.InsertNextPoint(normal.x, normal.y, normal.z)
                transform.TransformPoints(normal_pt, normal_pt)
                new_normal_pt = normal_pt.GetPoint(0)

                # Transform vertices
                vertices = triangle.get_vertices()
                rotated_vertices = []
                for vertex in vertices:
                    vertex_pt = vtk.vtkPoints()
                    vertex_pt.InsertNextPoint(vertex.x, vertex.y, vertex.z)
                    transform.TransformPoints(vertex_pt, vertex_pt)
                    new_vertex_pt = vertex_pt.GetPoint(0)
                    rotated_vertices.append(Vector3D(new_vertex_pt[0], new_vertex_pt[1], new_vertex_pt[2]))

                # Create rotated triangle
                rotated_tri = Triangle(
                    normal=Vector3D(new_normal_pt[0], new_normal_pt[1], new_normal_pt[2]),
                    vertex1=rotated_vertices[0],
                    vertex2=rotated_vertices[1],
                    vertex3=rotated_vertices[2],
                    attribute_byte_count=triangle.attribute_byte_count
                )
                rotated_triangles.append(rotated_tri)

            # Update model
            self.current_model = STLModel(
                header=self.current_model.header,
                triangles=rotated_triangles,
                stats=self.current_model.stats
            )

            # Re-render the model
            self.model_renderer.remove_model()
            polydata = self.model_renderer.create_vtk_polydata(self.current_model)
            self.model_renderer.create_actor(polydata)
            self.actor = self.model_renderer.actor

            # Reset camera view
            self.reset_view()

            self.logger.info(f"Set Z-up: rotated {angle:.1f}° around axis ({axis_x:.2f}, {axis_y:.2f}, {axis_z:.2f})")

        except Exception as e:
            self.logger.error(f"Failed to set Z-up: {e}", exc_info=True)

    def _open_material_picker(self) -> None:
        """Open material picker dialog."""
        try:
            # Get current model format if available
            model_format = None
            if self.current_model and hasattr(self.current_model, 'stats'):
                model_format = self.current_model.stats.format_type

            picker = MaterialPickerWidget(model_format=model_format, parent=self)
            if picker.exec():
                selected = picker.get_selected_species()
                if selected:
                    self.material_selected.emit(selected)
        except Exception as e:
            self.logger.error(f"Failed to open material picker: {e}")

    def _open_lighting_panel(self) -> None:
        """Request lighting panel."""
        self.lighting_panel_requested.emit()

    def _save_view_requested(self) -> None:
        """Request save view."""
        self.save_view_requested.emit()

    def reset_save_view_button(self) -> None:
        """Reset save view button."""
        self.ui_manager.reset_save_view_button()

