"""
UI management for 3D viewer.

Handles UI layout, controls, and theme application.
"""

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QLabel,
    QFrame,
)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.core.logging_config import get_logger, log_function_call


logger = get_logger(__name__)


class ViewerUIManager:
    """Manages the viewer UI layout and controls."""

    def __init__(self, parent_widget: QWidget):
        """
        Initialize UI manager.

        Args:
            parent_widget: Parent widget
        """
        self.parent_widget = parent_widget
        self.vtk_widget = None
        self.viewer_frame = None
        self.solid_button = None
        self.material_button = None
        self.lighting_button = None
        self.grid_button = None
        self.reset_button = None
        self.save_view_button = None
        self.rotate_ccw_button = None
        self.rotate_cw_button = None
        self.set_z_up_button = None
        self.progress_bar = None
        self.progress_label = None
        self.progress_frame = None

    @log_function_call(logger)
    def setup_ui(
        self,
        on_solid_clicked: Callable,
        on_material_clicked: Callable,
        on_lighting_clicked: Callable,
        on_reset_clicked: Callable,
        on_save_view_clicked: Callable,
        on_rotate_ccw_clicked: Callable,
        on_rotate_cw_clicked: Callable,
        on_set_z_up_clicked: Callable = None,
        on_rotate_x_pos: Callable = None,
        on_rotate_x_neg: Callable = None,
        on_rotate_y_pos: Callable = None,
        on_rotate_y_neg: Callable = None,
        on_rotate_z_pos: Callable = None,
        on_rotate_z_neg: Callable = None,
    ) -> None:
        """
        Set up the UI layout.

        Args:
            on_solid_clicked: Callback for solid button
            on_material_clicked: Callback for material button
            on_lighting_clicked: Callback for lighting button
            on_reset_clicked: Callback for reset button
            on_save_view_clicked: Callback for save view button
            on_rotate_ccw_clicked: Callback for rotate CCW button (view rotation)
            on_rotate_cw_clicked: Callback for rotate CW button (view rotation)
            on_set_z_up_clicked: Callback for set Z up button
            on_rotate_x_pos: Callback for rotate +X button
            on_rotate_x_neg: Callback for rotate -X button
            on_rotate_y_pos: Callback for rotate +Y button
            on_rotate_y_neg: Callback for rotate -Y button
            on_rotate_z_pos: Callback for rotate +Z button
            on_rotate_z_neg: Callback for rotate -Z button
        """
        layout = QVBoxLayout(self.parent_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self.parent_widget)

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

        # Solid button
        self.solid_button = QPushButton("Solid")
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)
        self.solid_button.clicked.connect(on_solid_clicked)
        control_layout.addWidget(self.solid_button)

        # Material button
        self.material_button = QPushButton("Material")
        self.material_button.setCheckable(False)
        self.material_button.clicked.connect(on_material_clicked)
        control_layout.addWidget(self.material_button)

        # Lighting button
        self.lighting_button = QPushButton("Lighting")
        self.lighting_button.setCheckable(False)
        self.lighting_button.clicked.connect(on_lighting_clicked)
        control_layout.addWidget(self.lighting_button)

        # Grid and Ground buttons removed - these settings are now managed in preferences dialog only

        # Reset view button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(on_reset_clicked)
        control_layout.addWidget(self.reset_button)

        # Save view button
        self.save_view_button = QPushButton("Save View")
        self.save_view_button.clicked.connect(on_save_view_clicked)
        control_layout.addWidget(self.save_view_button)

        # Rotate buttons
        self.rotate_ccw_button = QPushButton("↺ 90°")
        self.rotate_ccw_button.setToolTip("Rotate 90° counter-clockwise")
        self.rotate_ccw_button.clicked.connect(on_rotate_ccw_clicked)
        control_layout.addWidget(self.rotate_ccw_button)

        self.rotate_cw_button = QPushButton("↻ 90°")
        self.rotate_cw_button.setToolTip("Rotate view 90° clockwise")
        self.rotate_cw_button.clicked.connect(on_rotate_cw_clicked)
        control_layout.addWidget(self.rotate_cw_button)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        control_layout.addWidget(separator)

        # Model rotation buttons (rotate geometry, not view)
        # X-axis rotations
        if on_rotate_x_pos:
            self.rotate_x_pos_button = QPushButton("X+")
            self.rotate_x_pos_button.setToolTip("Rotate model +90° around X axis")
            self.rotate_x_pos_button.setMaximumWidth(40)
            self.rotate_x_pos_button.clicked.connect(on_rotate_x_pos)
            control_layout.addWidget(self.rotate_x_pos_button)

        if on_rotate_x_neg:
            self.rotate_x_neg_button = QPushButton("X-")
            self.rotate_x_neg_button.setToolTip("Rotate model -90° around X axis")
            self.rotate_x_neg_button.setMaximumWidth(40)
            self.rotate_x_neg_button.clicked.connect(on_rotate_x_neg)
            control_layout.addWidget(self.rotate_x_neg_button)

        # Y-axis rotations
        if on_rotate_y_pos:
            self.rotate_y_pos_button = QPushButton("Y+")
            self.rotate_y_pos_button.setToolTip("Rotate model +90° around Y axis")
            self.rotate_y_pos_button.setMaximumWidth(40)
            self.rotate_y_pos_button.clicked.connect(on_rotate_y_pos)
            control_layout.addWidget(self.rotate_y_pos_button)

        if on_rotate_y_neg:
            self.rotate_y_neg_button = QPushButton("Y-")
            self.rotate_y_neg_button.setToolTip("Rotate model -90° around Y axis")
            self.rotate_y_neg_button.setMaximumWidth(40)
            self.rotate_y_neg_button.clicked.connect(on_rotate_y_neg)
            control_layout.addWidget(self.rotate_y_neg_button)

        # Z-axis rotations
        if on_rotate_z_pos:
            self.rotate_z_pos_button = QPushButton("Z+")
            self.rotate_z_pos_button.setToolTip("Rotate model +90° around Z axis")
            self.rotate_z_pos_button.setMaximumWidth(40)
            self.rotate_z_pos_button.clicked.connect(on_rotate_z_pos)
            control_layout.addWidget(self.rotate_z_pos_button)

        if on_rotate_z_neg:
            self.rotate_z_neg_button = QPushButton("Z-")
            self.rotate_z_neg_button.setToolTip("Rotate model -90° around Z axis")
            self.rotate_z_neg_button.setMaximumWidth(40)
            self.rotate_z_neg_button.clicked.connect(on_rotate_z_neg)
            control_layout.addWidget(self.rotate_z_neg_button)

        control_layout.addStretch()

        # Set Z Up button (far right)
        self.set_z_up_button = QPushButton("Set Z Up")
        self.set_z_up_button.setToolTip("Rotate model to set Z-axis pointing up")
        if on_set_z_up_clicked:
            self.set_z_up_button.clicked.connect(on_set_z_up_clicked)
        control_layout.addWidget(self.set_z_up_button)

        layout.addWidget(control_panel)

        # Create progress bar
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

        logger.debug("UI setup completed")

    def show_progress(self, visible: bool = True) -> None:
        """Show or hide progress bar."""
        if self.progress_frame:
            self.progress_frame.setVisible(visible)

    def update_progress(self, value: float, message: str = "") -> None:
        """
        Update progress bar.

        Args:
            value: Progress value (0-100)
            message: Progress message
        """
        if self.progress_bar:
            self.progress_bar.setValue(int(value))
        if self.progress_label and message:
            self.progress_label.setText(message)

    def apply_theme(self) -> None:
        """Apply theme styling."""
        try:
            # Material Design theme is applied globally via ThemeService
            logger.debug("Theme applied")
        except Exception as e:
            logger.error("Failed to apply theme: %s", e)

    def get_vtk_widget(self) -> Optional[QVTKRenderWindowInteractor]:
        """Get the VTK widget."""
        return self.vtk_widget

    def reset_save_view_button(self) -> None:
        """Reset save view button state."""
        if self.save_view_button:
            self.save_view_button.setChecked(False)

    # Grid and Ground button state update methods removed - these buttons are no longer in the UI
    # Grid and floor plane settings are now managed exclusively through the preferences dialog
