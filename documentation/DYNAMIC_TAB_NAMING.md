# Dynamic Tab Naming System

## Overview

A responsive tab naming system has been implemented that automatically switches between long and short tab names based on available window space. This ensures tab names are always readable and the interface remains clean at any window size.

## Features

### Automatic Name Switching

The system monitors window width and automatically switches tab names:

**Wide Window (800px+)**
```
┌─────────────────────────────────────────────────────────────────┐
│ Model Previewer │ G Code Previewer │ Cut List Optimizer │ Feed and Speed │ Project Cost Estimator │
└─────────────────────────────────────────────────────────────────┘
```

**Narrow Window (<800px)**
```
┌──────────────────────────────────────────────────────────┐
│ MV │ GCP │ CLO │ F&S │ PCO │
└──────────────────────────────────────────────────────────┘
```

### Tab Naming Mapping

| Long Name | Short Name | Purpose |
|-----------|-----------|---------|
| Model Previewer | MV | 3D model viewing and manipulation |
| G Code Previewer | GCP | G-code visualization and analysis |
| Cut List Optimizer | CLO | Material optimization and cutting |
| Feed and Speed | F&S | CNC feeds and speeds calculator |
| Project Cost Estimator | PCO | Project cost estimation |

## How It Works

### 1. Registration

Each tab is registered with long and short names:

```python
manager.register_tab(0, "Model Previewer", "MV")
manager.register_tab(1, "G Code Previewer", "GCP")
manager.register_tab(2, "Cut List Optimizer", "CLO")
manager.register_tab(3, "Feed and Speed", "F&S")
manager.register_tab(4, "Project Cost Estimator", "PCO")
```

### 2. Monitoring

The system monitors window resize events and debounces updates:

- Resize events trigger a 100ms debounce timer
- Prevents excessive updates during continuous resizing
- Improves performance and reduces flickering

### 3. Decision Logic

For each tab, the system calculates:

1. **Available Width**: Total tab bar width divided by number of tabs
2. **Text Width**: Measured width of long name using font metrics
3. **Decision**: If text width > available width, use short name

### 4. Update

Tab names are updated only when they change:

- Reduces unnecessary UI updates
- Smooth transition between long and short names
- Maintains current tab selection

## Architecture

### Components

#### `TabNameConfig`
Stores configuration for a single tab:
- `long_name`: Full tab name
- `short_name`: Abbreviated name
- `current_name`: Currently displayed name
- `should_shorten()`: Determines if shortening is needed

#### `DynamicTabManager`
Main manager class:
- Monitors resize events
- Manages tab configurations
- Updates tab names dynamically
- Handles debouncing

#### `setup_dynamic_tabs()`
Convenience function:
- Creates manager instance
- Registers all standard tabs
- Performs initial update
- Returns manager for later access

### File Structure

```
src/gui/components/
└── dynamic_tab_manager.py
    ├── TabNameConfig class
    ├── DynamicTabManager class
    └── setup_dynamic_tabs() function
```

## Integration

### Central Widget Manager

The dynamic tab manager is initialized in `central_widget_manager.py`:

```python
# Setup dynamic tab naming
try:
    from src.gui.components.dynamic_tab_manager import setup_dynamic_tabs
    self.main_window.dynamic_tab_manager = setup_dynamic_tabs(self.main_window.hero_tabs)
    self.logger.info("Dynamic tab manager initialized")
except Exception as e:
    self.logger.warning(f"Failed to initialize dynamic tab manager: {e}")
```

### Main Window

The manager is accessible via:
```python
main_window.dynamic_tab_manager
```

## Configuration

### Thresholds

**Minimum Width for Long Names**
```python
MIN_WIDTH_FOR_LONG_NAMES = 800  # pixels
```

**Tab Padding**
```python
TAB_PADDING = 30  # pixels (left + right margins)
```

**Debounce Delay**
```python
resize_timer.start(100)  # milliseconds
```

### Customization

To add or modify tabs:

```python
manager.register_tab(index, "Long Name", "Short")
manager.force_update()  # Force immediate update
```

## Performance

- **Debouncing**: 100ms delay prevents excessive updates
- **Conditional Updates**: Only updates when name changes
- **Font Metrics**: Cached per tab bar
- **Memory**: Minimal overhead (one config per tab)

## Responsive Behavior

### Window Resize Scenarios

**Maximizing Window**
1. Window expands
2. Available width increases
3. Long names appear
4. Smooth transition

**Minimizing Window**
1. Window shrinks
2. Available width decreases
3. Short names appear
4. Smooth transition

**Dragging Splitter**
1. Tab bar width changes
2. Debounce timer resets
3. Names update after 100ms
4. No flickering

## Testing

### Manual Testing

1. **Wide Window**: Launch app at full screen
   - Should show long names
   - Example: "Model Previewer", "G Code Previewer"

2. **Narrow Window**: Resize window to 600px width
   - Should show short names
   - Example: "MV", "GCP"

3. **Resize Smoothly**: Drag window edge slowly
   - Names should switch smoothly
   - No flickering or jumping

4. **Rapid Resize**: Drag window edge quickly
   - Debouncing should prevent excessive updates
   - Performance should remain smooth

### Programmatic Testing

```python
from src.gui.components.dynamic_tab_manager import DynamicTabManager
from PySide6.QtWidgets import QTabWidget

tab_widget = QTabWidget()
manager = DynamicTabManager(tab_widget)

# Register tabs
manager.register_tab(0, "Model Previewer", "MV")

# Force update
manager.force_update()

# Check current name
current = tab_widget.tabText(0)
print(f"Current tab name: {current}")
```

## Troubleshooting

### Tab names not changing
- Check that `MIN_WIDTH_FOR_LONG_NAMES` threshold is appropriate
- Verify tab bar width is being calculated correctly
- Check application logs for errors

### Flickering when resizing
- Debounce delay may be too short
- Increase `resize_timer.start()` value
- Check for other resize event handlers

### Names not updating on startup
- Call `manager.force_update()` after adding tabs
- Verify tabs are registered before initialization
- Check that tab widget is properly sized

## Future Enhancements

1. **Configurable Thresholds**: Allow per-tab width thresholds
2. **Animation**: Smooth fade between long/short names
3. **Persistence**: Remember user's preferred name length
4. **Tooltips**: Show full name on hover
5. **Custom Abbreviations**: Allow user-defined short names
6. **Multi-level Abbreviations**: Support multiple shortening levels

## References

- Qt Documentation: QTabWidget, QTabBar
- Font Metrics: QFontMetrics
- Event Handling: QResizeEvent
- Timer: QTimer

## Related Files

- `src/gui/window/central_widget_manager.py` - Integration point
- `src/gui/main_window.py` - Main window setup
- `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py` - F&S tab
- `src/gui/CLO/cut_list_optimizer_widget.py` - CLO tab
- `src/gui/gcode_previewer_components/gcode_previewer_main.py` - GCP tab

