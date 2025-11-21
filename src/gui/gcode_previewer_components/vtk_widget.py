"""VTK Widget - Qt integration for VTK rendering with advanced camera controls."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QStyle,
    QSizePolicy,
)
from PySide6.QtGui import QMouseEvent, QWheelEvent, QIcon, QShowEvent
from PySide6.QtCore import QTimer

from .gcode_renderer import GcodeRenderer
from .camera_controller import CameraController


class CameraControlWidget(QFrame):
    """Toolbar widget that exposes camera control buttons."""

    def __init__(
        self,
        controller: CameraController,
        render_callback: Callable[[], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._render_callback = render_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._add_button(
            layout, "Fit All", QStyle.SP_TitleBarMaxButton, controller.fit_all
        )
        self._add_button(layout, "Front", QStyle.SP_ArrowUp, controller.set_view_front)
        self._add_button(layout, "Top", QStyle.SP_ArrowDown, controller.set_view_top)
        self._add_button(layout, "Side", QStyle.SP_ArrowRight, controller.set_view_side)
        self._add_button(
            layout,
            "Isometric",
            QStyle.SP_FileDialogDetailedView,
            controller.set_view_isometric,
        )
        self._add_button(
            layout, "Reset", QStyle.SP_BrowserReload, controller.reset_camera
        )
        layout.addStretch()

    def _add_button(
        self,
        layout: QHBoxLayout,
        text: str,
        icon_type,
        callback: Callable[[], None],
    ) -> None:
        button = QPushButton(text, self)
        button.setMaximumWidth(90)
        button.setIcon(self.style().standardIcon(icon_type))
        button.clicked.connect(self._wrap(callback))
        layout.addWidget(button)

    def _wrap(self, callback: Callable[[], None]) -> Callable[[], None]:
        def _inner() -> None:
            callback()
            if self._render_callback:
                self._render_callback()

        return _inner


class VTKWidget(QWidget):
    """Qt widget for VTK rendering with advanced camera controls."""

    def __init__(
        self,
        renderer: GcodeRenderer,
        parent: Optional[QWidget] = None,
        *,
        embed_camera_toolbar: bool = True,
    ) -> None:
        """Initialize the VTK widget."""
        super().__init__(parent)

        vtk_module = renderer.vtk
        from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

        self.renderer = renderer
        self.gcode_renderer = renderer

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.vtk_widget = QVTKRenderWindowInteractor(self)
        main_layout.addWidget(self.vtk_widget)

        self.vtk_widget.GetRenderWindow().AddRenderer(renderer.get_renderer())
        self._orientation_widget = None

        interactor_style = vtk_module.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(interactor_style)
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
        # Force an initial render so the canvas is not blank until the first interaction.
        self.update_render()
        # And schedule follow-up renders once the event loop processes layout/resize.
        QTimer.singleShot(0, self.update_render)
        QTimer.singleShot(50, self.update_render)

        self.camera_controller = CameraController(renderer.get_renderer())

        self.vtk_widget.mousePressEvent = self._on_mouse_press
        self.vtk_widget.mouseMoveEvent = self._on_mouse_move
        self.vtk_widget.mouseReleaseEvent = self._on_mouse_release
        self.vtk_widget.wheelEvent = self._on_wheel

        self._inline_toolbar: Optional[CameraControlWidget] = None
        if embed_camera_toolbar:
            self._inline_toolbar = self.create_camera_toolbar(self)
            main_layout.insertWidget(0, self._inline_toolbar)

        self._init_orientation_marker()
        # Kick a first render once the event loop is running so the background
        # is painted even before the user interacts.
        QTimer.singleShot(0, self.update_render)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # Render immediately and schedule a repeat after the event queue settles.
        self.update_render()
        QTimer.singleShot(0, self.update_render)
        QTimer.singleShot(50, self.update_render)

    def _std_icon(self, standard_pixmap) -> QIcon:
        style = self.style()
        return style.standardIcon(standard_pixmap)

    def create_camera_toolbar(
        self, parent: Optional[QWidget] = None
    ) -> CameraControlWidget:
        """Return a toolbar widget wired to the current camera controller."""
        return CameraControlWidget(self.camera_controller, self.update_render, parent)

    def set_toolbar_visible(self, visible: bool) -> None:
        if self._inline_toolbar is not None:
            self._inline_toolbar.setVisible(visible)

    def _on_mouse_press(self, event: QMouseEvent) -> None:
        self.camera_controller.handle_mouse_press(event)

    def _on_mouse_move(self, event: QMouseEvent) -> None:
        viewport_size = (self.vtk_widget.width(), self.vtk_widget.height())
        self.camera_controller.handle_mouse_move(event, viewport_size)
        self.update_render()

    def _on_mouse_release(self, event: QMouseEvent) -> None:
        self.camera_controller.handle_mouse_release(event)

    def _on_wheel(self, event: QWheelEvent) -> None:
        self.camera_controller.handle_wheel(event)
        self.update_render()

    def update_render(self) -> None:
        self.vtk_widget.GetRenderWindow().Render()

    def reset_camera(self) -> None:
        self.camera_controller.reset_camera()
        self.update_render()

    def fit_all(self) -> None:
        self.camera_controller.fit_all()
        self.update_render()

    def set_view_front(self) -> None:
        self.camera_controller.set_view_front()
        self.update_render()

    def set_view_top(self) -> None:
        self.camera_controller.set_view_top()
        self.update_render()

    def set_view_side(self) -> None:
        self.camera_controller.set_view_side()
        self.update_render()

    def set_view_isometric(self) -> None:
        self.camera_controller.set_view_isometric()
        self.update_render()

    def _init_orientation_marker(self) -> None:
        """Add a corner orientation marker similar to the model viewer."""
        try:
            vtk = self.gcode_renderer.vtk
            axes = vtk.vtkAxesActor()
            axes.SetTotalLength(12, 12, 12)
            widget = vtk.vtkOrientationMarkerWidget()
            widget.SetOrientationMarker(axes)
            widget.SetInteractor(self.vtk_widget.GetInteractor())
            widget.EnabledOn()
            widget.InteractiveOff()
            widget.SetViewport(0.8, 0.8, 1.0, 1.0)
            self._orientation_widget = widget
        except Exception:
            self._orientation_widget = None
