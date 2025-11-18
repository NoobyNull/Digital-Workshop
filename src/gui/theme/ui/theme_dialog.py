"""
Consolidated theme management dialog.

Provides a unified interface for:
- Selecting and applying presets
- Customizing individual colors
- Importing/exporting themes
- System theme detection settings

Single Responsibility: Unified theme management UI.
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..simple_service import ThemeService


class ThemeDialog(QDialog):
    """
    Consolidated theme management dialog.

    Provides tabs for:
    - Preset selection
    - Color customization
    - Import/export
    - System detection settings
    """

    theme_applied = Signal(str)  # Emitted when theme is applied

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the theme dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.service = ThemeService.instance()

        self.setWindowTitle("Theme Manager")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        try:
            self._setup_ui()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            from src.core.logging_config import get_logger

            logger = get_logger(__name__)
            logger.error("Failed to initialize ThemeDialog: %s", e, exc_info=True)
            raise

    def _setup_ui(self) -> None:
        """Setup the UI with tabs.

        The simplified dialog lets the user choose between light, dark
        and auto themes. Advanced color and import/export controls from
        the legacy theme system have been removed.
        """
        layout = QVBoxLayout()

        # Create tab widget
        tabs = QTabWidget()

        # Tab 1: Theme selection
        tabs.addTab(self._create_presets_tab(), "Theme")

        # Tab 2: System information
        tabs.addTab(self._create_system_detection_tab(), "System")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_presets_tab(self) -> QWidget:
        """Create the theme selection tab.

        This uses the simplified :class:`ThemeService` which supports
        "light", "dark" and "auto" modes.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Choose application theme:"))

        # Theme selector
        self.preset_combo = QComboBox()

        current_theme, _ = self.service.get_current_theme()
        options = [
            ("Dark (default)", "dark"),
            ("Light", "light"),
            ("Auto (follow system, if available)", "auto"),
        ]

        current_index = 0
        for index, (label, value) in enumerate(options):
            self.preset_combo.addItem(label, value)
            if value == current_theme:
                current_index = index

        self.preset_combo.setCurrentIndex(current_index)
        layout.addWidget(self.preset_combo)

        # Apply button
        apply_btn = QPushButton("Apply Theme")
        apply_btn.clicked.connect(self._on_apply_preset)
        layout.addWidget(apply_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_system_detection_tab(self) -> QWidget:
        """Create the system information tab.

        This no longer exposes low-level system detection toggles. Instead
        it reports the currently active theme and explains how the "Auto"
        mode behaves.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("System Theme Information:"))

        current_theme, _ = self.service.get_current_theme()
        self.system_theme_label = QLabel(f"Current Theme: {current_theme.title()}")
        layout.addWidget(self.system_theme_label)

        layout.addWidget(
            QLabel(
                "When the theme is set to 'Auto', the application will attempt\n"
                "to follow the operating system's dark/light preference if a\n"
                "supported detection library is available."
            )
        )

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _on_apply_preset(self) -> None:
        """Apply the selected theme using :class:`ThemeService`."""
        theme_name = self.preset_combo.currentData()
        if not theme_name:
            return

        ok = self.service.apply_theme(theme_name)
        if not ok:
            QMessageBox.warning(self, "Theme", "Failed to apply theme.")

        # Keep the system tab in sync with the current theme
        if hasattr(self, "system_theme_label"):
            self.system_theme_label.setText(f"Current Theme: {theme_name.title()}")

        self.theme_applied.emit(theme_name)

    def _on_reset(self) -> None:
        """Reset to the default dark theme."""
        reply = QMessageBox.question(
            self,
            "Reset Theme",
            "Reset to default (dark) theme?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self.service.reset_to_default()
            except AttributeError:
                # Fallback for older ThemeService implementations
                self.service.apply_theme("dark")

            # Dark is the first entry in the combo box
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentIndex(0)

            if hasattr(self, "system_theme_label"):
                self.system_theme_label.setText("Current Theme: Dark")

            self.theme_applied.emit("dark")

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception:
            pass
