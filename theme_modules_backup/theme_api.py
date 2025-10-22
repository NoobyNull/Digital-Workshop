"""
Public theme API and convenience functions.

Provides module-level functions for accessing colors, managing presets,
and generating QSS stylesheets.
"""

from typing import Any, Dict, Optional, Tuple

from PySide6.QtGui import QColor

from .theme_manager_core import ThemeManager


class _ColorsProxy:
    """
    Proxy object to allow f-string usage like f"color: {COLORS.text};"
    Values are resolved from ThemeManager at access time.
    """

    def __getattr__(self, name: str) -> str:
        return ThemeManager.instance().get_color(name, context="COLORS_proxy")


# Singleton-like proxy for read access inside f-strings, etc.
COLORS = _ColorsProxy()


def color(name: str) -> str:
    """
    Get a hex color string by name (e.g., 'primary', 'text').
    Returns a normalized '#rrggbb' string for hex variables, or raw string for non-hex values.
    """
    return ThemeManager.instance().get_color(name, context="function_color")


def qcolor(name: str) -> QColor:
    """Get a QColor for a named color (e.g., qcolor('primary'))."""
    return ThemeManager.instance().qcolor(name)


def vtk_rgb(name: str) -> Tuple[float, float, float]:
    """Get a normalized RGB tuple (0..1) for VTK for the given named color."""
    return ThemeManager.instance().vtk_rgb(name)


def theme_to_dict() -> Dict[str, str]:
    """Dump current theme colors as a dict of strings."""
    return ThemeManager.instance().colors


def set_theme(overrides: Dict[str, Any]) -> None:
    """
    Replace theme colors with provided overrides.
    Expects hex strings (with or without '#') or valid CSS color strings.
    Unknown keys are ignored to preserve stability.
    """
    ThemeManager.instance().set_colors({k: str(v) for k, v in overrides.items()})


def list_theme_presets() -> list[str]:
    """List names of available theme presets."""
    return ThemeManager.instance().available_presets()


def apply_theme_preset(preset_name: str, custom_mode: Optional[str] = None, base_primary: Optional[str] = None) -> None:
    """Apply a theme preset via ThemeManager."""
    ThemeManager.instance().apply_preset(preset_name, custom_mode=custom_mode, base_primary=base_primary)


def load_theme_from_settings() -> None:
    """
    Load theme from theme.json in AppData and apply to manager.
    If file doesn't exist or is invalid, keep defaults.
    """
    ThemeManager.instance().load_from_settings()


def save_theme_to_settings() -> None:
    """Persist current theme to theme.json in AppData."""
    ThemeManager.instance().save_to_settings()


# ============================================================
# Prebuilt QSS snippets (unchanged for backward compatibility)
# ============================================================

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

