"""
Metadata Manager for MainWindow.

Handles metadata panel management, visibility binding, and metadata events.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QMainWindow


class MetadataManager:
    """Manages metadata panel and metadata-related operations."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the metadata manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def setup_metadata_visibility_binding(self) -> None:
        """Set up metadata visibility binding with tab changes.

        When Model Previewer tab is hidden, metadata dock is hidden.
        When Model Previewer tab is shown, metadata dock is shown.
        """
        try:
            # Connect tab change signal to update metadata visibility
            if hasattr(self.main_window, "hero_tabs"):
                self.main_window.hero_tabs.currentChanged.connect(self._on_tab_changed)

            # Ensure metadata dock is visible initially
            if hasattr(self.main_window, "metadata_dock"):
                self.main_window.metadata_dock.show()
                self.main_window.metadata_dock.raise_()
                self.logger.debug("Metadata dock shown (initial state)")

            self.logger.debug("Metadata visibility binding established")
        except Exception as e:
            self.logger.warning("Failed to setup metadata visibility binding: %s", e)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event."""
        self.update_metadata_visibility()

    def update_metadata_visibility(self) -> None:
        """Update metadata dock visibility based on active tab."""
        try:
            if not hasattr(self.main_window, "metadata_dock"):
                return

            if not hasattr(self.main_window, "hero_tabs"):
                return

            # Find the Model Previewer tab index
            model_previewer_index = -1
            for i in range(self.main_window.hero_tabs.count()):
                if self.main_window.hero_tabs.tabText(i) in (
                    "Model Previewer",
                    "3D Viewer",
                ):
                    model_previewer_index = i
                    break

            current_index = self.main_window.hero_tabs.currentIndex()

            # Show metadata dock only if Model Previewer is active
            if model_previewer_index >= 0 and current_index == model_previewer_index:
                self.main_window.metadata_dock.show()
                self.main_window.metadata_dock.raise_()
                self.logger.debug("Metadata dock shown (Model Previewer tab active)")
            else:
                self.main_window.metadata_dock.hide()
                self.logger.debug("Metadata dock hidden (Model Previewer tab inactive)")

        except Exception as e:
            self.logger.warning("Failed to update metadata visibility: %s", e)

    def update_metadata_action_state(self) -> None:
        """Enable/disable 'Show Metadata Manager' based on panel visibility."""
        try:
            visible = False
            if (
                hasattr(self.main_window, "metadata_dock")
                and self.main_window.metadata_dock
            ):
                visible = bool(self.main_window.metadata_dock.isVisible())

            if hasattr(self.main_window, "show_metadata_action"):
                if self.main_window.show_metadata_action:
                    self.main_window.show_metadata_action.setEnabled(not visible)
        except Exception:
            pass

    def save_metadata_panel_visibility(self) -> None:
        """Persist the metadata panel visibility state."""
        try:
            if not hasattr(self.main_window, "metadata_dock"):
                return

            if self.main_window.metadata_dock is None:
                return

            settings = QSettings()
            vis = bool(self.main_window.metadata_dock.isVisible())
            settings.setValue("metadata_panel/visible", vis)
            self.logger.debug("Saved metadata panel visibility: %s", vis)
        except Exception as e:
            self.logger.warning("Failed to save metadata panel visibility: %s", e)

    def load_metadata_panel_visibility(self) -> bool:
        """Load and restore the metadata panel visibility state."""
        try:
            if not hasattr(self.main_window, "metadata_dock"):
                return False

            if self.main_window.metadata_dock is None:
                return False

            settings = QSettings()
            if settings.contains("metadata_panel/visible"):
                vis = settings.value("metadata_panel/visible", True, type=bool)
                self.main_window.metadata_dock.setVisible(vis)
                self.logger.debug("Restored metadata panel visibility: %s", vis)
                return True
        except Exception as e:
            self.logger.warning("Failed to load metadata panel visibility: %s", e)

        return False

    def on_metadata_saved(self, model_id: int) -> None:
        """Handle metadata saved event from the metadata editor."""
        try:
            self.logger.info("Metadata saved for model ID: %s", model_id)
            self.main_window.status_label.setText("Metadata saved")

            # Update the model library to reflect changes
            if hasattr(self.main_window, "model_library_widget"):
                self.main_window.model_library_widget._load_models_from_database()

            # Clear status after a delay
            QTimer.singleShot(
                3000, lambda: self.main_window.status_label.setText("Ready")
            )

        except Exception as e:
            self.logger.error("Failed to handle metadata saved event: %s", str(e))

    def on_metadata_changed(self, model_id: int) -> None:
        """Handle metadata changed event from the metadata editor."""
        try:
            self.logger.debug("Metadata changed for model ID: %s", model_id)
            self.main_window.status_label.setText("Metadata modified (unsaved changes)")

            # Refresh the model display in the library to show updated metadata
            if hasattr(self.main_window, "model_library_widget"):
                if self.main_window.model_library_widget:
                    self.main_window.model_library_widget._refresh_model_display(
                        model_id
                    )

        except Exception as e:
            self.logger.error("Failed to handle metadata changed event: %s", str(e))
