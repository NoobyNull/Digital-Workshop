# Refactoring Execution Guide - 8-Step Workflow

## Overview

This guide implements the 8-step Universal Refactor Workflow for all 14 files over 500 lines.

## Phase 1: CRITICAL Files (4 files)

### File 1: database_manager.py (1160 lines)

**STEP 1: Identify Boundaries**
- Database connection management
- Model CRUD operations
- Folder management
- Query operations
- Caching logic

**STEP 2: Determine Placement**
- `db_operations.py` - Connection, transactions
- `model_queries.py` - Model CRUD, queries
- `folder_manager.py` - Folder operations

**STEP 3: Add Extraction Markers**
- Mark each section with `# === EXTRACT_TO: module_name.py ===`
- Include start/end markers
- Add context comments

**STEP 4: Create Modules**
```
src/core/database/
├── __init__.py
├── db_operations.py
├── model_queries.py
└── folder_manager.py
```

**STEP 5: Extract Features**
- Copy marked code to target modules
- Update imports
- Add module docstrings

**STEP 6: Run Tests**
- Run `pytest tests/test_database.py`
- Verify all tests pass
- Check for import errors

**STEP 7: Remove Code**
- Remove extracted code from database_manager.py
- Keep imports from new modules
- Add relocation comments

**STEP 8: Benchmark**
- Measure query performance
- Check memory usage
- Compare before/after

---

### File 2: viewer_widget_vtk.py (1158 lines)

**STEP 1: Identify Boundaries**
- VTK renderer setup
- Camera control
- Lighting management
- Interaction handlers
- Scene management

**STEP 2: Determine Placement**
- `vtk_renderer.py` - Renderer, scene
- `camera_controller.py` - Camera operations
- `lighting_controller.py` - Lighting setup

**STEP 3-8**: Follow same process as File 1

---

### File 3: main_window.py (972 lines)

**STEP 1: Identify Boundaries**
- Window initialization
- Menu setup
- Event handlers
- Status bar management
- Dock widget management

**STEP 2: Determine Placement**
- `window_setup.py` - Window init, layout
- `menu_manager.py` - Menu creation, actions
- `event_handlers.py` - Event handling

**STEP 3-8**: Follow same process as File 1

---

### File 4: model_library.py (918 lines)

**STEP 1: Identify Boundaries**
- Library widget setup
- Model display logic
- Grid management
- Selection handling
- Thumbnail display

**STEP 2: Determine Placement**
- `library_widget.py` - Widget setup
- `model_display.py` - Display logic
- `grid_manager.py` - Grid operations

**STEP 3-8**: Follow same process as File 1

---

## Phase 2: HIGH Files (7 files)

Apply same 8-step workflow to:
- theme/manager.py
- theme.py
- theme_manager_widget.py
- stl_parser.py
- search_widget.py
- dock_manager.py
- metadata_editor.py

## Phase 3: MEDIUM Files (3 files)

Apply same 8-step workflow to:
- viewer_widget.py
- search_engine.py
- model_cache.py

## Workflow Execution Checklist

For each file:
- [ ] STEP 1: Identify boundaries (document in analysis)
- [ ] STEP 2: Determine placement (create mapping table)
- [ ] STEP 3: Add markers (update file with markers)
- [ ] STEP 4: Create modules (create directory structure)
- [ ] STEP 5: Extract features (move code to modules)
- [ ] STEP 6: Run tests (verify all tests pass)
- [ ] STEP 7: Remove code (clean up original file)
- [ ] STEP 8: Benchmark (measure performance)

## Success Criteria

✅ All 8 steps completed per file
✅ All tests passing
✅ No performance regression
✅ All files under 300 lines
✅ Clear module organization
✅ Proper imports
✅ Documentation complete

## Next Steps

1. Start with Phase 1, File 1 (database_manager.py)
2. Complete all 8 steps
3. Move to next file
4. Repeat for all 14 files
5. Final verification and testing

