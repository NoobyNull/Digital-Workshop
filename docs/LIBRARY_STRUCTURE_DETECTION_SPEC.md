# Library Structure Detection & Project Import Specification

## Overview

When users import a folder with existing organization, the system should:
1. **Detect** the existing folder structure and organization patterns
2. **Analyze** file types and metadata
3. **Present** findings with dry run preview
4. **Import** as a tagged "imported project" for easy location
5. **Preserve** the existing folder hierarchy

## 1. Library Structure Detector

### Purpose
Analyze folder hierarchies to detect existing organization patterns.

### Detection Patterns

#### 1.1 File Type Grouping
Detect if files are organized by type:
- `STL_Files/`, `OBJ_Files/`, `STEP_Files/` (extension-based)
- `Models/`, `Assets/`, `Resources/` (generic grouping)
- `Characters/`, `Props/`, `Environments/` (domain-based)

#### 1.2 Depth-Based Organization
- **Flat**: All files in root or one level deep
- **Nested**: Multi-level hierarchy (3+ levels)
- **Balanced**: Consistent depth across folders

#### 1.3 Metadata Detection
Scan for organizational metadata:
- `README.md`, `README.txt` - Project description
- `manifest.json` - File manifest
- `.project` - Project metadata
- `index.csv` - File index
- `metadata.json` - Custom metadata

#### 1.4 Naming Conventions
Detect patterns in folder/file names:
- Consistent prefixes (e.g., `model_`, `asset_`)
- Version numbering (e.g., `v1/`, `v2/`)
- Date-based organization (e.g., `2024-01/`)

### Output

```python
@dataclass
class LibraryStructureAnalysis:
    confidence_score: float  # 0-100%, how organized
    structure_type: str  # "flat", "nested", "balanced", "unknown"
    file_type_grouping: bool  # True if files grouped by type
    metadata_files: List[str]  # Found metadata files
    folder_depth: int  # Maximum nesting level
    total_files: int
    total_folders: int
    file_count_by_type: Dict[str, int]
    recommendations: List[str]  # Import suggestions
```

## 2. File Type Filter

### Supported File Types
**All files supported** except blocked system files:
- Documents: pdf, doc, docx, xls, xlsx, csv, txt, rtf
- Images: jpg, png, gif, bmp, svg, tiff
- 3D Models: stl, obj, step, stp, 3mf, ply, fbx, dae, gltf, glb
- Archives: zip, rar, 7z, tar, gz
- Data: json, xml, yaml, sql, db
- Media: mp4, avi, mov, mp3, wav
- Other: Any file not in blocked list

### Blocked System Files
**Never import** these potentially harmful files:
- Executables: exe, com, scr, msi, app, bin
- Scripts: bat, cmd, ps1, sh, bash, vbs, js, jar
- System: sys, ini, inf, dll, so, dylib, drv
- Config: cfg, conf, config, reg, plist
- Temporary: tmp, temp, cache, log (optional)

### File Classification

```python
@dataclass
class FileClassification:
    path: str
    file_type: str  # "supported", "blocked", "metadata"
    extension: str
    size_bytes: int
    reason: Optional[str]  # Why blocked, if applicable
```

## 3. Project Importer

### Workflow

1. **Detect Structure**
   - Run LibraryStructureDetector
   - Analyze folder hierarchy
   - Identify metadata

2. **Filter Files**
   - Classify all files
   - Identify blocked files
   - Count by type

3. **Dry Run**
   - Show what will be imported
   - Display folder structure
   - List blocked files
   - Estimate storage

4. **User Verification**
   - Present dry run report
   - Allow user to review
   - Option to proceed or cancel

5. **Import**
   - Create project with "imported project" tag
   - Link all supported files
   - Preserve folder structure
   - Generate import report

### Project Tagging

Projects imported from existing structures are tagged:
- **Tag**: "imported_project"
- **Metadata**: Original root path, import date, structure type
- **Purpose**: Easy filtering and identification in UI

### Import Report

```python
@dataclass
class ImportReport:
    project_id: str
    project_name: str
    import_date: datetime
    structure_type: str
    total_files_imported: int
    total_files_blocked: int
    total_folders_preserved: int
    storage_used_bytes: int
    import_duration_seconds: float
    blocked_files: List[str]
    errors: List[str]
```

## 4. Dry Run Analyzer

### Simulation Without Commitment

Dry run shows:
- File count by type
- Folder structure preview (tree view)
- Blocked files list
- Storage impact estimate
- Potential issues/warnings

### Output Format

```
=== DRY RUN ANALYSIS ===
Project: My Library
Structure Type: nested
Organization Score: 85%

FILES BY TYPE:
  3D Models: 245 files (1.2 GB)
  Documents: 18 files (5.3 MB)
  Images: 156 files (450 MB)
  Other: 12 files (2.1 MB)

FOLDER STRUCTURE:
  Models/
    ├── Characters/ (45 files)
    ├── Props/ (78 files)
    ├── Environments/ (122 files)
  Documentation/
    ├── Guides/ (8 files)
    ├── References/ (10 files)

BLOCKED FILES: 3
  - setup.exe
  - install.bat
  - config.ini

STORAGE ESTIMATE: 1.7 GB
IMPORT TIME ESTIMATE: 2-3 minutes

[PROCEED] [CANCEL]
```

## 5. UI Integration

### Project Import Dialog

New dialog: `src/gui/dialogs/project_import_dialog.py`

Features:
- Folder selection
- Structure detection progress
- Dry run results display
- File type summary
- Blocked files warning
- Proceed/Cancel buttons

### ProjectManagerWidget Extension

Add import button:
- "Import Existing Library" button
- Opens ProjectImportDialog
- Shows import progress
- Displays results

## 6. Database Schema Extension

Add to Projects table:
```sql
ALTER TABLE projects ADD COLUMN (
    import_tag TEXT,  -- "imported_project" or NULL
    original_path TEXT,  -- Original import path
    structure_type TEXT,  -- "flat", "nested", "balanced"
    import_date TIMESTAMP
);
```

## 7. Configuration (QSettings)

```python
# File type configuration
settings.setValue("file_types/blocked_extensions", 
    ["exe", "bat", "ps1", "sys", "ini", "inf", "com", "dll", "msi"])

# Import preferences
settings.setValue("import/preserve_structure", True)
settings.setValue("import/link_mode", "hard")  # or "symbolic"
settings.setValue("import/dry_run_default", True)
```

## 8. Error Handling

- **Permission Denied**: Skip folder, log warning
- **Blocked Files**: List in report, don't import
- **Metadata Parse Error**: Log, continue
- **Disk Space**: Estimate and warn user
- **Invalid Paths**: Validate before import

## 9. Success Criteria

- ✅ Detect organized folder structures
- ✅ Classify files (supported/blocked)
- ✅ Provide dry run preview
- ✅ Import with "imported_project" tag
- ✅ Preserve folder hierarchy
- ✅ Generate import report
- ✅ Handle errors gracefully
- ✅ All tests passing

