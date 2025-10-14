# 3MF Parser Documentation

## Overview

The 3MF parser is responsible for loading and parsing 3D Manufacturing Format (3MF) files. It handles vertices, triangles, transformations, and components within the ZIP-based 3MF format.

## Features

- Support for 3MF files with vertices, triangles, and transformations
- Component-based model structure support
- Transformation matrix handling for object placement
- Memory-efficient parsing for large files
- Progress reporting for long operations
- Comprehensive error handling and validation
- Integration with JSON logging system
- Performance optimization for different file sizes

## Usage

### Basic Usage

```python
from parsers.threemf_parser import ThreeMFParser, ProgressCallback

# Create parser instance
parser = ThreeMFParser()

# Parse 3MF file
model = parser.parse_file("path/to/model.3mf")

# Access model data
triangles = model.triangles
stats = model.stats
```

### With Progress Callback

```python
def progress_callback(percent, message):
    print(f"Progress: {percent}% - {message}")

progress = ProgressCallback(progress_callback)
model = parser.parse_file("path/to/model.3mf", progress)
```

## Implementation Details

### File Structure

The 3MF parser consists of the following main components:

- `ThreeMFParser`: Main parser class that handles file parsing
- `ThreeMFObject`: Data class for object definitions
- `ThreeMFComponent`: Data class for component references
- `ThreeMFBuildItem`: Data class for build items

### 3MF Format Structure

3MF files are ZIP archives containing:

- `3D/3dmodel.model`: XML file defining the 3D model
- `[Content_Types].xml`: MIME type definitions
- `_rels/.rels`: Package relationships

### Parsing Process

1. **ZIP Archive Validation**: Check if file is a valid ZIP archive
2. **Model File Extraction**: Extract and parse the 3D model XML
3. **Object Parsing**: Extract object definitions with vertices and triangles
4. **Component Parsing**: Process component references and transformations
5. **Build Item Parsing**: Process build items and their transformations
6. **Triangle Generation**: Generate triangles with applied transformations
7. **Geometry Processing**: Apply transformation matrices to vertices

### Transformation Support

The parser supports 4x4 transformation matrices for:

- Translation
- Rotation
- Scaling
- Complex transformations (combination of above)

### Component-Based Structure

3MF supports hierarchical model structures through components:

- Objects can reference other objects as components
- Each component can have its own transformation
- Supports nested components for complex assemblies

## Error Handling

The parser provides comprehensive error handling for:

- Invalid ZIP archives
- Missing required files (3D/3dmodel.model)
- Invalid XML structure
- Malformed transformation matrices
- Invalid vertex or triangle indices
- Missing object references

## Performance Considerations

- Memory-efficient processing with periodic garbage collection
- Progress reporting for large files
- Cancellation support for long operations
- Validation before full parsing to quickly detect errors
- Optimized XML parsing for large models

## Limitations

- Simplified STEP geometry processing (placeholder implementation)
- Limited support for advanced 3MF features (slices, textures)
- No support for print settings or metadata beyond basic properties

## Testing

The 3MF parser includes comprehensive unit tests covering:

- Valid file parsing
- Invalid file handling
- Transformation processing
- Component resolution
- Progress reporting
- Error conditions

Run tests with:
```bash
python -m pytest tests/test_threemf_parser.py
```

## Troubleshooting

### Common Issues

1. **"Invalid 3MF file" error**: File may not be a valid ZIP archive
2. **"Missing 3D/3dmodel.model" error**: Required model file not found in archive
3. **"Invalid XML" error**: Model file contains malformed XML
4. **"Object not found" warning**: Component references undefined object
5. **Slow parsing**: Large files with many components may take time to process

### Debug Logging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger("ThreeMFParser").setLevel(logging.DEBUG)
```

## Examples

See `tests/sample_files/cube.3mf` for an example 3MF file. Use `tests/sample_files/create_sample_3mf.py` to generate new test files.

## 3MF Specification

For more information about the 3MF format, see the official 3MF specification at: https://3mf.io/specification/