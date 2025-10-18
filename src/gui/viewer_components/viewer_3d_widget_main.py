"""
3D viewer widget using PyQt3D.

Provides interactive 3D model visualization with camera controls,
lighting, and multiple rendering modes.
"""

import gc
import time
from typing import Optional, Tuple, Any

from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel, QFrame
from PySide6.QtGui import QColor

from PyQt3D.Qt3DCore import QEntity, QTransform, QTranslateTransform, QVector3D
from PyQt3D.Qt3DExtras import Qt3DWindow, QOrbitCameraController, QPhongMaterial, QDiffuseSpecularMaterial
from PyQt3D.Qt3DExtras import QPlaneMesh, QCuboidMesh, QSphereMesh, QTorusMesh
from PyQt3D.Qt3DRender import QCamera, QCameraLens, QDirectionalLight, QPointLight
from PyQt3D.Qt3DRender import QRenderSettings, QFrameGraph, QViewport, QCameraSelector
from PyQt3D.Qt3DRender import QClearBuffers, QBuffer, QAttribute, QGeometryRenderer
from PyQt3D.Qt3DInput import QInputSettings

from src.core.logging_config import get_logger, log_function_call
from src.gui.theme import SPACING_4, SPACING_8, SPACING_12, SPACING_16
from src.gui.theme_core import get_theme_color
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache, CacheLevel
from src.parsers.stl_parser import STLModel
from src.core.data_structures import Model, LoadingState, Vector3D, Triangle
from .render_mode import RenderMode
from .progressive_load_worker import ProgressiveLoadWorker


class Viewer3DWidget(QWidget):
    """
    3D viewer widget using PyQt3D for interactive model visualization.

    Features:
    - Interactive camera controls (orbit, pan, zoom)
    - Configurable lighting with point and directional lights
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
        self.logger.info("Initializing 3D viewer widget")

        # Viewer state
        self.current_model = None
        self.render_mode = RenderMode.SOLID
        self.model_entity = None
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
        self.progressive_loader = None
        self.current_loading_quality = LoadingState.METADATA_ONLY
        self.loading_in_progress = False

        # Initialize UI
        self._init_ui()
        self._setup_3d_scene()
        self._setup_lighting()
        self._setup_camera_controls()
        self._setup_performance_monitoring()

        # Update performance settings from profile
        perf_profile = self.performance_monitor.get_performance_profile()
        self.max_triangles_for_full_quality = perf_profile.max_triangles_for_full_quality
        self.adaptive_quality = perf_profile.adaptive_quality_enabled

        self.logger.info("3D viewer widget initialized successfully")

    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create 3D window
        self.view = Qt3DWindow()
        self.view.defaultFrameGraph().setClearColor(get_theme_color('canvas_bg'))

        # Create container widget for the 3D window, wrapped in a framed container for styling
        self.container = QWidget.createWindowContainer(self.view)
        self.container.setMinimumSize(400, 300)

        self.viewer_frame = QFrame()
        self.viewer_frame.setObjectName("ViewerFrame")
        viewer_layout = QVBoxLayout(self.viewer_frame)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)
        viewer_layout.addWidget(self.container)

        layout.addWidget(self.viewer_frame)

        # Create control panel
        control_panel = QWidget()
        control_panel.setObjectName("ControlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)

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
        progress_layout.setContentsMargins(SPACING_8, SPACING_8, SPACING_8, SPACING_8)

        self.progress_label = QLabel("Loading...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch()

        layout.addWidget(self.progress_frame)
        self.progress_frame.setVisible(False)

        # Material Design theme is applied globally via ThemeService
        # No need to apply hardcoded stylesheets here

    def _setup_3d_scene(self) -> None:
        """Set up the 3D scene with root entity and camera."""
        # Create root entity
        self.root_entity = QEntity()

        # Create camera
        self.camera = self.view.camera()
        self.camera.lens().setPerspectiveProjection(45.0, 16.0/9.0, 0.1, 1000.0)
        self.camera.setPosition(QVector3D(0, 0, 20))
        self.camera.setViewCenter(QVector3D(0, 0, 0))

        # Set up input settings
        self.input_settings = QInputSettings()
        self.root_entity.addComponent(self.input_settings)

        # Set root entity for the view
        self.view.setRootEntity(self.root_entity)

        # Create a placeholder default object
        self._create_default_scene()

    def _create_default_scene(self) -> None:
        """Create a default scene with a simple object."""
        # Create a simple cube as default
        self.default_entity = QEntity(self.root_entity)

        # Create cube mesh
        self.cube_mesh = QCuboidMesh()
        self.cube_mesh.setXExtent(5.0)
        self.cube_mesh.setYExtent(5.0)
        self.cube_mesh.setZExtent(5.0)

        # Create material (theme-based)
        self.default_material = QPhongMaterial()
        self.default_material.setDiffuse(get_theme_color('model_surface'))
        self.default_material.setAmbient(get_theme_color('model_ambient'))
        self.default_material.setSpecular(get_theme_color('model_specular'))

        # Create transform
        self.default_transform = QTransform()

        # Add components to entity
        self.default_entity.addComponent(self.cube_mesh)
        self.default_entity.addComponent(self.default_material)
        self.default_entity.addComponent(self.default_transform)

    def _setup_lighting(self) -> None:
        """Set up configurable lighting for the scene."""
        # Main directional light (like sunlight)
        self.directional_light = QDirectionalLight()
        self.directional_light.setColor(get_theme_color('light_color'))
        self.directional_light.setIntensity(0.8)
        self.directional_light.setWorldDirection(QVector3D(-1, -1, -1))

        # Create light entity
        self.directional_light_entity = QEntity(self.root_entity)
        self.directional_light_entity.addComponent(self.directional_light)

        # Point light (for better illumination)
        self.point_light = QPointLight()
        self.point_light.setColor(get_theme_color('light_color'))
        self.point_light.setIntensity(0.5)
        self.point_light.setConstantAttenuation(1.0)
        self.point_light.setLinearAttenuation(0.1)
        self.point_light.setQuadraticAttenuation(0.01)

        # Create point light transform
        self.point_light_transform = QTransform()
        self.point_light_transform.setTranslation(QVector3D(10, 10, 10))

        # Create point light entity
        self.point_light_entity = QEntity(self.root_entity)
        self.point_light_entity.addComponent(self.point_light)
        self.point_light_entity.addComponent(self.point_light_transform)

        self.logger.debug("Lighting setup completed")

    def _setup_camera_controls(self) -> None:
        """Set up orbit camera controller for mouse interaction."""
        self.camera_controller = QOrbitCameraController(self.root_entity)
        self.camera_controller.setCamera(self.camera)
        self.camera_controller.setLinearSpeed(50.0)
        self.camera_controller.setLookSpeed(180.0)

        # Configure mouse controls
        self.camera_controller.setZoomInLimit(0.5)

        self.logger.debug("Camera controls setup completed")

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

            # Adaptive quality adjustment
            if self.adaptive_quality and self.current_model:
                self._adjust_quality_based_on_performance()

        # Reset counters
        self.frame_count = 0
        self.last_fps_time = current_time

    def _adjust_quality_based_on_performance(self) -> None:
        """Adjust rendering quality based on performance metrics."""
        if not self.current_model:
            return

        triangle_count = len(self.current_model.triangles)

        # Reduce quality for very large models with poor performance
        if triangle_count > self.max_triangles_for_full_quality and self.current_fps < 30:
            self.logger.info(f"Adaptive quality: Reducing detail for {triangle_count} triangles at {self.current_fps:.1f} FPS")

            # Switch to lower quality model if available
            if self.current_model.file_path and self.current_loading_quality == LoadingState.FULL_GEOMETRY:
                self.logger.info("Switching to lower quality model for better performance")
                low_res_model = self.model_cache.get(self.current_model.file_path, CacheLevel.GEOMETRY_LOW)
                if low_res_model:
                    self._load_model_internal(low_res_model)
                    self.current_loading_quality = LoadingState.LOW_RES_GEOMETRY

    def _create_stl_geometry(self, model: STLModel) -> QGeometryRenderer:
        """
        Create Qt3D geometry from STL model data.

        Args:
            model: The STL model to convert

        Returns:
            QGeometryRenderer with the model geometry
        """
        from PyQt3D.Qt3DRender import QGeometry, QBuffer, QAttribute
        # QVector3D is already imported at the top of the file

        self.logger.info(f"Creating 3D geometry for {len(model.triangles)} triangles")

        # Create geometry
        geometry = QGeometry()

        # Calculate total vertices and normals
        triangle_count = len(model.triangles)
        total_vertices = triangle_count * 3

        # Create vertex position data
        vertex_positions = []
        vertex_normals = []

        for triangle in model.triangles:
            # Add triangle vertices
            vertex_positions.extend([
                triangle.vertex1.x, triangle.vertex1.y, triangle.vertex1.z,
                triangle.vertex2.x, triangle.vertex2.y, triangle.vertex2.z,
                triangle.vertex3.x, triangle.vertex3.y, triangle.vertex3.z
            ])

            # Add triangle normal for each vertex
            vertex_normals.extend([
                triangle.normal.x, triangle.normal.y, triangle.normal.z,
                triangle.normal.x, triangle.normal.y, triangle.normal.z,
                triangle.normal.x, triangle.normal.y, triangle.normal.z
            ])

        # Create vertex buffer
        vertex_buffer = QBuffer(geometry)
        vertex_buffer.setData(bytearray(vertex_positions))

        # Create normal buffer
        normal_buffer = QBuffer(geometry)
        normal_buffer.setData(bytearray(vertex_normals))

        # Create position attribute
        position_attribute = QAttribute()
        position_attribute.setAttributeType(QAttribute.VertexAttribute)
        position_attribute.setBuffer(vertex_buffer)
        position_attribute.setVertexBaseType(QAttribute.Float)
        position_attribute.setVertexSize(3)
        position_attribute.setCount(total_vertices)
        position_attribute.setName(QAttribute.defaultPositionAttributeName())

        # Create normal attribute
        normal_attribute = QAttribute()
        normal_attribute.setAttributeType(QAttribute.VertexAttribute)
        normal_attribute.setBuffer(normal_buffer)
        normal_attribute.setVertexBaseType(QAttribute.Float)
        normal_attribute.setVertexSize(3)
        normal_attribute.setCount(total_vertices)
        normal_attribute.setName(QAttribute.defaultNormalAttributeName())

        # Add attributes to geometry
        geometry.addAttribute(position_attribute)
        geometry.addAttribute(normal_attribute)

        # Create geometry renderer
        renderer = QGeometryRenderer()
        renderer.setGeometry(geometry)
        renderer.setPrimitiveType(QGeometryRenderer.Triangles)
        renderer.setVertexCount(total_vertices)

        return renderer

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
        if self.model_entity:
            self._apply_render_mode()

        self.logger.info(f"Render mode changed to: {mode.value}")

    def _apply_render_mode(self) -> None:
        """Apply the current render mode to the model."""
        if not self.model_entity:
            return

        # Get the geometry renderer
        renderer = self.model_entity.components()[0]  # First component should be the renderer

        if isinstance(renderer, QGeometryRenderer):
            if self.render_mode == RenderMode.WIREFRAME:
                renderer.setPrimitiveType(QGeometryRenderer.Lines)
            elif self.render_mode == RenderMode.POINTS:
                renderer.setPrimitiveType(QGeometryRenderer.Points)
            else:  # SOLID
                renderer.setPrimitiveType(QGeometryRenderer.Triangles)

    def _remove_current_model(self) -> None:
        """Remove the currently loaded model from the scene."""
        if self.model_entity:
            # Remove entity from parent
            if self.model_entity.parent():
                self.model_entity.parent().removeChild(self.model_entity)

            # Delete the entity
            self.model_entity.deleteLater()
            self.model_entity = None

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

        # Calculate model bounds
        center_x = (model.stats.min_bounds.x + model.stats.max_bounds.x) / 2
        center_y = (model.stats.min_bounds.y + model.stats.max_bounds.y) / 2
        center_z = (model.stats.min_bounds.z + model.stats.max_bounds.z) / 2

        # Calculate model size
        dimensions = model.stats.get_dimensions()
        max_dimension = max(dimensions)

        # Position camera to fit the model
        distance = max_dimension * 2.5  # 2.5x the max dimension

        # Set camera position and view center
        self.camera.setPosition(QVector3D(center_x, center_y, center_z + distance))
        self.camera.setViewCenter(QVector3D(center_x, center_y, center_z))

        self.logger.debug(f"Camera positioned to fit model: center=({center_x:.2f}, {center_y:.2f}, {center_z:.2f}), distance={distance:.2f}")

    @log_function_call(get_logger(__name__))
    def load_model(self, model: Model) -> bool:
        """
        Load a model into the 3D viewer with progressive loading support.

        Args:
            model: The model to load

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            self.logger.info(f"Loading model with {model.stats.triangle_count} triangles")

            # Handle progressive loading
            if hasattr(model, 'file_path') and model.file_path:
                return self._load_model_progressively(model.file_path)
            else:
                # Direct loading for models without file path
                return self._load_model_internal(model)

        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            return False

    def _load_model_progressively(self, file_path: str) -> bool:
        """
        Load a model progressively with multiple quality levels.

        Args:
            file_path: Path to the model file

        Returns:
            True if loading was initiated successfully, False otherwise
        """
        if self.loading_in_progress:
            self.logger.warning("Model loading already in progress")
            return False

        try:
            # Cancel any existing loading
            if self.progressive_loader:
                self.progressive_loader.cancel()
                self.progressive_loader.wait(1000)

            # Show progress UI
            self.progress_frame.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_label.setText("Initializing...")
            self.progress_bar.setValue(0)

            # Start progressive loading
            self.loading_in_progress = True
            self.progressive_loader = ProgressiveLoadWorker(file_path)
            self.progressive_loader.progress_updated.connect(self._on_loading_progress)
            self.progressive_loader.model_ready.connect(self._on_model_ready)
            self.progressive_loader.loading_complete.connect(self._on_loading_complete)
            self.progressive_loader.error_occurred.connect(self._on_loading_error)
            self.progressive_loader.start()

            self.logger.info(f"Started progressive loading: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start progressive loading: {str(e)}")
            self._hide_progress_ui()
            return False

    def _load_model_internal(self, model: Model) -> bool:
        """
        Internal method to load a model into the 3D viewer.

        Args:
            model: The model to load

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Remove any existing model
            self._remove_current_model()

            # Store reference to the model
            self.current_model = model

            # Create geometry renderer from model data
            geometry_renderer = self._create_stl_geometry(model)

            # Create material for the model
            material = QPhongMaterial()
            material.setDiffuse(get_theme_color('model_surface'))
            material.setAmbient(get_theme_color('model_ambient'))
            material.setSpecular(get_theme_color('model_specular'))
            material.setShininess(100.0)

            # Create transform
            transform = QTransform()

            # Create entity for the model
            self.model_entity = QEntity(self.root_entity)
            self.model_entity.addComponent(geometry_renderer)
            self.model_entity.addComponent(material)
            self.model_entity.addComponent(transform)

            # Hide default scene
            if hasattr(self, 'default_entity'):
                self.default_entity.setEnabled(False)

            # Apply current render mode
            self._apply_render_mode()

            # Fit camera to model
            self._fit_camera_to_model(model)

            # Update loading state
            if hasattr(model, 'loading_state'):
                self.current_loading_quality = model.loading_state

            # Emit signal
            self.model_loaded.emit(f"Model with {model.stats.triangle_count} triangles")

            self.logger.info(f"Model loaded successfully: {model.stats.triangle_count} triangles, {model.stats.vertex_count} vertices")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            return False

    def _on_loading_progress(self, progress: float, message: str) -> None:
        """
        Handle loading progress updates.

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
        self.loading_progress_updated.emit(progress, message)

    def _on_model_ready(self, model: Model) -> None:
        """
        Handle model ready signal from progressive loader.

        Args:
            model: The loaded model
        """
        # Load the model
        if self._load_model_internal(model):
            # Update loading state
            if hasattr(model, 'loading_state'):
                self.current_loading_quality = model.loading_state

                # Request higher quality if needed
                if (model.loading_state == LoadingState.METADATA_ONLY and
                    self.adaptive_quality and
                    model.stats.triangle_count <= self.max_triangles_for_full_quality):
                    self.logger.info("Requesting higher quality model")
                    # The progressive loader will automatically provide higher quality

    def _on_loading_complete(self) -> None:
        """Handle loading completion."""
        self.loading_in_progress = False
        self._hide_progress_ui()

        # Clean up loader
        if self.progressive_loader:
            self.progressive_loader.deleteLater()
            self.progressive_loader = None

        self.logger.info("Progressive loading completed")

    def _on_loading_error(self, error_message: str) -> None:
        """
        Handle loading errors.

        Args:
            error_message: Error message
        """
        self.logger.error(f"Loading error: {error_message}")
        self.loading_in_progress = False
        self._hide_progress_ui()

        # Clean up loader
        if self.progressive_loader:
            self.progressive_loader.deleteLater()
            self.progressive_loader = None

    def _hide_progress_ui(self) -> None:
        """Hide the progress UI elements."""
        self.progress_frame.setVisible(False)
        self.progress_bar.setVisible(False)

    @log_function_call(get_logger(__name__))
    def clear_scene(self) -> None:
        """Clear the 3D scene and show default object."""
        self.logger.info("Clearing 3D scene")

        # Remove current model
        self._remove_current_model()

        # Show default scene
        if hasattr(self, 'default_entity'):
            self.default_entity.setEnabled(True)

        # Reset camera
        self.reset_view()

        self.logger.info("3D scene cleared")

    @log_function_call(get_logger(__name__))
    def reset_view(self) -> None:
        """Reset the camera view to default position."""
        self.logger.debug("Resetting camera view")

        if self.current_model:
            # Fit camera to current model
            self._fit_camera_to_model(self.current_model)
        else:
            # Reset to default position
            self.camera.setPosition(QVector3D(0, 0, 20))
            self.camera.setViewCenter(QVector3D(0, 0, 0))

        # Reset camera controller
        if hasattr(self, 'camera_controller'):
            # Reset the camera controller's internal state
            self.camera_controller.setCamera(self.camera)

    def set_light_intensity(self, intensity: float) -> None:
        """
        Set the intensity of the point light.

        Args:
            intensity: Light intensity (0.0 to 1.0)
        """
        intensity = max(0.0, min(1.0, intensity))
        self.point_light.setIntensity(intensity)
        self.logger.debug(f"Light intensity set to: {intensity}")

    def set_light_position(self, x: float, y: float, z: float) -> None:
        """
        Set the position of the point light.

        Args:
            x, y, z: Light position coordinates
        """
        self.point_light_transform.setTranslation(QVector3D(x, y, z))
        self.logger.debug(f"Light position set to: ({x:.2f}, {y:.2f}, {z:.2f})")

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
        self.logger.info("Cleaning up 3D viewer resources")

        # Stop progressive loading
        if self.progressive_loader:
            self.progressive_loader.cancel()
            self.progressive_loader.wait(2000)

        # Stop performance timer
        if hasattr(self, 'performance_timer'):
            self.performance_timer.stop()

        # Remove current model
        self._remove_current_model()

        # Clean up 3D resources
        if hasattr(self, 'view'):
            self.view.setRootEntity(None)

        # Force garbage collection
        gc.collect()

        self.logger.info("3D viewer cleanup completed")

    def apply_theme(self) -> None:
        """
        Reapply themed styling for the PyQt3D viewer:
        - Update canvas clear color
        - Refresh QSS for framed viewer container, control panel, buttons, and progress bar
        Safe to call multiple times.
        """
        try:
            # Update canvas background color
            if hasattr(self, "view"):
                self.view.defaultFrameGraph().setClearColor(get_theme_color('canvas_bg'))
            # Material Design theme is applied globally via ThemeService
            # No need to apply hardcoded stylesheets here
        except Exception:
            # Fail-safe: do not break UI due to theme update
            pass

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)


# Import required Qt3D classes
# QVector3D is already imported at the top of the file
