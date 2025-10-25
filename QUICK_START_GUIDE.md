# VTK G-code Viewer - Quick Start Guide

## Getting Started

### 1. Open the G-code Previewer
- Launch Digital Workshop
- Click the "G Code Previewer" tab in the main window

### 2. Load a G-code File
- Click "Load G-code File" button
- Select a G-code file (.nc, .gcode, .gco, or .tap)
- Watch the file load progressively in the 3D viewer

## 3D Viewer Controls

### Mouse Controls
| Action | Control |
|--------|---------|
| Rotate | Left-click and drag |
| Pan | Middle-click and drag |
| Zoom | Right-click and drag OR mouse wheel |

### Toolbar Buttons
| Button | Action |
|--------|--------|
| Fit All | Auto-fit all geometry in view |
| Front | Front view (Y-Z plane) |
| Top | Top view (X-Y plane) |
| Side | Side view (X-Z plane) |
| Isometric | Isometric 3D view |
| Reset | Return to initial camera state |

## Timeline & Playback

### Timeline Tab
1. **Slider**: Drag to jump to any frame
2. **Play Button**: Start playback
3. **Pause Button**: Pause playback
4. **Stop Button**: Stop and reset to frame 0
5. **Speed Control**: Adjust playback speed (10% - 500%)
6. **Frame Counter**: Shows current frame / total frames

### Statistics Display
- **Rapid Moves**: Count of G00 commands
- **Cutting Moves**: Count of G01 commands
- **Arc Moves**: Count of G02/G03 commands
- **Tool Changes**: Count of M06 commands

## Interactive Loader Tab

### Loading Progress
- **Progress Bar**: Shows loading percentage
- **Status Message**: Current loading status
- **Cancel Button**: Stop loading (if available)

### Features
- Progressive chunk-based loading
- Real-time visualization updates
- Watch the toolpath build as it loads
- Cancellable at any time

## Statistics Tab

### Toolpath Statistics
- Total move count
- Rapid move count
- Cutting move count
- Arc move count
- Tool change count
- File size and line count

### Moves Table
- Line number
- Move type (Rapid, Cutting, Arc, etc.)
- X, Y, Z coordinates
- Feed rate
- Spindle speed

## Editor Tab

### Editing G-code
1. Click "Editor" tab
2. Edit the G-code text
3. Click "Reload" button
4. Visualization updates automatically

### Features
- Syntax highlighting
- Line numbers
- Real-time preview updates
- Undo/Redo support

## Visualization Controls

### Visualization Mode
- **Default**: Standard polyline visualization
- **Feed Rate**: Color-coded by feed rate
- **Spindle Speed**: Color-coded by spindle speed

### Layer Selection
- Select specific layers to view
- "Show All" button to display all layers

### Export Options
- **Screenshot**: Export current view as image
- **Video**: Export playback as video

## Color Legend

| Color | Move Type | Meaning |
|-------|-----------|---------|
| Orange | Rapid | Fast positioning (G00) |
| Green | Cutting | Cutting operation (G01) |
| Cyan | Arc | Circular interpolation (G02/G03) |
| Magenta | Tool Change | Tool change command (M06) |

## Tips & Tricks

### Efficient Navigation
1. Use "Fit All" to see entire toolpath
2. Use preset views for quick orientation
3. Use timeline to jump to specific sections
4. Use playback to simulate cutting

### Performance
- For large files (>100K lines), use progressive loading
- Adjust playback speed for better visualization
- Use layer selection to focus on specific areas

### Editing Workflow
1. Load G-code file
2. Review in 3D viewer
3. Edit in Editor tab
4. Click Reload to see changes
5. Export screenshot or video

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| R | Reset camera |
| F | Fit all |
| 1 | Front view |
| 2 | Top view |
| 3 | Side view |
| 0 | Isometric view |
| Space | Toggle playback |
| Esc | Stop playback |

## Troubleshooting

### Viewer Not Showing
- Ensure VTK is installed: `pip install vtk`
- Check that file is valid G-code
- Try "Fit All" button

### Slow Loading
- Use chunk-based loading for large files
- Reduce playback speed
- Close other applications

### Camera Not Responding
- Ensure mouse is over viewer
- Try clicking "Reset" button
- Check that interactor is active

### Editor Not Updating
- Click "Reload" button after editing
- Check for syntax errors in G-code
- Verify file is not locked

## File Formats Supported

- **.nc** - CNC machine code
- **.gcode** - G-code format
- **.gco** - G-code format
- **.tap** - CNC tape format

## Getting Help

1. Check **GCODE_VIEWER_GUIDE.md** for detailed documentation
2. Review **GCODE_VIEWER_INTEGRATION.md** for technical details
3. Check component docstrings in source code
4. Review error messages in application logs

## Common Tasks

### View a Specific Layer
1. Load G-code file
2. Go to "Statistics" tab
3. Select layer from "Layers" dropdown
4. View selected layer in 3D viewer

### Export Current View
1. Position camera as desired
2. Click "Export Screenshot" button
3. Choose save location
4. Image is saved

### Simulate Cutting
1. Load G-code file
2. Go to "Timeline & Loader" tab
3. Click "Play" button
4. Adjust speed as needed
5. Watch simulation in 3D viewer

### Edit and Preview
1. Load G-code file
2. Click "Editor" tab
3. Make changes to G-code
4. Click "Reload" button
5. Changes appear in 3D viewer

## Performance Tips

- **Large Files**: Use progressive loading
- **Smooth Playback**: Reduce playback speed
- **Better Visibility**: Use "Fit All" and preset views
- **Faster Loading**: Reduce chunk size if memory limited

## Next Steps

1. Load your first G-code file
2. Explore 3D viewer controls
3. Try timeline scrubbing
4. Edit G-code and see changes
5. Export screenshots or videos

---

**For more information, see the documentation in the `docs/` directory.**

