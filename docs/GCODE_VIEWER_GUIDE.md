# VTK G-code Viewer Guide

## Overview

The VTK G-code Viewer is a comprehensive 3D visualization system for CNC G-code files. It provides interactive 3D viewing, real-time loading, timeline scrubbing, and integrated G-code editing capabilities.

## Features

### 1. 3D Visualization
- **Polyline-based rendering**: G-code moves are rendered as 3D polylines
- **Move type differentiation**: Different colors and line widths for different move types:
  - **Rapid moves (G00)**: Orange, thin lines - fast positioning moves
  - **Cutting moves (G01)**: Green, thick lines - actual cutting operations
  - **Arc moves (G02/G03)**: Cyan, medium lines - circular interpolation
  - **Tool changes (M06)**: Magenta markers - tool change events
  - **Spindle control (M03/M04/M05)**: Tracked for visualization context

### 2. Interactive 3D Camera Controls
- **Rotate**: Left-click and drag to rotate around the focal point
- **Pan**: Middle-click and drag to pan the view
- **Zoom**: Right-click and drag, or use mouse wheel
- **Preset views**: Front, Top, Side, Isometric
- **Fit All**: Auto-fit all geometry in view
- **Reset**: Return to initial camera state

### 3. Interactive Loading
- **Progressive loading**: G-code files load in chunks with real-time visualization
- **Watch it load**: See the toolpath build incrementally as the file loads
- **Cancellable**: Stop loading at any time
- **Statistics**: Real-time display of move counts and file progress

### 4. Timeline/Scrubber
- **Frame-by-frame scrubbing**: Drag the timeline slider to jump to any point
- **Playback controls**: Play, pause, and stop buttons
- **Speed control**: Adjust playback speed from 10% to 500%
- **Statistics display**: Shows rapid, cutting, arc, and tool change counts
- **Progress tracking**: Visual progress bar and frame counter

### 5. G-code Editor Integration
- **Syntax highlighting**: Color-coded G-code syntax
- **Live editing**: Edit G-code and see changes in real-time
- **Reload capability**: Reload visualization after editing

## Architecture

### Core Components

#### GcodeParser (`gcode_parser.py`)
Parses G-code files and extracts move information:
- Detects move types (rapid, cutting, arc)
- Tracks tool changes and spindle commands
- Maintains position and bounds information
- Supports modal G-code commands

**Key classes:**
- `GcodeMove`: Dataclass representing a single move
- `GcodeParser`: Main parser class

#### GcodeRenderer (`gcode_renderer.py`)
VTK-based rendering engine:
- Converts moves to 3D polylines
- Manages actors for different move types
- Supports incremental rendering
- Handles color and line width management

**Key methods:**
- `render_toolpath()`: Render complete toolpath
- `add_moves_incremental()`: Add moves progressively
- `clear_incremental()`: Reset incremental data

#### CameraController (`camera_controller.py`)
Advanced camera control system:
- Trackball-style rotation
- Pan and zoom operations
- Preset view angles
- Mouse event handling

**Key methods:**
- `handle_mouse_press/move/release()`: Mouse interaction
- `set_view_*()`: Preset views
- `fit_all()`: Auto-fit geometry

#### VTKWidget (`vtk_widget.py`)
Qt integration for VTK rendering:
- Embeds VTK renderer in Qt application
- Provides camera control toolbar
- Handles mouse and wheel events
- Manages render updates

#### GcodeTimeline (`gcode_timeline.py`)
Interactive timeline widget:
- Slider-based frame scrubbing
- Playback controls
- Speed adjustment
- Statistics display

#### InteractiveGcodeLoader (`gcode_interactive_loader.py`)
Progressive file loading system:
- Chunk-based loading
- Real-time visualization updates
- Progress tracking
- Error handling

## Usage Example

```python
from src.gui.gcode_previewer_components import (
    GcodeParser, GcodeRenderer, VTKWidget, 
    GcodeTimeline, InteractiveGcodeLoader
)

# Create parser and renderer
parser = GcodeParser()
renderer = GcodeRenderer()

# Create VTK widget with camera controls
vtk_widget = VTKWidget(renderer)

# Create timeline for scrubbing
timeline = GcodeTimeline()

# Create interactive loader
loader = InteractiveGcodeLoader(renderer)

# Load and visualize G-code
loader.load_file("path/to/file.gcode")

# Connect signals
loader.loading_complete.connect(lambda moves: timeline.set_moves(moves))
timeline.frame_changed.connect(on_frame_changed)
```

## Color Scheme

| Move Type | Color | RGB | Line Width |
|-----------|-------|-----|-----------|
| Rapid | Orange | (1.0, 0.5, 0.0) | 1.5 |
| Cutting | Green | (0.0, 1.0, 0.0) | 3.0 |
| Arc | Cyan | (0.0, 0.5, 1.0) | 2.5 |
| Tool Change | Magenta | (1.0, 0.0, 1.0) | 2.0 |

## Performance Considerations

- **Large files**: Use chunk-based loading for files > 100K lines
- **Incremental rendering**: Updates visualization as chunks load
- **Memory management**: Moves are stored efficiently in VTK structures
- **Rendering optimization**: Separate actors for each move type

## Keyboard Shortcuts

- **R**: Reset camera
- **F**: Fit all
- **1**: Front view
- **2**: Top view
- **3**: Side view
- **0**: Isometric view

## Troubleshooting

### Viewer not showing
- Ensure VTK is properly installed: `pip install vtk`
- Check that renderer is initialized before adding to widget

### Slow loading
- Use chunk-based loading for large files
- Reduce chunk size if memory is limited
- Consider sampling large files

### Camera not responding
- Ensure mouse events are properly connected
- Check that interactor is initialized
- Verify camera controller is created

## Future Enhancements

- [ ] Tool visualization (show tool geometry)
- [ ] Simulation playback with tool path animation
- [ ] Collision detection
- [ ] Multi-axis support (4-axis, 5-axis)
- [ ] Tool path optimization suggestions
- [ ] Export to various formats
- [ ] Measurement tools
- [ ] Annotation system

