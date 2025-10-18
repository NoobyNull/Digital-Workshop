"""
Dock management for main window.

Handles creation and management of dock widgets (metadata, library).
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QTextEdit, QTabWidget

from src.core.logging_config import get_logger, log_function_call
from src.gui.theme import ThemeManager


logger = get_logger(__name__)


class DockManager:
    """Manages dock widgets in the main window."""

    def __init__(self, main_window):
        """
        Initialize dock manager.

        Args:
            main_window: The main window instance
        """
        self.main_window = main_window

    @log_function_call(logger)
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
            self.main_window.metadata_editor.metadata_saved.connect(
                self.main_window._on_metadata_saved
            )
            self.main_window.metadata_editor.metadata_changed.connect(
                self.main_window._on_metadata_changed
            )

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

            self.main_window.metadata_dock.setWidget(self.main_window.metadata_tabs)

            # Theme the dock header
            try:
                tm = ThemeManager.instance()
                _dock_css_meta = """
                    QDockWidget#MetadataDock::title {
                        background-color: {{dock_title_bg}};
                        color: {{text}};
                        border-bottom: 1px solid {{dock_title_border}};
                        padding: 6px;
                    }
                """
                tm.register_widget(self.main_window.metadata_dock, css_text=_dock_css_meta)
                tm.apply_stylesheet(self.main_window.metadata_dock)
            except Exception:
                pass

            logger.info("Metadata editor widget created successfully")

        except Exception as e:
            logger.warning(f"Failed to create MetadataEditorWidget: {e}")

            # Fallback to placeholder
            metadata_widget = QTextEdit()
            metadata_widget.setReadOnly(True)
            metadata_widget.setPlainText("Metadata Editor\n\nComponent unavailable.")
            self.main_window.metadata_dock.setWidget(metadata_widget)

        # Attach dock
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.main_window.metadata_dock)

        # Connect signals
        try:
            self.main_window.metadata_dock.visibilityChanged.connect(
                lambda _=False: self.main_window._save_metadata_panel_visibility()
            )
            self.main_window.metadata_dock.visibilityChanged.connect(
                lambda _=False: self.main_window._update_metadata_action_state()
            )
        except Exception:
            pass

    @log_function_call(logger)
    def restore_metadata_manager(self) -> None:
        """Restore and show the Metadata Manager panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            if not hasattr(self.main_window, "metadata_dock") or self.main_window.metadata_dock is None:
                self.create_metadata_dock()
            else:
                # Ensure it has a widget
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

            # Show dock
            try:
                self.main_window.metadata_dock.show()
                self.main_window.metadata_dock.raise_()
            except Exception:
                pass

            # Persist visibility and menu state
            try:
                self.main_window._save_metadata_panel_visibility()
                self.main_window._update_metadata_action_state()
                self.main_window._schedule_layout_save()
            except Exception:
                pass

            try:
                self.main_window.statusBar().showMessage("Metadata Manager restored", 2000)
            except Exception:
                pass

            logger.info("Metadata Manager restored")

        except Exception as e:
            logger.error(f"Failed to restore Metadata Manager: {e}")

    @log_function_call(logger)
    def create_model_library_dock(self) -> None:
        """Create the Model Library dock and integrate it into the UI."""
        try:
            if hasattr(self.main_window, "model_library_dock") and self.main_window.model_library_dock:
                return
        except Exception:
            pass

        self.main_window.model_library_dock = QDockWidget("Model Library", self.main_window)
        self.main_window.model_library_dock.setObjectName("ModelLibraryDock")
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
            self.main_window.model_library_widget.model_selected.connect(
                self.main_window._on_model_selected
            )
            self.main_window.model_library_widget.model_double_clicked.connect(
                self.main_window._on_model_double_clicked
            )
            self.main_window.model_library_widget.models_added.connect(
                self.main_window._on_models_added
            )

            self.main_window.model_library_dock.setWidget(self.main_window.model_library_widget)

            # Theme the dock header
            try:
                tm = ThemeManager.instance()
                _dock_css_ml = """
                    QDockWidget#ModelLibraryDock::title {
                        background-color: {{dock_title_bg}};
                        color: {{text}};
                        border-bottom: 1px solid {{dock_title_border}};
                        padding: 6px;
                    }
                """
                tm.register_widget(self.main_window.model_library_dock, css_text=_dock_css_ml)
                tm.apply_stylesheet(self.main_window.model_library_dock)
            except Exception:
                pass

            logger.info("Model Library widget created successfully")

        except Exception as e:
            logger.warning(f"Failed to create ModelLibraryWidget: {e}")

            # Fallback widget
            lib_placeholder = QTextEdit()
            lib_placeholder.setReadOnly(True)
            lib_placeholder.setPlainText("Model Library\n\nComponent unavailable.")
            self.main_window.model_library_dock.setWidget(lib_placeholder)

        # Attach dock
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.main_window.model_library_dock)

        # Connect signals
        try:
            self.main_window.model_library_dock.visibilityChanged.connect(
                lambda _=False: self.main_window._update_library_action_state()
            )
            self.main_window._update_library_action_state()
        except Exception:
            pass

    @log_function_call(logger)
    def restore_model_library(self) -> None:
        """Restore and show the Model Library panel if it was closed or missing."""
        try:
            # Create or recreate the dock as needed
            recreate = False
            if not hasattr(self.main_window, "model_library_dock") or self.main_window.model_library_dock is None:
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

            # Show dock
            try:
                self.main_window.model_library_dock.show()
                self.main_window.model_library_dock.raise_()
            except Exception:
                pass

            # Persist menu/action state and layout
            try:
                self.main_window._update_library_action_state()
                self.main_window._schedule_layout_save()
            except Exception:
                pass

            try:
                self.main_window.statusBar().showMessage("Model Library restored", 2000)
            except Exception:
                pass

            logger.info("Model Library restored")

        except Exception as e:
            logger.error(f"Failed to restore Model Library: {e}")

    def update_library_action_state(self) -> None:
        """Enable/disable 'Show Model Library' based on panel visibility."""
        try:
            visible = False
            if hasattr(self.main_window, "model_library_dock") and self.main_window.model_library_dock:
                visible = bool(self.main_window.model_library_dock.isVisible())

            if hasattr(self.main_window, "show_library_action") and self.main_window.show_library_action:
                self.main_window.show_library_action.setEnabled(not visible)

        except Exception:
            pass

