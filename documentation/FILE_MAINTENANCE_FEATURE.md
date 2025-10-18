# File & Model Maintenance Feature

## Overview

A new **File & Model Maintenance** section has been added to the **Files** tab in the Preferences dialog. This feature allows users to force check/match files to models or regenerate thumbnails without restarting the application.

## Location

**Menu:** Edit → Preferences → Files tab → "File & Model Maintenance" section

## Features

### 1. **Recalculate File Hashes**
- Recalculates xxHash128 for all model files
- Updates the database with new hash values
- Useful when hash algorithm changes or needs verification
- **Use case:** After upgrading from BLAKE2b to xxHash

### 2. **Match Files to Models**
- Compares current file hashes with stored hashes
- Updates only models where hash has changed
- Detects if files have been modified or moved
- **Use case:** After moving model files or detecting file changes

### 3. **Regenerate Thumbnails**
- Regenerates 128×128 thumbnails for all models
- Uses hash-based naming: `{hash}_128x128.png`
- Stores thumbnails in `~/.3dmm/thumbnails/`
- **Use case:** After changing materials or rendering settings

### 4. **Full Maintenance (All)**
- Runs all three operations in sequence:
  1. Recalculate File Hashes
  2. Match Files to Models
  3. Regenerate Thumbnails
- **Use case:** Complete system maintenance and verification

## User Interface

### Operation Selection
```
Operation: [Dropdown Menu]
  - Recalculate File Hashes
  - Match Files to Models
  - Regenerate Thumbnails
  - Full Maintenance (All)
```

### Progress Tracking
- **Progress Bar:** Shows percentage completion (0-100%)
- **Status Label:** Displays current operation and count (e.g., "Hashing model 42 (42/150)")
- **Visible during operation only**

### Control Buttons
- **Start Maintenance:** Begins the selected operation
- **Cancel:** Stops the running operation (disabled when not running)

### Confirmation Dialog
Before starting, users must confirm:
```
"Start 'Operation Name' operation?

This may take some time depending on the number of models."
```

### Completion Dialog
Shows results:
```
"Operation Name completed successfully!

Processed: 150
Updated: 45
Errors: 0"
```

## Implementation Details

### New Class: `FileMaintenanceWorker`
- **Type:** QThread worker for background processing
- **Location:** `src/gui/files_tab.py`
- **Signals:**
  - `progress(int, int, str)` - current, total, message
  - `finished(dict)` - result dictionary
  - `error(str)` - error message

### Result Dictionary
```python
{
    "processed": 150,  # Total items processed
    "updated": 45,     # Items that were updated
    "errors": 0        # Items that failed
}
```

### Operations Implementation

#### Recalculate Hashes
1. Fetches all models from database
2. For each model:
   - Checks if file exists
   - Calculates xxHash128 of file content
   - Updates database with new hash
3. Tracks processed/updated/error counts

#### Match Files
1. Fetches all models from database
2. For each model:
   - Calculates current file hash
   - Compares with stored hash
   - Updates only if different
3. Detects file modifications

#### Regenerate Thumbnails
1. Fetches all models from database
2. For each model:
   - Uses ScreenshotGenerator (128×128)
   - Names file: `{hash}_128x128.png`
   - Updates database thumbnail path
3. Handles missing files gracefully

#### Full Maintenance
- Runs all three operations sequentially
- Aggregates results from each operation
- Can be cancelled at any point

## Error Handling

- **File Not Found:** Logged and counted as error, continues processing
- **Hash Calculation Failure:** Logged and counted as error
- **Thumbnail Generation Failure:** Logged and counted as error
- **Operation Cancelled:** Stops gracefully, shows partial results
- **Critical Error:** Shows error dialog with details

## Performance Considerations

- **Background Thread:** All operations run in separate thread (non-blocking UI)
- **Chunk Reading:** Files read in 8KB chunks for memory efficiency
- **Progress Updates:** Emitted after each model for responsive UI
- **Cancellation:** Can be stopped at any time

## Database Updates

Operations update the following database fields:
- `file_hash` - xxHash128 value (32 hex characters)
- `thumbnail_path` - Path to generated thumbnail PNG

## File Naming Convention

### Thumbnails
- **Format:** `{xxhash128}_{size}.png`
- **Example:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6_128x128.png`
- **Location:** `~/.3dmm/thumbnails/`
- **Self-identifying:** Hash ensures file can be matched to model even if separated

## Usage Workflow

### Scenario 1: After Upgrading Hash Algorithm
1. Open Preferences → Files tab
2. Select "Recalculate File Hashes"
3. Click "Start Maintenance"
4. Confirm operation
5. Wait for completion
6. Review results

### Scenario 2: After Moving Model Files
1. Open Preferences → Files tab
2. Select "Match Files to Models"
3. Click "Start Maintenance"
4. Confirm operation
5. System detects which files changed
6. Updates database accordingly

### Scenario 3: Complete System Maintenance
1. Open Preferences → Files tab
2. Select "Full Maintenance (All)"
3. Click "Start Maintenance"
4. Confirm operation
5. System runs all three operations
6. Review final results

## Technical Notes

- **Thread Safety:** Uses QThread for background processing
- **Database Access:** Uses existing DatabaseManager singleton
- **File Hashing:** Uses xxHash128 (32 hex character output)
- **Screenshot Generation:** Uses existing ScreenshotGenerator class
- **Material Manager:** Uses default material for thumbnails

## Future Enhancements

- Batch size configuration for large libraries
- Selective operation on specific models
- Scheduling for automatic maintenance
- Detailed operation logs/reports
- Dry-run mode to preview changes

