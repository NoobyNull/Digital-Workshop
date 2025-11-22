"""
UI event handling extracted from main_window.py.

Handles preferences/theme, viewer/AI settings changes, help/about, and screenshot/thumbnails events.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox


class UIEventsController:
    """Encapsulates UI event handlers for the main window."""

    def __init__(self, main_window) -> None:
        self.main = main_window
        self.logger = getattr(main_window, "logger", None)

    # Preferences / theme / settings ---------------------------------------
    def show_preferences(self) -> None:
        """Show preferences dialog."""
        self.logger.info("Opening preferences dialog")
        from src.gui.preferences import PreferencesDialog

        dlg = PreferencesDialog(
            self.main,
            on_reset_layout=self.main.layout_controller.reset_layout,
            on_save_layout_default=self.main.layout_controller.save_current_layout_as_default,
        )
        dlg.theme_changed.connect(self.on_theme_changed)
        dlg.viewer_settings_changed.connect(self.on_viewer_settings_changed)
        dlg.ai_settings_changed.connect(self.on_ai_settings_changed)
        if hasattr(dlg, "general_settings_changed"):
            dlg.general_settings_changed.connect(
                self.main._on_workspace_settings_changed
            )
        dlg.exec_()

    def on_theme_changed(self) -> None:
        """Handle theme change from preferences dialog."""
        self.logger.debug("Theme changed - qt-material handling automatically")
        updater = getattr(self.main.status_bar_manager, "_update_theme_icon", None)
        if callable(updater):
            updater()

    def on_viewer_settings_changed(self) -> None:
        """Handle viewer settings change from preferences dialog."""
        try:
            self.logger.info("=== VIEWER SETTINGS CHANGED SIGNAL RECEIVED ===")
            try:
                if hasattr(self.main, "viewer_widget") and self.main.viewer_widget:
                    self.logger.info("Reloading viewer settings...")
                    if hasattr(self.main.viewer_widget, "reload_settings"):
                        self.main.viewer_widget.reload_settings()
                else:
                    self.logger.warning("Viewer widget not available; skipping reload")
            except Exception as viewer_err:
                self.logger.error(
                    "Failed to reload viewer settings: %s", viewer_err, exc_info=True
                )

            try:
                if hasattr(self.main, "clo_widget") and self.main.clo_widget:
                    self.main.clo_widget.reload_grid_settings()
            except Exception as clo_error:  # pragma: no cover - defensive
                self.logger.error(
                    "Failed to reload CLO grid settings after viewer settings change: %s",
                    clo_error,
                    exc_info=True,
                )

            self.logger.info("=== VIEWER SETTINGS CHANGE HANDLING COMPLETE ===")
        except Exception as exc:
            self.logger.error(
                f"FATAL ERROR applying viewer settings: {exc}", exc_info=True
            )

    def on_ai_settings_changed(self) -> None:
        """Handle AI settings change from preferences dialog."""
        try:
            self.logger.info("=== AI SETTINGS CHANGED SIGNAL RECEIVED ===")
            if self.main.ai_service:
                self.logger.info("Reloading AI service configuration...")
                self.main.ai_service.reload_configuration()
                self.logger.info(
                    "AI service reloaded. Available providers: %s",
                    list(self.main.ai_service.providers.keys()),
                )
            else:
                self.logger.warning(
                    "AI service not available or locked, skipping reload"
                )
            self.logger.info("=== AI SETTINGS CHANGE HANDLING COMPLETE ===")
        except Exception as exc:
            self.logger.error("ERROR reloading AI service: %s", exc, exc_info=True)

    def show_theme_manager(self) -> None:
        """Show the Theme Manager dialog and hook apply signal."""
        try:
            from src.gui.theme.ui.theme_dialog import ThemeDialog

            dlg = ThemeDialog(self.main)
            dlg.theme_applied.connect(self.on_theme_applied)
            dlg.exec()
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to open Theme Manager: %s", exc)
            QMessageBox.warning(
                self.main, "Theme Manager", f"Failed to open Theme Manager:\n{exc}"
            )

    def on_theme_applied(self, preset_name: str) -> None:
        """Handle theme change notification."""
        if self.logger:
            self.logger.info("Theme changed: %s", preset_name)

    def cycle_theme(self) -> None:
        """Cycle through Light, Dark, and System themes."""
        try:
            from src.gui.theme.simple_service import ThemeService

            service = ThemeService.instance()
            current_theme, _ = service.get_current_theme()
            themes = ["light", "dark", "auto"]
            current_index = (
                themes.index(current_theme) if current_theme in themes else 0
            )
            next_theme = themes[(current_index + 1) % len(themes)]
            service.apply_theme(next_theme, "qt-material")
            theme_names = {"light": "Light", "dark": "Dark", "auto": "System"}
            self._set_status(f"Theme: {theme_names.get(next_theme, next_theme)}", 2000)
            updater = getattr(self.main.status_bar_manager, "_update_theme_icon", None)
            if callable(updater):
                updater()
            if self.logger:
                self.logger.info(
                    "Cycled theme from %s to %s", current_theme, next_theme
                )
        except Exception as exc:
            if self.logger:
                self.logger.error("Failed to cycle theme: %s", exc)
            self._set_status("Theme cycle failed", 2000)

    # Help / about ---------------------------------------------------------
    def show_help(self) -> None:
        """Show searchable help dialog."""
        try:
            from src.gui.help_system import HelpDialog

            help_dialog = HelpDialog(self.main)
            help_dialog.exec()
        except Exception as exc:
            if self.logger:
                self.logger.error("Error showing help dialog: %s", exc)
            QMessageBox.warning(
                self.main, "Help Error", f"Could not open help system: {exc}"
            )

    # Screenshots / thumbnails ---------------------------------------------
    def on_screenshot_progress(self, current: int, total: int) -> None:
        """Handle screenshot generation progress."""
        try:
            if total > 0:
                progress = int((current / total) * 100)
                if hasattr(self.main, "progress_bar"):
                    self.main.progress_bar.setValue(progress)
                if hasattr(self.main, "status_label"):
                    self.main.status_label.setText(
                        f"Generating screenshots: {current}/{total}"
                    )
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to update screenshot progress: %s", exc)

    def on_screenshot_generated(self, model_id: int, screenshot_path: str) -> None:
        """Handle screenshot generated event."""
        try:
            if self.logger:
                self.logger.debug(
                    "Screenshot generated for model %s: %s", model_id, screenshot_path
                )
        except Exception as exc:
            if self.logger:
                self.logger.warning(
                    "Failed to handle screenshot generated event: %s", exc
                )

    def on_screenshot_error(self, error_message: str) -> None:
        """Handle screenshot generation error."""
        try:
            if self.logger:
                self.logger.error("Screenshot generation error: %s", error_message)
            if hasattr(self.main, "status_label"):
                self.main.status_label.setText(f"Error: {error_message}")
        except Exception as exc:
            if self.logger:
                self.logger.warning("Failed to handle screenshot error: %s", exc)

    def on_screenshots_finished(self) -> None:
        """Handle batch screenshot generation completion."""
        try:
            if hasattr(self.main, "progress_bar"):
                self.main.progress_bar.setVisible(False)
            if hasattr(self.main, "status_label"):
                self.main.status_label.setText("Screenshots generated successfully")

            if (
                hasattr(self.main, "model_library_widget")
                and self.main.model_library_widget
            ):
                self.main.model_library_widget.refresh_models_from_database()

            QMessageBox.information(
                self.main,
                "Screenshot Generation Complete",
                "All model screenshots have been generated successfully!",
            )

            if self.logger:
                self.logger.info("Batch screenshot generation completed")

            QTimer.singleShot(3000, lambda: self._set_status("Ready"))
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "Failed to handle screenshots finished event: %s", exc
                )

    def on_library_thumbnails_completed(self) -> None:
        """Handle library thumbnail generation completion."""
        try:
            if (
                hasattr(self.main, "model_library_widget")
                and self.main.model_library_widget
            ):
                self.main.model_library_widget.refresh_models_from_database()
            if self.logger:
                self.logger.info("Library thumbnail generation completed")
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "Failed to handle library thumbnails completion: %s", exc
                )

    # ----------------------------------------------------------------------
    def _set_status(self, text: str, clear_after_ms: Optional[int] = None) -> None:
        if hasattr(self.main, "status_label"):
            self.main.status_label.setText(text)
        if clear_after_ms:
            QTimer.singleShot(clear_after_ms, lambda: self._set_status("Ready"))
