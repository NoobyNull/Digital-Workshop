"""
Dock Widget Management Module

This module handles the creation, management, and coordination of dock widgets
in the main window, including layout management and dock-specific functionality.

Classes:
    DockManager: Main class for managing dock widgets
"""

import logging
from typing import Optional, List

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QTextEdit,
    QTabWidget,
    QSizePolicy,
)

from src.gui.lighting_control_panel import LightingControlPanel


class DockManager:
    """
    Manages dock widgets for the main window.

    This class handles the creation, setup, and management of dock widgets,
    including the model library, properties panel, metadata editor, and
    their associated layout and persistence functionality.
    """

    def __init__(self, main_window: QMainWindow, logger: Optional[logging.Logger] = None):
        """
        Initialize the dock manager.

        Args:
            main_window: The main window instance
            logger: Optional logger instance for debugging
        """
        self.main_window = main_window
        self.logger = logger or logging.getLogger(__name__)

    def setup_dock_widgets(self) -> None:
        """Set up dockable widgets for the application."""
        self.logger.debug("Setting up dock widgets")

        # Model library dock (flexible positioning)
        self.model_library_dock = QDockWidget("Model Library", self.main_window)
        self.model_library_dock.setObjectName("ModelLibraryDock")
        # Allow docking to any area for maximum flexibility
        self.model_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.model_library_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
        )

        # Create model library widget
        try:
            from src.gui.model_library import ModelLibraryWidget

            self.model_library_widget = ModelLibraryWidget(self.main_window)

            # Connect signals
            self.model_library_widget.model_selected.connect(self._on_model_selected)
            self.model_library_widget.model_double_clicked.connect(self._on_model_double_clicked)
            self.model_library_widget.models_added.connect(self._on_models_added)

            self.model_library_dock.setWidget(self.model_library_widget)
            # Add context menu helpers for docking
            try:
                self._setup_dock_context_menu(self.model_library_dock, Qt.LeftDockWidgetArea)
            except Exception:
                pass
            # Let qt-material handle all dock styling
            self.logger.info("Model library widget created successfully")

        except ImportError as e:
            self.logger.warning("Failed to import model library widget: %s", str(e))

            # Fallback to placeholder
            model_library_widget = QTextEdit()
            model_library_widget.setReadOnly(True)
            model_library_widget.setPlainText(
                "Model Library\n\n"
                "Failed to load model library component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Model list with thumbnails\n"
                "- Category filtering\n"
                "- Search functionality\n"
                "- Import/export options"
            )
            self.model_library_dock.setWidget(model_library_widget)

        # Default to left side but user can move anywhere
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
        try:
            self._register_dock_for_snapping(self.model_library_dock)
        except Exception:
            pass
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.model_library_dock)
        except Exception:
            pass
        # Keep View menu action in sync with visibility
        try:
            self.model_library_dock.visibilityChanged.connect(
                lambda _=False: self._update_library_action_state()
            )
        except Exception:
            pass
        try:
            self._update_library_action_state()
        except Exception:
            pass

        # Properties dock (flexible positioning)
        self.properties_dock = QDockWidget("Project Details", self.main_window)
        self.properties_dock.setObjectName("PropertiesDock")
        # Allow docking to any area for maximum flexibility
        self.properties_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.properties_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
        )

        # Placeholder for model properties
        properties_widget = QTextEdit()
        properties_widget.setReadOnly(True)
        properties_widget.setPlainText(
            "Model Properties\n\n"
            "This panel will display properties and metadata\n"
            "for the selected 3D model.\n"
            "Features will include:\n"
            "- Model information\n"
            "- Metadata editing\n"
            "- Tag management\n"
            "- Export settings"
        )
        self.properties_dock.setWidget(properties_widget)
        try:
            self._setup_dock_context_menu(self.properties_dock, Qt.RightDockWidgetArea)
        except Exception:
            pass
        # Let qt-material handle all dock styling

        # Add as dock widget to the right side
        # The dock system will automatically manage layout and tabification
        try:
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
            self.logger.info("Properties dock added to right dock area")
        except Exception as e:
            self.logger.warning("Failed to add properties dock: %s", e)

        try:
            self._register_dock_for_snapping(self.properties_dock)
        except Exception:
            pass
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.properties_dock)
        except Exception:
            pass

        # Ensure proper central widget resizing by setting size constraints
        try:
            # Ensure the dock widget can resize properly
            self.properties_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        except Exception as e:
            self.logger.warning("Failed to set properties dock size constraints: %s", e)

        # Lighting control dialog (floating, initially hidden)
        try:
            self.main_window.lighting_panel = LightingControlPanel(self.main_window)
            self.main_window.lighting_panel.setObjectName("LightingDialog")
            self.main_window.lighting_panel.hide()
            # Dialog will float above main window when shown
            self.logger.info("Lighting control panel created as floating dialog")

            # Connect lighting panel signals to main window handlers
            try:
                if (
                    hasattr(self.main_window, "lighting_manager")
                    and self.main_window.lighting_manager
                ):
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

                    # Initialize panel with current lighting properties
                    props = self.main_window.lighting_manager.get_properties()
                    self.main_window.lighting_panel.set_values(
                        position=tuple(props.get("position", (100.0, 100.0, 100.0))),
                        color=tuple(props.get("color", (1.0, 1.0, 1.0))),
                        intensity=float(props.get("intensity", 0.8)),
                        cone_angle=float(props.get("cone_angle", 30.0)),
                        emit_signals=False,
                    )
                    self.logger.info("Lighting panel signals connected to main window handlers")
            except Exception as e:
                self.logger.warning("Failed to connect lighting panel signals: %s", e)
        except Exception as e:
            self.logger.warning("Failed to create LightingControlPanel: %s", e)

        # Metadata dock (flexible positioning)
        self.metadata_dock = QDockWidget("Metadata Editor", self.main_window)
        self.metadata_dock.setObjectName("MetadataDock")
        # Allow docking to any area for maximum flexibility
        self.metadata_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.metadata_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
        )

        # Set size policies for proper resizing behavior
        self.properties_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.metadata_dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Create metadata editor widget and wrap in a bottom tab bar for reduced clutter
        try:
            from src.gui.metadata_editor import MetadataEditorWidget

            self.metadata_editor = MetadataEditorWidget(self.main_window)

            # Connect signals
            self.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
            self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)

            # Bottom tabs: Metadata | Notes | History
            self.metadata_tabs = QTabWidget(self.main_window)
            self.metadata_tabs.setObjectName("MetadataTabs")
            self.metadata_tabs.addTab(self.metadata_editor, "Metadata")

            # Notes tab (placeholder)
            notes_widget = QTextEdit()
            notes_widget.setReadOnly(True)
            notes_widget.setPlainText(
                "Notes\n\n"
                "Add project or model-specific notes here.\n"
                "Future: rich text, timestamps, and attachments."
            )
            self.metadata_tabs.addTab(notes_widget, "Notes")

            # History tab (placeholder)
            history_widget = QTextEdit()
            history_widget.setReadOnly(True)
            history_widget.setPlainText(
                "History\n\n" "Timeline of edits and metadata changes will appear here."
            )
            self.metadata_tabs.addTab(history_widget, "History")

            # Material Design theme is applied globally via ThemeService
            # No need to apply custom stylesheets here

            self.metadata_dock.setWidget(self.metadata_tabs)
            try:
                self._setup_dock_context_menu(self.metadata_dock, Qt.BottomDockWidgetArea)
            except Exception:
                pass
            # Let qt-material handle all dock styling
            self.logger.info("Metadata editor widget created successfully (tabbed)")
        except ImportError as e:
            self.logger.warning("Failed to import metadata editor widget: %s", str(e))

            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText(
                "Metadata Editor\n\n"
                "Failed to load metadata editor component.\n"
                "Please ensure all dependencies are properly installed.\n\n"
                "Features will include:\n"
                "- Title and description editing\n"
                "- Category assignment\n"
                "- Keyword tagging\n"
                "- Custom properties"
            )
            self.metadata_dock.setWidget(metadata_widget)

        # Add to right dock container if it exists (splitter-based layout)
        # Otherwise add as dock widget (fallback)
        # Add as dock widget to the right side and tabify with properties dock
        # This creates a tabbed interface for Properties and Metadata
        try:
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.metadata_dock)
            try:
                self.main_window.tabifyDockWidget(self.properties_dock, self.metadata_dock)
                self.logger.info("Properties and Metadata docks tabified for unified resizing")

                # Connect to tab bar to allow expanding metadata when active
                try:
                    # Get the tab bar for the tabified docks
                    tab_bar = self.properties_dock.tabBar()
                    if tab_bar:
                        tab_bar.currentChanged.connect(self._on_right_dock_tab_changed)
                        self.logger.info("Connected tab change handler for right dock expansion")
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            self.logger.warning("Failed to add metadata dock: %s", e)

        try:
            self._register_dock_for_snapping(self.metadata_dock)
        except Exception:
            pass
        # Autosave when this dock changes state/position
        try:
            self._connect_layout_autosave(self.metadata_dock)
        except Exception:
            pass
        # Persist visibility and keep View menu action state in sync
        try:
            self.metadata_dock.visibilityChanged.connect(
                lambda _=False: self._save_metadata_panel_visibility()
            )
            self.metadata_dock.visibilityChanged.connect(
                lambda _=False: self._update_metadata_action_state()
            )
        except Exception:
            pass
        try:
            self._update_metadata_action_state()
        except Exception:
            pass

        # Capture the default layout as the baseline for future resets
        try:
            self._save_default_layout_state()
        except Exception:
            pass

        # Save current layout as default for fresh installations
        try:
            self._save_current_layout_as_default()
        except Exception:
            pass

        # Initialize autosave mechanics and attempt to restore last layout
        try:
            self._init_layout_persistence()
            self._load_saved_layout()
        except Exception:
            pass
        # Lighting panel is now a floating dialog, visibility is not persisted across sessions
        # It will be hidden by default and shown only when user clicks the Lighting button

        # Load persisted metadata panel visibility (in addition to dock state)
        try:
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                settings = QSettings()
                meta_visible = settings.value("metadata_panel/visible", True, type=bool)
                self.main_window.metadata_dock.setVisible(bool(meta_visible))
                self.logger.info("Loaded metadata panel visibility: %s", bool(meta_visible))
                try:
                    self._update_metadata_action_state()
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning("Failed to load metadata panel visibility: %s", e)

        # Ensure metadata dock is visible but don't force positioning
        try:
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                # Just make sure it's visible, user can position as needed
                if not self.main_window.metadata_dock.isVisible():
                    self.main_window.metadata_dock.setVisible(True)
                self.logger.info("Metadata dock made visible - user can position freely")
        except Exception as e:
            self.logger.warning("Failed to ensure metadata dock visibility: %s", e)

        self.logger.debug("Dock widgets setup completed")

    def _on_right_dock_tab_changed(self, index: int) -> None:
        """Handle tab changes in the right dock area to allow expansion."""
        try:
            # When metadata tab is active, it can expand to fill the right side
            # This is handled by Qt's dock system automatically
            self.logger.debug("Right dock tab changed to index %s", index)
        except Exception as e:
            self.logger.warning("Error handling dock tab change: %s", e)

    def iter_docks(self) -> List[QDockWidget]:
        """Iterate over all known dock widgets."""
        docks: List[QDockWidget] = []
        for name in ("model_library_dock", "properties_dock", "metadata_dock"):
            d = getattr(self.main_window, name, None)
            if isinstance(d, QDockWidget):
                docks.append(d)
        return docks

    def enable_snap_handlers(self, enable: bool) -> None:
        """Enable or disable snap overlay handlers for all docks."""
        try:
            if enable:
                for d in self.iter_docks():
                    self._register_dock_for_snapping(d)
            else:
                # Remove event filters and clear overlays
                if hasattr(self.main_window, "_snap_handlers"):
                    for key, handler in list(self.main_window._snap_handlers.items()):
                        try:
                            dock = getattr(handler, "_dock", None)
                            if dock:
                                dock.removeEventFilter(handler)
                        except Exception:
                            pass
                    self.main_window._snap_handlers.clear()
                if hasattr(self.main_window, "_snap_layer"):
                    self.main_window._snap_layer.hide_overlays()
        except Exception:
            pass

    def set_layout_edit_mode(self, enabled: bool) -> None:
        """Toggle Layout Edit Mode: when off, docks are locked; when on, docks movable/floatable."""
        try:
            self.main_window.layout_edit_mode = bool(enabled)
            for d in self.iter_docks():
                if self.main_window.layout_edit_mode:
                    d.setFeatures(
                        QDockWidget.DockWidgetMovable
                        | QDockWidget.DockWidgetFloatable
                        | QDockWidget.DockWidgetClosable
                    )
                else:
                    # Locked: disable moving and floating, keep closable so user can hide/pin panels
                    d.setFeatures(QDockWidget.DockWidgetClosable)
            self.enable_snap_handlers(self.main_window.layout_edit_mode)
            # Persist state for next launch
            settings = QSettings()
            settings.setValue("ui/layout_edit_mode", self.main_window.layout_edit_mode)
            # Status feedback
            try:
                self.main_window.statusBar().showMessage(
                    (
                        "Layout Edit Mode ON"
                        if self.main_window.layout_edit_mode
                        else "Layout locked"
                    ),
                    2000,
                )
            except Exception:
                pass
        except Exception as e:
            self.logger.warning("Failed to toggle Layout Edit Mode: %s", e)

    def snap_dock_to_edge(self, dock: QDockWidget, edge: str) -> bool:
        """Dock the provided QDockWidget to the specified edge if allowed."""
        area_map = {
            "left": Qt.LeftDockWidgetArea,
            "right": Qt.RightDockWidgetArea,
            "top": Qt.TopDockWidgetArea,
            "bottom": Qt.BottomDockWidgetArea,
        }
        target_area = area_map.get(edge)
        if target_area is None:
            return False
        allowed = dock.allowedAreas()
        if not (allowed & target_area):
            # Not permitted by this dock's allowed areas
            return False
        try:
            dock.setFloating(False)
        except Exception:
            pass
        # Perform docking
        self.main_window.addDockWidget(target_area, dock)
        try:
            dock.raise_()
        except Exception:
            pass
        try:
            self._schedule_layout_save()
        except Exception:
            pass
        return True

    def reset_dock_layout_and_save(self) -> None:
        """Reset layout to defaults and persist immediately."""
        self._reset_dock_layout()
        try:
            self._schedule_layout_save()
        except Exception:
            pass

    def create_metadata_dock(self) -> None:
        """Create the Metadata Manager dock and integrate it into the UI."""
        try:
            # Avoid recreating if it already exists
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                return
        except Exception:
            pass

        self.main_window.metadata_dock = QDockWidget("Metadata Editor", self.main_window)
        self.main_window.metadata_dock.setObjectName("MetadataDock")
        # Allow docking to any area for maximum flexibility
        self.main_window.metadata_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.main_window.metadata_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )

        try:
            from src.gui.metadata_editor import MetadataEditorWidget

            self.main_window.metadata_editor = MetadataEditorWidget(self.main_window)

            # Connect signals
            self.main_window.metadata_editor.metadata_saved.connect(self._on_metadata_saved)
            self.main_window.metadata_editor.metadata_changed.connect(self._on_metadata_changed)

            # Bottom tabs: Metadata | Notes | History
            self.main_window.metadata_tabs = QTabWidget(self.main_window)
            self.main_window.metadata_tabs.setObjectName("MetadataTabs")
            self.main_window.metadata_tabs.addTab(self.main_window.metadata_editor, "Metadata")

            # Notes tab (placeholder)
            notes_widget = QTextEdit()
            notes_widget.setReadOnly(True)
            notes_widget.setPlainText(
                "Notes\n\n"
                "Add project or model-specific notes here.\n"
                "Future: rich text, timestamps, and attachments."
            )
            self.main_window.metadata_tabs.addTab(notes_widget, "Notes")

            # History tab (placeholder)
            history_widget = QTextEdit()
            history_widget.setReadOnly(True)
            history_widget.setPlainText(
                "History\n\n" "Timeline of edits and metadata changes will appear here."
            )
            self.main_window.metadata_tabs.addTab(history_widget, "History")

            # Material Design theme is applied globally via ThemeService
            # No need to apply custom stylesheets here

            self.main_window.metadata_dock.setWidget(self.main_window.metadata_tabs)

            # Let qt-material handle all dock styling
            self.logger.info("Metadata editor widget created successfully (restored)")
        except Exception as e:
            self.logger.warning("Failed to create MetadataEditorWidget during restore: %s", e)

            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText("Metadata Editor\n\n" "Component unavailable.")
            self.main_window.metadata_dock.setWidget(metadata_widget)

        # Attach dock - default to right side but user can move anywhere
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.main_window.metadata_dock)
        try:
            self._register_dock_for_snapping(self.main_window.metadata_dock)
        except Exception:
            pass
        try:
            self._connect_layout_autosave(self.main_window.metadata_dock)
        except Exception:
            pass
        # Persist visibility and keep View menu action state in sync
        try:
            self.main_window.metadata_dock.visibilityChanged.connect(
                lambda _=False: self._save_metadata_panel_visibility()
            )
            self.main_window.metadata_dock.visibilityChanged.connect(
                lambda _=False: self._update_metadata_action_state()
            )
        except Exception:
            pass

    def restore_metadata_manager(self) -> None:
        """Restore and show the Metadata Manager panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            if (
                not hasattr(self.main_window, "metadata_dock")
                or self.main_window.metadata_dock is None
            ):
                self.create_metadata_dock()
            else:
                # Ensure it has a widget; recreate contents if missing
                try:
                    has_widget = self.main_window.metadata_dock.widget() is not None
                except Exception:
                    has_widget = False
                if not has_widget:
                    try:
                        self.main_window.removeDockWidget(self.main_window.metadata_dock)
                    except Exception:
                        pass
                    self.main_window.metadata_dock = None
                    self.create_metadata_dock()

            # Dock to default right side and show (user can move)
            try:
                self.snap_dock_to_edge(self.main_window.metadata_dock, "right")
            except Exception:
                pass
            try:
                self.main_window.metadata_dock.show()
                self.main_window.metadata_dock.raise_()
            except Exception:
                pass

            # Persist visibility and menu state
            try:
                self._save_metadata_panel_visibility()
            except Exception:
                pass
            try:
                self._update_metadata_action_state()
            except Exception:
                pass
            try:
                self._schedule_layout_save()
            except Exception:
                pass

            try:
                self.main_window.statusBar().showMessage("Metadata Manager restored", 2000)
            except Exception:
                pass
        except Exception as e:
            self.logger.error("Failed to restore Metadata Manager: %s", e)

    def create_model_library_dock(self) -> None:
        """Create the Model Library dock and integrate it into the UI."""
        try:
            if (
                hasattr(self.main_window, "model_library_dock")
                and self.main_window.model_library_dock
            ):
                return
        except Exception:
            pass

        self.main_window.model_library_dock = QDockWidget("Model Library", self.main_window)
        self.main_window.model_library_dock.setObjectName("ModelLibraryDock")
        # Allow docking to any area for maximum flexibility
        self.main_window.model_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.main_window.model_library_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )

        try:
            from src.gui.model_library import ModelLibraryWidget

            self.main_window.model_library_widget = ModelLibraryWidget(self.main_window)

            # Connect signals
            self.main_window.model_library_widget.model_selected.connect(self._on_model_selected)
            self.main_window.model_library_widget.model_double_clicked.connect(
                self._on_model_double_clicked
            )
            self.main_window.model_library_widget.models_added.connect(self._on_models_added)

            self.main_window.model_library_dock.setWidget(self.main_window.model_library_widget)

            # Let qt-material handle all dock styling
        except Exception as e:
            # Fallback widget
            lib_placeholder = QTextEdit()
            lib_placeholder.setReadOnly(True)
            lib_placeholder.setPlainText("Model Library\n\nComponent unavailable.")
            self.main_window.model_library_dock.setWidget(lib_placeholder)

        # Attach dock - default to left side but user can move anywhere
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.main_window.model_library_dock)
        try:
            self._register_dock_for_snapping(self.main_window.model_library_dock)
        except Exception:
            pass
        try:
            self._connect_layout_autosave(self.main_window.model_library_dock)
        except Exception:
            pass
        try:
            self.main_window.model_library_dock.visibilityChanged.connect(
                lambda _=False: self._update_library_action_state()
            )
        except Exception:
            pass
        try:
            self._update_library_action_state()
        except Exception:
            pass

    def restore_model_library(self) -> None:
        """Restore and show the Model Library panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            recreate = False
            if (
                not hasattr(self.main_window, "model_library_dock")
                or self.main_window.model_library_dock is None
            ):
                recreate = True
            else:
                try:
                    has_widget = self.main_window.model_library_dock.widget() is not None
                except Exception:
                    has_widget = False
                if not has_widget:
                    try:
                        self.main_window.removeDockWidget(self.main_window.model_library_dock)
                    except Exception:
                        pass
                    self.main_window.model_library_dock = None
                    recreate = True

            if recreate:
                self.create_model_library_dock()

            # Dock to default left side and show (user can move)
            try:
                self.snap_dock_to_edge(self.main_window.model_library_dock, "left")
            except Exception:
                pass
            try:
                self.main_window.model_library_dock.show()
                self.main_window.model_library_dock.raise_()
            except Exception:
                pass

            # Persist menu/action state and layout
            try:
                self._update_library_action_state()
            except Exception:
                pass
            try:
                self._schedule_layout_save()
            except Exception:
                pass

            try:
                self.main_window.statusBar().showMessage("Model Library restored", 2000)
            except Exception:
                pass
        except Exception as e:
            self.logger.error("Failed to restore Model Library: %s", e)

    def update_library_action_state(self) -> None:
        """Enable/disable 'Show Model Library' based on panel visibility."""
        try:
            visible = False
            if (
                hasattr(self.main_window, "model_library_dock")
                and self.main_window.model_library_dock
            ):
                visible = bool(self.main_window.model_library_dock.isVisible())
            if (
                hasattr(self.main_window, "show_model_library_action")
                and self.main_window.show_model_library_action
            ):
                self.main_window.show_model_library_action.setEnabled(not visible)
        except Exception:
            pass

    def update_metadata_action_state(self) -> None:
        """Enable/disable 'Show Metadata Manager' based on panel visibility."""
        try:
            visible = False
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                visible = bool(self.main_window.metadata_dock.isVisible())
            if (
                hasattr(self.main_window, "show_metadata_action")
                and self.main_window.show_metadata_action
            ):
                self.main_window.show_metadata_action.setEnabled(not visible)
        except Exception:
            pass

    def save_metadata_panel_visibility(self) -> None:
        """Persist the metadata panel visibility state."""
        try:
            if hasattr(self.main_window, "metadata_dock") and self.main_window.metadata_dock:
                settings = QSettings()
                vis = bool(self.main_window.metadata_dock.isVisible())
                settings.setValue("metadata_panel/visible", vis)
                self.logger.debug("Saved metadata panel visibility: %s", vis)
        except Exception as e:
            self.logger.warning("Failed to save metadata panel visibility: %s", e)

    # Helper methods that need to be connected to actual implementations
    def _setup_dock_context_menu(self, dock: QDockWidget, default_area: Qt.DockWidgetArea) -> None:
        """Set up context menu for dock widget."""
        # This would need to be implemented or connected to the main window's method
        if hasattr(self.main_window, "_setup_dock_context_menu"):
            self.main_window._setup_dock_context_menu(dock, default_area)

    def _register_dock_for_snapping(self, dock: QDockWidget) -> None:
        """Register dock for snapping functionality."""
        if hasattr(self.main_window, "_register_dock_for_snapping"):
            self.main_window._register_dock_for_snapping(dock)

    def _connect_layout_autosave(self, dock: QDockWidget) -> None:
        """Connect dock to layout autosave system."""
        if hasattr(self.main_window, "_connect_layout_autosave"):
            self.main_window._connect_layout_autosave(dock)

    def _update_library_action_state(self) -> None:
        """Update library action state."""
        if hasattr(self.main_window, "_update_library_action_state"):
            self.main_window._update_library_action_state()

    def _update_metadata_action_state(self) -> None:
        """Update metadata action state."""
        if hasattr(self.main_window, "_update_metadata_action_state"):
            self.main_window._update_metadata_action_state()

    def _save_metadata_panel_visibility(self) -> None:
        """Save metadata panel visibility."""
        if hasattr(self.main_window, "_save_metadata_panel_visibility"):
            self.main_window._save_metadata_panel_visibility()

    def _save_default_layout_state(self) -> None:
        """Save default layout state."""
        if hasattr(self.main_window, "_save_default_layout_state"):
            self.main_window._save_default_layout_state()

    def _save_current_layout_as_default(self) -> None:
        """Save current layout as default."""
        if hasattr(self.main_window, "_save_current_layout_as_default"):
            self.main_window._save_current_layout_as_default()

    def _init_layout_persistence(self) -> None:
        """Initialize layout persistence."""
        if hasattr(self.main_window, "_init_layout_persistence"):
            self.main_window._init_layout_persistence()

    def _load_saved_layout(self) -> None:
        """Load saved layout."""
        if hasattr(self.main_window, "_load_saved_layout"):
            self.main_window._load_saved_layout()

    def _schedule_layout_save(self) -> None:
        """Schedule layout save."""
        if hasattr(self.main_window, "_schedule_layout_save"):
            self.main_window._schedule_layout_save()

    def _reset_dock_layout(self) -> None:
        """Reset dock layout."""
        if hasattr(self.main_window, "_reset_dock_layout"):
            self.main_window._reset_dock_layout()

    def _on_model_selected(self, model_id: int) -> None:
        """Handle model selection."""
        if hasattr(self.main_window, "_on_model_selected"):
            self.main_window._on_model_selected(model_id)

    def _on_model_double_clicked(self, model_id: int) -> None:
        """Handle model double-click."""
        if hasattr(self.main_window, "_on_model_double_clicked"):
            self.main_window._on_model_double_clicked(model_id)

    def _on_models_added(self, model_ids: List[int]) -> None:
        """Handle models added."""
        if hasattr(self.main_window, "_on_models_added"):
            self.main_window._on_models_added(model_ids)

    def _on_metadata_saved(self, model_id: int) -> None:
        """Handle metadata saved."""
        if hasattr(self.main_window, "_on_metadata_saved"):
            self.main_window._on_metadata_saved(model_id)

    def _on_metadata_changed(self, model_id: int) -> None:
        """Handle metadata changed."""
        if hasattr(self.main_window, "_on_metadata_changed"):
            self.main_window._on_metadata_changed(model_id)


# Convenience function for easy dock management setup
def setup_dock_management(
    main_window: QMainWindow, logger: Optional[logging.Logger] = None
) -> DockManager:
    """
    Convenience function to set up dock management for a main window.

    Args:
        main_window: The main window to set up dock management for
        logger: Optional logger instance

    Returns:
        DockManager instance for further dock operations
    """
    manager = DockManager(main_window, logger)
    manager.setup_dock_widgets()
    return manager
