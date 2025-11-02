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
    set_theme, save_theme_to_settings, theme_to_dict, color as color_hex, hex_to_rgb
)
from src.gui.theme.color_helper import get_theme_color
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
        
        # Load and restore last selected tab
        self._restore_last_tab()
        
        # Connect signal to save tab index when changed
        self.tabs.currentChanged.connect(self._save_current_tab)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create new consolidated tabs
        self.general_tab = GeneralTab(on_reset_layout=self.on_reset_layout)
        self.theming_tab = ThemingTab(on_live_apply=self._on_theme_live_applied)
        self.viewer_settings_tab = ViewerSettingsTab()
        self.thumbnail_settings_tab = ThumbnailSettingsTab()
        self.ai_tab = AITab()
        self.advanced_tab = AdvancedTab()

        # Add tabs in new consolidated structure
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.theming_tab, "Appearance")
        self.tabs.addTab(self.viewer_settings_tab, "3D Viewer")
        self.tabs.addTab(self.thumbnail_settings_tab, "Content")
        self.tabs.addTab(self.ai_tab, "AI")
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
    
    def _restore_last_tab(self):
        """Restore the last selected tab from QSettings."""
        try:
            from PySide6.QtCore import QSettings
            from src.core.logging_config import get_logger
            
            settings = QSettings()
            last_tab = settings.value("preferences/last_tab_index", 0, type=int)
            
            # Debug logging
            logger = get_logger(__name__)
            logger.debug(f"Attempting to restore preferences tab index: {last_tab} (total tabs: {self.tabs.count()})")
            
            # Validate the tab index to ensure it's within range
            if 0 <= last_tab < self.tabs.count():
                self.tabs.setCurrentIndex(last_tab)
                logger.debug(f"Successfully restored tab index: {last_tab}")
            else:
                # Invalid index, default to first tab
                self.tabs.setCurrentIndex(0)
                logger.warning(f"Invalid tab index {last_tab}, defaulting to 0")
        except Exception as e:
            # On error, default to first tab
            try:
                from src.core.logging_config import get_logger
                logger = get_logger(__name__)
                logger.error(f"Failed to restore tab index: {e}")
            except Exception:
                pass
            self.tabs.setCurrentIndex(0)
    
    def _save_current_tab(self):
        """Save the current tab index to QSettings."""
        try:
            from PySide6.QtCore import QSettings
            from src.core.logging_config import get_logger
            
            settings = QSettings()
            tab_index = self.tabs.currentIndex()
            settings.setValue("preferences/last_tab_index", tab_index)
            settings.sync()  # Force immediate write to disk
            
            # Debug logging
            logger = get_logger(__name__)
            logger.debug(f"Saved preferences tab index: {tab_index}")
        except Exception as e:
            # Log error if possible
            try:
                from src.core.logging_config import get_logger
                logger = get_logger(__name__)
                logger.error(f"Failed to save tab index: {e}")
            except Exception:
                pass
    
    def closeEvent(self, event):
        """Handle dialog close event and save current tab as backup."""
        self._save_current_tab()
        super().closeEvent(event)

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
            from src.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.info("=== PREFERENCES SAVE STARTED ===")
            
            save_theme_to_settings()
            logger.info("✓ Theme settings saved")

            # Save general settings (window + performance)
            if hasattr(self, 'general_tab'):
                self.general_tab.save_settings()
                logger.info("✓ General tab settings saved")

            # Save viewer settings
            if hasattr(self, 'viewer_settings_tab'):
                self.viewer_settings_tab.save_settings()
                logger.info("✓ Viewer settings tab saved to QSettings")

            # Save thumbnail settings
            if hasattr(self, 'thumbnail_settings_tab'):
                self.thumbnail_settings_tab.save_settings()
                logger.info("✓ Thumbnail settings saved")

            # Save AI settings
            if hasattr(self, 'ai_tab'):
                self.ai_tab.save_settings()
                logger.info("✓ AI settings saved")

            # Emit viewer settings changed signal
            logger.info("Emitting viewer_settings_changed signal...")
            self.viewer_settings_changed.emit()
            logger.info("✓ viewer_settings_changed signal emitted")
            logger.info("=== PREFERENCES SAVE COMPLETE ===")

            QMessageBox.information(self, "Saved", "All settings saved successfully.")
        except Exception as e:
            logger.error(f"ERROR during save: {e}", exc_info=True)
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

            parent_layout.addWidget(mat_group)

        except Exception as e:
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
        except Exception as e:
            pass

    def _apply_theme_styling(self) -> None:
        """Apply theme styling to the tab."""
        try:
            # This is a placeholder for any additional styling
            # QDarkStyleSheet handles most styling automatically
            pass
        except Exception as e:
            pass

    def reload_from_current(self) -> None:
        """Reload theme selector from current theme."""
        try:
            if not self.service:
                return

            current_theme, _ = self.service.get_current_theme()
            self.mode_combo.setCurrentIndex({"dark": 0, "light": 1, "auto": 2}.get(current_theme, 0))
        except Exception as e:
            pass

    def save_settings(self) -> None:
        """Save theming settings."""
        try:
            if self.service:
                self.service.apply_theme(self.mode_combo.currentData())
        except Exception as e:
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

        # Light Position X
        self.light_pos_x_slider = QSlider(Qt.Horizontal)
        self.light_pos_x_slider.setRange(-200, 200)
        self.light_pos_x_slider.setValue(100)
        self.light_pos_x_label = QLabel("100")
        pos_x_row = QHBoxLayout()
        pos_x_row.addWidget(self.light_pos_x_slider)
        pos_x_row.addWidget(self.light_pos_x_label)
        lighting_layout.addRow("Light position X:", pos_x_row)

        # Light Position Y
        self.light_pos_y_slider = QSlider(Qt.Horizontal)
        self.light_pos_y_slider.setRange(-200, 200)
        self.light_pos_y_slider.setValue(100)
        self.light_pos_y_label = QLabel("100")
        pos_y_row = QHBoxLayout()
        pos_y_row.addWidget(self.light_pos_y_slider)
        pos_y_row.addWidget(self.light_pos_y_label)
        lighting_layout.addRow("Light position Y:", pos_y_row)

        # Light Position Z
        self.light_pos_z_slider = QSlider(Qt.Horizontal)
        self.light_pos_z_slider.setRange(-200, 200)
        self.light_pos_z_slider.setValue(100)
        self.light_pos_z_label = QLabel("100")
        pos_z_row = QHBoxLayout()
        pos_z_row.addWidget(self.light_pos_z_slider)
        pos_z_row.addWidget(self.light_pos_z_label)
        lighting_layout.addRow("Light position Z:", pos_z_row)

        self.light_color_btn = QPushButton()
        self.light_color_btn.setMaximumWidth(100)
        lighting_layout.addRow("Light color:", self.light_color_btn)

        self.light_intensity_slider = QSlider(Qt.Horizontal)
        self.light_intensity_slider.setRange(0, 200)
        self.light_intensity_slider.setValue(80)
        self.light_intensity_label = QLabel("0.8")
        intensity_row = QHBoxLayout()
        intensity_row.addWidget(self.light_intensity_slider)
        intensity_row.addWidget(self.light_intensity_label)
        lighting_layout.addRow("Light intensity:", intensity_row)

        # Light Cone Angle
        self.light_cone_angle_slider = QSlider(Qt.Horizontal)
        self.light_cone_angle_slider.setRange(1, 90)
        self.light_cone_angle_slider.setValue(90)
        self.light_cone_angle_label = QLabel("90°")
        cone_angle_row = QHBoxLayout()
        cone_angle_row.addWidget(self.light_cone_angle_slider)
        cone_angle_row.addWidget(self.light_cone_angle_label)
        lighting_layout.addRow("Light cone angle:", cone_angle_row)

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
        self.light_pos_x_slider.valueChanged.connect(self._on_light_pos_x_changed)
        self.light_pos_y_slider.valueChanged.connect(self._on_light_pos_y_changed)
        self.light_pos_z_slider.valueChanged.connect(self._on_light_pos_z_changed)
        self.light_color_btn.clicked.connect(self._on_light_color_clicked)
        self.light_intensity_slider.valueChanged.connect(self._on_light_intensity_changed)
        self.light_cone_angle_slider.valueChanged.connect(self._on_light_cone_angle_changed)
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
            pos_x = settings.value("lighting/position_x", 90.0, type=float)
            pos_y = settings.value("lighting/position_y", 90.0, type=float)
            pos_z = settings.value("lighting/position_z", 180.0, type=float)
            self.light_pos_x_slider.setValue(int(pos_x))
            self.light_pos_y_slider.setValue(int(pos_y))
            self.light_pos_z_slider.setValue(int(pos_z))

            r = settings.value("lighting/color_r", config.default_light_color_r, type=float)
            g = settings.value("lighting/color_g", config.default_light_color_g, type=float)
            b = settings.value("lighting/color_b", config.default_light_color_b, type=float)
            self._update_color_button(self.light_color_btn, self._rgb_to_hex(r, g, b))
            self.light_intensity_slider.setValue(int(settings.value("lighting/intensity", config.default_light_intensity, type=float) * 100))
            cone_angle = settings.value("lighting/cone_angle", 90.0, type=float)
            self.light_cone_angle_slider.setValue(int(cone_angle))
            self.light_cone_angle_label.setText(f"{int(cone_angle)}°")
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
            settings.setValue("lighting/position_x", float(self.light_pos_x_slider.value()))
            settings.setValue("lighting/position_y", float(self.light_pos_y_slider.value()))
            settings.setValue("lighting/position_z", float(self.light_pos_z_slider.value()))

            light_color = self.light_color_btn.palette().button().color().name()
            r, g, b = self._hex_to_rgb(light_color)
            settings.setValue("lighting/color_r", r)
            settings.setValue("lighting/color_g", g)
            settings.setValue("lighting/color_b", b)
            settings.setValue("lighting/intensity", float(self.light_intensity_slider.value()) / 100.0)
            settings.setValue("lighting/cone_angle", float(self.light_cone_angle_slider.value()))
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

    def _on_light_pos_x_changed(self, value: int) -> None:
        """Update light position X label."""
        self.light_pos_x_label.setText(f"{value}")

    def _on_light_pos_y_changed(self, value: int) -> None:
        """Update light position Y label."""
        self.light_pos_y_label.setText(f"{value}")

    def _on_light_pos_z_changed(self, value: int) -> None:
        """Update light position Z label."""
        self.light_pos_z_label.setText(f"{value}")

    def _on_light_intensity_changed(self, value: int) -> None:
        """Update light intensity label."""
        self.light_intensity_label.setText(f"{value / 100.0:.2f}")

    def _on_light_cone_angle_changed(self, value: int) -> None:
        """Update light cone angle label."""
        self.light_cone_angle_label.setText(f"{value}°")

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


class GeneralTab(QWidget):
    """General settings tab: window, layout, and performance settings combined."""
    
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
        """Setup the combined general settings UI."""
        # Create scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("General Application Settings")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)
        
        desc = QLabel("Configure window behavior, layout management, and system performance.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # === Window Settings Section ===
        window_section = QFrame()
        window_layout = QVBoxLayout(window_section)
        
        window_label = QLabel("<b>Window & Layout</b>")
        window_label.setStyleSheet("font-size: 11pt;")
        window_layout.addWidget(window_label)
        
        # Window dimensions
        dim_form = QFormLayout()
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1200)
        self.window_width_spin.setSuffix(" px")
        dim_form.addRow("Default width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(800)
        self.window_height_spin.setSuffix(" px")
        dim_form.addRow("Default height:", self.window_height_spin)
        
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(400, 1200)
        self.min_width_spin.setValue(800)
        self.min_width_spin.setSuffix(" px")
        dim_form.addRow("Minimum width:", self.min_width_spin)
        
        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(300, 1000)
        self.min_height_spin.setValue(600)
        self.min_height_spin.setSuffix(" px")
        dim_form.addRow("Minimum height:", self.min_height_spin)
        
        window_layout.addLayout(dim_form)
        
        # Startup behavior
        self.maximize_startup_check = QCheckBox("Maximize window on startup")
        self.remember_size_check = QCheckBox("Remember window size on exit")
        window_layout.addWidget(self.maximize_startup_check)
        window_layout.addWidget(self.remember_size_check)
        
        # Layout reset
        reset_row = QHBoxLayout()
        reset_row.addWidget(QLabel("Reset the window and dock layout to default positions."))
        reset_row.addStretch(1)
        self.btn_reset_layout = QPushButton("Reset Layout")
        reset_row.addWidget(self.btn_reset_layout)
        window_layout.addLayout(reset_row)
        
        layout.addWidget(window_section)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # === Performance Settings Section ===
        perf_section = QFrame()
        perf_layout = QVBoxLayout(perf_section)
        
        perf_label = QLabel("<b>Performance & Memory</b>")
        perf_label.setStyleSheet("font-size: 11pt;")
        perf_layout.addWidget(perf_label)
        
        perf_desc = QLabel(
            "Configure memory allocation. Smart calculation: min(doubled_minimum, 50% available, total - 20%)"
        )
        perf_desc.setWordWrap(True)
        perf_layout.addWidget(perf_desc)
        
        # Memory mode
        self.auto_radio = QCheckBox("Auto (Smart Calculation)")
        self.auto_radio.setChecked(True)
        perf_layout.addWidget(self.auto_radio)
        
        self.manual_radio = QCheckBox("Manual Override")
        perf_layout.addWidget(self.manual_radio)
        
        # Manual override slider
        slider_form = QFormLayout()
        slider_layout = QHBoxLayout()
        
        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(10)
        self.memory_slider.setMaximum(95)
        self.memory_slider.setValue(80)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(5)
        slider_layout.addWidget(self.memory_slider)
        
        self.memory_value_label = QLabel("80%")
        self.memory_value_label.setMinimumWidth(80)
        slider_layout.addWidget(self.memory_value_label)
        
        slider_form.addRow("Cache limit (% of RAM):", slider_layout)
        perf_layout.addLayout(slider_form)
        
        # System info
        self.system_info_label = QLabel()
        self.system_info_label.setWordWrap(True)
        self.system_info_label.setStyleSheet("padding: 8px; background-color: rgba(0, 0, 0, 0.05); border-radius: 4px;")
        perf_layout.addWidget(self.system_info_label)
        
        layout.addWidget(perf_section)
        
        layout.addStretch(1)
        
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Connect signals
        self.btn_reset_layout.clicked.connect(self._handle_reset)
        self.auto_radio.toggled.connect(self._on_mode_changed)
        self.manual_radio.toggled.connect(self._on_mode_changed)
        self.memory_slider.valueChanged.connect(self._on_slider_changed)
        
        # Update system info
        self._update_system_info()
    
    def _load_settings(self) -> None:
        """Load current settings from config."""
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()
            
            # Window settings
            self.window_width_spin.setValue(config.default_window_width)
            self.window_height_spin.setValue(config.default_window_height)
            self.min_width_spin.setValue(config.minimum_window_width)
            self.min_height_spin.setValue(config.minimum_window_height)
            self.maximize_startup_check.setChecked(config.maximize_on_startup)
            self.remember_size_check.setChecked(config.remember_window_size)
            
            # Performance settings
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
                self.logger.error(f"Failed to load general settings: {e}")
    
    def save_settings(self) -> None:
        """Save all general settings to config."""
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()
            
            # Save window settings
            config.default_window_width = self.window_width_spin.value()
            config.default_window_height = self.window_height_spin.value()
            config.minimum_window_width = self.min_width_spin.value()
            config.minimum_window_height = self.min_height_spin.value()
            config.maximize_on_startup = self.maximize_startup_check.isChecked()
            config.remember_window_size = self.remember_size_check.isChecked()
            
            # Save performance settings
            config.use_manual_memory_override = self.manual_radio.isChecked()
            if self.manual_radio.isChecked():
                config.manual_cache_limit_percent = self.memory_slider.value()
            
            if self.logger:
                self.logger.info("General settings saved")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save general settings: {e}")
    
    def _handle_reset(self):
        """Handle layout reset."""
        try:
            if callable(self.on_reset_layout):
                self.on_reset_layout()
                QMessageBox.information(self, "Layout Reset", "Window layout has been reset to defaults.")
        except Exception as e:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset layout:\n{e}")
    
    def _on_mode_changed(self) -> None:
        """Handle memory mode change."""
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
                    f"<b>Manual Mode:</b> {percent}% of {total_mb} MB = <b>{limit_mb} MB</b><br>"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB"
                )
            else:
                limit_mb = config.get_effective_memory_limit_mb(available_mb, total_mb)
                hard_max = int(total_mb * (100 - config.system_memory_reserve_percent) / 100)
                fifty_percent = available_mb // 2
                doubled_min = config.min_memory_specification_mb * 2
                
                info_text = (
                    f"<b>Smart Calculation:</b> <b>{limit_mb} MB</b><br>"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB<br>"
                    f"Calculated from: min({doubled_min}, {fifty_percent}, {hard_max})"
                )
            
            self.system_info_label.setText(info_text)
        except Exception as e:
            self.system_info_label.setText(f"Error: {e}")


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
        self.preview_label.setStyleSheet(f"border: 1px solid {get_theme_color('border')}; border-radius: 4px;")
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
        self.material_preview_label.setStyleSheet(f"border: 1px solid {get_theme_color('border')}; border-radius: 4px;")
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
        """Load current settings from QSettings with fallback to ApplicationConfig."""
        try:
            from src.core.application_config import ApplicationConfig
            from PySide6.QtCore import QSettings

            config = ApplicationConfig.get_default()
            settings = QSettings()

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS LOAD ===")

            # Load from QSettings with fallback to ApplicationConfig
            bg_image = settings.value("thumbnail/background_image", config.thumbnail_bg_image, type=str)
            material = settings.value("thumbnail/material", config.thumbnail_material, type=str)

            if self.logger:
                self.logger.info(f"Loaded from QSettings: bg={bg_image}, material={material}")

            # Update ApplicationConfig for runtime compatibility
            if bg_image:
                config.thumbnail_bg_image = bg_image
            if material:
                config.thumbnail_material = material

            # Load background into UI
            if bg_image:
                for i in range(self.bg_list.count()):
                    item = self.bg_list.item(i)
                    if item.data(Qt.UserRole) == bg_image:
                        self.bg_list.setCurrentItem(item)
                        if self.logger:
                            self.logger.info(f"✓ Set background to: {bg_image}")
                        break

            # Load material into UI
            if material:
                idx = self.material_combo.findData(material)
                if idx >= 0:
                    self.material_combo.setCurrentIndex(idx)
                    if self.logger:
                        self.logger.info(f"✓ Set material to: {material}")

            self._update_preview()
            
            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS LOAD COMPLETE ===")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load thumbnail settings: {e}", exc_info=True)

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
        """Save thumbnail settings to QSettings for persistence."""
        try:
            from src.core.application_config import ApplicationConfig
            from PySide6.QtCore import QSettings

            config = ApplicationConfig.get_default()
            settings = QSettings()  # Use QSettings for persistence
            settings_dict = self.get_settings()

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS SAVE ===")
                self.logger.info(f"Attempting to save: bg={settings_dict['background_image']}, material={settings_dict['material']}")

            # Save to QSettings (persistent storage)
            settings.setValue("thumbnail/background_image", settings_dict["background_image"])
            settings.setValue("thumbnail/material", settings_dict["material"])
            settings.sync()  # Force immediate write to disk

            # Also update ApplicationConfig for runtime compatibility
            config.thumbnail_bg_image = settings_dict["background_image"]
            config.thumbnail_material = settings_dict["material"]

            if self.logger:
                self.logger.info("✓ Content settings saved to QSettings (persistent)")
                self.logger.info(f"QSettings thumbnail/background_image = {settings_dict['background_image']}")
                self.logger.info(f"QSettings thumbnail/material = {settings_dict['material']}")
                self.logger.info(f"ApplicationConfig also updated for runtime compatibility")
                self.logger.info("=== THUMBNAIL SETTINGS SAVE COMPLETE ===")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save settings: {e}", exc_info=True)

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
        self.logger = None
        self.theme_manager = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Advanced Settings")
        header.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {get_theme_color('text_primary')};")
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
        db_warning.setStyleSheet(f"color: {get_theme_color('warning')}; padding: 8px; background-color: rgba(255, 165, 0, 0.1); border-radius: 4px;")
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
        warning.setStyleSheet(f"color: {get_theme_color('error')}; padding: 8px; background-color: rgba(255, 107, 107, 0.1); border-radius: 4px;")
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

    def save_settings(self) -> None:
        """Save advanced settings (no-op for this tab)."""
        pass


class AITab(QWidget):
    """AI Description Service configuration tab."""

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

    def _setup_ui(self):
        """Setup the AI configuration UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("AI Description Service")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)

        desc = QLabel(
            "Configure AI providers for automatic image description generation. "
            "Select your preferred provider and enter API keys to enable AI-powered descriptions."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Provider Selection Group
        provider_group = QFrame()
        provider_layout = QVBoxLayout(provider_group)

        provider_label = QLabel("<b>AI Provider Selection</b>")
        provider_label.setStyleSheet("font-size: 11pt;")
        provider_layout.addWidget(provider_label)

        # Provider combo box
        provider_form = QFormLayout()
        self.provider_combo = QComboBox()
        self._populate_providers()
        provider_form.addRow("Preferred Provider:", self.provider_combo)
        provider_layout.addLayout(provider_form)

        layout.addWidget(provider_group)

        # API Configuration Group
        api_group = QFrame()
        api_layout = QVBoxLayout(api_group)

        api_label = QLabel("<b>API Configuration</b>")
        api_label.setStyleSheet("font-size: 11pt;")
        api_layout.addWidget(api_label)

        # API Key input
        api_key_form = QFormLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter API key for selected provider")
        api_key_form.addRow("API Key:", self.api_key_edit)
        api_layout.addLayout(api_key_form)

        # Model selection
        model_form = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_form.addRow("Model:", self.model_combo)
        api_layout.addLayout(model_form)

        layout.addWidget(api_group)

        # Custom Prompt Group
        prompt_group = QFrame()
        prompt_layout = QVBoxLayout(prompt_group)

        prompt_label = QLabel("<b>Custom Prompt</b>")
        prompt_label.setStyleSheet("font-size: 11pt;")
        prompt_layout.addWidget(prompt_label)

        prompt_desc = QLabel(
            "Customize the prompt used for image description. Use {image_path} as placeholder for image path."
        )
        prompt_desc.setWordWrap(True)
        prompt_layout.addWidget(prompt_desc)

        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("Describe this image in detail...")
        prompt_layout.addWidget(self.prompt_edit)

        layout.addWidget(prompt_group)

        # Batch Processing Group
        batch_group = QFrame()
        batch_layout = QVBoxLayout(batch_group)

        batch_label = QLabel("<b>Batch Processing</b>")
        batch_label.setStyleSheet("font-size: 11pt;")
        batch_layout.addWidget(batch_label)

        # Batch size
        batch_form = QFormLayout()
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 50)
        self.batch_size_spin.setValue(5)
        self.batch_size_spin.setSuffix(" images")
        batch_form.addRow("Batch Size:", self.batch_size_spin)
        batch_layout.addLayout(batch_form)

        # Enable batch processing
        self.enable_batch_check = QCheckBox("Enable batch processing for multiple images")
        batch_layout.addWidget(self.enable_batch_check)

        layout.addWidget(batch_group)

        # Test Connection Group
        test_group = QFrame()
        test_layout = QVBoxLayout(test_group)

        test_label = QLabel("<b>Connection Test</b>")
        test_label.setStyleSheet("font-size: 11pt;")
        test_layout.addWidget(test_label)

        test_desc = QLabel("Test your AI provider configuration to ensure it's working correctly.")
        test_desc.setWordWrap(True)
        test_layout.addWidget(test_desc)

        test_button_row = QHBoxLayout()
        test_button_row.addStretch(1)
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        test_button_row.addWidget(self.test_button)
        test_layout.addLayout(test_button_row)

        self.test_result_label = QLabel()
        self.test_result_label.setWordWrap(True)
        self.test_result_label.setStyleSheet("padding: 8px; border-radius: 4px;")
        test_layout.addWidget(self.test_result_label)

        layout.addWidget(test_group)

        layout.addStretch()

        # Connect signals
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        # Also connect to activated signal for better compatibility
        self.provider_combo.activated.connect(self._on_provider_changed)
        self.api_key_edit.textChanged.connect(self._on_settings_changed)
        self.model_combo.currentTextChanged.connect(self._on_settings_changed)
        self.prompt_edit.textChanged.connect(self._on_settings_changed)
        self.batch_size_spin.valueChanged.connect(self._on_settings_changed)
        self.enable_batch_check.stateChanged.connect(self._on_settings_changed)

    def _populate_providers(self):
        """Populate provider combo box."""
        try:
            from src.gui.services.ai_description_service import AIDescriptionService
            
            providers = AIDescriptionService.get_provider_display_names()
            for provider_id, provider_name in providers.items():
                self.provider_combo.addItem(provider_name, provider_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate providers: {e}")

    def _populate_models(self, provider_id: str):
        """Populate model combo box for selected provider."""
        try:
            from src.gui.services.ai_description_service import AIDescriptionService
            
            # Clear existing items
            self.model_combo.clear()
            
            # Get available models for the provider
            models = AIDescriptionService.get_available_models(provider_id)
            
            if models:
                for model_id, model_name in models.items():
                    self.model_combo.addItem(model_name, model_id)
            else:
                # If no models found, add a default entry
                self.model_combo.addItem("Default Model", "default")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate models for {provider_id}: {e}")
            # Add fallback model
            self.model_combo.clear()
            self.model_combo.addItem("Default Model", "default")

    def _load_settings(self):
        """Load current AI settings from QSettings (excluding API keys)."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Load provider selection
            provider_id = settings.value("ai/provider_id", "openai", type=str)
            provider_index = self.provider_combo.findData(provider_id)
            if provider_index >= 0:
                self.provider_combo.setCurrentIndex(provider_index)

            # NOTE: API keys are NOT loaded from QSettings for security reasons
            # API keys should be provided via environment variables or secure storage
            self.api_key_edit.setText("")

            # Load model
            model_id = settings.value("ai/model_id", "", type=str)

            # Always populate models for the current provider first
            if provider_id:
                self._populate_models(provider_id)

            if model_id:
                model_index = self.model_combo.findData(model_id)
                if model_index >= 0:
                    self.model_combo.setCurrentIndex(model_index)
                else:
                    self.model_combo.setCurrentText(model_id)

            # Load custom prompt
            prompt = settings.value("ai/custom_prompt", "", type=str)
            self.prompt_edit.setText(prompt)

            # Load batch settings
            batch_size = settings.value("ai/batch_size", 5, type=int)
            self.batch_size_spin.setValue(batch_size)

            enable_batch = settings.value("ai/enable_batch", False, type=bool)
            self.enable_batch_check.setChecked(enable_batch)

            if self.logger:
                self.logger.info("AI settings loaded from QSettings (API keys excluded for security)")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load AI settings: {e}")

    def save_settings(self):
        """Save AI settings to QSettings (excluding API keys for security)."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Save provider selection
            provider_id = self.provider_combo.currentData()
            if provider_id:
                settings.setValue("ai/provider_id", provider_id)

            # NOTE: API keys are NOT saved to QSettings for security reasons
            # API keys should be provided via environment variables or secure storage
            # The API key field is cleared on load to prevent accidental exposure

            # Save model selection
            model_id = self.model_combo.currentData() or self.model_combo.currentText()
            if model_id:
                settings.setValue("ai/model_id", model_id)

            # Save custom prompt
            prompt = self.prompt_edit.text().strip()
            settings.setValue("ai/custom_prompt", prompt)

            # Save batch settings
            settings.setValue("ai/batch_size", self.batch_size_spin.value())
            settings.setValue("ai/enable_batch", self.enable_batch_check.isChecked())
            
            settings.sync()
            
            if self.logger:
                self.logger.info("AI settings saved to QSettings")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save AI settings: {e}")

    def _on_provider_changed(self, index: int):
        """Handle provider selection change."""
        provider_id = self.provider_combo.currentData()
        if provider_id:
            self._populate_models(provider_id)
        self._on_settings_changed()

    def _on_settings_changed(self):
        """Handle settings change."""
        # Update test result to indicate unsaved changes
        self.test_result_label.setText("Settings changed - save to apply")
        self.test_result_label.setStyleSheet("padding: 8px; background-color: rgba(255, 165, 0, 0.1); border-radius: 4px;")

    def _test_connection(self):
        """Test AI provider connection."""
        try:
            from src.gui.services.ai_description_service import AIDescriptionService
            
            provider_id = self.provider_combo.currentData()
            api_key = self.api_key_edit.text().strip()
            model_id = self.model_combo.currentData() or self.model_combo.currentText()
            
            if not provider_id:
                self._show_test_result("Please select a provider", "error")
                return
            
            if not api_key:
                self._show_test_result("Please enter an API key", "error")
                return
            
            if not model_id:
                self._show_test_result("Please select or enter a model", "error")
                return
            
            # Disable test button during test
            self.test_button.setEnabled(False)
            self.test_button.setText("Testing...")

            # Test provider connection (static method)
            success, message = AIDescriptionService.test_provider_connection(provider_id, api_key, model_id)
            
            if success:
                self._show_test_result(f"✓ Connection successful! {message}", "success")
            else:
                self._show_test_result(f"✗ Connection failed: {message}", "error")
                
        except Exception as e:
            self._show_test_result(f"✗ Test failed: {str(e)}", "error")
        finally:
            self.test_button.setEnabled(True)
            self.test_button.setText("Test Connection")

    def _show_test_result(self, message: str, status: str):
        """Show test result message."""
        self.test_result_label.setText(message)
        
        if status == "success":
            self.test_result_label.setStyleSheet("padding: 8px; background-color: rgba(76, 175, 80, 0.1); border-radius: 4px; color: #4CAF50;")
        elif status == "error":
            self.test_result_label.setStyleSheet("padding: 8px; background-color: rgba(244, 67, 54, 0.1); border-radius: 4px; color: #f44336;")
        else:
            self.test_result_label.setStyleSheet("padding: 8px; background-color: rgba(158, 158, 158, 0.1); border-radius: 4px;")

