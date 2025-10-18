# Theming System Implementation Guide

## 📋 Step-by-Step Implementation

### **Phase 1: Foundation Setup**

#### Step 1.1: Create Directory Structure
```bash
mkdir -p src/gui/theme/ui
mkdir -p src/gui/theme/materials
touch src/gui/theme/__init__.py
touch src/gui/theme/service.py
touch src/gui/theme/presets.py
touch src/gui/theme/detector.py
touch src/gui/theme/persistence.py
touch src/gui/theme/ui/__init__.py
touch src/gui/theme/ui/theme_switcher.py
touch src/gui/theme/ui/theme_dialog.py
touch src/gui/theme/ui/theme_preview.py
```

#### Step 1.2: Move Existing Code
```bash
# Move existing theme.py to theme/manager.py
mv src/gui/theme.py src/gui/theme/manager.py

# Update imports in theme/__init__.py to expose public API
```

#### Step 1.3: Create ThemeService
```python
# src/gui/theme/service.py
class ThemeService:
    """Unified API for all theme operations."""
    _instance = None
    
    def __init__(self):
        self.manager = ThemeManager.instance()
        self.presets = ThemePresetManager()
        self.detector = SystemThemeDetector()
        self._auto_save_enabled = True
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def apply_preset(self, name: str) -> None:
        """Apply a theme preset."""
        self.manager.apply_preset(name)
        if self._auto_save_enabled:
            self.save_theme()
    
    def set_color(self, name: str, value: str) -> None:
        """Set a single color."""
        self.manager.set_colors({name: value})
        if self._auto_save_enabled:
            self.save_theme()
    
    def save_theme(self) -> None:
        """Save current theme to AppData."""
        self.manager.save_to_settings()
    
    def enable_system_detection(self) -> None:
        """Enable automatic system theme detection."""
        self.detector.enable()
```

---

### **Phase 2: Presets & Detection**

#### Step 2.1: Create Preset Definitions
```python
# src/gui/theme/presets.py
PRESET_LIGHT = {
    "window_bg": "#ffffff",
    "text": "#000000",
    # ... all colors for light theme
}

PRESET_DARK = {
    "window_bg": "#1e1e1e",
    "text": "#ffffff",
    # ... all colors for dark theme
}

PRESET_HIGH_CONTRAST = {
    "window_bg": "#000000",
    "text": "#ffffff",
    # ... high contrast colors
}

# Add Solarized, Material Design, etc.
```

#### Step 2.2: Create System Theme Detector
```python
# src/gui/theme/detector.py
class SystemThemeDetector:
    """Detect OS dark mode and apply appropriate theme."""
    
    def __init__(self):
        self._enabled = False
        self._current_mode = self._detect_system_theme()
    
    def _detect_system_theme(self) -> str:
        """Detect if OS is in dark mode."""
        # Windows: Check registry
        # macOS: Check defaults
        # Linux: Check environment
        pass
    
    def enable(self) -> None:
        """Enable system theme detection."""
        self._enabled = True
        self._apply_system_theme()
    
    def _apply_system_theme(self) -> None:
        """Apply theme based on system preference."""
        mode = self._detect_system_theme()
        theme = "dark" if mode == "dark" else "light"
        ThemeService.instance().apply_preset(theme)
```

#### Step 2.3: Create Persistence Layer
```python
# src/gui/theme/persistence.py
class ThemePersistence:
    """Handle theme save/load/import/export."""
    
    def save_theme(self, colors: Dict[str, str]) -> None:
        """Save theme to AppData."""
        pass
    
    def load_theme(self) -> Dict[str, str]:
        """Load theme from AppData."""
        pass
    
    def export_theme(self, path: Path) -> None:
        """Export theme to JSON file."""
        pass
    
    def import_theme(self, path: Path) -> Dict[str, str]:
        """Import theme from JSON file."""
        pass
```

---

### **Phase 3: UI Components**

#### Step 3.1: Create Theme Switcher Widget
```python
# src/gui/theme/ui/theme_switcher.py
class ThemeSwitcher(QComboBox):
    """Quick theme selector for toolbar."""
    
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._populate_presets()
    
    def _populate_presets(self):
        """Load available presets into dropdown."""
        service = ThemeService.instance()
        for preset in service.get_available_presets():
            self.addItem(preset)
    
    def _on_theme_selected(self, index: int):
        """Apply selected theme."""
        theme_name = self.itemText(index)
        ThemeService.instance().apply_preset(theme_name)
        self.theme_changed.emit(theme_name)
```

#### Step 3.2: Create Consolidated Theme Dialog
```python
# src/gui/theme/ui/theme_dialog.py
class ThemeDialog(QDialog):
    """Consolidated theme editor (replaces both old UIs)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ThemeService.instance()
        self._setup_ui()
    
    def _setup_ui(self):
        """Create UI with:
        - Preset selector
        - Color editor (left)
        - Live preview (right)
        - Import/Export buttons
        - System theme detection toggle
        """
        pass
```

#### Step 3.3: Create Theme Preview
```python
# src/gui/theme/ui/theme_preview.py
class ThemePreview(QWidget):
    """Live preview of theme changes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_preview_widgets()
    
    def refresh(self):
        """Update preview with current theme."""
        pass
```

---

### **Phase 4: Integration**

#### Step 4.1: Update Main Window
```python
# In src/gui/main_window.py
from src.gui.theme import ThemeService

# Add theme switcher to toolbar
self.theme_switcher = ThemeSwitcher()
self.main_toolbar.addWidget(self.theme_switcher)

# Connect theme changes
self.theme_switcher.theme_changed.connect(self._on_theme_changed)
```

#### Step 4.2: Update Preferences
```python
# In src/gui/preferences.py
# Remove ThemingTab
# Add button to open ThemeDialog instead
self.btn_theme_manager = QPushButton("Theme Manager...")
self.btn_theme_manager.clicked.connect(self._open_theme_dialog)
```

#### Step 4.3: Remove Old Code
```bash
# Delete old theme manager widget
rm src/gui/theme_manager_widget.py

# Remove theming from preferences
# (keep preferences.py but remove ThemingTab)
```

---

### **Phase 5: Optional - qt-material Integration**

#### Step 5.1: Install qt-material
```bash
pip install qt-material
```

#### Step 5.2: Create Material Themes
```python
# src/gui/theme/materials/material_themes.py
class MaterialThemeProvider:
    """Provide Material Design themes via qt-material."""
    
    def get_material_light(self) -> Dict[str, str]:
        """Get Material Design light theme."""
        pass
    
    def get_material_dark(self) -> Dict[str, str]:
        """Get Material Design dark theme."""
        pass
```

---

## 🧪 Testing Checklist

- [ ] Theme switching works from toolbar dropdown
- [ ] All presets apply correctly
- [ ] System theme detection works
- [ ] Auto-save persists themes
- [ ] Theme dialog opens and closes properly
- [ ] Color picker works
- [ ] Import/export functionality works
- [ ] Live preview updates in real-time
- [ ] Old preferences theming tab removed
- [ ] Old theme manager widget removed
- [ ] All imports updated
- [ ] No broken references
- [ ] Performance is acceptable
- [ ] All widgets apply theme correctly

---

## 📝 Migration Guide

### For Users
1. Open Preferences → Theme Manager (new consolidated dialog)
2. Select preset from dropdown
3. Customize colors if desired
4. Changes auto-save
5. Use toolbar dropdown for quick switching

### For Developers
```python
# Old way (deprecated)
from src.gui.theme import ThemeManager
tm = ThemeManager.instance()
tm.apply_preset("dark")

# New way (recommended)
from src.gui.theme import ThemeService
service = ThemeService.instance()
service.apply_preset("dark")
```

---

## 🎯 Success Criteria

✅ Single unified theme UI
✅ Quick theme switcher in toolbar
✅ 8+ theme presets available
✅ System theme detection working
✅ Auto-save enabled
✅ Code is modular and maintainable
✅ All tests passing
✅ No performance degradation
✅ User experience improved

