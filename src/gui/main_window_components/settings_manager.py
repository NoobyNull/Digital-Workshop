"""
Settings management for main window.

Handles lighting and metadata panel settings persistence.
"""

from typing import Optional, Tuple

from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger, log_function_call


logger = get_logger(__name__)


class SettingsManager:
    """Manages application settings persistence."""

    def __init__(self, main_window):
        """
        Initialize settings manager.

        Args:
            main_window: The main window instance
        """
        self.main_window = main_window

    @log_function_call(logger)
    def save_lighting_settings(self) -> None:
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
                logger.debug("Lighting settings saved to QSettings")
        except Exception as e:
            logger.warning(f"Failed to save lighting settings: {e}")

    @log_function_call(logger)
    def load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings and apply to manager and panel."""
        try:
            settings = QSettings()
            if settings.contains("lighting/position_x"):
                pos_x = settings.value("lighting/position_x", 100.0, type=float)
                pos_y = settings.value("lighting/position_y", 100.0, type=float)
                pos_z = settings.value("lighting/position_z", 100.0, type=float)
                col_r = settings.value("lighting/color_r", 1.0, type=float)
                col_g = settings.value("lighting/color_g", 1.0, type=float)
                col_b = settings.value("lighting/color_b", 1.0, type=float)
                intensity = settings.value("lighting/intensity", 0.8, type=float)
                cone_angle = settings.value("lighting/cone_angle", 30.0, type=float)

                props = {
                    "position": (float(pos_x), float(pos_y), float(pos_z)),
                    "color": (float(col_r), float(col_g), float(col_b)),
                    "intensity": float(intensity),
                    "cone_angle": float(cone_angle),
                }

                if hasattr(self.main_window, "lighting_manager") and self.main_window.lighting_manager:
                    self.main_window.lighting_manager.apply_properties(props)

                # Sync to lighting_panel without re-emitting
                try:
                    if hasattr(self.main_window, "lighting_panel") and self.main_window.lighting_panel:
                        self.main_window.lighting_panel.set_values(
                            position=props["position"],
                            color=props["color"],
                            intensity=props["intensity"],
                            cone_angle=props["cone_angle"],
                            emit_signals=False,
                        )
                except Exception:
                    pass

                logger.info("Lighting settings loaded from QSettings")
        except Exception as e:
            logger.warning(f"Failed to load lighting settings: {e}")

    def save_lighting_panel_visibility(self) -> None:
        """Lighting panel is now a floating dialog, visibility is not persisted."""
        pass

    def update_metadata_action_state(self) -> None:
        """Enable/disable 'Show Metadata Manager' based on panel visibility."""
        try:
            visible = False
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                visible = bool(self.main_window.metadata_dock.isVisible())
            if hasattr(self.main_window, "show_metadata_action") and self.main_window.show_metadata_action:
                self.main_window.show_metadata_action.setEnabled(not visible)
        except Exception:
            pass

    @log_function_call(logger)
    def save_metadata_panel_visibility(self) -> None:
        """Persist the metadata panel visibility state."""
        try:
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                settings = QSettings()
                vis = bool(self.main_window.metadata_dock.isVisible())
                settings.setValue("metadata_panel/visible", vis)
                logger.debug(f"Saved metadata panel visibility: {vis}")
        except Exception as e:
            logger.warning(f"Failed to save metadata panel visibility: {e}")

    @log_function_call(logger)
    def load_metadata_panel_visibility(self) -> bool:
        """Load and restore the metadata panel visibility state."""
        try:
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                settings = QSettings()
                if settings.contains("metadata_panel/visible"):
                    vis = settings.value("metadata_panel/visible", True, type=bool)
                    self.main_window.metadata_dock.setVisible(vis)
                    logger.debug(f"Restored metadata panel visibility: {vis}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load metadata panel visibility: {e}")
        return False

    def save_library_panel_visibility(self) -> None:
        """Persist the library panel visibility state."""
        try:
            if hasattr(self.main_window, "library_dock") and self.main_window.library_dock:
                settings = QSettings()
                vis = bool(self.main_window.library_dock.isVisible())
                settings.setValue("library_panel/visible", vis)
                logger.debug(f"Saved library panel visibility: {vis}")
        except Exception as e:
            logger.warning(f"Failed to save library panel visibility: {e}")

    def load_library_panel_visibility(self) -> bool:
        """Load and restore the library panel visibility state."""
        try:
            if hasattr(self.main_window, "library_dock") and self.main_window.library_dock:
                settings = QSettings()
                if settings.contains("library_panel/visible"):
                    vis = settings.value("library_panel/visible", True, type=bool)
                    self.main_window.library_dock.setVisible(vis)
                    logger.debug(f"Restored library panel visibility: {vis}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load library panel visibility: {e}")
        return False

