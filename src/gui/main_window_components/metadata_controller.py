"""
Controller to build and wire the metadata dock away from the main window shell.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QTabWidget, QLabel, QSizePolicy

from src.gui.theme import MIN_WIDGET_SIZE


class MetadataController:
    """Encapsulates metadata dock creation and wiring."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)

    def setup_metadata_dock(self) -> None:
        """Create and attach the metadata dock."""
        try:
            dock = QDockWidget("Metadata Editor", self.main)
            dock.setObjectName("MetadataDock")
            dock.setAllowedAreas(
                Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.BottomDockWidgetArea
            )
            dock.setFeatures(QDockWidget.DockWidgetClosable)

            try:
                from src.gui.metadata_editor import MetadataEditorWidget

                editor = MetadataEditorWidget(self.main)
                editor.metadata_saved.connect(self.main._on_metadata_saved)
                editor.metadata_changed.connect(self.main._on_metadata_changed)

                tabs = QTabWidget(self.main)
                tabs.setObjectName("MetadataTabs")
                tabs.addTab(editor, "Metadata")

                notes_widget = QLabel(
                    "Notes\n\n"
                    "Add project or model-specific notes here.\n"
                    "Future: rich text, timestamps, and attachments."
                )
                notes_widget.setAlignment(Qt.AlignCenter)
                notes_widget.setWordWrap(True)
                tabs.addTab(notes_widget, "Notes")

                history_widget = QLabel(
                    "History\n\n"
                    "Timeline of edits and metadata changes will appear here."
                )
                history_widget.setAlignment(Qt.AlignCenter)
                history_widget.setWordWrap(True)
                tabs.addTab(history_widget, "History")

                dock.setWidget(tabs)

                self.main.metadata_editor = editor
                self.main.metadata_tabs = tabs
            except Exception as exc:
                if self.logger:
                    self.logger.warning("Failed to create metadata editor: %s", exc)
                fallback_widget = QLabel("Metadata Editor\n\nComponent unavailable.")
                fallback_widget.setAlignment(Qt.AlignCenter)
                fallback_widget.setWordWrap(True)
                dock.setWidget(fallback_widget)

            self.main.addDockWidget(Qt.RightDockWidgetArea, dock)

            try:
                self.main._register_dock_for_snapping(dock)
            except Exception as exc:
                if self.logger:
                    self.logger.debug("Failed to register dock for snapping: %s", exc)

            try:
                if getattr(self.main, "properties_dock", None):
                    self.main.tabifyDockWidget(self.main.properties_dock, dock)
                    if self.logger:
                        self.logger.info(
                            "Properties and Metadata docks tabified using native Qt"
                        )
            except Exception as exc:
                if self.logger:
                    self.logger.debug("Could not tabify docks: %s", exc)

            dock.setMinimumWidth(MIN_WIDGET_SIZE)
            dock.setMaximumWidth(500)
            dock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

            dock.visibilityChanged.connect(
                lambda visible: self.main._update_metadata_action_state()
            )

            self.main.metadata_dock = dock
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to setup metadata dock: %s", exc)
