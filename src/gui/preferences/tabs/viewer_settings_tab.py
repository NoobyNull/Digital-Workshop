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


from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ViewerSettingsTab(QWidget):
    """3D Viewer settings tab: grid, ground plane, camera, and lighting."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
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

        # Cut List Optimizer layout grid (2D cut layout view)
        clo_group = QFrame()
        clo_layout = QFormLayout(clo_group)
        clo_label = QLabel("<b>Cut List Layout Grid</b>")
        clo_layout.addRow(clo_label)

        self.clo_grid_spacing_spin = QSpinBox()
        self.clo_grid_spacing_spin.setRange(1, 100)
        self.clo_grid_spacing_spin.setValue(1)
        clo_layout.addRow("Grid spacing (layout):", self.clo_grid_spacing_spin)

        self.clo_grid_unit_combo = QComboBox()
        self.clo_grid_unit_combo.addItems(["Feet", "Meters"])
        clo_layout.addRow("Grid units:", self.clo_grid_unit_combo)

        self.clo_grid_opacity_spin = QSpinBox()
        self.clo_grid_opacity_spin.setRange(5, 100)
        self.clo_grid_opacity_spin.setSuffix("%")
        self.clo_grid_opacity_spin.setValue(30)
        clo_layout.addRow("Grid opacity:", self.clo_grid_opacity_spin)

        self.clo_grid_intermediate_check = QCheckBox("Show intermediate lines")
        clo_layout.addRow(self.clo_grid_intermediate_check)

        layout.addWidget(clo_group)

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

        # Quick Controls Group
        quick_group = QFrame()
        quick_layout = QFormLayout(quick_group)
        quick_label = QLabel("<b>Quick Viewer Buttons</b>")
        quick_layout.addRow(quick_label)

        self.show_quick_controls_check = QCheckBox(
            "Show quick action buttons (Solid/Material/Lighting/etc.)"
        )
        quick_layout.addRow(self.show_quick_controls_check)

        layout.addWidget(quick_group)

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
        self.clo_grid_spacing_spin.valueChanged.connect(self._on_settings_changed)
        self.clo_grid_unit_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.clo_grid_opacity_spin.valueChanged.connect(self._on_settings_changed)
        self.clo_grid_intermediate_check.stateChanged.connect(self._on_settings_changed)
        self.ground_visible_check.stateChanged.connect(self._on_settings_changed)
        self.ground_color_btn.clicked.connect(self._on_ground_color_clicked)
        self.ground_offset_slider.valueChanged.connect(self._on_ground_offset_changed)
        self.mouse_sensitivity_slider.valueChanged.connect(
            self._on_mouse_sensitivity_changed
        )
        self.fps_limit_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.zoom_speed_slider.valueChanged.connect(self._on_zoom_speed_changed)
        self.auto_fit_check.stateChanged.connect(self._on_settings_changed)
        self.light_pos_x_slider.valueChanged.connect(self._on_light_pos_x_changed)
        self.light_pos_y_slider.valueChanged.connect(self._on_light_pos_y_changed)
        self.light_pos_z_slider.valueChanged.connect(self._on_light_pos_z_changed)
        self.light_color_btn.clicked.connect(self._on_light_color_clicked)
        self.light_intensity_slider.valueChanged.connect(
            self._on_light_intensity_changed
        )
        self.light_cone_angle_slider.valueChanged.connect(
            self._on_light_cone_angle_changed
        )
        self.enable_fill_light_check.stateChanged.connect(self._on_settings_changed)

        # Gradient signals
        self.enable_gradient_check.stateChanged.connect(self._on_settings_changed)
        self.gradient_top_color_btn.clicked.connect(self._on_gradient_top_color_clicked)
        self.gradient_bottom_color_btn.clicked.connect(
            self._on_gradient_bottom_color_clicked
        )

    def _load_settings(self) -> None:
        """Load current settings from QSettings with fallback to
        ApplicationConfig."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Grid settings - load from QSettings with fallback to config
            self.grid_visible_check.setChecked(
                settings.value("viewer/grid_visible", config.grid_visible, type=bool)
            )
            grid_color = settings.value(
                "viewer/grid_color", config.grid_color, type=str
            )
            self._update_color_button(self.grid_color_btn, grid_color)
            self.grid_size_slider.setValue(
                int(settings.value("viewer/grid_size", config.grid_size, type=float))
            )

            # Ground settings
            self.ground_visible_check.setChecked(
                settings.value(
                    "viewer/ground_visible", config.ground_visible, type=bool
                )
            )
            ground_color = settings.value(
                "viewer/ground_color", config.ground_color, type=str
            )
            self._update_color_button(self.ground_color_btn, ground_color)
            self.ground_offset_slider.setValue(
                int(
                    settings.value(
                        "viewer/ground_offset", config.ground_offset, type=float
                    )
                    * 10
                )
            )

            # Camera settings
            self.mouse_sensitivity_slider.setValue(
                int(
                    settings.value(
                        "viewer/mouse_sensitivity", config.mouse_sensitivity, type=float
                    )
                    * 10
                )
            )
            fps_limit = int(
                settings.value("viewer/fps_limit", config.fps_limit, type=int)
            )
            self.fps_limit_combo.setCurrentIndex(
                {0: 0, 120: 1, 60: 2, 30: 3}.get(fps_limit, 0)
            )
            self.zoom_speed_slider.setValue(
                int(
                    settings.value("viewer/zoom_speed", config.zoom_speed, type=float)
                    * 10
                )
            )
            self.auto_fit_check.setChecked(
                settings.value(
                    "viewer/auto_fit_on_load", config.auto_fit_on_load, type=bool
                )
            )

            # Cut List Optimizer grid settings
            self.clo_grid_spacing_spin.setValue(
                int(
                    settings.value(
                        "clo/grid_spacing", config.clo_grid_spacing, type=float
                    )
                )
            )
            clo_unit = settings.value("clo/grid_unit", config.clo_grid_unit, type=str)
            index = self.clo_grid_unit_combo.findText(clo_unit.capitalize())
            if index != -1:
                self.clo_grid_unit_combo.setCurrentIndex(index)
            self.clo_grid_opacity_spin.setValue(
                int(
                    settings.value(
                        "clo/grid_major_opacity",
                        config.clo_grid_major_opacity,
                        type=int,
                    )
                )
            )
            self.clo_grid_intermediate_check.setChecked(
                settings.value(
                    "clo/grid_show_intermediate",
                    config.clo_grid_show_intermediate,
                    type=bool,
                )
            )

            # Lighting settings
            pos_x = settings.value("lighting/position_x", 90.0, type=float)
            pos_y = settings.value("lighting/position_y", 90.0, type=float)
            pos_z = settings.value("lighting/position_z", 180.0, type=float)
            self.light_pos_x_slider.setValue(int(pos_x))
            self.light_pos_y_slider.setValue(int(pos_y))
            self.light_pos_z_slider.setValue(int(pos_z))

            r = settings.value(
                "lighting/color_r", config.default_light_color_r, type=float
            )
            g = settings.value(
                "lighting/color_g", config.default_light_color_g, type=float
            )
            b = settings.value(
                "lighting/color_b", config.default_light_color_b, type=float
            )
            self._update_color_button(self.light_color_btn, self._rgb_to_hex(r, g, b))
            self.light_intensity_slider.setValue(
                int(
                    settings.value(
                        "lighting/intensity", config.default_light_intensity, type=float
                    )
                    * 100
                )
            )
            cone_angle = settings.value("lighting/cone_angle", 90.0, type=float)
            self.light_cone_angle_slider.setValue(int(cone_angle))
            self.light_cone_angle_label.setText(f"{int(cone_angle)}°")
            self.enable_fill_light_check.setChecked(
                settings.value(
                    "lighting/enable_fill_light", config.enable_fill_light, type=bool
                )
            )

            # Load gradient settings
            self.enable_gradient_check.setChecked(
                settings.value(
                    "viewer/enable_gradient", config.enable_gradient, type=bool
                )
            )
            gradient_top = settings.value(
                "viewer/gradient_top_color", config.gradient_top_color, type=str
            )
            gradient_bottom = settings.value(
                "viewer/gradient_bottom_color", config.gradient_bottom_color, type=str
            )
            self._update_color_button(self.gradient_top_color_btn, gradient_top)
            self._update_color_button(self.gradient_bottom_color_btn, gradient_bottom)

            # Quick controls visibility (default hidden)
            self.show_quick_controls_check.setChecked(
                settings.value("viewer/show_quick_controls", False, type=bool)
            )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to load viewer settings: %s", e)

    def save_settings(self) -> None:
        """Save viewer settings to QSettings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Grid settings
            settings.setValue(
                "viewer/grid_visible", self.grid_visible_check.isChecked()
            )
            settings.setValue(
                "viewer/grid_color",
                self.grid_color_btn.palette().button().color().name(),
            )
            settings.setValue("viewer/grid_size", float(self.grid_size_slider.value()))

            # Cut List Optimizer grid settings
            settings.setValue(
                "clo/grid_spacing", float(self.clo_grid_spacing_spin.value())
            )
            settings.setValue(
                "clo/grid_unit", self.clo_grid_unit_combo.currentText().lower()
            )
            settings.setValue(
                "clo/grid_major_opacity", int(self.clo_grid_opacity_spin.value())
            )
            settings.setValue(
                "clo/grid_show_intermediate",
                self.clo_grid_intermediate_check.isChecked(),
            )

            # Ground settings
            settings.setValue(
                "viewer/ground_visible", self.ground_visible_check.isChecked()
            )
            settings.setValue(
                "viewer/ground_color",
                self.ground_color_btn.palette().button().color().name(),
            )
            settings.setValue(
                "viewer/ground_offset", float(self.ground_offset_slider.value()) / 10.0
            )

            # Camera settings
            settings.setValue(
                "viewer/mouse_sensitivity",
                float(self.mouse_sensitivity_slider.value()) / 10.0,
            )
            settings.setValue(
                "viewer/fps_limit", int(self.fps_limit_combo.currentData())
            )
            settings.setValue(
                "viewer/zoom_speed", float(self.zoom_speed_slider.value()) / 10.0
            )
            settings.setValue(
                "viewer/auto_fit_on_load", self.auto_fit_check.isChecked()
            )

            # Lighting settings
            settings.setValue(
                "lighting/position_x", float(self.light_pos_x_slider.value())
            )
            settings.setValue(
                "lighting/position_y", float(self.light_pos_y_slider.value())
            )
            settings.setValue(
                "lighting/position_z", float(self.light_pos_z_slider.value())
            )

            light_color = self.light_color_btn.palette().button().color().name()
            r, g, b = self._hex_to_rgb(light_color)
            settings.setValue("lighting/color_r", r)
            settings.setValue("lighting/color_g", g)
            settings.setValue("lighting/color_b", b)
            settings.setValue(
                "lighting/intensity", float(self.light_intensity_slider.value()) / 100.0
            )
            settings.setValue(
                "lighting/cone_angle", float(self.light_cone_angle_slider.value())
            )
            settings.setValue(
                "lighting/enable_fill_light", self.enable_fill_light_check.isChecked()
            )

            # Gradient settings
            settings.setValue(
                "viewer/enable_gradient", self.enable_gradient_check.isChecked()
            )
            settings.setValue(
                "viewer/gradient_top_color",
                self.gradient_top_color_btn.palette().button().color().name(),
            )
            settings.setValue(
                "viewer/gradient_bottom_color",
                self.gradient_bottom_color_btn.palette().button().color().name(),
            )

            # Quick controls visibility
            settings.setValue(
                "viewer/show_quick_controls", self.show_quick_controls_check.isChecked()
            )

            if self.logger:
                self.logger.info("Viewer settings saved to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save viewer settings: %s", e)

    def _on_grid_color_clicked(self) -> None:
        """Handle grid color picker."""
        color = QColorDialog.getColor(
            QColor(self.grid_color_btn.palette().button().color()),
            self,
            "Select Grid Color",
        )
        if color.isValid():
            self._update_color_button(self.grid_color_btn, color.name())

    def _on_ground_color_clicked(self) -> None:
        """Handle ground color picker."""
        color = QColorDialog.getColor(
            QColor(self.ground_color_btn.palette().button().color()),
            self,
            "Select Ground Color",
        )
        if color.isValid():
            self._update_color_button(self.ground_color_btn, color.name())

    def _on_light_color_clicked(self) -> None:
        """Handle light color picker."""
        color = QColorDialog.getColor(
            QColor(self.light_color_btn.palette().button().color()),
            self,
            "Select Light Color",
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
            "Select Gradient Top Color (Sky)",
        )
        if color.isValid():
            self._update_color_button(self.gradient_top_color_btn, color.name())

    def _on_gradient_bottom_color_clicked(self) -> None:
        """Handle gradient bottom color picker."""
        color = QColorDialog.getColor(
            QColor(self.gradient_bottom_color_btn.palette().button().color()),
            self,
            "Select Gradient Bottom Color (Ground)",
        )
        if color.isValid():
            self._update_color_button(self.gradient_bottom_color_btn, color.name())

    def _on_settings_changed(self) -> None:
        """Handle settings change."""

    def _update_color_button(self, button: QPushButton, color_hex: str) -> None:
        """Update color button appearance."""
        try:
            color = QColor(color_hex)
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            button.setIcon(QIcon(pixmap))
            button.setStyleSheet(f"background-color: {color_hex};")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB (0-1 range)."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(r: float, g: float, b: float) -> str:
        """Convert RGB (0-1 range) to hex color."""
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
