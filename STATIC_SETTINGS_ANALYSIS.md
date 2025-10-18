# Static Settings Analysis - Candy-Cadence Application

**Date**: 2025-10-18  
**Status**: Comprehensive audit of hardcoded settings

---

## 📊 OVERVIEW

The Candy-Cadence application has **100+ hardcoded settings** across 15+ categories that should be user-controllable. This document identifies all static values and recommends which should be moved to user preferences.

---

## 🎯 PRIORITY 1: CRITICAL (Should be user-controllable immediately)

### **1. Window & UI Dimensions**
**File**: `src/core/application_config.py`
- Default window width: `1200px`
- Default window height: `800px`
- Minimum window width: `800px`
- Minimum window height: `600px`
- Preferences dialog min width: `560px`

**Impact**: Users can't customize initial window size or minimum constraints

---

### **2. Memory & Performance Limits**
**File**: `src/core/application_config.py`, `src/core/performance_monitor.py`
- Max memory usage: `2048 MB`
- Model cache size: Adaptive (but thresholds are hardcoded)
- Performance level thresholds:
  - MINIMAL: < 4GB RAM or < 4 CPUs
  - STANDARD: < 8GB RAM or < 8 CPUs
  - HIGH: < 16GB RAM or < 16 CPUs
  - ULTRA: >= 16GB RAM and >= 16 CPUs

**Cache sizes by level**:
- MINIMAL: 100 MB
- STANDARD: 256 MB
- HIGH: 512 MB
- ULTRA: 1024 MB

**Max triangles by level**:
- MINIMAL: 50,000
- STANDARD: 100,000
- HIGH: 500,000
- ULTRA: 1,000,000

**Thread counts**: 2, 4, 8 (based on CPU count)

**Chunk sizes**: 1000, 5000, 10000

**Impact**: Users can't override performance settings for their specific hardware

---

### **3. Viewer Camera Settings**
**File**: `src/gui/viewer_3d/camera_controller.py`
- Camera FOV: `45 degrees`
- Near clipping plane: `0.1`
- Far clipping plane: `1000`
- Camera distance multiplier: `2.2x` (radius)
- Clipping range multiplier: `4.0x` (radius)

**Impact**: Users can't adjust camera behavior or zoom sensitivity

---

### **4. Lighting Settings**
**File**: `src/gui/lighting_manager.py`, `src/gui/viewer_3d/vtk_scene_manager.py`

**Key Light**:
- Position: `(100, 100, 100)`
- Intensity: `0.8`
- Cone angle: `30 degrees`
- Exponent (falloff): `2.0`

**Fill Light**:
- Position: `(-50, -50, -50)` (opposite to key light)
- Intensity: `0.3` (30% of key light)
- Color: `(0.8, 0.8, 0.9)` (cool white)

**Scene Lights** (vtk_scene_manager):
- Light 1: Position (100, 100, 100), Intensity 0.8
- Light 2: Position (-100, -100, 100), Intensity 0.5

**Impact**: Users can't customize lighting for different model types

---

### **5. Thumbnail Settings**
**File**: `src/core/application_config.py`, `src/core/background_provider.py`
- Default background color: `#F5F5F5` (light gray)
- Background image path: `None` (optional)
- Material selection: `None` (optional)

**Impact**: Users can't change thumbnail appearance globally

---

## 🎯 PRIORITY 2: HIGH (Should be user-controllable soon)

### **6. Rendering Settings**
**File**: `src/gui/viewer_3d/model_renderer.py`
- Default render mode: `SOLID`
- Available modes: `SOLID`, `WIREFRAME`, `POINTS`
- Transparency: `1.0`
- Opacity: `1.0`

**Impact**: Users can't set default rendering mode

---

### **7. VTK Interactor Settings**
**File**: `src/gui/viewer_3d/vtk_scene_manager.py`
- Motion factor: `8.0`
- Desired update rate: `60.0 FPS`
- Still update rate: `10.0 FPS`
- Trackball camera style (hardcoded)

**Impact**: Users can't adjust mouse sensitivity or frame rates

---

### **8. Grid & Ground Plane**
**File**: `src/gui/viewer_3d/vtk_scene_manager.py`
- Grid visibility: `True` (default)
- Ground plane visibility: `True` (default)
- Grid size: Calculated from model bounds
- Ground position: `zmin - 0.5`

**Impact**: Users can't toggle or customize grid/ground appearance

---

### **9. Logging Configuration**
**File**: `src/core/application_config.py`
- Log level: `DEBUG`
- File logging enabled: `True`
- Log retention: `30 days`

**Impact**: Users can't adjust logging verbosity or retention

---

### **10. Feature Flags**
**File**: `src/core/application_config.py`
- Hardware acceleration: `True`
- High DPI support: `True`
- Performance monitoring: `True`

**Impact**: Users can't disable features for troubleshooting

---

## 🎯 PRIORITY 3: MEDIUM (Nice to have)

### **11. Theme/UI Spacing**
**File**: `src/gui/theme/theme_constants.py`
- SPACING_4: `4px`
- SPACING_8: `8px`
- SPACING_12: `12px`
- SPACING_16: `16px`
- SPACING_24: `24px`

**Impact**: UI spacing is fixed, can't be adjusted for accessibility

---

### **12. Theme Colors** (100+ colors)
**File**: `src/gui/theme/theme_defaults.py`
- Window background: `#ffffff`
- Text color: `#000000`
- Primary accent: `#0078d4`
- Canvas background: `#f0f0f0`
- Model surface: `#6496c8`
- And 95+ more colors

**Impact**: Already partially user-controllable via Theming tab, but defaults are hardcoded

---

### **13. Typography**
**File**: `src/resources/styles/main_window.scss`
- Font family: `Segoe UI, Arial, sans-serif`
- Base font size: `9pt`
- Small font size: `8pt`
- Font weight: `normal` / `bold`

**Impact**: Users can't adjust font sizes for accessibility

---

### **14. Border Radius**
**File**: `src/resources/styles/main_window.scss`
- Small: `2px`
- Medium: `4px`
- Large: `8px`
- Full: `50%`

**Impact**: UI roundness is fixed

---

### **15. Animation Durations**
**File**: `src/resources/styles/performance.css`
- Animation duration: `1s` (high performance: `0.8s`)
- Transition duration: `0.2s` (high performance: `0.3s`)
- Loading opacity: `0.9` (high performance: `0.8`)

**Impact**: Users can't adjust animation speeds

---

## 📋 SUMMARY TABLE

| Category | Count | Priority | User Control |
|----------|-------|----------|---------------|
| Window/UI | 5 | P1 | ❌ No |
| Memory/Performance | 15 | P1 | ❌ No |
| Camera | 5 | P1 | ❌ No |
| Lighting | 10 | P1 | ❌ No |
| Thumbnails | 3 | P1 | ⚠️ Partial |
| Rendering | 5 | P2 | ❌ No |
| Interactor | 4 | P2 | ❌ No |
| Grid/Ground | 4 | P2 | ❌ No |
| Logging | 3 | P2 | ❌ No |
| Feature Flags | 3 | P2 | ❌ No |
| Spacing | 5 | P3 | ❌ No |
| Colors | 100+ | P3 | ✅ Yes |
| Typography | 4 | P3 | ❌ No |
| Borders | 4 | P3 | ❌ No |
| Animations | 3 | P3 | ❌ No |
| **TOTAL** | **~170** | - | **~5%** |

---

## 🚀 RECOMMENDATIONS

### **Phase 1: Critical Settings (1-2 weeks)**
1. Move window dimensions to preferences
2. Add performance tuning UI
3. Create camera settings panel
4. Add lighting control panel (already partially done)
5. Thumbnail customization

### **Phase 2: High Priority (2-3 weeks)**
1. Rendering mode defaults
2. Interactor sensitivity settings
3. Grid/ground plane toggles
4. Logging level selector
5. Feature flag toggles

### **Phase 3: Medium Priority (3-4 weeks)**
1. Spacing scale adjustment
2. Font size selector
3. Animation speed control
4. Border radius customization

---

## ✅ ALREADY USER-CONTROLLABLE

- ✅ Theme colors (via Theming tab)
- ✅ Qt-Material theme variants (via Preferences)
- ✅ Thumbnail background (via Thumbnails tab)
- ✅ File maintenance settings (via Files tab)

---

## 📝 NEXT STEPS

1. Create `AdvancedSettingsTab` for performance tuning
2. Create `CameraSettingsTab` for viewer controls
3. Create `LightingSettingsTab` for light customization
4. Create `RenderingSettingsTab` for render options
5. Migrate hardcoded values to `ApplicationConfig`
6. Add settings persistence for all new options

