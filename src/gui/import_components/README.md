# Import Components Package

Comprehensive UI components for the 3D model import process.

## Components

### ImportDialog

Main dialog for importing 3D models with full-featured UI:

- **File Selection**: Drag-and-drop support for files and folders
- **File Management**: "Keep Organized" vs "Leave in Place" modes
- **Progress Tracking**: Multi-stage progress with real-time updates
- **Background Processing**: Thumbnails, analysis, and hashing
- **Cancellation**: Safe cancellation at any point
- **Results Summary**: Detailed import statistics

### ImportWorker

Background thread worker that handles all import operations:

- Non-blocking import processing
- Progress signal emissions
- Cancellation support
- Service integration (FileManager, ThumbnailService, AnalysisService)

## Quick Start

```python
from src.gui.import_components import ImportDialog

# Create and show dialog
dialog = ImportDialog(parent=main_window)

if dialog.exec() == ImportDialog.Accepted:
    result = dialog.get_import_result()
    print(f"Imported {result.processed_files} files")
```

## Features

### File Selection

- **Manual Selection**: Browse for files or folders
- **Drag-and-Drop**: Drag files/folders directly onto dialog
- **Supported Formats**: STL, OBJ, STEP, 3MF, PLY
- **Batch Import**: Import multiple files at once
- **File List Management**: Add, remove, clear files

### File Management Modes

#### Keep Organized Mode
- Copies files to managed directory
- Organized by file type
- Hash-based naming to prevent conflicts
- Requires root directory selection

#### Leave in Place Mode
- Tracks files in original locations
- No file copying
- Best for project-based workflows

### Progress Tracking

**Multi-Stage Progress:**
1. Validation - File and settings validation
2. Hashing - Fast hash calculation for deduplication
3. Copying - File copying (organized mode only)
4. Thumbnails - Thumbnail generation
5. Analysis - Background geometry analysis

**Progress Displays:**
- Overall progress bar (all files)
- Current file progress bar
- Stage indicator with elapsed time
- Detailed progress log with timestamps

### Background Services

**FastHasher Integration:**
- xxHash128 for optimal performance
- Progress callbacks during hashing
- Cancellation support

**ImportFileManager Integration:**
- File validation and management
- Session tracking for rollback
- Duplicate detection
- Error recovery

**ImportThumbnailService Integration:**
- Hash-based thumbnail naming
- Cache management
- Progressive generation
- VTK offscreen rendering

**ImportAnalysisService Integration:**
- Background geometry analysis
- Non-blocking analysis
- Detailed geometry metrics
- Batch processing support

## Architecture

```
ImportDialog (QDialog)
    │
    ├── UI Components
    │   ├── File Selection Section
    │   │   ├── File list widget
    │   │   ├── Add files/folder buttons
    │   │   └── Drag-and-drop support
    │   │
    │   ├── Options Section
    │   │   ├── File management mode radio buttons
    │   │   ├── Root directory selection
    │   │   ├── Thumbnail generation checkbox
    │   │   └── Background analysis checkbox
    │   │
    │   └── Progress Section
    │       ├── Overall progress bar
    │       ├── File progress bar
    │       ├── Stage indicator
    │       └── Progress log
    │
    └── ImportWorker (QThread)
        ├── ImportFileManager
        │   └── FastHasher
        ├── ImportThumbnailService
        │   └── ThumbnailGenerator
        └── ImportAnalysisService
            └── Parser (STL, OBJ, etc.)
```

## Error Handling

**File Access Errors:**
- Permission denied → Skip file, continue
- File not found → Warning, skip file
- Disk full → Error, stop import

**Validation Errors:**
- Invalid root directory → Error message
- No write permission → Error message
- Not configured root → Error message

**Processing Errors:**
- Hash failure → Warning, skip file
- Thumbnail failure → Warning, continue
- Analysis failure → Warning, continue

## Performance

**Responsive UI:**
- All heavy operations in background thread
- Never blocks UI thread
- Smooth progress updates
- Immediate user interaction

**Memory Efficient:**
- Stream-based file processing
- Chunked reading (1MB chunks)
- Automatic cleanup
- Resource management

**Fast Processing:**
- Files < 100MB: Hash in < 1s
- Files 100-500MB: Hash in < 3s
- Files > 500MB: Hash in < 5s
- Parallel processing support

## Accessibility

**Keyboard Navigation:**
- Full keyboard accessibility
- Tab order follows logical flow
- Keyboard shortcuts supported

**Screen Reader Support:**
- ARIA labels for all controls
- Progress announcements
- Error message accessibility

**Visual Accessibility:**
- High contrast support
- Clear visual hierarchy
- Adequate font sizes
- Tooltips for all buttons

## Testing

Run the test script:

```bash
python test_import_dialog.py
```

## Documentation

See [`IMPORT_DIALOG_GUIDE.md`](../../../documentation/IMPORT_DIALOG_GUIDE.md) for:
- Detailed usage examples
- Integration guide
- Troubleshooting
- Best practices

## Requirements

- PySide6 >= 6.0.0
- Python >= 3.8
- Backend services:
  - FastHasher
  - ImportFileManager
  - ImportThumbnailService
  - ImportAnalysisService

## License

Copyright (c) 2024 3D Model Manager Project