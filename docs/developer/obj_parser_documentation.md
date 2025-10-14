# OBJ Parser Documentation

## Overview

The OBJ parser is responsible for loading and parsing Wavefront OBJ files with MTL material support. It handles vertices, faces, normals, texture coordinates, and material definitions.

## Features

- Support for OBJ files with vertices, faces, normals, and texture coordinates
- MTL material file support with ambient, diffuse, specular, and other material properties
- Memory-efficient parsing for large files
- Progress reporting for long operations
- Comprehensive error handling and validation
- Integration with JSON logging system
- Performance optimization for different file sizes

## Usage

### Basic Usage

```python
from parsers.obj_parser import OBJParser, ProgressCallback

# Create parser instance
parser = OBJParser()

# Parse OBJ file
model = parser.parse_file("path/to/model.obj")

# Access model data
triangles = model.triangles
stats = model.stats
```

### With Progress Callback

```python
def progress_callback(percent, message):
    print(f"Progress: {percent}% - {message}")

progress = ProgressCallback(progress_callback)
model = parser.parse_file("path/to/model.obj", progress)
```

## Implementation Details

### File Structure

The OBJ parser consists of the following main components:

- `OBJParser`: Main parser class that handles file parsing
- `OBJMaterial`: Data class for material properties
- `OBJFace`: Data class for face definitions

### Parsing Process

1. **File Validation**: Check if file exists and is not empty
2. **Line-by-Line Parsing**: Process each line of the OBJ file
3. **Vertex Processing**: Extract vertex coordinates
4. **Normal Processing**: Extract vertex normals
5. **Texture Coordinate Processing**: Extract texture coordinates
6. **Face Processing**: Extract face definitions and triangulate if needed
7. **Material Processing**: Load and parse MTL material files
8. **Triangle Generation**: Convert faces to triangles with proper normals

### MTL Material Support

The parser supports the following MTL material properties:

- Ambient color (`Ka`)
- Diffuse color (`Kd`)
- Specular color (`Ks`)
- Specular exponent (`Ns`)
- Optical density (`Ni`)
- Dissolve/transparency (`d` or `Tr`)
- Illumination model (`illum`)
- Texture maps (`map_Ka`, `map_Kd`, `map_Ks`, etc.)

## Error Handling

The parser provides comprehensive error handling for:

- Missing or corrupted files
- Invalid vertex or face definitions
- Missing MTL files
- Invalid material properties
- Malformed face indices

## Performance Considerations

- Memory-efficient processing with periodic garbage collection
- Progress reporting for large files
- Cancellation support for long operations
- Validation before full parsing to quickly detect errors

## Limitations

- Only supports triangular faces (quadrilaterals are triangulated)
- Limited support for complex material properties
- No support for animation or skeletal data

## Testing

The OBJ parser includes comprehensive unit tests covering:

- Valid file parsing
- Invalid file handling
- Material loading
- Progress reporting
- Error conditions

Run tests with:
```bash
python -m pytest tests/test_obj_parser.py
```

## Troubleshooting

### Common Issues

1. **"File not found" error**: Check file path and ensure file exists
2. **"Invalid vertex" error**: File may contain corrupted vertex data
3. **"Missing material" warning**: MTL file not found or inaccessible
4. **Slow parsing**: Large files may take time to process

### Debug Logging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger("OBJParser").setLevel(logging.DEBUG)
```

## Examples

See `tests/sample_files/cube.obj` and `tests/sample_files/cube.mtl` for example OBJ and MTL files.