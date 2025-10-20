# Implementation Plan: High-Priority Settings (1-4)

## 🎯 Objective
Integrate Window & Display, 3D Viewer Grid/Ground, Camera & Interaction, and Lighting settings into the Preferences dialog.

---

## 📋 Phase Breakdown

### **Phase 1: Extend ApplicationConfig** ✅ PLANNED
**File:** `src/core/application_config.py`

**Add these fields to ApplicationConfig dataclass:**

```python
# Window & Display Settings
default_window_width: int = 1200
default_window_height: int = 800
minimum_window_width: int = 800
minimum_window_height: int = 600
maximize_on_startup: bool = False
remember_window_size: bool = True

# 3D Viewer - Grid Settings
grid_visible: bool = True
grid_color: str = "#CCCCCC"
grid_size: float = 10.0

# 3D Viewer - Ground Plane Settings
ground_visible: bool = True
ground_color: str = "#999999"
ground_offset: float = 0.5

# Camera & Interaction Settings
mouse_sensitivity: float = 1.0
fps_limit: int = 0  # 0 = unlimited
zoom_speed: float = 1.0
pan_speed: float = 1.0
auto_fit_on_load: bool = True

# Lighting Settings
default_light_position_x: float = 100.0
default_light_position_y: float = 100.0
default_light_position_z: float = 100.0
default_light_color_r: float = 1.0
default_light_color_g: float = 1.0
default_light_color_b: float = 1.0
default_light_intensity: float = 0.8
default_light_cone_angle: float = 30.0
enable_fill_light: bool = True
fill_light_intensity: float = 0.3
```

---

### **Phase 2: Create 3D Viewer Preferences Tab** ✅ PLANNED
**File:** `src/gui/preferences.py`

**Create new class: `ViewerSettingsTab(QWidget)`**

**Sections:**
1. Grid Settings
   - Checkbox: Show grid
   - Color picker: Grid color
   - Slider: Grid size (1-100)

2. Ground Plane
   - Checkbox: Show ground plane
   - Color picker: Ground color
   - Slider: Ground offset (-10 to +10)

3. Camera & Interaction
   - Slider: Mouse sensitivity (0.5-5.0)
   - Dropdown: FPS limit (30/60/120/Unlimited)
   - Slider: Zoom speed (0.5-3.0)
   - Slider: Pan speed (0.5-3.0)
   - Checkbox: Auto-fit on load

4. Lighting (Advanced)
   - 3x Spinbox: Light position (X, Y, Z)
   - Color picker: Light color
   - Slider: Light intensity (0-1)
   - Slider: Cone angle (5-90)
   - Checkbox: Enable fill light
   - Slider: Fill light intensity (0-1)

**Methods needed:**
- `_setup_ui()` - Build UI
- `_load_settings()` - Load from config
- `save_settings()` - Save to config
- `_on_grid_color_changed()` - Color picker handler
- `_on_ground_color_changed()` - Color picker handler
- `_on_light_color_changed()` - Color picker handler

---

### **Phase 3: Expand Window & Layout Tab** ✅ PLANNED
**File:** `src/gui/preferences.py` - `WindowLayoutTab` class

**Add new section: Window Dimensions**

```python
# Window Dimensions Group
group = QGroupBox("Window Dimensions")
layout = QFormLayout()

# Width/Height spinboxes
self.window_width_spin = QSpinBox()
self.window_width_spin.setRange(800, 3840)
self.window_width_spin.setValue(1200)

self.window_height_spin = QSpinBox()
self.window_height_spin.setRange(600, 2160)
self.window_height_spin.setValue(800)

# Min Width/Height spinboxes
self.min_width_spin = QSpinBox()
self.min_width_spin.setRange(400, 1200)
self.min_width_spin.setValue(800)

self.min_height_spin = QSpinBox()
self.min_height_spin.setRange(300, 1000)
self.min_height_spin.setValue(600)

# Checkboxes
self.maximize_startup_check = QCheckBox("Maximize on startup")
self.remember_size_check = QCheckBox("Remember window size")

layout.addRow("Default width:", self.window_width_spin)
layout.addRow("Default height:", self.window_height_spin)
layout.addRow("Minimum width:", self.min_width_spin)
layout.addRow("Minimum height:", self.min_height_spin)
layout.addRow(self.maximize_startup_check)
layout.addRow(self.remember_size_check)

group.setLayout(layout)
```

---

### **Phase 4: Update VTK Scene Manager** ✅ PLANNED
**File:** `src/gui/viewer_3d/vtk_scene_manager.py`

**In `_setup_grid()` method:**
```python
# Read from config instead of hardcoding
config = ApplicationConfig.get_default()
self.grid_visible = config.grid_visible
self.grid_color = config.grid_color
self.grid_size = config.grid_size

# Apply grid color
grid_actor.GetProperty().SetColor(
    int(config.grid_color[1:3], 16) / 255.0,
    int(config.grid_color[3:5], 16) / 255.0,
    int(config.grid_color[5:7], 16) / 255.0
)
```

**In `_setup_ground()` method:**
```python
# Read from config
config = ApplicationConfig.get_default()
self.ground_visible = config.ground_visible
self.ground_color = config.ground_color
self.ground_offset = config.ground_offset
```

---

### **Phase 5: Update Camera Controller** ✅ PLANNED
**File:** `src/gui/viewer_3d/camera_controller.py`

**In `__init__()` method:**
```python
config = ApplicationConfig.get_default()
self.mouse_sensitivity = config.mouse_sensitivity
self.zoom_speed = config.zoom_speed
self.pan_speed = config.pan_speed
self.fps_limit = config.fps_limit
self.auto_fit_on_load = config.auto_fit_on_load
```

**In mouse event handlers:**
```python
# Apply mouse sensitivity multiplier
delta = event.delta() * self.mouse_sensitivity
```

---

### **Phase 6: Update Lighting Manager** ✅ PLANNED
**File:** `src/gui/lighting_manager.py`

**In `__init__()` method:**
```python
config = ApplicationConfig.get_default()

# Set default light position
self.light_position = (
    config.default_light_position_x,
    config.default_light_position_y,
    config.default_light_position_z
)

# Set default light color
self.light_color = (
    config.default_light_color_r,
    config.default_light_color_g,
    config.default_light_color_b
)

# Set default intensity
self.light_intensity = config.default_light_intensity
```

---

### **Phase 7: Update Main Window** ✅ PLANNED
**File:** `src/gui/main_window.py`

**In `__init__()` method after window creation:**
```python
config = ApplicationConfig.get_default()

# Apply window dimensions
self.resize(config.default_window_width, config.default_window_height)
self.setMinimumWidth(config.minimum_window_width)
self.setMinimumHeight(config.minimum_window_height)

# Apply maximize on startup
if config.maximize_on_startup:
    self.showMaximized()
else:
    self.show()
```

---

### **Phase 8: Settings Persistence** ✅ PLANNED
**File:** `src/gui/main_window_components/settings_manager.py`

**Add new methods:**
```python
def save_viewer_settings(self) -> None:
    """Save 3D viewer settings."""
    settings = QSettings()
    config = ApplicationConfig.get_default()
    settings.setValue("viewer/grid_visible", config.grid_visible)
    settings.setValue("viewer/grid_color", config.grid_color)
    settings.setValue("viewer/grid_size", config.grid_size)
    # ... more settings

def load_viewer_settings(self) -> None:
    """Load 3D viewer settings."""
    settings = QSettings()
    config = ApplicationConfig.get_default()
    config.grid_visible = settings.value("viewer/grid_visible", True, type=bool)
    config.grid_color = settings.value("viewer/grid_color", "#CCCCCC", type=str)
    # ... more settings
```

---

### **Phase 9: Testing & Validation** ✅ PLANNED

**Test Cases:**
1. ✅ Window dimensions persist across restarts
2. ✅ Grid visibility toggle works
3. ✅ Grid color changes apply immediately
4. ✅ Camera sensitivity affects rotation speed
5. ✅ FPS limit reduces CPU usage
6. ✅ Lighting settings apply to new models
7. ✅ All color pickers validate hex values
8. ✅ All sliders respect min/max bounds
9. ✅ Settings save/load without errors
10. ✅ Application starts with custom settings

---

## 📊 Implementation Order

```
Phase 1: ApplicationConfig (foundation)
    ↓
Phase 2: 3D Viewer Tab (UI)
    ↓
Phase 3: Window & Layout Tab (UI)
    ↓
Phase 4-6: Component Updates (logic)
    ↓
Phase 7: Main Window Integration (startup)
    ↓
Phase 8: Settings Persistence (storage)
    ↓
Phase 9: Testing & Validation (QA)
```

---

## ⏱️ Estimated Timeline

- Phase 1: 30 min
- Phase 2: 1.5 hours
- Phase 3: 45 min
- Phase 4-6: 1.5 hours
- Phase 7: 30 min
- Phase 8: 45 min
- Phase 9: 1 hour

**Total: ~6.5 hours**


