# File Organisation and Project Manager - Research & Implementation Plan

## Executive Summary
Implement a Windows-first file organization and project binding subsystem with project management, file handling, and interaction file type enforcement. Single-user, non-concurrent system with background task tracking and graceful shutdown handling.

## Confirmed Specifications

### 1. IFT (Interaction File Types)
- **Storage**: QSettings (preferences table)
- **Scope**: Core objective files only (e.g., .nc → GcodePreviewer, .stl/.obj/.3mf/.step → ModelViewer)
- **Format**: Key-value pairs in QSettings under "ift/" namespace
- **Runtime**: Dynamically reloadable
- **Validation**: Restrict file operations to defined extensions only

### 2. Database Architecture
- **Single Database**: All data in existing `3dmm.db`
- **New Tables**: 
  - `Projects(id UUID PRIMARY KEY, name TEXT UNIQUE NOT NULL, base_path TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)`
  - `Files(id UUID PRIMARY KEY, project_id UUID FK, original_name TEXT, current_path TEXT, storage_mode TEXT, status TEXT, ext TEXT, hash TEXT, size INTEGER, created_at TIMESTAMP, updated_at TIMESTAMP)`
- **Single-User**: No file locking required
- **Migrations**: Use existing migration_manager.py

### 3. File Management Modes
- **Link in Place**: Hard/symbolic links (preference-based)
- **Copy to Destination**: Copy files to project base_path
- **Remove from Source**: Delete original after copy (optional)
- **Fallback**: If move/copy fails → link in place
- **Per-File Tracking**: Each file has independent storage_mode

### 4. Run Mode Handling
- **First Run**: Popup explains mode (RAW/PORTABLE/USER/SYSTEM) and allows storage customization
- **Storage Customization**: Set base paths for projects and files
- **Later Enhancement**: Migration assistant for changing modes post-setup
- **Storage**: QSettings under "run_mode/" namespace

### 5. Project Management
- **UUID Generation**: Each project gets UUID on creation
- **Duplicate Detection**: Case-insensitive, exact matches only
- **Duplicate Handling**: Prompt user to open existing or rename
- **File Association**: Files linked to project via project_id UUID

### 6. File Status Tracking
- **Background Task**: Async file tracking and import
- **Statuses**: pending, importing, imported, failed, linked, copied
- **Graceful Shutdown**: 
  - Warn user if background processes running
  - List active background tasks
  - Option to force close with status update before cleanup
  - Ensure database consistency before exit

### 7. Platform Strategy
- **Primary**: Windows (full implementation)
- **Other OS**: Stubs only (return NotImplementedError or log warnings)
- **Windows APIs**: Use ctypes for symlink creation, file operations

### 8. Integration Points
- **Existing Code**: Seamless integration with established codebase
- **Database**: Extend existing `database_manager.py` with new repositories
- **Settings**: Use existing QSettings infrastructure
- **Logging**: Use existing logging_config.py
- **Path Management**: Leverage existing path_manager.py

### 9. Preferences Storage
- **QSettings Namespace**: "projects/" and "ift/"
- **Customizable Paths**: Base paths for projects and files
- **IFT Configuration**: Extension-to-module mappings

## Architecture Overview

### Core Services
1. **IFTService**: Load, validate, and manage file type definitions
2. **ProjectManager**: Create, retrieve, detect duplicates, manage projects
3. **FileManager**: Handle file operations (link/copy/move), track status
4. **BackgroundTaskManager**: Track and manage async file operations
5. **RunModeManager**: Handle first-run setup and mode detection

### Database Repositories
1. **ProjectRepository**: CRUD operations for projects
2. **FileRepository**: CRUD operations for files
3. **IFTRepository**: Read IFT from QSettings

### UI Components
1. **RunModePopup**: First-run setup dialog
2. **ProjectManagerUI**: Create/open projects, handle duplicates
3. **DropZone**: Drag-and-drop file import with progress
4. **BackgroundTaskMonitor**: Show running tasks on shutdown

## Implementation Sequence

### Phase 1: Foundation (Database & Services)
1. Create database schema migrations
2. Implement ProjectRepository and FileRepository
3. Implement IFTService with QSettings integration
4. Implement RunModeManager

### Phase 2: Core Services
1. Implement ProjectManager with duplicate detection
2. Implement FileManager with link/copy/move modes
3. Implement BackgroundTaskManager for async operations
4. Implement error handling and fallback logic

### Phase 3: UI Integration
1. Create RunModePopup for first-run setup
2. Integrate ProjectManager UI
3. Integrate DropZone with file operations
4. Implement BackgroundTaskMonitor for shutdown

### Phase 4: Testing & Documentation
1. Unit tests for all services
2. Integration tests for workflows
3. Developer documentation
4. User documentation

## Key Design Decisions

1. **Single Database**: Simplifies transactions and consistency
2. **UUID for Projects**: Ensures uniqueness across systems
3. **Background Tasks**: Prevents UI blocking during file operations
4. **Graceful Shutdown**: Protects data integrity and user experience
5. **Windows-First**: Leverages platform-specific features
6. **QSettings for IFT**: Allows runtime configuration without file I/O

## Risk Mitigation

1. **File Operation Failures**: Fallback to link in place
2. **Database Corruption**: Graceful shutdown with status update
3. **Duplicate Projects**: Case-insensitive detection with user prompt
4. **Background Task Crashes**: Catch exceptions, update status, log errors
5. **Permission Issues**: Fallback mechanisms and detailed error logging

## Success Criteria

- [ ] All database operations working with new schema
- [ ] ProjectManager creates/detects duplicates correctly
- [ ] FileManager handles all three modes with fallback
- [ ] Background tasks track file status accurately
- [ ] Graceful shutdown with task monitoring
- [ ] All tests passing (unit + integration)
- [ ] Documentation complete and accurate

