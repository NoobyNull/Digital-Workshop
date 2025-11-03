# File Organisation - Detailed Implementation Plan

## Phase 1: Foundation (Database & Services)

### 1.1 Database Schema Migration
**File**: `src/core/database/migrations/001_create_projects_and_files_tables.py`

```sql
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    base_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    original_name TEXT NOT NULL,
    current_path TEXT NOT NULL,
    storage_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    ext TEXT,
    hash TEXT,
    size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
```

### 1.2 Repository Classes
**Files**:
- `src/core/database/project_repository.py` - CRUD for projects
- `src/core/database/file_repository.py` - CRUD for files

### 1.3 IFT Service
**File**: `src/core/services/ift_service.py`
- Load IFT from QSettings
- Validate file extensions
- Get module for extension
- Reload at runtime

### 1.4 Run Mode Manager
**File**: `src/core/services/run_mode_manager.py`
- Detect first run
- Store run mode in QSettings
- Manage storage paths

## Phase 1.5: Library Structure Detection & Project Import

### 1.5.1 Library Structure Detector
**File**: `src/core/services/library_structure_detector.py`
- Analyze folder hierarchies recursively
- Detect file type grouping patterns (STL_Files, OBJ_Files, etc.)
- Identify depth-based organization (flat vs. nested)
- Scan for metadata files (README.md, manifest.json, etc.)
- Calculate organization confidence score (0-100%)
- Return structure analysis with recommendations
- Support for custom folder naming patterns

### 1.5.2 File Type Filter
**File**: `src/core/services/file_type_filter.py`
- Whitelist: All file types supported (csv, pdf, txt, doc, xls, etc.)
- Blacklist: System files (exe, sys, ini, inf, com, bat, ps1, dll, msi, scr, vbs, js, etc.)
- Configurable via QSettings
- Validation during import
- Return file type classification (supported/blocked/metadata)

### 1.5.3 Project Importer
**File**: `src/core/services/project_importer.py`
- Top-level import workflow
- Tag projects as "imported project" for easy location
- Dry run capability (simulate without committing)
- Trust mode (user verification before import)
- Preserve existing folder structure
- Link all supported file types
- Generate import report with statistics

### 1.5.4 Dry Run Analyzer
**File**: `src/core/services/dry_run_analyzer.py`
- Simulate import without file operations
- Show file count by type
- Display folder structure preview
- Identify blocked files
- Estimate storage impact
- Generate verification report
- Support for cancellation before commit

## Phase 2: Core Services

### 2.1 Project Manager
**File**: `src/core/services/project_manager.py`
- Create project with UUID
- Detect duplicate names (case-insensitive)
- Retrieve project by ID/name
- List all projects

### 2.2 File Manager
**File**: `src/core/services/file_manager.py`
- Link files (hard/symbolic)
- Copy files to destination
- Remove source files
- Fallback logic
- Track file status

### 2.3 Background Task Manager
**File**: `src/core/services/background_task_manager.py`
- Track async file operations
- Update file status
- Handle task completion
- Provide task list for shutdown

### 2.4 Error Handling
**File**: `src/core/services/file_operation_error_handler.py`
- Catch file operation exceptions
- Implement fallback logic
- Log detailed errors
- Update file status

## Phase 3: UI Integration

### 3.1 Run Mode Popup
**File**: `src/gui/dialogs/run_mode_setup_dialog.py`
- Display run mode information
- Allow storage path customization
- Save preferences to QSettings
- Show on first run only

### 3.2 Project Manager UI
**File**: `src/gui/project_manager/project_manager_widget.py`
- Create new project
- Open existing project
- Handle duplicate detection
- Display project list

### 3.2.1 Main Window Integration
**File**: `src/gui/main_window.py` (extend)
- Add `_setup_project_manager_dock()` method
- Create ProjectManager dock widget
- Add to dock system alongside Model Library, Properties, Metadata
- Integrate with native Qt dock system

### 3.3 DropZone Integration
**File**: `src/gui/components/drop_zone_widget.py` (extend existing)
- Accept file drops
- Validate against IFT
- Trigger file manager
- Show progress

### 3.4 Background Task Monitor
**File**: `src/gui/dialogs/background_task_monitor_dialog.py`
- Show running tasks on shutdown
- List task details
- Option to force close
- Update status before cleanup

## Phase 4: Testing & Documentation

### 4.1 Unit Tests
- `tests/services/test_project_manager.py`
- `tests/services/test_file_manager.py`
- `tests/services/test_ift_service.py`
- `tests/services/test_background_task_manager.py`
- `tests/services/test_library_structure_detector.py`
- `tests/services/test_file_type_filter.py`
- `tests/services/test_dry_run_analyzer.py`

### 4.2 Integration Tests
- `tests/integration/test_project_workflow.py`
- `tests/integration/test_file_import_workflow.py`
- `tests/integration/test_shutdown_with_tasks.py`
- `tests/integration/test_project_import_workflow.py`
- `tests/integration/test_dry_run_and_commit.py`

### 4.3 Documentation
- Developer guide: Schema, services, integration
- User guide: Run modes, project creation, file management
- API documentation for services

## File Structure Summary

```
src/
├── core/
│   ├── database/
│   │   ├── project_repository.py
│   │   ├── file_repository.py
│   │   └── migrations/
│   │       └── 001_create_projects_and_files_tables.py
│   └── services/
│       ├── ift_service.py
│       ├── project_manager.py
│       ├── file_manager.py
│       ├── background_task_manager.py
│       ├── run_mode_manager.py
│       ├── file_operation_error_handler.py
│       ├── library_structure_detector.py
│       ├── file_type_filter.py
│       ├── project_importer.py
│       └── dry_run_analyzer.py
└── gui/
    ├── dialogs/
    │   ├── run_mode_setup_dialog.py
    │   ├── background_task_monitor_dialog.py
    │   └── project_import_dialog.py
    ├── project_manager/
    │   ├── __init__.py
    │   └── project_manager_widget.py
    ├── components/
    │   └── drop_zone_widget.py (extend)
    └── main_window.py (extend with _setup_project_manager_dock)

tests/
├── services/
│   ├── test_project_manager.py
│   ├── test_file_manager.py
│   ├── test_ift_service.py
│   └── test_background_task_manager.py
└── integration/
    ├── test_project_workflow.py
    ├── test_file_import_workflow.py
    └── test_shutdown_with_tasks.py

docs/
├── FILE_ORGANISATION_RESEARCH_AND_PLAN.md
├── FILE_ORGANISATION_IMPLEMENTATION_PLAN.md
├── FILE_ORGANISATION_DEVELOPER_GUIDE.md
└── FILE_ORGANISATION_USER_GUIDE.md
```

## Implementation Order

1. **Database Schema** - Foundation for all services
2. **Repositories** - Data access layer
3. **IFT Service** - File type validation
4. **Project Manager** - Core business logic
5. **File Manager** - File operations
6. **Background Task Manager** - Async tracking
7. **Run Mode Manager** - Setup and preferences
8. **UI Components** - User interface
9. **Tests** - Comprehensive coverage
10. **Documentation** - Developer and user guides

## Success Metrics

- All database operations functional
- 100% test coverage for services
- Graceful error handling with fallbacks
- Clean integration with existing code
- Complete documentation

