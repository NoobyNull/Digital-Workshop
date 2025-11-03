# Phase 1 API Reference

## ProjectRepository API

### Create Project
```python
project_id = db.create_project(
    name: str,                          # Project name (unique, case-insensitive)
    base_path: Optional[str] = None,    # Base directory path
    import_tag: Optional[str] = None,   # "imported_project" or None
    original_path: Optional[str] = None,# Original import path
    structure_type: Optional[str] = None# "flat", "nested", "balanced"
) -> str  # Returns project UUID
```

### Get Project
```python
project = db.get_project(project_id: str) -> Optional[Dict]
# Returns: {id, name, base_path, import_tag, original_path, structure_type, import_date, created_at, updated_at}
```

### Get Project by Name (Case-Insensitive)
```python
project = db.get_project_by_name(name: str) -> Optional[Dict]
# Returns: Project data or None
```

### List Projects
```python
projects = db.list_projects(
    limit: Optional[int] = None,  # Max results
    offset: int = 0               # Skip N results
) -> List[Dict]
# Returns: List of project data, ordered by created_at DESC
```

### List Imported Projects
```python
imported = db.list_imported_projects() -> List[Dict]
# Returns: List of projects with import_tag = "imported_project"
```

### Update Project
```python
success = db.update_project(
    project_id: str,
    **kwargs  # name, base_path, import_tag, original_path, structure_type, import_date
) -> bool
```

### Delete Project
```python
success = db.delete_project(project_id: str) -> bool
# Cascades: Deletes all associated files
```

### Get Project Count
```python
count = db.get_project_count() -> int
```

---

## FileRepository API

### Add File
```python
file_id = db.add_file(
    project_id: str,                    # Project UUID
    file_path: str,                     # Full file path
    file_name: str,                     # File name
    file_size: Optional[int] = None,    # File size in bytes
    file_hash: Optional[str] = None,    # File hash for duplicates
    status: str = "pending",            # pending, importing, imported, failed, linked, copied
    link_type: Optional[str] = None,    # hard, symbolic, copy, original
    original_path: Optional[str] = None # Original path before linking
) -> int  # Returns file ID
```

### Get File
```python
file_data = db.get_file(file_id: int) -> Optional[Dict]
# Returns: {id, project_id, file_path, file_name, file_size, file_hash, status, link_type, original_path, created_at, updated_at}
```

### Get Files by Project
```python
files = db.get_files_by_project(project_id: str) -> List[Dict]
# Returns: List of files in project, ordered by created_at DESC
```

### Get Files by Status
```python
files = db.get_files_by_status(
    project_id: str,
    status: str  # pending, importing, imported, failed, linked, copied
) -> List[Dict]
```

### Update File Status
```python
success = db.update_file_status(
    file_id: int,
    status: str  # New status
) -> bool
```

### Update File
```python
success = db.update_file(
    file_id: int,
    **kwargs  # file_path, file_name, file_size, file_hash, status, link_type, original_path
) -> bool
```

### Delete File
```python
success = db.delete_file(file_id: int) -> bool
```

### Get File Count by Project
```python
count = db.get_file_count_by_project(project_id: str) -> int
```

### Find Duplicate by Hash
```python
duplicate = db.find_duplicate_by_hash(
    project_id: str,
    file_hash: str
) -> Optional[Dict]
# Returns: First file with matching hash or None
```

---

## Usage Examples

### Create a Project and Add Files
```python
from src.core.database.database_manager import DatabaseManager

db = DatabaseManager("data/3dmm.db")

# Create project
project_id = db.create_project(
    name="My 3D Models",
    base_path="/models/my_collection"
)

# Add files
file1_id = db.add_file(
    project_id=project_id,
    file_path="/models/my_collection/model1.stl",
    file_name="model1.stl",
    file_size=2048,
    status="imported"
)

file2_id = db.add_file(
    project_id=project_id,
    file_path="/models/my_collection/model2.obj",
    file_name="model2.obj",
    file_size=4096,
    status="imported"
)

# List files
files = db.get_files_by_project(project_id)
print(f"Project has {len(files)} files")
```

### Import Existing Library
```python
# Create imported project
project_id = db.create_project(
    name="Imported Library",
    import_tag="imported_project",
    original_path="/original/library/path",
    structure_type="nested"
)

# Add files from library
for file_path in library_files:
    db.add_file(
        project_id=project_id,
        file_path=file_path,
        file_name=os.path.basename(file_path),
        status="imported",
        link_type="hard"
    )

# List all imported projects
imported = db.list_imported_projects()
```

### Track File Import Progress
```python
# Create file with pending status
file_id = db.add_file(
    project_id=project_id,
    file_path="/path/to/file.stl",
    file_name="file.stl",
    status="pending"
)

# Update status as import progresses
db.update_file_status(file_id, "importing")
# ... perform import ...
db.update_file_status(file_id, "imported")

# Or mark as failed
db.update_file_status(file_id, "failed")
```

### Find Duplicates
```python
# Calculate file hash
file_hash = calculate_hash("/path/to/file.stl")

# Check for duplicate
duplicate = db.find_duplicate_by_hash(project_id, file_hash)
if duplicate:
    print(f"Duplicate found: {duplicate['file_name']}")
else:
    print("No duplicate found")
```

---

## Error Handling

### Duplicate Project Detection
```python
try:
    db.create_project(name="Existing Project")
except ValueError as e:
    print(f"Error: {e}")  # "Project 'Existing Project' already exists"
```

### Database Errors
```python
try:
    db.add_file(project_id, file_path, file_name)
except sqlite3.Error as e:
    print(f"Database error: {e}")
```

---

## Status Values

### File Status
- `pending` - File added but not yet imported
- `importing` - File import in progress
- `imported` - File successfully imported
- `failed` - File import failed
- `linked` - File linked (hard or symbolic)
- `copied` - File copied to destination

### Link Type
- `hard` - Hard link
- `symbolic` - Symbolic link
- `copy` - File copied
- `original` - Original file location

### Structure Type
- `flat` - All files in single directory
- `nested` - Files organized in subdirectories
- `balanced` - Mixed organization

---

## Performance Considerations

### Indexes
- `idx_projects_name` - Fast lookup by project name
- `idx_projects_import_tag` - Fast filtering of imported projects
- `idx_files_project_id` - Fast retrieval of files by project
- `idx_files_status` - Fast filtering by status
- `idx_files_file_hash` - Fast duplicate detection

### Pagination
```python
# Get first 10 projects
projects = db.list_projects(limit=10, offset=0)

# Get next 10 projects
projects = db.list_projects(limit=10, offset=10)
```

---

## Database Connection

### Get Connection
```python
with db._db_ops.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()
```

### Connection Settings
- Foreign keys: ON
- Journal mode: WAL
- Synchronous: NORMAL
- Cache size: 10000
- Temp store: MEMORY

