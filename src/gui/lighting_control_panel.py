from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QHBoxLayout,
    QColorDialog,
)

from src.gui.theme import COLORS


class LightingControlPanel(QDialog):
    """Floating dialog panel for lighting controls with sliders"""

    # Signals
    position_changed = Signal(float, float, float)  # X, Y, Z
    color_changed = Signal(float, float, float)  # R, G, B normalized
    intensity_changed = Signal(float)  # 0-2.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lighting Controls")
        self.setObjectName("LightingControlPanel")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(400, 400)

        # Current values (defaults) - using angle-based positions (0-180 deg, 90 = center)
        self._pos_x = 90.0  # degrees, 90 = center (maps to 100 actual position)
        self._pos_y = 90.0  # degrees, 90 = center (maps to 100 actual position)
        self._pos_z = 90.0  # degrees, 90 = center (maps to 100 actual position)
        self._color = (1.0, 1.0, 1.0)  # normalized RGB
        self._intensity = 0.8
        self._cone_angle = 30.0  # Cone angle in degrees (1-90)

        # Build UI
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # Position group with sliders
        self.position_group = QGroupBox("Position")
        pos_layout = QVBoxLayout(self.position_group)
        pos_layout.setContentsMargins(10, 10, 10, 10)
        pos_layout.setSpacing(8)

        # X Position slider (0-180 degrees, 90 = center)
        x_layout = QHBoxLayout()
        x_label = QLabel("X Angle:")
        x_label.setMinimumWidth(80)
        self.x_slider = self._make_pos_slider("X", 0, 180, self._pos_x)
        self.x_value = QLabel(f"{self._pos_x:.0f}°")
        self.x_value.setMinimumWidth(50)
        self.x_value.setAlignment(Qt.AlignRight)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_slider, 1)
        x_layout.addWidget(self.x_value)
        pos_layout.addLayout(x_layout)

        # Y Position slider (0-180 degrees, 90 = center)
        y_layout = QHBoxLayout()
        y_label = QLabel("Y Angle:")
        y_label.setMinimumWidth(80)
        self.y_slider = self._make_pos_slider("Y", 0, 180, self._pos_y)
        self.y_value = QLabel(f"{self._pos_y:.0f}°")
        self.y_value.setMinimumWidth(50)
        self.y_value.setAlignment(Qt.AlignRight)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_slider, 1)
        y_layout.addWidget(self.y_value)
        pos_layout.addLayout(y_layout)

        # Z Position slider (0-180 degrees, 90 = center)
        z_layout = QHBoxLayout()
        z_label = QLabel("Z Angle:")
        z_label.setMinimumWidth(80)
        self.z_slider = self._make_pos_slider("Z", 0, 180, self._pos_z)
        self.z_value = QLabel(f"{self._pos_z:.0f}°")
        self.z_value.setMinimumWidth(50)
        self.z_value.setAlignment(Qt.AlignRight)
        z_layout.addWidget(z_label)
        z_layout.addWidget(self.z_slider, 1)
        z_layout.addWidget(self.z_value)
        pos_layout.addLayout(z_layout)

        # Color group
        self.color_group = QGroupBox("Color")
        color_layout = QHBoxLayout(self.color_group)
        color_layout.setContentsMargins(10, 10, 10, 10)
        color_layout.setSpacing(8)

        self.color_label = QLabel("Light Color:")
        self.color_button = QPushButton("Choose…")
        self._apply_button_style(self.color_button)
        self._update_color_button_bg(self._color)

        self.color_button.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()

        # Intensity group
        self.intensity_group = QGroupBox("Intensity")
        intensity_layout = QHBoxLayout(self.intensity_group)
        intensity_layout.setContentsMargins(10, 10, 10, 10)
        intensity_layout.setSpacing(8)

        self.intensity_label = QLabel("Intensity:")
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(0, 200)  # maps to 0.0 .. 2.0
        self.intensity_slider.setSingleStep(1)
        self.intensity_slider.setPageStep(10)
        self.intensity_slider.setValue(int(round(self._intensity * 100.0)))
        self.intensity_value = QLabel(f"{self._intensity:.1f}")

        self.intensity_slider.valueChanged.connect(self._on_intensity_changed)

        intensity_layout.addWidget(self.intensity_label)
        intensity_layout.addWidget(self.intensity_slider, 1)
        intensity_layout.addWidget(self.intensity_value)

        # Cone Angle group with slider (spread/fan control)
        self.cone_group = QGroupBox("Spotlight Cone")
        cone_layout = QHBoxLayout(self.cone_group)
        cone_layout.setContentsMargins(10, 10, 10, 10)
        cone_layout.setSpacing(8)

        self.cone_label = QLabel("Cone Angle:")
        self.cone_label.setMinimumWidth(80)
        self.cone_slider = QSlider(Qt.Horizontal)
        self.cone_slider.setRange(1, 90)  # 1-90 degrees
        self.cone_slider.setSingleStep(1)
        self.cone_slider.setPageStep(10)
        self.cone_slider.setValue(int(round(self._cone_angle)))
        self.cone_value = QLabel(f"{self._cone_angle:.0f}°")
        self.cone_value.setMinimumWidth(50)
        self.cone_value.setAlignment(Qt.AlignRight)

        self.cone_slider.valueChanged.connect(self._on_cone_angle_changed)

        cone_layout.addWidget(self.cone_label)
        cone_layout.addWidget(self.cone_slider, 1)
        cone_layout.addWidget(self.cone_value)

        # Actions group (Reset)
        self.actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(self.actions_group)
        actions_layout.setContentsMargins(10, 10, 10, 10)
        actions_layout.setSpacing(8)
        self.reset_button = QPushButton("Reset to Defaults")
        self._apply_button_style(self.reset_button)
        self.reset_button.clicked.connect(self._reset_defaults)
        actions_layout.addStretch()
        actions_layout.addWidget(self.reset_button)

        # Assemble groups
        root_layout.addWidget(self.position_group)
        root_layout.addWidget(self.color_group)
        root_layout.addWidget(self.intensity_group)
        root_layout.addWidget(self.cone_group)
        root_layout.addWidget(self.actions_group)
        root_layout.addStretch()

        self._apply_theme_styles(self)

    # ---- Public API ----
    # New signal for cone angle
    cone_angle_changed = Signal(float)  # 1-90 degrees
    
    def values(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float, float]:
        """Return (position(x,y,z), color(r,g,b normalized), intensity, cone_angle)"""
        return (self._pos_x, self._pos_y, self._pos_z), self._color, self._intensity, self._cone_angle

    def set_values(
        self,
        position: Tuple[float, float, float] | None = None,
        color: Tuple[float, float, float] | None = None,
        intensity: float | None = None,
        cone_angle: float | None = None,
        emit_signals: bool = False,
    ) -> None:
        """Programmatically set control values. Use emit_signals=True to propagate."""
        if position is not None:
            self._pos_x, self._pos_y, self._pos_z = map(float, position)
            self.x_slider.blockSignals(True)
            self.y_slider.blockSignals(True)
            self.z_slider.blockSignals(True)
            
            # Convert actual position to angle (0-180)
            x_angle = self._pos_to_angle(self._pos_x)
            y_angle = self._pos_to_angle(self._pos_y)
            z_angle = self._pos_to_angle(self._pos_z)
            
            self.x_slider.setValue(int(x_angle))
            self.y_slider.setValue(int(y_angle))
            self.z_slider.setValue(int(z_angle))
            
            self.x_value.setText(f"{x_angle:.0f}°")
            self.y_value.setText(f"{y_angle:.0f}°")
            self.z_value.setText(f"{z_angle:.0f}°")
            
            self.x_slider.blockSignals(False)
            self.y_slider.blockSignals(False)
            self.z_slider.blockSignals(False)
            if emit_signals:
                self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

        if color is not None:
            self._color = tuple(float(max(0.0, min(1.0, c))) for c in color)  # clamp
            self._update_color_button_bg(self._color)
            if emit_signals:
                self.color_changed.emit(*self._color)

        if intensity is not None:
            self._intensity = float(max(0.0, min(2.0, intensity)))
            val = int(round(self._intensity * 100.0))
            self.intensity_slider.blockSignals(True)
            self.intensity_slider.setValue(val)
            self.intensity_slider.blockSignals(False)
            self.intensity_value.setText(f"{self._intensity:.1f}")
            if emit_signals:
                self.intensity_changed.emit(self._intensity)

        if cone_angle is not None:
            self._cone_angle = float(max(1.0, min(90.0, cone_angle)))
            self.cone_slider.blockSignals(True)
            self.cone_slider.setValue(int(round(self._cone_angle)))
            self.cone_slider.blockSignals(False)
            self.cone_value.setText(f"{self._cone_angle:.0f}°")
            if emit_signals:
                self.cone_angle_changed.emit(self._cone_angle)

    # ---- Internals ----
    def _make_pos_slider(self, name: str, min_val: float, max_val: float, initial: float) -> QSlider:
        """Create a position slider with proper range and styling."""
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val))
        slider.setMaximum(int(max_val))
        slider.setValue(int(initial))
        slider.setSingleStep(5)
        slider.setPageStep(20)
        
        # Connect to appropriate handler
        if name == "X":
            slider.valueChanged.connect(self._on_x_position_changed)
        elif name == "Y":
            slider.valueChanged.connect(self._on_y_position_changed)
        elif name == "Z":
            slider.valueChanged.connect(self._on_z_position_changed)
            
        # Apply styling
        slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background-color: {COLORS.input_bg};
                border: 1px solid {COLORS.input_border};
                border-radius: 3px;
                height: 8px;
            }}
            QSlider::handle:horizontal {{
                background-color: {COLORS.primary};
                border: 1px solid {COLORS.primary};
                border-radius: 6px;
                width: 16px;
                margin: -4px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {COLORS.primary_hover};
                border-color: {COLORS.primary_hover};
            }}
            """
        )
        
        return slider

    def _angle_to_pos(self, angle: float) -> float:
        """Convert angle (0-180) to position (-200 to 200), with 90 = 0."""
        return (angle - 90.0) * (400.0 / 180.0)  # Maps 0->-200, 90->0, 180->200
    
    def _pos_to_angle(self, pos: float) -> float:
        """Convert position (-200 to 200) to angle (0-180), with 0 = 90."""
        return (pos / (400.0 / 180.0)) + 90.0  # Maps -200->0, 0->90, 200->180

    def _on_x_position_changed(self, value: int) -> None:
        angle = float(value)
        self._pos_x = self._angle_to_pos(angle)
        self.x_value.setText(f"{angle:.0f}°")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _on_y_position_changed(self, value: int) -> None:
        angle = float(value)
        self._pos_y = self._angle_to_pos(angle)
        self.y_value.setText(f"{angle:.0f}°")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _on_z_position_changed(self, value: int) -> None:
        angle = float(value)
        self._pos_z = self._angle_to_pos(angle)
        self.z_value.setText(f"{angle:.0f}°")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _pick_color(self) -> None:
        # Convert current normalized RGB to QColor
        r, g, b = self._color
        qr, qg, qb = int(r * 255.0), int(g * 255.0), int(b * 255.0)
        initial = QColor(qr, qg, qb)
        chosen = QColorDialog.getColor(initial, self, "Select Light Color")
        if not chosen.isValid():
            return
        nr, ng, nb = chosen.redF(), chosen.greenF(), chosen.blueF()
        self._color = (float(nr), float(ng), float(nb))
        self._update_color_button_bg(self._color)
        self.color_changed.emit(*self._color)

    def _on_intensity_changed(self, value: int) -> None:
        self._intensity = float(value) / 100.0  # 0.0 .. 2.0
        self.intensity_value.setText(f"{self._intensity:.1f}")
        self.intensity_changed.emit(self._intensity)

    def _on_cone_angle_changed(self, value: int) -> None:
        self._cone_angle = float(value)  # 1.0 .. 90.0 degrees
        self.cone_value.setText(f"{self._cone_angle:.0f}°")
        self.cone_angle_changed.emit(self._cone_angle)

    def _reset_defaults(self) -> None:
        # Defaults: (0, 0, 100) actual position (90° on XY sliders), white, 0.8 intensity, 30° cone
        self.set_values(
            position=(0.0, 0.0, 100.0),  # Centered XY, slightly positive Z
            color=(1.0, 1.0, 1.0),
            intensity=0.8,
            cone_angle=30.0,
            emit_signals=True,
        )

    # ---- Styling helpers ----
    def _apply_button_style(self, button: QPushButton) -> None:
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLORS.button_bg};
                color: {COLORS.button_text};
                border: 1px solid {COLORS.button_border};
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.button_hover_bg};
                border-color: {COLORS.button_hover_border};
            }}
            """
        )

    def _update_color_button_bg(self, color_norm: Tuple[float, float, float]) -> None:
        # Convert normalized to hex
        r = max(0, min(255, int(round(color_norm[0] * 255.0))))
        g = max(0, min(255, int(round(color_norm[1] * 255.0))))
        b = max(0, min(255, int(round(color_norm[2] * 255.0))))
        hex_col = f"#{r:02x}{g:02x}{b:02x}"
        self.color_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {hex_col};
                color: {COLORS.button_text};
                border: 1px solid {COLORS.button_border};
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {COLORS.button_hover_border};
            }}
            """
        )

    def _apply_theme_styles(self, dialog: QWidget) -> None:
        # Group boxes and labels theme
        dialog.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS.groupbox_border};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {COLORS.groupbox_bg};
                color: {COLORS.groupbox_text};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS.groupbox_title_text};
            }}
            QLabel {{
                color: {COLORS.label_text};
                background-color: transparent;
            }}
            """
        )