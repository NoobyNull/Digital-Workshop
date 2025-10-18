# Refactoring Execution Checklist

## Phase 1: CRITICAL FILES (900+ lines)

### 1. database_manager.py (1160 lines)
- [ ] Analyze current structure
- [ ] Identify logical modules
- [ ] Create db_operations.py
- [ ] Create model_queries.py
- [ ] Create folder_manager.py
- [ ] Update imports in database_manager.py
- [ ] Update all callers
- [ ] Run tests
- [ ] Verify functionality

### 2. viewer_widget_vtk.py (1158 lines)
- [ ] Analyze current structure
- [ ] Identify logical modules
- [ ] Create vtk_renderer.py
- [ ] Create camera_controller.py
- [ ] Create lighting_controller.py
- [ ] Update imports in viewer_widget_vtk.py
- [ ] Update all callers
- [ ] Run tests
- [ ] Verify functionality

### 3. main_window.py (972 lines)
- [ ] Analyze current structure
- [ ] Identify logical modules
- [ ] Create window_setup.py
- [ ] Create menu_manager.py
- [ ] Create event_handlers.py
- [ ] Update imports in main_window.py
- [ ] Update all callers
- [ ] Run tests
- [ ] Verify functionality

### 4. model_library.py (918 lines)
- [ ] Analyze current structure
- [ ] Identify logical modules
- [ ] Create library_widget.py
- [ ] Create model_display.py
- [ ] Create grid_manager.py
- [ ] Update imports in model_library.py
- [ ] Update all callers
- [ ] Run tests
- [ ] Verify functionality

## Phase 2: HIGH PRIORITY (700-900 lines)

### 5. theme/manager.py (866 lines)
- [ ] Review current structure
- [ ] Determine if refactoring needed
- [ ] If needed, create sub-modules
- [ ] Update imports
- [ ] Run tests

### 6. theme.py (866 lines)
- [ ] Analyze current structure
- [ ] Create theme_definitions.py
- [ ] Create theme_utils.py
- [ ] Update imports
- [ ] Run tests

### 7. theme_manager_widget.py (804 lines)
- [ ] Analyze current structure
- [ ] Create theme_ui_components.py
- [ ] Create theme_applier.py
- [ ] Update imports
- [ ] Run tests

### 8. stl_parser.py (703 lines)
- [ ] Analyze current structure
- [ ] Create stl_binary_parser.py
- [ ] Create stl_ascii_parser.py
- [ ] Create stl_utils.py
- [ ] Update imports
- [ ] Run tests

### 9. search_widget.py (682 lines)
- [ ] Analyze current structure
- [ ] Create search_ui.py
- [ ] Create search_logic.py
- [ ] Create results_display.py
- [ ] Update imports
- [ ] Run tests

### 10. dock_manager.py (680 lines)
- [ ] Analyze current structure
- [ ] Create dock_setup.py
- [ ] Create dock_widgets.py
- [ ] Update imports
- [ ] Run tests

### 11. metadata_editor.py (640 lines)
- [ ] Analyze current structure
- [ ] Create metadata_ui.py
- [ ] Create metadata_operations.py
- [ ] Update imports
- [ ] Run tests

## Phase 3: MEDIUM PRIORITY (500-700 lines)

### 12. viewer_widget.py (576 lines)
- [ ] Analyze current structure
- [ ] Create viewer_setup.py
- [ ] Create viewer_rendering.py
- [ ] Update imports
- [ ] Run tests

### 13. search_engine.py (551 lines)
- [ ] Analyze current structure
- [ ] Create search_logic.py
- [ ] Create search_indexing.py
- [ ] Update imports
- [ ] Run tests

### 14. model_cache.py (532 lines)
- [ ] Analyze current structure
- [ ] Create cache_operations.py
- [ ] Update imports
- [ ] Run tests

## Post-Refactoring

- [ ] Update all imports across codebase
- [ ] Run full test suite
- [ ] Verify no breaking changes
- [ ] Update documentation
- [ ] Code review
- [ ] Final verification

## Notes

- Each file should be under 300 lines
- Single responsibility principle
- Clear module organization
- All tests must pass
- No functionality changes

