# Theme System - Quick Reference

## Available Themes

### PyQtDarkTheme (3 options)
```
Light  → Clean, bright theme
Dark   → Modern dark theme
Auto   → Syncs with OS dark mode
```

### Qt-Material (19 options)

**Dark Themes (9):**
```
dark_amber, dark_blue, dark_cyan, dark_lightgreen, dark_pink,
dark_purple, dark_red, dark_teal, dark_yellow
```

**Light Themes (10):**
```
light_amber, light_blue, light_cyan, light_cyan_500, light_lightgreen,
light_pink, light_purple, light_red, light_teal, light_yellow
```

## Quick API

### Apply Theme
```python
from src.gui.theme.simple_service import ThemeService

service = ThemeService.instance()

# PyQtDarkTheme
service.apply_theme("dark", "pyqtdarktheme")
service.apply_theme("light", "pyqtdarktheme")
service.apply_theme("auto", "pyqtdarktheme")

# Qt-Material (uses stored variant, default: blue)
service.apply_theme("dark", "qt-material")
service.apply_theme("light", "qt-material")
service.apply_theme("auto", "qt-material")
```

### Change Qt-Material Variant
```python
service.set_qt_material_variant("purple")
service.apply_theme("dark", "qt-material")  # Now uses dark_purple
```

### Get Available Variants
```python
dark_variants = service.get_qt_material_variants("dark")
light_variants = service.get_qt_material_variants("light")
```

### Get Current Theme
```python
theme, library = service.get_current_theme()
print(f"Current: {theme} ({library})")
```

## UI Theme Switcher

Located in toolbar:
1. **Theme Dropdown** - Light / Dark / Auto
2. **Library Dropdown** - PyQtDarkTheme / Qt-Material
3. **Variant Dropdown** - Color variants (Qt-Material only)

## Settings Persistence

Automatically saved to QSettings:
- `theme` - Current theme (light/dark/auto)
- `theme_library` - Current library
- `qt_material_variant` - Color variant (default: blue)

## Color Variants

| Variant | Best For |
|---------|----------|
| amber | Warm, energetic feel |
| blue | Professional, calm |
| cyan | Modern, tech-focused |
| lightgreen | Fresh, natural |
| pink | Creative, modern |
| purple | Premium, elegant |
| red | Alert, energetic |
| teal | Balanced, professional |
| yellow | Cheerful, attention-grabbing |

## Common Tasks

### Switch to Dark Purple
```python
service.set_qt_material_variant("purple")
service.apply_theme("dark", "qt-material")
```

### Switch to Light Blue
```python
service.set_qt_material_variant("blue")
service.apply_theme("light", "qt-material")
```

### Use Auto Dark Mode
```python
service.apply_theme("auto", "pyqtdarktheme")
```

### Get All Themes
```python
themes = service.get_available_themes()
# {
#     "pyqtdarktheme": ["light", "dark", "auto"],
#     "qt-material": {
#         "themes": ["light", "dark", "auto"],
#         "variants": {
#             "dark": [...],
#             "light": [...]
#         }
#     }
# }
```

## Files

- `src/gui/theme/simple_service.py` - Theme service (207 lines)
- `src/gui/theme/ui/simple_theme_switcher.py` - UI widget (108 lines)
- `QT_MATERIAL_THEMES_GUIDE.md` - Full documentation
- `QT_MATERIAL_THEMES_IMPLEMENTATION.md` - Implementation details

## Key Features

✅ 22 total themes (3 PyQtDarkTheme + 19 Qt-Material)
✅ Real-time theme switching
✅ Settings auto-save
✅ Auto OS dark mode detection
✅ Light theme readability optimized
✅ Professional appearance
✅ Easy to use API

## Troubleshooting

**Theme not applying?**
- Ensure qt-material is installed: `pip install qt-material`
- Check variant name is correct
- Verify theme XML file exists

**Light theme text not visible?**
- `invert_secondary=True` is auto-applied
- Check OS display settings

**Auto theme not working?**
- Install darkdetect: `pip install darkdetect`
- Check OS dark mode settings
- Fall back to manual selection

## Performance

- Theme switching: Instant
- Memory usage: Minimal
- Startup impact: None
- Settings I/O: Minimal

## Next Steps

- [ ] Try different color variants
- [ ] Test light vs dark themes
- [ ] Check auto OS detection
- [ ] Customize theme in code if needed

