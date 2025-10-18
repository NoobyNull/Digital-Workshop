# Phase 1, File 2: viewer_widget_vtk.py - Refactoring Analysis

## File Overview
- **File**: `src/gui/viewer_widget_vtk.py`
- **Lines**: 1158 (excluding comments)
- **Main Class**: `Viewer3DWidget(QWidget)`
- **Purpose**: VTK-based 3D viewer widget for interactive model visualization

---

## Code Boundaries & Functional Areas

### 1. **VTK Scene Management** (~350 lines)
**Methods**:
- `_setup_vtk_scene()` - Initialize VTK renderer, render window, interactor
- `_setup_shadows()` - Configure shadow mapping
- `_update_grid()` - Create/update grid visualization
- `_create_ground_plane()` - Create ground plane actor
- `_toggle_grid()` - Toggle grid visibility
- `_on_orientation_widget_interaction()` - Handle UCS widget interaction

**Responsibility**: Core VTK scene setup, grid/ground plane management, orientation widget

**Extract to**: `vtk_scene_manager.py`

---

### 2. **Model Rendering & Geometry** (~400 lines)
**Methods**:
- `_create_vtk_polydata()` - Convert STLModel to VTK polydata
- `_create_vtk_polydata_from_arrays()` - Create polydata from arrays
- `_generate_uv_coordinates()` - Generate UV mapping for textures
- `_set_render_mode()` - Set rendering mode (solid/wireframe/points)
- `_apply_render_mode()` - Apply render mode to actor
- `set_render_mode()` - Public interface for render mode
- `_remove_current_model()` - Clean up current model
- `load_model()` - Load model into viewer

**Responsibility**: Model loading, geometry creation, rendering modes

**Extract to**: `model_renderer.py`

---

### 3. **Camera & View Management** (~250 lines)
**Methods**:
- `_fit_camera_to_model()` - Fit camera to model bounds
- `_fit_camera_to_model_preserving_orientation()` - Fit camera while preserving UCS
- `_rotate_around_view_axis()` - Rotate view around axis
- `reset_view()` - Reset camera to default
- `get_model_info()` - Get current model information

**Responsibility**: Camera positioning, view management, orientation preservation

**Extract to**: `camera_controller.py`

---

### 4. **Performance Monitoring** (~100 lines)
**Methods**:
- `_setup_performance_monitoring()` - Initialize performance tracking
- `_update_performance()` - Update FPS and performance metrics

**Responsibility**: FPS tracking, performance monitoring

**Extract to**: `performance_tracker.py`

---

### 5. **UI & Integration** (~150 lines)
**Methods**:
- `_init_ui()` - Initialize UI layout and controls
- `apply_theme()` - Apply theme styling
- `_open_material_picker()` - Open material picker dialog
- `_open_lighting_panel()` - Request lighting panel
- `_save_view_requested()` - Request save view
- `reset_save_view_button()` - Reset save view button
- `cleanup()` - Clean up resources
- `closeEvent()` - Handle widget close

**Responsibility**: UI initialization, theme application, signal handling

**Extract to**: `viewer_ui_manager.py`

---

## Module Extraction Plan

### New Module Structure
```
src/gui/viewer_3d/
├── __init__.py
├── viewer_widget_vtk.py (refactored facade, ~150 lines)
├── vtk_scene_manager.py (~350 lines)
├── model_renderer.py (~400 lines)
├── camera_controller.py (~250 lines)
├── performance_tracker.py (~100 lines)
└── viewer_ui_manager.py (~150 lines)
```

### Compatibility Layer
- `src/gui/viewer_widget_vtk.py` → Facade pattern
- Maintains all public methods
- Delegates to specialized modules
- Backward compatible with existing imports

---

## Refactoring Benefits

1. **Modularity**: Each module has single responsibility
2. **Maintainability**: Easier to understand and modify
3. **Testability**: Each module can be tested independently
4. **Reusability**: Components can be used in other contexts
5. **Performance**: No performance degradation expected

---

## 8-Step Workflow Alignment

| Step | Task | Status |
|------|------|--------|
| 1 | Identify boundaries | ✅ Complete |
| 2 | Determine placement | ✅ Complete |
| 3 | Add markers | ⏳ Next |
| 4 | Create modules | ⏳ Next |
| 5 | Extract features | ⏳ Next |
| 6 | Run tests | ⏳ Next |
| 7 | Remove code | ⏳ Next |
| 8 | Benchmark | ⏳ Next |

---

## Next Steps

1. Add extraction markers to original file
2. Create module directory structure
3. Extract each module
4. Create compatibility layer
5. Run regression tests
6. Verify performance

