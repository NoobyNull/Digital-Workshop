# Qt-Material Themes Integration Guide

## Overview

The application now supports all 19 professional Material Design themes from the `qt-material` library, in addition to the pyqtdarktheme options.

## Available Themes

### PyQtDarkTheme (3 options)
- **Light** - Clean, bright theme
- **Dark** - Modern dark theme
- **Auto** - Syncs with OS dark mode preference

### Qt-Material Dark Themes (9 color variants)
1. **dark_amber** - Warm amber accent
2. **dark_blue** - Cool blue accent (default)
3. **dark_cyan** - Cyan accent
4. **dark_lightgreen** - Light green accent
5. **dark_pink** - Pink accent
6. **dark_purple** - Purple accent
7. **dark_red** - Red accent
8. **dark_teal** - Teal accent
9. **dark_yellow** - Yellow accent

### Qt-Material Light Themes (10 color variants)
1. **light_amber** - Warm amber accent
2. **light_blue** - Cool blue accent (default)
3. **light_cyan** - Cyan accent
4. **light_cyan_500** - Cyan 500 variant
5. **light_lightgreen** - Light green accent
6. **light_pink** - Pink accent
7. **light_purple** - Purple accent
8. **light_red** - Red accent
9. **light_teal** - Teal accent
10. **light_yellow** - Yellow accent

## Usage

### Programmatic Theme Switching

```python
from src.gui.theme.simple_service import ThemeService

service = ThemeService.instance()

# Apply pyqtdarktheme
service.apply_theme("dark", "pyqtdarktheme")
service.apply_theme("light", "pyqtdarktheme")
service.apply_theme("auto", "pyqtdarktheme")

# Apply qt-material with specific variant
service.apply_theme("dark", "qt-material")  # Uses stored variant (default: blue)
service.apply_theme("light", "qt-material")

# Change qt-material color variant
service.set_qt_material_variant("purple")
service.apply_theme("dark", "qt-material")  # Now uses dark_purple
```

### Get Available Themes

```python
service = ThemeService.instance()

# Get all available themes
themes = service.get_available_themes()
# Returns:
# {
#     "pyqtdarktheme": ["light", "dark", "auto"],
#     "qt-material": {
#         "themes": ["light", "dark", "auto"],
#         "variants": {
#             "dark": ["dark_amber", "dark_blue", ...],
#             "light": ["light_amber", "light_blue", ...]
#         }
#     }
# }

# Get variants for a specific theme type
dark_variants = service.get_qt_material_variants("dark")
light_variants = service.get_qt_material_variants("light")
```

### Get Current Theme

```python
theme, library = service.get_current_theme()
print(f"Current: {theme} ({library})")
# Output: Current: dark (pyqtdarktheme)
```

## UI Theme Switcher

The toolbar includes a theme switcher with:
- **Theme Dropdown**: Light / Dark / Auto
- **Library Dropdown**: PyQtDarkTheme / Qt-Material
- **Variant Dropdown**: Color variants (only visible when Qt-Material is selected)

### How It Works

1. Select a library (PyQtDarkTheme or Qt-Material)
2. Select a theme (Light, Dark, or Auto)
3. If Qt-Material is selected, choose a color variant
4. Theme applies immediately and is saved to settings

## Settings Persistence

Theme preferences are automatically saved to QSettings:
- `theme` - Current theme (light/dark/auto)
- `theme_library` - Current library (pyqtdarktheme/qt-material)
- `qt_material_variant` - Current qt-material color variant (default: blue)

Settings are restored on application startup.

## Implementation Details

### ThemeService Class

Located in `src/gui/theme/simple_service.py`

**Key Methods:**
- `apply_theme(theme, library)` - Apply a theme
- `get_available_themes()` - Get all available themes
- `get_qt_material_variants(theme_type)` - Get color variants
- `set_qt_material_variant(variant)` - Set color variant
- `get_current_theme()` - Get current theme info

### SimpleThemeSwitcher Widget

Located in `src/gui/theme/ui/simple_theme_switcher.py`

**Features:**
- Three dropdowns for easy theme selection
- Real-time theme switching
- Variant selector for qt-material
- Automatic settings persistence

## Color Variants Explained

Each qt-material theme uses a primary accent color:

| Variant | Color | Use Case |
|---------|-------|----------|
| amber | Warm orange | Warm, energetic feel |
| blue | Cool blue | Professional, calm |
| cyan | Bright cyan | Modern, tech-focused |
| lightgreen | Light green | Fresh, natural |
| pink | Vibrant pink | Creative, modern |
| purple | Royal purple | Premium, elegant |
| red | Bright red | Alert, energetic |
| teal | Teal | Balanced, professional |
| yellow | Bright yellow | Cheerful, attention-grabbing |

## Light Theme Considerations

When using light themes, the `invert_secondary=True` parameter is automatically applied to ensure:
- Proper text contrast
- Icon visibility
- Overall readability

## Auto Theme Detection

When "Auto" is selected:
1. Detects OS dark mode preference (requires `darkdetect` package)
2. Applies dark theme if OS is in dark mode
3. Applies light theme if OS is in light mode
4. Falls back to dark theme if detection fails

## Customization

### Adding Custom Themes

To add custom qt-material themes:

1. Create a custom theme XML file
2. Place it in the qt-material themes directory
3. Update `QT_MATERIAL_DARK_THEMES` or `QT_MATERIAL_LIGHT_THEMES` lists
4. Restart the application

### Modifying Theme Colors

Qt-material themes can be customized by:
1. Exporting the theme from the qt-material example app
2. Editing the XML file
3. Using the custom theme in your application

See: https://qt-material.readthedocs.io/en/latest/

## Troubleshooting

### Theme Not Applying
- Ensure qt-material is installed: `pip install qt-material`
- Check that the variant name is correct
- Verify the theme XML file exists

### Light Theme Text Not Visible
- Ensure `invert_secondary=True` is being used
- This is automatically handled by the service

### Auto Theme Not Working
- Install darkdetect: `pip install darkdetect`
- Check OS dark mode settings
- Fallback to manual theme selection if needed

## Performance

- Theme switching is instant
- No noticeable performance impact
- Settings are cached in memory
- Minimal disk I/O for persistence

## Future Enhancements

- [ ] Theme preview before applying
- [ ] Custom color picker for variants
- [ ] Theme export/import functionality
- [ ] Per-widget theme customization
- [ ] Theme scheduling (e.g., dark at night)

