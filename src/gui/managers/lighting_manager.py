"""
Lighting Manager for MainWindow.

Handles lighting settings, material properties, and lighting panel management.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow


class LightingManager:
    """Manages lighting settings and lighting panel."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the lighting manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger
        self.lighting_manager = None
        self.lighting_panel = None

    def setup_lighting(self) -> None:
        """Set up lighting manager and control panel."""
        self._setup_lighting_manager()
        self._setup_lighting_panel()
        self._load_lighting_settings()

    def _setup_lighting_manager(self) -> None:
        """Initialize the VTK lighting manager."""
        try:
            from src.gui.lighting_control_panel import LightingManager as VTKLightingManager

            renderer = getattr(self.main_window.viewer_widget, "renderer", None)
            if renderer:
                self.lighting_manager = VTKLightingManager(renderer)
                self.lighting_manager.create_light()
                self.main_window.lighting_manager = self.lighting_manager
                self.logger.info("VTK Lighting manager created")
            else:
                self.logger.warning("No renderer available for lighting manager")
        except Exception as e:
            self.logger.warning("Failed to create lighting manager: %s", e)

    def _setup_lighting_panel(self) -> None:
        """Create and configure the lighting control panel."""
        try:
            from src.gui.lighting_control_panel import LightingControlPanel

            self.lighting_panel = LightingControlPanel(self.main_window)
            self.lighting_panel.setObjectName("LightingDialog")
            self.lighting_panel.hide()
            self.main_window.lighting_panel = self.lighting_panel

            # Connect signals
            if self.lighting_manager:
                self.lighting_panel.position_changed.connect(self._on_position_changed)
                self.lighting_panel.color_changed.connect(self._on_color_changed)
                self.lighting_panel.intensity_changed.connect(self._on_intensity_changed)
                self.lighting_panel.cone_angle_changed.connect(self._on_cone_angle_changed)

                # Initialize panel with current properties
                props = self.lighting_manager.get_properties()
                self.lighting_panel.set_values(
                    position=tuple(props.get("position", (100.0, 100.0, 100.0))),
                    color=tuple(props.get("color", (1.0, 1.0, 1.0))),
                    intensity=float(props.get("intensity", 0.8)),
                    cone_angle=float(props.get("cone_angle", 30.0)),
                    emit_signals=False,
                )

            self.logger.info("Lighting control panel created")
        except Exception as e:
            self.logger.warning("Failed to create lighting panel: %s", e)

    def _load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings."""
        try:
            settings = QSettings()
            if not settings.contains("lighting/position_x"):
                return

            pos_x = settings.value("lighting/position_x", 90.0, type=float)
            pos_y = settings.value("lighting/position_y", 90.0, type=float)
            pos_z = settings.value("lighting/position_z", 180.0, type=float)
            col_r = settings.value("lighting/color_r", 1.0, type=float)
            col_g = settings.value("lighting/color_g", 1.0, type=float)
            col_b = settings.value("lighting/color_b", 1.0, type=float)
            intensity = settings.value("lighting/intensity", 1.2, type=float)
            cone_angle = settings.value("lighting/cone_angle", 90.0, type=float)

            props = {
                "position": (float(pos_x), float(pos_y), float(pos_z)),
                "color": (float(col_r), float(col_g), float(col_b)),
                "intensity": float(intensity),
                "cone_angle": float(cone_angle),
            }

            if self.lighting_manager:
                self.lighting_manager.apply_properties(props)

            if self.lighting_panel:
                self.lighting_panel.set_values(
                    position=props["position"],
                    color=props["color"],
                    intensity=props["intensity"],
                    cone_angle=props["cone_angle"],
                    emit_signals=False,
                )

            self.logger.info("Lighting settings loaded")
        except Exception as e:
            self.logger.warning("Failed to load lighting settings: %s", e)

    def _save_lighting_settings(self) -> None:
        """Save current lighting settings to QSettings."""
        try:
            if not self.lighting_manager:
                return

            settings = QSettings()
            props = self.lighting_manager.get_properties()

            settings.setValue("lighting/position_x", float(props["position"][0]))
            settings.setValue("lighting/position_y", float(props["position"][1]))
            settings.setValue("lighting/position_z", float(props["position"][2]))
            settings.setValue("lighting/color_r", float(props["color"][0]))
            settings.setValue("lighting/color_g", float(props["color"][1]))
            settings.setValue("lighting/color_b", float(props["color"][2]))
            settings.setValue("lighting/intensity", float(props["intensity"]))
            settings.setValue("lighting/cone_angle", float(props["cone_angle"]))
            settings.sync()

            self.logger.debug("Lighting settings saved")
        except Exception as e:
            self.logger.warning("Failed to save lighting settings: %s", e)

    def toggle_lighting_panel(self) -> None:
        """Toggle the lighting control panel visibility."""
        try:
            if not self.lighting_panel:
                self.logger.warning("Lighting panel not available")
                return

            if self.lighting_panel.isVisible():
                self.lighting_panel.hide()
            else:
                self.lighting_panel.show()
                self.lighting_panel.raise_()
                self.lighting_panel.activateWindow()

            self.logger.debug("Lighting panel toggled")
        except Exception as e:
            self.logger.warning("Failed to toggle lighting panel: %s", e)

    def _on_position_changed(self, x: float, y: float, z: float) -> None:
        """Handle light position change."""
        try:
            if self.lighting_manager:
                self.lighting_manager.update_position(x, y, z)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning("Failed to update light position: %s", e)

    def _on_color_changed(self, r: float, g: float, b: float) -> None:
        """Handle light color change."""
        try:
            if self.lighting_manager:
                self.lighting_manager.update_color(r, g, b)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning("Failed to update light color: %s", e)

    def _on_intensity_changed(self, value: float) -> None:
        """Handle light intensity change."""
        try:
            if self.lighting_manager:
                self.lighting_manager.update_intensity(value)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning("Failed to update light intensity: %s", e)

    def _on_cone_angle_changed(self, angle: float) -> None:
        """Handle light cone angle change."""
        try:
            if self.lighting_manager:
                self.lighting_manager.update_cone_angle(angle)
                self._save_lighting_settings()
        except Exception as e:
            self.logger.warning("Failed to update light cone angle: %s", e)

    def apply_material_species(self, species_name: str) -> None:
        """Apply selected material species to the current model."""
        try:
            if not species_name:
                return

            if (
                hasattr(self.main_window, "material_lighting_integrator")
                and self.main_window.material_lighting_integrator
            ):
                self.main_window.material_lighting_integrator.apply_material_species(species_name)
            else:
                self.logger.warning("MaterialLightingIntegrator not available")
        except Exception as e:
            self.logger.error(f"Failed to apply material species '{species_name}': {e}")
