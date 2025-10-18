# Phase 1, File 3: main_window.py - Analysis & Planning

## File Overview

- **File**: `src/gui/main_window.py`
- **Lines**: 1283 (excluding comments)
- **Class**: `MainWindow(QMainWindow)`
- **Status**: Ready for refactoring

---

## Functional Areas Identified

### 1. **Layout Management** (~350 lines)
**Lines**: 74-366, 378-493

**Responsibility**: Dock layout persistence, snapping, and restoration

**Methods**:
- `_init_ui()` - Initialize main UI layout
- `_connect_layout_autosave()` - Auto-save layout changes
- `_redock_all()` - Restore all docks to default positions
- `_settings_json_path()` - Get settings file path
- `_read_settings_json()` - Read layout settings
- `_write_settings_json()` - Write layout settings
- `_init_layout_persistence()` - Initialize persistence system
- `_schedule_layout_save()` - Schedule layout save
- `_save_current_layout()` - Save current layout
- `_load_saved_layout()` - Load saved layout
- `_init_snapping_system()` - Initialize dock snapping
- `_register_dock_for_snapping()` - Register dock for snapping
- `_iter_docks()` - Iterate over docks
- `_enable_snap_handlers()` - Enable/disable snap handlers
- `_set_layout_edit_mode()` - Set layout edit mode
- `_snap_dock_to_edge()` - Snap dock to edge
- `_reset_dock_layout_and_save()` - Reset layout

**Dependencies**: QSettings, QDockWidget, Path

---

### 2. **Lighting & Settings Management** (~150 lines)
**Lines**: 502-572

**Responsibility**: Lighting panel and settings persistence

**Methods**:
- `_save_lighting_settings()` - Save lighting configuration
- `_load_lighting_settings()` - Load lighting configuration
- `_save_lighting_panel_visibility()` - Save panel visibility
- `_update_metadata_action_state()` - Update action states
- `_save_metadata_panel_visibility()` - Save metadata panel visibility

**Dependencies**: LightingPanel, QSettings

---

### 3. **Dock Management** (~400 lines)
**Lines**: 583-855

**Responsibility**: Create and manage dock widgets (metadata, library)

**Methods**:
- `_create_metadata_dock()` - Create metadata editor dock
- `_restore_metadata_manager()` - Restore metadata manager state
- `_create_model_library_dock()` - Create model library dock
- `_restore_model_library()` - Restore library state
- `_update_library_action_state()` - Update library action states

**Dependencies**: MetadataEditorWidget, ModelLibraryWidget, QDockWidget

---

### 4. **Event Handlers & Actions** (~300 lines)
**Lines**: 871-1230

**Responsibility**: Handle user actions and model events

**Methods**:
- `_reload_stylesheet_action()` - Reload stylesheet
- `_on_model_double_clicked()` - Handle model selection
- `_on_models_added()` - Handle models added
- `_on_metadata_saved()` - Handle metadata save
- `_on_metadata_changed()` - Handle metadata change
- `_show_preferences()` - Show preferences dialog
- `_show_theme_manager()` - Show theme manager
- `_on_theme_applied()` - Handle theme change
- `_zoom_in()` - Zoom in
- `_zoom_out()` - Zoom out
- `_reset_view()` - Reset view
- `_save_current_view()` - Save current view
- `_restore_saved_camera()` - Restore camera view
- `_show_about()` - Show about dialog
- `_generate_library_screenshots()` - Generate screenshots
- `_on_screenshot_progress()` - Handle screenshot progress
- `_on_screenshot_generated()` - Handle screenshot generated
- `_on_screenshot_error()` - Handle screenshot error
- `_on_screenshots_finished()` - Handle screenshots finished

**Dependencies**: Viewer3DWidget, ModelLibraryWidget, signals/slots

---

## Proposed Module Structure

### Module 1: **layout_manager.py** (~350 lines)
- Dock layout persistence
- Snapping system
- Layout restoration

### Module 2: **settings_manager.py** (~150 lines)
- Lighting settings
- Metadata settings
- Settings persistence

### Module 3: **dock_manager.py** (~400 lines)
- Metadata dock creation
- Library dock creation
- Dock state management

### Module 4: **event_handler.py** (~300 lines)
- User action handlers
- Model event handlers
- View management

### Refactored MainWindow (~80 lines)
- Facade pattern
- Coordinate modules
- Maintain public API

---

## Extraction Strategy

1. **Create** `src/gui/main_window/` directory
2. **Extract** layout management → `layout_manager.py`
3. **Extract** settings management → `settings_manager.py`
4. **Extract** dock management → `dock_manager.py`
5. **Extract** event handlers → `event_handler.py`
6. **Create** refactored `MainWindow` facade
7. **Create** compatibility layer at `src/gui/main_window.py`
8. **Run** regression tests

---

## Key Considerations

- **Signals/Slots**: Maintain Qt signal/slot connections
- **State Management**: Preserve all state variables
- **Dependencies**: Manage cross-module dependencies
- **Backward Compatibility**: Maintain existing public API
- **Settings Persistence**: Ensure settings continue to work

---

## Next Steps

1. Create module directory structure
2. Extract layout management
3. Extract settings management
4. Extract dock management
5. Extract event handlers
6. Create facade and compatibility layer
7. Run tests
8. Benchmark performance

