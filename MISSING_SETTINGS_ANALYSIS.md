# Missing Application Settings Analysis

## Overview
This document identifies all application settings that are currently **hardcoded or not user-adjustable** and would benefit from being added to the Preferences dialog.

---

## 🎯 HIGH PRIORITY SETTINGS (Immediate User Value)

### 1. **Window & Display Settings** 
**Current Status:** Hardcoded  
**Location:** `src/core/application_config.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Default window width | 1200px | Users want custom startup size | Spinbox (800-3840) |
| Default window height | 800px | Users want custom startup size | Spinbox (600-2160) |
| Minimum window width | 800px | Prevent accidental resize too small | Spinbox (400-1200) |
| Minimum window height | 600px | Prevent accidental resize too small | Spinbox (300-1000) |
| Maximize on startup | Not available | Users want fullscreen launch | Checkbox |
| Remember window size | Not available | Restore last used size | Checkbox |
| Preferences dialog width | 560px (hardcoded) | Users want wider dialog | Spinbox (400-1000) |

**Recommendation:** Add to **"Window & Layout"** tab

---

### 2. **3D Viewer - Grid & Ground Plane**
**Current Status:** Hardcoded  
**Location:** `src/gui/viewer_3d/vtk_scene_manager.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Grid visibility | Always ON | Toggle for cleaner view | Checkbox |
| Grid color | Theme-dependent | Customize for visibility | Color picker |
| Grid size | Fixed | Adjust for different models | Slider (1-100) |
| Ground plane visibility | Always ON | Toggle for cleaner view | Checkbox |
| Ground plane color | Theme-dependent | Customize appearance | Color picker |
| Ground plane offset | zmin - 0.5 | Adjust height | Slider (-10 to +10) |

**Recommendation:** Add to new **"3D Viewer"** tab

---

### 3. **Camera & Interaction Settings**
**Current Status:** Hardcoded  
**Location:** `src/gui/viewer_3d/camera_controller.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Mouse sensitivity | Fixed | Users want faster/slower rotation | Slider (0.5-5.0) |
| FPS limit | Unlimited | Reduce CPU usage | Dropdown (30/60/120/∞) |
| Zoom speed | Fixed | Customize scroll behavior | Slider (0.5-3.0) |
| Pan speed | Fixed | Customize pan behavior | Slider (0.5-3.0) |
| Interactor style | TrackballCamera | Different interaction modes | Dropdown |
| Auto-fit on load | Not available | Auto-center new models | Checkbox |

**Recommendation:** Add to new **"3D Viewer"** tab

---

### 4. **Lighting Settings (Advanced)**
**Current Status:** Partially persistent, not all adjustable  
**Location:** `src/gui/lighting_manager.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Default light position | (100, 100, 100) | Customize default | 3x Spinbox |
| Default light color | White (1,1,1) | Customize default | Color picker |
| Default intensity | 0.8 | Customize default | Slider (0-1) |
| Cone angle | 30° | Adjust light spread | Slider (5-90) |
| Fill light enabled | Yes | Toggle secondary light | Checkbox |
| Fill light intensity | 0.3 | Adjust fill light | Slider (0-1) |

**Recommendation:** Add to **"3D Viewer"** tab (Advanced section)

---

## ⚠️ MEDIUM PRIORITY SETTINGS (Developer/Power User Value)

### 5. **Logging & Debugging**
**Current Status:** Hardcoded  
**Location:** `src/core/application_config.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Log level | DEBUG | Reduce verbosity | Dropdown (DEBUG/INFO/WARNING/ERROR) |
| File logging enabled | True | Disable for performance | Checkbox |
| Log retention days | 30 | Customize cleanup | Spinbox (1-365) |
| Log file location | AppData | View/change location | File browser |

**Recommendation:** Add to new **"Debug"** tab (Advanced section)

---

### 6. **Feature Flags**
**Current Status:** Hardcoded  
**Location:** `src/core/application_config.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Hardware acceleration | Enabled | Troubleshoot GPU issues | Checkbox (⚠️ Restart required) |
| High DPI support | Enabled | Fix scaling issues | Checkbox (⚠️ Restart required) |
| Performance monitoring | Enabled | Reduce overhead | Checkbox |

**Recommendation:** Add to new **"Debug"** tab with restart warning

---

### 7. **Model Rendering**
**Current Status:** Hardcoded  
**Location:** `src/gui/viewer_3d/model_renderer.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Edge visibility | Default | Show/hide model edges | Checkbox |
| Wireframe mode | Off | Toggle wireframe | Checkbox |
| Ambient occlusion | Default | Enhance depth perception | Checkbox |
| Specular highlights | Default | Adjust shininess | Slider (0-1) |

**Recommendation:** Add to **"3D Viewer"** tab (Rendering section)

---

## 📊 LOWER PRIORITY SETTINGS (Niche Use Cases)

### 8. **Performance Thresholds**
**Current Status:** Hardcoded  
**Location:** `src/core/performance_monitor.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| FPS warning threshold | 30 FPS | Customize alert level | Spinbox (10-60) |
| Memory warning threshold | 80% | Customize alert level | Slider (50-95%) |
| Cache eviction threshold | 90% | Customize cleanup trigger | Slider (50-95%) |

**Recommendation:** Add to **"Performance"** tab (Advanced section)

---

### 9. **Dock Widget Defaults**
**Current Status:** Partially saved, not customizable  
**Location:** `src/gui/main_window.py`

| Setting | Current Value | User Value | Suggested Control |
|---------|---------------|-----------|-------------------|
| Library panel default width | Auto | Set preferred width | Spinbox |
| Metadata panel default width | Auto | Set preferred width | Spinbox |
| Viewer panel default size | Auto | Set preferred size | Spinbox |

**Recommendation:** Add to **"Window & Layout"** tab

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: High Priority (1-2 weeks)
- [ ] Window & Display Settings
- [ ] 3D Viewer (Grid, Ground, Camera)
- [ ] Lighting Settings (Advanced)

### Phase 2: Medium Priority (2-3 weeks)
- [ ] Logging & Debugging
- [ ] Feature Flags
- [ ] Model Rendering

### Phase 3: Lower Priority (3-4 weeks)
- [ ] Performance Thresholds
- [ ] Dock Widget Defaults

---

## 🎨 Suggested New Preference Tabs

1. **"3D Viewer"** (NEW)
   - Grid & Ground Plane
   - Camera & Interaction
   - Lighting (Advanced)
   - Model Rendering

2. **"Debug"** (NEW)
   - Logging Configuration
   - Feature Flags
   - Performance Thresholds

3. **"Window & Layout"** (EXPAND)
   - Window dimensions
   - Startup behavior
   - Dock widget defaults

---

## 💡 User Value Summary

**Total Missing Settings:** 30+

**High Impact Settings:** 13
- Window customization
- 3D viewer controls
- Lighting preferences

**Medium Impact Settings:** 10
- Logging & debugging
- Feature flags
- Rendering options

**Low Impact Settings:** 7+
- Performance thresholds
- Dock defaults
- Advanced tweaks


