# Grid View Hover Preview Feature

## Overview

Added a hover preview feature to the Grid view in the Model Library. When you hover over a model thumbnail in the grid, a larger 512x512 preview image appears after a short delay.

## How It Works

### Components

**1. GridPreviewDelegate** (`src/gui/model_library_components/grid_preview_delegate.py`)
   - Custom `QStyledItemDelegate` for the grid view
   - Handles mouse hover events
   - Loads and displays larger preview images
   - Manages preview positioning and rendering

**2. Integration** (`src/gui/model_library.py`)
   - Grid view now uses `GridPreviewDelegate` instead of default delegate
   - Automatically applied when grid view is created

### Features

- **Hover Detection**: Detects when mouse hovers over a grid item
- **Delayed Display**: Preview appears after 500ms delay (prevents flickering)
- **Smart Positioning**: Preview appears to the right of the item, or to the left if not enough space
- **Automatic Scaling**: Preview image is scaled to fit the 512x512 preview area
- **Semi-transparent Background**: Dark background with border for better visibility
- **Smooth Transitions**: Uses `Qt.SmoothTransformation` for high-quality scaling

### Preview Size

- **Grid Thumbnails**: 128x128 (current size)
- **Hover Preview**: 512x512 (4x larger)
- **Preview Delay**: 500ms before showing

### Positioning Logic

The preview is positioned intelligently:

1. **Default**: To the right of the hovered item
2. **If off-screen right**: Positioned to the left of the item
3. **If off-screen bottom**: Adjusted upward to fit in viewport

This ensures the preview is always visible and doesn't go off-screen.

## User Experience

### Before
- Grid view shows small 128x128 thumbnails
- Hard to see details in small thumbnails
- Need to open model to see full preview

### After
- Grid view shows small 128x128 thumbnails (same as before)
- Hover over any thumbnail to see 512x512 preview
- Preview appears after 500ms delay
- Preview automatically positioned to avoid going off-screen
- No need to open model to preview

## Technical Details

### Event Handling

The delegate intercepts mouse events:
- `MouseMove`: Triggers preview loading with 500ms delay
- `Leave`: Clears preview when mouse leaves item

### Preview Loading

When preview timer fires:
1. Gets model ID from the item
2. Queries database for model data
3. Loads thumbnail image from disk
4. Caches pixmap for rendering
5. Triggers viewport repaint

### Performance Considerations

- **Lazy Loading**: Preview only loads when hovering (not on grid load)
- **Caching**: Preview pixmap cached while hovering
- **Delayed Loading**: 500ms delay prevents loading on quick mouse movements
- **Efficient Rendering**: Uses Qt's built-in scaling and painting

## Code Structure

```python
class GridPreviewDelegate(QStyledItemDelegate):
    PREVIEW_SIZE = 512
    PREVIEW_DELAY_MS = 500
    
    def paint(painter, option, index):
        # Draw default item
        # Draw preview if hovering
    
    def editorEvent(event, model, option, index):
        # Handle mouse move/leave events
    
    def _on_preview_timer():
        # Load preview image when timer fires
```

## Future Enhancements

Possible improvements:
- Configurable preview size (currently 512x512)
- Configurable delay (currently 500ms)
- Preview animation/fade-in effect
- Keyboard shortcut to show/hide previews
- Preview for multiple selected items
- Thumbnail generation on-demand for larger sizes

## Files Modified

- `src/gui/model_library.py` - Added delegate integration
- `src/gui/model_library_components/grid_preview_delegate.py` - New file with delegate implementation

## Testing

To test the feature:
1. Open the Model Library
2. Switch to Grid view
3. Hover over any model thumbnail
4. After 500ms, a larger preview should appear
5. Move mouse away to hide preview
6. Move to another item to show its preview

