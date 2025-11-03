# DWW Import Function - Complete Guide

## Overview

The DWW Import function allows users to import previously exported DWW (Digital Wood Works) projects back into Digital Workshop. The import process includes automatic integrity verification, thumbnail extraction, and metadata restoration.

## Features

✅ **File Selection**: Browse and select DWW files to import
✅ **Integrity Verification**: Automatic cryptographic verification before import
✅ **Preview Information**: Shows project details before importing
✅ **Thumbnail Extraction**: Restores model thumbnails from archive
✅ **Metadata Restoration**: Preserves file metadata and attributes
✅ **Duplicate Detection**: Prevents overwriting existing projects
✅ **Progress Tracking**: Real-time import progress updates
✅ **Error Handling**: Comprehensive error messages and logging

## User Interface

### Import DWW Button

Located in the Project Manager panel alongside other project management buttons:
- **New Project** - Create a new project
- **Import Library** - Import from folder
- **Refresh** - Refresh project list
- **Delete** - Delete selected project
- **Export as DWW** - Export to DWW format
- **Import DWW** - Import from DWW file ← NEW

### Import Workflow

```
1. Click "Import DWW" button
   ↓
2. Select DWW file from file browser
   ↓
3. System reads project information
   ↓
4. Preview dialog shows project details
   ↓
5. User confirms import
   ↓
6. Enter project name (or use default)
   ↓
7. System checks for duplicates
   ↓
8. Extract files to temporary directory
   ↓
9. Verify integrity with cryptographic hash
   ↓
10. Import files as new project
    ↓
11. Extract and restore thumbnails
    ↓
12. Success message with file count
```

## Step-by-Step Instructions

### Step 1: Open Import Dialog

Click the **"Import DWW"** button in the Project Manager panel.

### Step 2: Select DWW File

A file browser dialog will open. Navigate to your DWW file and select it.

**Supported file types:**
- `.dww` - Digital Wood Works format (recommended)
- `*` - All files (if DWW file has different extension)

### Step 3: Review Project Information

A preview dialog will show:
- **Project Name**: Original project name
- **File Count**: Number of files in the project
- **Created Date**: When the project was originally created

Example:
```
Import DWW Project

Project: My Woodworking Project
Files: 15
Created: 2024-01-15T10:30:00

Proceed with import?
```

### Step 4: Confirm Import

Click **"Yes"** to proceed or **"No"** to cancel.

### Step 5: Enter Project Name

A dialog will ask for the project name. You can:
- Use the original project name (default)
- Enter a new name
- Leave blank to cancel

### Step 6: Automatic Processing

The system will:
1. Check for duplicate project names
2. Extract files to temporary directory
3. Verify file integrity with cryptographic hash
4. Import files as a new project
5. Extract and restore thumbnails
6. Update the project tree

### Step 7: Completion

A success message will show:
```
Import Complete

Project 'My Woodworking Project' imported successfully with 15 files.
```

The imported project will appear in the Project Manager tree with all files organized by category.

## What Gets Imported

### Files
- All project files (STL, OBJ, STEP, NC, GCODE, CSV, XLSX, PDF, DOCX, TXT, MD)
- Organized by category (Models, Gcode, Cut Lists, Cost Sheets, Documents, Other)

### Thumbnails
- Model preview images
- Restored to thumbnails directory
- Automatically linked to models

### Metadata
- File information (names, sizes, hashes)
- Timestamps (created, modified)
- File attributes and properties

### Integrity Data
- Cryptographic verification
- Ensures no file corruption
- Automatic validation before import

## Error Handling

### "Could not read DWW file information"
- DWW file may be corrupted
- File may not be a valid DWW archive
- Try re-exporting the project

### "Integrity verification failed"
- File was corrupted during transfer
- Download/copy the file again
- Ask sender to re-export

### "Project 'Name' already exists"
- A project with that name already exists
- Enter a different project name
- Or delete the existing project first

### "Failed to import project files"
- Some files may be inaccessible
- Check file permissions
- Ensure sufficient disk space
- Try importing again

## Technical Details

### Import Process

1. **File Selection**: User selects DWW file
2. **Info Retrieval**: Read manifest without extraction
3. **Preview**: Display project information
4. **Confirmation**: User confirms import
5. **Naming**: User provides project name
6. **Duplicate Check**: Verify name doesn't exist
7. **Extraction**: Extract to temporary directory
8. **Verification**: Verify cryptographic hash
9. **Import**: Import files as new project
10. **Thumbnails**: Extract and restore thumbnails
11. **Cleanup**: Remove temporary files
12. **Refresh**: Update project tree

### Integrity Verification

- **Algorithm**: SHA256
- **Salt**: 32-byte random value
- **Verification**: Automatic before import
- **Failure**: Import aborted if verification fails

### Temporary Directory

- Created automatically during import
- Cleaned up after import completes
- Used for file extraction and verification
- Prevents conflicts with existing files

## Best Practices

1. **Verify Source**: Ensure DWW file is from trusted source
2. **Check Space**: Ensure sufficient disk space for import
3. **Unique Names**: Use descriptive project names
4. **Backup**: Keep original DWW files as backup
5. **Verify Import**: Check that all files imported correctly

## Troubleshooting

### Import Hangs or Takes Too Long
- Large projects may take time to import
- Check system resources
- Try importing smaller projects first
- Restart application if needed

### Thumbnails Not Showing
- Thumbnails may not have been in original export
- Re-export project with thumbnail option enabled
- Manually add thumbnails to models

### Files Missing After Import
- Check project tree for all files
- Verify file count matches preview
- Check application logs for errors
- Try importing again

## API Usage

### Python Code Example

```python
from src.core.export.dww_import_manager import DWWImportManager
from src.core.database.database_manager import get_database_manager

# Get database manager
db_manager = get_database_manager()

# Create import manager
import_manager = DWWImportManager(db_manager)

# Get project info without extraction
success, manifest = import_manager.get_dww_info("/path/to/project.dww")

if success:
    print(f"Project: {manifest['project']['name']}")
    print(f"Files: {manifest['file_count']}")

# Import project
success, message, manifest = import_manager.import_project(
    dww_path="/path/to/project.dww",
    import_dir="/path/to/import",
    verify_integrity=True,
    import_thumbnails=True
)

if success:
    print("Import successful!")
else:
    print(f"Import failed: {message}")
```

## Related Documentation

- `docs/DWW_FORMAT_SPECIFICATION.md` - Technical format details
- `docs/DWW_USER_GUIDE.md` - General DWW usage guide
- `docs/DWW_ENHANCEMENT_SUMMARY.md` - Enhancement details
- `docs/DWW_IMPLEMENTATION_SUMMARY.md` - Implementation overview

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Verify DWW file integrity
4. Contact support with error messages

