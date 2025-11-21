"""Preferences dialog with tabbed interface."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

from src.gui.preferences.tabs import (
    AdvancedTab,
    AITab,
    GeneralTab,
    ThumbnailSettingsTab,
    ViewerSettingsTab,
    InvoicePreferencesTab,
    ImportSettingsTab,
)
from src.gui.files_components.files_tab_widget import FilesTab


class PreferencesDialog(QDialog):
    """Application preferences dialog with multiple tabs.

    Emits theme_changed whenever the Theming tab applies updates. Emits
    viewer_settings_changed whenever viewer settings are modified. Emits
    ai_settings_changed whenever AI settings are modified.
    """

    theme_changed = Signal()
    viewer_settings_changed = Signal()
    ai_settings_changed = Signal()
    general_settings_changed = Signal()

    def __init__(
        self,
        parent=None,
        on_reset_layout: Callable | None = None,
        on_save_layout_default: Callable | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.on_reset_layout = on_reset_layout
        self.on_save_layout_default = on_save_layout_default
        self._was_saved = False

        self._setup_ui()
        # Always start on General tab (index 0)
        self.tabs.setCurrentIndex(0)

    def _setup_ui(self) -> None:
        """Set up the preferences dialog UI."""
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.general_tab = GeneralTab(
            on_reset_layout=self.on_reset_layout,
            on_save_layout_default=self.on_save_layout_default,
        )
        self.viewer_settings_tab = ViewerSettingsTab()
        self.thumbnail_settings_tab = ThumbnailSettingsTab()
        self.files_tab = FilesTab()
        self.ai_tab = AITab()
        self.advanced_tab = AdvancedTab()
        self.invoice_tab = InvoicePreferencesTab()
        self.import_tab = ImportSettingsTab()

        # Add tabs
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.viewer_settings_tab, "3D Viewer")
        self.tabs.addTab(self.thumbnail_settings_tab, "Content")
        self.tabs.addTab(self.files_tab, "Model Library")
        self.tabs.addTab(self.import_tab, "Imports")
        self.tabs.addTab(self.invoice_tab, "Invoices")
        self.tabs.addTab(self.ai_tab, "AI")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        # Dialog buttons
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_save = QPushButton("Save")
        self.btn_close = QPushButton("Close")

        buttons_row.addWidget(self.btn_reset)
        buttons_row.addWidget(self.btn_save)
        buttons_row.addWidget(self.btn_close)

        layout.addLayout(buttons_row)

        # Connect signals
        self.btn_close.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save_and_notify)
        self.btn_reset.clicked.connect(self._reset_to_defaults)

    def _restore_last_tab(self) -> None:
        """Restore the last selected tab from QSettings."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.logging_config import get_logger

            settings = QSettings()
            last_tab = settings.value("preferences/last_tab_index", 0, type=int)

            logger = get_logger(__name__)
            logger.debug("Restoring preferences tab index: %s", last_tab)

            if 0 <= last_tab < self.tabs.count():
                self.tabs.setCurrentIndex(last_tab)
            else:
                self.tabs.setCurrentIndex(0)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            try:
                from src.core.logging_config import get_logger

                logger = get_logger(__name__)
                logger.error("Failed to restore tab index: %s", e)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
                pass

    def _save_current_tab(self, index: int) -> None:
        """Save the current tab index to QSettings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            settings.setValue("preferences/last_tab_index", index)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

    def _on_theme_live_applied(self) -> None:
        """Handle theme live apply."""
        self.theme_changed.emit()

    def _save_and_notify(self) -> None:
        """Save all settings and notify listeners."""
        try:
            self.general_tab.save_settings()
            self.viewer_settings_tab.save_settings()
            self.thumbnail_settings_tab.save_settings()
            self.invoice_tab.save_settings()
            self.import_tab.save_settings()
            self.ai_tab.save_settings()
            self.advanced_tab.save_settings()

            self.theme_changed.emit()
            self.viewer_settings_changed.emit()
            self.ai_settings_changed.emit()
            self.general_settings_changed.emit()
            self._was_saved = True
            self.accept()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            try:
                from src.core.logging_config import get_logger

                logger = get_logger(__name__)
                logger.error("Failed to save preferences: %s", e)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
                pass

    def _save_silent(self) -> None:
        """Persist settings without closing signals or prompts."""
        try:
            self.general_tab.save_settings()
            self.viewer_settings_tab.save_settings()
            self.thumbnail_settings_tab.save_settings()
            self.invoice_tab.save_settings()
            self.import_tab.save_settings()
            self.ai_tab.save_settings()
            self.advanced_tab.save_settings()
            self._was_saved = True
        except Exception:
            # Silent save best-effort; failures will be logged inside tabs.
            pass

    def reject(self) -> None:
        """
        Auto-save on close to keep preferences even when the user just closes the dialog.

        This replaces the old "unsaved changes" prompt with best-effort persistence.
        """
        self._save_silent()
        super().reject()

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        try:
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Reset to Defaults",
                "Are you sure you want to reset all preferences to defaults?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Reset each tab
                self.general_tab._load_settings()
                self.viewer_settings_tab._load_settings()
                self.thumbnail_settings_tab._load_settings()
                self.import_tab.reset_to_defaults()
                self.invoice_tab._load_settings()
                self.ai_tab._load_settings()
                self.advanced_tab._load_settings()
                # Reload model library files tab from current root folder configuration
                self.files_tab._load_folders()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            try:
                from src.core.logging_config import get_logger

                logger = get_logger(__name__)
                logger.error("Failed to reset preferences: %s", e)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
                pass
