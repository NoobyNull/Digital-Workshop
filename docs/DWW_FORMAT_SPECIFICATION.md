# DWW (Digital Wood Works) Format Specification

## Overview

DWW is a custom archive format designed for Digital Workshop to export and share projects with integrity verification. It combines the portability of ZIP archives with JSON metadata and cryptographic hash verification.

## File Structure

A DWW file is a ZIP archive with the following structure:

```
project.dww
├── manifest.json                    # Project metadata and file listing
├── integrity.json                   # Hash verification data with salt
├── files/                           # Directory containing all project files
│   ├── model.stl
│   ├── gcode.nc
│   ├── cost_sheet.pdf
│   └── ...
├── thumbnails/                      # Optional: Thumbnail images for models
│   ├── model.stl.thumb.png
│   ├── model2.stl.thumb.png
│   └── ...
└── metadata/                        # Optional: Additional metadata
    └── files_metadata.json          # File-level metadata and attributes
```

## Format Version

- **Current Version**: 1.0
- **Format Name**: Digital Wood Works

## File Specifications

### manifest.json

Contains project metadata and file information.

```json
{
  "version": "1.0",
  "format": "Digital Wood Works",
  "created_at": "2024-01-15T10:30:00.123456",
  "project": {
    "id": "project-uuid-here",
    "name": "My Woodworking Project",
    "description": "A detailed description of the project",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  "files": [
    {
      "name": "model.stl",
      "path": "/path/to/model.stl",
      "size": 1024000,
      "type": ".stl",
      "thumbnail": true
    },
    {
      "name": "gcode.nc",
      "path": "/path/to/gcode.nc",
      "size": 512000,
      "type": ".nc",
      "thumbnail": false
    }
  ],
  "file_count": 2
}
```

### metadata/files_metadata.json

Contains detailed metadata for each file in the project.

```json
{
  "project_id": "project-uuid-here",
  "export_date": "2024-01-15T10:30:00.123456",
  "files_metadata": [
    {
      "file_name": "model.stl",
      "file_path": "/path/to/model.stl",
      "file_size": 1024000,
      "file_hash": "abc123def456...",
      "thumbnail_path": "thumbnails/model.stl.thumb.png",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    },
    {
      "file_name": "gcode.nc",
      "file_path": "/path/to/gcode.nc",
      "file_size": 512000,
      "file_hash": "xyz789abc123...",
      "thumbnail_path": null,
      "created_at": "2024-01-05T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### integrity.json

Contains cryptographic hash verification data to ensure file integrity.

```json
{
  "version": "1.0",
  "salt": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "hash": "sha256_hash_of_manifest_and_files_with_salt",
  "algorithm": "SHA256",
  "file_hashes": {
    "model.stl": "individual_file_sha256_hash",
    "gcode.nc": "individual_file_sha256_hash"
  }
}
```

## Security Features

### Salted Hash Verification

- **Salt Length**: 32 bytes (256 bits) of random data
- **Algorithm**: SHA256
- **Hash Input**: Combined JSON of manifest + file_hashes + salt
- **Purpose**: Ensures file integrity and detects tampering

### Verification Process

1. Extract manifest.json and integrity.json from DWW file
2. Retrieve salt from integrity.json
3. Recalculate hash using: SHA256(manifest + file_hashes + salt)
4. Compare calculated hash with stored hash
5. If hashes match, file integrity is verified

## Supported File Types

DWW can contain any file type, but Digital Workshop recognizes:

- **Models**: .stl, .obj, .step, .stp, .3mf, .ply
- **G-Code**: .nc, .gcode
- **Cut Lists**: .csv, .xlsx, .xls
- **Cost Sheets**: .pdf, .docx, .doc
- **Documents**: .txt, .md
- **Other**: Any other file type

## Usage

### Exporting a Project

```python
from src.core.export.dww_export_manager import DWWExportManager

export_manager = DWWExportManager(db_manager)
success, message = export_manager.export_project(
    project_id="project-uuid",
    output_path="/path/to/export.dww",
    include_metadata=True,           # Include file metadata
    include_thumbnails=True,         # Include model thumbnails
    include_renderings=True,         # Include rendered images
    progress_callback=progress_func  # Optional progress updates
)
```

### Importing a Project

```python
from src.core.export.dww_import_manager import DWWImportManager

import_manager = DWWImportManager(db_manager)
success, message, manifest = import_manager.import_project(
    dww_path="/path/to/export.dww",
    import_dir="/path/to/import/directory",
    verify_integrity=True,           # Verify file integrity
    import_thumbnails=True,          # Extract thumbnails
    progress_callback=progress_func  # Optional progress updates
)
```

### Verifying Integrity

```python
export_manager = DWWExportManager()
is_valid, message = export_manager.verify_dww_file("/path/to/export.dww")
```

### Getting Project Info

```python
import_manager = DWWImportManager()
success, manifest = import_manager.get_dww_info("/path/to/export.dww")
```

## Advantages

1. **Portability**: Single file containing entire project
2. **Integrity**: Cryptographic verification prevents tampering
3. **Metadata**: Rich project information included
4. **Compression**: ZIP compression reduces file size
5. **Compatibility**: Standard ZIP format readable by any archive tool
6. **Extensibility**: Easy to add new metadata fields

## Limitations

- Maximum file size limited by ZIP format (typically 4GB per file)
- Requires extraction before use (files not directly accessible)
- No encryption (use OS-level encryption for sensitive projects)

## Future Enhancements

- Encryption support (AES-256)
- Incremental backups
- Version history tracking
- Digital signatures
- Compression level options

