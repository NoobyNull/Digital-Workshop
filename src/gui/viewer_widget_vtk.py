"""
VTK-based 3D viewer widget for 3D-MM application.

This module provides a 3D visualization widget using VTK with PySide6 integration,
offering interactive model viewing with camera controls and configurable rendering.
"""

import gc
import time
from enum import Enum
from typing import Optional, Tuple, Any

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel
from PySide6.QtGui import QColor

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from core.logging_config import get_logger, log_function_call
from core.performance_monitor import get_performance_monitor
from core.model_cache import get_model_cache, CacheLevel
from parsers.stl_parser import STLModel
from core.data_structures import Model, LoadingState, Vector3D, Triangle
from gui.theme import COLORS, vtk_rgb


class RenderMode(Enum):
    """Rendering modes for the 3D viewer."""
    SOLID = "solid"
    WIREFRAME = "wireframe"
    POINTS = "points"


class Viewer3DWidget(QWidget):
    """
    3D viewer widget using VTK for interactive model visualization.
    
    Features:
    - Interactive camera controls (orbit, pan, zoom)
    - Configurable rendering with multiple display modes
    - Multiple rendering modes (solid, wireframe, points)
    - Performance optimization for large models
    - Memory-efficient rendering with resource cleanup
    - Progressive loading with quality levels
    - Integration with STL parser for model loading
    """
    
    # Signals for UI integration
    model_loaded = Signal(str)  # Emitted when a model is loaded
    render_mode_changed = Signal(str)  # Emitted when render mode changes
    performance_updated = Signal(float)  # Emitted with FPS updates
    loading_progress_updated = Signal(float, str)  # Emitted with loading progress
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the 3D viewer widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing VTK-based 3D viewer widget")
        
        # Viewer state
        self.current_model = None
        self.render_mode = RenderMode.SOLID
        self.actor = None
        self.performance_timer = QTimer(self)
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # Performance settings
        self.adaptive_quality = True
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
        self.max_triangles_for_full_quality = 100000
        
        # Progressive loading
        self.loading_in_progress = False
        
        # Initialize UI
        self._init_ui()
        self._setup_vtk_scene()
        self._setup_performance_monitoring()
        
        # Update performance settings from profile
        perf_profile = self.performance_monitor.get_performance_profile()
        self.max_triangles_for_full_quality = perf_profile.max_triangles_for_full_quality
        self.adaptive_quality = perf_profile.adaptive_quality_enabled
        
        self.logger.info("VTK-based 3D viewer widget initialized successfully")
    
    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)
        
        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # Render mode buttons
        self.solid_button = QPushButton("Solid")
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)
        self.solid_button.clicked.connect(lambda: self._set_render_mode(RenderMode.SOLID))
        
        self.wireframe_button = QPushButton("Wireframe")
        self.wireframe_button.setCheckable(True)
        self.wireframe_button.clicked.connect(lambda: self._set_render_mode(RenderMode.WIREFRAME))
        
        # Points mode intentionally removed per requirements (keep backend support if needed)
        control_layout.addWidget(self.solid_button)
        control_layout.addWidget(self.wireframe_button)
        control_layout.addStretch()
        
        # Reset view button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        control_layout.addWidget(self.reset_button)
        
        layout.addWidget(control_panel)
        
        # Create progress bar for loading
        self.progress_frame = QWidget()
        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(5, 5, 5, 5)
        
        self.progress_label = QLabel("Loading...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch()
        
        layout.addWidget(self.progress_frame)
        self.progress_frame.setVisible(False)
        
        # Style the widget using theme variables
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 6px 12px;
                border: 1px solid {COLORS.border};
                background-color: {COLORS.surface};
                color: {COLORS.text};
                border-radius: 2px;
                font-weight: normal;
            }}
            QPushButton:checked {{
                background-color: {COLORS.primary};
                color: {COLORS.primary_text};
                border: 1px solid {COLORS.primary};
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
            QProgressBar {{
                border: 1px solid {COLORS.border};
                border-radius: 2px;
                text-align: center;
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS.progress_chunk};
                border-radius: 1px;
            }}
            QLabel {{
                color: {COLORS.text};
                background-color: transparent;
            }}
        """)
    
    def _setup_vtk_scene(self) -> None:
        """Set up the VTK scene with renderer and interactor."""
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(*vtk_rgb('canvas_bg'))  # Theme canvas background

        # Configure VTK multi-threading to use available CPU cores
        try:
            import multiprocessing as _mp  # local import to avoid global overhead
            threads = max(2, (_mp.cpu_count() or 2))
            # Set thread count for legacy threader
            vtk.vtkMultiThreader.SetGlobalDefaultNumberOfThreads(threads)
            # If SMPTools exists (newer VTK), set number of threads too
            if hasattr(vtk, "vtkSMPTools"):
                try:
                    vtk.vtkSMPTools.SetNumberOfThreads(threads)
                except Exception:
                    pass
            self.logger.info(f"VTK thread count set to {threads}")
        except Exception:
            # Non-fatal if this fails; VTK will use its defaults
            pass
        
        # Add better lighting for improved visibility
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
        
        # Create render window
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Create interactor
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        # Use position-based, trackball-style camera interaction (prevents speed acceleration)
        try:
            style = vtk.vtkInteractorStyleTrackballCamera()
            style.SetMotionFactor(8.0)  # sensitivity
            self.interactor.SetInteractorStyle(style)
            try:
                # Tune interactor update rates for more responsive interaction
                self.interactor.SetDesiredUpdateRate(60.0)
                self.interactor.SetStillUpdateRate(10.0)
            except Exception:
                pass
            self.logger.debug("VTK interactor style set to TrackballCamera with MotionFactor=3.0")
        except Exception:
            pass
        
        # Add default axes actor with better visibility
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetOrientationMarker(axes)
        self.marker.SetInteractor(self.interactor)
        self.marker.SetEnabled(1)
        self.marker.InteractiveOn()
        self.marker.SetViewport(0.0, 0.0, 0.2, 0.2)  # Position in bottom-left corner
        
        # Set up default camera
        self.renderer.ResetCamera()
        
        # Start interactor
        self.interactor.Initialize()
        
        self.logger.debug("VTK scene setup completed")
    
    def _setup_performance_monitoring(self) -> None:
        """Set up performance monitoring for FPS tracking."""
        self.performance_timer.timeout.connect(self._update_performance)
        self.performance_timer.start(1000)  # Update every second
    
    def _update_performance(self) -> None:
        """Update performance metrics and emit signals."""
        current_time = time.time()
        time_delta = current_time - self.last_fps_time
        
        if time_delta > 0:
            self.current_fps = self.frame_count / time_delta
            self.performance_updated.emit(self.current_fps)
        
        # Reset counters
        self.frame_count = 0
        self.last_fps_time = current_time
    
    def _create_vtk_polydata(self, model: STLModel) -> vtk.vtkPolyData:
        """
        Create VTK polydata from STL model.
        
        Args:
            model: The STL model to convert
            
        Returns:
            vtk.vtkPolyData with the model geometry
        """
        self.logger.info(f"Creating VTK polydata for {len(model.triangles)} triangles")
        
        # Create points
        points = vtk.vtkPoints()
        
        # Create triangles
        triangles = vtk.vtkCellArray()
        
        # Create normals
        normals = vtk.vtkFloatArray()
        normals.SetNumberOfComponents(3)
        normals.SetName("Normals")
        
        # Process each triangle
        for i, triangle in enumerate(model.triangles):
            # Add vertices
            point_id1 = points.InsertNextPoint(triangle.vertex1.x, triangle.vertex1.y, triangle.vertex1.z)
            point_id2 = points.InsertNextPoint(triangle.vertex2.x, triangle.vertex2.y, triangle.vertex2.z)
            point_id3 = points.InsertNextPoint(triangle.vertex3.x, triangle.vertex3.y, triangle.vertex3.z)
            
            # Add triangle
            triangle_cell = vtk.vtkTriangle()
            triangle_cell.GetPointIds().SetId(0, point_id1)
            triangle_cell.GetPointIds().SetId(1, point_id2)
            triangle_cell.GetPointIds().SetId(2, point_id3)
            triangles.InsertNextCell(triangle_cell)
            
            # Add normals (one for each vertex)
            normal = [triangle.normal.x, triangle.normal.y, triangle.normal.z]
            normals.InsertNextTuple(normal)
            normals.InsertNextTuple(normal)
            normals.InsertNextTuple(normal)
        
        # Create polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(triangles)
        polydata.GetPointData().SetNormals(normals)
        
        return polydata
    
    def _set_render_mode(self, mode: RenderMode) -> None:
        """
        Set the rendering mode for the 3D view.
        
        Args:
            mode: The render mode to set
        """
        if self.render_mode == mode:
            return
        
        self.render_mode = mode
        self.render_mode_changed.emit(mode.value)
        
        # Update button states
        self.solid_button.setChecked(mode == RenderMode.SOLID)
        self.wireframe_button.setChecked(mode == RenderMode.WIREFRAME)
        # Points button removed from UI
        
        # Apply rendering mode if model is loaded
        if self.actor:
            self._apply_render_mode()
        
        self.logger.info(f"Render mode changed to: {mode.value}")
    
    def set_render_mode(self, name: str) -> None:
        """Public API to change render mode by name: 'solid', 'wireframe', 'points'."""
        try:
            mapping = {
                "solid": RenderMode.SOLID,
                "wireframe": RenderMode.WIREFRAME,
                "points": RenderMode.POINTS,
            }
            mode = mapping.get(str(name).lower().strip())
            if mode:
                self._set_render_mode(mode)
        except Exception:
            pass

    def _apply_render_mode(self) -> None:
        """Apply the current render mode to the model."""
        if not self.actor:
            return

        if self.render_mode == RenderMode.WIREFRAME:
            self.actor.GetProperty().SetRepresentationToWireframe()
            self.actor.GetProperty().SetLineWidth(1.0)
            self.actor.GetProperty().SetEdgeVisibility(0)  # Disable edges in wireframe mode
        elif self.render_mode == RenderMode.POINTS:
            self.actor.GetProperty().SetRepresentationToPoints()
            self.actor.GetProperty().SetPointSize(3.0)
            self.actor.GetProperty().SetEdgeVisibility(0)  # Disable edges in points mode
        else:  # SOLID
            self.actor.GetProperty().SetRepresentationToSurface()
            self.actor.GetProperty().SetEdgeVisibility(0)  # Disable edges in solid mode

        # Update the view
        self.vtk_widget.GetRenderWindow().Render()

        # Log the render mode change for debugging
        self.logger.debug(f"Applied render mode: {self.render_mode.value}, EdgeVisibility: {self.actor.GetProperty().GetEdgeVisibility()}")
    
    def _remove_current_model(self) -> None:
        """Remove the currently loaded model from the scene."""
        if self.actor:
            self.renderer.RemoveActor(self.actor)
            self.actor = None
        
        # Clear reference to current model
        self.current_model = None
        
        # Force garbage collection
        gc.collect()
    
    def _fit_camera_to_model(self, model: STLModel) -> None:
        """
        Adjust camera position to fit the model in view with a natural rotation feel.
        Uses model bounds to center focal point and set a reasonable camera distance.
        """
        try:
            if not model or not hasattr(self, "actor") or self.actor is None:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.vtk_widget.GetRenderWindow().Render()
                self.logger.debug("Camera reset (no actor); clipping range updated")
                return

            # Compute bounds and center
            bounds = self.actor.GetBounds()  # (xmin,xmax,ymin,ymax,zmin,zmax)
            if not bounds:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.vtk_widget.GetRenderWindow().Render()
                self.logger.debug("Camera reset (no bounds); clipping range updated")
                return

            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            cx = (xmin + xmax) * 0.5
            cy = (ymin + ymax) * 0.5
            cz = (zmin + zmax) * 0.5

            # Diagonal/2 as radius heuristic
            dx = max(1e-6, xmax - xmin)
            dy = max(1e-6, ymax - ymin)
            dz = max(1e-6, zmax - zmin)
            diag = (dx * dx + dy * dy + dz * dz) ** 0.5
            radius = max(1e-3, 0.5 * diag)

            cam = self.renderer.GetActiveCamera()
            if cam is None:
                cam = vtk.vtkCamera()
                self.renderer.SetActiveCamera(cam)

            # Position camera along +Z looking at center; scale distance for better trackball feel
            distance = max(1.0, radius * 2.2)
            cam.SetFocalPoint(cx, cy, cz)
            cam.SetPosition(cx, cy, cz + distance)
            cam.SetViewUp(0.0, 1.0, 0.0)

            # Update clipping range for current bounds
            self.renderer.ResetCameraClippingRange()

            # Render updates
            self.vtk_widget.GetRenderWindow().Render()
            self.logger.debug(
                f"Camera fitted to model: center=({cx:.3f},{cy:.3f},{cz:.3f}) "
                f"radius={radius:.3f} distance={distance:.3f}"
            )
        except Exception as e:
            # Fallback to default reset on any error
            try:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()
                self.vtk_widget.GetRenderWindow().Render()
            except Exception:
                pass
            self.logger.warning(f"Fallback camera reset due to error: {e}")
    
    @log_function_call(get_logger(__name__))
    def load_model(self, model: Model) -> bool:
        """
        Load a model into the 3D viewer.
        
        Args:
            model: The model to load
            
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            self.logger.info(f"Loading model with {model.stats.triangle_count} triangles")
            
            # Remove any existing model
            self._remove_current_model()
            
            # Store reference to the model
            self.current_model = model
            
            # Create VTK polydata from model
            polydata = self._create_vtk_polydata(model)
            
            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            
            # Create actor
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            
            # Set properties using theme colors
            self.actor.GetProperty().SetColor(*vtk_rgb('model_surface'))
            self.actor.GetProperty().SetAmbient(0.3)  # Increased ambient lighting
            self.actor.GetProperty().SetDiffuse(0.8)  # Increased diffuse lighting
            self.actor.GetProperty().SetSpecular(0.4)
            self.actor.GetProperty().SetSpecularPower(15.0)
            self.actor.GetProperty().SetEdgeColor(*vtk_rgb('edge_color'))
            self.actor.GetProperty().SetLineWidth(1.0)
            # Edge visibility will be controlled by render mode in _apply_render_mode()
            
            # Add actor to renderer
            self.renderer.AddActor(self.actor)
            
            # Apply current render mode
            self._apply_render_mode()
            
            # Fit camera to model
            self._fit_camera_to_model(model)
            
            # Emit signal
            self.model_loaded.emit(f"Model with {model.stats.triangle_count} triangles")
            
            self.logger.info(f"Model loaded successfully: {model.stats.triangle_count} triangles, {model.stats.vertex_count} vertices")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            return False
    
    @log_function_call(get_logger(__name__))
    def clear_scene(self) -> None:
        """Clear the 3D scene."""
        self.logger.info("Clearing 3D scene")
        
        # Remove current model
        self._remove_current_model()
        
        # Reset camera
        self.reset_view()
        
        self.logger.info("3D scene cleared")
    
    @log_function_call(get_logger(__name__))
    def reset_view(self) -> None:
        """Reset the camera view to default position."""
        self.logger.debug("Resetting camera view")
        
        # Reset camera
        self.renderer.ResetCamera()
        
        # Update the view
        self.vtk_widget.GetRenderWindow().Render()
    
    def get_model_info(self) -> Optional[dict]:
        """
        Get information about the currently loaded model.
        
        Returns:
            Dictionary with model information or None if no model is loaded
        """
        if not self.current_model:
            return None
        
        return {
            'triangle_count': self.current_model.stats.triangle_count,
            'vertex_count': self.current_model.stats.vertex_count,
            'dimensions': self.current_model.stats.get_dimensions(),
            'file_size': self.current_model.stats.file_size_bytes,
            'format': self.current_model.stats.format_type.value,
            'parsing_time': self.current_model.stats.parsing_time_seconds,
            'current_fps': self.current_fps
        }
    
    def cleanup(self) -> None:
        """Clean up resources before widget destruction."""
        self.logger.info("Cleaning up VTK viewer resources")
        
        # Stop performance timer
        if hasattr(self, 'performance_timer'):
            self.performance_timer.stop()
        
        # Remove current model
        self._remove_current_model()
        
        # Clean up VTK resources
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.Finalize()
        
        # Force garbage collection
        gc.collect()
        
        self.logger.info("VTK viewer cleanup completed")
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)

    # ---- Theme live-apply support ----
    def apply_theme(self) -> None:
        """
        Reapply QSS and VTK colors from gui.theme at runtime.
        Safe to call multiple times.
        """
        try:
            # Re-apply widget QSS using current COLORS
            from gui.theme import COLORS, vtk_rgb  # late import to read current theme
            self.setStyleSheet(f"""
                QPushButton {{
                    padding: 6px 12px;
                    border: 1px solid {COLORS.border};
                    background-color: {COLORS.surface};
                    color: {COLORS.text};
                    border-radius: 2px;
                    font-weight: normal;
                }}
                QPushButton:checked {{
                    background-color: {COLORS.primary};
                    color: {COLORS.primary_text};
                    border: 1px solid {COLORS.primary};
                }}
                QPushButton:hover {{
                    background-color: {COLORS.hover};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS.pressed};
                }}
                QProgressBar {{
                    border: 1px solid {COLORS.border};
                    border-radius: 2px;
                    text-align: center;
                    background-color: {COLORS.window_bg};
                    color: {COLORS.text};
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS.progress_chunk};
                    border-radius: 1px;
                }}
                QLabel {{
                    color: {COLORS.text};
                    background-color: transparent;
                }}
            """)

            # Update renderer background
            if hasattr(self, "renderer"):
                self.renderer.SetBackground(*vtk_rgb('canvas_bg'))

                # Update lights in the renderer
                lights = self.renderer.GetLights()
                if lights is not None:
                    lights.InitTraversal()
                    import vtk as _vtk  # type: ignore
                    l = lights.GetNextItem()
                    while l:
                        l.SetColor(*vtk_rgb('light_color'))
                        l = lights.GetNextItem()

            # Update actor colors if present
            if hasattr(self, "actor") and self.actor:
                prop = self.actor.GetProperty()
                prop.SetColor(*vtk_rgb('model_surface'))
                prop.SetEdgeColor(*vtk_rgb('edge_color'))

            # Render updates
            if hasattr(self, "vtk_widget"):
                self.vtk_widget.GetRenderWindow().Render()
        except Exception:
            # Fail-safe: never break UI due to theme update
            pass