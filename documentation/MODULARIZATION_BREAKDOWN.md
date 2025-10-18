# Detailed Modularization Breakdown

## 1. viewer_widget_vtk.py (1,781 lines) → 6 modules

### Current Structure Issues
- **Mixed Concerns**: UI, rendering, camera, lighting, performance all in one file
- **Hard to Test**: Can't test camera logic without VTK setup
- **Difficult to Extend**: Adding new render modes requires editing massive file
- **Performance Monitoring**: Intertwined with rendering logic

### Proposed Split

#### `viewer_widget.py` (~400 lines)
```python
# Main widget orchestrator
class Viewer3DWidget(QWidget):
    - __init__()
    - _init_ui()
    - load_model()
    - clear_scene()
    - Signal connections
    - Public API
```

#### `vtk_scene_manager.py` (~300 lines)
```python
# VTK scene setup and management
class VTKSceneManager:
    - _setup_vtk_scene()
    - _setup_renderer()
    - _setup_lighting()
    - _setup_interactor()
    - get_renderer()
    - get_render_window()
```

#### `camera_controller.py` (~250 lines)
```python
# Camera manipulation and control
class CameraController:
    - reset_view()
    - fit_camera_to_model()
    - fit_camera_preserving_orientation()
    - pan_camera()
    - rotate_camera()
    - zoom_camera()
```

#### `lighting_manager.py` (~200 lines)
```python
# Lighting configuration
class LightingManager:
    - setup_default_lights()
    - add_light()
    - remove_light()
    - update_light_intensity()
    - get_lights()
```

#### `render_modes.py` (~150 lines)
```python
# Rendering mode management
class RenderModeManager:
    - set_render_mode()
    - apply_solid_rendering()
    - apply_wireframe_rendering()
    - apply_points_rendering()
    - get_current_mode()
```

#### `performance_monitor.py` (~200 lines)
```python
# Performance tracking
class ViewerPerformanceMonitor:
    - _setup_performance_monitoring()
    - _update_fps()
    - get_current_fps()
    - get_performance_stats()
```

---

## 2. database_manager.py (1,442 lines) → 6 modules

### Current Structure Issues
- **God Object**: Handles schema, CRUD, search, stats, maintenance
- **Hard to Mock**: Tests need full database setup
- **Difficult to Extend**: Adding new tables requires editing massive file
- **Mixed Responsibilities**: Data access + business logic

### Proposed Split

#### `manager.py` (~300 lines)
```python
# Main database manager (facade)
class DatabaseManager:
    - __init__()
    - get_models_repository()
    - get_metadata_repository()
    - get_search_repository()
    - close()
    - Singleton pattern
```

#### `schema.py` (~250 lines)
```python
# Database schema and migrations
class DatabaseSchema:
    - _initialize_database()
    - _migrate_database_schema()
    - _create_models_table()
    - _create_metadata_table()
    - _create_categories_table()
    - _create_indices()
```

#### `models_repository.py` (~250 lines)
```python
# Model CRUD operations
class ModelsRepository:
    - add_model()
    - get_model()
    - get_all_models()
    - update_model()
    - delete_model()
    - get_model_by_hash()
```

#### `metadata_repository.py` (~200 lines)
```python
# Metadata operations
class MetadataRepository:
    - add_model_metadata()
    - get_model_metadata()
    - update_model_metadata()
    - delete_model_metadata()
    - get_camera_position()
    - save_camera_position()
```

#### `search_repository.py` (~200 lines)
```python
# Search and filtering
class SearchRepository:
    - search_models()
    - filter_by_category()
    - filter_by_format()
    - filter_by_rating()
    - get_recent_models()
```

#### `maintenance.py` (~100 lines)
```python
# Database maintenance
class DatabaseMaintenance:
    - vacuum_database()
    - analyze_database()
    - get_database_stats()
    - check_integrity()
    - optimize_indices()
```

---

## 3. model_library.py (1,157 lines) → 5 modules

### Proposed Split

#### `model_library.py` (~300 lines)
- Main widget orchestrator
- Signal connections
- Public API

#### `file_browser.py` (~200 lines)
- File system model
- Directory navigation
- File filtering

#### `model_loader_worker.py` (~250 lines)
- Background loading thread
- Progress reporting
- Error handling

#### `view_modes.py` (~150 lines)
- List view management
- Grid view management
- View switching

#### `library_filters.py` (~150 lines)
- Search filtering
- Category filtering
- Format filtering

---

## 4. theme.py (1,128 lines) → 4 modules

### Proposed Split

#### `colors.py` (~200 lines)
- Color definitions
- Color constants
- Spacing constants

#### `theme_manager.py` (~300 lines)
- ThemeManager singleton
- Theme switching
- Widget registry

#### `css_processor.py` (~200 lines)
- CSS template processing
- Variable substitution
- CSS caching

#### `theme_persistence.py` (~150 lines)
- Save theme to settings
- Load theme from settings
- Export/import themes

---

## 5. search_widget.py (1,115 lines) → 4 modules

### Proposed Split

#### `search_widget.py` (~300 lines)
- Main search UI
- Signal connections

#### `search_engine.py` (~250 lines)
- Search logic
- Query building
- Result ranking

#### `filter_builder.py` (~200 lines)
- Filter UI components
- Filter logic
- Filter persistence

#### `result_renderer.py` (~150 lines)
- Result display
- Result formatting
- Result caching

---

## Benefits Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Max File Size | 1,781 | ~400 | **77% reduction** |
| Avg Module Size | 1,200 | ~300 | **75% reduction** |
| Cognitive Load | Very High | Low | **Easier to understand** |
| Test Coverage | Difficult | Easy | **Better testability** |
| Reusability | Low | High | **More composable** |
| Maintenance | Hard | Easy | **Faster bug fixes** |

---

## Implementation Strategy

1. **Create new module directories** (viewer/, database/, library/, theme/, search/)
2. **Extract classes** one at a time
3. **Update imports** in dependent files
4. **Write unit tests** for each module
5. **Run integration tests** to verify functionality
6. **Update documentation** with new structure
7. **Delete old monolithic files** after verification

