from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QSlider,
    QHBoxLayout,
    QColorDialog,
)

from gui.theme import COLORS


class LightingControlPanel(QDockWidget):
    """Pop-out/in panel for lighting controls"""

    # Signals
    position_changed = Signal(float, float, float)  # X, Y, Z
    color_changed = Signal(float, float, float)  # R, G, B normalized
    intensity_changed = Signal(float)  # 0-2.0

    def __init__(self, parent=None):
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

        # Position group
        self.position_group = QGroupBox("Position")
        pos_form = QFormLayout(self.position_group)
        pos_form.setLabelAlignment(Qt.AlignRight)

        self.x_spin = self._make_pos_spin(self._pos_x)
        self.y_spin = self._make_pos_spin(self._pos_y)
        self.z_spin = self._make_pos_spin(self._pos_z)

        self.x_spin.valueChanged.connect(self._on_position_changed)
        self.y_spin.valueChanged.connect(self._on_position_changed)
        self.z_spin.valueChanged.connect(self._on_position_changed)

        pos_form.addRow("X Position:", self.x_spin)
        pos_form.addRow("Y Position:", self.y_spin)
        pos_form.addRow("Z Position:", self.z_spin)

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
    def values(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float]:
        """Return (position(x,y,z), color(r,g,b normalized), intensity)"""
        return (self._pos_x, self._pos_y, self._pos_z), self._color, self._intensity

    def set_values(
        self,
        position: Tuple[float, float, float] | None = None,
        color: Tuple[float, float, float] | None = None,
        intensity: float | None = None,
        emit_signals: bool = False,
    ) -> None:
        """Programmatically set control values. Use emit_signals=True to propagate."""
        if position is not None:
            self._pos_x, self._pos_y, self._pos_z = map(float, position)
            self.x_spin.blockSignals(True)
            self.y_spin.blockSignals(True)
            self.z_spin.blockSignals(True)
            self.x_spin.setValue(self._pos_x)
            self.y_spin.setValue(self._pos_y)
            self.z_spin.setValue(self._pos_z)
            self.x_spin.blockSignals(False)
            self.y_spin.blockSignals(False)
            self.z_spin.blockSignals(False)
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
    def _make_pos_spin(self, initial: float) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(-500.0, 500.0)
        sb.setSingleStep(10.0)
        sb.setDecimals(1)
        sb.setValue(float(initial))
        sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        sb.setKeyboardTracking(False)
        sb.setAlignment(Qt.AlignRight)
        # Input styling (theme-aware)
        sb.setStyleSheet(
            f"""
            QDoubleSpinBox {{
                background-color: {COLORS.input_bg};
                color: {COLORS.input_text};
                border: 1px solid {COLORS.input_border};
                padding: 4px 6px;
                border-radius: 3px;
            }}
            QDoubleSpinBox:focus {{
                border: 1px solid {COLORS.input_focus_border};
            }}
            """
        )
        return sb

    def _on_position_changed(self) -> None:
        self._pos_x = float(self.x_spin.value())
        self._pos_y = float(self.y_spin.value())
        self._pos_z = float(self.z_spin.value())
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

    def _reset_defaults(self) -> None:
        # Defaults: (100,100,100), white, 0.8
        self.set_values(
            position=(100.0, 100.0, 100.0),
            color=(1.0, 1.0, 1.0),
            intensity=0.8,
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

    def _apply_theme_styles(self, container: QWidget) -> None:
        # Group boxes and labels theme
        container.setStyleSheet(
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