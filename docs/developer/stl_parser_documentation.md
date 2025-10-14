# STL Parser Documentation

## Overview

The STL parser is a comprehensive module for loading and parsing STL (STereoLithography) files in both binary and ASCII formats. It provides memory-efficient processing, progress reporting, and comprehensive error handling for the 3D-MM application.

## Features

- **Dual Format Support**: Parses both binary and ASCII STL formats with automatic detection
- **Memory-Efficient Processing**: Optimized for large files with periodic garbage collection
- **Progress Reporting**: Real-time progress updates for long-running operations
- **Comprehensive Error Handling**: Graceful handling of corrupted or invalid files
- **JSON Logging Integration**: Full integration with the application's logging system
- **Performance Optimization**: Adaptive processing based on file size and system capabilities
- **Cancellation Support**: Ability to cancel long-running parsing operations

## Architecture

### Core Classes

#### STLParser
The main parser class that handles format detection and parsing operations.

**Key Methods:**
- `parse_file(file_path, progress_callback=None)`: Parse an STL file with auto-format detection
- `validate_file(file_path)`: Validate an STL file without full parsing
- `cancel_parsing()`: Cancel the current parsing operation
- `reset_cancel_state()`: Reset cancellation state for new operations

#### Data Structures

##### Vector3D
Represents a 3D vector with x, y, z coordinates.
```python
vector = Vector3D(1.0, 2.0, 3.0)
x, y, z = vector  # Unpacking support
x_coord = vector[0]  # Indexing support
```

##### Triangle
Represents a triangle with normal vector and three vertices.
```python
triangle = Triangle(normal, vertex1, vertex2, vertex3, attribute_byte_count)
vertices = triangle.get_vertices()  # Get all vertices as list
```

##### ModelStats
Contains statistical information about a parsed model.
```python
stats = ModelStats(
    vertex_count=3,
    triangle_count=1,
    min_bounds=Vector3D(0, 0, 0),
    max_bounds=Vector3D(1, 1, 1),
    file_size_bytes=1024,
    format_type=STLFormat.BINARY,
    parsing_time_seconds=0.1
)
dimensions = stats.get_dimensions()  # Get width, height, depth
```

##### STLModel
Complete representation of a parsed 3D model with geometry and statistics.
```python
model = STLModel(header="Test Model", triangles=[triangle], stats=stats)
all_vertices = model.get_vertices()
memory_usage = model.get_memory_usage()
```

## Usage Examples

### Basic File Parsing

```python
from src.parsers.stl_parser import STLParser

# Create parser instance
parser = STLParser()

# Parse STL file (auto-detects format)
model = parser.parse_file("path/to/model.stl")

# Access model information
print(f"Triangles: {model.stats.triangle_count}")
print(f"Vertices: {model.stats.vertex_count}")
print(f"Bounds: {model.stats.min_bounds} to {model.stats.max_bounds}")
print(f"Format: {model.stats.format_type.value}")
print(f"Parse time: {model.stats.parsing_time_seconds:.3f}s")
```

### Progress Reporting

```python
from src.parsers.stl_parser import STLParser, STLProgressCallback

# Create progress callback
def progress_handler(percent, message):
    print(f"Progress: {percent:.1f}% - {message}")

progress_callback = STLProgressCallback(progress_handler)

# Parse with progress reporting
parser = STLParser()
model = parser.parse_file("large_model.stl", progress_callback)
```

### File Validation

```python
from src.parsers.stl_parser import STLParser

parser = STLParser()

# Validate file without full parsing
is_valid, error_message = parser.validate_file("model.stl")

if is_valid:
    print("File is valid")
else:
    print(f"Invalid file: {error_message}")
```

### Cancellation Support

```python
from src.parsers.stl_parser import STLParser
import threading
import time

parser = STLParser()

def parse_in_background():
    try:
        model = parser.parse_file("very_large_model.stl")
        print("Parsing completed")
    except Exception as e:
        print(f"Parsing failed: {e}")

# Start parsing in background
parse_thread = threading.Thread(target=parse_in_background)
parse_thread.start()

# Cancel after 2 seconds
time.sleep(2)
parser.cancel_parsing()

parse_thread.join()
```

## Format Specifications

### Binary STL Format
- **Header**: 80 bytes (can contain any data, often descriptive)
- **Triangle Count**: 4 bytes (unsigned 32-bit integer, little-endian)
- **Triangle Data**: 50 bytes per triangle
  - Normal Vector: 12 bytes (3 × 4-byte floats, little-endian)
  - Vertices: 36 bytes (3 × 3 × 4-byte floats, little-endian)
  - Attribute Byte Count: 2 bytes (unsigned 16-bit integer, little-endian)

### ASCII STL Format
- Starts with `solid [name]` header line
- Each triangle defined as:
  ```
  facet normal [nx] [ny] [nz]
    outer loop
      vertex [x1] [y1] [z1]
      vertex [x2] [y2] [z2]
      vertex [x3] [y3] [z3]
    endloop
  endfacet
  ```
- Ends with `endsolid [name]` line

## Performance Characteristics

### Memory Usage
- **Small Files** (< 100MB): Loaded entirely into memory
- **Medium Files** (100-500MB): Streaming with periodic garbage collection
- **Large Files** (> 500MB): Chunked processing with memory monitoring

### Processing Speed
- **Small Files**: < 5 seconds
- **Medium Files**: < 15 seconds  
- **Large Files**: < 30 seconds

### Memory Management
- Automatic garbage collection every 10,000 triangles
- Memory usage monitoring and adaptive allocation
- No memory leaks during repeated operations (verified by testing)

## Error Handling

The parser provides comprehensive error handling for various scenarios:

### File-Level Errors
- File not found
- Empty files
- Permission issues
- Corrupted file headers

### Format Errors
- Unknown or unsupported formats
- Invalid triangle counts
- Mismatched file sizes (binary format)

### Data Errors
- Invalid numeric values
- Incomplete triangle data
- Corrupted vertex information

### System Errors
- Insufficient memory
- I/O errors
- Cancellation exceptions

## Logging Integration

The STL parser integrates with the application's JSON logging system:

```python
# All parsing operations are automatically logged
# Log entries include:
# - File path and size
# - Format type
# - Triangle and vertex counts
# - Parsing time
# - Error details (if applicable)
# - Memory usage statistics
```

## Testing

Comprehensive unit tests are provided covering:
- Format detection
- Binary and ASCII parsing
- Error handling
- Performance benchmarks
- Memory leak detection
- Progress reporting
- File validation

Run tests with:
```bash
cd tests
python -m pytest test_stl_parser.py -v
```

## Troubleshooting

### Common Issues

#### "Unable to determine STL format"
- **Cause**: File is corrupted or not a valid STL file
- **Solution**: Verify file integrity and format

#### "Invalid triangle count"
- **Cause**: Binary file header indicates unreasonable number of triangles
- **Solution**: Check if file is actually a binary STL format

#### "unpack requires a buffer of X bytes"
- **Cause**: Incomplete or corrupted triangle data
- **Solution**: File may be truncated or corrupted

#### Memory issues with large files
- **Cause**: Insufficient available RAM
- **Solution**: Close other applications or use a system with more memory

### Performance Tips

1. **Use binary STL format** when possible, as it's typically faster to parse
2. **Enable progress reporting** for large files to monitor operation status
3. **Validate files before parsing** to quickly identify invalid files
4. **Consider cancellation** for very large files if processing time is excessive

## Dependencies

- **Python 3.8+**: Core language requirements
- **struct**: Binary data handling (built-in)
- **pathlib**: Path handling (built-in)
- **logging**: Logging integration (built-in)
- **gc**: Garbage collection (built-in)
- **typing**: Type hints (built-in)
- **time**: Performance measurement (built-in)
- **enum**: Enumeration support (built-in)
- **dataclasses**: Data structure definitions (built-in)

## Future Enhancements

Potential improvements for future versions:
- **Streaming Parser**: Process files larger than available memory
- **Parallel Processing**: Multi-threaded parsing for large files
- **Format Conversion**: Convert between STL and other formats
- **Mesh Optimization**: Remove duplicate vertices and optimize mesh data
- **Partial Loading**: Load specific regions of very large models