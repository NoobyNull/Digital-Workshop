# Adding New Panes and Widgets to Candy-Cadence

Complete guide for creating and integrating new dock panes and widgets into the application.

## Architecture Overview

The application uses a **modular component architecture** with:
- **Dock Widgets**: Dockable panels managed by `DockManager`
- **Component Modules**: Self-contained feature packages under `src/gui/`
- **Facade Pattern**: Simplified interfaces for complex components
- **Qt-Material Theming**: All widgets automatically themed via qt-material

## Step 1: Create Your Component Module

### Directory Structure
```
src/gui/my_feature_components/
├── __init__.py                    # Exports public API
├── my_feature_main.py             # Main widget (< 300 lines)
├── my_feature_manager.py          # Business logic (< 300 lines)
├── my_feature_worker.py           # Background tasks (optional)
└── my_feature_facade.py           # Simplified interface (optional)
```

### Example: Main Widget (`my_feature_main.py`)

```python
"""My Feature Widget - Main component."""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from src.core.logging_config import get_logger

class MyFeatureWidget(QWidget):
    """Main widget for my feature."""
    
    # Define signals for communication
    feature_action = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the widget."""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        # Initialize UI
        self._init_ui()
        self._setup_connections()
        
        self.logger.info("My Feature Widget initialized")
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Add your widgets here
        button = QPushButton("Do Something")
        layout.addWidget(button)
    
    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        pass
```

### Create `__init__.py`

```python
"""My Feature Components - Modular feature package."""

from .my_feature_main import MyFeatureWidget

__all__ = ['MyFeatureWidget']
```

## Step 2: Create the Dock Widget

Edit `src/gui/window/dock_manager.py` and add a method:

```python
def create_my_feature_dock(self) -> None:
    """Create and setup My Feature dock widget."""
    self.my_feature_dock = QDockWidget("My Feature", self.main_window)
    self.my_feature_dock.setObjectName("MyFeatureDock")
    self.my_feature_dock.setAllowedAreas(
        Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | 
        Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
    )
    self.my_feature_dock.setFeatures(
        QDockWidget.DockWidgetMovable | 
        QDockWidget.DockWidgetFloatable | 
        QDockWidget.DockWidgetClosable
    )
    
    try:
        from src.gui.my_feature_components import MyFeatureWidget
        self.my_feature_widget = MyFeatureWidget(self.main_window)
        
        # Connect signals if needed
        self.my_feature_widget.feature_action.connect(self._on_feature_action)
        
        self.my_feature_dock.setWidget(self.my_feature_widget)
        
        # Let qt-material handle all dock styling
        self.logger.info("My Feature widget created successfully")
        
    except Exception as e:
        # Fallback widget
        placeholder = QTextEdit()
        placeholder.setReadOnly(True)
        placeholder.setPlainText("My Feature\n\nComponent unavailable.")
        self.my_feature_dock.setWidget(placeholder)
        self.logger.warning(f"Failed to create My Feature widget: {e}")
    
    # Attach dock to main window
    self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.my_feature_dock)
    
    # Register for snapping and autosave
    try:
        self._register_dock_for_snapping(self.my_feature_dock)
        self._connect_layout_autosave(self.my_feature_dock)
    except Exception:
        pass
```

## Step 3: Register in Main Window

Edit `src/gui/main_window.py` in `setup_dock_widgets()`:

```python
def setup_dock_widgets(self) -> None:
    """Setup all dock widgets."""
    # ... existing docks ...
    
    # Create My Feature dock
    self.dock_manager.create_my_feature_dock()
```

## Step 4: Add Menu Item (Optional)

Edit `src/gui/components/menu_manager.py`:

```python
def setup_view_menu(self) -> None:
    """Setup View menu with dock visibility toggles."""
    # ... existing items ...
    
    # Add My Feature toggle
    self.show_my_feature_action = QAction("My Feature", self.main_window)
    self.show_my_feature_action.setCheckable(True)
    self.show_my_feature_action.setChecked(True)
    self.show_my_feature_action.triggered.connect(
        lambda checked: self.main_window.my_feature_dock.setVisible(checked)
    )
    self.view_menu.addAction(self.show_my_feature_action)
```

## Step 5: Apply Theming

**No additional theming code needed!** Qt-material handles everything automatically:

```python
# ✅ Correct - Let qt-material handle theming
class MyFeatureWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Just create widgets normally
        layout = QVBoxLayout(self)
        button = QPushButton("Click me")
        layout.addWidget(button)
        # Qt-material stylesheet cascades automatically!
```

## Step 6: Testing

### Test Widget Standalone
```python
# test_my_feature.py
from PySide6.QtWidgets import QApplication
from src.gui.my_feature_components import MyFeatureWidget

app = QApplication([])
widget = MyFeatureWidget()
widget.show()
app.exec()
```

### Test in Main Window
1. Run the application: `python -m src.main`
2. Verify dock appears in correct location
3. Test dragging/floating the dock
4. Verify theming (dark/light mode)
5. Test View menu toggle

## Best Practices

### ✅ DO:
- Keep each file under 300 lines (modularity)
- Use signals for inter-widget communication
- Let qt-material handle all styling
- Add logging for debugging
- Create a facade for complex components
- Use type hints
- Document public methods

### ❌ DON'T:
- Add custom stylesheets (use qt-material)
- Mix business logic with UI code
- Create monolithic files
- Use hardcoded colors
- Ignore theming requirements
- Skip error handling

## Common Patterns

### Pattern 1: Simple Widget
```python
class SimpleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        # Add widgets
```

### Pattern 2: Widget with Manager
```python
class FeatureWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = FeatureManager()
        self._init_ui()
        self._setup_connections()
    
    def _setup_connections(self):
        self.manager.data_ready.connect(self._on_data_ready)
```

### Pattern 3: Widget with Facade
```python
class FeatureWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.facade = FeatureFacade(self)
        self.facade.initialize()
```

## File Size Guidelines

| Component | Max Lines | Reason |
|-----------|-----------|--------|
| Main Widget | 300 | UI initialization |
| Manager | 300 | Business logic |
| Worker | 200 | Background tasks |
| Facade | 150 | Interface simplification |
| __init__.py | 30 | Exports only |

## Troubleshooting

### Widget not appearing?
- Check `create_my_feature_dock()` is called in `setup_dock_widgets()`
- Verify import path is correct
- Check logs for exceptions

### Theming not working?
- Don't add custom stylesheets
- Don't use hardcoded colors
- Let qt-material cascade automatically

### Dock not docking?
- Verify `setAllowedAreas()` includes target area
- Check `addDockWidget()` uses correct area
- Ensure dock features are set correctly

## Example: Complete Feature

See existing implementations:
- **Model Library**: `src/gui/model_library_components/`
- **Metadata Editor**: `src/gui/metadata_components/`
- **Search**: `src/gui/search_components/`
- **Materials**: `src/gui/material_components/`

All follow this exact pattern!

## Summary Checklist

- [ ] Create component module directory
- [ ] Create main widget file (< 300 lines)
- [ ] Create `__init__.py` with exports
- [ ] Add `create_*_dock()` method to DockManager
- [ ] Call dock creation in main_window.py
- [ ] Add menu item (optional)
- [ ] Test widget standalone
- [ ] Test in main window
- [ ] Verify theming works
- [ ] Commit changes

