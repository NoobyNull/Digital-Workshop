"""Camera Controller - Advanced camera controls for VTK viewer."""

from typing import Tuple, TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent

if TYPE_CHECKING:
    pass


class CameraController:
    """Manages camera controls for VTK viewer with pan, tilt, rotate, and zoom."""

    def __init__(self, renderer) -> None:
        """Initialize camera controller.

        Args:
            renderer: VTK renderer to control
        """
        self.renderer = renderer
        self.camera = renderer.GetActiveCamera()

        # Mouse interaction state
        self.last_mouse_pos = (0, 0)
        self.is_panning = False
        self.is_rotating = False
        self.is_zooming = False

        # Camera state
        self.zoom_speed = 0.1
        self.rotation_speed = 1.0
        self.pan_speed = 0.01

        # Store initial camera state for reset
        self.initial_position = self.camera.GetPosition()
        self.initial_focal_point = self.camera.GetFocalPoint()
        self.initial_view_up = self.camera.GetViewUp()
        # Keep clipping range reasonable as the camera moves to avoid
        # near-plane clipping when zoomed in close to the toolpath.
        self._update_clipping_range()

    def _update_clipping_range(self) -> None:
        """Ensure the camera clipping range fits the visible geometry.

        VTK's default clipping range can leave geometry clipped when the
        camera is moved or zoomed aggressively. Resetting it relative to
        the current bounds keeps the toolpath fully visible.
        """
        try:
            self.renderer.ResetCameraClippingRange()
        except Exception:
            # Clipping is a visual aid only; never allow failures here to
            # break interaction.
            pass

    def handle_mouse_press(self, event: QMouseEvent) -> None:
        """Handle mouse press event."""
        self.last_mouse_pos = (event.x(), event.y())

        if event.button() == Qt.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MiddleButton:
            self.is_panning = True
        elif event.button() == Qt.RightButton:
            self.is_zooming = True

    def handle_mouse_move(self, event: QMouseEvent, viewport_size: Tuple[int, int]) -> None:
        """Handle mouse move event."""
        current_pos = (event.x(), event.y())
        delta_x = current_pos[0] - self.last_mouse_pos[0]
        delta_y = current_pos[1] - self.last_mouse_pos[1]

        if self.is_rotating:
            self._rotate_camera(delta_x, delta_y)
        elif self.is_panning:
            self._pan_camera(delta_x, delta_y, viewport_size)
        elif self.is_zooming:
            self._zoom_camera(delta_y)

        self.last_mouse_pos = current_pos

    def handle_mouse_release(self, event: QMouseEvent) -> None:
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self.is_rotating = False
        elif event.button() == Qt.MiddleButton:
            self.is_panning = False
        elif event.button() == Qt.RightButton:
            self.is_zooming = False

    def handle_wheel(self, event: QWheelEvent) -> None:
        """Handle mouse wheel event for zooming."""
        delta = event.angleDelta().y()
        self._zoom_camera(delta / 120.0)  # Normalize wheel delta

    def _rotate_camera(self, delta_x: float, delta_y: float) -> None:
        """Rotate camera around focal point."""
        # Get camera parameters
        focal_point = self.camera.GetFocalPoint()
        position = self.camera.GetPosition()

        # Calculate distance from focal point
        dx = position[0] - focal_point[0]
        dy = position[1] - focal_point[1]
        dz = position[2] - focal_point[2]

        # Convert to spherical coordinates
        radius = (dx**2 + dy**2 + dz**2) ** 0.5

        # Apply rotation
        azimuth = delta_x * self.rotation_speed
        elevation = delta_y * self.rotation_speed

        # Rotate around focal point
        self.camera.Azimuth(azimuth)
        self.camera.Elevation(elevation)
        self.camera.OrthogonalizeViewUp()

        # Keep clipping range in sync so geometry is not clipped when zoomed in
        self._update_clipping_range()

    def _pan_camera(self, delta_x: float, delta_y: float, viewport_size: Tuple[int, int]) -> None:
        """Pan camera in the view plane."""
        # Get camera parameters
        focal_point = self.camera.GetFocalPoint()
        position = self.camera.GetPosition()

        # Calculate pan vectors
        view_vector = (
            focal_point[0] - position[0],
            focal_point[1] - position[1],
            focal_point[2] - position[2],
        )

        # Get right and up vectors
        view_up = self.camera.GetViewUp()

        # Calculate pan amount based on viewport size
        pan_scale = self.pan_speed * (viewport_size[0] + viewport_size[1]) / 2.0

        # Pan in screen space
        self.camera.Pan(-delta_x * pan_scale, -delta_y * pan_scale)

    def _zoom_camera(self, delta: float) -> None:
        """Zoom camera in/out."""
        zoom_factor = 1.0 + (delta * self.zoom_speed)
        self.camera.Zoom(zoom_factor)
        self._update_clipping_range()

    def reset_camera(self) -> None:
        """Reset camera to initial state."""
        self.camera.SetPosition(self.initial_position)
        self.camera.SetFocalPoint(self.initial_focal_point)
        self.camera.SetViewUp(self.initial_view_up)
        self._update_clipping_range()

    def fit_all(self) -> None:
        """Fit all actors in view."""
        self.renderer.ResetCamera()
        self.initial_position = self.camera.GetPosition()
        self.initial_focal_point = self.camera.GetFocalPoint()
        self.initial_view_up = self.camera.GetViewUp()
        self._update_clipping_range()

    def set_view_front(self) -> None:
        """Set camera to front view."""
        self.camera.SetPosition(0, 0, 100)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 1, 0)
        self._update_clipping_range()

    def set_view_top(self) -> None:
        """Set camera to top view."""
        self.camera.SetPosition(0, 100, 0)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 0, -1)
        self._update_clipping_range()

    def set_view_side(self) -> None:
        """Set camera to side view."""
        self.camera.SetPosition(100, 0, 0)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 1, 0)
        self._update_clipping_range()

    def set_view_isometric(self) -> None:
        """Set camera to isometric view."""
        self.camera.SetPosition(100, 100, 100)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 1, 0)
        self._update_clipping_range()
