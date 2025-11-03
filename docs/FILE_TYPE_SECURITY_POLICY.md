# File Type Security Policy

## Overview

The File Type Filter implements a security-first approach to file imports:
- **Whitelist**: All file types supported by default
- **Blacklist**: Potentially harmful system files blocked
- **Configurable**: Administrators can customize via QSettings

## Blocked File Types

### Executables (CRITICAL)
These files can execute arbitrary code:
- `.exe` - Windows executable
- `.com` - DOS/Windows command file
- `.scr` - Windows screensaver (executable)
- `.msi` - Windows installer
- `.app` - macOS application
- `.bin` - Binary executable
- `.run` - Linux executable script

### Scripts (HIGH RISK)
These files execute code in various interpreters:
- `.bat` - Windows batch script
- `.cmd` - Windows command script
- `.ps1` - PowerShell script
- `.sh` - Unix/Linux shell script
- `.bash` - Bash shell script
- `.vbs` - VBScript
- `.js` - JavaScript (when executed)
- `.jar` - Java archive (executable)
- `.py` - Python script (when executed)
- `.rb` - Ruby script (when executed)

### System Files (HIGH RISK)
These files control system behavior:
- `.sys` - Windows system driver
- `.dll` - Windows dynamic library
- `.so` - Unix/Linux shared object
- `.dylib` - macOS dynamic library
- `.drv` - Device driver
- `.ocx` - OLE control extension

### Configuration Files (MEDIUM RISK)
These files can modify system/application behavior:
- `.ini` - Windows initialization file
- `.inf` - Windows information file
- `.cfg` - Configuration file
- `.conf` - Configuration file
- `.config` - Configuration file
- `.reg` - Windows registry file
- `.plist` - macOS property list

### Temporary/Cache Files (LOW RISK - Optional)
These files are typically temporary:
- `.tmp` - Temporary file
- `.temp` - Temporary file
- `.cache` - Cache file
- `.log` - Log file (optional blocking)

## Supported File Types

### 3D Models (PRIMARY)
- `.stl` - Stereolithography
- `.obj` - Wavefront OBJ
- `.step` / `.stp` - STEP format
- `.3mf` - 3D Manufacturing Format
- `.ply` - Polygon File Format
- `.fbx` - Autodesk FBX
- `.dae` - COLLADA
- `.gltf` / `.glb` - glTF format

### Documents
- `.pdf` - Portable Document Format
- `.doc` / `.docx` - Microsoft Word
- `.xls` / `.xlsx` - Microsoft Excel
- `.ppt` / `.pptx` - Microsoft PowerPoint
- `.txt` - Plain text
- `.rtf` - Rich Text Format
- `.odt` - OpenDocument Text
- `.ods` - OpenDocument Spreadsheet

### Images
- `.jpg` / `.jpeg` - JPEG image
- `.png` - PNG image
- `.gif` - GIF image
- `.bmp` - Bitmap image
- `.svg` - Scalable Vector Graphics
- `.tiff` / `.tif` - TIFF image
- `.webp` - WebP image
- `.ico` - Icon file

### Data Files
- `.csv` - Comma-separated values
- `.json` - JSON data
- `.xml` - XML data
- `.yaml` / `.yml` - YAML data
- `.sql` - SQL script (data only)
- `.db` / `.sqlite` - Database files
- `.tsv` - Tab-separated values

### Archives
- `.zip` - ZIP archive
- `.rar` - RAR archive
- `.7z` - 7-Zip archive
- `.tar` - TAR archive
- `.gz` / `.gzip` - GZIP archive
- `.bz2` - Bzip2 archive

### Media
- `.mp4` - MPEG-4 video
- `.avi` - AVI video
- `.mov` - QuickTime video
- `.mkv` - Matroska video
- `.mp3` - MPEG audio
- `.wav` - WAV audio
- `.flac` - FLAC audio
- `.aac` - AAC audio

### Metadata (ALWAYS INCLUDED)
- `.md` - Markdown
- `.txt` - Plain text
- `.json` - JSON
- `README` - Project readme
- `manifest.json` - File manifest
- `.project` - Project metadata

## Configuration

### QSettings Keys

```python
# Blocked extensions (comma-separated)
settings.setValue("file_types/blocked_extensions", 
    "exe,com,scr,msi,app,bin,run,bat,cmd,ps1,sh,bash,vbs,js,jar,sys,dll,so,dylib,drv,ini,inf,cfg,conf,config,reg,plist")

# Allow temporary files (optional)
settings.setValue("file_types/block_temporary", False)

# Custom blocked extensions (user-defined)
settings.setValue("file_types/custom_blocked", "")

# Custom allowed extensions (override blocking)
settings.setValue("file_types/custom_allowed", "")
```

### Runtime Configuration

```python
from src.core.services.file_type_filter import FileTypeFilter

filter = FileTypeFilter()

# Check if file is supported
is_supported = filter.is_supported("model.stl")  # True
is_supported = filter.is_supported("setup.exe")  # False

# Get file classification
classification = filter.classify("document.pdf")
# Returns: FileClassification(
#     path="document.pdf",
#     file_type="supported",
#     extension="pdf",
#     size_bytes=1024000,
#     reason=None
# )

# Get blocked file classification
classification = filter.classify("malware.exe")
# Returns: FileClassification(
#     path="malware.exe",
#     file_type="blocked",
#     extension="exe",
#     size_bytes=2048000,
#     reason="Executable files are blocked for security"
# )
```

## Security Rationale

### Why Block Executables?
- Can execute arbitrary code
- Potential malware vector
- No legitimate reason to import into 3D model library

### Why Block Scripts?
- Can execute code in various interpreters
- Potential for system compromise
- No legitimate reason to import into 3D model library

### Why Block System Files?
- Control system behavior
- Can modify OS/application functionality
- No legitimate reason to import into 3D model library

### Why Block Configuration Files?
- Can modify system/application settings
- Potential for configuration hijacking
- No legitimate reason to import into 3D model library

## User Warnings

When blocked files are detected during import:

```
⚠️ BLOCKED FILES DETECTED

The following files cannot be imported for security reasons:
  - setup.exe (Executable)
  - install.bat (Script)
  - config.ini (Configuration)

These file types are blocked to protect your system.
You can proceed with importing other files.

[PROCEED WITHOUT BLOCKED FILES] [CANCEL]
```

## Admin Override

Administrators can customize blocking via QSettings:

```python
# Allow specific blocked extension
settings.setValue("file_types/custom_allowed", "exe")

# Block additional extensions
settings.setValue("file_types/custom_blocked", "xyz,abc")
```

## Audit Logging

All blocked file attempts are logged:

```json
{
  "timestamp": "2025-11-02T10:30:45Z",
  "event": "file_blocked",
  "file_path": "/path/to/setup.exe",
  "extension": "exe",
  "reason": "Executable files are blocked for security",
  "user": "john_doe",
  "project": "My Library"
}
```

## Future Enhancements

- [ ] Content-based detection (magic bytes)
- [ ] Virus scanning integration
- [ ] Quarantine for suspicious files
- [ ] Admin approval workflow
- [ ] Audit trail dashboard

