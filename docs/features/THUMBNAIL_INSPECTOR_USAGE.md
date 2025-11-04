# Thumbnail Inspector - User Guide

## Quick Start

### Opening the Inspector

1. **Select a Model** in the Model Library
2. **View Thumbnail** in the Metadata Editor's "Preview Image" section
3. **Double-Click** on the thumbnail to open the inspector

### Inspector Controls

```
┌─────────────────────────────────────────────────────────────┐
│  Thumbnail Inspector                                    [X]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                                                               │
│                    [Full Resolution Image]                   │
│                                                               │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ [Zoom In] [Zoom Out] [Reset] [Fit] ... Zoom: 100% | [Close] │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Zoom Controls

| Button | Action | Keyboard |
|--------|--------|----------|
| **Zoom In (+)** | Increase zoom by 20% | `+` or `=` |
| **Zoom Out (-)** | Decrease zoom by 20% | `-` |
| **Reset Zoom** | Return to 100% | `0` |
| **Fit to Window** | Auto-fit to dialog | (Button only) |

### Information Display

The info label shows:
- **Zoom Level**: Current zoom percentage (e.g., "100%")
- **Image Size**: Original dimensions (e.g., "1080x1080px")
- **File Size**: Thumbnail file size in KB (if available)

Example: `Zoom: 150% | Size: 1080x1080px | File: 2.5KB`

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `+` or `=` | Zoom in |
| `-` | Zoom out |
| `0` | Reset zoom to 100% |
| `Esc` | Close inspector |

## Workflow Examples

### Example 1: Inspect Model Quality

1. Double-click thumbnail to open inspector
2. Click "Fit to Window" to see full image
3. Use "Zoom In" to inspect details
4. Press `Esc` to close

### Example 2: Compare Zoom Levels

1. Open inspector
2. Start at 100% (Reset Zoom)
3. Zoom in to 150% to see details
4. Zoom out to 50% to see overall composition
5. Use "Fit to Window" to see full image

### Example 3: Quick Inspection

1. Double-click thumbnail
2. Press `+` several times to zoom in
3. Press `-` to zoom out
4. Press `Esc` to close

## Tips & Tricks

### Smooth Zooming
- Use keyboard shortcuts (`+`, `-`, `0`) for quick zoom control
- Click buttons for precise zoom increments

### Viewing Large Details
- Zoom in to 200-300% to inspect fine details
- Use scroll bars to pan around zoomed image

### Fitting to Window
- Click "Fit to Window" to see entire thumbnail
- Useful after zooming in to see overall composition

### Keyboard Navigation
- All controls are keyboard accessible
- Use `Esc` to quickly close without clicking

## Troubleshooting

### Inspector Won't Open
- Ensure thumbnail is loaded (not showing placeholder text)
- Try generating a new thumbnail via context menu

### Image Appears Blurry
- This is normal at high zoom levels (>200%)
- Thumbnails are 1080x1080, so extreme zoom shows pixelation

### Zoom Not Working
- Ensure you're clicking on the image area
- Try using keyboard shortcuts instead

## Technical Notes

### Thumbnail Resolution
- Thumbnails are generated at 1080x1080 pixels
- Optimal viewing at 100% zoom
- Zoom up to 300% for detail inspection

### Performance
- Smooth scrolling for panned images
- Efficient scaling using Qt's SmoothTransformation
- No lag even at high zoom levels

### File Information
- File size shown if thumbnail file is accessible
- Size displayed in kilobytes (KB)

## Accessibility

### Keyboard Users
- All features accessible via keyboard
- Tab navigation through buttons
- Shortcuts for common actions

### Mouse Users
- Intuitive button layout
- Clear visual feedback
- Pointing hand cursor indicates interactivity

### Screen Readers
- Dialog has proper title and labels
- Buttons have descriptive text
- Info label provides context

## Related Features

- **Generate Preview**: Create thumbnail via context menu
- **AI Analysis**: Analyze thumbnail with AI
- **Metadata Editor**: Edit model information
- **Model Library**: Browse all models

## Support

For issues or feature requests:
1. Check this guide for troubleshooting
2. Verify thumbnail is properly generated
3. Try closing and reopening the inspector
4. Report persistent issues to development team

