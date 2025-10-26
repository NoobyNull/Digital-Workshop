# Import File Manager Guide

## Overview

The Import File Manager is a comprehensive file management system for the 3D model import process. It provides two distinct file management modes and includes features for duplicate detection, progress tracking, and error recovery.

## Features

- **Dual Management Modes**: "Keep Organized" and "Leave in Place"
- **Root Directory Validation**: Ensures proper configuration for organized mode
- **File Copying with Progress**: Efficient file operations with real-time progress
- **Duplicate Detection**: Uses FastHasher for fast duplicate identification
- **Organized Directory Structure**: Automatic file organization by type
- **Rollback Capability**: Undo operations on failure
- **Comprehensive Logging**: JSON-formatted logs for debugging
- **Error Handling**: Graceful error recovery and reporting
- **Cancellation Support**: User-controlled operation interruption

## Architecture

### Core Components

```
ImportFileManager
├── FileManagementMode (Enum)
│   ├── KEEP_ORGANIZED
│   └── LEAVE_IN_PLACE
├── ImportSession (Session tracking)
├── ImportFileInfo (File metadata)
└── ImportResult (Operation results)
```

### Dependencies

- [`FastHasher`](../src/core/fast_hasher.py) - xxHash128 file hashing
- [`RootFolderManager`](../src/core/root_folder_manager.py) - Root directory management
- [`CancellationToken`](../src/core/cancellation_token.py) - Cancellation support

## File Management Modes

### Keep Organized Mode

Application manages file locations with an organized directory structure.

**Requirements:**
- Root directory must be configured in RootFolderManager
- Root directory must have write permissions
- Sufficient disk space for file copies

**Directory Structure:**
```
Root Directory/
├── STL_Files/
├── OBJ_Files/
├── STEP_Files/
├── 3MF_Files/
├── PLY_Files/
├── FBX_Files/
├── Collada_Files/
├── GLTF_Files/
└── Other_Files/
```

**Behavior:**
- Files are copied to organized subdirectories
- Filename conflicts are automatically resolved
- Original files remain untouched
- Supports hash-based naming for consistency

### Leave in Place Mode

Files remain in their original locations.

**Requirements:**
- Read access to source files
- No root directory needed

**Behavior:**
- Files stay in original locations
- Only file paths are tracked in database
- No file copying occurs
- Minimal disk space impact

## Usage Examples

### Basic Import Session

```python
from src.core.import_file_manager import (
    ImportFileManager,
    FileManagementMode
)

# Initialize manager
manager = ImportFileManager()

# Prepare file list
file_paths = [
    "/path/to/model1.stl",
    "/path/to/model2.obj",
    "/path/to/model3.3mf"
]

# Start import session (leave in place mode)
success, error, session = manager.start_import_session(
    file_paths=file_paths,
    mode=FileManagementMode.LEAVE_IN_PLACE
)

if not success:
    print(f"Failed to start session: {error}")
    exit(1)

# Process each file
for file_info in session.files:
    success, error = manager.process_file(file_info, session)
    if not success:
        print(f"Failed to process {file_info.original_path}: {error}")

# Complete session
result = manager.complete_import_session(session, success=True)

print(f"Imported {result.processed_files}/{result.total_files} files")
print(f"Duration: {result.duration_seconds:.2f}s")
```

### Keep Organized Mode with Root Directory

```python
# Validate root directory first
root_dir = "/path/to/organized/storage"
is_valid, error = manager.validate_root_directory(
    root_dir,
    FileManagementMode.KEEP_ORGANIZED
)

if not is_valid:
    print(f"Invalid root directory: {error}")
    exit(1)

# Start session with organized mode
success, error, session = manager.start_import_session(
    file_paths=file_paths,
    mode=FileManagementMode.KEEP_ORGANIZED,
    root_directory=root_dir
)
```

### With Progress Tracking

```python
def progress_callback(message, percent):
    print(f"{message}: {percent}%")

# Process file with progress
success, error = manager.process_file(
    file_info,
    session,
    progress_callback=progress_callback
)
```

### With Cancellation Support

```python
from src.core.cancellation_token import CancellationToken

token = CancellationToken()

# Start processing in background thread
# ...

# Cancel if needed
token.cancel()
```

### Error Handling and Rollback

```python
try:
    # Process files
    for file_info in session.files:
        success, error = manager.process_file(file_info, session)
        if not success:
            raise Exception(f"Processing failed: {error}")
    
    # Complete on success
    result = manager.complete_import_session(session, success=True)
    
except Exception as e:
    print(f"Import failed: {e}")
    
    # Rollback changes
    if manager.rollback_session(session):
        print("Successfully rolled back changes")
    else:
        print("Rollback failed - manual cleanup may be needed")
    
    # Mark session as failed
    result = manager.complete_import_session(session, success=False)
```

### Duplicate Detection

```python
# Build existing hashes dictionary from database
existing_hashes = {}
for model in database.get_all_models():
    if model.get('file_hash'):
        existing_hashes[model['file_hash']] = model

# Check for duplicates during import
for file_info in session.files:
    # Process file to get hash
    manager.process_file(file_info, session)
    
    # Check if duplicate
    is_dup, existing = manager.check_duplicate(
        file_info.file_hash,
        existing_hashes
    )
    
    if is_dup:
        print(f"Duplicate found: {file_info.original_path}")
        print(f"Matches: {existing['file_path']}")
        # Handle duplicate (skip, replace, prompt user, etc.)
```

## API Reference

### ImportFileManager

#### `__init__()`

Initialize the import file manager.

#### `validate_root_directory(root_directory, mode) -> Tuple[bool, Optional[str]]`

Validate root directory for the specified management mode.

**Parameters:**
- `root_directory` (str): Path to root directory
- `mode` (FileManagementMode): File management mode

**Returns:**
- Tuple of (is_valid, error_message)

#### `start_import_session(file_paths, mode, root_directory, duplicate_action) -> Tuple[bool, Optional[str], Optional[ImportSession]]`

Start a new import session.

**Parameters:**
- `file_paths` (List[str]): List of file paths to import
- `mode` (FileManagementMode): File management mode
- `root_directory` (Optional[str]): Root directory (required for keep_organized)
- `duplicate_action` (DuplicateAction): Action for duplicates (default: SKIP)

**Returns:**
- Tuple of (success, error_message, session)

#### `process_file(file_info, session, progress_callback, cancellation_token) -> Tuple[bool, Optional[str]]`

Process a single file for import.

**Parameters:**
- `file_info` (ImportFileInfo): File information
- `session` (ImportSession): Import session
- `progress_callback` (Optional[Callable]): Progress callback(message, percent)
- `cancellation_token` (Optional[CancellationToken]): Cancellation token

**Returns:**
- Tuple of (success, error_message)

#### `rollback_session(session) -> bool`

Rollback a failed import session.

**Parameters:**
- `session` (ImportSession): Import session to rollback

**Returns:**
- True if rollback successful

#### `complete_import_session(session, success) -> ImportResult`

Complete an import session and generate result.

**Parameters:**
- `session` (ImportSession): Import session to complete
- `success` (bool): Whether session completed successfully

**Returns:**
- ImportResult with session details

#### `check_duplicate(file_hash, existing_hashes) -> Tuple[bool, Optional[Any]]`

Check if file is a duplicate based on hash.

**Parameters:**
- `file_hash` (str): Hash of file to check
- `existing_hashes` (Dict): Map of hashes to existing file info

**Returns:**
- Tuple of (is_duplicate, existing_file_info)

### Data Classes

#### ImportFileInfo

```python
@dataclass
class ImportFileInfo:
    original_path: str              # Original file path
    file_size: int                  # File size in bytes
    file_hash: Optional[str]        # File hash (xxHash128)
    managed_path: Optional[str]     # Path in managed storage
    import_status: str              # Status: pending/hashing/copying/completed/failed
    error_message: Optional[str]    # Error message if failed
    progress_percent: int           # Progress percentage (0-100)
    start_time: Optional[float]     # Start timestamp
    end_time: Optional[float]       # End timestamp
```

#### ImportSession

```python
@dataclass
class ImportSession:
    session_id: str                         # Unique session ID
    mode: FileManagementMode                # Management mode
    root_directory: Optional[str]           # Root directory (for keep_organized)
    files: List[ImportFileInfo]             # Files in session
    copied_files: List[str]                 # Copied files (for rollback)
    created_directories: List[str]          # Created dirs (for rollback)
    start_time: Optional[float]             # Session start time
    end_time: Optional[float]               # Session end time
    status: str                             # Status: pending/running/completed/failed
```

#### ImportResult

```python
@dataclass
class ImportResult:
    success: bool                   # Overall success
    session: ImportSession          # Import session
    total_files: int                # Total files in session
    processed_files: int            # Successfully processed
    failed_files: int               # Failed to process
    skipped_files: int              # Skipped files
    duplicate_count: int            # Number of duplicates
    total_size_bytes: int           # Total size of files
    duration_seconds: float         # Total duration
    error_message: Optional[str]    # Error message if failed
```

## Performance Characteristics

### File Hashing

- Leverages FastHasher for optimal performance
- xxHash128 is 10-20x faster than MD5
- Files under 100MB: < 1 second hash time
- Files 100-500MB: < 3 seconds hash time
- Files over 500MB: < 5 seconds hash time

### File Copying

- 1MB chunk size for efficient I/O
- Progress reported at reasonable intervals
- Memory-efficient streaming (constant memory usage)
- Typical throughput: 50-200 MB/s (depends on disk)

### Memory Usage

- Constant memory usage during file operations
- No full file loading into memory
- Efficient cleanup of resources
- Memory stable over repeated operations
- Tested with 10+ consecutive import sessions

## Error Handling

### Common Errors

1. **Root Directory Not Configured**
   - Error: "Directory is not a configured root folder"
   - Solution: Add directory to RootFolderManager before importing

2. **Permission Denied**
   - Error: "No write permission for directory"
   - Solution: Check directory permissions

3. **File Not Found**
   - Error: "File not found: [path]"
   - Solution: Verify file exists and is accessible

4. **Disk Space Insufficient**
   - Error during file copy
   - Solution: Check available disk space

### Recovery Strategies

1. **Automatic Rollback**: Failed sessions can be rolled back automatically
2. **Partial Success**: Completed files remain even if some fail
3. **Error Logging**: All errors logged with full context
4. **User Feedback**: Clear error messages for user action

## Logging

All operations logged in JSON format:

```json
{
  "event": "file_processed",
  "timestamp": 1698765432.123,
  "file": "model.stl",
  "hash": "abc123...",
  "mode": "leave_in_place",
  "managed_path": "/path/to/model.stl"
}
```

Log events include:
- `file_manager_initialized`
- `validating_root_directory`
- `root_directory_valid`
- `starting_import_session`
- `import_session_started`
- `calculating_file_hash`
- `copying_file`
- `file_processed`
- `rolling_back_session`
- `rollback_completed`
- `import_session_completed`

## Testing

### Unit Tests

Run unit tests:
```bash
python -m pytest tests/test_import_file_manager.py -v
```

Tests cover:
- Root directory validation
- File management modes
- Duplicate detection
- Progress tracking
- Cancellation support
- Error handling
- Memory stability
- Rollback functionality

### Integration Tests

Integration tests verify:
- Complete import workflows
- Multi-file imports
- Database integration
- Error recovery

## Best Practices

### 1. Validate Before Import

```python
# Always validate root directory for keep_organized mode
is_valid, error = manager.validate_root_directory(root_dir, mode)
if not is_valid:
    # Handle error
    pass
```

### 2. Handle Errors Gracefully

```python
# Wrap imports in try/except
try:
    # Import operations
    pass
except Exception as e:
    # Rollback and handle error
    manager.rollback_session(session)
```

### 3. Provide Progress Feedback

```python
# Always provide progress callbacks for long operations
def progress(msg, pct):
    # Update UI
    pass

manager.process_file(file_info, session, progress_callback=progress)
```

### 4. Check for Duplicates

```python
# Build hash dictionary before importing
existing_hashes = build_hash_dict_from_database()

# Check each file
is_dup, existing = manager.check_duplicate(hash, existing_hashes)
```

### 5. Use Cancellation Tokens

```python
# Provide cancellation for long operations
token = CancellationToken()
manager.process_file(file_info, session, cancellation_token=token)
```

## Troubleshooting

### Import Session Fails to Start

**Symptoms:**
- start_import_session returns False
- Error message provided

**Solutions:**
1. Check if files exist and are accessible
2. Verify root directory is configured (for keep_organized mode)
3. Check file permissions
4. Review error message for specific issue

### Files Not Copying

**Symptoms:**
- process_file fails during copy
- Status stuck at "copying"

**Solutions:**
1. Check available disk space
2. Verify write permissions on target directory
3. Check if antivirus is blocking operations
4. Review logs for specific error

### High Memory Usage

**Symptoms:**
- Memory increases during import
- System becomes slow

**Solutions:**
1. Process files in smaller batches
2. Check for memory leaks (run tests)
3. Monitor with tracemalloc
4. Report issue if consistent

### Rollback Fails

**Symptoms:**
- rollback_session returns False
- Files not cleaned up

**Solutions:**
1. Check file permissions
2. Verify files not locked by other processes
3. Manual cleanup may be needed
4. Review logs for specific failures

## Future Enhancements

Potential improvements:
1. **Parallel Processing**: Process multiple files concurrently
2. **Smart Caching**: Cache file information for repeated imports
3. **Move Support**: Option to move instead of copy
4. **Custom Organization**: User-defined directory structures
5. **Import Profiles**: Save/load import configurations
6. **Batch Operations**: Import entire directories recursively

## Support

For issues, questions, or contributions:
1. Check this documentation
2. Review unit tests for examples
3. Check logs for detailed error information
4. Report issues with reproduction steps

## License

Part of Digital Workshop - See main project license.