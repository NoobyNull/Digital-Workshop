# Tab Data Integration - Complete Summary

## Your Question: "How do I save data from the other tabs? And how do I add them to the project?"

## Quick Answer

**3 Simple Steps:**

1. **Save as JSON file** in project directory
2. **Link file to project** in database
3. **File appears in Project Manager tree** and can be exported/imported

## The Tabs

### Already Integrated ✅
- **Model Previewer**: 3D model files (STL, OBJ, STEP, etc.)
- **G Code Previewer**: G-code files (NC, GCODE)

### Need Integration ❌
- **Cut List Optimizer**: Cut pieces, materials, optimization results
- **Feed and Speed**: Tools, presets, calculations
- **Project Cost Estimator**: Materials, labor, machine costs

## How It Works

### Save Workflow

```
User clicks "Save to Project"
    ↓
Gather tab data (cut pieces, tools, costs, etc.)
    ↓
Create JSON file in project directory
    ↓
Link file to project in database
    ↓
File appears in Project Manager tree
    ↓
User sees success message
```

### Load Workflow

```
User clicks "Load from Project"
    ↓
Find tab data file in project
    ↓
Load JSON file
    ↓
Populate tab with data
    ↓
User can continue working
```

### Export/Import Workflow

```
Export:
User clicks "Export as DWW"
    ↓
System includes ALL project files (including tab data)
    ↓
Creates portable DWW archive
    ↓
User can share/backup

Import:
User clicks "Import DWW"
    ↓
System extracts ALL files (including tab data)
    ↓
Creates new project with all files
    ↓
User can load tab data back into tabs
```

## Code Template

### Save Tab Data

```python
from pathlib import Path
from datetime import datetime
import json
from src.core.database.database_manager import get_database_manager

def save_tab_data_to_project(project_id: str, tab_name: str, data: dict, filename: str):
    """Save any tab data to project."""
    
    db_manager = get_database_manager()
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    
    # Create subdirectory
    tab_dir = project_dir / tab_name.lower().replace(" ", "_")
    tab_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON file
    file_path = tab_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Link to project
    db_manager.add_file_to_project(
        project_id=project_id,
        file_path=str(file_path),
        file_name=filename,
        category=tab_name
    )
    
    return str(file_path)
```

### Load Tab Data

```python
def load_tab_data_from_project(project_id: str, filename: str) -> dict:
    """Load tab data from project."""
    
    db_manager = get_database_manager()
    project = db_manager.get_project(project_id)
    project_dir = Path(project['base_path'])
    
    # Find file
    file_path = None
    for root, dirs, files in os.walk(project_dir):
        if filename in files:
            file_path = Path(root) / filename
            break
    
    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"File {filename} not found")
    
    # Load JSON
    with open(file_path, 'r') as f:
        return json.load(f)
```

## File Organization

```
Project/
├── models/
│   ├── model1.stl
│   └── model2.obj
├── gcode/
│   ├── part1.nc
│   └── part2.gcode
├── cut_list_optimizer/
│   └── cut_list.json
├── feed_and_speed/
│   └── feeds_and_speeds.json
├── project_cost_estimator/
│   └── cost_estimate.json
└── documents/
    └── notes.txt
```

## Data Examples

### Cut List Optimizer

```json
{
  "cut_pieces": [
    {"width": 10, "height": 20, "quantity": 5},
    {"width": 15, "height": 25, "quantity": 3}
  ],
  "raw_materials": [
    {"width": 48, "height": 96, "quantity": 2}
  ],
  "optimization_options": {
    "strategy": "Waste Reduction Optimized",
    "blade_rotation": "90° (Standard)",
    "trim_cuts": false,
    "edge_banding": false,
    "priority": "Largest First",
    "rotation": true,
    "kerf": 0.09375
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### Feed and Speed

```json
{
  "tools": [
    {
      "name": "End Mill 1/4",
      "type": "End Mill",
      "diameter": 0.25,
      "flutes": 2,
      "material": "HSS"
    }
  ],
  "presets": [
    {
      "tool": "End Mill 1/4",
      "material": "Aluminum",
      "rpm": 5000,
      "feed": 50,
      "stepdown": 0.25,
      "stepover": 0.125
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

### Project Cost Estimator

```json
{
  "materials": {
    "Wood (Oak)": {
      "cost_per_unit": 15.50,
      "unit": "board_foot",
      "quantity": 10,
      "waste_percentage": 15
    }
  },
  "labor_costs": {
    "hourly_rate": 50,
    "estimated_hours": 8
  },
  "machine_costs": {
    "hourly_rate": 25,
    "estimated_hours": 4
  },
  "total_estimate": 1250.00,
  "timestamp": "2024-01-15T10:30:00"
}
```

## UI Integration

### Add Buttons to Each Tab

```python
# In tab widget
save_button = QPushButton("Save to Project")
save_button.clicked.connect(self._on_save_to_project)

load_button = QPushButton("Load from Project")
load_button.clicked.connect(self._on_load_from_project)

def _on_save_to_project(self):
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

## Key Benefits

✅ **Portable**: Tab data travels with project
✅ **Shareable**: Export entire project with all data
✅ **Recoverable**: Import restores all tab data
✅ **Organized**: Files organized by tab in project tree
✅ **Persistent**: Data saved between sessions
✅ **Integrated**: Works with existing DWW system

## Implementation Phases

### Phase 1: Add Methods
- Add `save_to_project()` to each tab
- Add `load_from_project()` to each tab

### Phase 2: Add UI
- Add "Save to Project" button
- Add "Load from Project" button

### Phase 3: Connect
- Connect to Project Manager
- Notify tabs when project changes

### Phase 4: Auto-Save
- Implement auto-save timer
- Save on interval

### Phase 5: Testing
- Unit tests for each tab
- Integration tests with DWW
- End-to-end testing

## Documentation Files

📄 **TAB_DATA_QUICK_REFERENCE.md** - Quick answers and code templates
📄 **SAVING_TAB_DATA_TO_PROJECT.md** - Detailed implementation guide
📄 **TAB_DATA_IMPLEMENTATION_ROADMAP.md** - Phase-by-phase roadmap
📄 **TAB_DATA_INTEGRATION_SUMMARY.md** - This file

## Next Steps

1. Review the quick reference guide
2. Choose a tab to start with (e.g., Cut List Optimizer)
3. Add `save_to_project()` method
4. Add `load_from_project()` method
5. Add UI buttons
6. Test save/load workflow
7. Test export/import with tab data
8. Repeat for other tabs

## Questions?

- **Quick answers**: See `TAB_DATA_QUICK_REFERENCE.md`
- **Code examples**: See `SAVING_TAB_DATA_TO_PROJECT.md`
- **Implementation plan**: See `TAB_DATA_IMPLEMENTATION_ROADMAP.md`
- **Architecture**: See `FILE_ORGANISATION_IMPLEMENTATION_PLAN.md`

## Summary

**To save tab data to projects:**

1. Create JSON file with tab data
2. Save to project directory
3. Link file to project in database
4. File appears in Project Manager tree
5. File included in DWW export
6. File restored on DWW import

**That's it!** The rest of the system handles the rest.

