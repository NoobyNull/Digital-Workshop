"""
Theme presets for Digital Workshop.

Defines built-in theme presets: Light, Dark, High Contrast, Solarized, etc.
Each preset is a dictionary mapping color variable names to hex values.

Single Responsibility: Define and manage theme preset definitions.
"""

from typing import Dict

# ============================================================
# Light Theme Preset (Default)
# ============================================================

PRESET_LIGHT: Dict[str, str] = {
    # Window & UI
    "window_bg": "#ffffff",
    "text": "#000000",
    "surface": "#f5f5f5",
    "surface_grad_start": "#f9f9f9",
    "surface_grad_end": "#f0f0f0",

    # Borders & Dividers
    "border": "#d0d0d0",
    "border_light": "#e8e8e8",
    "focus_border": "#0078d4",

    # Menu & Toolbar
    "menubar_bg": "#f5f5f5",
    "menubar_text": "#000000",
    "menubar_item_hover_bg": "#e1e1e1",
    "menubar_item_hover_text": "#000000",
    "toolbar_bg": "#f5f5f5",
    "toolbar_text": "#000000",

    # Status Bar
    "statusbar_bg": "#f5f5f5",
    "statusbar_text": "#000000",
    "statusbar_border": "#d0d0d0",

    # Dock Widgets
    "dock_title_bg": "#e8e8e8",
    "dock_title_text": "#000000",
    "dock_title_border": "#d0d0d0",

    # Buttons
    "button_default_bg": "#f0f0f0",
    "button_default_text": "#000000",
    "button_default_border": "#d0d0d0",
    "button_hover_bg": "#e1e1e1",
    "button_hover_text": "#000000",
    "button_pressed_bg": "#d0d0d0",
    "button_pressed_text": "#000000",

    # Inputs
    "input_bg": "#ffffff",
    "input_text": "#000000",
    "input_border": "#d0d0d0",
    "input_focus_border": "#0078d4",

    # Accent / Brand
    "primary": "#0078d4",
    "primary_hover": "#106ebe",
    "primary_text": "#ffffff",

    # Interactions
    "hover": "#e1e1e1",
    "pressed": "#d0d0d0",
    "selection_bg": "#0078d4",
    "selection_text": "#ffffff",

    # Viewer / 3D
    "canvas_bg": "#f0f0f0",
    "model_surface": "#6496c8",
    "model_ambient": "#324b64",
    "model_specular": "#ffffff",
    "light_color": "#ffffff",
    "edge_color": "#000000",

    # Status Indicators
    "status_success_bg": "#d4edda",
    "status_success_text": "#155724",
    "status_success_border": "#c3e6cb",
    "status_warning_bg": "#fff3cd",
    "status_warning_text": "#856404",
    "status_warning_border": "#ffeaa7",
    "status_error_bg": "#f8d7da",
    "status_error_text": "#721c24",
    "status_error_border": "#f5c6cb",
}

# ============================================================
# Dark Theme Preset
# ============================================================

PRESET_DARK: Dict[str, str] = {
    # Window & UI
    "window_bg": "#1e1e1e",
    "text": "#e0e0e0",
    "surface": "#2d2d2d",
    "surface_grad_start": "#333333",
    "surface_grad_end": "#2a2a2a",

    # Borders & Dividers
    "border": "#404040",
    "border_light": "#555555",
    "focus_border": "#0078d4",

    # Menu & Toolbar
    "menubar_bg": "#2d2d2d",
    "menubar_text": "#e0e0e0",
    "menubar_item_hover_bg": "#404040",
    "menubar_item_hover_text": "#ffffff",
    "toolbar_bg": "#2d2d2d",
    "toolbar_text": "#e0e0e0",

    # Status Bar
    "statusbar_bg": "#2d2d2d",
    "statusbar_text": "#e0e0e0",
    "statusbar_border": "#404040",

    # Dock Widgets
    "dock_title_bg": "#333333",
    "dock_title_text": "#e0e0e0",
    "dock_title_border": "#404040",

    # Buttons
    "button_default_bg": "#333333",
    "button_default_text": "#e0e0e0",
    "button_default_border": "#404040",
    "button_hover_bg": "#404040",
    "button_hover_text": "#ffffff",
    "button_pressed_bg": "#555555",
    "button_pressed_text": "#ffffff",

    # Inputs
    "input_bg": "#2a2a2a",
    "input_text": "#e0e0e0",
    "input_border": "#404040",
    "input_focus_border": "#0078d4",

    # Accent / Brand
    "primary": "#0078d4",
    "primary_hover": "#1084d7",
    "primary_text": "#ffffff",

    # Interactions
    "hover": "#404040",
    "pressed": "#555555",
    "selection_bg": "#0078d4",
    "selection_text": "#ffffff",

    # Viewer / 3D
    "canvas_bg": "#1a1a1a",
    "model_surface": "#6496c8",
    "model_ambient": "#324b64",
    "model_specular": "#ffffff",
    "light_color": "#ffffff",
    "edge_color": "#cccccc",

    # Status Indicators
    "status_success_bg": "#1e4620",
    "status_success_text": "#90ee90",
    "status_success_border": "#2d5a2d",
    "status_warning_bg": "#4d3d00",
    "status_warning_text": "#ffeb99",
    "status_warning_border": "#664d00",
    "status_error_bg": "#4d1a1a",
    "status_error_text": "#ff6b6b",
    "status_error_border": "#802020",
}

# ============================================================
# High Contrast Theme Preset
# ============================================================

PRESET_HIGH_CONTRAST: Dict[str, str] = {
    # Window & UI
    "window_bg": "#000000",
    "text": "#ffffff",
    "surface": "#000000",
    "surface_grad_start": "#000000",
    "surface_grad_end": "#000000",

    # Borders & Dividers
    "border": "#ffffff",
    "border_light": "#e0e0e0",
    "focus_border": "#ffff00",

    # Menu & Toolbar
    "menubar_bg": "#000000",
    "menubar_text": "#ffffff",
    "menubar_item_hover_bg": "#ffff00",
    "menubar_item_hover_text": "#000000",
    "toolbar_bg": "#000000",
    "toolbar_text": "#ffffff",

    # Status Bar
    "statusbar_bg": "#000000",
    "statusbar_text": "#ffffff",
    "statusbar_border": "#ffffff",

    # Dock Widgets
    "dock_title_bg": "#000000",
    "dock_title_text": "#ffffff",
    "dock_title_border": "#ffffff",

    # Buttons
    "button_default_bg": "#000000",
    "button_default_text": "#ffffff",
    "button_default_border": "#ffffff",
    "button_hover_bg": "#ffff00",
    "button_hover_text": "#000000",
    "button_pressed_bg": "#c0c0c0",
    "button_pressed_text": "#000000",

    # Inputs
    "input_bg": "#000000",
    "input_text": "#ffffff",
    "input_border": "#ffffff",
    "input_focus_border": "#ffff00",

    # Accent / Brand
    "primary": "#ffff00",
    "primary_hover": "#ffea00",
    "primary_text": "#000000",

    # Interactions
    "hover": "#ffffff",
    "pressed": "#c0c0c0",
    "selection_bg": "#ffff00",
    "selection_text": "#000000",

    # Viewer / 3D
    "canvas_bg": "#000000",
    "model_surface": "#ffff00",
    "model_ambient": "#ffffff",
    "model_specular": "#ffffff",
    "light_color": "#ffffff",
    "edge_color": "#ffffff",

    # Status Indicators
    "status_success_bg": "#000000",
    "status_success_text": "#00ff00",
    "status_success_border": "#00ff00",
    "status_warning_bg": "#000000",
    "status_warning_text": "#ffff00",
    "status_warning_border": "#ffff00",
    "status_error_bg": "#000000",
    "status_error_text": "#ff0000",
    "status_error_border": "#ff0000",
}

# ============================================================
# Solarized Light Theme Preset
# ============================================================

PRESET_SOLARIZED_LIGHT: Dict[str, str] = {
    # Window & UI
    "window_bg": "#fdf6e3",
    "text": "#657b83",
    "surface": "#eee8d5",
    "surface_grad_start": "#f5f0e8",
    "surface_grad_end": "#ebe6d9",

    # Borders & Dividers
    "border": "#d6d0c8",
    "border_light": "#e8e3db",
    "focus_border": "#268bd2",

    # Menu & Toolbar
    "menubar_bg": "#eee8d5",
    "menubar_text": "#657b83",
    "menubar_item_hover_bg": "#d6d0c8",
    "menubar_item_hover_text": "#073642",
    "toolbar_bg": "#eee8d5",
    "toolbar_text": "#657b83",

    # Status Bar
    "statusbar_bg": "#eee8d5",
    "statusbar_text": "#657b83",
    "statusbar_border": "#d6d0c8",

    # Dock Widgets
    "dock_title_bg": "#d6d0c8",
    "dock_title_text": "#657b83",
    "dock_title_border": "#c5bfb7",

    # Buttons
    "button_default_bg": "#eee8d5",
    "button_default_text": "#657b83",
    "button_default_border": "#d6d0c8",
    "button_hover_bg": "#d6d0c8",
    "button_hover_text": "#073642",
    "button_pressed_bg": "#c5bfb7",
    "button_pressed_text": "#073642",

    # Inputs
    "input_bg": "#fdf6e3",
    "input_text": "#657b83",
    "input_border": "#d6d0c8",
    "input_focus_border": "#268bd2",

    # Accent / Brand
    "primary": "#268bd2",
    "primary_hover": "#2aa198",
    "primary_text": "#fdf6e3",

    # Interactions
    "hover": "#d6d0c8",
    "pressed": "#c5bfb7",
    "selection_bg": "#268bd2",
    "selection_text": "#fdf6e3",

    # Viewer / 3D
    "canvas_bg": "#eee8d5",
    "model_surface": "#268bd2",
    "model_ambient": "#073642",
    "model_specular": "#fdf6e3",
    "light_color": "#fdf6e3",
    "edge_color": "#073642",

    # Status Indicators
    "status_success_bg": "#d5f4e6",
    "status_success_text": "#27ae60",
    "status_success_border": "#a9dfbf",
    "status_warning_bg": "#fef5e7",
    "status_warning_text": "#d68910",
    "status_warning_border": "#f8c471",
    "status_error_bg": "#fadbd8",
    "status_error_text": "#c0392b",
    "status_error_border": "#f5b7b1",
}

# ============================================================
# Solarized Dark Theme Preset
# ============================================================

PRESET_SOLARIZED_DARK: Dict[str, str] = {
    # Window & UI
    "window_bg": "#002b36",
    "text": "#839496",
    "surface": "#073642",
    "surface_grad_start": "#0d3f47",
    "surface_grad_end": "#0a3840",

    # Borders & Dividers
    "border": "#1a4d56",
    "border_light": "#2a5f68",
    "focus_border": "#268bd2",

    # Menu & Toolbar
    "menubar_bg": "#073642",
    "menubar_text": "#839496",
    "menubar_item_hover_bg": "#1a4d56",
    "menubar_item_hover_text": "#93a1a1",
    "toolbar_bg": "#073642",
    "toolbar_text": "#839496",

    # Status Bar
    "statusbar_bg": "#073642",
    "statusbar_text": "#839496",
    "statusbar_border": "#1a4d56",

    # Dock Widgets
    "dock_title_bg": "#0d3f47",
    "dock_title_text": "#839496",
    "dock_title_border": "#1a4d56",

    # Buttons
    "button_default_bg": "#073642",
    "button_default_text": "#839496",
    "button_default_border": "#1a4d56",
    "button_hover_bg": "#1a4d56",
    "button_hover_text": "#93a1a1",
    "button_pressed_bg": "#2a5f68",
    "button_pressed_text": "#93a1a1",

    # Inputs
    "input_bg": "#002b36",
    "input_text": "#839496",
    "input_border": "#1a4d56",
    "input_focus_border": "#268bd2",

    # Accent / Brand
    "primary": "#268bd2",
    "primary_hover": "#2aa198",
    "primary_text": "#002b36",

    # Interactions
    "hover": "#1a4d56",
    "pressed": "#2a5f68",
    "selection_bg": "#268bd2",
    "selection_text": "#002b36",

    # Viewer / 3D
    "canvas_bg": "#002b36",
    "model_surface": "#268bd2",
    "model_ambient": "#073642",
    "model_specular": "#93a1a1",
    "light_color": "#93a1a1",
    "edge_color": "#839496",

    # Status Indicators
    "status_success_bg": "#0d3f2d",
    "status_success_text": "#2ecc71",
    "status_success_border": "#1a5f3f",
    "status_warning_bg": "#3f3d0d",
    "status_warning_text": "#f1c40f",
    "status_warning_border": "#5f5f1a",
    "status_error_bg": "#3f0d0d",
    "status_error_text": "#e74c3c",
    "status_error_border": "#5f1a1a",
}

# ============================================================
# Preset Registry
# ============================================================

PRESETS: Dict[str, Dict[str, str]] = {
    "light": PRESET_LIGHT,
    "dark": PRESET_DARK,
    "high_contrast": PRESET_HIGH_CONTRAST,
    "solarized_light": PRESET_SOLARIZED_LIGHT,
    "solarized_dark": PRESET_SOLARIZED_DARK,
}


def get_preset(name: str) -> Dict[str, str]:
    """Get a preset by name. Returns light preset if not found."""
    return PRESETS.get(name, PRESET_LIGHT)


def list_presets() -> list[str]:
    """List all available preset names."""
    return list(PRESETS.keys())

