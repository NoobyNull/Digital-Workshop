# VTK G-code Viewer - Integration Guide

## Quick Start Integration

### Step 1: Import Components

```python
from src.gui.gcode_previewer_components import (
    GcodeParser,
    GcodeRenderer,
    VTKWidget,
    GcodeTimeline,
    InteractiveGcodeLoader,
    GcodeEditorWidget,
    AnimationController,
)
```

### Step 2: Create Main Widget

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt

class GcodeViewerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create components
        self.parser = GcodeParser()
        self.renderer = GcodeRenderer()
        self.animation_controller = AnimationController()
        
        # Create UI
        layout = QVBoxLayout(self)
        
        # Create splitter for 3D view and controls
        splitter = QSplitter(Qt.Horizontal)
        
        # 3D Viewer
        self.vtk_widget = VTKWidget(self.renderer)
        splitter.addWidget(self.vtk_widget)
        
        # Right panel with timeline and editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Timeline
        self.timeline = GcodeTimeline()
        right_layout.addWidget(self.timeline)
        
        # Interactive loader
        self.loader = InteractiveGcodeLoader(self.renderer)
        right_layout.addWidget(self.loader)
        
        # G-code editor
        self.editor = GcodeEditorWidget()
        right_layout.addWidget(self.editor)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect all signals between components."""
        
        # Loader -> Timeline
        self.loader.loading_complete.connect(self.timeline.set_moves)
        
        # Timeline -> Animation
        self.timeline.frame_changed.connect(self._on_frame_changed)
        self.timeline.playback_requested.connect(self.animation_controller.play)
        self.timeline.pause_requested.connect(self.animation_controller.pause)
        self.timeline.stop_requested.connect(self.animation_controller.stop)
        
        # Animation -> Timeline
        self.animation_controller.frame_changed.connect(self.timeline.set_current_frame)
        
        # Editor -> Renderer
        self.editor.reload_requested.connect(self._on_editor_reload)
    
    def _on_frame_changed(self, frame_index: int):
        """Handle frame change from timeline."""
        if frame_index < len(self.loader.all_moves):
            # Update visualization to show moves up to this frame
            moves_to_show = self.loader.all_moves[:frame_index + 1]
            self.renderer.render_toolpath(moves_to_show)
            self.vtk_widget.update_render()
    
    def _on_editor_reload(self, content: str):
        """Handle G-code editor reload."""
        # Parse edited content
        lines = content.split('\n')
        moves = self.parser.parse_lines(lines)
        
        # Update visualization
        self.renderer.render_toolpath(moves)
        self.timeline.set_moves(moves)
        self.vtk_widget.update_render()
    
    def load_gcode_file(self, filepath: str):
        """Load a G-code file."""
        self.loader.load_file(filepath)
```

### Step 3: Add to Main Window

```python
# In MainWindow._setup_viewer_widget() or similar

from gcode_viewer_panel import GcodeViewerPanel

# Create G-code viewer panel
self.gcode_viewer = GcodeViewerPanel()

# Add to tab widget
self.hero_tabs.addTab(self.gcode_viewer, "G-code Previewer")
```

## Signal Flow Diagram

```
InteractiveGcodeLoader
    ↓ loading_complete
GcodeTimeline
    ↓ frame_changed
GcodeRenderer (render_toolpath)
    ↓
VTKWidget (update_render)

AnimationController
    ↓ frame_changed
GcodeTimeline (set_current_frame)

GcodeEditorWidget
    ↓ reload_requested
GcodeParser (parse_lines)
    ↓
GcodeRenderer (render_toolpath)
```

## Integration Checklist

- [ ] Import all components
- [ ] Create main widget class
- [ ] Create VTK widget with renderer
- [ ] Create timeline widget
- [ ] Create interactive loader
- [ ] Create/reference editor widget
- [ ] Connect loader → timeline signals
- [ ] Connect timeline → animation signals
- [ ] Connect animation → timeline signals
- [ ] Connect editor → renderer signals
- [ ] Add to main window
- [ ] Test file loading
- [ ] Test timeline scrubbing
- [ ] Test playback
- [ ] Test editor integration
- [ ] Test camera controls

## Common Integration Patterns

### Pattern 1: Minimal Integration
```python
# Just the 3D viewer
vtk_widget = VTKWidget(renderer)
layout.addWidget(vtk_widget)
```

### Pattern 2: With Timeline
```python
# 3D viewer + timeline
splitter = QSplitter(Qt.Vertical)
splitter.addWidget(VTKWidget(renderer))
splitter.addWidget(GcodeTimeline())
layout.addWidget(splitter)
```

### Pattern 3: Full Integration
```python
# All components with proper signal connections
# See Step 2 above
```

## Keyboard Shortcuts to Add

```python
def _setup_shortcuts(self):
    """Setup keyboard shortcuts."""
    from PySide6.QtGui import QKeySequence
    
    # Camera shortcuts
    QShortcut(Qt.Key_R, self, self.vtk_widget.reset_camera)
    QShortcut(Qt.Key_F, self, self.vtk_widget.fit_all)
    QShortcut(Qt.Key_1, self, self.vtk_widget.set_view_front)
    QShortcut(Qt.Key_2, self, self.vtk_widget.set_view_top)
    QShortcut(Qt.Key_3, self, self.vtk_widget.set_view_side)
    QShortcut(Qt.Key_0, self, self.vtk_widget.set_view_isometric)
    
    # Playback shortcuts
    QShortcut(Qt.Key_Space, self, self._toggle_playback)
    QShortcut(Qt.Key_Escape, self, self.animation_controller.stop)
```

## Troubleshooting Integration

### Issue: VTK widget not showing
**Solution**: Ensure renderer is initialized before adding to widget
```python
renderer = GcodeRenderer()
vtk_widget = VTKWidget(renderer)  # Must be in this order
```

### Issue: Timeline not updating
**Solution**: Connect signals properly
```python
self.loader.loading_complete.connect(self.timeline.set_moves)
```

### Issue: Camera not responding
**Solution**: Check mouse event connections
```python
# Verify in VTKWidget.__init__
self.vtk_widget.mousePressEvent = self._on_mouse_press
```

### Issue: Slow rendering
**Solution**: Use chunk-based loading
```python
loader = InteractiveGcodeLoader(renderer, chunk_size=200)
```

## Performance Optimization Tips

1. **Use chunk-based loading** for files > 10K lines
2. **Reduce chunk size** if memory is limited
3. **Use incremental rendering** instead of full re-render
4. **Disable unnecessary features** for large files
5. **Profile with large test files** before deployment

## Testing Integration

```python
def test_integration():
    """Test the integrated G-code viewer."""
    
    # Create panel
    panel = GcodeViewerPanel()
    
    # Load test file
    panel.load_gcode_file("test_files/sample.gcode")
    
    # Test timeline
    panel.timeline.set_current_frame(10)
    assert panel.timeline.current_frame == 10
    
    # Test playback
    panel.animation_controller.play()
    assert panel.animation_controller.state == PlaybackState.PLAYING
    
    # Test editor
    panel.editor.setPlainText("G00 X10 Y20 Z5")
    panel.editor.reload_requested.emit("G00 X10 Y20 Z5")
    
    print("Integration test passed!")
```

## Next Steps

1. Implement the integration following Step 2
2. Test with sample G-code files
3. Add keyboard shortcuts
4. Optimize performance
5. Add tool visualization (optional)
6. Add measurement tools (optional)

