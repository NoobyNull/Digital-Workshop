"""
Material and Lighting Integration Module

This module handles the integration of materials and lighting with 3D models,
including material application, lighting controls, and MTL file parsing.

Classes:
    MaterialLightingIntegrator: Main class for managing material and lighting integration
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow

from src.core.logging_config import get_logger
from src.core.data_structures import ModelFormat


class MaterialLightingIntegrator:
    """
    Manages material and lighting integration for 3D models.

    This class handles material application, lighting controls, MTL file parsing,
    and the coordination between materials and lighting systems.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the material lighting integrator.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or get_logger(__name__)
        self._current_applied_material = None

    def toggle_lighting_panel(self) -> None:
        """Show/hide the floating lighting control dialog."""
        try:
            if hasattr(self.main_window, "lighting_panel") and self.main_window.lighting_panel:
                if self.main_window.lighting_panel.isVisible():
                    self.main_window.lighting_panel.hide()
                else:
                    self.main_window.lighting_panel.show()
                    self.main_window.lighting_panel.raise_()
                    self.main_window.lighting_panel.activateWindow()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to toggle lighting panel: %s", e)

    def update_light_position(self, x: float, y: float, z: float) -> None:
        """Update light position."""
        if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
            try:
                self.main_window.lighting_manager.update_position(x, y, z)
                self._save_lighting_settings()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("update_position failed: %s", e)

    def update_light_color(self, r: float, g: float, b: float) -> None:
        """Update light color."""
        if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
            try:
                self.main_window.lighting_manager.update_color(r, g, b)
                self._save_lighting_settings()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("update_color failed: %s", e)

    def update_light_intensity(self, value: float) -> None:
        """Update light intensity."""
        if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
            try:
                self.main_window.lighting_manager.update_intensity(value)
                self._save_lighting_settings()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("update_intensity failed: %s", e)

    def update_light_cone_angle(self, angle: float) -> None:
        """Update light cone angle."""
        if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
            try:
                self.main_window.lighting_manager.update_cone_angle(angle)
                self._save_lighting_settings()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("update_cone_angle failed: %s", e)

    def apply_material_species(self, species_name: str) -> None:
        """Apply selected material species to the current viewer actor."""
        try:
            if not species_name:
                return

            if not hasattr(self.main_window, "viewer_widget") or not getattr(
                self.main_window.viewer_widget, "actor", None
            ):
                self.logger.warning("No model loaded, cannot apply material")
                return
            if (
                not hasattr(self.main_window, "material_manager")
                or self.main_window.material_manager is None
            ):
                self.logger.warning("MaterialManager not available")
                return

            # Check if this material is already applied to prevent duplicates
            current_material = getattr(self, "_current_applied_material", None)
            if current_material == species_name:
                self.logger.debug(f"Material '{species_name}' already applied, skipping")
                return

            # Get current model to determine format
            current_model = getattr(self.main_window.viewer_widget, "current_model", None)
            if not current_model:
                self.logger.warning("No current model information available")
                return

            model_format = getattr(current_model, "format_type", None)
            if not model_format:
                self.logger.warning("Cannot determine model format")
                return

            # Get material information
            material = self.main_window.material_manager.material_provider.get_material_by_name(
                species_name
            )
            material_has_texture = (
                bool(material and material.get("texture_path")) if material else False
            )

            # Apply material based on model format
            if model_format == ModelFormat.STL:
                self.logger.info("Applying STL material")
                if not material_has_texture:
                    # STL files: Apply only material properties (colors, shininess) - no textures
                    self.apply_stl_material_properties(
                        self.main_window.viewer_widget.actor, species_name
                    )
                    if hasattr(self.main_window, "statusBar"):
                        self.main_window.statusBar().showMessage(
                            f"Applied STL material properties: {species_name}", 2000
                        )
                    self.logger.info(f"Applied STL material properties for '{species_name}'")
                else:
                    # STL files: Apply full texture without UV mapping
                    ok = self.main_window.material_manager.apply_material_to_actor(
                        self.main_window.viewer_widget.actor, species_name
                    )
                    if ok:
                        if hasattr(self.main_window, "statusBar"):
                            self.main_window.statusBar().showMessage(
                                f"Applied STL material with texture: {species_name}",
                                2000,
                            )
                        self.logger.info(f"Applied STL material with texture for '{species_name}'")
                    else:
                        if hasattr(self.main_window, "statusBar"):
                            self.main_window.statusBar().showMessage(
                                f"Failed to apply STL material: {species_name}", 3000
                            )
                        return
            else:
                # OBJ files: Apply full MTL textures with UV mapping
                ok = self.main_window.material_manager.apply_material_to_actor(
                    self.main_window.viewer_widget.actor, species_name
                )
                if ok:
                    if hasattr(self.main_window, "statusBar"):
                        self.main_window.statusBar().showMessage(
                            f"Applied OBJ material with texture: {species_name}", 2000
                        )
                    self.logger.info(f"Applied OBJ material with texture for '{species_name}'")
                else:
                    if hasattr(self.main_window, "statusBar"):
                        self.main_window.statusBar().showMessage(
                            f"Failed to apply OBJ material: {species_name}", 3000
                        )
                    return

            # Save last selected material species
            try:
                settings = QSettings()
                settings.setValue("material/last_species", species_name)
                self.logger.info("Saved last material species: %s", species_name)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as se:
                self.logger.warning("Failed to persist last material species: %s", se)

            # Track the currently applied material to prevent duplicates
            self._current_applied_material = species_name

            # Re-render
            try:
                self.main_window.viewer_widget.vtk_widget.GetRenderWindow().Render()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.warning("Failed to render after material application: %s", e)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(f"Failed to apply material '{species_name}': {e}")
            if hasattr(self.main_window, "statusBar"):
                self.main_window.statusBar().showMessage(
                    f"Error applying material: {species_name}", 3000
                )

    def apply_stl_material_properties(self, actor, species_name: str) -> None:
        """Apply MTL material properties directly to STL models using VTK approach."""
        try:
            # Get material from provider to access MTL file
            material = self.main_window.material_manager.material_provider.get_material_by_name(
                species_name
            )

            if not material or not material.get("mtl_path"):
                self.logger.warning(f"No MTL file found for STL material '{species_name}'")
                return

            # Parse MTL file directly using VTK approach
            # Convert Path object to string for file operations
            mtl_props = self.parse_mtl_direct(str(material["mtl_path"]))

            # Apply properties to VTK actor
            prop = actor.GetProperty()

            # Set material colors from MTL
            kd_color = mtl_props.get("Kd", (0.8, 0.8, 0.8))  # diffuse color
            ks_color = mtl_props.get("Ks", (0.0, 0.0, 0.0))  # specular color
            ns_value = mtl_props.get("Ns", 10.0)  # shininess
            d_value = mtl_props.get("d", 1.0)  # opacity

            # Apply colors and properties
            prop.SetColor(*kd_color)
            prop.SetSpecularColor(*ks_color)
            prop.SetSpecular(0.5 if sum(ks_color) > 0 else 0.0)  # Enable specular if color is set
            prop.SetSpecularPower(ns_value)
            prop.SetOpacity(d_value)

            # Set reasonable defaults for STL rendering
            prop.SetAmbient(0.2)
            prop.SetDiffuse(0.8)

            self.logger.info(
                f"Applied MTL properties to STL for '{species_name}': Kd={kd_color}, Ks={ks_color}, Ns={ns_value}, d={d_value}"
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(f"Failed to apply MTL properties to STL for '{species_name}': {e}")
            # Fallback to default material
            try:
                prop = actor.GetProperty()
                prop.SetColor(0.7, 0.7, 0.7)  # Default gray
                prop.SetAmbient(0.2)
                prop.SetDiffuse(0.8)
                prop.SetSpecular(0.3)
                prop.SetSpecularPower(20.0)
                prop.SetOpacity(1.0)
            except Exception:
                pass

    def parse_mtl_direct(self, mtl_path: str) -> Dict[str, Any]:
        """Parse MTL file directly to extract material properties for STL application."""
        material = {
            "Kd": (0.8, 0.8, 0.8),  # diffuse color default
            "Ks": (0.0, 0.0, 0.0),  # specular color default
            "Ns": 10.0,  # shininess default
            "d": 1.0,  # opacity default
        }

        try:
            with open(mtl_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("Kd "):  # diffuse color
                        parts = line.split()
                        if len(parts) >= 4:
                            material["Kd"] = tuple(map(float, parts[1:4]))
                    elif line.startswith("Ks "):  # specular color
                        parts = line.split()
                        if len(parts) >= 4:
                            material["Ks"] = tuple(map(float, parts[1:4]))
                    elif line.startswith("Ns "):  # shininess
                        parts = line.split()
                        if len(parts) >= 2:
                            material["Ns"] = float(parts[1])
                    elif line.startswith("d "):  # opacity
                        parts = line.split()
                        if len(parts) >= 2:
                            material["d"] = float(parts[1])

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to parse MTL file %s: {e}", mtl_path)

        return material

    def _save_lighting_settings(self) -> None:
        """Save current lighting settings to QSettings."""
        try:
            settings = QSettings()
            if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
                props = self.main_window.lighting_manager.get_properties()
                settings.setValue("lighting/position_x", float(props["position"][0]))
                settings.setValue("lighting/position_y", float(props["position"][1]))
                settings.setValue("lighting/position_z", float(props["position"][2]))
                settings.setValue("lighting/color_r", float(props["color"][0]))
                settings.setValue("lighting/color_g", float(props["color"][1]))
                settings.setValue("lighting/color_b", float(props["color"][2]))
                settings.setValue("lighting/intensity", float(props["intensity"]))
                settings.setValue("lighting/cone_angle", float(props.get("cone_angle", 30.0)))
                self.logger.debug("Lighting settings saved to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to save lighting settings: %s", e)


# Convenience function for easy material and lighting integration setup
def setup_material_lighting_integration(
    """TODO: Add docstring."""
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> MaterialLightingIntegrator:
    """
    Convenience function to set up material and lighting integration for a main window.

    Args:
        main_window: The main window to set up material and lighting integration for
        logger: Optional logger instance

    Returns:
        MaterialLightingIntegrator instance for further material and lighting operations
    """
    return MaterialLightingIntegrator(main_window, logger)
