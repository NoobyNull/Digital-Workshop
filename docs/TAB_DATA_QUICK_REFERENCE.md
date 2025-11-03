# Tab Data - Quick Reference Guide

## Quick Answer: How to Save Tab Data to Projects

### **3 Simple Steps:**

```
1. Save data as JSON file in project directory
2. Link file to project in database
3. File appears in Project Manager tree
```

## Tab Data Summary

| Tab | Data Type | Current Storage | How to Save |
|-----|-----------|-----------------|------------|
| **Model Previewer** | 3D Models (STL, OBJ, STEP) | Project files | ✅ Already linked |
| **G Code Previewer** | G-Code (NC, GCODE) | Project files | ✅ Already linked |
| **Cut List Optimizer** | Cut pieces, materials, results | Local JSON | Save as project file |
| **Feed and Speed** | Tools, presets, calculations | QSettings | Save as project file |
| **Project Cost Estimator** | Materials, labor, machine costs | Local JSON | Save as project file |

## Code Template: Save Tab Data

```python
from pathlib import Path
from datetime import datetime
import json
from src.core.database.database_manager import get_database_manager

def save_tab_data_to_project(project_id: str, tab_name: str, data: dict, filename: str):
    """Generic function to save any tab data to project."""
    
    db_manager = get_database_manager()
    
    # Get project
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    
    # Create subdirectory for tab data
    tab_dir = project_dir / tab_name.lower().replace(" ", "_")
    tab_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data to JSON file
    file_path = tab_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Link file to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(file_path),
        file_name=filename,
        category=tab_name
    )
    
    return str(file_path)
```

## Usage Examples

### Cut List Optimizer

```python
# Save cut list
cut_list_data = {
    'cut_pieces': widget.cut_pieces,
    'raw_materials': widget.raw_materials,
    'optimization_options': widget.optimization_options,
    'timestamp': datetime.now().isoformat()
}

save_tab_data_to_project(
    project_id="project-uuid",
    tab_name="Cut List Optimizer",
    data=cut_list_data,
    filename="cut_list.json"
)
```

### Feed and Speed

```python
# Save feeds and speeds
feeds_data = {
    'tools': widget.tool_database_manager.get_all_tools(),
    'presets': widget.personal_toolbox_manager.get_toolbox(),
    'timestamp': datetime.now().isoformat()
}

save_tab_data_to_project(
    project_id="project-uuid",
    tab_name="Feed and Speed",
    data=feeds_data,
    filename="feeds_and_speeds.json"
)
```

### Project Cost Estimator

```python
# Save cost estimate
cost_data = {
    'materials': widget.material_cost_manager.get_materials(),
    'labor_costs': widget.get_labor_costs(),
    'machine_costs': widget.get_machine_costs(),
    'total': widget.calculate_total(),
    'timestamp': datetime.now().isoformat()
}

save_tab_data_to_project(
    project_id="project-uuid",
    tab_name="Project Cost Estimator",
    data=cost_data,
    filename="cost_estimate.json"
)
```

## Code Template: Load Tab Data

```python
def load_tab_data_from_project(project_id: str, filename: str) -> dict:
    """Load tab data from project."""
    
    db_manager = get_database_manager()
    
    # Get project
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    
    # Find file in project
    file_path = None
    for root, dirs, files in os.walk(project_dir):
        if filename in files:
            file_path = Path(root) / filename
            break
    
    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"File {filename} not found in project")
    
    # Load data
    with open(file_path, 'r') as f:
        return json.load(f)
```

## Integration Points

### 1. **Project Manager Tree**
- Tab data files appear as project files
- Can be clicked to view/edit
- Can be exported with project

### 2. **DWW Export/Import**
- Tab data files included in DWW archive
- Automatically restored on import
- Preserves all project data

### 3. **File Organization**
```
Project/
├── cut_list_optimizer/
│   └── cut_list.json
├── feed_and_speed/
│   └── feeds_and_speeds.json
├── project_cost_estimator/
│   └── cost_estimate.json
├── models/
│   └── model.stl
└── gcode/
    └── part.nc
```

## UI Integration

### Add Save Button to Tab

```python
# In tab widget __init__
save_button = QPushButton("Save to Project")
save_button.clicked.connect(self._on_save_to_project)
layout.addWidget(save_button)

def _on_save_to_project(self):
    """Save tab data to current project."""
    project = self.get_current_project()
    if not project:
        QMessageBox.warning(self, "No Project", "Select a project first")
        return
    
    try:
        data = self.get_tab_data()
        save_tab_data_to_project(
            project['id'],
            self.tab_name,
            data,
            self.filename
        )
        QMessageBox.information(self, "Success", "Data saved to project")
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))
```

### Add Load Button to Tab

```python
load_button = QPushButton("Load from Project")
load_button.clicked.connect(self._on_load_from_project)
layout.addWidget(load_button)

def _on_load_from_project(self):
    """Load tab data from current project."""
    project = self.get_current_project()
    if not project:
        QMessageBox.warning(self, "No Project", "Select a project first")
        return
    
    try:
        data = load_tab_data_from_project(project['id'], self.filename)
        self.load_tab_data(data)
        QMessageBox.information(self, "Success", "Data loaded from project")
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))
```

## Workflow Summary

### Save Workflow
```
User clicks "Save to Project"
    ↓
Get current project
    ↓
Gather tab data
    ↓
Create JSON file in project directory
    ↓
Link file to project in database
    ↓
Show success message
    ↓
File appears in Project Manager tree
```

### Load Workflow
```
User clicks "Load from Project"
    ↓
Get current project
    ↓
Find tab data file in project
    ↓
Load JSON file
    ↓
Populate tab with data
    ↓
Show success message
```

### Export Workflow
```
User clicks "Export as DWW"
    ↓
System gathers all project files (including tab data)
    ↓
Creates DWW archive with all files
    ↓
Includes manifest and integrity verification
    ↓
User can share/backup DWW file
```

### Import Workflow
```
User clicks "Import DWW"
    ↓
Select DWW file
    ↓
System extracts all files (including tab data)
    ↓
Creates new project with all files
    ↓
Tab data files linked to project
    ↓
User can load tab data into tabs
```

## Key Points

✅ **Tab data is stored as JSON files** in project directory
✅ **Files are linked to project** in database
✅ **Files appear in Project Manager tree** for easy access
✅ **Files are included in DWW export** for portability
✅ **Files are restored on DWW import** automatically
✅ **Each tab can have save/load buttons** for user control
✅ **Auto-save can be implemented** for convenience

## Related Files

- `docs/SAVING_TAB_DATA_TO_PROJECT.md` - Detailed guide
- `docs/FILE_ORGANISATION_IMPLEMENTATION_PLAN.md` - Project structure
- `docs/DWW_COMPLETE_SYSTEM.md` - Export/import system

