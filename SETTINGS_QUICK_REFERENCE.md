# Settings Quick Reference - What's Missing

## 📊 At-a-Glance Summary

| Category | Count | Priority | User Value | Effort |
|----------|-------|----------|-----------|--------|
| Window & Display | 7 | 🔴 HIGH | Very High | Low |
| 3D Viewer (Grid/Ground) | 6 | 🔴 HIGH | Very High | Low |
| Camera & Interaction | 6 | 🔴 HIGH | Very High | Medium |
| Lighting (Advanced) | 6 | 🔴 HIGH | High | Medium |
| Logging & Debug | 4 | 🟡 MEDIUM | Medium | Low |
| Feature Flags | 3 | 🟡 MEDIUM | Medium | Low |
| Model Rendering | 4 | 🟡 MEDIUM | Medium | Medium |
| Performance Thresholds | 3 | 🟢 LOW | Low | Low |
| Dock Defaults | 3 | 🟢 LOW | Low | Low |
| **TOTAL** | **42** | - | - | - |

---

## 🎯 Top 10 Most Requested Settings

1. ✅ **Grid visibility toggle** - Users want cleaner 3D view
2. ✅ **Window size customization** - Different monitor sizes
3. ✅ **Camera mouse sensitivity** - Faster/slower rotation
4. ✅ **Ground plane visibility** - Cleaner workspace
5. ✅ **FPS limit** - Reduce CPU usage
6. ✅ **Grid color picker** - Better visibility
7. ✅ **Maximize on startup** - Fullscreen launch
8. ✅ **Lighting defaults** - Customize initial lighting
9. ✅ **Log level selector** - Reduce verbosity
10. ✅ **Auto-fit on model load** - Auto-center models

---

## 📁 Files That Need Updates

### Core Configuration
- `src/core/application_config.py` - Add new config fields
- `src/core/performance_monitor.py` - Make thresholds configurable

### UI Components
- `src/gui/preferences.py` - Add new tabs
- `src/gui/viewer_3d/camera_controller.py` - Use config values
- `src/gui/viewer_3d/vtk_scene_manager.py` - Use config values
- `src/gui/lighting_manager.py` - Use config values
- `src/gui/viewer_3d/model_renderer.py` - Use config values
- `src/gui/main_window.py` - Use config values

### Settings Persistence
- `src/gui/main_window_components/settings_manager.py` - Extend for new settings

---

## 🔧 Implementation Strategy

### Step 1: Extend ApplicationConfig
Add new fields to `src/core/application_config.py`:
```python
# Window settings
default_window_width: int = 1200
default_window_height: int = 800
maximize_on_startup: bool = False
remember_window_size: bool = True

# 3D Viewer settings
grid_visible: bool = True
grid_color: str = "#CCCCCC"
grid_size: float = 10.0
ground_visible: bool = True
ground_color: str = "#999999"

# Camera settings
mouse_sensitivity: float = 1.0
fps_limit: int = 0  # 0 = unlimited
zoom_speed: float = 1.0
auto_fit_on_load: bool = True

# Lighting settings
default_light_position: Tuple[float, float, float] = (100, 100, 100)
default_light_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
default_light_intensity: float = 0.8

# Logging settings
log_level: str = "DEBUG"
enable_file_logging: bool = True
log_retention_days: int = 30

# Feature flags
enable_hardware_acceleration: bool = True
enable_high_dpi: bool = True
enable_performance_monitoring: bool = True
```

### Step 2: Create New Preference Tabs
- `3DViewerTab` - Grid, ground, camera, lighting
- `DebugTab` - Logging, feature flags, performance

### Step 3: Update Components
- Modify viewers to read from config
- Update managers to use config values
- Persist settings to QSettings

### Step 4: Add UI Controls
- Sliders for continuous values
- Checkboxes for toggles
- Color pickers for colors
- Spinboxes for numeric values
- Dropdowns for selections

---

## 💾 Settings Persistence Pattern

```python
# Save
settings = QSettings()
settings.setValue("viewer/grid_visible", True)
settings.setValue("viewer/grid_color", "#CCCCCC")

# Load
grid_visible = settings.value("viewer/grid_visible", True, type=bool)
grid_color = settings.value("viewer/grid_color", "#CCCCCC", type=str)
```

---

## ⚠️ Special Considerations

### Restart Required
- Hardware acceleration
- High DPI support
- Log level (for file logging)

### Performance Impact
- Performance monitoring (disable to reduce overhead)
- File logging (disable for better performance)

### Validation Needed
- Window dimensions (min/max bounds)
- Color values (hex validation)
- Numeric ranges (sliders with limits)

---

## 📈 Expected User Impact

**Immediate Benefits:**
- 🎯 Better 3D viewer control
- 🎯 Customized workspace
- 🎯 Improved performance tuning

**Long-term Benefits:**
- 🎯 Reduced support requests
- 🎯 Better user satisfaction
- 🎯 Professional appearance


