# File Organisation Plan - Update

## Issue Identified
ProjectManagerWidget creation was not explicitly documented in the implementation plan.

## Resolution
Added comprehensive documentation for ProjectManagerWidget creation and main window integration.

## Updated Components

### 1. ProjectManagerWidget Creation
**File**: `src/gui/project_manager/project_manager_widget.py`

A new dock widget that provides:
- Create new project UI
- Open existing project UI
- Duplicate detection and handling
- Project list display
- Project selection and management

### 2. Main Window Integration
**File**: `src/gui/main_window.py` (extend)

New method: `_setup_project_manager_dock()`
- Creates ProjectManager dock widget
- Integrates with native Qt dock system
- Positions alongside Model Library, Properties, Metadata docks
- Supports tabification and nesting
- Persists layout via QSettings

### 3. Package Structure
**File**: `src/gui/project_manager/__init__.py`

Package initialization file that exports:
- ProjectManagerWidget
- Related utilities and helpers

## Integration Pattern

Following the existing codebase pattern:

```python
# In main_window.py _setup_native_dock_widgets()

def _setup_project_manager_dock(self) -> None:
    """Set up project manager dock using native Qt."""
    try:
        self.project_manager_dock = QDockWidget("Project Manager", self)
        self.project_manager_dock.setObjectName("ProjectManagerDock")
        
        # Configure with native Qt dock features
        self.project_manager_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.BottomDockWidgetArea
        )
        self.project_manager_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable
        )
        
        # Create project manager widget
        from src.gui.project_manager import ProjectManagerWidget
        self.project_manager_widget = ProjectManagerWidget(self)
        self.project_manager_dock.setWidget(self.project_manager_widget)
        
        # Add to dock system
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_manager_dock)
        
        self.logger.info("Project Manager dock created successfully")
    except Exception as e:
        self.logger.warning(f"Failed to create Project Manager dock: {e}")
```

## Updated File Structure

```
src/gui/project_manager/
├── __init__.py
└── project_manager_widget.py
```

## Updated Task List

Added subtasks under "Run Mode Popup & Preferences UI":
1. Create ProjectManagerWidget
2. Integrate ProjectManager into main window
3. Create __init__.py for project_manager package

## Implementation Sequence

### Phase 3: UI Integration (Updated)
1. Create RunModeSetupDialog for first-run setup
2. **Create ProjectManagerWidget** ← NEW
3. **Integrate ProjectManager into main window** ← NEW
4. Integrate DropZone with file operations
5. Implement BackgroundTaskMonitorDialog for shutdown

## Key Design Decisions

1. **Dock Widget**: ProjectManager is a dock widget (not a tab) for flexibility
2. **Native Qt Integration**: Uses native Qt dock system for consistency
3. **Layout Persistence**: Dock position/state saved via QSettings
4. **Tabification Support**: Can be tabified with other docks
5. **Nesting Support**: Supports nested docking for advanced layouts

## Next Steps

1. ✅ Research & Planning Phase - COMPLETE
2. ✅ Identified missing ProjectManagerWidget - COMPLETE
3. 🔄 Database Schema Design & Migration - READY TO START
4. IFT Service Implementation
5. Project Manager Implementation
6. File Manager Implementation
7. Background Task Manager Implementation
8. Run Mode Manager Implementation
9. **ProjectManagerWidget Creation** ← ADDED
10. **Main Window Integration** ← ADDED
11. DropZone Integration
12. Background Task Monitor Implementation
13. Error Handling & Logging
14. Testing & Documentation

## Documentation Updated

- ✅ FILE_ORGANISATION_IMPLEMENTATION_PLAN.md
- ✅ FILE_ORGANISATION_SUMMARY.md
- ✅ FILE_ORGANISATION_PLAN_UPDATE.md (this file)

All documentation now includes explicit ProjectManagerWidget creation and main window integration steps.

