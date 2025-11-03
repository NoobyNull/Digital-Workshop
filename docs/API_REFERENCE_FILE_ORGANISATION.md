# API Reference: File Organisation and Project Manager

## Database Layer

### ProjectRepository

**Location**: `src/core/database/project_repository.py`

#### Methods

```python
def create_project(name: str, base_path: str = None, 
                  import_tag: str = None, original_path: str = None,
                  structure_type: str = None) -> str
```
Creates a new project. Returns project UUID.

```python
def get_project(project_id: str) -> dict
```
Retrieves project by ID.

```python
def get_project_by_name(name: str) -> dict
```
Retrieves project by name (case-insensitive).

```python
def list_projects() -> list
```
Lists all projects.

```python
def list_imported_projects() -> list
```
Lists only imported projects.

```python
def update_project(project_id: str, **kwargs) -> bool
```
Updates project fields.

```python
def delete_project(project_id: str) -> bool
```
Deletes project and cascades to files.

### FileRepository

**Location**: `src/core/database/file_repository.py`

#### Methods

```python
def add_file(project_id: str, file_path: str, file_name: str,
            status: str = "pending", link_type: str = None,
            file_hash: str = None) -> int
```
Adds file to project. Returns file ID.

```python
def get_file(file_id: int) -> dict
```
Retrieves file by ID.

```python
def get_files_by_project(project_id: str) -> list
```
Lists all files in project.

```python
def update_file_status(file_id: int, status: str) -> bool
```
Updates file status (pending, importing, imported, failed, linked, copied).

```python
def delete_file(file_id: int) -> bool
```
Deletes file record.

---

## Service Layer

### LibraryStructureDetector

**Location**: `src/core/services/library_structure_detector.py`

```python
def analyze(folder_path: str) -> LibraryStructureAnalysis
```

Returns:
```python
{
    'structure_type': 'nested|flat|balanced',
    'confidence_score': 0.0-1.0,
    'file_count': int,
    'folder_depth': int,
    'file_types': {ext: count},
    'metadata_files': [list],
    'organization_patterns': [list]
}
```

### FileTypeFilter

**Location**: `src/core/services/file_type_filter.py`

```python
def filter_file(file_path: str) -> FileTypeFilterResult
```

Returns:
```python
{
    'allowed': bool,
    'reason': str,
    'file_type': str,
    'extension': str
}
```

### DryRunAnalyzer

**Location**: `src/core/services/dry_run_analyzer.py`

```python
def analyze(folder_path: str, project_name: str) -> DryRunReport
```

Returns:
```python
{
    'can_proceed': bool,
    'allowed_files': int,
    'blocked_files': int,
    'total_size_mb': float,
    'structure_analysis': dict,
    'recommendations': [list],
    'blocked_file_details': [list]
}
```

### ProjectImporter

**Location**: `src/core/services/project_importer.py`

```python
def import_project(folder_path: str, project_name: str,
                  structure_type: str = 'nested') -> ImportReport
```

Returns:
```python
{
    'success': bool,
    'project_id': str,
    'files_imported': int,
    'files_blocked': int,
    'total_size_mb': float,
    'errors': [list],
    'warnings': [list],
    'import_time_seconds': float
}
```

### IFTService

**Location**: `src/core/services/ift_service.py`

```python
def get_ift(ift_name: str) -> IFTDefinition
```
Retrieves IFT definition.

```python
def get_ift_by_extension(extension: str) -> IFTDefinition
```
Retrieves IFT by file extension.

```python
def list_ifts() -> list
```
Lists all IFT definitions.

```python
def add_ift(ift_definition: IFTDefinition) -> bool
```
Adds new IFT definition.

```python
def enable_ift(ift_name: str) -> bool
```
Enables IFT.

```python
def disable_ift(ift_name: str) -> bool
```
Disables IFT.

### RunModeManager

**Location**: `src/core/services/run_mode_manager.py`

```python
def get_run_mode() -> str
```
Returns current run mode (RAW, PORTABLE, USER, SYSTEM).

```python
def set_run_mode(mode: str) -> bool
```
Sets run mode.

```python
def is_first_run() -> bool
```
Checks if first run.

```python
def mark_first_run_complete() -> bool
```
Marks first run as complete.

```python
def get_storage_location() -> str
```
Gets configured storage location.

```python
def set_storage_location(location: str) -> bool
```
Sets storage location.

```python
def get_database_path() -> str
```
Gets database file path.

```python
def get_projects_directory() -> str
```
Gets projects directory path.

### ProjectManager

**Location**: `src/core/services/project_manager.py`

```python
def create_project(name: str, base_path: str = None) -> str
```
Creates project. Returns project ID.

```python
def open_project(project_id: str) -> bool
```
Opens project.

```python
def close_project() -> bool
```
Closes current project.

```python
def get_project(project_id: str) -> dict
```
Gets project details.

```python
def list_projects() -> list
```
Lists all projects.

```python
def check_duplicate(name: str) -> bool
```
Checks if project name exists.

```python
def delete_project(project_id: str) -> bool
```
Deletes project.

### FileManager

**Location**: `src/core/services/file_manager.py`

```python
def add_file(project_id: str, file_path: str, file_name: str) -> int
```
Adds file to project. Returns file ID.

```python
def get_file(file_id: int) -> dict
```
Gets file details.

```python
def update_file_status(file_id: int, status: str) -> bool
```
Updates file status.

```python
def get_files_by_project(project_id: str) -> list
```
Lists project files.

```python
def delete_file(file_id: int) -> bool
```
Deletes file.

---

## UI Layer

### RunModeSetupDialog

**Location**: `src/gui/dialogs/run_mode_setup_dialog.py`

#### Signals
- `setup_complete()`: Emitted when setup completes

#### Methods
```python
def get_storage_location() -> str
```
Returns configured storage location.

### ProjectManagerWidget

**Location**: `src/gui/project_manager/project_manager_widget.py`

#### Signals
- `project_opened(project_id: str)`
- `project_created(project_id: str)`
- `project_deleted(project_id: str)`

#### Methods
```python
def _refresh_project_list() -> None
```
Refreshes project list display.

---

## Data Models

### IFTDefinition
```python
{
    'name': str,
    'extension': str,
    'description': str,
    'enabled': bool,
    'icon': str
}
```

### LibraryStructureAnalysis
```python
{
    'structure_type': str,
    'confidence_score': float,
    'file_count': int,
    'folder_depth': int,
    'file_types': dict,
    'metadata_files': list,
    'organization_patterns': list
}
```

### FileTypeFilterResult
```python
{
    'allowed': bool,
    'reason': str,
    'file_type': str,
    'extension': str
}
```

### DryRunReport
```python
{
    'can_proceed': bool,
    'allowed_files': int,
    'blocked_files': int,
    'total_size_mb': float,
    'structure_analysis': dict,
    'recommendations': list,
    'blocked_file_details': list
}
```

### ImportReport
```python
{
    'success': bool,
    'project_id': str,
    'files_imported': int,
    'files_blocked': int,
    'total_size_mb': float,
    'errors': list,
    'warnings': list,
    'import_time_seconds': float
}
```

---

## Error Codes

- `ValueError`: Duplicate project name
- `FileNotFoundError`: File or folder not found
- `PermissionError`: Insufficient permissions
- `DatabaseError`: Database operation failed
- `ImportError`: Import operation failed


