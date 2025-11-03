# Saving Tab Data to Projects - Complete Guide

## Overview

Digital Workshop has multiple tabs with different types of data. This guide explains how to save data from each tab and associate it with projects.

## Available Tabs

```
┌─────────────────────────────────────────────────────────────┐
│ Model Previewer | G Code Previewer | Cut List Optimizer    │
│ Feed and Speed | Project Cost Estimator                     │
└─────────────────────────────────────────────────────────────┘
```

## Tab Data Types

### 1. **Model Previewer** 📦
- **Data**: 3D model files (STL, OBJ, STEP, 3MF, PLY)
- **Storage**: Files linked to project
- **Status**: ✅ Already integrated with projects

### 2. **G Code Previewer** 🔧
- **Data**: G-code files (NC, GCODE)
- **Storage**: Files linked to project
- **Status**: ✅ Already integrated with projects

### 3. **Cut List Optimizer** ✂️
- **Data**: Cut pieces, raw materials, optimization results
- **Storage**: JSON files or database
- **Current**: Saves to local files (project.json, cut_list.csv)
- **Needed**: Link to project system

### 4. **Feed and Speed** ⚙️
- **Data**: Tool database, presets, calculations
- **Storage**: QSettings (application settings)
- **Current**: Saves to application settings
- **Needed**: Link to project system

### 5. **Project Cost Estimator** 💰
- **Data**: Materials, labor costs, machine costs
- **Storage**: JSON files
- **Current**: Saves to local files
- **Needed**: Link to project system

## How to Save Tab Data to Projects

### Method 1: Save as Project Files (Recommended)

Save tab data as files and link them to the project:

```python
from src.core.database.database_manager import get_database_manager
from pathlib import Path
import json

# Get database manager
db_manager = get_database_manager()

# Example: Save Cut List Optimizer data
def save_cut_list_to_project(project_id: str, cut_pieces: list, raw_materials: list):
    """Save cut list data as project file."""
    
    # Create cut list file
    cut_list_data = {
        'cut_pieces': cut_pieces,
        'raw_materials': raw_materials,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to project directory
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    cut_list_file = project_dir / "cut_list.json"
    
    with open(cut_list_file, 'w') as f:
        json.dump(cut_list_data, f, indent=2)
    
    # Link file to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(cut_list_file),
        file_name="cut_list.json",
        category="Cut Lists"
    )
    
    return str(cut_list_file)
```

### Method 2: Save to Database

Store tab data directly in the database:

```python
# Add new table for tab data
# In database migration:
CREATE TABLE tab_data (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    tab_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

# Usage:
def save_tab_data_to_project(project_id: str, tab_name: str, data: dict):
    """Save tab data to database."""
    db_manager.save_tab_data(
        project_id=project_id,
        tab_name=tab_name,
        data_type="json",
        data=json.dumps(data)
    )
```

### Method 3: Export Tab Data with Project

Include tab data when exporting to DWW:

```python
from src.core.export.dww_export_manager import DWWExportManager

# Export includes all project files
export_manager = DWWExportManager(db_manager)
success, message = export_manager.export_project(
    project_id="project-uuid",
    output_path="/path/to/export.dww",
    include_metadata=True,
    include_thumbnails=True,
    include_renderings=True
)

# All linked files (including tab data) are included
```

## Implementation for Each Tab

### Cut List Optimizer

**Current**: Saves to local files
**Needed**: Link to project

```python
# In CutListOptimizerWidget
def save_to_project(self, project_id: str):
    """Save cut list to project."""
    project_data = {
        'cut_pieces': self.cut_pieces,
        'raw_materials': self.raw_materials,
        'optimization_options': self.optimization_options
    }
    
    # Save as file
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    cut_list_file = project_dir / "cut_list.json"
    
    with open(cut_list_file, 'w') as f:
        json.dump(project_data, f, indent=2)
    
    # Link to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(cut_list_file),
        file_name="cut_list.json",
        category="Cut Lists"
    )
```

### Feed and Speed

**Current**: Saves to QSettings
**Needed**: Link to project

```python
# In FeedsAndSpeedsWidget
def save_to_project(self, project_id: str):
    """Save feeds and speeds data to project."""
    feeds_data = {
        'tool_database': self.tool_database_manager.get_all_tools(),
        'presets': self.personal_toolbox_manager.get_toolbox(),
        'calculations': self.get_current_calculations()
    }
    
    # Save as file
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    feeds_file = project_dir / "feeds_and_speeds.json"
    
    with open(feeds_file, 'w') as f:
        json.dump(feeds_data, f, indent=2)
    
    # Link to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(feeds_file),
        file_name="feeds_and_speeds.json",
        category="Documents"
    )
```

### Project Cost Estimator

**Current**: Saves to local files
**Needed**: Link to project

```python
# In CostEstimatorWidget
def save_to_project(self, project_id: str):
    """Save cost estimate to project."""
    cost_data = {
        'materials': self.material_cost_manager.get_materials(),
        'labor_costs': self.get_labor_costs(),
        'machine_costs': self.get_machine_costs(),
        'total_estimate': self.calculate_total()
    }
    
    # Save as file
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    cost_file = project_dir / "cost_estimate.json"
    
    with open(cost_file, 'w') as f:
        json.dump(cost_data, f, indent=2)
    
    # Link to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(cost_file),
        file_name="cost_estimate.json",
        category="Cost Sheets"
    )
```

## UI Integration

### Add Save Button to Each Tab

```python
# In each tab widget
def _setup_save_button(self):
    """Add save to project button."""
    save_button = QPushButton("Save to Project")
    save_button.clicked.connect(self._on_save_to_project)
    self.layout().addWidget(save_button)

def _on_save_to_project(self):
    """Handle save to project."""
    # Get current project
    current_project = self.get_current_project()
    if not current_project:
        QMessageBox.warning(self, "No Project", "Please select a project first")
        return
    
    # Save data
    try:
        self.save_to_project(current_project['id'])
        QMessageBox.information(self, "Success", "Data saved to project")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
```

### Add Load Button to Each Tab

```python
def _setup_load_button(self):
    """Add load from project button."""
    load_button = QPushButton("Load from Project")
    load_button.clicked.connect(self._on_load_from_project)
    self.layout().addWidget(load_button)

def _on_load_from_project(self):
    """Handle load from project."""
    current_project = self.get_current_project()
    if not current_project:
        QMessageBox.warning(self, "No Project", "Please select a project first")
        return
    
    try:
        self.load_from_project(current_project['id'])
        QMessageBox.information(self, "Success", "Data loaded from project")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")
```

## File Organization in Project

```
Project/
├── models/
│   ├── model1.stl
│   └── model2.obj
├── gcode/
│   ├── part1.nc
│   └── part2.gcode
├── cut_lists/
│   ├── cut_list.json
│   └── cut_list.csv
├── feeds_and_speeds/
│   └── feeds_and_speeds.json
├── cost_estimates/
│   └── cost_estimate.json
└── documents/
    ├── notes.txt
    └── README.md
```

## Workflow: Save Tab Data to Project

```
1. User works in tab (e.g., Cut List Optimizer)
2. User clicks "Save to Project"
3. System checks if project is selected
4. System saves data to JSON file
5. System links file to project
6. File appears in Project Manager tree
7. File can be exported with project (DWW)
8. File can be imported with project (DWW)
```

## Workflow: Load Tab Data from Project

```
1. User selects project in Project Manager
2. User clicks "Load from Project" in tab
3. System finds tab data file in project
4. System loads data from file
5. System populates tab with data
6. User can continue working
```

## Best Practices

✅ **Save Regularly**: Auto-save tab data when project changes
✅ **Version Control**: Include timestamps in saved data
✅ **Backup**: Keep backups of tab data files
✅ **Validation**: Validate data before saving
✅ **Error Handling**: Handle save/load errors gracefully
✅ **User Feedback**: Show success/error messages
✅ **File Organization**: Use consistent naming and structure

## Next Steps

1. Add save/load buttons to each tab
2. Implement save_to_project() method in each tab
3. Implement load_from_project() method in each tab
4. Add auto-save functionality
5. Test export/import with tab data
6. Update documentation with examples

## Related Documentation

- `docs/FILE_ORGANISATION_IMPLEMENTATION_PLAN.md` - Project structure
- `docs/DWW_COMPLETE_SYSTEM.md` - Export/import system
- `docs/DWW_USER_GUIDE.md` - User guide

