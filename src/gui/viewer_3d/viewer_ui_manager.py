"""
UI management for 3D viewer.

Handles UI layout, controls, and theme application.
"""

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QLabel, QFrame
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
        on_grid_clicked: Callable,
        on_reset_clicked: Callable,
        on_save_view_clicked: Callable,
        on_rotate_ccw_clicked: Callable,
        on_rotate_cw_clicked: Callable,
        on_ground_clicked: Callable = None,
        on_set_z_up_clicked: Callable = None
    ) -> None:
        """
        Set up the UI layout.

        Args:
            on_solid_clicked: Callback for solid button
            on_material_clicked: Callback for material button
            on_lighting_clicked: Callback for lighting button
            on_grid_clicked: Callback for grid button
            on_ground_clicked: Callback for ground plane button
            on_reset_clicked: Callback for reset button
            on_save_view_clicked: Callback for save view button
            on_rotate_ccw_clicked: Callback for rotate CCW button
            on_rotate_cw_clicked: Callback for rotate CW button
            on_set_z_up_clicked: Callback for set Z up button
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

        # Grid button
        self.grid_button = QPushButton("Grid")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(True)
        self.grid_button.clicked.connect(on_grid_clicked)
        control_layout.addWidget(self.grid_button)

        # Ground plane button
        if on_ground_clicked:
            self.ground_button = QPushButton("Ground")
            self.ground_button.setCheckable(True)
            self.ground_button.setChecked(True)
            self.ground_button.clicked.connect(on_ground_clicked)
            control_layout.addWidget(self.ground_button)

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
        self.rotate_cw_button.setToolTip("Rotate 90° clockwise")
        self.rotate_cw_button.clicked.connect(on_rotate_cw_clicked)
        control_layout.addWidget(self.rotate_cw_button)

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
            logger.error(f"Failed to apply theme: {e}")

    def get_vtk_widget(self) -> Optional[QVTKRenderWindowInteractor]:
        """Get the VTK widget."""
        return self.vtk_widget

    def reset_save_view_button(self) -> None:
        """Reset save view button state."""
        if self.save_view_button:
            self.save_view_button.setChecked(False)

    def update_grid_button_state(self, is_visible: bool) -> None:
        """Update grid button appearance based on visibility state."""
        if self.grid_button:
            self.grid_button.setChecked(is_visible)
            self._update_toggle_button_appearance(self.grid_button, is_visible)

    def update_ground_button_state(self, is_visible: bool) -> None:
        """Update ground button appearance based on visibility state."""
        if hasattr(self, 'ground_button') and self.ground_button:
            self.ground_button.setChecked(is_visible)
            self._update_toggle_button_appearance(self.ground_button, is_visible)

    def _update_toggle_button_appearance(self, button: QPushButton, is_active: bool) -> None:
        """
        Update button appearance to show subdued state when inactive.

        Args:
            button: The button to update
            is_active: Whether the button is in active state
        """
        if is_active:
            # Active state - bright and visible
            button.setStyleSheet("")  # Reset to default theme
        else:
            # Inactive state - subdued appearance
            button.setStyleSheet("""
                QPushButton {
                    opacity: 0.6;
                    color: #888888;
                }
                QPushButton:hover {
                    opacity: 0.8;
                }
            """)

