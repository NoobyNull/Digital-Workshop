"""VTK Widget - Qt integration for VTK rendering with advanced camera controls."""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QMouseEvent, QWheelEvent

from .gcode_renderer import GcodeRenderer
from .camera_controller import CameraController

# Defer VTK imports to avoid initialization issues
vtk = None
QVTKRenderWindowInteractor = None


class VTKWidget(QWidget):
    """Qt widget for VTK rendering with advanced camera controls."""

    def __init__(self, renderer: GcodeRenderer, parent: Optional[QWidget] = None):
        """Initialize the VTK widget."""
        super().__init__(parent)

        global vtk, QVTKRenderWindowInteractor
        if vtk is None:
            import vtk as vtk_module
            from vtk.qt.QVTKRenderWindowInteractor import (
                QVTKRenderWindowInteractor as QVTKInteractor,
            )

            vtk = vtk_module
            QVTKRenderWindowInteractor = QVTKInteractor

        self.renderer = renderer
        self.gcode_renderer = renderer

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create VTK interactor
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        main_layout.addWidget(self.vtk_widget)

        # Connect renderer to interactor
        self.vtk_widget.GetRenderWindow().AddRenderer(renderer.get_renderer())

        # Setup interactor style (custom trackball)
        interactor_style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(interactor_style)

        # Initialize interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

        # Create camera controller
        self.camera_controller = CameraController(renderer.get_renderer())

        # Connect mouse events
        self.vtk_widget.mousePressEvent = self._on_mouse_press
        self.vtk_widget.mouseMoveEvent = self._on_mouse_move
        self.vtk_widget.mouseReleaseEvent = self._on_mouse_release
        self.vtk_widget.wheelEvent = self._on_wheel

        # Create camera control toolbar
        self._create_camera_toolbar(main_layout)

    def _create_camera_toolbar(self, parent_layout: QVBoxLayout) -> None:
        """Create toolbar with camera control buttons."""
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(4, 4, 4, 4)
        toolbar_layout.setSpacing(4)

        # View buttons
        btn_fit = QPushButton("Fit All")
        btn_fit.setMaximumWidth(80)
        btn_fit.clicked.connect(self.fit_all)
        toolbar_layout.addWidget(btn_fit)

        btn_front = QPushButton("Front")
        btn_front.setMaximumWidth(60)
        btn_front.clicked.connect(self.set_view_front)
        toolbar_layout.addWidget(btn_front)

        btn_top = QPushButton("Top")
        btn_top.setMaximumWidth(60)
        btn_top.clicked.connect(self.set_view_top)
        toolbar_layout.addWidget(btn_top)

        btn_side = QPushButton("Side")
        btn_side.setMaximumWidth(60)
        btn_side.clicked.connect(self.set_view_side)
        toolbar_layout.addWidget(btn_side)

        btn_iso = QPushButton("Isometric")
        btn_iso.setMaximumWidth(80)
        btn_iso.clicked.connect(self.set_view_isometric)
        toolbar_layout.addWidget(btn_iso)

        btn_reset = QPushButton("Reset")
        btn_reset.setMaximumWidth(60)
        btn_reset.clicked.connect(self.reset_camera)
        toolbar_layout.addWidget(btn_reset)

        toolbar_layout.addStretch()
        parent_layout.addWidget(toolbar)

    def _on_mouse_press(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        self.camera_controller.handle_mouse_press(event)
        # QVTKRenderWindowInteractor handles events automatically, no need to call OnLeftButtonDown

    def _on_mouse_move(self, event: QMouseEvent) -> None:
        """Handle mouse move."""
        viewport_size = (self.vtk_widget.width(), self.vtk_widget.height())
        self.camera_controller.handle_mouse_move(event, viewport_size)
        self.update_render()

    def _on_mouse_release(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        self.camera_controller.handle_mouse_release(event)
        # QVTKRenderWindowInteractor handles events automatically

    def _on_wheel(self, event: QWheelEvent) -> None:
        """Handle mouse wheel."""
        self.camera_controller.handle_wheel(event)
        self.update_render()

    def update_render(self) -> None:
        """Update the VTK render."""
        self.vtk_widget.GetRenderWindow().Render()

    def reset_camera(self) -> None:
        """Reset camera to fit all actors."""
        self.camera_controller.reset_camera()
        self.update_render()

    def fit_all(self) -> None:
        """Fit all actors in view."""
        self.camera_controller.fit_all()
        self.update_render()

    def set_view_front(self) -> None:
        """Set camera to front view."""
        self.camera_controller.set_view_front()
        self.update_render()

    def set_view_top(self) -> None:
        """Set camera to top view."""
        self.camera_controller.set_view_top()
        self.update_render()

    def set_view_side(self) -> None:
        """Set camera to side view."""
        self.camera_controller.set_view_side()
        self.update_render()

    def set_view_isometric(self) -> None:
        """Set camera to isometric view."""
        self.camera_controller.set_view_isometric()
        self.update_render()
