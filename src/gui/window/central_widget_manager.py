"""
Central Widget Management Module

This module handles the creation and management of the central widget area,
including the hero tabs, 3D viewer integration, and central layout management.

Classes:
    CentralWidgetManager: Main class for managing central widget functionality
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QSizePolicy

from src.gui.theme import qss_tabs_lists_labels, SPACING_8, SPACING_16
from src.gui.material_manager import MaterialManager
from src.gui.lighting_manager import LightingManager
from src.core.database_manager import get_database_manager


class CentralWidgetManager:
    """
    Manages the central widget area of the main window.

    This class handles the creation of the hero tabs, 3D viewer integration,
    and management of the central widget area including tab organization
    and layout coordination.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the central widget manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

    def setup_central_widget(self) -> None:
        """Create Center Hero Tabs and ensure right-column stacking for Properties and Metadata."""
        self.logger.debug("Setting up central widget")

        # 1) Create the 3D viewer widget
        try:
            try:
                from src.gui.viewer_widget_vtk import Viewer3DWidget
            except ImportError:
                try:
                    from src.gui.viewer_widget import Viewer3DWidget
                except ImportError:
                    Viewer3DWidget = None

            self.main_window.viewer_widget = Viewer3DWidget(self.main_window)

            # Connect signals
            self.main_window.viewer_widget.model_loaded.connect(self._on_model_loaded)
            self.main_window.viewer_widget.performance_updated.connect(self._on_performance_updated)

            # Managers
            try:
                self.main_window.material_manager = MaterialManager(get_database_manager())
            except Exception as e:
                self.main_window.material_manager = None
                self.logger.warning(f"MaterialManager unavailable: {e}")

            try:
                renderer = getattr(self.main_window.viewer_widget, "renderer", None)
                self.main_window.lighting_manager = LightingManager(renderer) if renderer is not None else None
                if self.main_window.lighting_manager:
                    self.main_window.lighting_manager.create_light()
                    try:
                        self._load_lighting_settings()
                    except Exception as le:
                        self.logger.warning(f"Failed to load lighting settings: {le}")
            except Exception as e:
                self.main_window.lighting_manager = None
                self.logger.warning(f"LightingManager unavailable: {e}")

            # Create MaterialLightingIntegrator for material and lighting integration
            try:
                from src.gui.materials.integration import MaterialLightingIntegrator
                self.main_window.material_lighting_integrator = MaterialLightingIntegrator(self.main_window)
                self.logger.info("MaterialLightingIntegrator created successfully")
            except Exception as e:
                self.main_window.material_lighting_integrator = None
                self.logger.warning(f"MaterialLightingIntegrator unavailable: {e}")

            if hasattr(self.main_window.viewer_widget, "lighting_panel_requested"):
                self.main_window.viewer_widget.lighting_panel_requested.connect(self._toggle_lighting_panel)
            if hasattr(self.main_window.viewer_widget, "material_selected"):
                self.main_window.viewer_widget.material_selected.connect(self._apply_material_species)
            if hasattr(self.main_window.viewer_widget, "save_view_requested"):
                self.main_window.viewer_widget.save_view_requested.connect(self._save_current_view)

            try:
                if hasattr(self.main_window, "lighting_panel") and self.main_window.lighting_panel and self.main_window.lighting_manager:
                    self.main_window.lighting_panel.position_changed.connect(self._update_light_position)
                    self.main_window.lighting_panel.color_changed.connect(self._update_light_color)
                    self.main_window.lighting_panel.intensity_changed.connect(self._update_light_intensity)
                    self.main_window.lighting_panel.cone_angle_changed.connect(self._update_light_cone_angle)
                    props = self.main_window.lighting_manager.get_properties()
                    self.main_window.lighting_panel.set_values(
                        position=tuple(props.get("position", (100.0, 100.0, 100.0))),
                        color=tuple(props.get("color", (1.0, 1.0, 1.0))),
                        intensity=float(props.get("intensity", 0.8)),
                        cone_angle=float(props.get("cone_angle", 30.0)),
                        emit_signals=False,
                    )
            except Exception as e:
                self.logger.warning(f"Failed to connect lighting panel: {e}")

            if hasattr(self.main_window.viewer_widget, "apply_theme"):
                try:
                    self.main_window.viewer_widget.apply_theme()
                except Exception:
                    pass

            self.logger.info("3D viewer widget created successfully")

        except ImportError as e:
            self.logger.warning(f"Failed to import 3D viewer widget: {str(e)}")
            self.main_window.viewer_widget = QTextEdit()
            self.main_window.viewer_widget.setReadOnly(True)
            self.main_window.viewer_widget.setPlainText(
                "3D Model Viewer\n\n"
                "Failed to load 3D viewer component.\n"
                "Please ensure VTK or PyQt3D is properly installed.\n\n"
                "Features will include:\n"
                "- Interactive 3D model rendering\n"
                "- Multiple view modes (wireframe, solid, textured)\n"
                "- Camera controls (orbit, pan, zoom)\n"
                "- Lighting controls\n"
                "- Measurement tools\n"
                "- Animation playback\n"
                "- Screenshot capture"
            )
            self.main_window.viewer_widget.setAlignment(Qt.AlignCenter)

        # 2) Center Hero Tabs (Model | GP | CLO | F&S | Project Cost Calculator)
        self.main_window.hero_tabs = QTabWidget(self.main_window)
        self.main_window.hero_tabs.setObjectName("HeroTabs")
        try:
            self.main_window.hero_tabs.setDocumentMode(True)
            self.main_window.hero_tabs.setTabsClosable(False)
            self.main_window.hero_tabs.setMovable(True)
            self.main_window.hero_tabs.setUsesScrollButtons(False)  # Disable scrolling to allow even spacing
            self.main_window.hero_tabs.setElideMode(Qt.ElideNone)  # Don't truncate tab text
            # Set expanding policy for tabs to use available space evenly
            self.main_window.hero_tabs.setTabBarAutoHide(False)

            # Get the tab bar and set expanding policy
            tab_bar = self.main_window.hero_tabs.tabBar()
            if tab_bar:
                tab_bar.setExpanding(True)  # This makes tabs expand to fill available space
                tab_bar.setUsesScrollButtons(False)

            # Make hero tabs sticky to all sides
            self.main_window.hero_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.main_window.hero_tabs.setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass

        # Material Design theme is applied globally via ThemeService
        # No need to apply custom stylesheets here - let qt-material handle it

        # Add tabs: Model (viewer) + placeholders
        self.main_window.hero_tabs.addTab(self.main_window.viewer_widget, "Model Previewer")

        def _placeholder(title: str, body: str) -> QWidget:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(12, 12, 12, 12)
            lbl = QLabel(body)
            try:
                lbl.setWordWrap(True)
            except Exception:
                pass
            v.addWidget(lbl)
            v.addStretch(1)
            return w

        # Create G-code Previewer widget
        try:
            from src.gui.gcode_previewer_components import GcodePreviewerWidget
            self.main_window.gcode_previewer_widget = GcodePreviewerWidget(self.main_window)
            self.main_window.hero_tabs.addTab(self.main_window.gcode_previewer_widget, "G Code Previewer")
            self.logger.info("G-code Previewer widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create G-code Previewer widget: {e}")
            self.main_window.hero_tabs.addTab(_placeholder("GCP", "G-code Previewer\n\nComponent unavailable."), "G Code Previewer")

        # Create CLO widget
        try:
            from src.gui.CLO import CutListOptimizerWidget
            self.main_window.clo_widget = CutListOptimizerWidget()
            self.main_window.hero_tabs.addTab(self.main_window.clo_widget, "Cut List Optimizer")
            self.logger.info("CLO widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create CLO widget: {e}")
            self.main_window.hero_tabs.addTab(_placeholder("CLO", "Cut List Optimizer\n\nComponent unavailable."), "Cut List Optimizer")

        # Create Feeds & Speeds widget
        try:
            from src.gui.feeds_and_speeds import FeedsAndSpeedsWidget
            self.main_window.feeds_and_speeds_widget = FeedsAndSpeedsWidget(self.main_window)
            self.main_window.hero_tabs.addTab(self.main_window.feeds_and_speeds_widget, "Feed and Speed")
            self.logger.info("Feeds & Speeds widget created successfully")
        except Exception as e:
            self.logger.warning(f"Failed to create Feeds & Speeds widget: {e}")
            self.main_window.hero_tabs.addTab(_placeholder("F&S", "Feeds & Speeds Calculator\n\nComponent unavailable."), "Feed and Speed")

        self.main_window.hero_tabs.addTab(_placeholder("Project Cost Estimator", "Cost Calculator placeholder\n\nEstimate material, machine, and labor costs."), "Project Cost Estimator")

        # Setup dynamic tab naming
        try:
            from src.gui.components.dynamic_tab_manager import setup_dynamic_tabs
            self.main_window.dynamic_tab_manager = setup_dynamic_tabs(self.main_window.hero_tabs)
            self.logger.info("Dynamic tab manager initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize dynamic tab manager: {e}")

        # Persist active hero tab on change
        try:
            self.main_window.hero_tabs.currentChanged.connect(lambda _=0: self._schedule_layout_save())
        except Exception:
            pass

        # Restore last active hero tab index
        try:
            _settings = self._read_settings_json()
            hidx = _settings.get("active_hero_tab_index")
            if isinstance(hidx, int) and 0 <= hidx < self.main_window.hero_tabs.count():
                self.main_window.hero_tabs.setCurrentIndex(int(hidx))
        except Exception:
            pass

        # Set hero tabs as the central widget
        # The dock system will automatically manage all other widgets around it
        # This ensures 100% window fill and proper "sticky" behavior
        try:
            self.main_window.setCentralWidget(self.main_window.hero_tabs)
            self.logger.info("Hero tabs set as central widget - dock system will manage layout")
        except Exception as e:
            self.logger.warning(f"Failed to set central widget: {e}")

        # 3) Ensure all docks are visible but don't force positioning
        try:
            # Just make sure all main docks are visible, let users arrange them
            if hasattr(self.main_window, "properties_dock") and self.main_window.properties_dock:
                if not self.main_window.properties_dock.isVisible():
                    self.main_window.properties_dock.setVisible(True)
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                if not self.main_window.metadata_dock.isVisible():
                    self.main_window.metadata_dock.setVisible(True)
            if hasattr(self.main_window, "model_library_dock") and self.main_window.model_library_dock:
                if not self.main_window.model_library_dock.isVisible():
                    self.main_window.model_library_dock.setVisible(True)
            self.logger.info("All docks made visible - user can arrange freely")
        except Exception as e:
            self.logger.warning(f"Failed to ensure dock visibility: {e}")

        self.logger.debug("Center Hero Tabs layout with right-column stacking completed")

    # Helper methods that need to be connected to actual implementations
    def _on_model_loaded(self, info: str) -> None:
        """Handle model loaded signal."""
        if hasattr(self.main_window, '_on_model_loaded'):
            self.main_window._on_model_loaded(info)

    def _on_performance_updated(self, fps: float) -> None:
        """Handle performance update signal."""
        if hasattr(self.main_window, '_on_performance_updated'):
            self.main_window._on_performance_updated(fps)

    def _toggle_lighting_panel(self) -> None:
        """Toggle lighting panel visibility."""
        if hasattr(self.main_window, '_toggle_lighting_panel'):
            self.main_window._toggle_lighting_panel()

    def _apply_material_species(self, species_name: str) -> None:
        """Apply material species."""
        if hasattr(self.main_window, '_apply_material_species'):
            self.main_window._apply_material_species(species_name)

    def _save_current_view(self) -> None:
        """Save current view."""
        if hasattr(self.main_window, '_save_current_view'):
            self.main_window._save_current_view()

    def _update_light_position(self, x: float, y: float, z: float) -> None:
        """Update light position."""
        if hasattr(self.main_window, '_update_light_position'):
            self.main_window._update_light_position(x, y, z)

    def _update_light_color(self, r: float, g: float, b: float) -> None:
        """Update light color."""
        if hasattr(self.main_window, '_update_light_color'):
            self.main_window._update_light_color(r, g, b)

    def _update_light_intensity(self, value: float) -> None:
        """Update light intensity."""
        if hasattr(self.main_window, '_update_light_intensity'):
            self.main_window._update_light_intensity(value)

    def _update_light_cone_angle(self, angle: float) -> None:
        """Update light cone angle."""
        if hasattr(self.main_window, '_update_light_cone_angle'):
            self.main_window._update_light_cone_angle(angle)

    def _load_lighting_settings(self) -> None:
        """Load lighting settings."""
        if hasattr(self.main_window, '_load_lighting_settings'):
            self.main_window._load_lighting_settings()

    def _schedule_layout_save(self) -> None:
        """Schedule layout save."""
        if hasattr(self.main_window, '_schedule_layout_save'):
            self.main_window._schedule_layout_save()

    def _read_settings_json(self) -> dict:
        """Read settings from JSON."""
        if hasattr(self.main_window, '_read_settings_json'):
            return self.main_window._read_settings_json()
        return {}


# Convenience function for easy central widget setup
def setup_central_widget(main_window: QMainWindow, logger: Optional[logging.Logger] = None) -> CentralWidgetManager:
    """
    Convenience function to set up central widget for a main window.

    Args:
        main_window: The main window to set up central widget for
        logger: Optional logger instance

    Returns:
        CentralWidgetManager instance for further central widget operations
    """
    manager = CentralWidgetManager(main_window, logger)
    manager.setup_central_widget()
    return manager
