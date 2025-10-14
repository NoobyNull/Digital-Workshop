# Format Detector Documentation

## Overview

The Format Detector is a utility class responsible for automatically detecting the format of 3D model files. It uses both file extension and content analysis to accurately identify file formats.

## Features

- Detection based on file extension
- Content-based verification for ambiguous files
- Support for STL, OBJ, 3MF, and STEP formats
- Comprehensive validation of file structure
- Error handling for invalid or corrupted files
- Integration with all parser classes

## Usage

### Basic Usage

```python
from parsers.format_detector import FormatDetector
from pathlib import Path

# Create detector instance
detector = FormatDetector()

# Detect format of a file
file_path = Path("path/to/model.stl")
format_type = detector.detect_format(file_path)

print(f"Detected format: {format_type}")
```

### Validation

```python
# Validate a file
is_valid, error_msg = detector.validate_file(file_path)
if is_valid:
    print("File is valid")
else:
    print(f"File is invalid: {error_msg}")
```

### Check Supported Format

```python
# Check if format is supported
if detector.is_supported_format(file_path):
    print("Format is supported")
else:
    print("Format is not supported")
```

## Implementation Details

### Detection Methods

The format detector uses multiple methods to identify file formats:

1. **Extension-based Detection**: Initial detection based on file extension
2. **Content Verification**: Verification of file content for certain formats
3. **Fallback Detection**: Content-based detection when extension is ambiguous

### Supported Formats

| Extension | Format | Verification Method |
|-----------|--------|---------------------|
| .stl | STL | Binary/ASCII structure check |
| .obj | OBJ | Vertex/face keyword check |
| .3mf | 3MF | ZIP archive with required files |
| .step, .stp | STEP | ISO-10303-21 header check |

### Verification Processes

#### STL Verification

- Checks for binary STL format with proper triangle count
- Verifies ASCII STL format with "solid" and "facet normal" keywords
- Validates file size matches expected binary format size

#### OBJ Verification

- Checks for vertex definitions ("v ")
- Checks for face definitions ("f ")
- Verifies basic OBJ structure

#### 3MF Verification

- Validates ZIP archive structure
- Checks for required "3D/3dmodel.model" file
- Verifies XML structure in model file

#### STEP Verification

- Checks for ISO-10303-21 header
- Verifies presence of DATA section
- Validates basic entity structure

## Error Handling

The format detector provides comprehensive error handling for:

- Non-existent files
- Empty files
- Invalid file structures
- Corrupted archives
- Missing required files

## Performance Considerations

- Efficient file reading for content verification
- Minimal memory usage during detection
- Fast extension-based detection as primary method
- Content verification only when necessary

## Examples

### Detecting Multiple Files

```python
import os
from pathlib import Path

detector = FormatDetector()
models_dir = Path("models")

for file_path in models_dir.glob("*"):
    if file_path.is_file():
        try:
            format_type = detector.detect_format(file_path)
            print(f"{file_path.name}: {format_type}")
        except Exception as e:
            print(f"{file_path.name}: Error - {str(e)}")
```

### Filtering by Format

```python
import os
from pathlib import Path

detector = FormatDetector()
stl_files = []

for file_path in Path("models").glob("*"):
    if detector.is_supported_format(file_path):
        format_type = detector.detect_format(file_path)
        if format_type == ModelFormat.STL:
            stl_files.append(file_path)

print(f"Found {len(stl_files)} STL files")
```

## Testing

The format detector includes comprehensive unit tests covering:

- Valid format detection
- Invalid format handling
- Extension-based detection
- Content-based verification
- Error conditions

Run tests with:
```bash
python -m pytest tests/test_format_detector.py
```

## Troubleshooting

### Common Issues

1. **"File does not exist" error**: Check file path and ensure file exists
2. **"Unknown format" result**: File may have unsupported extension or content
3. **"Invalid file format" error**: File may be corrupted or have invalid structure
4. **Slow detection**: Content verification may take time for large files

### Debug Logging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger("FormatDetector").setLevel(logging.DEBUG)
```

## Integration with Parsers

The format detector is designed to work seamlessly with all parser classes:

```python
from parsers.format_detector import FormatDetector
from parsers import STLParser, OBJParser, ThreeMFParser, STEPParser

detector = FormatDetector()
file_path = Path("model.stl")

# Detect format
format_type = detector.detect_format(file_path)

# Get appropriate parser
if format_type == ModelFormat.STL:
    parser = STLParser()
elif format_type == ModelFormat.OBJ:
    parser = OBJParser()
elif format_type == ModelFormat.THREE_MF:
    parser = ThreeMFParser()
elif format_type == ModelFormat.STEP:
    parser = STEPParser()

# Parse the file
model = parser.parse_file(file_path)
```

## Future Enhancements

Potential improvements for the format detector:

- Support for additional 3D formats (PLY, PCD, etc.)
- More sophisticated content analysis
- Metadata extraction
- Format confidence scoring
- Batch processing optimization