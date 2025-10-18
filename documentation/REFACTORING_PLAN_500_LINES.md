# Refactoring Plan: Files Over 500 Lines

## Files Identified (14 total)

| Rank | File | Lines | Priority | Status |
|------|------|-------|----------|--------|
| 1 | `src/core/database_manager.py` | 1160 | 🔴 CRITICAL | NOT_STARTED |
| 2 | `src/gui/viewer_widget_vtk.py` | 1158 | 🔴 CRITICAL | NOT_STARTED |
| 3 | `src/gui/main_window.py` | 972 | 🔴 CRITICAL | NOT_STARTED |
| 4 | `src/gui/model_library.py` | 918 | 🔴 CRITICAL | NOT_STARTED |
| 5 | `src/gui/theme/manager.py` | 866 | 🟠 HIGH | NOT_STARTED |
| 6 | `src/gui/theme.py` | 866 | 🟠 HIGH | NOT_STARTED |
| 7 | `src/gui/theme_manager_widget.py` | 804 | 🟠 HIGH | NOT_STARTED |
| 8 | `src/parsers/stl_parser.py` | 703 | 🟠 HIGH | NOT_STARTED |
| 9 | `src/gui/search_widget.py` | 682 | 🟠 HIGH | NOT_STARTED |
| 10 | `src/gui/window/dock_manager.py` | 680 | 🟠 HIGH | NOT_STARTED |
| 11 | `src/gui/metadata_editor.py` | 640 | 🟠 HIGH | NOT_STARTED |
| 12 | `src/gui/viewer_widget.py` | 576 | 🟡 MEDIUM | NOT_STARTED |
| 13 | `src/core/search_engine.py` | 551 | 🟡 MEDIUM | NOT_STARTED |
| 14 | `src/core/model_cache.py` | 532 | 🟡 MEDIUM | NOT_STARTED |

## Refactoring Strategy

### Phase 1: CRITICAL (Lines 900+)
1. **database_manager.py** (1160 lines)
   - Split into: database operations, model queries, folder management
   - Create: `db_operations.py`, `model_queries.py`, `folder_manager.py`

2. **viewer_widget_vtk.py** (1158 lines)
   - Split into: rendering, camera control, lighting, interaction
   - Create: `vtk_renderer.py`, `camera_controller.py`, `lighting_controller.py`

3. **main_window.py** (972 lines)
   - Split into: window setup, menu management, event handling
   - Create: `window_setup.py`, `menu_manager.py`, `event_handlers.py`

4. **model_library.py** (918 lines)
   - Split into: library widget, model display, grid management
   - Create: `library_widget.py`, `model_display.py`, `grid_manager.py`

### Phase 2: HIGH (Lines 700-900)
5. **theme/manager.py** (866 lines)
   - Already modularized, may need minor cleanup

6. **theme.py** (866 lines)
   - Split into: theme definitions, theme utilities, theme constants
   - Create: `theme_definitions.py`, `theme_utils.py`

7. **theme_manager_widget.py** (804 lines)
   - Split into: UI components, theme application, preview
   - Create: `theme_ui_components.py`, `theme_applier.py`

8. **stl_parser.py** (703 lines)
   - Split into: binary parser, ASCII parser, utilities
   - Create: `stl_binary_parser.py`, `stl_ascii_parser.py`, `stl_utils.py`

9. **search_widget.py** (682 lines)
   - Split into: search UI, search logic, results display
   - Create: `search_ui.py`, `search_logic.py`, `results_display.py`

10. **dock_manager.py** (680 lines)
    - Split into: dock setup, dock widgets, dock management
    - Create: `dock_setup.py`, `dock_widgets.py`

11. **metadata_editor.py** (640 lines)
    - Split into: editor UI, metadata operations, validation
    - Create: `metadata_ui.py`, `metadata_operations.py`

### Phase 3: MEDIUM (Lines 500-700)
12. **viewer_widget.py** (576 lines)
    - Split into: widget setup, rendering, interaction
    - Create: `viewer_setup.py`, `viewer_rendering.py`

13. **search_engine.py** (551 lines)
    - Split into: search logic, indexing, filtering
    - Create: `search_logic.py`, `search_indexing.py`

14. **model_cache.py** (532 lines)
    - Split into: cache management, cache operations
    - Create: `cache_operations.py`

## Execution Order

1. Start with Phase 1 (most critical)
2. Move to Phase 2 (high priority)
3. Complete Phase 3 (medium priority)
4. Update all imports across codebase
5. Run tests to verify functionality
6. Update documentation

## Success Criteria

- ✅ All files under 300 lines (project policy)
- ✅ Single responsibility per file
- ✅ Clear module organization
- ✅ All imports updated
- ✅ All tests passing
- ✅ No functionality changes

## Estimated Effort

- Phase 1: 4-6 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- Import updates: 1-2 hours
- Testing: 1-2 hours
- **Total: 11-17 hours**

## Notes

- Will follow project policy: files under 300 lines
- Each module will have single responsibility
- Clear separation of concerns
- Backward compatible refactoring
- No breaking changes to public APIs

