from __future__ import annotations

"""
Preferences dialog with tabbed interface:
- Display
- System
- Files
- Theming (live-apply + persist to AppData)

The Theming tab edits central color variables in gui.theme.COLORS and applies
changes live across the running app. On Save, the current theme is persisted
to AppData and loaded on next startup.
"""


from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)



class ThemingTab(QWidget):
    """Simplified theming tab with Material Design theme selection.

    Provides options to select:
    - Theme mode: Dark, Light, or Auto (system)
    - Material Design color variant
    """

    def __init__(self, on_live_apply=None, parent=None) -> None:
        super().__init__(parent)
        self.on_live_apply = on_live_apply
        self.service = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup simplified theming UI with Material Design theme selector."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("Select your preferred theme mode.")
        hdr.setWordWrap(True)
        layout.addWidget(hdr)

        # Qt-Material theme selector
        self._setup_material_theme_selector(layout)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Apply theme styling
        self._apply_theme_styling()

    def _setup_material_theme_selector(self, parent_layout: QVBoxLayout) -> None:
        """Setup qt-material theme mode selector."""
        try:
            self.service = None

            # Material theme group
            mat_group = QFrame()
            mat_layout = QVBoxLayout(mat_group)
            mat_layout.setContentsMargins(0, 0, 0, 0)

            mat_label = QLabel("<b>Qt-Material Theme</b>")
            mat_layout.addWidget(mat_label)

            # Theme mode selector (Dark/Light/Auto)
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("Mode:"))

            self.mode_combo = QComboBox()
            self.mode_combo.addItem("Dark", "dark")
            self.mode_combo.addItem("Light", "light")
            self.mode_combo.addItem("Auto (System)", "auto")

            # Set current mode
            current_theme, _ = self.service.get_current_theme()
            self.mode_combo.setCurrentIndex({"dark": 0, "light": 1, "auto": 2}.get(current_theme, 0))
            self.mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)

            mode_layout.addWidget(self.mode_combo)
            mode_layout.addStretch()
            mat_layout.addLayout(mode_layout)

            parent_layout.addWidget(mat_group)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Silently fail if ThemeService not available
            pass

    def _on_theme_mode_changed(self, index: int) -> None:
        """Handle theme mode change."""
        try:
            if not self.service:
                return

            theme_mode = self.mode_combo.currentData()
            if theme_mode:
                self.service.set_theme(theme_mode)
                if self.on_live_apply:
                    self.on_live_apply()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            pass

    def _apply_theme_styling(self) -> None:
        """Apply theme styling to the tab."""
        try:
            # This is a placeholder for any additional styling
            # QDarkStyleSheet handles most styling automatically
            pass
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            pass

    def reload_from_current(self) -> None:
        """Reload theme selector from current theme."""
        try:
            if not self.service:
                return

            current_theme, _ = self.service.get_current_theme()
            self.mode_combo.setCurrentIndex({"dark": 0, "light": 1, "auto": 2}.get(current_theme, 0))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            pass

    def save_settings(self) -> None:
        """Save theming settings."""
        try:
            if self.service:
                self.service.apply_theme(self.mode_combo.currentData())
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            pass


