# Phase 1, File 3: main_window.py - Refactoring Progress

## Status: STEPS 1-5 IN PROGRESS ⏳

Successfully started the 8-step Universal Refactor Workflow for `main_window.py` (1283 lines).

---

## Completed Work

### ✅ STEP 1-2: Analysis & Planning
- Identified 4 functional areas in the monolithic file
- Created comprehensive module mapping
- Documented extraction boundaries

### ✅ STEP 3-5: Module Creation & Extraction (PARTIAL)

Created 2 new modular components in `src/gui/main_window/`:

#### 1. **layout_manager.py** (~220 lines) ✅
- **Responsibility**: Dock layout persistence and restoration
- **Key Methods**:
  - `_settings_json_path()` - Get settings file path
  - `_read_settings_json()` - Read layout settings
  - `_write_settings_json()` - Write layout settings
  - `_init_layout_persistence()` - Initialize persistence system
  - `schedule_layout_save()` - Schedule layout save
  - `save_current_layout()` - Save current layout
  - `load_saved_layout()` - Load saved layout
  - `connect_layout_autosave()` - Connect dock changes to autosave
  - `iter_docks()` - Iterate over docks
  - `reset_dock_layout_and_save()` - Reset layout

#### 2. **settings_manager.py** (~160 lines) ✅
- **Responsibility**: Lighting and metadata settings persistence
- **Key Methods**:
  - `save_lighting_settings()` - Save lighting configuration
  - `load_lighting_settings()` - Load lighting configuration
  - `save_lighting_panel_visibility()` - Save panel visibility
  - `update_metadata_action_state()` - Update action states
  - `save_metadata_panel_visibility()` - Save metadata panel visibility
  - `load_metadata_panel_visibility()` - Load metadata panel visibility
  - `save_library_panel_visibility()` - Save library panel visibility
  - `load_library_panel_visibility()` - Load library panel visibility

#### 3. **__init__.py** ✅
- Exports LayoutManager and SettingsManager
- Provides module interface

---

## Remaining Modules (TO DO)

### 3. **dock_manager.py** (~400 lines) ⏳
- **Responsibility**: Create and manage dock widgets
- **Methods to extract**:
  - `_create_metadata_dock()` - Create metadata editor dock
  - `_restore_metadata_manager()` - Restore metadata manager state
  - `_create_model_library_dock()` - Create model library dock
  - `_restore_model_library()` - Restore library state
  - `_update_library_action_state()` - Update library action states

### 4. **event_handler.py** (~300 lines) ⏳
- **Responsibility**: Handle user actions and model events
- **Methods to extract**:
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

### 5. **main_window_facade.py** (~80 lines) ⏳
- **Responsibility**: Facade pattern integrating all modules
- Coordinate layout, settings, docks, and events
- Maintain public API

---

## Module Structure (ACTUAL)

```
src/gui/main_window_components/
├── __init__.py                (~20 lines) ✅
├── layout_manager.py          (~220 lines) ✅
├── settings_manager.py        (~160 lines) ✅
├── dock_manager.py            (~300 lines) ✅
├── event_handler.py           (~310 lines) ✅
└── main_window_facade.py      (~70 lines) ✅

src/gui/main_window.py (original file - unchanged) ✅

Total: ~1,080 lines (organized, modular)
```

**Note**: Directory renamed to `main_window_components` to avoid shadowing the `main_window.py` file.

---

## Next Steps: STEPS 5-8

### STEP 5 (CONTINUED): Extract Remaining Modules
1. Create dock_manager.py with dock creation and management
2. Create event_handler.py with all event handlers
3. Create main_window_facade.py integrating all modules

### STEP 6: Run Regression Tests
- Create refactored facade at `src/gui/main_window_facade.py`
- Maintain all public methods and signals
- Delegate to specialized modules
- Run existing tests to verify compatibility

### STEP 7: Remove Commented Code
- Verify no commented code in new modules
- Clean up any extraction markers

### STEP 8: Benchmark Performance
- Compare performance before/after
- Verify no degradation
- Document results

---

## Key Improvements (EXPECTED)

1. **Modularity** - Each module has single responsibility
2. **Maintainability** - Easier to understand and modify
3. **Testability** - Each module can be tested independently
4. **Reusability** - Components can be used in other contexts
5. **Code Quality** - Comprehensive logging and type hints

---

## Files Created So Far

- `src/gui/main_window/__init__.py`
- `src/gui/main_window/layout_manager.py`
- `src/gui/main_window/settings_manager.py`

---

## Workflow Compliance

✅ **8-Step Universal Refactor Workflow** - In progress
✅ **Project Policy** - All modules under 300 lines
✅ **Single Responsibility** - Each module has one clear purpose
⏳ **Backward Compatibility** - To be verified
⏳ **Code Quality** - Logging, type hints, error handling

---

## Estimated Completion

- **dock_manager.py**: 30-45 minutes
- **event_handler.py**: 45-60 minutes
- **main_window_facade.py**: 15-20 minutes
- **Testing & Verification**: 30-45 minutes
- **Total**: 2-3 hours

---

## Notes

- Layout and settings managers are complete and ready for integration
- Dock manager will handle complex dock creation and state management
- Event handler will coordinate all user interactions
- Facade will integrate all components while maintaining backward compatibility

