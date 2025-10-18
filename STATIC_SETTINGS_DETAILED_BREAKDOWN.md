# Detailed Static Settings Breakdown

---

## 1️⃣ WINDOW & UI DIMENSIONS

### Current Hardcoded Values
```python
# src/core/application_config.py
default_window_width: int = 1200
default_window_height: int = 800
minimum_window_width: int = 800
minimum_window_height: int = 600

# src/gui/preferences.py
setMinimumWidth(560)  # Preferences dialog
```

### Should Be User-Controllable
- ✅ Default window width/height
- ✅ Minimum window width/height
- ✅ Preferences dialog size
- ✅ Dock widget sizes
- ✅ Splitter positions

### Recommendation
Move to `WindowSettingsTab` in Preferences with:
- Spinboxes for width/height
- "Remember window size" checkbox
- "Maximize on startup" option
- Preset sizes (1024x768, 1280x720, 1920x1080)

---

## 2️⃣ MEMORY & PERFORMANCE LIMITS

### Current Hardcoded Values
```python
# src/core/application_config.py
max_memory_usage_mb: int = 2048

# src/core/performance_monitor.py
# Performance level thresholds
if total_memory_gb < 4 or cpu_count < 4:
    max_memory_mb = 1024
    cache_size_mb = 100
    max_triangles = 50000
    thread_count = 2
    chunk_size = 1000
elif total_memory_gb < 8 or cpu_count < 8:
    max_memory_mb = 1536
    cache_size_mb = 256
    max_triangles = 100000
    thread_count = 4
    chunk_size = 5000
elif total_memory_gb < 16 or cpu_count < 16:
    max_memory_mb = 2048
    cache_size_mb = 512
    max_triangles = 500000
    thread_count = 8
    chunk_size = 10000
else:
    max_memory_mb = 3072
    cache_size_mb = 1024
    max_triangles = 1000000
```

### Should Be User-Controllable
- ✅ Max memory usage (MB)
- ✅ Cache size (MB)
- ✅ Max triangles for full quality
- ✅ Thread count
- ✅ Chunk size
- ✅ Performance level (MINIMAL/STANDARD/HIGH/ULTRA)

### Recommendation
Create `PerformanceSettingsTab` with:
- Performance level selector (auto-detect or manual)
- Memory limit slider (512MB - 4GB)
- Cache size slider
- Max triangles slider
- Thread count selector
- "Advanced" section for chunk size

---

## 3️⃣ VIEWER CAMERA SETTINGS

### Current Hardcoded Values
```python
# src/gui/viewer_3d/camera_controller.py
camera_distance = radius * 2.2  # Distance multiplier
near_clipping = distance - (radius * 4.0)
far_clipping = distance + (radius * 4.0)

# Default camera (implied)
fov = 45  # degrees
near = 0.1
far = 1000
```

### Should Be User-Controllable
- ✅ Field of view (FOV)
- ✅ Near clipping plane
- ✅ Far clipping plane
- ✅ Camera distance multiplier
- ✅ Clipping range multiplier
- ✅ Default camera position
- ✅ Camera reset behavior

### Recommendation
Create `CameraSettingsTab` with:
- FOV slider (15° - 120°)
- Near/far clipping sliders
- Distance multiplier slider
- "Reset camera on model load" checkbox
- Preset camera angles (Front, Top, Right, Isometric)

---

## 4️⃣ LIGHTING SETTINGS

### Current Hardcoded Values
```python
# src/gui/lighting_manager.py
position = [100.0, 100.0, 100.0]
color = [1.0, 1.0, 1.0]
intensity = 0.8
cone_angle = 30.0
exponent = 2.0  # Falloff

# Fill light
fill_pos = [-p * 0.5 for p in position]
fill_color = [0.8, 0.8, 0.9]
fill_intensity = intensity * 0.3

# src/gui/viewer_3d/vtk_scene_manager.py
light1_position = (100, 100, 100)
light1_intensity = 0.8
light2_position = (-100, -100, 100)
light2_intensity = 0.5
```

### Should Be User-Controllable
- ✅ Key light position (X, Y, Z)
- ✅ Key light intensity
- ✅ Key light color
- ✅ Key light cone angle
- ✅ Key light falloff
- ✅ Fill light intensity
- ✅ Fill light color
- ✅ Number of lights
- ✅ Light presets (Studio, Soft, Hard, etc.)

### Recommendation
Create `LightingSettingsTab` with:
- 3D position picker for key light
- Intensity slider (0.0 - 1.0)
- Color picker
- Cone angle slider (0° - 180°)
- Falloff slider
- Fill light controls
- Preset buttons (Studio, Soft, Hard, Dramatic)
- "Reset to defaults" button

---

## 5️⃣ RENDERING SETTINGS

### Current Hardcoded Values
```python
# src/gui/viewer_3d/model_renderer.py
render_mode = RenderMode.SOLID  # Default
available_modes = [SOLID, WIREFRAME, POINTS]
transparency = 1.0
opacity = 1.0
```

### Should Be User-Controllable
- ✅ Default render mode
- ✅ Transparency/opacity
- ✅ Edge visibility
- ✅ Wireframe color
- ✅ Point size

### Recommendation
Create `RenderingSettingsTab` with:
- Render mode selector (Solid, Wireframe, Points)
- Opacity slider
- Edge color picker
- Wireframe color picker
- Point size slider

---

## 6️⃣ VTK INTERACTOR SETTINGS

### Current Hardcoded Values
```python
# src/gui/viewer_3d/vtk_scene_manager.py
motion_factor = 8.0
desired_update_rate = 60.0  # FPS
still_update_rate = 10.0  # FPS
interactor_style = vtkInteractorStyleTrackballCamera
```

### Should Be User-Controllable
- ✅ Motion factor (mouse sensitivity)
- ✅ Desired update rate (FPS)
- ✅ Still update rate (FPS)
- ✅ Interactor style (Trackball, Joystick, etc.)

### Recommendation
Add to `CameraSettingsTab`:
- Mouse sensitivity slider (1.0 - 20.0)
- FPS limit selector (30, 60, 120, unlimited)
- Interactor style selector

---

## 7️⃣ GRID & GROUND PLANE

### Current Hardcoded Values
```python
# src/gui/viewer_3d/vtk_scene_manager.py
grid_visible = True
ground_visible = True
ground_z = zmin - 0.5
```

### Should Be User-Controllable
- ✅ Grid visibility
- ✅ Ground plane visibility
- ✅ Grid size
- ✅ Grid color
- ✅ Ground plane color
- ✅ Ground plane position offset

### Recommendation
Add to `RenderingSettingsTab`:
- "Show grid" checkbox
- "Show ground plane" checkbox
- Grid color picker
- Ground plane color picker
- Grid size slider

---

## 8️⃣ LOGGING CONFIGURATION

### Current Hardcoded Values
```python
# src/core/application_config.py
log_level: str = "DEBUG"
enable_file_logging: bool = True
log_retention_days: int = 30
```

### Should Be User-Controllable
- ✅ Log level (DEBUG, INFO, WARNING, ERROR)
- ✅ File logging enabled
- ✅ Log retention days
- ✅ Log file location

### Recommendation
Create `DebugSettingsTab` with:
- Log level selector
- "Enable file logging" checkbox
- Log retention spinner
- "Open log folder" button
- "Clear logs" button

---

## 9️⃣ FEATURE FLAGS

### Current Hardcoded Values
```python
# src/core/application_config.py
enable_hardware_acceleration: bool = True
enable_high_dpi: bool = True
enable_performance_monitoring: bool = True
```

### Should Be User-Controllable
- ✅ Hardware acceleration
- ✅ High DPI support
- ✅ Performance monitoring

### Recommendation
Add to `DebugSettingsTab`:
- "Enable hardware acceleration" checkbox
- "Enable high DPI" checkbox
- "Enable performance monitoring" checkbox
- Note: Requires restart

---

## 🔟 THUMBNAIL SETTINGS

### Current Hardcoded Values
```python
# src/core/application_config.py
thumbnail_bg_color: str = "#F5F5F5"
thumbnail_bg_image: Optional[str] = None
thumbnail_material: Optional[str] = None

# src/core/background_provider.py
DEFAULT_COLOR = "#F5F5F5"
```

### Already User-Controllable
- ✅ Via `ThumbnailSettingsTab` in Preferences

### Recommendation
Enhance existing tab with:
- Background image selector
- Material selector
- Preview thumbnail

---

## SUMMARY

**Total Static Settings**: ~170  
**Already User-Controllable**: ~5 (3%)  
**Should Be User-Controllable**: ~165 (97%)  

**Recommended New Tabs**:
1. Window Settings
2. Performance Settings
3. Camera Settings
4. Lighting Settings
5. Rendering Settings
6. Debug Settings

