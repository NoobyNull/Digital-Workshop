"""
Theme system for 3D-MM application.

Centralizes ALL UI colors as variables and provides helpers to use them
consistently across Qt widgets, Qt3D, and VTK. This makes the color scheme
easy to tweak, ensures readability, and supports future theming.

Usage:
- Import hex colors for QSS (Qt Stylesheets) with: from gui.theme import COLORS
  and use Python f-strings in setStyleSheet, e.g. f"color: {COLORS.text};"
- Get QColor for Qt APIs with: from gui.theme import qcolor
- Get normalized RGB tuple (0..1) for VTK with: from gui.theme import vtk_rgb
- Load and persist theme settings: from gui.theme import load_theme_from_settings, save_theme_to_settings
"""

from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any
from pathlib import Path
import json

from PySide6.QtGui import QColor
from PySide6.QtCore import QStandardPaths


def _normalize_hex(h: str) -> str:
    """Return a normalized #RRGGBB hex string."""
    h = h.strip()
    if not h.startswith("#"):
        h = "#" + h
    if len(h) == 4:  # e.g. #abc
        r, g, b = h[1], h[2], h[3]
        h = f"#{r}{r}{g}{g}{b}{b}"
    return h.lower()


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert #RRGGBB to integer RGB tuple (0..255)."""
    h = _normalize_hex(hex_code)
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def hex_to_qcolor(hex_code: str) -> QColor:
    """Convert #RRGGBB to QColor."""
    r, g, b = hex_to_rgb(hex_code)
    return QColor(r, g, b)


def hex_to_vtk_rgb(hex_code: str) -> Tuple[float, float, float]:
    """Convert #RRGGBB to normalized RGB tuple (0..1) for VTK."""
    r, g, b = hex_to_rgb(hex_code)
    return (r / 255.0, g / 255.0, b / 255.0)


@dataclass(frozen=True)
class ThemeColors:
    # Core palette
    window_bg: str = "#ffffff"         # Main window background
    surface: str = "#f5f5f5"           # Toolbars, menubars, cards
    canvas_bg: str = "#f0f0f0"         # 3D canvas/alt background
    text: str = "#000000"              # Primary text
    text_inverse: str = "#ffffff"      # Text on primary or dark surfaces
    text_muted: str = "#666666"        # Subdued text, icons
    disabled_text: str = "#9aa0a6"     # Disabled text/icons

    # Surfaces
    toolbar_bg: str = "#f5f5f5"        # Toolbar background
    card_bg: str = "#ffffff"           # Cards/panels inner background

    # Borders and dividers
    border: str = "#d0d0d0"
    border_light: str = "#f0f0f0"
    focus_border: str = "#2684ff"      # Focus ring / active border

    # Accent/brand
    primary: str = "#0078d4"           # Accent / selection / primary actions
    primary_hover: str = "#106ebe"     # Hover variant for primary
    primary_text: str = "#ffffff"      # Text on primary

    # UI interactions
    hover: str = "#e1e1e1"
    pressed: str = "#d0d0d0"
    selection_bg: str = "#0078d4"
    selection_text: str = "#ffffff"

    # Status
    success: str = "#52c41a"
    warning: str = "#faad14"
    error: str = "#ff4d4f"

    # Controls
    progress_chunk: str = "#0078d4"
    slider_handle: str = "#0078d4"
    tab_selected_border: str = "#0078d4"

    # Viewer / 3D
    model_surface: str = "#6496c8"     # Approx (100,150,200)
    model_ambient: str = "#324b64"     # Approx (50,75,100)
    model_specular: str = "#ffffff"
    light_color: str = "#ffffff"
    edge_color: str = "#000000"

    # Star rating
    star_filled: str = "#ffd700"       # Gold
    star_empty: str = "#c8c8c8"        # Light gray
    star_hover: str = "#ffeb64"        # Light gold

    # Gradients
    surface_grad_start: str = "#fafafa"
    surface_grad_end: str = "#f2f2f2"


# Singleton palette object (can be replaced at runtime via set_theme)
COLORS = ThemeColors()


def color(name: str) -> str:
    """
    Get a hex color string by name (e.g., 'primary', 'text').
    Returns a normalized '#rrggbb' string.
    """
    value = getattr(COLORS, name)
    return _normalize_hex(value)


def qcolor(name: str) -> QColor:
    """
    Get a QColor for a named color (e.g., qcolor('primary')).
    """
    return hex_to_qcolor(color(name))


def vtk_rgb(name: str) -> Tuple[float, float, float]:
    """
    Get a normalized RGB tuple (0..1) for VTK for the given named color.
    """
    return hex_to_vtk_rgb(color(name))


# Prebuilt QSS snippets you can compose if helpful in the future.
# These are optional convenience blocks to encourage consistent styling.

def qss_button_base() -> str:
    return (
        f"QPushButton {{"
        f"  background-color: {COLORS.surface};"
        f"  color: {COLORS.text};"
        f"  border: 1px solid {COLORS.border};"
        f"  padding: 6px 12px;"
        f"  border-radius: 2px;"
        f"}}"
        f"QPushButton:hover {{"
        f"  background-color: {COLORS.hover};"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
        f"QPushButton:pressed {{"
        f"  background-color: {COLORS.pressed};"
        f"}}"
        f"QPushButton:checked {{"
        f"  background-color: {COLORS.primary};"
        f"  color: {COLORS.primary_text};"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
        f"QPushButton:default {{"
        f"  border: 1px solid {COLORS.primary};"
        f"  background-color: {COLORS.primary};"
        f"  color: {COLORS.primary_text};"
        f"  font-weight: bold;"
        f"}}"
        f"QPushButton:default:hover {{"
        f"  background-color: {COLORS.primary_hover};"
        f"}}"
    )


def qss_progress_bar() -> str:
    return (
        f"QProgressBar {{"
        f"  border: 1px solid {COLORS.border};"
        f"  border-radius: 2px;"
        f"  text-align: center;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QProgressBar::chunk {{"
        f"  background-color: {COLORS.progress_chunk};"
        f"  border-radius: 1px;"
        f"}}"
    )


def qss_inputs_base() -> str:
    return (
        f"QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {{"
        f"  border: 1px solid {COLORS.border};"
        f"  border-radius: 2px;"
        f"  padding: 6px;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"  selection-background-color: {COLORS.selection_bg};"
        f"  selection-color: {COLORS.selection_text};"
        f"}}"
        f"QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{"
        f"  border: 2px solid {COLORS.primary};"
        f"  outline: none;"
        f"}}"
        f"QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDateEdit:hover {{"
        f"  border: 1px solid {COLORS.primary};"
        f"}}"
    )

# ---------- Persistence and runtime updates ----------

def _settings_path() -> Path:
    """Return the path to the theme.json in AppData."""
    app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "theme.json"


def theme_to_dict() -> Dict[str, str]:
    """Dump current COLORS to a dict of hex strings."""
    return {k: _normalize_hex(v) for k, v in asdict(COLORS).items()}


def set_theme(overrides: Dict[str, Any]) -> None:
    """
    Replace global COLORS with a new ThemeColors built from overrides.
    Expects hex strings for colors (with or without '#').
    """
    global COLORS
    base = theme_to_dict()
    base.update({k: _normalize_hex(str(v)) for k, v in overrides.items() if hasattr(COLORS, k)})
    COLORS = ThemeColors(**base)  # type: ignore[arg-type]


def load_theme_from_settings() -> None:
    """
    Load theme from theme.json in AppData and apply to COLORS.
    If file doesn't exist or is invalid, keep defaults.
    """
    try:
        path = _settings_path()
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            set_theme({k: v for k, v in data.items() if hasattr(COLORS, k)})
    except Exception:
        # Fail-safe: ignore malformed files
        pass


def save_theme_to_settings() -> None:
    """Persist current COLORS to theme.json in AppData."""
    try:
        path = _settings_path()
        with path.open("w", encoding="utf-8") as f:
            json.dump(theme_to_dict(), f, indent=2)
    except Exception:
        # Fail-safe: ignore IO errors
        pass


def qss_tabs_lists_labels() -> str:
    return (
        f"QTabWidget::pane {{"
        f"  border: 1px solid {COLORS.border};"
        f"  background-color: {COLORS.window_bg};"
        f"}}"
        f"QTabBar::tab {{"
        f"  background: {COLORS.surface};"
        f"  padding: 8px;"
        f"  margin-right: 2px;"
        f"  border: 1px solid {COLORS.border};"
        f"  border-bottom: none;"
        f"  color: {COLORS.text};"
        f"}}"
        f"QTabBar::tab:selected {{"
        f"  background: {COLORS.window_bg};"
        f"  border-bottom: 2px solid {COLORS.tab_selected_border};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QTabBar::tab:hover {{"
        f"  background: {COLORS.hover};"
        f"}}"
        f"QListWidget {{"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"  border: 1px solid {COLORS.border};"
        f"  selection-background-color: {COLORS.selection_bg};"
        f"  selection-color: {COLORS.selection_text};"
        f"}}"
        f"QListWidget::item {{"
        f"  padding: 5px;"
        f"  border-bottom: 1px solid {COLORS.border_light};"
        f"}}"
        f"QListWidget::item:selected {{"
        f"  background-color: {COLORS.selection_bg};"
        f"  color: {COLORS.selection_text};"
        f"}}"
        f"QLabel {{"
        f"  color: {COLORS.text};"
        f"  background-color: transparent;"
        f"}}"
    )


def qss_groupbox_base() -> str:
    return (
        f"QGroupBox {{"
        f"  font-weight: bold;"
        f"  border: 2px solid {COLORS.border};"
        f"  border-radius: 4px;"
        f"  margin-top: 1ex;"
        f"  padding-top: 10px;"
        f"  background-color: {COLORS.window_bg};"
        f"  color: {COLORS.text};"
        f"}}"
        f"QGroupBox::title {{"
        f"  subcontrol-origin: margin;"
        f"  left: 10px;"
        f"  padding: 0 5px 0 5px;"
        f"  color: {COLORS.text};"
        f"}}"
    )