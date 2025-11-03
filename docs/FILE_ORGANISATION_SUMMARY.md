# File Organisation & Project Manager - Implementation Summary

## Overview
A Windows-first file organization and project binding subsystem for Digital Workshop with project management, file handling, and interaction file type enforcement.

## Key Specifications (Confirmed)

### IFT (Interaction File Types)
- Stored in **QSettings** (preferences)
- Core objective files only (e.g., .nc, .stl, .obj, .3mf, .step)
- Dynamically reloadable at runtime
- Restricts file operations to defined extensions

### Database
- **Single database**: All data in existing `3dmm.db`
- **New tables**: Projects and Files
- **Single-user**: No file locking required
- **Migrations**: Use existing migration_manager.py

### File Management
- **Three modes**: Link (hard/symbolic), Copy, Remove source
- **Per-file tracking**: Each file has independent storage_mode
- **Fallback**: If copy/move fails → link in place
- **Status tracking**: pending, importing, imported, failed, linked, copied

### Run Mode
- **First run only**: Popup explains mode and allows storage customization
- **Storage**: QSettings under "run_mode/" namespace
- **Later enhancement**: Migration assistant for changing modes post-setup

### Project Management
- **UUID generation**: Each project gets unique UUID
- **Duplicate detection**: Case-insensitive, exact matches only
- **Duplicate handling**: Prompt user to open existing or rename
- **File association**: Files linked to project via project_id UUID

### Background Tasks
- **Async file tracking**: Background task for file operations
- **Graceful shutdown**: 
  - Warn user if background processes running
  - List active background tasks
  - Option to force close with status update
  - Ensure database consistency before exit

### Platform
- **Primary**: Windows (full implementation)
- **Other OS**: Stubs only
- **Windows APIs**: Use ctypes for symlinks and file operations

### Integration
- **Seamless**: Integrate with established codebase
- **Database**: Extend existing database_manager.py
- **Settings**: Use existing QSettings infrastructure
- **Logging**: Use existing logging_config.py
- **Paths**: Leverage existing path_manager.py

## Architecture

### Core Services
1. **IFTService** - File type validation and management
2. **ProjectManager** - Project CRUD and duplicate detection
3. **FileManager** - File operations with fallback logic
4. **BackgroundTaskManager** - Async task tracking
5. **RunModeManager** - First-run setup and preferences

### Database Repositories
1. **ProjectRepository** - Projects table operations
2. **FileRepository** - Files table operations

### UI Components
1. **RunModeSetupDialog** - First-run setup dialog
2. **ProjectManagerWidget** - Project management dock widget (integrated into main window)
3. **DropZoneWidget** - File import with progress (extend existing)
4. **BackgroundTaskMonitorDialog** - Shutdown task monitoring dialog

### Main Window Integration
- **ProjectManager Dock**: Added as native Qt dock widget alongside Model Library, Properties, and Metadata docks
- **Dock System**: Uses native Qt dock system with AllowNestedDocks, AllowTabbedDocks, AnimatedDocks
- **Layout Persistence**: Dock layout saved/restored via QSettings

## Implementation Phases

### Phase 1: Foundation
- Database schema migration
- ProjectRepository and FileRepository
- IFTService with QSettings integration
- RunModeManager

### Phase 2: Core Services
- ProjectManager with duplicate detection
- FileManager with link/copy/move modes
- BackgroundTaskManager for async operations
- Error handling and fallback logic

### Phase 3: UI Integration
- RunModeSetupDialog for first-run setup
- ProjectManagerWidget for project management
- DropZone integration with file operations
- BackgroundTaskMonitorDialog for shutdown

### Phase 4: Testing & Documentation
- Unit tests for all services
- Integration tests for workflows
- Developer documentation
- User documentation

## Database Schema

### Projects Table
```
id (UUID PRIMARY KEY)
name (TEXT UNIQUE NOT NULL)
base_path (TEXT)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Files Table
```
id (UUID PRIMARY KEY)
project_id (UUID FK → projects.id)
original_name (TEXT NOT NULL)
current_path (TEXT NOT NULL)
storage_mode (TEXT NOT NULL)
status (TEXT NOT NULL)
ext (TEXT)
hash (TEXT)
size (INTEGER)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

## File Structure

```
src/core/
├── database/
│   ├── project_repository.py
│   ├── file_repository.py
│   └── migrations/001_create_projects_and_files_tables.py
└── services/
    ├── ift_service.py
    ├── project_manager.py
    ├── file_manager.py
    ├── background_task_manager.py
    ├── run_mode_manager.py
    └── file_operation_error_handler.py

src/gui/
├── dialogs/
│   ├── run_mode_setup_dialog.py
│   └── background_task_monitor_dialog.py
├── project_manager/
│   └── project_manager_widget.py
└── components/
    └── drop_zone_widget.py (extend)
```

## Next Steps

1. ✅ Research & Planning Phase - COMPLETE
2. 🔄 Database Schema Design & Migration - READY TO START
3. IFT Service Implementation
4. Project Manager Implementation
5. File Manager Implementation
6. Background Task Manager Implementation
7. Run Mode Manager Implementation
8. UI Components Implementation
9. Testing & Documentation

## Success Criteria

- ✅ All specifications confirmed
- ✅ Architecture designed
- ✅ Implementation plan created
- ⏳ Database operations working
- ⏳ All services implemented
- ⏳ UI components integrated
- ⏳ All tests passing
- ⏳ Documentation complete

