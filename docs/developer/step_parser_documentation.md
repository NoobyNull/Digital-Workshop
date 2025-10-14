# STEP Parser Documentation

## Overview

The STEP parser is responsible for loading and parsing STEP/ISO 10303 files. It handles entity definitions, geometric relationships, and complex CAD data structures.

## Features

- Support for STEP files with entity definitions and geometric relationships
- Cartesian point, direction, and vector entity parsing
- Advanced face and edge loop processing
- Component-based model structure support
- Memory-efficient parsing for large files
- Progress reporting for long operations
- Comprehensive error handling and validation
- Integration with JSON logging system
- Performance optimization for different file sizes

## Usage

### Basic Usage

```python
from parsers.step_parser import STEPParser, ProgressCallback

# Create parser instance
parser = STEPParser()

# Parse STEP file
model = parser.parse_file("path/to/model.step")

# Access model data
triangles = model.triangles
stats = model.stats
```

### With Progress Callback

```python
def progress_callback(percent, message):
    print(f"Progress: {percent}% - {message}")

progress = ProgressCallback(progress_callback)
model = parser.parse_file("path/to/model.step", progress)
```

## Implementation Details

### File Structure

The STEP parser consists of the following main components:

- `STEPParser`: Main parser class that handles file parsing
- `STEPEntity`: Base data class for STEP entities
- `STEPCartesianPoint`: Data class for cartesian point entities
- `STEPDirection`: Data class for direction entities
- `STEPVector`: Data class for vector entities
- `STEPAxis2Placement3D`: Data class for axis placement entities
- `STEPAdvancedFace`: Data class for advanced face entities
- `STEPFaceBound`: Data class for face bound entities
- `STEPEdgeLoop`: Data class for edge loop entities
- `STEPOrientedEdge`: Data class for oriented edge entities
- `STEPEdgeCurve`: Data class for edge curve entities
- `STEPVertexPoint`: Data class for vertex point entities

### STEP Format Structure

STEP files are text files with the following structure:

```
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(...);
FILE_NAME(...);
FILE_SCHEMA(...);
ENDSEC;

DATA;
#1 = ENTITY_TYPE(...parameters...);
#2 = ENTITY_TYPE(...parameters...);
...
ENDSEC;
END-ISO-10303-21;
```

### Parsing Process

1. **File Validation**: Check if file exists and has valid STEP header
2. **DATA Section Extraction**: Extract the DATA section from the file
3. **Entity Parsing**: Parse each entity definition with ID, type, and parameters
4. **Entity Classification**: Classify entities into specific types
5. **Entity Relationship Processing**: Process references between entities
6. **Geometry Processing**: Generate triangles from geometric entities
7. **Model Assembly**: Assemble complete model from processed entities

### Entity Types Supported

The parser supports the following STEP entity types:

- `CARTESIAN_POINT`: 3D point coordinates
- `DIRECTION`: Direction vector
- `VECTOR`: Vector with magnitude
- `AXIS2_PLACEMENT_3D`: 3D coordinate system placement
- `ADVANCED_FACE`: Face definition with surface geometry
- `FACE_BOUND`: Face boundary definition
- `EDGE_LOOP`: Loop of edges
- `ORIENTED_EDGE`: Edge with orientation
- `EDGE_CURVE`: Curve between two vertices
- `VERTEX_POINT`: Vertex with point geometry

### Parameter Parsing

The parser handles various parameter types:

- Numbers (integers and floats)
- Strings (quoted with single quotes)
- Entity references (prefixed with #)
- Lists/arrays (parenthesized)
- Unspecified parameters ($ or *)

## Error Handling

The parser provides comprehensive error handling for:

- Invalid STEP file format
- Missing DATA section
- Malformed entity definitions
- Invalid parameter types
- Missing entity references
- Invalid numeric values

## Performance Considerations

- Memory-efficient processing with periodic garbage collection
- Progress reporting for large files
- Cancellation support for long operations
- Validation before full parsing to quickly detect errors
- Optimized entity parsing for large models

## Limitations

- Simplified geometry processing (placeholder implementation)
- Limited support for complex STEP entities
- No support for advanced surface types (NURBS, B-splines)
- No support for assembly structures or product data

## Testing

The STEP parser includes comprehensive unit tests covering:

- Valid file parsing
- Invalid file handling
- Entity parsing
- Parameter processing
- Progress reporting
- Error conditions

Run tests with:
```bash
python -m pytest tests/test_step_parser.py
```

## Troubleshooting

### Common Issues

1. **"Invalid STEP file" error**: File missing ISO-10303-21 header
2. **"No DATA section" error**: File missing required DATA section
3. **"Invalid entity" warning**: Malformed entity definition
4. **"Missing entity reference" warning**: Entity references undefined entity
5. **Slow parsing**: Large files with many entities may take time to process

### Debug Logging

Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger("STEPParser").setLevel(logging.DEBUG)
```

## Examples

See `tests/sample_files/cube.step` for an example STEP file with basic entity definitions.

## STEP Specification

For more information about the STEP format, see the official ISO 10303 specification.

## Future Enhancements

Potential improvements for the STEP parser:

- Full implementation of geometry processing
- Support for advanced surface types
- Assembly structure parsing
- Product data extraction
- Validation against STEP application protocols