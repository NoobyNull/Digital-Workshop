"""
ColorRow widget - Single color variable editor.

Provides a row with label, color preview, pick button, and reset button.
"""

from typing import Callable, Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QColorDialog
)

from src.gui.theme import ThemeManager, COLORS, SPACING_8, hex_to_rgb
from .theme_manager_helpers import contrasting_text_color, pretty_label


class ColorRow(QWidget):
    """
    One row for a single color variable:
    - label
    - color preview button (shows hex)
    - Pick Color
    - Reset
    """

    def __init__(
        self,
        var_name: str,
        default_hex: str,
        on_changed: Callable[[str, str], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.var_name = var_name
        self._default_hex = default_hex
        self._on_changed = on_changed

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_8)

        self.name_label = QLabel(pretty_label(var_name))
        self.name_label.setMinimumWidth(160)

        self.color_btn = QPushButton("")
        self.color_btn.setObjectName("colorPreviewBtn")
        self.color_btn.setFixedWidth(120)

        self.pick_btn = QPushButton("Pick Color")
        self.reset_btn = QPushButton("Reset")

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.color_btn, 0)
        layout.addWidget(self.pick_btn, 0)
        layout.addWidget(self.reset_btn, 0)
        layout.addStretch(1)

        self.pick_btn.clicked.connect(self._on_pick)
        self.reset_btn.clicked.connect(self._on_reset)
        self.color_btn.clicked.connect(self._on_pick)

        self.update_from_theme()

    def update_from_theme(self) -> None:
        """Update button style from current theme color."""
        tm = ThemeManager.instance()
        hex_val = tm.get_color(self.var_name, context="ColorRow")
        self._apply_button_style(hex_val)

    def _apply_button_style(self, hex_val: str) -> None:
        """Apply color to button with contrasting text."""
        txt = contrasting_text_color(hex_val)
        self.color_btn.setText(hex_val)
        self.color_btn.setStyleSheet(
            f"QPushButton#colorPreviewBtn {{ background-color: {hex_val}; color: {txt}; border: 1px solid {COLORS.border}; padding: 4px 8px; }}"
        )

    def _on_pick(self) -> None:
        """Open color picker dialog."""
        current_hex = ThemeManager.instance().get_color(self.var_name, context="picker")
        try:
            r, g, b = hex_to_rgb(current_hex)
            initial = QColor(r, g, b)
        except Exception:
            initial = QColor(255, 0, 255)  # fallback visually noticeable

        color = QColorDialog.getColor(initial, self, f"Select color for {self.var_name}")
        if color.isValid():
            new_hex = f"#{color.red():02x}{color.green():02x}{color.blue():02x}"
            self._apply_button_style(new_hex)
            self._on_changed(self.var_name, new_hex)

    def _on_reset(self) -> None:
        """Reset color to default."""
        self._apply_button_style(self._default_hex)
        self._on_changed(self.var_name, self._default_hex)

