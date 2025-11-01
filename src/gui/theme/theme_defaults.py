"""
Default theme color definitions.

Provides the ThemeDefaults dataclass with comprehensive color definitions
organized by functional categories (buttons, inputs, surfaces, etc.).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeDefaults:
    """Default color definitions for light theme."""

    # Window & UI Elements
    window_bg: str = "#ffffff"
    text: str = "#000000"
    text_inverse: str = "#ffffff"
    text_muted: str = "#666666"
    disabled_text: str = "#9aa0a6"

    menubar_bg: str = "#f5f5f5"
    menubar_text: str = "#000000"
    menubar_border: str = "#d0d0d0"
    menubar_item_hover_bg: str = "#0078d4"
    menubar_item_hover_text: str = "#ffffff"
    menubar_item_pressed_bg: str = "#106ebe"

    # Surfaces
    surface: str = "#f5f5f5"  # toolbars, panes
    surface_alt: str = "#ffffff"  # cards/panels inner background
    card_bg: str = "#ffffff"
    surface_grad_start: str = "#fafafa"  # subtle gradient example
    surface_grad_end: str = "#f2f2f2"

    # Toolbars
    toolbar_bg: str = "#f5f5f5"
    toolbar_border: str = "#d0d0d0"
    toolbar_handle_bg: str = "#d0d0d0"
    toolbutton_bg: str = "transparent"
    toolbutton_border: str = "transparent"
    toolbutton_hover_bg: str = "#e1e1e1"
    toolbutton_hover_border: str = "#0078d4"
    toolbutton_pressed_bg: str = "#d0d0d0"
    toolbutton_checked_bg: str = "#0078d4"
    toolbutton_checked_border: str = "#0078d4"
    toolbutton_checked_text: str = "#ffffff"

    # Status Bar
    statusbar_bg: str = "#f5f5f5"
    statusbar_text: str = "#000000"
    statusbar_border: str = "#d0d0d0"

    # Dock Widgets
    dock_bg: str = "#ffffff"
    dock_text: str = "#000000"
    dock_border: str = "#d0d0d0"
    dock_title_bg: str = "#f5f5f5"
    dock_title_border: str = "#d0d0d0"

    # Controls - Buttons (all states)
    button_bg: str = "#f5f5f5"
    button_text: str = "#000000"
    button_border: str = "#d0d0d0"
    button_hover_bg: str = "#e1e1e1"
    button_hover_border: str = "#0078d4"
    button_pressed_bg: str = "#d0d0d0"
    button_checked_bg: str = "#0078d4"
    button_checked_text: str = "#ffffff"
    button_checked_border: str = "#0078d4"
    button_default_bg: str = "#0078d4"
    button_default_text: str = "#ffffff"
    button_default_border: str = "#0078d4"
    button_default_hover_bg: str = "#106ebe"
    button_disabled_bg: str = "#f0f0f0"
    button_disabled_text: str = "#a0a0a0"
    button_disabled_border: str = "#e0e0e0"

    # Inputs & Selection
    input_bg: str = "#ffffff"
    input_text: str = "#000000"
    input_border: str = "#d0d0d0"
    input_focus_border: str = "#0078d4"
    input_disabled_bg: str = "#f5f5f5"
    input_disabled_text: str = "#a0a0a0"

    selection_bg: str = "#0078d4"
    selection_text: str = "#ffffff"

    # Combobox
    combobox_bg: str = "#ffffff"
    combobox_text: str = "#000000"
    combobox_border: str = "#d0d0d0"
    combobox_focus_border: str = "#0078d4"
    combobox_arrow_color: str = "#666666"

    # Progress Bar
    progress_bg: str = "#ffffff"
    progress_text: str = "#000000"
    progress_border: str = "#d0d0d0"
    progress_chunk: str = "#0078d4"
    progress_disabled_border: str = "#e0e0e0"
    progress_disabled_bg: str = "#f5f5f5"
    progress_disabled_text: str = "#a0a0a0"
    progress_disabled_chunk: str = "#d0d0d0"

    # Tabs
    tab_pane_border: str = "#d0d0d0"
    tab_pane_bg: str = "#ffffff"
    tab_bg: str = "#f5f5f5"
    tab_text: str = "#000000"
    tab_border: str = "#d0d0d0"
    tab_selected_bg: str = "#ffffff"
    tab_selected_border: str = "#0078d4"
    tab_hover_bg: str = "#e1e1e1"

    # Tables & Lists
    table_bg: str = "#ffffff"
    table_text: str = "#000000"
    table_border: str = "#d0d0d0"
    table_gridline: str = "#e0e0e0"
    table_alternate_row_bg: str = "#f5f5f5"
    header_bg: str = "#f5f5f5"
    header_text: str = "#000000"
    header_border: str = "#d0d0d0"

    # Scrollbars
    scrollbar_bg: str = "#f5f5f5"
    scrollbar_border: str = "#d0d0d0"
    scrollbar_handle_bg: str = "#d0d0d0"
    scrollbar_handle_hover_bg: str = "#a0a0a0"

    # Splitters
    splitter_handle_bg: str = "#d0d0d0"

    # Group Boxes
    groupbox_border: str = "#d0d0d0"
    groupbox_bg: str = "#ffffff"
    groupbox_text: str = "#000000"
    groupbox_title_text: str = "#000000"

    # Checkboxes & Radios
    checkbox_unchecked_border: str = "#d0d0d0"
    checkbox_unchecked_bg: str = "#ffffff"
    checkbox_checked_border: str = "#0078d4"
    checkbox_checked_bg: str = "#0078d4"

    radio_unchecked_border: str = "#d0d0d0"
    radio_unchecked_bg: str = "#ffffff"
    radio_checked_border: str = "#0078d4"
    radio_checked_bg: str = "#0078d4"

    # Spin Boxes & Sliders
    spinbox_bg: str = "#ffffff"
    spinbox_text: str = "#000000"
    spinbox_border: str = "#d0d0d0"
    spinbox_focus_border: str = "#0078d4"

    slider_groove_bg: str = "#f5f5f5"
    slider_groove_border: str = "#d0d0d0"
    slider_handle: str = "#0078d4"  # legacy name preserved
    slider_handle_border: str = "#0078d4"

    # Date/Time Edits
    dateedit_bg: str = "#ffffff"
    dateedit_text: str = "#000000"
    dateedit_border: str = "#d0d0d0"
    dateedit_focus_border: str = "#0078d4"

    # Labels
    label_text: str = "#000000"

    # Status Indicators
    success: str = "#52c41a"
    warning: str = "#faad14"
    error: str = "#ff4d4f"
    critical: str = "#d32f2f"  # Darker red for critical issues

    status_good_bg: str = "#d4edda"
    status_good_text: str = "#155724"
    status_good_border: str = "#c3e6cb"

    status_warning_bg: str = "#fff3cd"
    status_warning_text: str = "#856404"
    status_warning_border: str = "#ffeeba"

    status_error_bg: str = "#f8d7da"
    status_error_text: str = "#721c24"
    status_error_border: str = "#f5c6cb"

    # Loading Overlay / Misc
    loading_overlay_bg_rgba: str = "rgba(255, 255, 255, 0.8)"

    # Accent / Brand
    primary: str = "#0078d4"
    primary_hover: str = "#106ebe"
    primary_text: str = "#ffffff"

    # Interactions
    hover: str = "#e1e1e1"
    pressed: str = "#d0d0d0"

    # Viewer / 3D
    canvas_bg: str = "#f0f0f0"
    model_surface: str = "#6496c8"  # Approx (100,150,200)
    model_ambient: str = "#324b64"  # Approx (50,75,100)
    model_specular: str = "#ffffff"
    light_color: str = "#ffffff"
    edge_color: str = "#000000"

    # Stars / Ratings
    star_filled: str = "#ffd700"
    star_empty: str = "#c8c8c8"
    star_hover: str = "#ffeb64"

    # Borders & Dividers
    border: str = "#d0d0d0"
    border_light: str = "#f0f0f0"
    focus_border: str = "#2684ff"
