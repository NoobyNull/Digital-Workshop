"""
Improved lighting control panel with sliders for position, color, and intensity.
This replaces the spinboxes with more intuitive sliders.
"""

from typing import Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QHBoxLayout,
    QColorDialog,
)


class LightingControlPanel(QDockWidget):
    """Improved lighting control panel with sliders for position, color, and intensity."""

    # Signals
    position_changed = Signal(float, float, float)  # X, Y, Z
    color_changed = Signal(float, float, float)  # R, G, B normalized
    intensity_changed = Signal(float)  # 0-2.0

    def __init__(self, parent=None) -> None:
        """TODO: Add docstring."""
        super().__init__("Lighting", parent)
        self.setObjectName("LightingControlPanel")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )

        # Current values (defaults)
        self._pos_x = 100.0
        self._pos_y = 100.0
        self._pos_z = 100.0
        self._color = (1.0, 1.0, 1.0)  # normalized RGB
        self._intensity = 0.8

        # Build UI
        container = QWidget(self)
        root_layout = QVBoxLayout(container)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # Position group with sliders
        self.position_group = QGroupBox("Position")
        pos_layout = QVBoxLayout(self.position_group)
        pos_layout.setContentsMargins(10, 10, 10, 10)
        pos_layout.setSpacing(8)

        # X Position slider
        x_layout = QHBoxLayout()
        x_label = QLabel("X Position:")
        x_label.setMinimumWidth(80)
        self.x_slider = self._make_pos_slider("X", -200.0, 200.0, self._pos_x)
        self.x_value = QLabel(f"{self._pos_x:.0f}")
        self.x_value.setMinimumWidth(40)
        self.x_value.setAlignment(Qt.AlignRight)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_slider, 1)
        x_layout.addWidget(self.x_value)
        pos_layout.addLayout(x_layout)

        # Y Position slider
        y_layout = QHBoxLayout()
        y_label = QLabel("Y Position:")
        y_label.setMinimumWidth(80)
        self.y_slider = self._make_pos_slider("Y", -200.0, 200.0, self._pos_y)
        self.y_value = QLabel(f"{self._pos_y:.0f}")
        self.y_value.setMinimumWidth(40)
        self.y_value.setAlignment(Qt.AlignRight)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_slider, 1)
        y_layout.addWidget(self.y_value)
        pos_layout.addLayout(y_layout)

        # Z Position slider
        z_layout = QHBoxLayout()
        z_label = QLabel("Z Position:")
        z_label.setMinimumWidth(80)
        self.z_slider = self._make_pos_slider("Z", -200.0, 200.0, self._pos_z)
        self.z_value = QLabel(f"{self._pos_z:.0f}")
        self.z_value.setMinimumWidth(40)
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

        # Intensity group with slider
        self.intensity_group = QGroupBox("Intensity")
        intensity_layout = QHBoxLayout(self.intensity_group)
        intensity_layout.setContentsMargins(10, 10, 10, 10)
        intensity_layout.setSpacing(8)

        self.intensity_label = QLabel("Intensity:")
        self.intensity_label.setMinimumWidth(80)
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(0, 200)  # maps to 0.0 .. 2.0
        self.intensity_slider.setSingleStep(1)
        self.intensity_slider.setPageStep(10)
        self.intensity_slider.setValue(int(round(self._intensity * 100.0)))
        self.intensity_value = QLabel(f"{self._intensity:.1f}")
        self.intensity_value.setMinimumWidth(40)
        self.intensity_value.setAlignment(Qt.AlignRight)

        self.intensity_slider.valueChanged.connect(self._on_intensity_changed)

        intensity_layout.addWidget(self.intensity_label)
        intensity_layout.addWidget(self.intensity_slider, 1)
        intensity_layout.addWidget(self.intensity_value)

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
        root_layout.addWidget(self.actions_group)
        root_layout.addStretch()

        self._apply_theme_styles(container)
        self.setWidget(container)

    # ---- Public API ----
    def values(
        """TODO: Add docstring."""
        self,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float]:
        """Return (position(x,y,z), color(r,g,b normalized), intensity)"""
        return (self._pos_x, self._pos_y, self._pos_z), self._color, self._intensity

    def set_values(
        """TODO: Add docstring."""
        self,
        position: Tuple[float, float, float] | None = None,
        color: Tuple[float, float, float] | None = None,
        intensity: float | None = None,
        emit_signals: bool = False,
    ) -> None:
        """Programmatically set control values. Use emit_signals=True to propagate."""
        if position is not None:
            self._pos_x, self._pos_y, self._pos_z = map(float, position)
            self.x_slider.blockSignals(True)
            self.y_slider.blockSignals(True)
            self.z_slider.blockSignals(True)

            self.x_slider.setValue(int(self._pos_x))
            self.y_slider.setValue(int(self._pos_y))
            self.z_slider.setValue(int(self._pos_z))

            self.x_value.setText(f"{self._pos_x:.0f}")
            self.y_value.setText(f"{self._pos_y:.0f}")
            self.z_value.setText(f"{self._pos_z:.0f}")

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

    # ---- Internals ----
    def _make_pos_slider(
        """TODO: Add docstring."""
        self, name: str, min_val: float, max_val: float, initial: float
    ) -> QSlider:
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

        return slider

    def _on_x_position_changed(self, value: int) -> None:
        """TODO: Add docstring."""
        self._pos_x = float(value)
        self.x_value.setText(f"{self._pos_x:.0f}")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _on_y_position_changed(self, value: int) -> None:
        """TODO: Add docstring."""
        self._pos_y = float(value)
        self.y_value.setText(f"{self._pos_y:.0f}")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _on_z_position_changed(self, value: int) -> None:
        """TODO: Add docstring."""
        self._pos_z = float(value)
        self.z_value.setText(f"{self._pos_z:.0f}")
        self.position_changed.emit(self._pos_x, self._pos_y, self._pos_z)

    def _pick_color(self) -> None:
        """TODO: Add docstring."""
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
        """TODO: Add docstring."""
        self._intensity = float(value) / 100.0  # 0.0 .. 2.0
        self.intensity_value.setText(f"{self._intensity:.1f}")
        self.intensity_changed.emit(self._intensity)

    def _reset_defaults(self) -> None:
        """TODO: Add docstring."""
        # Defaults: (100,100,100), white, 0.8
        self.set_values(
            position=(100.0, 100.0, 100.0),
            color=(1.0, 1.0, 1.0),
            intensity=0.8,
            emit_signals=True,
        )

    def _update_color_button_bg(self, color_norm: Tuple[float, float, float]) -> None:
        """TODO: Add docstring."""
        # Convert normalized to hex
        r = max(0, min(255, int(round(color_norm[0] * 255.0))))
        g = max(0, min(255, int(round(color_norm[1] * 255.0))))
        b = max(0, min(255, int(round(color_norm[2] * 255.0))))
        hex_col = f"#{r:02x}{g:02x}{b:02x}"
        # Set background color only, let qt-material handle other styling
        self.color_button.setStyleSheet(f"background-color: {hex_col};")
