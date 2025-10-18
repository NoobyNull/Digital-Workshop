# Refactoring Workflow - Aligned with .kilocode/workflows/refactor.md

## Universal 8-Step Refactor Workflow

### STEP 1: Identify Code Boundaries
**Objective**: Identify code boundaries in the target file
**Deliverable**: Boundary map with code sections and their responsibilities

For each file over 500 lines:
- Identify logical code sections
- Map function/class groupings
- Document responsibilities
- Create boundary annotations

### STEP 2: Determine Functional Placement
**Objective**: Determine proper functional placement for each code block
**Deliverable**: Mapping table (block → module)

For each boundary:
- Assign to target module
- Verify single responsibility
- Check for dependencies
- Document placement rationale

### STEP 3: Comment Extraction Markers
**Objective**: Comment identified code blocks with extraction markers
**Deliverable**: Updated file with extraction markers

For each code block:
- Add `# === EXTRACT_TO: module_name.py ===` markers
- Mark start and end of extraction
- Include context comments
- Save annotated file

### STEP 4: Create Core Modules
**Objective**: Create core module directories
**Deliverable**: Created directory structure

For each target module:
- Create directory if needed
- Create `__init__.py`
- Create module file
- Validate structure

### STEP 5: Extract Features
**Objective**: Extract features into dedicated modules
**Deliverable**: Extracted features in new modules

For each marked code block:
- Copy code to target module
- Update imports
- Add module docstring
- Verify functionality

### STEP 6: Run Regression Tests
**Objective**: Run existing tests to verify functionality preservation
**Deliverable**: Test results report

- Run full test suite
- Check for failures
- Document results
- Flag any issues

### STEP 7: Remove Commented Code
**Objective**: Remove commented code from target file
**Deliverable**: Cleaned target file

- Remove extracted code
- Keep import statements
- Add relocation comments
- Verify file integrity

### STEP 8: Benchmark Performance
**Objective**: Test memory usage and runtime performance
**Deliverable**: Benchmark report

- Measure memory usage
- Check runtime performance
- Compare before/after
- Validate thresholds

## Execution Plan

### Phase 1: CRITICAL Files (4 files)
Apply 8-step workflow to:
1. database_manager.py
2. viewer_widget_vtk.py
3. main_window.py
4. model_library.py

### Phase 2: HIGH Files (7 files)
Apply 8-step workflow to:
5. theme/manager.py
6. theme.py
7. theme_manager_widget.py
8. stl_parser.py
9. search_widget.py
10. dock_manager.py
11. metadata_editor.py

### Phase 3: MEDIUM Files (3 files)
Apply 8-step workflow to:
12. viewer_widget.py
13. search_engine.py
14. model_cache.py

## Workflow Checklist

For each file:
- [ ] STEP 1: Identify boundaries
- [ ] STEP 2: Determine placement
- [ ] STEP 3: Add extraction markers
- [ ] STEP 4: Create modules
- [ ] STEP 5: Extract features
- [ ] STEP 6: Run tests
- [ ] STEP 7: Remove commented code
- [ ] STEP 8: Benchmark performance

## Success Criteria

✅ All 8 steps completed per file
✅ All tests passing
✅ No performance regression
✅ All files under 300 lines
✅ Clear module organization
✅ Proper imports
✅ Documentation complete

## Status

**Workflow**: ALIGNED WITH .kilocode/workflows/refactor.md
**Ready**: YES - Ready to execute Phase 1

