"""
Settings management for main window.

Handles lighting and metadata panel settings persistence.
"""

from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger, log_function_call


logger = get_logger(__name__)


class SettingsManager:
    """Manages application settings persistence."""

    def __init__(self, main_window) -> None:
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
            if (
                hasattr(self.main_window, "lighting_manager")
                and self.main_window.lighting_manager
            ):
                props = self.main_window.lighting_manager.get_properties()
                settings.setValue("lighting/position_x", float(props["position"][0]))
                settings.setValue("lighting/position_y", float(props["position"][1]))
                settings.setValue("lighting/position_z", float(props["position"][2]))
                settings.setValue("lighting/color_r", float(props["color"][0]))
                settings.setValue("lighting/color_g", float(props["color"][1]))
                settings.setValue("lighting/color_b", float(props["color"][2]))
                settings.setValue("lighting/intensity", float(props["intensity"]))
                settings.setValue(
                    "lighting/cone_angle", float(props.get("cone_angle", 30.0))
                )
                logger.debug("Lighting settings saved to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save lighting settings: %s", e)

    @log_function_call(logger)
    def load_lighting_settings(self) -> None:
        """Load lighting settings from QSettings and apply to manager and panel."""
        try:
            settings = QSettings()
            if settings.contains("lighting/position_x"):
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

                if (
                    hasattr(self.main_window, "lighting_manager")
                    and self.main_window.lighting_manager
                ):
                    self.main_window.lighting_manager.apply_properties(props)

                # Sync to lighting_panel without re-emitting
                try:
                    if (
                        hasattr(self.main_window, "lighting_panel")
                        and self.main_window.lighting_panel
                    ):
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
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to load lighting settings: %s", e)

    def save_lighting_panel_visibility(self) -> None:
        """Lighting panel is now a floating dialog, visibility is not persisted."""

    def update_metadata_action_state(self) -> None:
        """Enable/disable 'Show Metadata Manager' based on panel visibility."""
        try:
            visible = False
            if (
                hasattr(self.main_window, "metadata_dock")
                and self.main_window.metadata_dock
            ):
                visible = bool(self.main_window.metadata_dock.isVisible())
            if (
                hasattr(self.main_window, "show_metadata_action")
                and self.main_window.show_metadata_action
            ):
                self.main_window.show_metadata_action.setEnabled(not visible)
        except Exception:
            pass

    @log_function_call(logger)
    def save_metadata_panel_visibility(self) -> None:
        """Persist the metadata panel visibility state."""
        try:
            if (
                hasattr(self.main_window, "metadata_dock")
                and self.main_window.metadata_dock
            ):
                settings = QSettings()
                vis = bool(self.main_window.metadata_dock.isVisible())
                settings.setValue("metadata_panel/visible", vis)
                logger.debug("Saved metadata panel visibility: %s", vis)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save metadata panel visibility: %s", e)

    @log_function_call(logger)
    def load_metadata_panel_visibility(self) -> bool:
        """Load and restore the metadata panel visibility state."""
        try:
            if (
                hasattr(self.main_window, "metadata_dock")
                and self.main_window.metadata_dock
            ):
                settings = QSettings()
                if settings.contains("metadata_panel/visible"):
                    vis = settings.value("metadata_panel/visible", True, type=bool)
                    self.main_window.metadata_dock.setVisible(vis)
                    logger.debug("Restored metadata panel visibility: %s", vis)
                    return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to load metadata panel visibility: %s", e)
        return False

    def save_library_panel_visibility(self) -> None:
        """Persist the library panel visibility state."""
        try:
            if (
                hasattr(self.main_window, "library_dock")
                and self.main_window.library_dock
            ):
                settings = QSettings()
                vis = bool(self.main_window.library_dock.isVisible())
                settings.setValue("library_panel/visible", vis)
                logger.debug("Saved library panel visibility: %s", vis)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save library panel visibility: %s", e)

    def load_library_panel_visibility(self) -> bool:
        """Load and restore the library panel visibility state."""
        try:
            if (
                hasattr(self.main_window, "library_dock")
                and self.main_window.library_dock
            ):
                settings = QSettings()
                if settings.contains("library_panel/visible"):
                    vis = settings.value("library_panel/visible", True, type=bool)
                    self.main_window.library_dock.setVisible(vis)
                    logger.debug("Restored library panel visibility: %s", vis)
                    return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to load library panel visibility: %s", e)
        return False

    @log_function_call(logger)
    def save_viewer_settings(self) -> None:
        """Save 3D viewer settings (grid, ground, camera, lighting) to QSettings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Grid settings
            settings.setValue("viewer/grid_visible", config.grid_visible)
            settings.setValue("viewer/grid_color", config.grid_color)
            settings.setValue("viewer/grid_size", float(config.grid_size))

            # Cut List Optimizer layout grid defaults
            settings.setValue("clo/grid_spacing", float(config.clo_grid_spacing))
            settings.setValue("clo/grid_unit", config.clo_grid_unit)
            settings.setValue(
                "clo/grid_major_opacity", int(config.clo_grid_major_opacity)
            )
            settings.setValue(
                "clo/grid_show_intermediate", config.clo_grid_show_intermediate
            )

            # Ground plane settings
            settings.setValue("viewer/ground_visible", config.ground_visible)
            settings.setValue("viewer/ground_color", config.ground_color)
            settings.setValue("viewer/ground_offset", float(config.ground_offset))

            # Camera settings
            settings.setValue(
                "viewer/mouse_sensitivity", float(config.mouse_sensitivity)
            )
            settings.setValue("viewer/fps_limit", int(config.fps_limit))
            settings.setValue("viewer/zoom_speed", float(config.zoom_speed))
            settings.setValue("viewer/pan_speed", float(config.pan_speed))
            settings.setValue("viewer/auto_fit_on_load", config.auto_fit_on_load)

            logger.debug("Viewer settings saved to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save viewer settings: %s", e)

    @log_function_call(logger)
    def save_window_settings(self) -> None:
        """Save window settings (startup behavior) to QSettings.

        NOTE: Actual window dimensions are saved by MainWindow._save_window_settings()
        using saveGeometry() and explicit width/height values. This method only saves
        configuration defaults and startup behavior, NOT the current window size.
        """
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Save configuration defaults (not current window size)
            # Current window size is saved by MainWindow._save_window_settings()
            settings.setValue("window/default_width", int(config.default_window_width))
            settings.setValue(
                "window/default_height", int(config.default_window_height)
            )
            settings.setValue("window/minimum_width", int(config.minimum_window_width))
            settings.setValue(
                "window/minimum_height", int(config.minimum_window_height)
            )

            # Startup behavior
            settings.setValue("window/maximize_on_startup", config.maximize_on_startup)
            settings.setValue(
                "window/remember_window_size", config.remember_window_size
            )

            logger.debug("Window settings saved to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to save window settings: %s", e)
