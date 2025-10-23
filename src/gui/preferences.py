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

from dataclasses import asdict
from typing import Dict, List, Callable
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QCheckBox,
    QComboBox, QListWidget, QListWidgetItem, QScrollArea, QSlider, QInputDialog,
    QSpinBox
)

from src.gui.theme import (
    COLORS,
    set_theme, save_theme_to_settings, theme_to_dict, color as color_hex, hex_to_rgb
)
from src.gui.files_tab import FilesTab


class PreferencesDialog(QDialog):
    """
    Application preferences dialog with multiple tabs.
    Emits theme_changed whenever the Theming tab applies updates.
    Emits viewer_settings_changed whenever viewer settings are modified.
    """
    theme_changed = Signal()
    viewer_settings_changed = Signal()

    def __init__(self, parent=None, on_reset_layout=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.on_reset_layout = on_reset_layout

        # Remove native title bar and frame - we'll use custom title bar
        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs in logical order
        self.window_layout_tab = WindowLayoutTab(on_reset_layout=self.on_reset_layout)
        self.theming_tab = ThemingTab(on_live_apply=self._on_theme_live_applied)
        self.viewer_settings_tab = ViewerSettingsTab()
        self.thumbnail_settings_tab = ThumbnailSettingsTab()
        self.performance_tab = PerformanceSettingsTab()
        self.files_tab = FilesTab()
        self.advanced_tab = AdvancedTab()

        # Add tabs in logical order: UI → Content → System → Advanced
        self.tabs.addTab(self.window_layout_tab, "Window & Layout")
        self.tabs.addTab(self.theming_tab, "Theming")
        self.tabs.addTab(self.viewer_settings_tab, "3D Viewer")
        self.tabs.addTab(self.thumbnail_settings_tab, "Thumbnail Settings")
        self.tabs.addTab(self.performance_tab, "Performance")
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        # Dialog action buttons
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_save = QPushButton("Save")
        self.btn_close = QPushButton("Close")

        buttons_row.addWidget(self.btn_reset)
        buttons_row.addWidget(self.btn_save)
        buttons_row.addWidget(self.btn_close)

        layout.addLayout(buttons_row)

        # Wire actions
        self.btn_close.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save_and_notify)
        self.btn_reset.clicked.connect(self._reset_to_defaults)

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception:
            pass

    def _on_theme_live_applied(self):
        # Bubble up to MainWindow so it can re-render stylesheets on key widgets
        self.theme_changed.emit()

    def _save_and_notify(self):
        try:
            save_theme_to_settings()

            # Save window settings
            if hasattr(self, 'window_layout_tab'):
                self.window_layout_tab.save_settings()

            # Save viewer settings
            if hasattr(self, 'viewer_settings_tab'):
                self.viewer_settings_tab.save_settings()

            # Save thumbnail settings
            if hasattr(self, 'thumbnail_settings_tab'):
                self.thumbnail_settings_tab.save_settings()

            # Save performance settings
            if hasattr(self, 'performance_tab'):
                self.performance_tab.save_settings()

            # Emit viewer settings changed signal
            self.viewer_settings_changed.emit()

            QMessageBox.information(self, "Saved", "All settings saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save settings:\n{e}")

    def _reset_to_defaults(self):
        # Build defaults from the dataclass defaults
        try:
            # Get default values from the ThemeDefaults dataclass
            from src.gui.theme import ThemeDefaults
            default_map = asdict(ThemeDefaults())
        except Exception:
            # Fallback: if introspection doesn't work cross-runtime, use initial theme_to_dict()
            default_map = theme_to_dict()
        set_theme(default_map)
        self.theming_tab.reload_from_current()
        self._on_theme_live_applied()


class ThemingTab(QWidget):
    """
    Simplified theming tab with Material Design theme selection.

    Provides options to select:
    - Theme mode: Dark, Light, or Auto (system)
    - Material Design color variant
    """

    def __init__(self, on_live_apply=None, parent=None):
        super().__init__(parent)
        self.on_live_apply = on_live_apply
        self.service = None
        self._setup_ui()



    def _setup_ui(self):
        """Setup simplified theming UI with Material Design theme selector."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("Select your preferred theme mode and color variant.")
        hdr.setWordWrap(True)
        layout.addWidget(hdr)

        # Qt-Material theme selector
        self._setup_material_theme_selector(layout)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Apply theme styling
        self._apply_theme_styling()

    def _setup_material_theme_selector(self, parent_layout: QVBoxLayout) -> None:
        """Setup qt-material theme mode and variant selector."""
        try:
            from src.gui.theme.simple_service import ThemeService
            self.service = ThemeService.instance()

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

            # Variant selector
            mat_desc = QLabel("Select a Material Design color variant:")
            mat_desc.setWordWrap(True)
            mat_layout.addWidget(mat_desc)

            variant_layout = QHBoxLayout()
            variant_layout.addWidget(QLabel("Variant:"))

            self.variant_combo = QComboBox()
            self._populate_material_variants()
            self.variant_combo.currentTextChanged.connect(self._on_material_variant_changed)
            variant_layout.addWidget(self.variant_combo)
            variant_layout.addStretch()

            mat_layout.addLayout(variant_layout)
            parent_layout.addWidget(mat_group)

        except Exception as e:
            # Silently fail if ThemeService not available
            pass

    def _populate_material_variants(self) -> None:
        """Populate material variant combo."""
        try:
            if not self.service:
                return

            self.variant_combo.blockSignals(True)
            self.variant_combo.clear()

            # Get current theme type
            theme_type, _ = self.service.get_current_theme()
            variants = self.service.get_qt_material_variants(theme_type)

            # Get the currently selected variant from QSettings
            from PySide6.QtCore import QSettings
            settings = QSettings("Candy-Cadence", "3D-MM")
            current_variant = settings.value("qt_material_variant", "blue", type=str)

            current_index = 0
            for idx, variant in enumerate(variants):
                # Extract color name from variant (e.g., "dark_blue" -> "blue")
                color_name = variant.split("_", 1)[1] if "_" in variant else variant
                self.variant_combo.addItem(color_name.title(), variant)
                
                # Set current index if this variant matches the saved variant
                if variant == current_variant or color_name == current_variant:
                    current_index = idx

            self.variant_combo.setCurrentIndex(current_index)
            self.variant_combo.blockSignals(False)
        except Exception:
            pass

    def _apply_theme_styling(self) -> None:
        """Apply theme styling (no-op - qt-material handles this)."""
        pass

    def _on_theme_mode_changed(self, index: int) -> None:
        """Handle theme mode change (Dark/Light/Auto)."""
        try:
            if not self.service:
                return

            mode = self.mode_combo.itemData(index)
            if not mode:
                return

            # Get the current variant from QSettings to apply with new mode
            from PySide6.QtCore import QSettings
            settings = QSettings("Candy-Cadence", "3D-MM")
            current_variant = settings.value("qt_material_variant", "blue", type=str)
            
            # Apply the new theme mode with the current variant
            self.service.apply_theme(mode, "qt-material")

            # Update variant selector to show correct variants for new mode
            self._populate_material_variants()

            # Reapply styling to this tab
            self._apply_theme_styling()

            # Notify parent of theme change
            if callable(self.on_live_apply):
                self.on_live_apply()
        except Exception:
            pass

    def _on_material_variant_changed(self, variant_name: str) -> None:
        """Handle material variant change."""
        try:
            if not self.service or not variant_name:
                return

            # Set the variant and apply theme
            self.service.set_qt_material_variant(variant_name.lower())
            current_theme, _ = self.service.get_current_theme()
            self.service.apply_theme(current_theme, "qt-material")

            # Reapply styling to this tab
            self._apply_theme_styling()

            # Notify parent of theme change
            if callable(self.on_live_apply):
                self.on_live_apply()
        except Exception:
            pass
class ViewerSettingsTab(QWidget):
    """3D Viewer settings tab: grid, ground plane, camera, and lighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("3D Viewer Settings")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel(
            "Customize the 3D viewer appearance and interaction behavior. "
            "Changes apply to new models and can be adjusted anytime."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Grid Settings Group
        grid_group = QFrame()
        grid_layout = QFormLayout(grid_group)
        grid_label = QLabel("<b>Grid Settings</b>")
        grid_layout.addRow(grid_label)

        self.grid_visible_check = QCheckBox("Show grid")
        grid_layout.addRow(self.grid_visible_check)

        self.grid_color_btn = QPushButton()
        self.grid_color_btn.setMaximumWidth(100)
        grid_layout.addRow("Grid color:", self.grid_color_btn)

        self.grid_size_slider = QSlider(Qt.Horizontal)
        self.grid_size_slider.setRange(1, 100)
        self.grid_size_slider.setValue(10)
        self.grid_size_label = QLabel("10.0")
        grid_size_row = QHBoxLayout()
        grid_size_row.addWidget(self.grid_size_slider)
        grid_size_row.addWidget(self.grid_size_label)
        grid_layout.addRow("Grid size:", grid_size_row)

        layout.addWidget(grid_group)

        # Ground Plane Group
        ground_group = QFrame()
        ground_layout = QFormLayout(ground_group)
        ground_label = QLabel("<b>Ground Plane</b>")
        ground_layout.addRow(ground_label)

        self.ground_visible_check = QCheckBox("Show ground plane")
        ground_layout.addRow(self.ground_visible_check)

        self.ground_color_btn = QPushButton()
        self.ground_color_btn.setMaximumWidth(100)
        ground_layout.addRow("Ground color:", self.ground_color_btn)

        self.ground_offset_slider = QSlider(Qt.Horizontal)
        self.ground_offset_slider.setRange(-100, 100)
        self.ground_offset_slider.setValue(5)
        self.ground_offset_label = QLabel("0.5")
        ground_offset_row = QHBoxLayout()
        ground_offset_row.addWidget(self.ground_offset_slider)
        ground_offset_row.addWidget(self.ground_offset_label)
        ground_layout.addRow("Ground offset:", ground_offset_row)

        layout.addWidget(ground_group)

        # Camera & Interaction Group
        camera_group = QFrame()
        camera_layout = QFormLayout(camera_group)
        camera_label = QLabel("<b>Camera & Interaction</b>")
        camera_layout.addRow(camera_label)

        self.mouse_sensitivity_slider = QSlider(Qt.Horizontal)
        self.mouse_sensitivity_slider.setRange(5, 50)
        self.mouse_sensitivity_slider.setValue(10)
        self.mouse_sensitivity_label = QLabel("1.0x")
        mouse_row = QHBoxLayout()
        mouse_row.addWidget(self.mouse_sensitivity_slider)
        mouse_row.addWidget(self.mouse_sensitivity_label)
        camera_layout.addRow("Mouse sensitivity:", mouse_row)

        self.fps_limit_combo = QComboBox()
        self.fps_limit_combo.addItem("Unlimited", 0)
        self.fps_limit_combo.addItem("120 FPS", 120)
        self.fps_limit_combo.addItem("60 FPS", 60)
        self.fps_limit_combo.addItem("30 FPS", 30)
        camera_layout.addRow("FPS limit:", self.fps_limit_combo)

        self.zoom_speed_slider = QSlider(Qt.Horizontal)
        self.zoom_speed_slider.setRange(5, 30)
        self.zoom_speed_slider.setValue(10)
        self.zoom_speed_label = QLabel("1.0x")
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(self.zoom_speed_slider)
        zoom_row.addWidget(self.zoom_speed_label)
        camera_layout.addRow("Zoom speed:", zoom_row)

        self.auto_fit_check = QCheckBox("Auto-fit model on load")
        camera_layout.addRow(self.auto_fit_check)

        layout.addWidget(camera_group)

        # Lighting Group
        lighting_group = QFrame()
        lighting_layout = QFormLayout(lighting_group)
        lighting_label = QLabel("<b>Lighting (Advanced)</b>")
        lighting_layout.addRow(lighting_label)

        self.light_color_btn = QPushButton()
        self.light_color_btn.setMaximumWidth(100)
        lighting_layout.addRow("Light color:", self.light_color_btn)

        self.light_intensity_slider = QSlider(Qt.Horizontal)
        self.light_intensity_slider.setRange(0, 100)
        self.light_intensity_slider.setValue(80)
        self.light_intensity_label = QLabel("0.8")
        intensity_row = QHBoxLayout()
        intensity_row.addWidget(self.light_intensity_slider)
        intensity_row.addWidget(self.light_intensity_label)
        lighting_layout.addRow("Light intensity:", intensity_row)

        self.enable_fill_light_check = QCheckBox("Enable fill light")
        lighting_layout.addRow(self.enable_fill_light_check)

        layout.addWidget(lighting_group)

        # Background Gradient Group
        gradient_group = QFrame()
        gradient_layout = QFormLayout(gradient_group)
        gradient_label = QLabel("<b>Background Gradient</b>")
        gradient_layout.addRow(gradient_label)

        self.enable_gradient_check = QCheckBox("Enable gradient background")
        gradient_layout.addRow(self.enable_gradient_check)

        self.gradient_top_color_btn = QPushButton()
        self.gradient_top_color_btn.setMaximumWidth(100)
        gradient_layout.addRow("Top color (sky):", self.gradient_top_color_btn)

        self.gradient_bottom_color_btn = QPushButton()
        self.gradient_bottom_color_btn.setMaximumWidth(100)
        gradient_layout.addRow("Bottom color (ground):", self.gradient_bottom_color_btn)

        layout.addWidget(gradient_group)

        layout.addStretch()

        # Connect signals
        self.grid_visible_check.stateChanged.connect(self._on_settings_changed)
        self.grid_color_btn.clicked.connect(self._on_grid_color_clicked)
        self.grid_size_slider.valueChanged.connect(self._on_grid_size_changed)
        self.ground_visible_check.stateChanged.connect(self._on_settings_changed)
        self.ground_color_btn.clicked.connect(self._on_ground_color_clicked)
        self.ground_offset_slider.valueChanged.connect(self._on_ground_offset_changed)
        self.mouse_sensitivity_slider.valueChanged.connect(self._on_mouse_sensitivity_changed)
        self.fps_limit_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.zoom_speed_slider.valueChanged.connect(self._on_zoom_speed_changed)
        self.auto_fit_check.stateChanged.connect(self._on_settings_changed)
        self.light_color_btn.clicked.connect(self._on_light_color_clicked)
        self.light_intensity_slider.valueChanged.connect(self._on_light_intensity_changed)
        self.enable_fill_light_check.stateChanged.connect(self._on_settings_changed)

        # Gradient signals
        self.enable_gradient_check.stateChanged.connect(self._on_settings_changed)
        self.gradient_top_color_btn.clicked.connect(self._on_gradient_top_color_clicked)
        self.gradient_bottom_color_btn.clicked.connect(self._on_gradient_bottom_color_clicked)

    def _load_settings(self) -> None:
        """Load current settings from QSettings with fallback to ApplicationConfig."""
        try:
            from PySide6.QtCore import QSettings
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Grid settings - load from QSettings with fallback to config
            self.grid_visible_check.setChecked(settings.value("viewer/grid_visible", config.grid_visible, type=bool))
            grid_color = settings.value("viewer/grid_color", config.grid_color, type=str)
            self._update_color_button(self.grid_color_btn, grid_color)
            self.grid_size_slider.setValue(int(settings.value("viewer/grid_size", config.grid_size, type=float)))

            # Ground settings
            self.ground_visible_check.setChecked(settings.value("viewer/ground_visible", config.ground_visible, type=bool))
            ground_color = settings.value("viewer/ground_color", config.ground_color, type=str)
            self._update_color_button(self.ground_color_btn, ground_color)
            self.ground_offset_slider.setValue(int(settings.value("viewer/ground_offset", config.ground_offset, type=float) * 10))

            # Camera settings
            self.mouse_sensitivity_slider.setValue(int(settings.value("viewer/mouse_sensitivity", config.mouse_sensitivity, type=float) * 10))
            fps_limit = int(settings.value("viewer/fps_limit", config.fps_limit, type=int))
            self.fps_limit_combo.setCurrentIndex({0: 0, 120: 1, 60: 2, 30: 3}.get(fps_limit, 0))
            self.zoom_speed_slider.setValue(int(settings.value("viewer/zoom_speed", config.zoom_speed, type=float) * 10))
            self.auto_fit_check.setChecked(settings.value("viewer/auto_fit_on_load", config.auto_fit_on_load, type=bool))

            # Lighting settings
            r = settings.value("lighting/color_r", config.default_light_color_r, type=float)
            g = settings.value("lighting/color_g", config.default_light_color_g, type=float)
            b = settings.value("lighting/color_b", config.default_light_color_b, type=float)
            self._update_color_button(self.light_color_btn, self._rgb_to_hex(r, g, b))
            self.light_intensity_slider.setValue(int(settings.value("lighting/intensity", config.default_light_intensity, type=float) * 100))
            self.enable_fill_light_check.setChecked(settings.value("lighting/enable_fill_light", config.enable_fill_light, type=bool))

            # Load gradient settings
            self.enable_gradient_check.setChecked(settings.value("viewer/enable_gradient", config.enable_gradient, type=bool))
            gradient_top = settings.value("viewer/gradient_top_color", config.gradient_top_color, type=str)
            gradient_bottom = settings.value("viewer/gradient_bottom_color", config.gradient_bottom_color, type=str)
            self._update_color_button(self.gradient_top_color_btn, gradient_top)
            self._update_color_button(self.gradient_bottom_color_btn, gradient_bottom)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load viewer settings: {e}")

    def save_settings(self) -> None:
        """Save viewer settings to QSettings."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings()

            # Grid settings
            settings.setValue("viewer/grid_visible", self.grid_visible_check.isChecked())
            settings.setValue("viewer/grid_color", self.grid_color_btn.palette().button().color().name())
            settings.setValue("viewer/grid_size", float(self.grid_size_slider.value()))

            # Ground settings
            settings.setValue("viewer/ground_visible", self.ground_visible_check.isChecked())
            settings.setValue("viewer/ground_color", self.ground_color_btn.palette().button().color().name())
            settings.setValue("viewer/ground_offset", float(self.ground_offset_slider.value()) / 10.0)

            # Camera settings
            settings.setValue("viewer/mouse_sensitivity", float(self.mouse_sensitivity_slider.value()) / 10.0)
            settings.setValue("viewer/fps_limit", int(self.fps_limit_combo.currentData()))
            settings.setValue("viewer/zoom_speed", float(self.zoom_speed_slider.value()) / 10.0)
            settings.setValue("viewer/auto_fit_on_load", self.auto_fit_check.isChecked())

            # Lighting settings
            light_color = self.light_color_btn.palette().button().color().name()
            r, g, b = self._hex_to_rgb(light_color)
            settings.setValue("lighting/color_r", r)
            settings.setValue("lighting/color_g", g)
            settings.setValue("lighting/color_b", b)
            settings.setValue("lighting/intensity", float(self.light_intensity_slider.value()) / 100.0)
            settings.setValue("lighting/enable_fill_light", self.enable_fill_light_check.isChecked())

            # Gradient settings
            settings.setValue("viewer/enable_gradient", self.enable_gradient_check.isChecked())
            settings.setValue("viewer/gradient_top_color", self.gradient_top_color_btn.palette().button().color().name())
            settings.setValue("viewer/gradient_bottom_color", self.gradient_bottom_color_btn.palette().button().color().name())

            if self.logger:
                self.logger.info("Viewer settings saved to QSettings")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save viewer settings: {e}")

    def _on_grid_color_clicked(self) -> None:
        """Handle grid color picker."""
        color = QColorDialog.getColor(
            QColor(self.grid_color_btn.palette().button().color()),
            self,
            "Select Grid Color"
        )
        if color.isValid():
            self._update_color_button(self.grid_color_btn, color.name())

    def _on_ground_color_clicked(self) -> None:
        """Handle ground color picker."""
        color = QColorDialog.getColor(
            QColor(self.ground_color_btn.palette().button().color()),
            self,
            "Select Ground Color"
        )
        if color.isValid():
            self._update_color_button(self.ground_color_btn, color.name())

    def _on_light_color_clicked(self) -> None:
        """Handle light color picker."""
        color = QColorDialog.getColor(
            QColor(self.light_color_btn.palette().button().color()),
            self,
            "Select Light Color"
        )
        if color.isValid():
            self._update_color_button(self.light_color_btn, color.name())

    def _on_grid_size_changed(self, value: int) -> None:
        """Update grid size label."""
        self.grid_size_label.setText(f"{value}.0")

    def _on_ground_offset_changed(self, value: int) -> None:
        """Update ground offset label."""
        self.ground_offset_label.setText(f"{value / 10.0:.1f}")

    def _on_mouse_sensitivity_changed(self, value: int) -> None:
        """Update mouse sensitivity label."""
        self.mouse_sensitivity_label.setText(f"{value / 10.0:.1f}x")

    def _on_zoom_speed_changed(self, value: int) -> None:
        """Update zoom speed label."""
        self.zoom_speed_label.setText(f"{value / 10.0:.1f}x")

    def _on_light_intensity_changed(self, value: int) -> None:
        """Update light intensity label."""
        self.light_intensity_label.setText(f"{value / 100.0:.2f}")

    def _on_gradient_top_color_clicked(self) -> None:
        """Handle gradient top color picker."""
        color = QColorDialog.getColor(
            QColor(self.gradient_top_color_btn.palette().button().color()),
            self,
            "Select Gradient Top Color (Sky)"
        )
        if color.isValid():
            self._update_color_button(self.gradient_top_color_btn, color.name())

    def _on_gradient_bottom_color_clicked(self) -> None:
        """Handle gradient bottom color picker."""
        color = QColorDialog.getColor(
            QColor(self.gradient_bottom_color_btn.palette().button().color()),
            self,
            "Select Gradient Bottom Color (Ground)"
        )
        if color.isValid():
            self._update_color_button(self.gradient_bottom_color_btn, color.name())

    def _on_settings_changed(self) -> None:
        """Handle settings change."""
        pass

    def _update_color_button(self, button: QPushButton, color_hex: str) -> None:
        """Update color button appearance."""
        try:
            color = QColor(color_hex)
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            button.setIcon(QIcon(pixmap))
            button.setStyleSheet(f"background-color: {color_hex};")
        except Exception:
            pass

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(r: float, g: float, b: float) -> str:
        """Convert RGB (0-1 range) to hex color."""
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


class WindowLayoutTab(QWidget):
    """Window and layout settings tab: window dimensions and layout management."""
    def __init__(self, on_reset_layout: Callable | None = None, parent=None):
        super().__init__(parent)
        self.on_reset_layout = on_reset_layout
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QLabel("Window Layout and Docking")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel("Layout auto-saves when you move or dock panels. Use 'Reset Window Layout' to restore defaults.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Window Dimensions Group
        dim_group = QFrame()
        dim_layout = QFormLayout(dim_group)
        dim_label = QLabel("<b>Window Dimensions</b>")
        dim_layout.addRow(dim_label)

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1200)
        self.window_width_spin.setSuffix(" px")
        dim_layout.addRow("Default width:", self.window_width_spin)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(800)
        self.window_height_spin.setSuffix(" px")
        dim_layout.addRow("Default height:", self.window_height_spin)

        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(400, 1200)
        self.min_width_spin.setValue(800)
        self.min_width_spin.setSuffix(" px")
        dim_layout.addRow("Minimum width:", self.min_width_spin)

        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(300, 1000)
        self.min_height_spin.setValue(600)
        self.min_height_spin.setSuffix(" px")
        dim_layout.addRow("Minimum height:", self.min_height_spin)

        layout.addWidget(dim_group)

        # Startup Behavior Group
        startup_group = QFrame()
        startup_layout = QVBoxLayout(startup_group)
        startup_label = QLabel("<b>Startup Behavior</b>")
        startup_layout.addWidget(startup_label)

        self.maximize_startup_check = QCheckBox("Maximize window on startup")
        startup_layout.addWidget(self.maximize_startup_check)

        self.remember_size_check = QCheckBox("Remember window size on exit")
        startup_layout.addWidget(self.remember_size_check)

        layout.addWidget(startup_group)

        # Layout Management Group
        layout_group = QFrame()
        layout_layout = QVBoxLayout(layout_group)
        layout_label = QLabel("<b>Layout Management</b>")
        layout_layout.addWidget(layout_label)

        desc2 = QLabel("Reset the window and dock layout to default positions.")
        desc2.setWordWrap(True)
        layout_layout.addWidget(desc2)

        # Actions row
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_reset_layout = QPushButton("Reset Window Layout")
        row.addWidget(self.btn_reset_layout)
        layout_layout.addLayout(row)

        layout.addWidget(layout_group)

        layout.addStretch(1)

        # Connect signals
        self.btn_reset_layout.clicked.connect(self._handle_reset)

    def _load_settings(self) -> None:
        """Load current settings from config."""
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()

            self.window_width_spin.setValue(config.default_window_width)
            self.window_height_spin.setValue(config.default_window_height)
            self.min_width_spin.setValue(config.minimum_window_width)
            self.min_height_spin.setValue(config.minimum_window_height)
            self.maximize_startup_check.setChecked(config.maximize_on_startup)
            self.remember_size_check.setChecked(config.remember_window_size)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load window settings: {e}")

    def save_settings(self) -> None:
        """Save window settings to config."""
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()

            config.default_window_width = self.window_width_spin.value()
            config.default_window_height = self.window_height_spin.value()
            config.minimum_window_width = self.min_width_spin.value()
            config.minimum_window_height = self.min_height_spin.value()
            config.maximize_on_startup = self.maximize_startup_check.isChecked()
            config.remember_window_size = self.remember_size_check.isChecked()

            if self.logger:
                self.logger.info("Window settings saved")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save window settings: {e}")

    def _handle_reset(self):
        try:
            if callable(self.on_reset_layout):
                self.on_reset_layout()
                QMessageBox.information(self, "Layout Reset", "Window layout has been reset to defaults.")
        except Exception as e:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset layout:\n{e}")


class ThumbnailSettingsTab(QWidget):
    """Thumbnail generation settings tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Thumbnail Generation Settings")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel(
            "Choose background image and material for all generated thumbnails. "
            "These settings apply to all thumbnail generation operations."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Background selection group
        bg_group = QFrame()
        bg_layout = QVBoxLayout(bg_group)

        bg_label = QLabel("<b>Background Image</b>")
        bg_layout.addWidget(bg_label)

        bg_desc = QLabel("Select a background image for thumbnails:")
        bg_desc.setWordWrap(True)
        bg_layout.addWidget(bg_desc)

        # Background list
        self.bg_list = QListWidget()
        self.bg_list.setMaximumHeight(150)
        self._populate_backgrounds()
        bg_layout.addWidget(self.bg_list)

        layout.addWidget(bg_group)

        # Material selection group
        mat_group = QFrame()
        mat_layout = QVBoxLayout(mat_group)

        mat_label = QLabel("<b>Material</b>")
        mat_layout.addWidget(mat_label)

        mat_desc = QLabel("Select a material to apply to all thumbnails:")
        mat_desc.setWordWrap(True)
        mat_layout.addWidget(mat_desc)

        # Material combo
        self.material_combo = QComboBox()
        self._populate_materials()
        mat_layout.addWidget(self.material_combo)

        layout.addWidget(mat_group)

        # Preview group - side by side layout
        preview_group = QFrame()
        preview_layout = QVBoxLayout(preview_group)

        preview_label = QLabel("<b>Preview</b>")
        preview_layout.addWidget(preview_label)

        # Horizontal layout for side-by-side previews
        preview_h_layout = QHBoxLayout()

        # Background preview
        bg_preview_container = QVBoxLayout()
        bg_preview_title = QLabel("Background")
        bg_preview_title.setAlignment(Qt.AlignCenter)
        bg_preview_container.addWidget(bg_preview_title)

        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(120)
        self.preview_label.setMinimumWidth(120)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        bg_preview_container.addWidget(self.preview_label)

        # Material preview
        mat_preview_container = QVBoxLayout()
        mat_preview_title = QLabel("Material")
        mat_preview_title.setAlignment(Qt.AlignCenter)
        mat_preview_container.addWidget(mat_preview_title)

        self.material_preview_label = QLabel()
        self.material_preview_label.setMinimumHeight(120)
        self.material_preview_label.setMinimumWidth(120)
        self.material_preview_label.setAlignment(Qt.AlignCenter)
        self.material_preview_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        mat_preview_container.addWidget(self.material_preview_label)

        preview_h_layout.addLayout(bg_preview_container)
        preview_h_layout.addLayout(mat_preview_container)
        preview_layout.addLayout(preview_h_layout)

        layout.addWidget(preview_group)

        layout.addStretch()

        # Connect signals
        self.bg_list.itemSelectionChanged.connect(self._on_background_selected)
        self.material_combo.currentIndexChanged.connect(self._update_preview)

    def _populate_backgrounds(self) -> None:
        """Populate background list from resources/backgrounds."""
        try:
            bg_dir = Path(__file__).parent.parent / "resources" / "backgrounds"
            if bg_dir.exists():
                for bg_file in sorted(bg_dir.glob("*.png")):
                    item = QListWidgetItem(bg_file.stem)
                    item.setData(Qt.UserRole, str(bg_file))
                    self.bg_list.addItem(item)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate backgrounds: {e}")

    def _populate_materials(self) -> None:
        """Populate material combo from resources/materials."""
        try:
            self.material_combo.addItem("None (Default)", None)

            mat_dir = Path(__file__).parent.parent / "resources" / "materials"
            if mat_dir.exists():
                for mat_file in sorted(mat_dir.glob("*.mtl")):
                    material_name = mat_file.stem
                    self.material_combo.addItem(material_name, material_name)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate materials: {e}")

    def _load_settings(self) -> None:
        """Load current settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()

            # Load background
            if config.thumbnail_bg_image:
                for i in range(self.bg_list.count()):
                    item = self.bg_list.item(i)
                    if item.data(Qt.UserRole) == config.thumbnail_bg_image:
                        self.bg_list.setCurrentItem(item)
                        break

            # Load material
            if config.thumbnail_material:
                idx = self.material_combo.findData(config.thumbnail_material)
                if idx >= 0:
                    self.material_combo.setCurrentIndex(idx)

            self._update_preview()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load settings: {e}")

    def _on_background_selected(self) -> None:
        """Handle background selection."""
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview images for both background and material."""
        try:
            # Update background preview
            current_item = self.bg_list.currentItem()
            if current_item:
                bg_path = current_item.data(Qt.UserRole)
                pixmap = QPixmap(bg_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaledToHeight(
                        120, Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled)
                else:
                    self.preview_label.setText("Error loading\nbackground")
            else:
                self.preview_label.setText("No background\nselected")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update background preview: {e}")
            self.preview_label.setText("Error loading\npreview")

        # Update material preview
        try:
            material_name = self.material_combo.currentData()
            if material_name:
                # Look for material texture image
                mat_dir = Path(__file__).parent.parent / "resources" / "materials"
                mat_image_path = mat_dir / f"{material_name}.png"

                if mat_image_path.exists():
                    pixmap = QPixmap(str(mat_image_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaledToHeight(
                            120, Qt.SmoothTransformation
                        )
                        self.material_preview_label.setPixmap(scaled)
                        return

                self.material_preview_label.setText(f"{material_name}\n(no preview)")
            else:
                self.material_preview_label.setText("No material\nselected")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update material preview: {e}")
            self.material_preview_label.setText("Error loading\nmaterial")

    def get_settings(self) -> dict:
        """Get current thumbnail settings."""
        settings = {
            "background_image": None,
            "material": None
        }

        try:
            current_item = self.bg_list.currentItem()
            if current_item:
                settings["background_image"] = current_item.data(Qt.UserRole)

            settings["material"] = self.material_combo.currentData()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get settings: {e}")

        return settings

    def save_settings(self) -> None:
        """Save thumbnail settings to application config."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = self.get_settings()

            config.thumbnail_bg_image = settings["background_image"]
            config.thumbnail_material = settings["material"]

            if self.logger:
                self.logger.info(
                    f"Saved thumbnail settings: "
                    f"bg={settings['background_image']}, "
                    f"material={settings['material']}"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save settings: {e}")

class PerformanceSettingsTab(QWidget):
    """Performance settings tab for memory allocation and system optimization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the performance settings UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<b>Memory Allocation Settings</b>")
        layout.addWidget(header)

        desc = QLabel(
            "Configure how much system memory the application can use. "
            "Smart calculation: min(doubled_minimum, 50% available, total - 20%)"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Mode selection group
        mode_group = QFrame()
        mode_layout = QVBoxLayout(mode_group)

        mode_label = QLabel("<b>Memory Mode</b>")
        mode_layout.addWidget(mode_label)

        self.auto_radio = QCheckBox("Auto (Smart Calculation)")
        self.auto_radio.setChecked(True)
        mode_layout.addWidget(self.auto_radio)

        self.manual_radio = QCheckBox("Manual Override")
        mode_layout.addWidget(self.manual_radio)

        layout.addWidget(mode_group)

        # Manual override group
        override_group = QFrame()
        override_layout = QVBoxLayout(override_group)

        override_label = QLabel("<b>Cache Limit (% of System RAM)</b>")
        override_layout.addWidget(override_label)

        slider_layout = QHBoxLayout()
        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(10)
        self.memory_slider.setMaximum(95)
        self.memory_slider.setValue(80)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(5)
        slider_layout.addWidget(self.memory_slider)

        self.memory_value_label = QLabel("80%")
        self.memory_value_label.setMinimumWidth(100)
        slider_layout.addWidget(self.memory_value_label)

        override_layout.addLayout(slider_layout)
        layout.addWidget(override_group)

        # System info group
        info_group = QFrame()
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel("<b>System Information</b>")
        info_layout.addWidget(info_label)

        self.system_info_label = QLabel()
        self.system_info_label.setWordWrap(True)
        info_layout.addWidget(self.system_info_label)

        layout.addWidget(info_group)

        layout.addStretch()

        # Connect signals
        self.auto_radio.toggled.connect(self._on_mode_changed)
        self.manual_radio.toggled.connect(self._on_mode_changed)
        self.memory_slider.valueChanged.connect(self._on_slider_changed)

        # Update system info
        self._update_system_info()

    def _on_mode_changed(self) -> None:
        """Handle mode change."""
        is_manual = self.manual_radio.isChecked()
        self.memory_slider.setEnabled(is_manual)
        self._update_system_info()

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider change."""
        self.memory_value_label.setText(f"{value}%")
        self._update_system_info()

    def _update_system_info(self) -> None:
        """Update system information display."""
        try:
            import psutil
            from src.core.application_config import ApplicationConfig

            memory = psutil.virtual_memory()
            total_mb = int(memory.total / (1024 ** 2))
            available_mb = int(memory.available / (1024 ** 2))

            config = ApplicationConfig.get_default()

            if self.manual_radio.isChecked():
                percent = self.memory_slider.value()
                limit_mb = int(total_mb * (percent / 100))
                info_text = (
                    f"Cache Limit: {percent}% of {total_mb} MB = {limit_mb} MB\n"
                    f"System Total: {total_mb} MB\n"
                    f"Available: {available_mb} MB\n"
                    f"Reserve: {config.system_memory_reserve_percent}%"
                )
            else:
                limit_mb = config.get_effective_memory_limit_mb(available_mb, total_mb)
                hard_max = int(total_mb * (100 - config.system_memory_reserve_percent) / 100)
                fifty_percent = available_mb // 2
                doubled_min = config.min_memory_specification_mb * 2

                info_text = (
                    f"Smart Calculation: {limit_mb} MB\n"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB\n"
                    f"Candidates: min({doubled_min}, {fifty_percent}, {hard_max})\n"
                    f"Reserve: {config.system_memory_reserve_percent}%"
                )

            self.system_info_label.setText(info_text)
        except Exception as e:
            self.system_info_label.setText(f"Error: {e}")

    def _load_settings(self) -> None:
        """Load current settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()

            if config.use_manual_memory_override:
                self.manual_radio.setChecked(True)
                self.auto_radio.setChecked(False)
                if config.manual_cache_limit_percent:
                    self.memory_slider.setValue(config.manual_cache_limit_percent)
            else:
                self.auto_radio.setChecked(True)
                self.manual_radio.setChecked(False)

            self._on_mode_changed()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load settings: {e}")

    def save_settings(self) -> None:
        """Save performance settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            config.use_manual_memory_override = self.manual_radio.isChecked()

            if self.manual_radio.isChecked():
                config.manual_cache_limit_percent = self.memory_slider.value()

            if self.logger:
                self.logger.info(
                    f"Saved performance settings: "
                    f"manual={config.use_manual_memory_override}, "
                    f"cache_limit_percent={config.manual_cache_limit_percent}%"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save settings: {e}")


class AdvancedTab(QWidget):
    """Advanced settings tab with system reset functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Advanced Settings")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Database Reset Section
        db_section = QFrame()
        db_layout = QVBoxLayout(db_section)

        db_title = QLabel("<b>Database Management</b>")
        db_layout.addWidget(db_title)

        db_warning = QLabel(
            "Reset the application database. This will clear all model records, "
            "metadata, and library information. The database will be recreated on next startup."
        )
        db_warning.setWordWrap(True)
        db_warning.setStyleSheet("color: #ffa500; padding: 8px; background-color: rgba(255, 165, 0, 0.1); border-radius: 4px;")
        db_layout.addWidget(db_warning)

        reset_db_button = QPushButton("Reset Database")
        reset_db_button.setStyleSheet(
            "QPushButton { background-color: #ffa500; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #ff8c00; }"
        )
        reset_db_button.clicked.connect(self._perform_database_reset)
        db_layout.addWidget(reset_db_button)

        layout.addWidget(db_section)

        # System Reset Section
        system_section = QFrame()
        system_layout = QVBoxLayout(system_section)

        system_title = QLabel("<b>Complete System Reset</b>")
        system_layout.addWidget(system_title)

        # Warning message
        warning = QLabel(
            "This will reset all application settings, clear the cache, and restore "
            "the application to its default state. This action cannot be undone."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #ff6b6b; padding: 8px; background-color: rgba(255, 107, 107, 0.1); border-radius: 4px;")
        system_layout.addWidget(warning)

        # Reset button
        reset_button = QPushButton("Complete System Reset")
        reset_button.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #ff5252; }"
        )
        reset_button.clicked.connect(self._perform_system_reset)
        system_layout.addWidget(reset_button)

        layout.addWidget(system_section)

        layout.addStretch(1)

    def _perform_database_reset(self) -> None:
        """Perform database reset with confirmation."""
        # First verification: Simple confirmation
        reply1 = QMessageBox.warning(
            self,
            "Reset Database - Confirmation 1/2",
            "Are you sure you want to reset the database?\n\n"
            "This will delete all model records, metadata, and library information.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply1 != QMessageBox.Yes:
            return

        # Second verification: Text input
        text, ok = QInputDialog.getText(
            self,
            "Reset Database - Confirmation 2/2",
            "Type 'RESET DATABASE' to confirm:",
            QLineEdit.Normal,
            ""
        )

        if not ok or text.strip().upper() != "RESET DATABASE":
            QMessageBox.information(
                self,
                "Reset Cancelled",
                "Database reset cancelled. No changes were made."
            )
            return

        # All verifications passed - perform reset
        self._execute_database_reset()

    def _execute_database_reset(self) -> None:
        """Execute the actual database reset."""
        try:
            from PySide6.QtCore import QStandardPaths
            from pathlib import Path

            # Close database manager to release file locks
            try:
                from src.core.database_manager import close_database_manager
                close_database_manager()
            except Exception as e:
                print(f"Warning: Could not close database manager: {e}")

            # Delete database file
            try:
                app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
                db_file = app_data / "3dmm.db"
                if db_file.exists():
                    db_file.unlink()
                    print(f"✓ Deleted database: {db_file}")

                # Also delete WAL and SHM files if they exist
                wal_file = app_data / "3dmm.db-wal"
                shm_file = app_data / "3dmm.db-shm"
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete database file: {e}")

            # Reinitialize database manager to create fresh database
            try:
                from src.core.database_manager import get_database_manager
                db_manager = get_database_manager()
                print("✓ Database manager reinitialized with fresh database")
            except Exception as e:
                print(f"Warning: Could not reinitialize database manager: {e}")

            # Reload model library widget to show empty database
            try:
                # Get the main window from the preferences dialog parent
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'model_library_widget'):
                    main_window = main_window.parent()

                if main_window and hasattr(main_window, 'model_library_widget'):
                    if hasattr(main_window.model_library_widget, '_load_models_from_database'):
                        main_window.model_library_widget._load_models_from_database()
                        print("✓ Model library reloaded")
                    else:
                        print("Warning: Model library widget does not have _load_models_from_database method")
                else:
                    print("Warning: Could not find main window to reload model library")
            except Exception as e:
                print(f"Warning: Could not reload model library: {e}")

            # Show success message
            QMessageBox.information(
                self,
                "Database Reset Complete",
                "✓ Database reset completed successfully!\n\n"
                "The model library has been cleared and reloaded."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"An error occurred during database reset:\n\n{str(e)}"
            )

    def _perform_system_reset(self) -> None:
        """Perform complete system reset with triple verification."""
        # First verification: Simple confirmation
        reply1 = QMessageBox.warning(
            self,
            "System Reset - Confirmation 1/3",
            "Are you sure you want to reset the entire system?\n\n"
            "This will delete all settings, cache, and restore defaults.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply1 != QMessageBox.Yes:
            return

        # Second verification: More serious warning
        reply2 = QMessageBox.critical(
            self,
            "System Reset - Confirmation 2/3",
            "⚠️ WARNING ⚠️\n\n"
            "This action will:\n"
            "• Delete all application settings\n"
            "• Clear the model cache\n"
            "• Reset window layout\n"
            "• Reset all preferences\n\n"
            "This CANNOT be undone. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply2 != QMessageBox.Yes:
            return

        # Third verification: Text input
        text, ok = QInputDialog.getText(
            self,
            "System Reset - Confirmation 3/3",
            "Type 'RESET' to confirm complete system reset:",
            QLineEdit.Normal,
            ""
        )

        if not ok or text.strip().upper() != "RESET":
            QMessageBox.information(
                self,
                "Reset Cancelled",
                "System reset cancelled. No changes were made."
            )
            return

        # All verifications passed - perform reset
        self._execute_system_reset()

    def _execute_system_reset(self) -> None:
        """Execute the actual system reset."""
        try:
            from PySide6.QtCore import QSettings, QStandardPaths
            from pathlib import Path

            # Close database manager to release file locks
            try:
                from src.core.database_manager import close_database_manager
                close_database_manager()
            except Exception as e:
                print(f"Warning: Could not close database manager: {e}")

            # Clear QSettings
            settings = QSettings()
            settings.clear()
            settings.sync()

            # Delete database file
            try:
                app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
                db_file = app_data / "3dmm.db"
                if db_file.exists():
                    db_file.unlink()
                    print(f"✓ Deleted database: {db_file}")

                # Also delete WAL and SHM files if they exist
                wal_file = app_data / "3dmm.db-wal"
                shm_file = app_data / "3dmm.db-shm"
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete database file: {e}")

            # Clear model cache
            try:
                from src.core.model_cache import ModelCache
                cache = ModelCache.get_instance()
                cache.clear()
            except Exception as e:
                print(f"Warning: Could not clear model cache: {e}")

            # Show success message
            QMessageBox.information(
                self,
                "System Reset Complete",
                "✓ System reset completed successfully!\n\n"
                "The application will now close and restart."
            )

            # Relaunch the application
            import subprocess
            import sys
            subprocess.Popen([sys.executable, sys.argv[0]])

            # Close the application
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"An error occurred during system reset:\n\n{str(e)}"
            )

