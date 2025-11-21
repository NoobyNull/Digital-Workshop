"""
Project Manager for MainWindow.

Handles project operations and project-related events.
Extracted from MainWindow to reduce monolithic class size.
"""

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow


class ProjectManager:
    """Manages project operations and interactions."""

    def __init__(self, main_window: QMainWindow, logger: logging.Logger):
        """
        Initialize the project manager.

        Args:
            main_window: The main window instance
            logger: Logger instance
        """
        self.main_window = main_window
        self.logger = logger

    def update_project_details_visibility(self) -> None:
        """Update project details dock visibility based on active tab.

        Project details is visible when Model Previewer OR Project Cost Estimator is active.
        """
        try:
            if not hasattr(self.main_window, "properties_dock"):
                return

            if not hasattr(self.main_window, "hero_tabs"):
                return

            # Find the Model Previewer and Cost Estimator tab indices
            model_previewer_index = -1
            cost_estimator_index = -1

            for i in range(self.main_window.hero_tabs.count()):
                tab_text = self.main_window.hero_tabs.tabText(i)
                if tab_text in ("Model Previewer", "3D Viewer"):
                    model_previewer_index = i
                elif tab_text == "Project Cost Estimator":
                    cost_estimator_index = i

            current_index = self.main_window.hero_tabs.currentIndex()

            # Show project details dock if Model Previewer OR Cost Estimator is active
            if (
                model_previewer_index >= 0 and current_index == model_previewer_index
            ) or (cost_estimator_index >= 0 and current_index == cost_estimator_index):
                self.main_window.properties_dock.show()
                self.main_window.properties_dock.raise_()
                self.logger.debug(
                    "Project details dock shown (Model Previewer or Cost Estimator tab active)"
                )
            else:
                self.main_window.properties_dock.hide()
                self.logger.debug("Project details dock hidden (other tab active)")

        except Exception as e:
            self.logger.warning("Failed to update project details visibility: %s", e)

    def update_project_manager_action_state(self) -> None:
        """Update project manager action state based on dock visibility."""
        try:
            if not hasattr(self.main_window, "project_manager_dock"):
                return

            if self.main_window.project_manager_dock is None:
                return

            # Update menu action if it exists
            if hasattr(self.main_window, "toggle_project_manager_action"):
                if self.main_window.toggle_project_manager_action:
                    self.main_window.toggle_project_manager_action.setChecked(
                        self.main_window.project_manager_dock.isVisible()
                    )

        except Exception as e:
            self.logger.debug("Failed to update project manager action state: %s", e)

    def on_project_opened(self, project_id: str) -> None:
        """Handle project opened event from project manager."""
        try:
            self.logger.info("Project opened: %s", project_id)
            self.main_window.status_label.setText(f"Project opened: {project_id}")

            # Set current project for all tabs that support tab data save/load
            if hasattr(self.main_window, "clo_widget") and self.main_window.clo_widget:
                try:
                    self.main_window.clo_widget.set_current_project(project_id)
                    self.logger.debug(
                        f"Set current project for Cut List Optimizer: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Cut List Optimizer: {e}"
                    )

            if (
                hasattr(self.main_window, "feeds_and_speeds_widget")
                and self.main_window.feeds_and_speeds_widget
            ):
                try:
                    self.main_window.feeds_and_speeds_widget.set_current_project(
                        project_id
                    )
                    self.logger.debug(
                        f"Set current project for Feeds & Speeds: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Feeds & Speeds: {e}"
                    )

            if (
                hasattr(self.main_window, "cost_estimator_widget")
                and self.main_window.cost_estimator_widget
            ):
                try:
                    self.main_window.cost_estimator_widget.set_current_project(
                        project_id
                    )
                    self.logger.debug(
                        f"Set current project for Cost Estimator: {project_id}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Cost Estimator: {e}"
                    )

            if (
                hasattr(self.main_window, "project_details_widget")
                and self.main_window.project_details_widget
            ):
                try:
                    self.main_window.project_details_widget.set_project_context(
                        project_id
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to set project for Project Details: {e}"
                    )

            # Clear status after a delay
            QTimer.singleShot(
                3000, lambda: self.main_window.status_label.setText("Ready")
            )

        except Exception as e:
            self.logger.error("Failed to handle project opened event: %s", str(e))

    def on_project_created(self, project_id: str) -> None:
        """Handle project created event from project manager."""
        try:
            self.logger.info("Project created: %s", project_id)
            self.main_window.status_label.setText(f"Project created: {project_id}")
            QTimer.singleShot(
                3000, lambda: self.main_window.status_label.setText("Ready")
            )

        except Exception as e:
            self.logger.error("Failed to handle project created event: %s", str(e))

    def on_project_deleted(self, project_id: str) -> None:
        """Handle project deleted event from project manager."""
        try:
            self.logger.info("Project deleted: %s", project_id)
            self.main_window.status_label.setText(f"Project deleted: {project_id}")
            QTimer.singleShot(
                3000, lambda: self.main_window.status_label.setText("Ready")
            )

        except Exception as e:
            self.logger.error("Failed to handle project deleted event: %s", str(e))
