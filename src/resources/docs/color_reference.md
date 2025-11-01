# Theme Color Reference

This document lists all ThemeManager color variables (148 total) and their default values derived from [ThemeDefaults](src/gui/theme.py:117). Values are used via CSS template placeholders like {{variable_name}} and resolved by ThemeManager.

## Theme Presets

The system includes three built-in theme presets accessible via View → Theme Manager...:

### Modern (Default)
Professional blue color scheme inspired by Microsoft Fluent Design:
- Primary: #0078d4 (Microsoft blue)
- Light backgrounds with subtle grays
- High contrast for readability
- Full 148-variable cohesive palette auto-derived

### High Contrast
Accessibility-focused theme for users with visual impairments:
- Black backgrounds (#000000) with white text (#ffffff)
- Yellow primary (#ffff00) for maximum visibility
- All controls have 2px white borders
- WCAG AAA contrast compliance

### Custom
User-configurable theme with automatic dark/light mode calculation:
- Select seed primary color
- Choose mode: Auto (detects from primary), Light, or Dark
- System derives complete cohesive palette from seed color
- All 148 variables generated harmoniously

## Usage Overview

### In CSS Files
Use placeholders, e.g. `color: {{text}};` - processed by [`ThemeManager.process_css_file()`](src/gui/theme.py:752)

### In Python - File-based Stylesheet
```python
ThemeManager.instance().register_widget(widget, css_path="src/resources/styles/main_window.css")
ThemeManager.instance().apply_stylesheet(widget)
```

### In Python - Inline CSS Template
```python
css_text = "QPushButton { background: {{primary}}; color: {{primary_text}}; }"
ThemeManager.instance().register_widget(widget, css_text=css_text)
ThemeManager.instance().apply_stylesheet(widget)
```

### Applying Presets Programmatically
```python
from gui.theme import apply_theme_preset

# Apply Modern preset
apply_theme_preset("modern")

# Apply High Contrast preset
apply_theme_preset("high_contrast")

# Apply Custom preset with dark mode
apply_theme_preset("custom", custom_mode="dark", base_primary="#ff6b35")
```

## Window & UI Elements (11 variables)
| Variable | Default | Usage |
|---|---|---|
| window_bg | #ffffff | Main window background |
| text | #000000 | Primary text color |
| text_inverse | #ffffff | Text on dark/high-contrast surfaces |
| text_muted | #666666 | Secondary/placeholder text |
| disabled_text | #9aa0a6 | Disabled control text |
| menubar_bg | #f5f5f5 | Menu bar background |
| menubar_text | #000000 | Menu bar text |
| menubar_border | #d0d0d0 | Menu bar bottom border |
| menubar_item_hover_bg | #0078d4 | Menu item hover background |
| menubar_item_hover_text | #ffffff | Menu item hover text |
| menubar_item_pressed_bg | #106ebe | Menu item pressed background |

## Surfaces (5)
| Variable | Default | Usage |
|---|---|---|
| surface | #f5f5f5 | Generic surface/panel/toolbar |
| surface_alt | #ffffff | Alternate surface (cards) |
| card_bg | #ffffff | Card/inner panel background |
| surface_grad_start | #fafafa | Light gradient start |
| surface_grad_end | #f2f2f2 | Light gradient end |

## Toolbars (11)
| Variable | Default | Usage |
|---|---|---|
| toolbar_bg | #f5f5f5 | QToolBar background |
| toolbar_border | #d0d0d0 | QToolBar border |
| toolbar_handle_bg | #d0d0d0 | Toolbar handle color |
| toolbutton_bg | transparent | QToolButton idle background |
| toolbutton_border | transparent | QToolButton idle border |
| toolbutton_hover_bg | #e1e1e1 | QToolButton hover background |
| toolbutton_hover_border | #0078d4 | QToolButton hover border |
| toolbutton_pressed_bg | #d0d0d0 | QToolButton pressed background |
| toolbutton_checked_bg | #0078d4 | QToolButton checked background |
| toolbutton_checked_border | #0078d4 | QToolButton checked border |
| toolbutton_checked_text | #ffffff | QToolButton checked text |

## Status Bar (3)
| Variable | Default | Usage |
|---|---|---|
| statusbar_bg | #f5f5f5 | Status bar background |
| statusbar_text | #000000 | Status bar text |
| statusbar_border | #d0d0d0 | Status bar top border |

## Dock Widgets (5)
| Variable | Default | Usage |
|---|---|---|
| dock_bg | #ffffff | Dock inner background |
| dock_text | #000000 | Dock text color |
| dock_border | #d0d0d0 | Dock border |
| dock_title_bg | #f5f5f5 | Dock title bar background |
| dock_title_border | #d0d0d0 | Dock title bottom border |

## Buttons (16)
| Variable | Default | Usage |
|---|---|---|
| button_bg | #f5f5f5 | QPushButton background |
| button_text | #000000 | QPushButton text |
| button_border | #d0d0d0 | QPushButton border |
| button_hover_bg | #e1e1e1 | Hover background |
| button_hover_border | #0078d4 | Hover border |
| button_pressed_bg | #d0d0d0 | Pressed background |
| button_checked_bg | #0078d4 | Checked background |
| button_checked_text | #ffffff | Checked text color |
| button_checked_border | #0078d4 | Checked border |
| button_default_bg | #0078d4 | Default button background |
| button_default_text | #ffffff | Default button text |
| button_default_border | #0078d4 | Default button border |
| button_default_hover_bg | #106ebe | Default button hover |
| button_disabled_bg | #f0f0f0 | Disabled background |
| button_disabled_text | #a0a0a0 | Disabled text |
| button_disabled_border | #e0e0e0 | Disabled border |

## Inputs (6) & Selection (2)
| Variable | Default | Usage |
|---|---|---|
| input_bg | #ffffff | Input background |
| input_text | #000000 | Input text color |
| input_border | #d0d0d0 | Input border |
| input_focus_border | #0078d4 | Focused input border |
| input_disabled_bg | #f5f5f5 | Disabled input background |
| input_disabled_text | #a0a0a0 | Disabled input text |
| selection_bg | #0078d4 | Selection background |
| selection_text | #ffffff | Selection text |

## Combo Box (5)
| Variable | Default | Usage |
|---|---|---|
| combobox_bg | #ffffff | Combo box background |
| combobox_text | #000000 | Combo box text |
| combobox_border | #d0d0d0 | Combo box border |
| combobox_focus_border | #0078d4 | Focus border |
| combobox_arrow_color | #666666 | Arrow indicator color |

## Progress Bar (8)
| Variable | Default | Usage |
|---|---|---|
| progress_bg | #ffffff | Bar background |
| progress_text | #000000 | Bar text color |
| progress_border | #d0d0d0 | Bar border |
| progress_chunk | #0078d4 | Progress chunk color |
| progress_disabled_border | #e0e0e0 | Disabled border |
| progress_disabled_bg | #f5f5f5 | Disabled background |
| progress_disabled_text | #a0a0a0 | Disabled text |
| progress_disabled_chunk | #d0d0d0 | Disabled chunk |

## Tabs (8)
| Variable | Default | Usage |
|---|---|---|
| tab_pane_border | #d0d0d0 | Tab widget border |
| tab_pane_bg | #ffffff | Pane background |
| tab_bg | #f5f5f5 | Tab background |
| tab_text | #000000 | Tab text |
| tab_border | #d0d0d0 | Tab border |
| tab_selected_bg | #ffffff | Selected tab background |
| tab_selected_border | #0078d4 | Selected indicator border |
| tab_hover_bg | #e1e1e1 | Tab hover background |

## Tables & Lists (8)
| Variable | Default | Usage |
|---|---|---|
| table_bg | #ffffff | Table/list background |
| table_text | #000000 | Table/list text |
| table_border | #d0d0d0 | Table border |
| table_gridline | #e0e0e0 | Grid line color |
| table_alternate_row_bg | #f5f5f5 | Alternate row |
| header_bg | #f5f5f5 | Header section background |
| header_text | #000000 | Header text |
| header_border | #d0d0d0 | Header border |

## Scrollbars (4)
| Variable | Default | Usage |
|---|---|---|
| scrollbar_bg | #f5f5f5 | Scrollbar track |
| scrollbar_border | #d0d0d0 | Scrollbar border |
| scrollbar_handle_bg | #d0d0d0 | Thumb color |
| scrollbar_handle_hover_bg | #a0a0a0 | Thumb hover color |

## Splitters (1)
| Variable | Default | Usage |
|---|---|---|
| splitter_handle_bg | #d0d0d0 | Splitter handle |

## Group Boxes (4)
| Variable | Default | Usage |
|---|---|---|
| groupbox_border | #d0d0d0 | Group box border |
| groupbox_bg | #ffffff | Group box background |
| groupbox_text | #000000 | Group box text |
| groupbox_title_text | #000000 | Group box title text |

## Checkboxes & Radios (8)
| Variable | Default | Usage |
|---|---|---|
| checkbox_unchecked_border | #d0d0d0 | Checkbox border (unchecked) |
| checkbox_unchecked_bg | #ffffff | Checkbox background (unchecked) |
| checkbox_checked_border | #0078d4 | Checkbox border (checked) |
| checkbox_checked_bg | #0078d4 | Checkbox background (checked) |
| radio_unchecked_border | #d0d0d0 | Radio border (unchecked) |
| radio_unchecked_bg | #ffffff | Radio background (unchecked) |
| radio_checked_border | #0078d4 | Radio border (checked) |
| radio_checked_bg | #0078d4 | Radio background (checked) |

## Spin Boxes & Sliders (8)
| Variable | Default | Usage |
|---|---|---|
| spinbox_bg | #ffffff | SpinBox background |
| spinbox_text | #000000 | SpinBox text |
| spinbox_border | #d0d0d0 | SpinBox border |
| spinbox_focus_border | #0078d4 | SpinBox focused border |
| slider_groove_bg | #f5f5f5 | Slider groove background |
| slider_groove_border | #d0d0d0 | Slider groove border |
| slider_handle | #0078d4 | Slider handle background |
| slider_handle_border | #0078d4 | Slider handle border |

## Date/Time Edits (4)
| Variable | Default | Usage |
|---|---|---|
| dateedit_bg | #ffffff | Date/Datetime/Time background |
| dateedit_text | #000000 | Text color |
| dateedit_border | #d0d0d0 | Border |
| dateedit_focus_border | #0078d4 | Focus border |

## Labels (1)
| Variable | Default | Usage |
|---|---|---|
| label_text | #000000 | QLabel text color |

## Status Indicators (13)
| Variable | Default | Usage |
|---|---|---|
| success | #52c41a | Generic success accent |
| warning | #faad14 | Generic warning accent |
| error | #ff4d4f | Generic error accent |
| critical | #d32f2f | Critical error accent (darker red) |
| status_good_bg | #d4edda | "Good" badge background |
| status_good_text | #155724 | "Good" badge text |
| status_good_border | #c3e6cb | "Good" badge border |
| status_warning_bg | #fff3cd | "Warning" badge background |
| status_warning_text | #856404 | "Warning" badge text |
| status_warning_border | #ffeeba | "Warning" badge border |
| status_error_bg | #f8d7da | "Error" badge background |
| status_error_text | #721c24 | "Error" badge text |
| status_error_border | #f5c6cb | "Error" badge border |

## Loading Overlay / Misc (1)
| Variable | Default | Usage |
|---|---|---|
| loading_overlay_bg_rgba | rgba(255, 255, 255, 0.8) | Overlay background |

## Accent / Brand (3)
| Variable | Default | Usage |
|---|---|---|
| primary | #0078d4 | Brand/primary accent |
| primary_hover | #106ebe | Primary hover state |
| primary_text | #ffffff | Text on primary background |

## Interactions (2)
| Variable | Default | Usage |
|---|---|---|
| hover | #e1e1e1 | Generic hover background |
| pressed | #d0d0d0 | Generic pressed background |

## Viewer / 3D (6)
| Variable | Default | Usage |
|---|---|---|
| canvas_bg | #f0f0f0 | Viewer canvas background |
| model_surface | #6496c8 | Model surface color |
| model_ambient | #324b64 | Ambient shading color |
| model_specular | #ffffff | Specular highlight |
| light_color | #ffffff | Light color |
| edge_color | #000000 | Outlines/edges |

## Stars / Ratings (3)
| Variable | Default | Usage |
|---|---|---|
| star_filled | #ffd700 | Filled star color |
| star_empty | #c8c8c8 | Empty star color |
| star_hover | #ffeb64 | Hover star color |

## Borders & Dividers (3)
| Variable | Default | Usage |
|---|---|---|
| border | #d0d0d0 | Generic border |
| border_light | #f0f0f0 | Light border/divider |
| focus_border | #2684ff | Focus ring/outline |

---

## Fallback System
- Undefined variables resolve to hot pink FALLBACK_COLOR: `#E31C79`
- ThemeManager logs WARNING event with context when fallback occurs
- See [`ThemeManager.get_color()`](src/gui/theme.py:656) and [`FALLBACK_COLOR`](src/gui/theme.py:49)

## Template Processing
- Placeholders replaced by [`ThemeManager.process_css_template()`](src/gui/theme.py:727) and [`process_css_file()`](src/gui/theme.py:752)
- CSS caching by file mtime and theme version for performance
- Widgets register via [`ThemeManager.register_widget()`](src/gui/theme.py:785)
- Apply with [`ThemeManager.apply_stylesheet()`](src/gui/theme.py:798) or [`apply_to_registered()`](src/gui/theme.py:820)

## Preset System Architecture
- **Built-in presets** (Modern, High Contrast): Defined in [`PRESETS`](src/gui/theme.py:597)
- **Custom preset**: Uses [`derive_mode_palette()`](src/gui/theme.py:364) for full palette generation
- **Color derivation**:
  - Luminance calculation: [`_relative_luminance_from_hex()`](src/gui/theme.py:332)
  - Text contrast selection: [`_choose_text_for_bg()`](src/gui/theme.py:343)
  - Color mixing utilities: [`_mix_hex()`](src/gui/theme.py:347), [`_lighten()`](src/gui/theme.py:356), [`_darken()`](src/gui/theme.py:360)
- **Application**: [`ThemeManager.apply_preset()`](src/gui/theme.py:695)

## Integration Examples
- **Main window**: Registers file-based stylesheet in [`MainWindow._init_ui()`](src/gui/main_window.py:74), re-applies on theme change in [`MainWindow._on_theme_applied()`](src/gui/main_window.py:1313)
- **Metadata Editor**: Inline template CSS in [`MetadataEditorWidget._apply_styling()`](src/gui/metadata_editor.py:382)
- **Model Library**: Inline template CSS in [`ModelLibraryWidget._apply_styling()`](src/gui/model_library.py:383)
- **VTK Viewer**: Theme-aware via [`Viewer3DWidget.apply_theme()`](src/gui/viewer_widget_vtk.py:910)

## Theme Persistence
- **Save to AppData**: [`ThemeManager.save_to_settings()`](src/gui/theme.py:847)
- **Load from AppData**: [`ThemeManager.load_from_settings()`](src/gui/theme.py:856)
- **Export JSON**: [`ThemeManager.export_theme()`](src/gui/theme.py:873)
- **Import JSON**: [`ThemeManager.import_theme()`](src/gui/theme.py:881)

## Debugging Stylesheet Loading
All stylesheet applications log DEBUG-level events with:
- Event: `"stylesheet_applied"`
- Widget identifier
- CSS path (if file-based)
- CSS text length (if inline)

Check logs to verify each widget's stylesheet is loading correctly.