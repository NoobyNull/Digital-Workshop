"""Model Viewer controller for MainWindow.

Encapsulates 3D viewer setup, model loading from the library,
status/progress updates, and camera restore logic so that the
MainWindow remains a thin orchestrator.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QMessageBox

from src.core.database_manager import get_database_manager
from src.core.model_recent_service import record_model_access

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from src.gui.main_window import MainWindow


class ModelViewerController:
    """Controller responsible for Model Viewer integration."""

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        # Reuse the main window logger to keep logging consistent
        self.logger = main_window.logger

    # ------------------------------------------------------------------
    # Viewer setup
    # ------------------------------------------------------------------
    def setup_viewer_widget(self) -> None:
        """Set up the 3D viewer widget and add it as the primary hero tab."""
        try:
            # Try to load the VTK-based viewer widget first
            try:
                from src.gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                try:
                    from src.gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None

            if Viewer3DWidget is not None:
                self.main_window.viewer_widget = Viewer3DWidget(self.main_window)
                self.logger.info("3D viewer widget created successfully")
            else:
                # Native Qt fallback
                self.main_window.viewer_widget = QLabel("3D Viewer not available")
                self.main_window.viewer_widget.setAlignment(Qt.AlignCenter)
                self.logger.warning("Viewer3DWidget not available, using native Qt placeholder")

            # Connect viewer signals
            if hasattr(self.main_window.viewer_widget, "model_loaded"):
                self.main_window.viewer_widget.model_loaded.connect(
                    self.main_window._on_model_loaded
                )

            # Set up viewer-related managers (lighting, materials, etc.)
            self._setup_viewer_managers()

            # Connect lighting panel signal after managers are set up
            if hasattr(self.main_window.viewer_widget, "lighting_panel_requested"):
                self.main_window.viewer_widget.lighting_panel_requested.connect(
                    self.main_window._toggle_lighting_panel
                )
                self.logger.info("Lighting panel signal connected to main window")

        except Exception as e:  # pragma: no cover - defensive fallback
            self.logger.warning("Failed to setup viewer widget: %s", e)
            # Native Qt fallback
            self.main_window.viewer_widget = QLabel("3D Model Viewer\n\nComponent unavailable.")
            self.main_window.viewer_widget.setAlignment(Qt.AlignCenter)

        # Always add the viewer widget as the first hero tab
        self.main_window.hero_tabs.addTab(self.main_window.viewer_widget, "Model Previewer")

    def _setup_viewer_managers(self) -> None:
        """Set up viewer-related managers using native Qt integration."""
        try:
            from src.core.database_manager import get_database_manager
            from src.gui.material_manager import MaterialManager
            from src.gui.lighting_manager import LightingManager

            # Material manager
            try:
                self.main_window.material_manager = MaterialManager(get_database_manager())
            except Exception as e:  # pragma: no cover - defensive
                self.main_window.material_manager = None
                self.logger.warning("MaterialManager unavailable: %s", e)

            # Lighting manager
            try:
                renderer = getattr(self.main_window.viewer_widget, "renderer", None)
                self.main_window.lighting_manager = LightingManager(renderer) if renderer else None
                if self.main_window.lighting_manager:
                    self.main_window.lighting_manager.create_light()
            except Exception as e:  # pragma: no cover - defensive
                self.main_window.lighting_manager = None
                self.logger.warning("LightingManager unavailable: %s", e)

            # Create lighting control panel
            try:
                from src.gui.lighting_control_panel import LightingControlPanel

                self.main_window.lighting_panel = LightingControlPanel(self.main_window)
                self.main_window.lighting_panel.setObjectName("LightingDialog")
                self.main_window.lighting_panel.hide()
                self.logger.info("Lighting control panel created as floating dialog")

                # Connect lighting panel signals to main window handlers
                if self.main_window.lighting_manager:
                    self.main_window.lighting_panel.position_changed.connect(
                        self.main_window._update_light_position
                    )
                    self.main_window.lighting_panel.color_changed.connect(
                        self.main_window._update_light_color
                    )
                    self.main_window.lighting_panel.intensity_changed.connect(
                        self.main_window._update_light_intensity
                    )
                    self.main_window.lighting_panel.cone_angle_changed.connect(
                        self.main_window._update_light_cone_angle
                    )
            except Exception as e:  # pragma: no cover - defensive
                self.main_window.lighting_panel = None
                self.logger.warning("Failed to create LightingControlPanel: %s", e)

            # Material-Lighting integration
            try:
                from src.gui.materials.integration import MaterialLightingIntegrator

                self.main_window.material_lighting_integrator = MaterialLightingIntegrator(
                    self.main_window
                )
                self.logger.info("MaterialLightingIntegrator created successfully")
            except Exception as e:  # pragma: no cover - defensive
                self.main_window.material_lighting_integrator = None
                self.logger.warning("MaterialLightingIntegrator unavailable: %s", e)

        except Exception as e:  # pragma: no cover - defensive
            self.logger.warning("Failed to setup viewer managers: %s", e)

    # ------------------------------------------------------------------
    # Model loading and camera restore
    # ------------------------------------------------------------------
    def on_model_double_clicked(self, model_id: int) -> None:
        """Handle model double-click from the model library."""
        try:
            db_manager = get_database_manager()
            model = db_manager.get_model(model_id)

            if model:
                record_model_access(model_id)
                self._refresh_recent_panel()

                file_path = model["file_path"]
                self.logger.info("Loading model from library: %s", file_path)

                filename = Path(file_path).name
                self.main_window.status_label.setText(f"Loading: {filename}")
                self.main_window.progress_bar.setVisible(True)
                self.main_window.progress_bar.setRange(0, 0)  # Indeterminate progress

                # Store model ID for save-view functionality
                self.main_window.current_model_id = model_id

                # Load the model using the shared model loader manager
                self.main_window.model_loader_manager.load_stl_model(file_path)

                # After model loads, restore saved camera orientation if available
                QTimer.singleShot(500, lambda: self.restore_saved_camera(model_id))
            else:
                self.logger.warning("Model with ID %s not found in database", model_id)

        except Exception as e:  # pragma: no cover - defensive
            self.logger.error("Failed to handle model double-click: %s", str(e))

    def restore_saved_camera(self, model_id: int) -> None:
        """Restore saved camera orientation for a model."""
        try:
            db_manager = get_database_manager()
            camera_data = db_manager.get_camera_orientation(model_id)

            if camera_data and hasattr(self.main_window.viewer_widget, "renderer"):
                camera = self.main_window.viewer_widget.renderer.GetActiveCamera()
                if camera:
                    # Restore camera position, focal point, and view up
                    camera.SetPosition(
                        camera_data["camera_position_x"],
                        camera_data["camera_position_y"],
                        camera_data["camera_position_z"],
                    )
                    camera.SetFocalPoint(
                        camera_data["camera_focal_x"],
                        camera_data["camera_focal_y"],
                        camera_data["camera_focal_z"],
                    )
                    camera.SetViewUp(
                        camera_data["camera_view_up_x"],
                        camera_data["camera_view_up_y"],
                        camera_data["camera_view_up_z"],
                    )

                    # Update clipping range and render
                    self.main_window.viewer_widget.renderer.ResetCameraClippingRange()
                    self.main_window.viewer_widget.vtk_widget.GetRenderWindow().Render()

                    self.logger.info("Restored saved camera view for model ID %s", model_id)
                    self.main_window.status_label.setText("Restored saved view")
                    QTimer.singleShot(2000, lambda: self.main_window.status_label.setText("Ready"))
            else:
                self.logger.debug("No saved camera view for model ID %s", model_id)

        except Exception as e:  # pragma: no cover - defensive
            self.logger.warning("Failed to restore saved camera: %s", e)

    def _refresh_recent_panel(self) -> None:
        """Refresh the MRU widget if it exists."""

        widget = getattr(self.main_window, "model_library_widget", None)
        if widget and hasattr(widget, "refresh_recent_models"):
            try:
                widget.refresh_recent_models()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.debug("Failed to refresh MRU panel: %s", exc)
