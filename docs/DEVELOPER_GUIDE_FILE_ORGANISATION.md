# Developer Guide: File Organisation and Project Manager

## Overview

This guide covers the File Organisation and Project Manager system implemented in Digital Workshop. The system provides:

- Project-based file organization
- Library import with structure detection
- File type security and filtering
- Database persistence
- UI integration with Qt dock widgets

---

## Architecture

### Database Layer

**Location**: `src/core/database/`

#### Tables

**Projects Table**
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    base_path TEXT,
    import_tag TEXT,
    original_path TEXT,
    structure_type TEXT,
    import_date DATETIME,
    created_at DATETIME,
    updated_at DATETIME
)
```

**Files Table**
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    project_id TEXT,
    file_path TEXT,
    file_name TEXT,
    status TEXT,
    link_type TEXT,
    file_hash TEXT,
    created_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
)
```

#### Repositories

- **ProjectRepository**: CRUD operations for projects
- **FileRepository**: File tracking and status management

### Service Layer

**Location**: `src/core/services/`

#### Phase 1.5 Services

1. **LibraryStructureDetector**
   - Analyzes folder hierarchies
   - Detects organization patterns
   - Calculates confidence scores

2. **FileTypeFilter**
   - Whitelist/blacklist system
   - 50+ supported file types
   - Blocks system files (exe, bat, ps1, etc.)

3. **DryRunAnalyzer**
   - Simulates import without file operations
   - Generates verification reports
   - Provides recommendations

4. **ProjectImporter**
   - Executes library imports
   - Creates projects with "imported_project" tag
   - Generates import reports

#### Phase 2 Services

1. **IFTService**
   - Manages Interaction File Types
   - Loads/saves from QSettings
   - 6 default IFT definitions

2. **RunModeManager**
   - First run detection
   - Storage location configuration
   - Preferences management

3. **ProjectManager**
   - Project lifecycle management
   - Duplicate detection
   - Project listing and filtering

4. **FileManager**
   - File operations (link, copy, move)
   - Status tracking
   - Fallback logic

### UI Layer

**Location**: `src/gui/`

#### Components

1. **RunModeSetupDialog** (`dialogs/run_mode_setup_dialog.py`)
   - First-run configuration
   - Storage location selection
   - Welcome message

2. **ProjectManagerWidget** (`project_manager/project_manager_widget.py`)
   - Project list display
   - Create/import/delete projects
   - Dry run preview
   - Signal emission

3. **Main Window Integration** (`main_window.py`)
   - ProjectManagerWidget as dock
   - Signal handlers
   - Status bar updates

---

## Usage Examples

### Creating a Project

```python
from src.core.services.project_manager import ProjectManager
from src.core.database.database_manager import DatabaseManager

db_manager = DatabaseManager()
project_manager = ProjectManager(db_manager)

# Create project
project_id = project_manager.create_project("My Project")
```

### Importing a Library

```python
from src.core.services.project_importer import ProjectImporter
from src.core.services.dry_run_analyzer import DryRunAnalyzer

importer = ProjectImporter(db_manager)
analyzer = DryRunAnalyzer()

# Dry run
dry_run = analyzer.analyze("/library/path", "My Library")

# Import
if dry_run.can_proceed:
    report = importer.import_project("/library/path", "My Library")
```

### File Type Filtering

```python
from src.core.services.file_type_filter import FileTypeFilter

filter = FileTypeFilter()

# Check file
result = filter.filter_file("/path/to/file.stl")
if result.allowed:
    print("File is allowed")
else:
    print(f"File blocked: {result.reason}")
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Phase-specific tests
pytest tests/test_phase1_database_schema.py -v
pytest tests/test_phase1_5_library_detection.py -v
pytest tests/test_phase2_core_services.py -v
pytest tests/test_phase3_ui_components.py -v
```

### Test Coverage

- Database schema and repositories: 19 tests
- Library detection and import: 20 tests
- Core services: 26 tests
- UI components: 12 tests

---

## Configuration

### QSettings Keys

**IFT Configuration**
```
IFT/stl/enabled
IFT/stl/name
IFT/stl/extension
```

**Run Mode Configuration**
```
run_mode/first_run_complete
storage/location
```

**Project Preferences**
```
projects/last_opened
projects/default_import_mode
```

---

## File Type Security

### Supported Extensions

- 3D Models: .stl, .obj, .3mf, .step, .iges
- Documents: .pdf, .txt, .md, .doc, .docx
- Images: .png, .jpg, .jpeg, .bmp, .gif
- Data: .json, .csv, .xml, .yaml

### Blocked Extensions

- Executables: .exe, .com, .bat, .cmd
- Scripts: .ps1, .sh, .py, .js
- System: .sys, .dll, .ini, .inf
- Archives: .zip, .rar, .7z (optional)

---

## Error Handling

### Common Errors

**Duplicate Project**
```python
try:
    project_id = project_manager.create_project("Existing Project")
except ValueError as e:
    print(f"Error: {e}")  # Project 'Existing Project' already exists
```

**File Type Blocked**
```python
result = filter.filter_file("/path/to/malware.exe")
if not result.allowed:
    print(f"Blocked: {result.reason}")  # File type not allowed
```

---

## Performance Considerations

1. **Database Indexes**: Optimized for name, import_tag, project_id, status
2. **Lazy Loading**: Projects loaded on demand
3. **Batch Operations**: Import processes files in batches
4. **Caching**: Structure analysis cached during import

---

## Future Enhancements

1. Background task monitoring
2. Import progress tracking
3. File synchronization
4. Project templates
5. Advanced filtering options
6. Export functionality

---

## Support

For issues or questions:
1. Check test files for usage examples
2. Review service docstrings
3. Check main_window.py for UI integration
4. Review database schema in db_operations.py


