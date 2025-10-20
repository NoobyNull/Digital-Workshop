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
from PySide6.QtWidgets import QWidget, QDialog

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
    z_up_orientation_set = Signal()  # Emitted when Z-up is set, before save

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the 3D viewer widget."""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.logger.info("Initializing refactored VTK-based 3D viewer widget")

        # State
        self.current_model = None
        self.loading_in_progress = False
        self.z_up_pending_save = False  # Track if Z-up was just set and needs saving

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

    def _reload_model_in_viewer(self) -> None:
        """Reload the current model in the viewer with updated geometry."""
        try:
            if not self.current_model:
                return

            # Remove existing model from renderer
            self.model_renderer.remove_model()

            # Create polydata from updated model geometry
            if hasattr(self.current_model, "is_array_based") and self.current_model.is_array_based():
                polydata = self.model_renderer.create_vtk_polydata_from_arrays(self.current_model)
            else:
                polydata = self.model_renderer.create_vtk_polydata(self.current_model)

            # Load polydata into renderer
            self.model_renderer.load_model(polydata)
            self.actor = self.model_renderer.get_actor()

            # Fit camera to model
            self.camera_controller.fit_camera_to_model(
                self.current_model,
                self.actor
            )

            # Render the scene
            self.scene_manager.render()
            self.logger.info("Model reloaded in viewer with updated geometry")

        except Exception as e:
            self.logger.error(f"Failed to reload model in viewer: {e}", exc_info=True)

    def _calculate_z_up_rotation_from_camera(self) -> tuple:
        """
        Calculate Z-up rotation based on current camera ViewUp vector.

        Reads the UCS icon orientation (camera ViewUp) to determine which axis
        is currently pointing up, then calculates the rotation needed to make Z point up.

        Handles all 24 possible orientations (6 faces × 4 rotations each).

        Returns:
            Tuple of (axis_str, degrees) to rotate model to Z-up
        """
        try:
            camera = self.renderer.GetActiveCamera()
            if not camera:
                return ("Z", 0)

            # Get current ViewUp vector (shows which axis is pointing up)
            view_up = camera.GetViewUp()
            self.logger.info(f"Current camera ViewUp: ({view_up[0]:.2f}, {view_up[1]:.2f}, {view_up[2]:.2f})")

            # Check which axis is most dominant in ViewUp
            abs_x = abs(view_up[0])
            abs_y = abs(view_up[1])
            abs_z = abs(view_up[2])

            # Threshold for considering an axis dominant
            threshold = 0.9

            # Z-axis cases (already pointing up/down)
            if abs_z > threshold:
                if view_up[2] > 0:
                    self.logger.info("Z-axis pointing up (0°), no rotation needed")
                    return ("Z", 0)
                else:
                    self.logger.info("Z-axis pointing down (180°), rotating 180° around X")
                    return ("X", 180)

            # Y-axis cases (Y is dominant)
            if abs_y > threshold and abs_y > abs_x and abs_y > abs_z:
                if view_up[1] > 0:
                    self.logger.info("Y-axis pointing up (90°), rotating 90° around X")
                    return ("X", 90)
                else:
                    self.logger.info("Y-axis pointing down (270°), rotating 270° around X")
                    return ("X", 270)

            # X-axis cases (X is dominant)
            if abs_x > threshold and abs_x > abs_y and abs_x > abs_z:
                if view_up[0] > 0:
                    self.logger.info("X-axis pointing up (90°), rotating 90° around Y")
                    return ("Y", 90)
                else:
                    self.logger.info("X-axis pointing down (270°), rotating 270° around Y")
                    return ("Y", 270)

            # Default: no rotation
            self.logger.info("No dominant axis detected, no rotation needed")
            return ("Z", 0)

        except Exception as e:
            self.logger.error(f"Failed to calculate Z-up rotation from camera: {e}", exc_info=True)
            return ("Z", 0)

    def _set_z_up(self) -> None:
        """Set Z-axis pointing up by rotating model based on UCS icon orientation."""
        try:
            if not self.current_model or not self.actor:
                self.logger.warning("No model loaded to set Z-up")
                return

            from src.gui.model_editor.model_editor_core import ModelEditor, RotationAxis

            # Calculate rotation needed based on camera's current ViewUp (UCS icon)
            axis_str, degrees = self._calculate_z_up_rotation_from_camera()

            self.logger.info(f"Z-up rotation needed: {degrees}° around {axis_str} axis")

            if degrees == 0:
                self.logger.info("Model is already Z-up oriented")
                self.z_up_pending_save = True
                return

            # Apply rotation to model geometry
            try:
                # Create a temporary STLModel from current Model for rotation
                stl_model = STLModel(
                    header=getattr(self.current_model, 'header', 'Model'),
                    triangles=self.current_model.triangles,
                    stats=self.current_model.stats
                )

                editor = ModelEditor(stl_model)
                axis = RotationAxis[axis_str]
                rotated_stl = editor.rotate_model(axis, degrees)
                self.logger.info(f"Rotated model {degrees}° around {axis_str} for Z-up")

                # Update the Model object's triangles with rotated geometry
                self.current_model.triangles = rotated_stl.triangles

            except Exception as e:
                self.logger.error(f"Failed to rotate model: {e}", exc_info=True)
                return

            # Re-render the model with new geometry
            self._reload_model_in_viewer()

            # Mark that Z-up is pending save
            self.z_up_pending_save = True

            self.logger.info(f"Set Z-up: Model rotated {degrees}° around {axis_str} axis (pending save)")

            # Emit signal to notify UI that Z-up was set
            self.z_up_orientation_set.emit()

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
        # If Z-up is pending, show special dialog
        if self.z_up_pending_save:
            self._handle_z_up_save()
        else:
            self.save_view_requested.emit()

    def _handle_z_up_save(self) -> None:
        """Handle Z-up save workflow with dialog."""
        try:
            from .z_up_save_dialog import ZUpSaveDialog
            from src.gui.model_editor.stl_writer import STLWriter
            from src.gui.model_editor.model_editor_core import ModelEditor, RotationAxis

            if not self.current_model:
                self.logger.warning("No model loaded for Z-up save")
                return

            # Get model filename
            model_filename = getattr(self.current_model, 'header', 'model.stl')

            # Show dialog
            dialog = ZUpSaveDialog(model_filename, self.ui_manager.viewer_widget if hasattr(self.ui_manager, 'viewer_widget') else None)
            if dialog.exec() != QDialog.Accepted:
                return

            option = dialog.get_selected_option()

            if option == ZUpSaveDialog.SAVE_VIEW_ONLY:
                # Just save camera view
                self.save_view_requested.emit()
                self.z_up_pending_save = False

            elif option == ZUpSaveDialog.SAVE_AND_REPLACE:
                # Rotate model and save to original file
                self._rotate_and_save_model(model_filename, replace_original=True)
                self.z_up_pending_save = False

            elif option == ZUpSaveDialog.SAVE_AS_NEW:
                # Rotate model and save as new file
                new_path = dialog.get_new_filepath()
                self._rotate_and_save_model(new_path, replace_original=False)
                self.z_up_pending_save = False

        except Exception as e:
            self.logger.error(f"Failed to handle Z-up save: {e}", exc_info=True)

    def _rotate_and_save_model(self, output_path: str, replace_original: bool = False) -> None:
        """
        Rotate model to Z-up and save to file.

        Args:
            output_path: Path to save the model
            replace_original: If True, replaces original file
        """
        try:
            from src.gui.model_editor.model_editor_core import ModelEditor, RotationAxis
            from src.gui.model_editor.stl_writer import STLWriter
            from PySide6.QtWidgets import QMessageBox

            if not self.current_model:
                return

            # Create editor and detect Z-up rotation needed
            editor = ModelEditor(self.current_model)
            axis_str, degrees = editor.analyzer.get_z_up_recommendation()

            if degrees != 0:
                # Apply rotation
                axis = RotationAxis[axis_str]
                rotated_model = editor.rotate_model(axis, degrees)
                self.logger.info(f"Rotated model {degrees}° around {axis_str} for Z-up")
            else:
                rotated_model = self.current_model
                self.logger.info("Model already Z-up, no rotation needed")

            # Save model
            success = STLWriter.write(rotated_model, output_path, binary=True)

            if success:
                self.logger.info(f"Saved Z-up model to {output_path}")
                if replace_original:
                    QMessageBox.information(
                        None,
                        "Success",
                        f"Model rotated to Z-up and saved:\n{output_path}"
                    )
                else:
                    QMessageBox.information(
                        None,
                        "Success",
                        f"Model rotated to Z-up and saved as:\n{output_path}"
                    )
            else:
                QMessageBox.critical(None, "Error", f"Failed to save model to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to rotate and save model: {e}", exc_info=True)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Error", f"Failed to save model: {str(e)}")

    def reset_save_view_button(self) -> None:
        """Reset save view button."""
        self.ui_manager.reset_save_view_button()

