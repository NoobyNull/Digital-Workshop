"""
Helper functions for theme manager widget.

Provides utilities for color contrast calculation, label formatting, and category mapping.
"""

from typing import Dict, List

from src.gui.theme import ThemeManager, COLORS, hex_to_rgb


def contrasting_text_color(hex_color: str) -> str:
    """
    Choose black/white text for best contrast against a background color.
    Falls back to default theme text if parsing fails.
    """
    try:
        r, g, b = hex_to_rgb(hex_color)
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        return "#000000" if brightness >= 128 else "#ffffff"
    except Exception:
        return COLORS.text


def pretty_label(var_name: str) -> str:
    """Humanize variable name: button_default_bg -> Button Default Bg"""
    return " ".join([part.capitalize() for part in var_name.split("_")])


def build_category_map() -> Dict[str, List[str]]:
    """
    Build category grouping for variables based on prefix heuristics.
    Any unknown keys fall into 'Other'.
    """
    tm = ThemeManager.instance()
    keys = sorted(tm.colors.keys())

    # Category definitions by prefixes
    categories: Dict[str, List[str]] = {
        "Window & UI": [],
        "Surfaces": [],
        "Toolbars": [],
        "Status Bar": [],
        "Dock Widgets": [],
        "Buttons": [],
        "Inputs": [],
        "Combobox": [],
        "Progress Bar": [],
        "Tabs": [],
        "Tables & Lists": [],
        "Scrollbars": [],
        "Splitters": [],
        "Group Boxes": [],
        "Checkboxes & Radios": [],
        "Spinbox & Slider": [],
        "Date/Time Edits": [],
        "Labels": [],
        "Status Indicators": [],
        "Accent / Brand": [],
        "Interactions": [],
        "Viewer / 3D": [],
        "Stars / Ratings": [],
        "Borders & Dividers": [],
        "Misc": [],
        "Other": [],
    }

    def add(cat: str, name: str) -> bool:
        """TODO: Add docstring."""
        categories[cat].append(name)
        return True

    for k in keys:
        if (
            k.startswith("window_")
            or k.startswith("text_")
            or k.startswith("disabled_")
            or k.startswith("menubar_")
        ):
            add("Window & UI", k)
        elif k.startswith("surface_"):
            add("Surfaces", k)
        elif k.startswith("toolbar_"):
            add("Toolbars", k)
        elif k.startswith("statusbar_"):
            add("Status Bar", k)
        elif k.startswith("dock_"):
            add("Dock Widgets", k)
        elif k.startswith("button_"):
            add("Buttons", k)
        elif k.startswith("input_") or k.startswith("selection_"):
            add("Inputs", k)
        elif k.startswith("combobox_"):
            add("Combobox", k)
        elif k.startswith("progress_"):
            add("Progress Bar", k)
        elif k.startswith("tab_"):
            add("Tabs", k)
        elif k.startswith("table_") or k.startswith("header_") or k.startswith("list_"):
            add("Tables & Lists", k)
        elif k.startswith("scrollbar_"):
            add("Scrollbars", k)
        elif k.startswith("splitter_"):
            add("Splitters", k)
        elif k.startswith("groupbox_"):
            add("Group Boxes", k)
        elif k.startswith("checkbox_") or k.startswith("radio_"):
            add("Checkboxes & Radios", k)
        elif k.startswith("spinbox_") or k.startswith("slider_"):
            add("Spinbox & Slider", k)
        elif k.startswith("dateedit_") or k.startswith("timeedit_"):
            add("Date/Time Edits", k)
        elif k.startswith("label_"):
            add("Labels", k)
        elif k.startswith("status_"):
            add("Status Indicators", k)
        elif k.startswith("primary") or k.startswith("accent_") or k.startswith("brand_"):
            add("Accent / Brand", k)
        elif k.startswith("interaction_"):
            add("Interactions", k)
        elif k.startswith("viewer_") or k.startswith("vtk_"):
            add("Viewer / 3D", k)
        elif k.startswith("star_") or k.startswith("rating_"):
            add("Stars / Ratings", k)
        elif k.startswith("border_") or k.startswith("divider_"):
            add("Borders & Dividers", k)
        elif k.startswith("misc_"):
            add("Misc", k)
        else:
            add("Other", k)

    return categories
