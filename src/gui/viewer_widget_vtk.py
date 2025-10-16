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
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel, QFrame
from PySide6.QtGui import QColor

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util import numpy_support as vtk_np

from core.logging_config import get_logger, log_function_call
from core.performance_monitor import get_performance_monitor
from core.model_cache import get_model_cache, CacheLevel
from parsers.stl_parser import STLModel
from core.data_structures import Model, LoadingState, Vector3D, Triangle
from gui.theme import COLORS, vtk_rgb
from gui.material_picker_widget import MaterialPickerWidget


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

    # New integration signals
    lighting_panel_requested = Signal()  # Ask MainWindow to toggle lighting dock
    material_selected = Signal(str)      # Forward selected species name to MainWindow
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
        self.grid_visible = True  # Grid visibility state - MUST be set before _setup_vtk_scene()
        self.grid_actor = None
        self.ground_actor = None
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
        
        # Create VTK widget wrapped in a framed container
        self.vtk_widget = QVTKRenderWindowInteractor(self)

        self.viewer_frame = QFrame()
        self.viewer_frame.setObjectName("ViewerFrame")
        viewer_layout = QVBoxLayout(self.viewer_frame)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        viewer_layout.addWidget(self.vtk_widget)

        layout.addWidget(self.viewer_frame)
        
        # Create control panel
        control_panel = QWidget()
        control_panel.setObjectName("ControlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # Render mode buttons
        self.solid_button = QPushButton("Solid")
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)
        self.solid_button.clicked.connect(lambda: self._set_render_mode(RenderMode.SOLID))

        # Add material picker button
        self.material_button = QPushButton("Material")
        self.material_button.setCheckable(False)
        self.material_button.clicked.connect(self._open_material_picker)

        # Add lighting panel button
        self.lighting_button = QPushButton("Lighting")
        self.lighting_button.setCheckable(False)
        self.lighting_button.clicked.connect(self._open_lighting_panel)

        # Assemble controls
        control_layout.addWidget(self.solid_button)
        control_layout.addWidget(self.material_button)
        control_layout.addWidget(self.lighting_button)

        # Grid toggle button
        self.grid_button = QPushButton("Grid")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(True)
        self.grid_button.clicked.connect(self._toggle_grid)
        control_layout.addWidget(self.grid_button)

        # Reset view button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        control_layout.addWidget(self.reset_button)

        # Rotate 90° buttons (rotate around view axis)
        self.rotate_ccw_button = QPushButton("↺ 90°")
        self.rotate_ccw_button.setToolTip("Rotate 90° counter-clockwise around view axis")
        self.rotate_ccw_button.clicked.connect(lambda: self._rotate_around_view_axis(90))
        control_layout.addWidget(self.rotate_ccw_button)
        
        self.rotate_cw_button = QPushButton("↻ 90°")
        self.rotate_cw_button.setToolTip("Rotate 90° clockwise around view axis")
        self.rotate_cw_button.clicked.connect(lambda: self._rotate_around_view_axis(-90))
        control_layout.addWidget(self.rotate_cw_button)

        control_layout.addStretch()

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
            QFrame#ViewerFrame {{
                border: 1px solid {COLORS.border};
                border-radius: 6px;
                background-color: {COLORS.window_bg};
            }}
            QWidget#ControlPanel {{
                background-color: {COLORS.card_bg};
                border-top: 1px solid {COLORS.border};
            }}
            QPushButton {{
                padding: 6px 12px;
                border: 1px solid {COLORS.border};
                background-color: {COLORS.surface};
                color: {COLORS.text};
                border-radius: 4px;
                font-weight: normal;
            }}
            QPushButton:checked {{
                background-color: {COLORS.primary};
                color: {COLORS.primary_text};
                border: 1px solid {COLORS.primary};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS.hover};
                border-color: {COLORS.primary};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.pressed};
            }}
            QProgressBar {{
                border: 1px solid {COLORS.border};
                border-radius: 3px;
                text-align: center;
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS.progress_chunk};
                border-radius: 2px;
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
        # Gradient studio-style background (darker at top, lighter at bottom)
        self.renderer.GradientBackgroundOn()
        bg_rgb = vtk_rgb('canvas_bg')
        top_color = (max(0, bg_rgb[0] - 0.15), max(0, bg_rgb[1] - 0.15), max(0, bg_rgb[2] - 0.15))
        self.renderer.SetBackground2(*top_color)  # Top (darker)
        self.renderer.SetBackground(*bg_rgb)      # Bottom (original)

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
        
        # Camera orientation widget in top-right corner (Fusion360-style face toggle)
        self.camera_widget = None
        try:
            if hasattr(vtk, "vtkCameraOrientationWidget"):
                # Preferred: clickable orientation cube that reorients the main camera
                self.camera_widget = vtk.vtkCameraOrientationWidget()
                self.camera_widget.SetInteractor(self.interactor)
                self.camera_widget.SetParentRenderer(self.renderer)
                try:
                    # Put it in the upper-right corner
                    self.camera_widget.SetViewportCorner(vtk.vtkCameraOrientationWidget.UpperRight)
                except Exception:
                    pass
                # Enable interaction
                try:
                    self.camera_widget.SetEnableInteractivity(True)
                except Exception:
                    pass
                
                # Add observer to fit camera after orientation change
                try:
                    self.camera_widget.AddObserver("EndInteractionEvent", self._on_orientation_widget_interaction)
                except Exception:
                    pass
                
                try:
                    self.camera_widget.SetEnabled(1)
                except Exception:
                    # Some VTK builds use On()
                    self.camera_widget.On()
            else:
                # Fallback: annotated cube inside an orientation marker widget (less interactive)
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
                # Style cube faces and edges
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
                # Position in top-right corner
                self.marker.SetViewport(0.8, 0.8, 1.0, 1.0)
                
                # Add observer to fit camera after interaction
                try:
                    self.marker.AddObserver("EndInteractionEvent", self._on_orientation_widget_interaction)
                except Exception:
                    pass
        except Exception:
            # Non-fatal if orientation widget setup fails
            pass

        # Add a themed grid floor (initial baseline, resized when a model loads)
        # grid_actor and ground_actor initialized in __init__ before this point
        try:
            self.logger.info(f"Creating initial grid and ground with grid_visible={self.grid_visible}")
            # Force grid to be visible initially for debugging
            self.grid_visible = True
            self._update_grid(radius=100.0, center_x=0.0, center_y=0.0)
            self._create_ground_plane(radius=100.0, center_x=0.0, center_y=0.0)
            
            # Ensure visibility is set correctly
            if self.grid_actor:
                self.grid_actor.SetVisibility(True)
                self.logger.info("Grid actor visibility set to True")
            if self.ground_actor:
                self.ground_actor.SetVisibility(True)
                self.logger.info("Ground actor visibility set to True")
                
            self.logger.info(f"Initial grid and ground plane created - grid_actor exists: {self.grid_actor is not None}, ground_actor exists: {self.ground_actor is not None}")
        except Exception as e:
            self.logger.error(f"Failed to create initial grid/ground: {e}", exc_info=True)
        
        # Set up shadow mapping for realistic rendering
        self._setup_shadows()
        
        # Set up default camera
        self.renderer.ResetCamera()
        
        # Start interactor
        self.interactor.Initialize()
        
        self.logger.debug("VTK scene setup completed")

    def _update_grid(self, radius: float, center_x: float = 0.0, center_y: float = 0.0) -> None:
        """
        Create/update a studio-style, infinite-looking XY grid at Z=0 using a large planar mesh's edges.
        Uses the radius and center parameters to properly size the grid around the model.
        """
        try:
            grid_size = max(100.0, radius * 3.0)  # Ensure grid is large enough
            
            if self.grid_actor is None:
                # Create properly sized grid plane
                plane = vtk.vtkPlaneSource()
                plane.SetOrigin(center_x - grid_size, center_y - grid_size, 0.0)
                plane.SetPoint1(center_x + grid_size, center_y - grid_size, 0.0)
                plane.SetPoint2(center_x - grid_size, center_y + grid_size, 0.0)
                plane.SetResolution(50, 50)  # Good balance of detail and performance

                # Extract only the grid lines (edges)
                edges = vtk.vtkExtractEdges()
                edges.SetInputConnection(plane.GetOutputPort())

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(edges.GetOutputPort())

                self.grid_actor = vtk.vtkActor()
                self.grid_actor.SetMapper(mapper)

                # Studio-style grid appearance
                prop = self.grid_actor.GetProperty()
                prop.SetColor(*vtk_rgb('edge_color'))
                prop.SetOpacity(0.4)  # Slightly more visible
                prop.SetLineWidth(1.0)
                try:
                    prop.LightingOff()
                    # Ensure grid renders on top of ground plane
                    prop.SetRenderLinesAsTubes(False)
                except Exception:
                    pass

                self.renderer.AddActor(self.grid_actor)
                # Respect current visibility toggle state
                self.grid_actor.SetVisibility(self.grid_visible if hasattr(self, "grid_visible") else True)
                self.logger.info(f"Studio-style infinite grid created with size {grid_size:.2f}")
            else:
                # Update existing grid with new size/position
                plane = vtk.vtkPlaneSource()
                plane.SetOrigin(center_x - grid_size, center_y - grid_size, 0.0)
                plane.SetPoint1(center_x + grid_size, center_y - grid_size, 0.0)
                plane.SetPoint2(center_x - grid_size, center_y + grid_size, 0.0)
                plane.SetResolution(50, 50)
                
                edges = vtk.vtkExtractEdges()
                edges.SetInputConnection(plane.GetOutputPort())
                
                mapper = self.grid_actor.GetMapper()
                mapper.SetInputConnection(edges.GetOutputPort())
                
                # Ensure theme-aligned styling on updates
                prop = self.grid_actor.GetProperty()
                prop.SetColor(*vtk_rgb('edge_color'))
                prop.SetOpacity(0.4)
                prop.SetLineWidth(1.0)
                if hasattr(self, "grid_visible"):
                    self.grid_actor.SetVisibility(self.grid_visible)

            # Force render update
            try:
                self.vtk_widget.GetRenderWindow().Render()
            except Exception:
                pass
        except Exception as e:
            # Never break rendering due to grid failure
            self.logger.warning(f"Grid update failed: {e}")
            pass

    def _create_ground_plane(self, radius: float, center_x: float = 0.0, center_y: float = 0.0) -> None:
        """
        Create a solid ground plane for shadow reception and better spatial reference.
        
        Args:
            radius: Ground plane size
            center_x: X coordinate of center
            center_y: Y coordinate of center
        """
        try:
            # Create a plane at Z=0 (slightly below to avoid z-fighting with grid)
            plane = vtk.vtkPlaneSource()
            size = max(100.0, radius * 2.0)  # Ensure adequate size for shadows
            plane.SetOrigin(center_x - size, center_y - size, -0.02)  # Slightly below Z=0
            plane.SetPoint1(center_x + size, center_y - size, -0.02)
            plane.SetPoint2(center_x - size, center_y + size, -0.02)
            plane.SetResolution(20, 20)  # Higher resolution for better shadow quality
            
            if self.ground_actor is None:
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(plane.GetOutputPort())
                
                self.ground_actor = vtk.vtkActor()
                self.ground_actor.SetMapper(mapper)
                
                # Make ground visible with subtle color and shadow reception
                prop = self.ground_actor.GetProperty()
                # Use slightly darker version of canvas_bg for ground contrast
                bg_rgb = vtk_rgb('canvas_bg')
                ground_color = (max(0, bg_rgb[0] - 0.12), max(0, bg_rgb[1] - 0.12), max(0, bg_rgb[2] - 0.12))
                prop.SetColor(*ground_color)
                prop.SetOpacity(0.98)  # Nearly opaque for good shadow reception
                prop.LightingOn()
                
                # Enable shadow reception with proper material properties
                prop.SetAmbient(0.2)  # Lower ambient for better shadows
                prop.SetDiffuse(0.9)  # Higher diffuse for shadow reception
                prop.SetSpecular(0.05)  # Low specular to avoid hot spots
                prop.SetSpecularPower(5.0)
                
                self.renderer.AddActor(self.ground_actor)
                # Set initial visibility
                if hasattr(self, 'grid_visible'):
                    self.ground_actor.SetVisibility(self.grid_visible)
                else:
                    self.ground_actor.SetVisibility(True)
                self.logger.info(f"Ground plane created and added: center=({center_x:.2f}, {center_y:.2f}), size={size:.2f}")
            else:
                # Update existing ground plane
                mapper = self.ground_actor.GetMapper()
                mapper.SetInputConnection(plane.GetOutputPort())
                
                # Update color
                bg_rgb = vtk_rgb('canvas_bg')
                ground_color = (max(0, bg_rgb[0] - 0.12), max(0, bg_rgb[1] - 0.12), max(0, bg_rgb[2] - 0.12))
                self.ground_actor.GetProperty().SetColor(*ground_color)
                # Ensure visibility matches state
                if hasattr(self, 'grid_visible'):
                    self.ground_actor.SetVisibility(self.grid_visible)
                    
            # Force render update
            try:
                self.vtk_widget.GetRenderWindow().Render()
            except Exception:
                pass
                
        except Exception as e:
            # Never break rendering due to ground plane failure
            self.logger.warning(f"Ground plane creation/update failed: {e}")

    def _setup_shadows(self) -> None:
        """Enable shadow mapping for realistic shadows."""
        try:
            # Enable shadow mapping on the renderer
            if hasattr(vtk, 'vtkShadowMapPass'):
                shadows = vtk.vtkShadowMapPass()
                
                # Configure shadow parameters for better quality
                try:
                    shadows.SetResolution(2048)  # Higher resolution shadows
                    shadows.SetIntensityCorrection(True)
                except Exception:
                    pass
                
                # Create sequence pass for shadow rendering
                seq = vtk.vtkSequencePass()
                passes = vtk.vtkRenderPassCollection()
                passes.AddItem(shadows.GetShadowMapBakerPass())
                passes.AddItem(shadows)
                seq.SetPasses(passes)
                
                # Create camera pass
                cameraP = vtk.vtkCameraPass()
                cameraP.SetDelegatePass(seq)
                
                # Set render pass to renderer
                try:
                    self.renderer.SetPass(cameraP)
                    self.logger.info("High-quality shadow mapping enabled")
                except Exception as e:
                    self.logger.debug(f"Could not set shadow pass (may not be supported): {e}")
            else:
                # Fallback: ensure proper lighting for depth perception
                self.logger.debug("Shadow mapping not available in this VTK build")
        except Exception as e:
            # Shadows are optional enhancement, don't break viewer if unavailable
            self.logger.debug(f"Shadow mapping setup failed: {e}")
    
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

    def _create_vtk_polydata_from_arrays(self, model: Model) -> vtk.vtkPolyData:
        """
        Create VTK polydata directly from NumPy arrays on the Model.
        Expects:
          - model.vertex_array: float32 [N*3, 3]
          - model.normal_array: float32 [N*3, 3]
        """
        try:
            if not hasattr(model, "is_array_based") or not model.is_array_based():
                # Fallback to legacy path if arrays are not available
                return self._create_vtk_polydata(model)  # type: ignore[arg-type]

            import numpy as _np  # local import to avoid global dependency
            vertex_array = model.vertex_array  # type: ignore[assignment]
            normal_array = model.normal_array  # type: ignore[assignment]
            if vertex_array is None or normal_array is None:
                return self._create_vtk_polydata(model)  # type: ignore[arg-type]

            total_vertices = int(vertex_array.shape[0])
            if total_vertices % 3 != 0:
                # Data integrity check failed; fallback
                self.logger.warning("Vertex array length is not multiple of 3; falling back to legacy path")
                return self._create_vtk_polydata(model)  # type: ignore[arg-type]

            tri_count = total_vertices // 3
            self.logger.info(f"Creating VTK polydata for {tri_count} triangles via array fast path")

            # Ensure arrays are contiguous and use double precision for maximum VTK compatibility
            vertex_array = _np.ascontiguousarray(vertex_array, dtype=_np.float64)
            normal_array = _np.ascontiguousarray(normal_array, dtype=_np.float64)

            # Points
            points = vtk.vtkPoints()
            vtk_points = vtk_np.numpy_to_vtk(vertex_array, deep=True, array_type=vtk.VTK_DOUBLE)
            # Ensure 3 components per tuple for xyz
            vtk_points.SetNumberOfComponents(3)
            points.SetData(vtk_points)

            # Normals
            normals_vtk = vtk_np.numpy_to_vtk(normal_array, deep=True, array_type=vtk.VTK_DOUBLE)
            normals_vtk.SetName("Normals")
            # Ensure 3 components per tuple for nx ny nz
            normals_vtk.SetNumberOfComponents(3)

            # Build connectivity using VTK 9 explicit offsets + connectivity API
            conn = _np.arange(total_vertices, dtype=_np.int64)
            offsets = _np.arange(0, total_vertices + 1, 3, dtype=_np.int64)  # length tri_count+1

            conn_vtk = vtk_np.numpy_to_vtkIdTypeArray(conn, deep=True)
            offsets_vtk = vtk_np.numpy_to_vtkIdTypeArray(offsets, deep=True)

            triangles = vtk.vtkCellArray()
            triangles.SetData(offsets_vtk, conn_vtk)

            # Assemble polydata
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(triangles)
            polydata.GetPointData().SetNormals(normals_vtk)
            polydata.GetPointData().SetActiveNormals("Normals")
            polydata.Modified()
            try:
                # Compact internal arrays and finalize topology for safe rendering
                polydata.Squeeze()
                polydata.BuildCells()
                # Explicitly mark sub-datasets as modified to avoid stale pipeline states
                if polydata.GetPoints() is not None:
                    polydata.GetPoints().Modified()
                if polydata.GetPolys() is not None:
                    polydata.GetPolys().Modified()
            except Exception:
                pass

            # If some VTK builds still report 0 polys, try legacy var-encoding SetCells fallback
            if polydata.GetNumberOfPolys() == 0:
                self.logger.warning("VTK9 SetData connectivity yielded 0 polys; trying legacy SetCells fallback")
                ids = _np.arange(total_vertices, dtype=_np.int64).reshape(tri_count, 3)
                three_col = _np.full((tri_count, 1), 3, dtype=_np.int64)
                cells_flat = _np.hstack((three_col, ids)).ravel()
                id_array = vtk_np.numpy_to_vtkIdTypeArray(cells_flat, deep=True)
                triangles_legacy = vtk.vtkCellArray()
                triangles_legacy.SetCells(tri_count, id_array)

                polydata_legacy = vtk.vtkPolyData()
                polydata_legacy.SetPoints(points)
                polydata_legacy.SetPolys(triangles_legacy)
                polydata_legacy.GetPointData().SetNormals(normals_vtk)
                polydata_legacy.GetPointData().SetActiveNormals("Normals")
                try:
                    polydata_legacy.Squeeze()
                    polydata_legacy.BuildCells()
                except Exception:
                    pass
                self.logger.info(
                    f"Legacy path counts: points={polydata_legacy.GetNumberOfPoints()}, polys={polydata_legacy.GetNumberOfPolys()}"
                )
                if polydata_legacy.GetNumberOfPolys() > 0:
                    polydata = polydata_legacy

            self.logger.info(
                f"PolyData created: points={polydata.GetNumberOfPoints()}, polys={polydata.GetNumberOfPolys()}, "
                f"expected_points={total_vertices}, expected_polys={tri_count}"
            )
            return polydata
        except Exception as e:
            # Fail-safe: log and fallback
            self.logger.error(f"Array-to-VTK fast path failed: {e}; using legacy path")
            return self._create_vtk_polydata(model)  # type: ignore[arg-type]
    
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
        # Wireframe/Points buttons are not present in the UI; backend modes remain available
        
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

    def _toggle_grid(self) -> None:
        """Toggle grid and ground plane visibility."""
        self.grid_visible = not self.grid_visible
        
        self.logger.info(f"Grid toggle requested: new state={self.grid_visible}, grid_actor={self.grid_actor is not None}, ground_actor={self.ground_actor is not None}")
        
        # Update grid visibility
        if self.grid_actor:
            self.grid_actor.SetVisibility(self.grid_visible)
            self.logger.info(f"Grid actor visibility set to {self.grid_visible}")
        else:
            self.logger.warning("Grid actor not found during toggle")
        
        # Update ground plane visibility
        if self.ground_actor:
            self.ground_actor.SetVisibility(self.grid_visible)
            self.logger.info(f"Ground actor visibility set to {self.grid_visible}")
        else:
            self.logger.warning("Ground actor not found during toggle")
        
        # Update button state
        self.grid_button.setChecked(self.grid_visible)
        
        # Render update
        try:
            self.vtk_widget.GetRenderWindow().Render()
            self.logger.debug("Render window updated after grid toggle")
        except Exception as e:
            self.logger.error(f"Failed to render after grid toggle: {e}")
    
    def _on_orientation_widget_interaction(self, obj, event) -> None:
        """
        Callback for when the UCS orientation widget is clicked.
        Resets camera to properly frame the model after orientation change.
        
        Args:
            obj: The VTK object that triggered the event
            event: The event type
        """
        import time
        start_time = time.time()
        
        try:
            # Capture camera state before interaction
            camera = self.renderer.GetActiveCamera()
            if camera:
                pre_position = camera.GetPosition()
                pre_focal = camera.GetFocalPoint()
                pre_viewup = camera.GetViewUp()
                pre_clipping = camera.GetClippingRange()
                
                self.logger.debug(
                    f"UCS INTERACTION START - Event: {event}, Object: {obj.__class__.__name__ if obj else 'None'}"
                )
                self.logger.debug(
                    f"  PRE-INTERACTION Camera State:\n"
                    f"    Position: ({pre_position[0]:.3f}, {pre_position[1]:.3f}, {pre_position[2]:.3f})\n"
                    f"    Focal Point: ({pre_focal[0]:.3f}, {pre_focal[1]:.3f}, {pre_focal[2]:.3f})\n"
                    f"    View Up: ({pre_viewup[0]:.3f}, {pre_viewup[1]:.3f}, {pre_viewup[2]:.3f})\n"
                    f"    Clipping Range: ({pre_clipping[0]:.3f}, {pre_clipping[1]:.3f})"
                )
            
            # DON'T automatically refit camera after UCS interaction
            # The UCS widget already sets the correct camera orientation
            # We only need to update clipping range to ensure model is visible
            if self.current_model and self.actor:
                bounds = self.actor.GetBounds() if self.actor else None
                self.logger.debug(
                    f"  Model loaded: triangle_count={self.current_model.stats.triangle_count}, "
                    f"bounds={bounds if bounds else 'None'} - Preserving UCS orientation"
                )
                # Only update clipping range, don't reset camera position
                try:
                    self.renderer.ResetCameraClippingRange()
                    self.vtk_widget.GetRenderWindow().Render()
                except Exception:
                    pass
            else:
                # No model loaded, just update clipping range
                self.logger.debug("  No model loaded, updating clipping range only")
                try:
                    self.renderer.ResetCameraClippingRange()
                    self.vtk_widget.GetRenderWindow().Render()
                except Exception:
                    pass
            
            # Capture camera state after interaction
            if camera:
                post_position = camera.GetPosition()
                post_focal = camera.GetFocalPoint()
                post_viewup = camera.GetViewUp()
                post_clipping = camera.GetClippingRange()
                
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                
                self.logger.debug(
                    f"  POST-INTERACTION Camera State:\n"
                    f"    Position: ({post_position[0]:.3f}, {post_position[1]:.3f}, {post_position[2]:.3f})\n"
                    f"    Focal Point: ({post_focal[0]:.3f}, {post_focal[1]:.3f}, {post_focal[2]:.3f})\n"
                    f"    View Up: ({post_viewup[0]:.3f}, {post_viewup[1]:.3f}, {post_viewup[2]:.3f})\n"
                    f"    Clipping Range: ({post_clipping[0]:.3f}, {post_clipping[1]:.3f})\n"
                    f"  Duration: {elapsed:.2f}ms"
                )
                
                # Calculate changes for easier analysis
                pos_delta = ((post_position[0]-pre_position[0])**2 +
                             (post_position[1]-pre_position[1])**2 +
                             (post_position[2]-pre_position[2])**2)**0.5
                focal_delta = ((post_focal[0]-pre_focal[0])**2 +
                               (post_focal[1]-pre_focal[1])**2 +
                               (post_focal[2]-pre_focal[2])**2)**0.5
                
                self.logger.debug(
                    f"  CHANGES: Position delta={pos_delta:.3f}, Focal point delta={focal_delta:.3f}"
                )
            
            self.logger.debug("UCS INTERACTION COMPLETE")
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self.logger.error(
                f"UCS INTERACTION FAILED after {elapsed:.2f}ms - Error: {e}",
                exc_info=True
            )
    
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

            # Resize grid and ground plane to comfortably cover the scene, centered on model
            try:
                self._update_grid(radius, center_x=cx, center_y=cy)
                self._create_ground_plane(radius, center_x=cx, center_y=cy)
            except Exception:
                pass

            cam = self.renderer.GetActiveCamera()
            if cam is None:
                cam = vtk.vtkCamera()
                self.renderer.SetActiveCamera(cam)

            # Position camera along +Z looking at center; scale distance for better trackball feel
            distance = max(1.0, radius * 2.2)
            cam.SetFocalPoint(cx, cy, cz)
            cam.SetPosition(cx, cy, cz + distance)
            cam.SetViewUp(0.0, 1.0, 0.0)

            # Explicit clipping range to avoid empty viewport on extreme bounds
            try:
                near = max(0.001, distance - (radius * 4.0))
                far = distance + (radius * 4.0)
                if far <= near:
                    far = near * 10.0
                cam.SetClippingRange(near, far)
            except Exception:
                pass

            # Also ask the renderer to recompute clipping
            try:
                self.renderer.ResetCameraClippingRange()
            except Exception:
                pass

            # Render updates
            try:
                self.vtk_widget.GetRenderWindow().Render()
            except Exception:
                pass

            self.logger.debug(
                f"Camera fitted to model: center=({cx:.3f},{cy:.3f},{cz:.3f}) "
                f"radius={radius:.3f} distance={distance:.3f} "
                f"clip={tuple(round(v,3) for v in (cam.GetClippingRange() if hasattr(cam,'GetClippingRange') else (0,0)))}"
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

            # On-demand full geometry load if buffers are missing but stats indicate geometry
            try:
                missing_arrays = not (hasattr(model, "is_array_based") and callable(getattr(model, "is_array_based")) and model.is_array_based())
                no_triangles_list = (len(getattr(model, "triangles", [])) == 0)
                has_stats = getattr(model, "stats", None) is not None
                has_tris_in_stats = has_stats and getattr(model.stats, "triangle_count", 0) > 0
                has_path = bool(getattr(model, "file_path", None))
                if missing_arrays and no_triangles_list and has_tris_in_stats and has_path:
                    self.logger.warning("No geometry buffers present; performing on-demand full load (non-lazy)")
                    from parsers.stl_parser import STLParser  # late import to avoid overhead on normal path
                    _parser = STLParser()
                    loaded = _parser.parse_file(model.file_path, progress_callback=None, lazy_loading=False)  # type: ignore[arg-type]
                    self.current_model = loaded
                    model = loaded
            except Exception as _ond_err:
                self.logger.error(f"On-demand full load failed: {_ond_err}")

            # Create VTK polydata from model
            # Emit diagnostics so we can see why a path was selected
            va = getattr(model, "vertex_array", None)
            na = getattr(model, "normal_array", None)
            ls = getattr(model, "loading_state", None)

            va_len = -1
            va_shape = None
            na_len = -1
            na_shape = None
            try:
                if va is not None:
                    va_shape = getattr(va, "shape", None)
                    if hasattr(va, "shape") and len(va.shape) > 0:
                        va_len = int(va.shape[0] or 0)
                    elif hasattr(va, "__len__"):
                        va_len = len(va)  # type: ignore[arg-type]
                if na is not None:
                    na_shape = getattr(na, "shape", None)
                    if hasattr(na, "shape") and len(na.shape) > 0:
                        na_len = int(na.shape[0] or 0)
                    elif hasattr(na, "__len__"):
                        na_len = len(na)  # type: ignore[arg-type]
            except Exception:
                pass

            self.logger.info(
                f"Array path diagnostics: loading_state={getattr(ls,'value',ls)}, "
                f"va_present={va is not None}, va_len={va_len}, va_shape={va_shape}, "
                f"na_present={na is not None}, na_len={na_len}, na_shape={na_shape}"
            )

            use_array = (
                (ls == LoadingState.ARRAY_GEOMETRY) and
                (va is not None) and (na is not None) and
                (va_len is not None and va_len > 0)
            )

            # Also honor explicit method if available
            if not use_array:
                try:
                    is_array_based_attr = getattr(model, "is_array_based", None)
                    if callable(is_array_based_attr) and bool(is_array_based_attr()):
                        use_array = True
                except Exception:
                    pass

            if use_array:
                self.logger.info("Selected ARRAY geometry path for VTK creation")
                polydata = self._create_vtk_polydata_from_arrays(model)
                self.logger.info("Used array-based fast path for VTK creation")
            else:
                self.logger.info("Selected legacy Triangle-object path for VTK creation")
                # Fallback to legacy triangle-object path
                polydata = self._create_vtk_polydata(model)

            # Safety fallback: if polys are zero try triangle filter (some VTK builds require this)
            try:
                if polydata.GetNumberOfPolys() == 0 and polydata.GetNumberOfStrips() == 0:
                    self.logger.warning("Polydata has zero polygons; applying vtkTriangleFilter fallback")
                    tf = vtk.vtkTriangleFilter()
                    tf.SetInputData(polydata)
                    tf.PassLinesOff()
                    tf.PassVertsOff()
                    tf.Update()
                    polydata = tf.GetOutput()
                    self.logger.info(
                        f"TriangleFilter result: points={polydata.GetNumberOfPoints()}, polys={polydata.GetNumberOfPolys()}"
                    )
            except Exception as _tf_err:
                self.logger.error(f"TriangleFilter fallback failed: {_tf_err}")

            # Preprocess normals to ensure shading and visibility
            try:
                need_normals = True
                pd_normals = polydata.GetPointData().GetNormals()
                if pd_normals is not None and pd_normals.GetNumberOfTuples() == polydata.GetNumberOfPoints():
                    need_normals = False
                if need_normals:
                    nrm = vtk.vtkPolyDataNormals()
                    nrm.SetInputData(polydata)
                    nrm.SetSplitting(0)
                    nrm.SetConsistency(1)
                    nrm.ComputePointNormalsOn()
                    nrm.ComputeCellNormalsOff()
                    nrm.AutoOrientNormalsOn()
                    nrm.Update()
                    polydata = nrm.GetOutput()
            except Exception:
                # Non-fatal; proceed without normals filter
                pass

            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            # Avoid unexpected scalar coloring affecting visibility
            try:
                mapper.ScalarVisibilityOff()
            except Exception:
                pass
            mapper.Update()

            # Create actor
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)

            # Set properties using theme colors and enable shadows
            prop = self.actor.GetProperty()
            prop.SetColor(*vtk_rgb('model_surface'))
            prop.SetAmbient(0.2)  # Lower ambient for better shadow contrast
            prop.SetDiffuse(0.9)  # Higher diffuse for shadow reception
            prop.SetSpecular(0.3)
            prop.SetSpecularPower(15.0)
            prop.SetEdgeColor(*vtk_rgb('edge_color'))
            prop.SetLineWidth(1.0)
            prop.BackfaceCullingOff()
            self.actor.VisibilityOn()
            # Ensure fully opaque and lighting enabled for visibility
            try:
                self.actor.GetProperty().SetOpacity(1.0)
                self.actor.GetProperty().LightingOn()
            except Exception:
                pass
            # If model color too close to background, switch to high-contrast fallback color
            try:
                ms = vtk_rgb('model_surface')
                bg = vtk_rgb('canvas_bg')
                if abs(ms[0]-bg[0]) + abs(ms[1]-bg[1]) + abs(ms[2]-bg[2]) < 0.30:
                    self.actor.GetProperty().SetColor(0.95, 0.2, 0.2)
                    self.logger.info("Adjusted model color for contrast with background")
            except Exception:
                pass
            # Edge visibility will be controlled by render mode in _apply_render_mode()
 
            # Add actor to renderer
            self.renderer.AddActor(self.actor)

            # Apply current render mode
            self._apply_render_mode()
 
            # Fit camera to model
            self._fit_camera_to_model(model)

            # Extra safety: ensure bounds not empty; if empty, force compute and reset camera
            try:
                _ = self.actor.GetBounds()
                self.renderer.ResetCameraClippingRange()
            except Exception:
                self.renderer.ResetCamera()
                self.renderer.ResetCameraClippingRange()

            # Render scene to ensure on-screen
            self.vtk_widget.GetRenderWindow().Render()

            # Emit signal
            self.model_loaded.emit(f"Model with {model.stats.triangle_count} triangles")

            self.logger.info(
                f"Model loaded successfully: {model.stats.triangle_count} triangles, "
                f"{model.stats.vertex_count} vertices, "
                f"polydata points={polydata.GetNumberOfPoints()}, polys={polydata.GetNumberOfPolys()}"
            )
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
    
    def _rotate_around_view_axis(self, degrees: float) -> None:
        """
        Rotate the view 90° around the camera's view direction (the axis you're looking down).
        
        Args:
            degrees: Rotation angle in degrees (positive = counter-clockwise, negative = clockwise)
        """
        try:
            import math
            camera = self.renderer.GetActiveCamera()
            if not camera:
                return
            
            # Get camera orientation
            position = camera.GetPosition()
            focal_point = camera.GetFocalPoint()
            view_up = camera.GetViewUp()
            
            # Calculate view direction (normalized)
            dx = focal_point[0] - position[0]
            dy = focal_point[1] - position[1]
            dz = focal_point[2] - position[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length < 0.0001:
                return
            view_dir = (dx/length, dy/length, dz/length)
            
            # Rotate the view-up vector around the view direction by 'degrees'
            angle = math.radians(degrees)
            
            # Use Rodrigues' rotation formula to rotate view_up around view_dir
            # v_rot = v*cos(θ) + (k×v)*sin(θ) + k*(k·v)*(1-cos(θ))
            # where k = view_dir (rotation axis), v = view_up (vector to rotate)
            
            k = view_dir
            v = view_up
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            # Dot product k·v
            k_dot_v = k[0]*v[0] + k[1]*v[1] + k[2]*v[2]
            
            # Cross product k×v
            k_cross_v = (
                k[1]*v[2] - k[2]*v[1],
                k[2]*v[0] - k[0]*v[2],
                k[0]*v[1] - k[1]*v[0]
            )
            
            # Rodrigues formula
            new_view_up = (
                v[0]*cos_a + k_cross_v[0]*sin_a + k[0]*k_dot_v*(1-cos_a),
                v[1]*cos_a + k_cross_v[1]*sin_a + k[1]*k_dot_v*(1-cos_a),
                v[2]*cos_a + k_cross_v[2]*sin_a + k[2]*k_dot_v*(1-cos_a)
            )
            
            # Apply the new view-up vector
            camera.SetViewUp(new_view_up[0], new_view_up[1], new_view_up[2])
            
            # Update clipping and render
            self.renderer.ResetCameraClippingRange()
            self.vtk_widget.GetRenderWindow().Render()
            
            self.logger.debug(f"Rotated view {degrees}° around view axis")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate around view axis: {e}")
    
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
                QFrame#ViewerFrame {{
                    border: 1px solid {COLORS.border};
                    border-radius: 6px;
                    background-color: {COLORS.window_bg};
                }}
                QWidget#ControlPanel {{
                    background-color: {COLORS.card_bg};
                    border-top: 1px solid {COLORS.border};
                }}
                QPushButton {{
                    padding: 6px 12px;
                    border: 1px solid {COLORS.border};
                    background-color: {COLORS.surface};
                    color: {COLORS.text};
                    border-radius: 4px;
                    font-weight: normal;
                }}
                QPushButton:checked {{
                    background-color: {COLORS.primary};
                    color: {COLORS.primary_text};
                    border: 1px solid {COLORS.primary};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.hover};
                    border-color: {COLORS.primary};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS.pressed};
                }}
                QProgressBar {{
                    border: 1px solid {COLORS.border};
                    border-radius: 3px;
                    text-align: center;
                    background-color: {COLORS.window_bg};
                    color: {COLORS.text};
                }}
                QProgressBar::chunk {{
                    background-color: {COLORS.progress_chunk};
                    border-radius: 2px;
                }}
                QLabel {{
                    color: {COLORS.text};
                    background-color: transparent;
                }}
            """)

            # Update renderer background
            if hasattr(self, "renderer"):
                bg_rgb = vtk_rgb('canvas_bg')
                # Gradient background
                top_color = (max(0, bg_rgb[0] - 0.15), max(0, bg_rgb[1] - 0.15), max(0, bg_rgb[2] - 0.15))
                try:
                    self.renderer.GradientBackgroundOn()
                except Exception:
                    pass
                self.renderer.SetBackground2(*top_color)
                self.renderer.SetBackground(*bg_rgb)

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

            # Update grid color/opacity if present
            if hasattr(self, "grid_actor") and self.grid_actor:
                try:
                    gp = self.grid_actor.GetProperty()
                    gp.SetColor(*vtk_rgb('edge_color'))
                    gp.SetOpacity(0.3)
                    gp.SetLineWidth(1.0)
                    if hasattr(gp, "SetRenderLinesAsTubes"):
                        gp.SetRenderLinesAsTubes(True)
                except Exception:
                    pass

            # Update ground plane color if present
            if hasattr(self, "ground_actor") and self.ground_actor:
                try:
                    bg_rgb = vtk_rgb('canvas_bg')
                    ground_color = (max(0, bg_rgb[0] - 0.05), max(0, bg_rgb[1] - 0.05), max(0, bg_rgb[2] - 0.05))
                    self.ground_actor.GetProperty().SetColor(*ground_color)
                except Exception:
                    pass

            # Render updates
            if hasattr(self, "vtk_widget"):
                self.vtk_widget.GetRenderWindow().Render()
        except Exception:
            # Fail-safe: never break UI due to theme update
            pass

    # ---- UI Actions: Material / Lighting ----
    def _open_material_picker(self) -> None:
        """Open material picker dialog"""
        try:
            dlg = MaterialPickerWidget(parent=self)
            # Forward selection to MainWindow; MainWindow's MaterialManager will apply
            dlg.material_selected.connect(lambda species: self.material_selected.emit(species))
            dlg.exec_()
        except Exception as e:
            try:
                self.logger.error(f"Failed to open material picker: {e}")
            except Exception:
                pass

    def _open_lighting_panel(self) -> None:
        """Toggle lighting control panel"""
        try:
            self.lighting_panel_requested.emit()
        except Exception:
            pass