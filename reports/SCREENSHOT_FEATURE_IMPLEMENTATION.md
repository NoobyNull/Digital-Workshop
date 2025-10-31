# Screenshot Feature Implementation

## Overview
Added functionality to capture and save screenshots of 3D models currently displayed in the viewer to disk.

## Changes Made

### 1. **Viewer Widget Enhancement** (`src/gui/viewer_3d/viewer_widget_facade.py`)
Added `capture_screenshot()` method to the `Viewer3DWidget` class:

```python
def capture_screenshot(self, output_path: str, width: int = 1920, height: int = 1080) -> bool:
    """
    Capture a screenshot of the current viewer and save to disk.
    
    Args:
        output_path: Path to save the screenshot (e.g., '/path/to/screenshot.png')
        width: Screenshot width in pixels (default: 1920)
        height: Screenshot height in pixels (default: 1080)
    
    Returns:
        True if successful, False otherwise
    """
```

**Features:**
- Uses VTK's `vtkWindowToImageFilter` to capture the render window
- Saves to PNG format using `vtkPNGWriter`
- Configurable resolution (default 1920x1080)
- Comprehensive error handling and logging
- Returns success/failure status

### 2. **Menu Integration** (`src/gui/components/menu_manager.py`)
Added menu action "Save Screenshot of Current View" to the Tools menu:

```python
# Save current view screenshot action
save_screenshot_action = QAction("&Save Screenshot of Current View", self.main_window)
save_screenshot_action.setStatusTip("Save a screenshot of the currently displayed model")
save_screenshot_action.triggered.connect(self._save_current_screenshot)
tools_menu.addAction(save_screenshot_action)
```

Added handler method:
```python
def _save_current_screenshot(self) -> None:
    """Handle save current screenshot action."""
    if hasattr(self.main_window, '_save_current_screenshot'):
        self.main_window._save_current_screenshot()
```

### 3. **Main Window Handler** (`src/gui/main_window.py`)
Added `_save_current_screenshot()` method to handle the screenshot workflow:

**Features:**
- Validates that a model is loaded
- Opens file save dialog (defaults to Pictures folder)
- Supports PNG, JPEG, and BMP formats
- Shows success/error messages to user
- Comprehensive error handling

**Workflow:**
1. User clicks Tools > Save Screenshot of Current View
2. File save dialog opens (defaults to Pictures folder)
3. User selects location and filename
4. Screenshot is captured and saved
5. Success/error message is displayed

## Usage

### For End Users:
1. Load a 3D model in the viewer
2. Go to **Tools** menu → **Save Screenshot of Current View**
3. Choose a location and filename
4. Click Save
5. Screenshot is saved to disk

### For Developers:
```python
# Direct usage from code
viewer_widget.capture_screenshot('/path/to/screenshot.png', width=1920, height=1080)
```

## Technical Details

### VTK Pipeline:
1. `vtkWindowToImageFilter` - Captures render window to image
2. `vtkPNGWriter` - Writes image to PNG file
3. Configurable resolution and quality

### Error Handling:
- Checks if render window is available
- Validates file path
- Catches and logs all exceptions
- Provides user-friendly error messages

### File Format Support:
- PNG (default, lossless)
- JPEG (compressed)
- BMP (uncompressed)

## Integration Points

### Existing Features:
- Uses existing VTK scene manager
- Integrates with current viewer widget
- Works with all loaded models
- Respects current camera position and lighting

### Related Features:
- **Batch Screenshot Generation** (`src/gui/batch_screenshot_worker.py`) - For generating thumbnails of all models
- **GCode Previewer Export** (`src/gui/gcode_previewer_components/export_manager.py`) - For exporting GCode preview screenshots

## Testing

The implementation includes:
- Proper error handling for missing render window
- Validation of file paths
- User feedback via message boxes
- Logging of all operations

## Future Enhancements

Possible improvements:
1. Add screenshot resolution presets (720p, 1080p, 4K)
2. Add watermark/annotation support
3. Add batch screenshot export for multiple views
4. Add screenshot history/gallery
5. Add screenshot comparison tools
6. Add screenshot metadata (model name, date, settings)

