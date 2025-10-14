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
        
        self.points_button = QPushButton("Points")
        self.points_button.setCheckable(True)
        self.points_button.clicked.connect(lambda: self._set_render_mode(RenderMode.POINTS))
        
        control_layout.addWidget(self.solid_button)
        control_layout.addWidget(self.wireframe_button)
        control_layout.addWidget(self.points_button)
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
        
        # Style the widget with Windows standard colors
        self.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                background-color: #f5f5f5;
                color: #000000;
                border-radius: 2px;
                font-weight: normal;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: #ffffff;
                border: 1px solid #0078d4;
            }
            QPushButton:hover {
                background-color: #e1e1e1;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 2px;
                text-align: center;
                background-color: #ffffff;
                color: #000000;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 1px;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
        """)
    
    def _setup_vtk_scene(self) -> None:
        """Set up the VTK scene with renderer and interactor."""
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1.0, 1.0, 1.0)  # White background for better contrast
        
        # Add better lighting for improved visibility
        light1 = vtk.vtkLight()
        light1.SetPosition(100, 100, 100)
        light1.SetIntensity(0.8)
        light1.SetColor(1.0, 1.0, 1.0)  # White light
        self.renderer.AddLight(light1)
        
        light2 = vtk.vtkLight()
        light2.SetPosition(-100, -100, 100)
        light2.SetIntensity(0.5)
        light2.SetColor(1.0, 1.0, 1.0)  # White light
        self.renderer.AddLight(light2)
        
        # Create render window
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Create interactor
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        
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
        self.points_button.setChecked(mode == RenderMode.POINTS)
        
        # Apply rendering mode if model is loaded
        if self.actor:
            self._apply_render_mode()
        
        self.logger.info(f"Render mode changed to: {mode.value}")
    
    def _apply_render_mode(self) -> None:
        """Apply the current render mode to the model."""
        if not self.actor:
            return
        
        if self.render_mode == RenderMode.WIREFRAME:
            self.actor.GetProperty().SetRepresentationToWireframe()
            self.actor.GetProperty().SetLineWidth(1.0)
        elif self.render_mode == RenderMode.POINTS:
            self.actor.GetProperty().SetRepresentationToPoints()
            self.actor.GetProperty().SetPointSize(3.0)
        else:  # SOLID
            self.actor.GetProperty().SetRepresentationToSurface()
        
        # Update the view
        self.vtk_widget.GetRenderWindow().Render()
    
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
        Adjust camera position to fit the model in view.
        
        Args:
            model: The model to fit in view
        """
        if not model:
            return
        
        # Reset camera to fit all actors
        self.renderer.ResetCamera()
        
        # Update the view
        self.vtk_widget.GetRenderWindow().Render()
        
        self.logger.debug("Camera positioned to fit model")
    
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
            
            # Set properties with better contrast
            self.actor.GetProperty().SetColor(0.2, 0.4, 0.8)  # Darker blue for better contrast
            self.actor.GetProperty().SetAmbient(0.3)  # Increased ambient lighting
            self.actor.GetProperty().SetDiffuse(0.8)  # Increased diffuse lighting
            self.actor.GetProperty().SetSpecular(0.4)
            self.actor.GetProperty().SetSpecularPower(15.0)
            self.actor.GetProperty().SetEdgeVisibility(1)  # Show edges for better definition
            self.actor.GetProperty().SetEdgeColor(0.0, 0.0, 0.0)  # Black edges
            self.actor.GetProperty().SetLineWidth(1.0)
            
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