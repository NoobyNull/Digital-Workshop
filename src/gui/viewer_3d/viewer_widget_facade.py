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

from src.core.logging_config import get_logger, get_activity_logger, log_function_call
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.stl_parser import STLModel
from src.core.data_structures import Model, LoadingState, Triangle, Vector3D
from src.gui.theme import vtk_rgb
from src.gui.material_picker_widget import MaterialPickerWidget
from src.gui.components.detailed_progress_tracker import DetailedProgressTracker, LoadingStage

from .vtk_scene_manager import VTKSceneManager
from .model_renderer import ModelRenderer, RenderMode
from .camera_controller import CameraController
from .performance_tracker import PerformanceTracker
from .viewer_ui_manager import ViewerUIManager

# Import VTK error handling system
from src.gui.vtk import (
    get_vtk_error_handler,
    get_vtk_context_manager,
    get_vtk_cleanup_coordinator,
    get_vtk_resource_tracker,
    get_vtk_fallback_renderer,
    register_vtk_resource,
    ResourceType
)


logger = get_logger(__name__)
activity_logger = get_activity_logger(__name__)


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

        # Connect internal signals
        self.material_selected.connect(self._on_material_selected)

        # Update performance settings based on system info
        perf_report = self.performance_monitor.get_performance_report()
        system_info = perf_report.get('system_info', {})
        total_memory_gb = system_info.get('memory_total_gb', 8.0)
        
        # Set triangle limits based on available memory
        if total_memory_gb >= 16.0:
            self.max_triangles_for_full_quality = 200000
            self.adaptive_quality = False
        elif total_memory_gb >= 8.0:
            self.max_triangles_for_full_quality = 100000
            self.adaptive_quality = True
        else:
            self.max_triangles_for_full_quality = 50000
            self.adaptive_quality = True

        self.logger.info("VTK-based 3D viewer widget initialized successfully")

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.ui_manager = ViewerUIManager(self)
        self.ui_manager.setup_ui(
            on_solid_clicked=lambda: self._set_render_mode(RenderMode.SOLID),
            on_material_clicked=self._open_material_picker,
            on_lighting_clicked=self._open_lighting_panel,
            on_reset_clicked=self.reset_view,
            on_save_view_clicked=self._save_view_requested,
            on_rotate_ccw_clicked=lambda: self._rotate_around_view_axis(90),
            on_rotate_cw_clicked=lambda: self._rotate_around_view_axis(-90),
            on_set_z_up_clicked=self._set_z_up,
            on_rotate_x_pos=self.rotate_x_positive,
            on_rotate_x_neg=self.rotate_x_negative,
            on_rotate_y_pos=self.rotate_y_positive,
            on_rotate_y_neg=self.rotate_y_negative,
            on_rotate_z_pos=self.rotate_z_positive,
            on_rotate_z_neg=self.rotate_z_negative,
        )

    def _init_modules(self) -> None:
        """Initialize modular components."""
        self.vtk_widget = self.ui_manager.get_vtk_widget()

        # Initialize VTK error handling system
        self.error_handler = get_vtk_error_handler()
        self.context_manager = get_vtk_context_manager()
        self.cleanup_coordinator = get_vtk_cleanup_coordinator()
        self.resource_tracker = get_vtk_resource_tracker()
        self.fallback_renderer = get_vtk_fallback_renderer()

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

        # Register VTK resources for tracking (after all attributes are set)
        self._register_vtk_resources()

        self.logger.info("VTK error handling system integrated successfully")

    def _register_vtk_resources(self) -> None:
        """Register VTK resources for proper cleanup tracking."""
        try:
            # Register main VTK components
            if self.render_window:
                self.resource_tracker.register_resource(
                    self.render_window,
                    ResourceType.RENDER_WINDOW,
                    "main_render_window"
                )

            if self.renderer:
                self.resource_tracker.register_resource(
                    self.renderer,
                    ResourceType.RENDERER,
                    "main_renderer"
                )

            if self.interactor:
                self.resource_tracker.register_resource(
                    self.interactor,
                    ResourceType.INTERACTOR,
                    "main_interactor"
                )

            # Register actors
            if self.grid_actor:
                self.resource_tracker.register_resource(
                    self.grid_actor,
                    ResourceType.ACTOR,
                    "grid_actor"
                )

            if self.ground_actor:
                self.resource_tracker.register_resource(
                    self.ground_actor,
                    ResourceType.ACTOR,
                    "ground_actor"
                )

            # Register camera
            if self.camera:
                self.resource_tracker.register_resource(
                    self.camera,
                    ResourceType.CAMERA,
                    "main_camera"
                )

            self.logger.debug("VTK resources registered for tracking")

        except Exception as e:
            self.logger.warning(f"Error registering VTK resources: {e}")

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
        """Set rendering mode with enhanced error handling."""
        try:
            self.render_mode = mode
            self.model_renderer.set_render_mode(mode)
            self.render_mode_changed.emit(mode.value)

            # Use fallback renderer for safe rendering
            if self.render_window:
                success = self.fallback_renderer.render_with_fallback(self.render_window)
                if not success:
                    self.logger.warning(f"Render failed for mode {mode.value}, continuing anyway")
            else:
                self.scene_manager.render()

        except Exception as e:
            self.logger.error(f"Error setting render mode {mode.value}: {e}")
            # Continue with fallback rendering
            if self.render_window:
                self.fallback_renderer.render_with_fallback(self.render_window)

    def set_render_mode(self, name: str) -> None:
        """Public interface for setting render mode."""
        try:
            mode = RenderMode[name.upper()]
            self._set_render_mode(mode)
        except (KeyError, ValueError):
            self.logger.warning(f"Invalid render mode: {name}")

    # Grid and ground plane toggle methods removed - these are now controlled via preferences dialog only
    # The VTK scene manager still maintains grid_visible and ground_visible state loaded from QSettings

    def _rotate_around_view_axis(self, degrees: float) -> None:
        """Rotate view around axis."""
        self.camera_controller.rotate_around_view_axis(degrees)

    def load_model(self, model: Model, progress_callback=None) -> bool:
        """
        Load a model into the viewer with optional progress tracking.

        Args:
            model: The model to load
            progress_callback: Optional callback for progress updates (progress_pct, message)
        """
        try:
            self.logger.info(f"Loading model with {model.stats.triangle_count} triangles")

            # Create progress tracker
            tracker = DetailedProgressTracker(
                triangle_count=model.stats.triangle_count,
                file_size_mb=model.stats.file_size_bytes / (1024 * 1024) if model.stats.file_size_bytes else 0
            )

            # Set up progress callback
            def emit_progress(progress: float, message: str) -> None:
                if progress_callback:
                    progress_callback(progress, message)

            tracker.set_progress_callback(emit_progress)

            # Remove existing model
            tracker.start_stage(LoadingStage.RENDERING, "Removing existing model...")
            self.model_renderer.remove_model()

            # Store reference
            self.current_model = model

            # Create polydata with progress tracking
            tracker.start_stage(LoadingStage.RENDERING, "Creating VTK polydata...")
            self.model_renderer.set_progress_callback(emit_progress)

            if hasattr(model, "is_array_based") and model.is_array_based():
                polydata = self.model_renderer.create_vtk_polydata_from_arrays(model)
            else:
                polydata = self.model_renderer.create_vtk_polydata(model)  # type: ignore

            # Load into renderer
            tracker.update_stage_progress(50, 100, "Loading into renderer...")
            self.model_renderer.load_model(polydata)
            self.actor = self.model_renderer.get_actor()

            # Fit camera
            tracker.update_stage_progress(75, 100, "Fitting camera...")
            self.camera_controller.fit_camera_to_model(
                model,
                self.actor,
                update_grid_callback=self.scene_manager.update_grid,
                update_ground_callback=self.scene_manager.create_ground_plane,
            )

            # Complete
            tracker.complete_stage("Model loaded successfully")

            # Emit signal
            self.model_loaded.emit(model.filename if hasattr(model, "filename") else "Model")

            activity_logger.info("Model loaded successfully")
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
        """Clean up resources using enhanced VTK error handling."""
        try:
            self.logger.info("Starting enhanced VTK cleanup")

            # Use the cleanup coordinator for proper VTK cleanup sequence
            cleanup_success = self.cleanup_coordinator.coordinate_cleanup(
                render_window=self.render_window,
                renderer=self.renderer,
                interactor=self.interactor
            )

            if cleanup_success:
                self.logger.info("VTK cleanup completed successfully")
            else:
                self.logger.info("VTK cleanup completed with context loss (normal during shutdown)")

            # Clean up model renderer
            try:
                self.model_renderer.remove_model()
                self.logger.debug("Model renderer cleaned up")
            except Exception as e:
                self.logger.warning(f"Error removing model: {e}")

            # Clean up performance tracker
            try:
                self.perf_tracker.cleanup()
                self.logger.debug("Performance tracker cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up performance tracker: {e}")

            # Clean up fallback renderer
            try:
                if self.fallback_renderer.is_fallback_active():
                    self.fallback_renderer.deactivate_fallback()
                    self.logger.debug("Fallback renderer deactivated")
            except Exception as e:
                self.logger.warning(f"Error deactivating fallback renderer: {e}")

            # Clear resource tracking
            try:
                cleanup_stats = self.resource_tracker.cleanup_all_resources()
                self.logger.info(f"Resource cleanup stats: {cleanup_stats}")
            except Exception as e:
                self.logger.warning(f"Error during resource cleanup: {e}")

            # Force garbage collection
            gc.collect()

            self.logger.info("Enhanced viewer cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during enhanced cleanup: {e}")
            # Fallback to basic cleanup if enhanced cleanup fails
            self._basic_cleanup()

    def _basic_cleanup(self) -> None:
        """Basic cleanup fallback if enhanced cleanup fails."""
        try:
            self.logger.info("Performing basic cleanup fallback")

            # Basic VTK cleanup
            try:
                if hasattr(self, 'scene_manager') and self.scene_manager:
                    self.scene_manager.cleanup()
            except Exception as e:
                self.logger.debug(f"Basic scene manager cleanup error: {e}")

            # Force garbage collection
            gc.collect()

            self.logger.info("Basic cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during basic cleanup: {e}")

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

    def _calculate_z_up_rotation_from_model_bounds(self) -> tuple:
        """
        Calculate Z-up rotation based on model's bounding box dimensions.

        Analyzes which dimension (X, Y, Z) is tallest in the model's world-space bounds,
        then calculates the rotation needed to make Z the tallest dimension (Z-up).

        This is the correct approach for determining model orientation in world space,
        as opposed to camera-relative orientation.

        Returns:
            Tuple of (axis_str, degrees) to rotate model to Z-up
        """
        try:
            if not self.actor:
                return ("Z", 0)

            # Get model bounds in world space
            bounds = self.actor.GetBounds()
            xmin, xmax, ymin, ymax, zmin, zmax = bounds

            # Calculate dimensions
            dx = abs(xmax - xmin)
            dy = abs(ymax - ymin)
            dz = abs(zmax - zmin)

            self.logger.info(f"Model dimensions - X: {dx:.2f}, Y: {dy:.2f}, Z: {dz:.2f}")

            # Threshold for considering dimensions equal (avoid rotation for nearly-cubic models)
            equal_threshold = 0.1  # 10% difference
            max_dim = max(dx, dy, dz)

            # Check if all dimensions are roughly equal (cube-like)
            if (abs(dx - max_dim) / max_dim < equal_threshold and
                abs(dy - max_dim) / max_dim < equal_threshold and
                abs(dz - max_dim) / max_dim < equal_threshold):
                self.logger.info("Model is roughly cubic, assuming already Z-up")
                return ("Z", 0)

            # Determine which dimension is tallest and calculate required rotation
            if dz >= dy and dz >= dx:
                # Z is already the tallest dimension
                self.logger.info("Z is tallest dimension, already Z-up")
                return ("Z", 0)
            elif dy > dx and dy > dz:
                # Y is tallest, need to rotate 90° around X to make Z tallest
                self.logger.info("Y is tallest dimension, rotating 90° around X to make Z-up")
                return ("X", 90)
            elif dx > dy and dx > dz:
                # X is tallest, need to rotate -90° around Y to make Z tallest
                self.logger.info("X is tallest dimension, rotating -90° around Y to make Z-up")
                return ("Y", -90)
            else:
                # Fallback
                self.logger.info("Unable to determine tallest dimension, no rotation")
                return ("Z", 0)

        except Exception as e:
            self.logger.error(f"Failed to calculate Z-up rotation from model bounds: {e}", exc_info=True)
            return ("Z", 0)

    def _set_z_up(self) -> None:
        """Set Z-axis pointing up by rotating model geometry based on bounds analysis."""
        try:
            if not self.current_model or not self.actor:
                self.logger.warning("No model loaded to set Z-up")
                return

            from src.gui.model_editor.model_editor_core import ModelEditor, RotationAxis

            # Calculate rotation needed based on model's bounding box dimensions
            axis_str, degrees = self._calculate_z_up_rotation_from_model_bounds()

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

    def rotate_model_geometry(self, axis: str, degrees: float) -> None:
        """
        Rotate model geometry around world-space axis.
        
        This modifies the actual triangle coordinates, not just the visual representation.
        Camera stays fixed while model rotates in world space.
        
        Args:
            axis: Rotation axis - "X", "Y", or "Z"
            degrees: Rotation angle in degrees (positive = counterclockwise when looking along axis)
        """
        try:
            if not self.current_model or not self.actor:
                self.logger.warning("No model loaded to rotate")
                return

            from src.gui.model_editor.model_editor_core import ModelEditor, RotationAxis

            # Create STLModel from current Model for rotation
            from src.parsers.stl_parser import STLModel
            stl_model = STLModel(
                header=getattr(self.current_model, 'header', 'Model'),
                triangles=self.current_model.triangles,
                stats=self.current_model.stats
            )

            # Apply rotation using ModelEditor
            editor = ModelEditor(stl_model)
            try:
                axis_enum = RotationAxis[axis.upper()]
            except KeyError:
                self.logger.error(f"Invalid rotation axis: {axis}")
                return

            rotated_model = editor.rotate_model(axis_enum, degrees)
            self.logger.info(f"Rotated model {degrees}° around {axis} axis")

            # Update current model's triangles with rotated geometry
            self.current_model.triangles = rotated_model.triangles

            # Reload the model in the viewer with new geometry
            self._reload_model_in_viewer()

            self.logger.info(f"Model geometry rotated {degrees}° around {axis} axis")

        except Exception as e:
            self.logger.error(f"Failed to rotate model geometry: {e}", exc_info=True)

    def rotate_x_positive(self) -> None:
        """Rotate model +90° around X axis."""
        self.rotate_model_geometry("X", 90)

    def rotate_x_negative(self) -> None:
        """Rotate model -90° around X axis."""
        self.rotate_model_geometry("X", -90)

    def rotate_y_positive(self) -> None:
        """Rotate model +90° around Y axis."""
        self.rotate_model_geometry("Y", 90)

    def rotate_y_negative(self) -> None:
        """Rotate model -90° around Y axis."""
        self.rotate_model_geometry("Y", -90)

    def rotate_z_positive(self) -> None:
        """Rotate model +90° around Z axis."""
        self.rotate_model_geometry("Z", 90)

    def rotate_z_negative(self) -> None:
        """Rotate model -90° around Z axis."""
        self.rotate_model_geometry("Z", -90)

    def apply_material_to_current_model(self, material_name: str, material_manager=None) -> bool:
        """
        Apply material to the currently loaded model.
        
        Args:
            material_name: Name of the material to apply
            material_manager: MaterialManager instance (optional, will be found if not provided)
            
        Returns:
            True if material was applied successfully
        """
        try:
            if not self.actor:
                self.logger.warning("No model loaded to apply material to")
                return False
                
            # Get material manager if not provided
            if material_manager is None:
                material_manager = self._get_material_manager()
                if not material_manager:
                    self.logger.warning("Material manager not available")
                    return False
                    
            # Apply material using the model renderer
            success = self.model_renderer.apply_material(material_name, material_manager)
            
            if success:
                self.logger.info(f"Applied material '{material_name}' to current model")
                # Force a render update
                self.scene_manager.render()
            else:
                self.logger.warning(f"Failed to apply material '{material_name}'")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying material '{material_name}': {e}", exc_info=True)
            return False

    def apply_default_material_to_current_model(self, material_manager=None) -> bool:
        """
        Apply the default material from preferences to the current model.
        
        Args:
            material_manager: MaterialManager instance (optional, will be found if not provided)
            
        Returns:
            True if default material was applied successfully
        """
        try:
            # Get material manager if not provided
            if material_manager is None:
                material_manager = self._get_material_manager()
                if not material_manager:
                    self.logger.warning("Material manager not available for default material")
                    return False
                    
            # Apply default material using the model renderer
            success = self.model_renderer.apply_default_material(material_manager)
            
            if success:
                self.logger.info("Applied default material to current model")
                # Force a render update
                self.scene_manager.render()
            else:
                self.logger.warning("Failed to apply default material")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying default material: {e}", exc_info=True)
            return False

    def _get_material_manager(self):
        """
        Get the material manager from the main window or application.

        Returns:
            MaterialManager instance or None if not found
        """
        try:
            parent = self.parent()

            # Try to get from parent window (main window) - check multiple times
            if parent and hasattr(parent, 'material_manager'):
                mm = getattr(parent, 'material_manager', None)
                if mm is not None:
                    self.logger.debug("Found material manager on parent window")
                    return mm

            # Try to get from application
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app and hasattr(app, 'material_manager'):
                mm = getattr(app, 'material_manager', None)
                if mm is not None:
                    self.logger.debug("Found material manager on application")
                    return mm

            # Try to get from central widget manager
            if parent and hasattr(parent, 'central_widget_manager'):
                cwm = getattr(parent, 'central_widget_manager', None)
                if cwm and hasattr(cwm, 'material_manager'):
                    mm = getattr(cwm, 'material_manager', None)
                    if mm is not None:
                        self.logger.debug("Found material manager on central widget manager")
                        return mm

            # If still not found, try to create one as a fallback
            try:
                from src.core.database_manager import get_database_manager
                from src.gui.material_manager import MaterialManager
                self.logger.warning("Material manager not found, creating fallback instance")
                return MaterialManager(get_database_manager())
            except Exception as fallback_error:
                self.logger.debug(f"Could not create fallback material manager: {fallback_error}")

            self.logger.debug("Material manager not found in any location")
            return None

        except Exception as e:
            self.logger.error(f"Error getting material manager: {e}", exc_info=True)
            return None

    def _on_material_selected(self, material_name: str) -> None:
        """
        Handle material selection from the material picker.
        
        Args:
            material_name: Name of the selected material
        """
        try:
            self.logger.info(f"Material selected: {material_name}")
            success = self.apply_material_to_current_model(material_name)
            
            if success:
                # Save the material selection as the last used
                from PySide6.QtCore import QSettings
                settings = QSettings()
                settings.setValue('material/last_species', material_name)
                self.logger.info(f"Saved material selection: {material_name}")
            else:
                self.logger.warning(f"Failed to apply selected material: {material_name}")
                
        except Exception as e:
            self.logger.error(f"Error handling material selection: {e}", exc_info=True)

