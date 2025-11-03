# Tab Data Integration - Implementation Roadmap

## Overview

This roadmap outlines how to integrate tab data (Cut List Optimizer, Feed and Speed, Cost Estimator) with the project system.

## Current State

### ✅ Already Integrated
- **Model Previewer**: Files linked to projects
- **G Code Previewer**: Files linked to projects
- **Project Manager**: Tree view with file organization
- **DWW Export/Import**: Complete system for project portability

### ❌ Not Yet Integrated
- **Cut List Optimizer**: Saves to local files only
- **Feed and Speed**: Saves to QSettings only
- **Project Cost Estimator**: Saves to local files only

## Integration Strategy

### Phase 1: Add Save/Load Methods to Each Tab

**Files to Modify**:
- `src/gui/CLO/cut_list_optimizer_widget.py`
- `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py`
- `src/gui/cost_estimator/cost_estimator_widget.py`

**Changes**:
```python
# Add to each tab widget
def save_to_project(self, project_id: str) -> bool:
    """Save tab data to project."""
    # Gather data
    # Create JSON file
    # Link to project
    # Return success

def load_from_project(self, project_id: str) -> bool:
    """Load tab data from project."""
    # Find data file
    # Load JSON
    # Populate tab
    # Return success
```

### Phase 2: Add UI Buttons

**Files to Modify**:
- `src/gui/CLO/cut_list_optimizer_widget.py`
- `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py`
- `src/gui/cost_estimator/cost_estimator_widget.py`

**Changes**:
```python
# Add to each tab's UI setup
save_button = QPushButton("Save to Project")
save_button.clicked.connect(self._on_save_to_project)

load_button = QPushButton("Load from Project")
load_button.clicked.connect(self._on_load_from_project)
```

### Phase 3: Connect to Project Manager

**Files to Modify**:
- `src/gui/project_manager/project_tree_widget.py`

**Changes**:
```python
# Add signal to notify tabs when project changes
project_selected = Signal(str)  # project_id

# Connect to tabs
self.project_selected.connect(self.cut_list_widget.on_project_selected)
self.project_selected.connect(self.feeds_widget.on_project_selected)
self.project_selected.connect(self.cost_widget.on_project_selected)
```

### Phase 4: Auto-Save Implementation

**Files to Create**:
- `src/core/services/tab_data_manager.py`

**Features**:
```python
class TabDataManager:
    """Manages auto-save for tab data."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.auto_save_enabled = True
        self.auto_save_interval = 5 * 60  # 5 minutes
    
    def register_tab(self, tab_widget, project_id):
        """Register tab for auto-save."""
        # Start auto-save timer
        # Save on interval
    
    def save_all_tabs(self, project_id):
        """Save all registered tabs."""
        # Call save_to_project on each tab
```

### Phase 5: Testing

**Files to Create**:
- `tests/test_tab_data_integration.py`

**Test Cases**:
```python
def test_save_cut_list_to_project():
    """Test saving cut list to project."""
    
def test_load_cut_list_from_project():
    """Test loading cut list from project."""
    
def test_export_import_with_tab_data():
    """Test DWW export/import includes tab data."""
    
def test_auto_save_tab_data():
    """Test auto-save functionality."""
```

## Implementation Details

### Cut List Optimizer

**Data to Save**:
```python
{
    'cut_pieces': [
        {'width': 10, 'height': 20, 'quantity': 5},
        ...
    ],
    'raw_materials': [
        {'width': 48, 'height': 96, 'quantity': 2},
        ...
    ],
    'optimization_options': {
        'strategy': 'Waste Reduction Optimized',
        'blade_rotation': '90° (Standard)',
        'trim_cuts': False,
        'edge_banding': False,
        'priority': 'Largest First',
        'rotation': True,
        'kerf': 0.09375
    },
    'timestamp': '2024-01-15T10:30:00'
}
```

**File Location**: `project/cut_list_optimizer/cut_list.json`

### Feed and Speed

**Data to Save**:
```python
{
    'tools': [
        {
            'name': 'Tool 1',
            'type': 'End Mill',
            'diameter': 0.25,
            'flutes': 2,
            'material': 'HSS'
        },
        ...
    ],
    'presets': [
        {
            'tool': 'Tool 1',
            'material': 'Aluminum',
            'rpm': 5000,
            'feed': 50,
            'stepdown': 0.25,
            'stepover': 0.125
        },
        ...
    ],
    'timestamp': '2024-01-15T10:30:00'
}
```

**File Location**: `project/feed_and_speed/feeds_and_speeds.json`

### Project Cost Estimator

**Data to Save**:
```python
{
    'materials': {
        'Wood (Oak)': {
            'cost_per_unit': 15.50,
            'unit': 'board_foot',
            'quantity': 10,
            'waste_percentage': 15
        },
        ...
    },
    'labor_costs': {
        'hourly_rate': 50,
        'estimated_hours': 8
    },
    'machine_costs': {
        'hourly_rate': 25,
        'estimated_hours': 4
    },
    'total_estimate': 1250.00,
    'timestamp': '2024-01-15T10:30:00'
}
```

**File Location**: `project/project_cost_estimator/cost_estimate.json`

## Timeline

### Week 1: Phase 1 & 2
- Add save/load methods to each tab
- Add UI buttons
- Basic testing

### Week 2: Phase 3 & 4
- Connect to Project Manager
- Implement auto-save
- Integration testing

### Week 3: Phase 5
- Comprehensive testing
- Bug fixes
- Documentation

## Success Criteria

✅ Each tab can save data to project
✅ Each tab can load data from project
✅ Tab data appears in Project Manager tree
✅ Tab data included in DWW export
✅ Tab data restored on DWW import
✅ Auto-save works correctly
✅ All tests passing
✅ Documentation complete

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Data loss | Implement auto-save and backups |
| File conflicts | Use unique filenames and directories |
| Performance | Implement lazy loading for large files |
| Compatibility | Version tab data format |

## Dependencies

- `src/core/database_manager.py` - Project and file management
- `src/core/export/dww_export_manager.py` - Export functionality
- `src/core/export/dww_import_manager.py` - Import functionality
- `src/gui/project_manager/project_tree_widget.py` - Project UI

## Related Documentation

- `docs/SAVING_TAB_DATA_TO_PROJECT.md` - Detailed implementation guide
- `docs/TAB_DATA_QUICK_REFERENCE.md` - Quick reference
- `docs/FILE_ORGANISATION_IMPLEMENTATION_PLAN.md` - Project structure
- `docs/DWW_COMPLETE_SYSTEM.md` - Export/import system

## Next Steps

1. Review this roadmap with team
2. Prioritize phases
3. Assign developers
4. Create detailed task tickets
5. Begin Phase 1 implementation
6. Set up continuous testing
7. Deploy incrementally

## Questions?

Refer to:
- `docs/TAB_DATA_QUICK_REFERENCE.md` for quick answers
- `docs/SAVING_TAB_DATA_TO_PROJECT.md` for detailed examples
- Code comments in implementation files

