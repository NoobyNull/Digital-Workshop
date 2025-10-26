# Import Dialog User Guide

## Overview

The ImportDialog provides a comprehensive user interface for importing 3D model files into your library with advanced features including:

- **File Selection**: Drag-and-drop support for files and folders
- **File Management**: Choose between organized storage or leave-in-place
- **Progress Tracking**: Real-time multi-stage progress updates
- **Background Processing**: Thumbnail generation and model analysis
- **Cancellation Support**: Cancel operations at any time
- **Results Summary**: Detailed import statistics

## Usage

### Basic Usage

```python
from src.gui.import_components import ImportDialog

# Create and show the dialog
dialog = ImportDialog(parent=main_window)

if dialog.exec() == ImportDialog.Accepted:
    result = dialog.get_import_result()
    print(f"Successfully imported {result.processed_files} files")
```

### With Root Folder Manager

```python
from src.core.root_folder_manager import RootFolderManager
from src.gui.import_components import ImportDialog

# Pass root folder manager for organized mode
root_manager = RootFolderManager.get_instance()
dialog = ImportDialog(parent=main_window, root_folder_manager=root_manager)

if dialog.exec() == ImportDialog.Accepted:
    result = dialog.get_import_result()
    # Process results...
```

## Features

### 1. File Selection

**Add Individual Files:**
- Click "Add Files..." button
- Or drag and drop files directly onto the dialog

**Add Entire Folders:**
- Click "Add Folder..." button
- Or drag and drop folders directly onto the dialog
- Automatically finds all 3D model files recursively

**Supported Formats:**
- STL (.stl)
- OBJ (.obj)
- STEP (.step, .stp)
- 3MF (.3mf)
- PLY (.ply)

**File List Management:**
- View all selected files with size information
- Remove individual files
- Clear all files
- Files display full path on hover

### 2. File Management Modes

#### Keep Organized Mode
- **Purpose**: Application manages file locations with organized directory structure
- **Behavior**: 
  - Copies files to a managed root directory
  - Organizes by file type (STL_Files, OBJ_Files, etc.)
  - Uses hash-based filenames to prevent conflicts
  - Requires root directory selection
- **Best For**: Central library management

#### Leave in Place Mode
- **Purpose**: Track files in their original locations
- **Behavior**:
  - No file copying
  - Tracks original file paths
  - Monitors for file changes
- **Best For**: Working with files in project folders

### 3. Processing Options

#### Generate Thumbnails
- **Enabled by default**
- Generates preview thumbnails during import
- Uses hash-based naming for deduplication
- Stored in AppData or custom location
- Skips generation if thumbnail already exists

#### Run Background Analysis
- **Enabled by default**
- Analyzes model geometry after import
- Runs in background thread
- Extracts:
  - Triangle and vertex counts
  - Bounding box dimensions
  - Volume and surface area
  - Mesh quality metrics

### 4. Progress Tracking

The dialog provides detailed progress information across multiple stages:

**Overall Progress:**
- Shows total files processed vs total files
- Overall percentage completion
- Visual progress bar

**Current File Progress:**
- Individual file being processed
- Stage-specific progress (hashing, copying, etc.)
- File-level percentage completion

**Stage Indicator:**
- Current import stage
- Elapsed time
- Stage-specific messages

**Progress Stages:**
1. **Validation**: Validating files and settings
2. **Hashing**: Calculating file hashes for deduplication
3. **Copying**: Copying files (organized mode only)
4. **Thumbnails**: Generating preview thumbnails
5. **Analysis**: Queueing background analysis

**Progress Log:**
- Timestamped messages
- Real-time updates
- Auto-scrolling to latest message
- Detailed error information

### 5. Cancellation

**During Import:**
- Click "Cancel" button
- Confirmation dialog appears
- Files already processed remain imported
- Safe cancellation of all operations

**Cancellation Propagation:**
- Cancels file hashing
- Stops file copying
- Aborts thumbnail generation
- Stops analysis operations

### 6. Results Summary

After import completion, the dialog shows:

**Import Statistics:**
- Total files attempted
- Successfully processed files
- Failed files
- Skipped files (duplicates)
- Duplicate count
- Total size imported
- Duration

**Result Object:**
```python
result = dialog.get_import_result()

# Access result properties
result.success           # Overall success status
result.total_files       # Total files attempted
result.processed_files   # Successfully imported
result.failed_files      # Failed imports
result.skipped_files     # Skipped (duplicates)
result.duplicate_count   # Duplicates detected
result.total_size_bytes  # Total size in bytes
result.duration_seconds  # Import duration
result.session           # Full session details
```

## Architecture

### Component Integration

```
ImportDialog
    ├── ImportWorker (QThread)
    │   ├── ImportFileManager
    │   │   ├── FastHasher (file hashing)
    │   │   └── RootFolderManager (path validation)
    │   ├── ImportThumbnailService
    │   │   └── ThumbnailGenerator
    │   └── ImportAnalysisService
    │       └── STLParser (geometry analysis)
    └── UI Components
        ├── File Selection Section
        ├── Options Section
        └── Progress Section
```

### Background Processing

**ImportWorker Thread:**
- Runs all import operations in background
- Prevents UI blocking
- Emits progress signals
- Supports cancellation
- Handles errors gracefully

**Signal Flow:**
```
ImportWorker → ImportDialog
    • stage_changed: Import stage updates
    • file_progress: Individual file progress
    • overall_progress: Total progress
    • import_completed: Success result
    • import_failed: Error message
```

## Error Handling

### Common Errors

**File Access Errors:**
- Permission denied
- File not found
- Disk full
- **Recovery**: Skip file, continue with others

**Validation Errors:**
- Invalid root directory
- No write permission
- Not a configured root folder
- **Recovery**: Show error message, require correction

**Processing Errors:**
- Hash calculation failure
- Thumbnail generation failure
- Analysis errors
- **Recovery**: Log warning, continue import

**User Errors:**
- No files selected
- Missing root directory
- **Recovery**: Show warning, prevent import

### Error Display

**During Import:**
- Errors logged in progress text
- Individual file failures don't stop batch
- Final summary shows all errors

**Critical Errors:**
- Modal error dialog
- Detailed error message
- Import stops
- Controls re-enabled

## Performance Considerations

### Memory Management

**File Processing:**
- Chunked reading (1MB chunks)
- Stream-based hashing
- Efficient file copying
- Automatic cleanup

**Thumbnail Generation:**
- Memory-efficient VTK rendering
- Garbage collection after each thumbnail
- Cache management
- Progressive generation

### Responsiveness

**UI Thread:**
- Never blocked during import
- All heavy operations in worker thread
- Smooth progress updates
- Immediate user interaction

**Progress Updates:**
- Throttled to prevent UI flooding
- Meaningful progress increments
- Batch updates for efficiency

### Large File Handling

**Optimization:**
- Adaptive chunk sizes based on file size
- Progressive loading
- Memory monitoring
- Resource cleanup

**Performance Targets:**
- Files < 100MB: Hash in < 1 second
- Files 100-500MB: Hash in < 3 seconds
- Files > 500MB: Hash in < 5 seconds
- UI remains responsive throughout

## Accessibility

**Keyboard Navigation:**
- Tab order follows logical flow
- All buttons keyboard accessible
- Dialog shortcuts supported

**Screen Reader Support:**
- Descriptive labels for all controls
- Progress announcements
- Error message accessibility

**Visual Accessibility:**
- Clear visual hierarchy
- High contrast support
- Adequate font sizes
- Icon tooltips

## Best Practices

### For Developers

**Integration:**
```python
# Always provide parent for proper dialog ownership
dialog = ImportDialog(parent=self)

# Check dialog result before accessing data
if dialog.exec() == ImportDialog.Accepted:
    result = dialog.get_import_result()
    if result and result.success:
        # Process successful import
        pass
```

**Error Handling:**
```python
try:
    dialog = ImportDialog(parent=self)
    if dialog.exec() == ImportDialog.Accepted:
        result = dialog.get_import_result()
        # Handle result...
except Exception as e:
    logger.error(f"Import dialog error: {e}")
    # Show error to user
```

### For Users

**Before Import:**
1. Select appropriate file management mode
2. Configure root directory for organized mode
3. Review processing options
4. Check available disk space

**During Import:**
1. Monitor progress log for issues
2. Don't close application during import
3. Use cancel if needed

**After Import:**
1. Review import summary
2. Check for any failed files
3. Verify imported models in library

## Troubleshooting

### Import Fails to Start

**Symptom**: Import button disabled
**Solutions**:
- Ensure files are selected
- Select root directory (organized mode)
- Check file accessibility

### Slow Import Performance

**Symptom**: Import takes longer than expected
**Solutions**:
- Disable thumbnail generation for speed
- Disable background analysis
- Check disk speed (SSD recommended)
- Reduce concurrent operations

### Thumbnail Generation Fails

**Symptom**: Some thumbnails not generated
**Solutions**:
- Check file format support
- Verify VTK installation
- Check disk space
- Review error log

### High Memory Usage

**Symptom**: Application uses excessive memory
**Solutions**:
- Import smaller batches
- Disable background analysis
- Restart application between large imports

## Examples

### Example 1: Basic Import

```python
from src.gui.import_components import ImportDialog

def import_models(parent):
    """Simple import workflow."""
    dialog = ImportDialog(parent)
    
    if dialog.exec() == ImportDialog.Accepted:
        result = dialog.get_import_result()
        
        if result.success:
            print(f"Imported {result.processed_files} models")
            return True
    
    return False
```

### Example 2: Import with Custom Settings

```python
from src.gui.import_components import ImportDialog
from src.core.root_folder_manager import RootFolderManager

def import_with_settings(parent, root_dir):
    """Import with pre-configured settings."""
    root_manager = RootFolderManager.get_instance()
    
    dialog = ImportDialog(parent, root_manager)
    
    # Pre-configure if needed
    # (User can still modify in dialog)
    
    if dialog.exec() == ImportDialog.Accepted:
        result = dialog.get_import_result()
        return result
    
    return None
```

### Example 3: Batch Import with Progress Callback

```python
from src.gui.import_components import ImportDialog

def batch_import_models(parent, file_lists):
    """Import multiple batches with tracking."""
    total_imported = 0
    total_failed = 0
    
    for files in file_lists:
        dialog = ImportDialog(parent)
        
        # Pre-add files programmatically if needed
        # dialog._add_files(files)
        
        if dialog.exec() == ImportDialog.Accepted:
            result = dialog.get_import_result()
            total_imported += result.processed_files
            total_failed += result.failed_files
    
    print(f"Total: {total_imported} imported, {total_failed} failed")
    return total_imported, total_failed
```

## Integration Points

### Main Window Integration

```python
# In main window menu/toolbar
def on_import_action(self):
    """Handle import action from menu."""
    from src.gui.import_components import ImportDialog
    
    dialog = ImportDialog(self, self.root_folder_manager)
    
    if dialog.exec() == ImportDialog.Accepted:
        result = dialog.get_import_result()
        
        # Refresh library view
        self.refresh_library()
        
        # Show notification
        self.show_import_notification(result)
```

### Database Integration

The ImportDialog automatically integrates with:
- `ImportFileManager` for file tracking
- `FastHasher` for duplicate detection
- `ImportThumbnailService` for thumbnail storage
- `ImportAnalysisService` for geometry data

No additional database code needed in most cases.

## Future Enhancements

Potential improvements for future versions:

1. **Batch Import Templates**: Save/load import settings
2. **Import Scheduling**: Schedule imports for later
3. **Network Import**: Import from URLs or network shares
4. **Format Conversion**: Auto-convert during import
5. **Smart Duplicate Handling**: Advanced duplicate resolution
6. **Import History**: View past import sessions
7. **Metadata Extraction**: Extract metadata during import
8. **Cloud Storage**: Import from cloud providers

## Support

For issues or questions:
1. Check this guide
2. Review error logs
3. Consult IMPORT_PROCESS_ARCHITECTURE.md
4. Report bugs with log files