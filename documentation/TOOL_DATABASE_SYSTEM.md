# Tool Database Management System - Comprehensive Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Requirements & Setup](#system-requirements--setup)
3. [Architecture & Implementation](#architecture--implementation)
4. [Database Schema](#database-schema)
5. [File Formats Supported](#file-formats-supported)
6. [User Guide](#user-guide)
   - [Importing Tools](#importing-tools)
   - [Exporting Tools](#exporting-tools)
   - [Managing Preferences](#managing-preferences)
7. [API Reference for Developers](#api-reference-for-developers)
8. [Integration with Feeds and Speeds](#integration-with-feeds-and-speeds)
9. [Performance Characteristics](#performance-characteristics)
10. [Known Issues & Limitations](#known-issues--limitations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Testing & Validation](#testing--validation)
13. [Quality Standards & Memory Management](#quality-standards--memory-management)
14. [FAQ & Best Practices](#faq--best-practices)

---

## Overview

The Tool Database Management System is a comprehensive solution for managing tool definitions from multiple formats (CSV, JSON, VTDB, TDB) within the Digital Workshop application. This system provides a unified SQLite-based database for storing, organizing, searching, and exporting tool information used for feeds and speeds calculations.

### Key Capabilities

- **Multi-format support** - Import from CSV, JSON, VTDB, and TDB formats
- **Unified database** - SQLite-based central repository for all tools
- **Provider management** - Organize tools by vendor/provider
- **Advanced search** - Filter and search tools by diameter, type, vendor, and custom properties
- **Import/Export** - Move tools between databases and formats
- **UI Integration** - Seamless integration with Feeds and Speeds widget
- **Preferences system** - User-configurable settings and external database paths
- **Quality standards** - JSON logging, comprehensive error handling, memory efficiency

---

## System Requirements & Setup

### Hardware Requirements

**Minimum:**
- OS: Windows 7 SP1 (64-bit)
- CPU: Intel Core i3-3220 or equivalent
- RAM: 4GB
- Storage: 100MB free space

**Recommended:**
- OS: Windows 10/11 (64-bit)
- CPU: Intel Core i5-3470 or equivalent
- RAM: 8GB
- Storage: 500MB free space (SSD recommended)

### Software Requirements

**Required:**
- Python 3.8-3.12 (64-bit)
- PySide6 6.0.0+
- SQLite 3.0+ (built-in with Python)

**Optional:**
- NumPy 1.24.0+ (for geometry calculations)
- lxml 4.6.0+ (for advanced XML parsing)

### Installation & Setup

1. **Database Initialization**

   The system automatically initializes the SQLite database on first use:

   ```python
   from src.core.database.tool_database_schema import ToolDatabaseSchema
   
   # Initialize database schema
   schema = ToolDatabaseSchema("tools.db")
   schema.initialize_database()
   ```

2. **File Structure**

   ```
   src/
   ├── core/
   │   └── database/
   │       ├── tool_database_schema.py
   │       ├── tool_database_repository.py
   │       ├── provider_repository.py
   │       └── tool_preferences_repository.py
   ├── gui/
   │   └── widgets/
   │       ├── add_tool_dialog.py
   │       ├── external_database_editor.py
   │       └── tool_database_preferences.py
   └── parsers/
       ├── tool_database_manager.py
       ├── tool_migration_utility.py
       ├── tool_export_manager.py
       └── tool_parsers/
           ├── base_tool_parser.py
           ├── csv_tool_parser.py
           ├── json_tool_parser.py
           ├── vtdb_tool_parser.py
           └── tdb_tool_parser.py
   ```

---

## Architecture & Implementation

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Digital Workshop Application                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │         UI Layer (PySide6 Widgets)              │    │
│  │                                                  │    │
│  │  • AddToolDialog - Tool selection & browsing   │    │
│  │  • ExternalDatabaseEditor - Viewer/Editor      │    │
│  │  • ToolDatabasePreferences - Configuration     │    │
│  └─────────────────────────────────────────────────┘    │
│                          ▲                               │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │    Business Logic Layer (Managers)              │    │
│  │                                                  │    │
│  │  • ToolDatabaseManager - Central coordinator   │    │
│  │  • ToolExportManager - Export functionality    │    │
│  │  • ToolMigrationUtility - Data migration       │    │
│  └─────────────────────────────────────────────────┘    │
│                          ▲                               │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │     Parser Layer (Format Handlers)              │    │
│  │                                                  │    │
│  │  • CSVToolParser - IDC Carbide format          │    │
│  │  • JSONToolParser - Fusion360 format           │    │
│  │  • VTDBToolParser - Vectric format             │    │
│  │  • TDBToolParser - Carveco format              │    │
│  └─────────────────────────────────────────────────┘    │
│                          ▲                               │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │      Data Access Layer (Repositories)           │    │
│  │                                                  │    │
│  │  • ToolDatabaseRepository - Tool CRUD           │    │
│  │  • ProviderRepository - Provider management     │    │
│  │  • ToolPreferencesRepository - Settings         │    │
│  └─────────────────────────────────────────────────┘    │
│                          ▲                               │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │      SQLite Database Layer                       │    │
│  │                                                  │    │
│  │  • Providers Table - Tool vendors               │    │
│  │  • Tools Table - Tool definitions               │    │
│  │  • ToolProperties Table - Custom properties     │    │
│  │  • Preferences Table - System settings          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Component Overview

#### Database Layer
- **tool_database_schema.py** - SQLite schema definition and initialization
- **tool_database_repository.py** - Tool CRUD operations and queries
- **provider_repository.py** - Provider management
- **tool_preferences_repository.py** - User preferences storage

#### Parser Layer
- **base_tool_parser.py** - Abstract base class for all parsers
- **csv_tool_parser.py** - CSV format parser (IDC Carbide)
- **json_tool_parser.py** - JSON format parser (Fusion 360)
- **vtdb_tool_parser.py** - VTDB format parser (Vectric)
- **tdb_tool_parser.py** - TDB format parser (Carveco)

#### Business Logic Layer
- **tool_database_manager.py** - Unified manager coordinating all operations
- **tool_export_manager.py** - Export tools to external formats
- **tool_migration_utility.py** - Data migration utilities

#### UI Layer
- **add_tool_dialog.py** - Dialog for browsing and selecting tools
- **external_database_editor.py** - External database viewer/editor
- **tool_database_preferences.py** - Settings and preferences UI

---

## Database Schema

### Providers Table

Stores tool provider/vendor information.

```sql
CREATE TABLE Providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id` - Unique provider identifier
- `name` - Provider name (unique)
- `description` - Provider description
- `created_at` - Creation timestamp

### Tools Table

Stores individual tool definitions.

```sql
CREATE TABLE Tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE,
    provider_id INTEGER NOT NULL,
    description TEXT,
    type TEXT,
    diameter REAL,
    vendor TEXT,
    geometry TEXT,
    start_values TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(provider_id) REFERENCES Providers(id)
);
```

**Fields:**
- `id` - Unique tool identifier
- `guid` - External unique identifier (optional)
- `provider_id` - Reference to provider
- `description` - Tool name/description
- `type` - Tool type (End Mill, Ball Nose, etc.)
- `diameter` - Tool diameter in inches
- `vendor` - Vendor/manufacturer name
- `geometry` - JSON string with geometry data
- `start_values` - JSON string with initial speed/feed values
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### ToolProperties Table

Stores custom properties for tools.

```sql
CREATE TABLE ToolProperties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    FOREIGN KEY(tool_id) REFERENCES Tools(id),
    UNIQUE(tool_id, key)
);
```

**Fields:**
- `id` - Unique property identifier
- `tool_id` - Reference to tool
- `key` - Property key name
- `value` - Property value (JSON string for complex types)

### Preferences Table

Stores system preferences and user settings.

```sql
CREATE TABLE Preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id` - Unique preference identifier
- `key` - Preference key
- `value` - Preference value (JSON for complex types)
- `created_at` - Creation timestamp

---

## File Formats Supported

### 1. CSV Format (IDC-Woodcraft-Carbide-Create-Database)

**Parser:** [`CSVToolParser`](../src/parsers/tool_parsers/csv_tool_parser.py)

Expected columns:
- GUID (optional, unique identifier)
- Description (tool name)
- Type (tool type classification)
- Diameter (in mm or inches)
- Vendor (manufacturer)
- Flute Length, Overall Length, etc. (geometry data)

**Example:**
```csv
GUID,Description,Type,Diameter (mm),Vendor,Flute Length (mm),Overall Length (mm)
tool-001,Carbide End Mill 3.175mm,End Mill,3.175,IDC Woodcraft,10,50
tool-002,Carbide Ball Nose 6.35mm,Ball Nose,6.35,IDC Woodcraft,15,60
```

### 2. JSON Format (IDCWoodcraftFusion360Library)

**Parser:** [`JSONToolParser`](../src/parsers/tool_parsers/json_tool_parser.py)

Expected structure:
```json
{
  "tools": [
    {
      "guid": "tool-uuid",
      "description": "Tool Name",
      "type": "End Mill",
      "diameter": 0.25,
      "vendor": "IDC",
      "geometry": {
        "fluteLength": 10,
        "overallLength": 50,
        "fluteCount": 2
      },
      "startValues": {
        "rpm": 18000,
        "feedRate": 100
      }
    }
  ]
}
```

### 3. VTDB Format (Vectric Tool Database)

**Parser:** [`VTDBToolParser`](../src/parsers/tool_parsers/vtdb_tool_parser.py)

- SQLite-based format used by Vectric CNC software
- Contains embedded tool definitions and macros
- Automatically detected by file extension (.vtdb)
- Efficiently batch-processed for large datasets

### 4. TDB Format (Carveco Tool Database)

**Parser:** [`TDBToolParser`](../src/parsers/tool_parsers/tdb_tool_parser.py)

- Binary format with UTF-16 encoding
- Used by CarveWare/Carveco software
- Magic byte validation for file integrity
- Struct-based binary data unpacking

---

## User Guide

### Importing Tools

#### Importing from CSV

1. **Open Add Tool Dialog**
   ```
   Menu: Tools → Import Tools
   or
   Button: Add Tool in Feeds and Speeds window
   ```

2. **Select CSV File**
   - Navigate to your CSV file
   - Click "Open"

3. **Choose Provider**
   - Select existing provider or enter new name
   - Provide description (optional)

4. **Review Import**
   - System validates file format
   - Shows preview of tools to import
   - Displays any warnings or errors

5. **Import Tools**
   - Click "Import"
   - Progress dialog shows import status
   - Tools are added to database

**Python API:**
```python
from src.parsers.tool_database_manager import ToolDatabaseManager

manager = ToolDatabaseManager("tools.db")

def progress_callback(progress, message):
    print(f"{message}: {progress*100:.1f}%")

success, imported_count, errors = manager.import_tools_from_file(
    file_path="IDC-Woodcraft-Carbide-Create-Database-5-2-2025.csv",
    provider_name="IDC-Carbide",
    progress_callback=progress_callback
)

if success:
    print(f"Successfully imported {imported_count} tools")
    if errors:
        print(f"Warnings: {len(errors)} issues encountered")
```

#### Importing from JSON

1. Same process as CSV
2. System auto-detects JSON format
3. Recursively handles nested tool properties
4. Validates JSON structure

**Python API:**
```python
# Same as CSV - format is auto-detected
manager.import_tools_from_file(
    file_path="IDCWoodcraftFusion360Library.json",
    provider_name="IDC-Fusion360"
)
```

#### Importing from VTDB (Vectric)

1. Select .vtdb file
2. System reads SQLite database embedded in VTDB
3. Maps Vectric tool definitions to standard format
4. Batch processes for efficiency

```python
manager.import_tools_from_file(
    file_path="IDC Woodcraft Vectric Tool Database.vtdb",
    provider_name="IDC-Vectric"
)
```

#### Importing from TDB (Carveco)

1. Select .tdb file
2. System validates binary format (magic bytes)
3. Decodes UTF-16 encoded tool data
4. Extracts tool definitions from binary structure

```python
manager.import_tools_from_file(
    file_path="IDC-Woodcraft-Carveco-Tool-Database.tdb",
    provider_name="IDC-Carveco"
)
```

### Exporting Tools

#### Export to CSV

```python
from src.parsers.tool_export_manager import ToolExportManager

exporter = ToolExportManager("tools.db")

success = exporter.export_to_csv(
    output_path="exported_tools.csv",
    provider_ids=[1, 2],  # Optional: specific providers
    include_properties=True
)
```

#### Export to JSON

```python
success = exporter.export_to_json(
    output_path="exported_tools.json",
    provider_ids=[1, 2],
    include_geometry=True,
    include_start_values=True
)
```

#### Export to External Database

```python
success = exporter.export_to_database(
    output_path="external_tools.db",
    provider_ids=[1, 2],
    format="csv"  # or "json"
)
```

### Managing Preferences

#### Set Preferences

```python
from src.core.database.tool_preferences_repository import ToolPreferencesRepository

prefs = ToolPreferencesRepository("tools.db")

# Set external database paths
prefs.set_preference(
    "external_database_paths",
    {
        "csv": "/path/to/csv/databases",
        "json": "/path/to/json/databases",
        "vtdb": "/path/to/vtdb/databases"
    }
)

# Set default provider
prefs.set_preference("default_provider_id", "1")

# Enable auto-import
prefs.set_preference("auto_import_enabled", "true")
prefs.set_preference("auto_import_interval", "3600")  # seconds
```

#### Get Preferences

```python
db_paths = prefs.get_preference("external_database_paths")
default_provider = prefs.get_preference("default_provider_id")

# Access with defaults
db_path = prefs.get_preference("external_database_path", "/default/path")
```

#### Using Preferences UI

1. **Open Preferences Dialog**
   ```
   Menu: Edit → Preferences
   Tab: Tool Database
   ```

2. **Configure Settings**
   - Database location
   - External database paths
   - Auto-import settings
   - Provider defaults

3. **Save Changes**
   - Changes persist immediately
   - Validation occurs on save

---

## API Reference for Developers

### ToolDatabaseManager

Central coordinator for all tool database operations.

```python
from src.parsers.tool_database_manager import ToolDatabaseManager

manager = ToolDatabaseManager(db_path="tools.db")
```

#### Methods

**`import_tools_from_file(file_path, provider_name, progress_callback=None)`**

Import tools from any supported file format.

```python
success, imported_count, errors = manager.import_tools_from_file(
    file_path="tools.csv",
    provider_name="MyProvider",
    progress_callback=lambda p, m: print(f"{m}: {p*100:.0f}%")
)
```

**`export_tools(output_path, provider_ids=None, format='csv')`**

Export tools to external database or file.

```python
success = manager.export_tools(
    output_path="backup.db",
    provider_ids=[1, 2, 3],
    format="csv"
)
```

**`search_tools(tool_type=None, vendor=None, diameter_min=None, diameter_max=None)`**

Search tools with optional filters.

```python
tools = manager.search_tools(
    tool_type="End Mill",
    vendor="IDC",
    diameter_min=0.1,
    diameter_max=0.5
)

for tool in tools:
    print(f"{tool['description']}: {tool['diameter']} inch")
```

**`get_providers()`**

Get list of all providers.

```python
providers = manager.get_providers()
for provider in providers:
    print(f"ID: {provider['id']}, Name: {provider['name']}")
```

**`get_tools_for_provider(provider_id)`**

Get all tools from specific provider.

```python
tools = manager.get_tools_for_provider(provider_id=1)
```

### ToolDatabaseRepository

Manages tool CRUD operations and queries.

```python
from src.core.database.tool_database_repository import ToolDatabaseRepository

repo = ToolDatabaseRepository("tools.db")
```

#### Methods

**`add_tool(provider_id, guid, description, tool_type, diameter, vendor, geometry_data, start_values)`**

Add a new tool.

```python
tool_id = repo.add_tool(
    provider_id=1,
    guid="tool-123",
    description="Carbide End Mill 1/4",
    tool_type="End Mill",
    diameter=0.25,
    vendor="Carbide",
    geometry_data={"flute_length": 10},
    start_values={"rpm": 18000, "feed": 100}
)
```

**`get_tool(tool_id)`**

Retrieve tool by ID.

```python
tool = repo.get_tool(tool_id=1)
print(tool['description'])
```

**`update_tool(tool_id, **kwargs)`**

Update tool properties.

```python
repo.update_tool(tool_id=1, description="Updated Name", diameter=0.3)
```

**`delete_tool(tool_id)`**

Delete tool.

```python
repo.delete_tool(tool_id=1)
```

**`search_tools(tool_type=None, vendor=None, description=None)`**

Search tools.

```python
results = repo.search_tools(tool_type="End Mill", vendor="IDC")
```

**`filter_by_diameter(min_diameter, max_diameter)`**

Filter tools by diameter range.

```python
small_tools = repo.filter_by_diameter(0.1, 0.25)
```

**`add_tool_properties(tool_id, properties)`**

Add custom properties to tool.

```python
repo.add_tool_properties(
    tool_id=1,
    properties={
        "flute_count": 2,
        "material": "carbide",
        "max_rpm": 24000
    }
)
```

**`get_tool_properties(tool_id)`**

Retrieve tool properties.

```python
props = repo.get_tool_properties(tool_id=1)
print(props["flute_count"])
```

### ProviderRepository

Manages tool providers/vendors.

```python
from src.core.database.provider_repository import ProviderRepository

provider_repo = ProviderRepository("tools.db")
```

#### Methods

**`add_provider(name, description, format_type)`**

Create new provider.

```python
provider_id = provider_repo.add_provider(
    name="IDC Woodcraft",
    description="IDC Woodcraft tool database",
    format_type="CSV"
)
```

**`get_provider(provider_id)`**

Retrieve provider.

```python
provider = provider_repo.get_provider(provider_id=1)
```

**`list_providers()`**

Get all providers.

```python
providers = provider_repo.list_providers()
```

**`update_provider(provider_id, **kwargs)`**

Update provider.

```python
provider_repo.update_provider(provider_id=1, description="Updated description")
```

**`delete_provider(provider_id)`**

Delete provider.

```python
provider_repo.delete_provider(provider_id=1)
```

### ToolPreferencesRepository

Manages user preferences.

```python
from src.core.database.tool_preferences_repository import ToolPreferencesRepository

prefs = ToolPreferencesRepository("tools.db")
```

#### Methods

**`set_preference(key, value)`**

Set preference value.

```python
prefs.set_preference("external_db_path", "/path/to/db")
```

**`get_preference(key, default=None)`**

Get preference value.

```python
value = prefs.get_preference("external_db_path", "/default")
```

**`delete_preference(key)`**

Delete preference.

```python
prefs.delete_preference("external_db_path")
```

### BaseToolParser

Abstract base class for format-specific parsers.

```python
from src.parsers.tool_parsers import BaseToolParser, ToolData

class CustomToolParser(BaseToolParser):
    def validate_file(self, file_path: str) -> tuple:
        # Implement validation
        pass
    
    def parse(self, file_path: str, progress_callback=None) -> list:
        # Implement parsing
        # Return list of ToolData objects
        pass
    
    def get_format_name(self) -> str:
        return "CustomFormat"
```

### ToolData Dataclass

Represents a single tool.

```python
from src.parsers.tool_parsers import ToolData

tool = ToolData(
    guid="tool-001",
    description="Carbide End Mill",
    tool_type="End Mill",
    diameter=3.175,
    vendor="IDC",
    geometry_data={"flute_length": 10},
    start_values={"rpm": 18000},
    custom_properties={"flute_count": 2}
)

print(tool.description)
```

---

## Integration with Feeds and Speeds

### Integrating AddToolDialog

```python
from src.gui.widgets.add_tool_dialog import AddToolDialog
from PySide6.QtWidgets import QDialog

# In your Feeds and Speeds widget
def add_tool_from_database(self):
    dialog = AddToolDialog(parent=self, db_path="tools.db")
    
    if dialog.exec() == QDialog.Accepted:
        selected_tools = dialog.get_selected_tools()
        
        for tool in selected_tools:
            self.add_tool_to_calculator(tool)
```

### Accessing Tool Data in Calculator

```python
def add_tool_to_calculator(self, tool_data):
    # tool_data contains:
    # - tool_data['description']
    # - tool_data['diameter']
    # - tool_data['type']
    # - tool_data['geometry']
    # - tool_data['start_values']
    
    self.tool_name.setText(tool_data['description'])
    self.tool_diameter.setValue(tool_data['diameter'])
    
    # Use start_values if available
    if tool_data.get('start_values'):
        start_vals = json.loads(tool_data['start_values'])
        if 'rpm' in start_vals:
            self.rpm_spinbox.setValue(start_vals['rpm'])
```

### Exporting Tool Configurations

```python
def export_current_tool_settings(self):
    from src.parsers.tool_export_manager import ToolExportManager
    
    exporter = ToolExportManager("tools.db")
    
    # Export current tool as new entry
    tool_data = {
        'description': self.tool_name.text(),
        'diameter': self.tool_diameter.value(),
        'type': self.tool_type.currentText(),
        'geometry': json.dumps(self.current_geometry),
        'start_values': json.dumps({
            'rpm': self.rpm_spinbox.value(),
            'feed': self.feed_spinbox.value()
        })
    }
    
    success = exporter.export_tool(tool_data)
```

---

## Performance Characteristics

### Load Time Requirements

- Files under 100MB: < 5 seconds
- Files 100-500MB: < 15 seconds
- Files over 500MB: < 30 seconds

### Memory Management

- Maximum memory usage: 2GB for typical usage
- Streaming parsing for large files
- Configurable batch processing
- Automatic resource cleanup

### Database Performance

- Indexed queries for tool searches
- Batch insert operations for bulk imports
- Lazy loading for large datasets
- Connection pooling support

### Optimization Guidelines

**1. Use Progress Callbacks**

```python
def on_progress(progress, message):
    # Update UI with progress
    self.progress_bar.setValue(int(progress * 100))
    self.status_label.setText(message)

manager.import_tools_from_file(
    file_path="large_file.csv",
    provider_name="Provider",
    progress_callback=on_progress
)
```

**2. Batch Operations**

```python
# Import multiple files in sequence
for file_path in file_list:
    manager.import_tools_from_file(file_path, provider_name)
```

**3. Search Optimization**

```python
# Use specific filters to reduce result set
tools = repo.filter_by_diameter(0.1, 0.5)  # Faster
tools = repo.search_tools(tool_type="End Mill")  # Uses index
```

**4. Periodic Maintenance**

```python
# Vacuum database periodically
import sqlite3
conn = sqlite3.connect("tools.db")
conn.execute("VACUUM")
conn.close()
```

---

## Known Issues & Limitations

### Identified Issues

1. **Large File Import Performance**
   - **Issue**: CSV files over 500MB may take longer than 30 seconds
   - **Status**: Performance optimization in progress
   - **Workaround**: Split large files or use batch import with smaller chunks

2. **VTDB Format Incompatibility**
   - **Issue**: Some VTDB databases from older Vectric versions (pre-2020) may not parse correctly
   - **Status**: Partial support; newer versions fully supported
   - **Workaround**: Export VTDB to CSV and reimport

3. **TDB Binary Format Edge Cases**
   - **Issue**: TDB files with custom encoding variants may fail
   - **Status**: UTF-16 standard supported; variants documented
   - **Workaround**: Convert TDB to CSV using original software

4. **Memory Usage with Many Custom Properties**
   - **Issue**: Tools with >1000 custom properties may impact performance
   - **Status**: Normal; design limitation
   - **Workaround**: Archive old properties or split into multiple tools

5. **Unicode Handling in Tool Names**
   - **Issue**: Some special Unicode characters in tool descriptions may be truncated
   - **Status**: Limited by SQLite text encoding
   - **Workaround**: Use ASCII-compatible descriptions

### Limitations

1. **Maximum Database Size**: SQLite has a practical limit of ~2TB, but application limits to 2GB for stability

2. **Concurrent Access**: SQLite doesn't support concurrent writes; only one import at a time

3. **File Format Conversion**: Lossy conversion between formats (some properties may not convert)

4. **Provider Relationships**: Tools can belong to only one provider; multi-provider tools require duplication

5. **Version Compatibility**: Database schema locked to version; no automatic migrations

---

## Troubleshooting Guide

### Import Issues

#### Problem: "File not found" error

**Solution:**
1. Verify file path is correct
2. Check file exists: `dir filename.csv`
3. Ensure you have read permissions
4. Try using absolute path instead of relative

#### Problem: "Invalid CSV format" error

**Solution:**
1. Verify CSV has required columns (GUID, Description, Type, Diameter, Vendor)
2. Check for special characters in column headers
3. Ensure consistent column count in all rows
4. Try opening in Excel to verify format

**Example - Check CSV:**
```python
import csv

def validate_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        required_fields = ['GUID', 'Description', 'Type', 'Diameter', 'Vendor']
        
        if reader.fieldnames:
            missing = [f for f in required_fields if f not in reader.fieldnames]
            if missing:
                print(f"Missing fields: {missing}")
                return False
    return True
```

#### Problem: "JSON parsing failed" error

**Solution:**
1. Validate JSON syntax: Use `python -m json.tool filename.json`
2. Check for trailing commas
3. Ensure all quotes are proper JSON (not smart quotes)
4. Use online JSON validator

```python
import json

def validate_json(file_path):
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        print("JSON is valid")
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
```

#### Problem: VTDB file won't import

**Solution:**
1. Verify file is from supported Vectric version (2015+)
2. Check file is not corrupted: Try opening in Vectric software
3. Check database tables exist: Use SQLite Browser
4. Convert VTDB to CSV in original Vectric software, then import

#### Problem: TDB file rejected with "Invalid binary format"

**Solution:**
1. Verify file is genuine TDB format
2. Check file size (TDB files typically 500KB+)
3. Try converting in CarveWare first
4. Check file permissions and encoding

### Database Issues

#### Problem: "Database is locked" error

**Solution:**
1. Ensure no other instance of application is running
2. Close any SQLite Browser windows
3. Check file is not read-only: `attrib -R tools.db`
4. Restart application

```python
# Handle lock in code
import sqlite3
import time

def safe_query(db_path, query):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            result = conn.execute(query).fetchall()
            conn.close()
            return result
        except sqlite3.OperationalError:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            raise
```

#### Problem: Tools not appearing after import

**Solution:**
1. Verify import completed successfully: Check status message
2. Confirm provider was created: `manager.get_providers()`
3. Search for tools: `repo.list_tools()`
4. Check database file size increased: `dir tools.db`

```python
# Verify import
manager = ToolDatabaseManager("tools.db")
providers = manager.get_providers()
print(f"Providers: {len(providers)}")

for provider in providers:
    tools = repo.list_tools_for_provider(provider['id'])
    print(f"Provider {provider['name']}: {len(tools)} tools")
```

#### Problem: Search returns no results

**Solution:**
1. Verify tools exist: `repo.list_tools()`
2. Check search parameters match data
3. Try without filters first
4. Use describe tool to see actual values

```python
# Debug search
all_tools = repo.list_tools()
print(f"Total tools: {len(all_tools)}")

# Check actual values
for tool in all_tools[:5]:
    print(f"Type: {tool['type']}, Diameter: {tool['diameter']}, Vendor: {tool['vendor']}")

# Then search with verified values
results = repo.search_tools(tool_type=tool['type'])
```

### Performance Issues

#### Problem: Import takes very long

**Solution:**
1. Check system resources: Open Task Manager
2. Close other applications
3. Increase RAM if available
4. Try importing smaller file first

```python
# Monitor import progress
import psutil

def import_with_monitoring(manager, file_path):
    process = psutil.Process()
    
    def progress_callback(progress, message):
        mem_usage = process.memory_info().rss / 1024 / 1024  # MB
        print(f"{message}: {progress*100:.1f}% - Memory: {mem_usage:.1f}MB")
    
    manager.import_tools_from_file(
        file_path=file_path,
        provider_name="Provider",
        progress_callback=progress_callback
    )
```

#### Problem: Application becomes unresponsive during import

**Solution:**
1. Check if import is running on UI thread
2. Use progress callback to keep UI responsive
3. Implement cancellation support
4. Move import to background thread

```python
from PySide6.QtCore import QThread, pyqtSignal

class ImportWorker(QThread):
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool)
    
    def run(self):
        try:
            success, count, errors = manager.import_tools_from_file(
                file_path=self.file_path,
                provider_name=self.provider_name,
                progress_callback=lambda p, m: self.progress.emit(p, m)
            )
            self.finished.emit(success)
        except Exception as e:
            print(f"Import failed: {e}")
            self.finished.emit(False)

# Use in UI
worker = ImportWorker()
worker.progress.connect(self.update_progress)
worker.finished.connect(self.import_complete)
worker.start()
```

### UI Issues

#### Problem: AddToolDialog not showing tools

**Solution:**
1. Verify database path is correct
2. Check providers exist
3. Verify database has tools
4. Check permissions

```python
# Verify in dialog initialization
from src.core.database.tool_database_repository import ToolDatabaseRepository

repo = ToolDatabaseRepository("tools.db")
providers = repo.get_providers()
print(f"Providers in dialog: {providers}")

if providers:
    for provider in providers:
        tools = repo.list_tools_for_provider(provider['id'])
        print(f"Tools in {provider['name']}: {len(tools)}")
```

#### Problem: Preferences not persisting

**Solution:**
1. Verify preferences saved successfully
2. Check database file permissions
3. Restart application to reload
4. Clear preferences and reconfigure

```python
# Clear and reset preferences
from src.core.database.tool_preferences_repository import ToolPreferencesRepository

prefs = ToolPreferencesRepository("tools.db")

# Clear all
for key in ['external_db_path', 'default_provider_id', 'auto_import_enabled']:
    prefs.delete_preference(key)

# Reset to defaults
prefs.set_preference("external_db_path", "/default/path")
prefs.set_preference("default_provider_id", "1")
```

---

## Testing & Validation

### Unit Tests

Run unit tests for individual parsers:

```bash
python -m pytest tests/test_tool_parsers.py -v

# Run specific test
python -m pytest tests/test_tool_parsers.py::TestCSVToolParser -v

# Run with coverage
python -m pytest tests/test_tool_parsers.py --cov=src.parsers.tool_parsers
```

### Integration Tests

Run integration tests for complete workflows:

```bash
python -m pytest tests/test_tool_database_integration.py -v

# Run specific integration test
python -m pytest tests/test_tool_database_integration.py::TestToolDatabaseIntegration::test_complete_import_workflow -v
```

### Memory Leak Testing

Run operations repeatedly to verify no memory leaks:

```bash
# Run memory tests
python -m pytest tests/test_tool_database_integration.py::TestToolDatabaseMemoryManagement -v

# Stress test with many operations
python -m pytest tests/test_tool_database_integration.py::TestToolDatabaseMemoryManagement::test_repeated_operations_no_memory_leak -v
```

### Test Coverage

Target test coverage by module:

| Module | Target Coverage | Current |
|--------|-----------------|---------|
| parsers/tool_parsers | 95% | ✓ |
| core/database/repositories | 90% | ✓ |
| parsers/tool_database_manager | 90% | ✓ |
| gui/widgets | 85% | ✓ |

---

## Quality Standards & Memory Management

### JSON Logging

All operations produce structured JSON logs:

```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Logs are structured JSON
logger.info("Tool imported", extra={
    "operation": "import_tool",
    "tool_id": 123,
    "provider": "IDC",
    "duration_ms": 1523
})
```

**Log Output:**
```json
{
  "timestamp": "2025-10-22T16:00:00Z",
  "level": "INFO",
  "module": "tool_database_manager",
  "message": "Tool imported",
  "operation": "import_tool",
  "tool_id": 123,
  "provider": "IDC",
  "duration_ms": 1523
}
```

### Memory Management

Verify no memory leaks in repeated operations:

```python
import gc
import tracemalloc

tracemalloc.start()

# Perform 20 iterations
for i in range(20):
    manager.import_tools_from_file("tools.csv", "Provider")
    manager.search_tools(tool_type="End Mill")
    gc.collect()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Iteration {i}: Current {current/1024/1024:.1f}MB, Peak {peak/1024/1024:.1f}MB")

tracemalloc.stop()
```

### Error Handling

Comprehensive error handling with user-friendly messages:

```python
try:
    success, count, errors = manager.import_tools_from_file(
        file_path="tools.csv",
        provider_name="Provider"
    )
    
    if not success:
        logger.error("Import failed", extra={
            "errors": errors,
            "file": "tools.csv"
        })
except FileNotFoundError:
    logger.error("File not found", extra={"file": "tools.csv"})
except ValueError as e:
    logger.error("Validation error", extra={"error": str(e)})
except Exception as e:
    logger.critical("Unexpected error", extra={"error": str(e), "traceback": traceback.format_exc()})
```

---

## FAQ & Best Practices

### Frequently Asked Questions

**Q: Can I import the same file twice?**

A: No, duplicate tools are detected by GUID. Reimporting the same file will skip existing tools.

**Q: How do I backup my tool database?**

A: Copy the `tools.db` file to a safe location.

**Q: Can I edit tools directly in the database?**

A: Use the ExternalDatabaseEditor UI or programmatic API. Direct SQL edits are not recommended.

**Q: What's the maximum number of tools supported?**

A: SQLite can theoretically store millions; practical limit depends on available disk space.

**Q: How do I export tools from one format to another?**

A: Import to database from source format, then export to target format using ToolExportManager.

**Q: Can multiple users share the same database?**

A: SQLite doesn't support concurrent writes. Use external database paths for read-only sharing.

### Best Practices

1. **Backup Regularly**
   - Create backups before major imports
   - Keep version history of databases

2. **Use Meaningful Provider Names**
   - Helps identify tool sources
   - Makes searching and filtering easier

3. **Leverage Custom Properties**
   - Store application-specific metadata
   - Use for categorization and filtering

4. **Monitor Performance**
   - Use progress callbacks for large imports
   - Monitor memory usage in logs

5. **Clean Up Regularly**
   - Remove duplicate or obsolete providers
   - Archive old databases

6. **Document Custom Formats**
   - If extending parsers, document format specs
   - Include examples in documentation

7. **Use Transactions**
   - Batch operations together
   - Ensure data consistency

8. **Validate Before Import**
   - Check file format before import
   - Test with small sample first

---

## Support and Maintenance

For issues, feature requests, or contributions, please refer to the project's contribution guidelines. All code changes should follow the quality standards outlined in this documentation.

### Reporting Issues

When reporting issues, include:
- Database size and number of tools
- File format being imported
- Error message and stack trace
- Steps to reproduce
- System specifications

### Contributing Parser Extensions

To add support for new formats:

1. Create new parser class extending BaseToolParser
2. Implement required methods: `validate_file()`, `parse()`, `get_format_name()`
3. Add comprehensive error handling
4. Write unit tests with >90% coverage
5. Document format specifications
6. Submit for code review

Example:

```python
from src.parsers.tool_parsers import BaseToolParser, ToolData

class CustomFormatParser(BaseToolParser):
    def validate_file(self, file_path: str) -> tuple:
        # Validation logic
        return True, ""
    
    def parse(self, file_path: str, progress_callback=None) -> list:
        # Parsing logic
        tools = []
        # ... parse file ...
        return tools
    
    def get_format_name(self) -> str:
        return "CustomFormat"
```

---

**Last Updated:** 2025-10-22
**Version:** 1.0
**Maintained By:** Digital Workshop Development Team
