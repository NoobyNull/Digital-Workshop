# Tab Data Integration Guide

## Quick Start

The tab data JSON save/load functionality is now **fully implemented**. Here's how to integrate it with your Project Manager.

## What Was Implemented

### 1. TabDataManager Service
- **Location**: `src/core/services/tab_data_manager.py`
- **Purpose**: Unified service for saving/loading tab data to/from projects
- **Features**: Automatic database linking, error handling, logging

### 2. Tab Implementations

#### Cut List Optimizer
- **File**: `src/gui/CLO/cut_list_optimizer_widget.py`
- **Methods**: `set_current_project()`, `save_to_project()`, `load_from_project()`
- **Data File**: `cut_list.json`
- **Category**: Cut Lists

#### Feed and Speed
- **File**: `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py`
- **Methods**: `set_current_project()`, `save_to_project()`, `load_from_project()`
- **Data File**: `feeds_and_speeds.json`
- **Category**: Feed and Speed

#### Project Cost Estimator
- **File**: `src/gui/cost_estimator/cost_estimator_widget.py`
- **Methods**: `set_current_project()`, `save_to_project()`, `load_from_project()`
- **Data File**: `cost_estimate.json`
- **Category**: Cost Sheets

## Integration Steps

### Step 1: Connect to Project Manager

In your `main_window.py` or `project_manager.py`, when a project is selected:

```python
def on_project_selected(self, project_id: str):
    """Called when user selects a project."""
    
    # Set current project for all tabs
    self.cut_list_widget.set_current_project(project_id)
    self.feeds_speeds_widget.set_current_project(project_id)
    self.cost_estimator_widget.set_current_project(project_id)
    
    # Optional: Auto-load tab data if it exists
    # self.cut_list_widget.load_from_project()
```

### Step 2: Connect Signals

If your Project Manager emits a signal when project is selected:

```python
# In main_window.py __init__
self.project_manager.project_selected.connect(self.on_project_selected)
```

### Step 3: Verify UI Buttons

Each tab should have "Save to Project" and "Load from Project" buttons. These are already connected to:
- `save_to_project()` method
- `load_from_project()` method

If buttons don't exist, add them to the tab UI.

## Usage Flow

### Saving Tab Data

```
User clicks "Save to Project" button
    ↓
save_to_project() is called
    ↓
Data gathered from UI
    ↓
TabDataManager.save_tab_data_to_project() called
    ↓
JSON file created in project directory
    ↓
File linked to project in database
    ↓
Success message shown
    ↓
File appears in Project Manager tree
```

### Loading Tab Data

```
User clicks "Load from Project" button
    ↓
load_from_project() is called
    ↓
TabDataManager.load_tab_data_from_project() called
    ↓
JSON file loaded from project directory
    ↓
Data restored to UI
    ↓
Success message shown
```

### Exporting to DWW

```
User clicks "Export as DWW"
    ↓
DWW Export Manager includes all project files
    ↓
Tab data files automatically included
    ↓
DWW archive created with all data
    ↓
User can share/backup
```

### Importing from DWW

```
User clicks "Import DWW"
    ↓
DWW Import Manager extracts all files
    ↓
Tab data files extracted to project directory
    ↓
Files linked to new project
    ↓
User can load tab data back into tabs
```

## File Structure

After saving tab data, projects will have:

```
Project/
├── cut_list_optimizer/
│   └── cut_list.json
├── feed_and_speed/
│   └── feeds_and_speeds.json
├── project_cost_estimator/
│   └── cost_estimate.json
└── [other project files]
```

## API Reference

### TabDataManager

```python
from src.core.services.tab_data_manager import TabDataManager
from src.core.database_manager import get_database_manager

# Initialize
tab_data_manager = TabDataManager(get_database_manager())

# Save data
success, message = tab_data_manager.save_tab_data_to_project(
    project_id="project-uuid",
    tab_name="Cut List Optimizer",
    data={"cut_pieces": [...], "raw_materials": [...]},
    filename="cut_list.json",
    category="Cut Lists"
)

# Load data
success, data, message = tab_data_manager.load_tab_data_from_project(
    project_id="project-uuid",
    filename="cut_list.json"
)

# List files
success, files, message = tab_data_manager.list_tab_data_files(
    project_id="project-uuid",
    tab_name="Cut List Optimizer"
)

# Delete file
success, message = tab_data_manager.delete_tab_data_file(
    project_id="project-uuid",
    filename="cut_list.json"
)
```

### Tab Widgets

```python
# Set current project
widget.set_current_project(project_id)

# Save to project
widget.save_to_project()

# Load from project
widget.load_from_project()
```

## Error Handling

All methods include error handling:

- **No Project Selected**: Warning dialog
- **File Not Found**: Warning dialog
- **Invalid JSON**: Error dialog
- **Database Error**: Error dialog with logging
- **UI Restoration Error**: Error dialog

## Testing Checklist

- [ ] Select a project in Project Manager
- [ ] Click "Save to Project" in Cut List Optimizer
- [ ] Verify file appears in Project Manager tree
- [ ] Click "Load from Project" in Cut List Optimizer
- [ ] Verify data is restored correctly
- [ ] Repeat for Feed and Speed tab
- [ ] Repeat for Cost Estimator tab
- [ ] Export project to DWW
- [ ] Verify tab data files included in DWW
- [ ] Import DWW file
- [ ] Verify tab data files extracted
- [ ] Load tab data from imported project

## Troubleshooting

### "No Project" Warning
- Make sure to call `set_current_project()` when project is selected
- Check that project_id is valid

### "File Not Found" Warning
- Make sure to save data first before loading
- Check that file exists in project directory

### Data Not Restoring
- Check that JSON file is valid
- Check that all required fields are present
- Check error logs for details

### Files Not Appearing in Project Manager
- Make sure database linking is working
- Check that `add_file_to_project()` is being called
- Refresh Project Manager tree

## Next Steps

1. **Integrate with Project Manager**
   - Add `on_project_selected()` handler
   - Connect project selection signal

2. **Test Integration**
   - Test save/load workflow
   - Test DWW export/import
   - Test Project Manager tree display

3. **Optional: Auto-Save**
   - Implement auto-save timer
   - Save on interval or on data change

4. **Optional: Auto-Load**
   - Auto-load tab data when project selected
   - Show notification when data loaded

## Summary

✅ All tab data save/load functionality is implemented
✅ TabDataManager service is ready to use
✅ All three tabs support save/load
✅ Database linking is automatic
✅ DWW export/import ready
✅ Error handling comprehensive

**Ready for integration!**

