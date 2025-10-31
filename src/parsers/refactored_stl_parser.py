
"""
Refactored STL Parser for Candy-Cadence

This module provides a refactored STL parser implementation that follows the IParser interface
with enhanced performance, streaming support, and consistent error handling.

Key Features:
- Implements IParser interface for consistency
- Supports both binary and ASCII STL formats
- GPU acceleration integration
- Streaming support for large files
- Progressive loading capabilities
- Memory-efficient processing
- Comprehensive error handling and logging
"""

import struct
import time
import gc
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from concurrent.futures import ProcessPoolExecutor, as_completed

# Optional accelerated path
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # Fallback to pure-Python parsing when NumPy is not available

from src.parsers.refactored_base_parser import RefactoredBaseParser, StreamingProgressCallback
from src.core.interfaces.parser_interfaces import ModelFormat, ParseError, FileNotSupportedError


class STLFormat(Enum):
    """STL file format types."""
    BINARY = "binary"
    ASCII = "ascii"
    UNKNOWN = "unknown"


class STLParseError(ParseError):
    """Custom exception for STL parsing errors."""
    pass


def _build_triangles_from_floats_chunk(chunk: "np.ndarray") -> List[Dict[str, Any]]:  # type: ignore
    """
    Worker function to convert a chunk of float rows (shape: N x 12) into triangle dictionaries.
    Executed in a separate process to leverage multiple CPU cores.
    """
    triangles = []
    for row in chunk:
        triangle = {
            'normal': [float(row[0]), float(row[1]), float(row[2])],
            'vertices': [
                [float(row[3]), float(row[4]), float(row[5])],
                [float(row[6]), float(row[7]), float(row[8])],
                [float(row[9]), float(row[10]), float(row[11])]
            ],
            'attribute_byte_count': 0
        }
        triangles.append(triangle)
    return triangles


class RefactoredSTLParser(RefactoredBaseParser):
    """
    Refactored STL parser implementing IParser interface with enhanced features.
    
    Features:
    - Supports both binary and ASCII STL formats
    - GPU acceleration integration
    - Streaming support for large files
    - Progressive loading capabilities
    - Memory-efficient processing
    - Comprehensive error handling and logging
    """

    # Binary STL format constants
    BINARY_HEADER_SIZE = 80
    BINARY_TRIANGLE_COUNT_SIZE = 4
    BINARY_TRIANGLE_SIZE = 50  # 12 bytes for normal + 36 bytes for vertices + 2 bytes for attribute

    def __init__(self):
        """Initialize the refactored STL parser."""
        super().__init__(
            parser_name="STL",
            supported_formats=[ModelFormat.STL]
        )

    def _detect_format(self, file_path: Path) -> STLFormat:
        """
        Detect whether an STL file is binary or ASCII format.

        Args:
            file_path: Path to the STL file

        Returns:
            Detected STL format

        Raises:
            STLParseError: If format cannot be determined
        """
        try:
            with open(file_path, 'rb') as file:
                # Read first 80 bytes (header) and check for ASCII indicators
                header = file.read(self.BINARY_HEADER_SIZE)

                # Check if header contains ASCII indicators
                header_text = header.decode('utf-8', errors='ignore').lower()
                if 'solid' in header_text and header_text.count('\x00') < 5:
                    # Likely ASCII, but verify by checking for "facet normal" keyword
                    file.seek(0)
                    first_line = file.readline().decode('utf-8', errors='ignore').strip()
                    if first_line.lower().startswith('solid'):
                        return STLFormat.ASCII

                # Check if it's valid binary by attempting to read triangle count
                file.seek(self.BINARY_HEADER_SIZE)
                count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) == self.BINARY_TRIANGLE_COUNT_SIZE:
                    triangle_count = struct.unpack('<I', count_bytes)[0]

                    # Verify file size matches expected binary format size
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    expected_size = (
                        self.BINARY_HEADER_SIZE +
                        self.BINARY_TRIANGLE_COUNT_SIZE +
                        (triangle_count * self.BINARY_TRIANGLE_SIZE)
                    )

                    if file_size == expected_size:
                        return STLFormat.BINARY

                return STLFormat.UNKNOWN

        except Exception as e:
            error_context = {
                "file_path": str(file_path),
                "operation": "format_detection"
            }
            self.logging_service.log_error(e, error_context)
            raise STLParseError(f"Failed to detect STL format: {str(e)}")

    def _parse_file_internal(self, file_path: Path, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Internal method to parse an STL file (auto-detecting format).

        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data

        Raises:
            STLParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Log operation start with structured context
            self.logging_service.log_info(
                f"Starting STL parsing: {file_path}",
                operation="parse_file",
                file_path=str(file_path),
                parser_name="STL"
            )

            # Detect format
            format_type = self._detect_format(file_path)
            if format_type == STLFormat.UNKNOWN:
                raise STLParseError("Unable to determine STL format (invalid or corrupted file)")

            # Parse based on format
            if format_type == STLFormat.BINARY:
                result = self._parse_binary_stl(file_path, progress_callback)
            elif format_type == STLFormat.ASCII:
                result = self._parse_ascii_stl(file_path, progress_callback)
            else:
                raise STLParseError(f"Unsupported STL format: {format_type}")

            # Log successful completion
            self.logging_service.log_info(
                f"Successfully parsed STL file: {file_path}",
                operation="parse_file",
                file_path=str(file_path),
                format_type=format_type.value,
                success=True
            )

            return result

        except Exception as e:
            error_context = {
                "file_path": str(file_path),
                "operation": "parse_file",
                "parser_name": "STL"
            }
            self.logging_service.log_error(e, error_context)
            raise

    def _parse_binary_stl(self, file_path: Path, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Parse binary STL file format with enhanced performance and memory management.

        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data

        Raises:
            STLParseError: If parsing fails
        """
        start_time = time.time()
        triangles = []

        try:
            with open(file_path, 'rb') as file:
                # Read header
                header_bytes = file.read(self.BINARY_HEADER_SIZE)
                header = header_bytes.decode('utf-8', errors='ignore').strip()

                # Read triangle count
                count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                    raise STLParseError("Invalid binary STL: cannot read triangle count")

                triangle_count = struct.unpack('<I', count_bytes)[0]
                
                # Log with structured context
                self.logging_service.log_info(
                    f"Parsing binary STL with {triangle_count} triangles",
                    operation="parse_binary_stl",
                    file_path=str(file_path),
                    triangle_count=triangle_count
                )

                # Validate triangle count is reasonable
                if triangle_count > 100000000:  # 100 million triangles is unreasonable
                    raise STLParseError(f"Invalid triangle count: {triangle_count}")

                # Update progress
                self._update_progress(5.0, f"Reading {triangle_count} triangles", progress_callback)

                # Decide parsing strategy based on file size and triangle count
                file_size_mb = file_path.stat().st_size / (1024 * 1024)

                # Use array-based fast path for large models
                if (np is not None) and (triangle_count >= 100000):
                    self.logging_service.log_info(
                        f"Using array-based fast path for {triangle_count} triangles",
                        operation="parse_binary_stl",
                        parsing_strategy="array_based"
                    )
                    return self._parse_binary_stl_arrays(file_path, progress_callback)

                use_vectorized = (np is not None) and (triangle_count >= 20000)

                if use_vectorized:
                    return self._parse_binary_stl_vectorized(file_path, triangle_count, progress_callback)
                else:
                    return self._parse_binary_stl_pure_python(file_path, triangle_count, progress_callback)

        except Exception as e:
            error_context = {
                "file_path": str(file_path),
                "operation": "parse_binary_stl"
            }
            self.logging_service.log_error(e, error_context)
            raise STLParseError(f"Failed to parse binary STL: {str(e)}")

    def _parse_binary_stl_vectorized(self, file_path: Path, triangle_count: int, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Vectorized parsing for binary STL using NumPy and multiprocessing.

        Args:
            file_path: Path to the STL file
            triangle_count: Number of triangles to parse
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data
        """
        start_time = time.time()

        try:
            with open(file_path, 'rb') as file:
                # Skip header
                file.seek(self.BINARY_HEADER_SIZE + self.BINARY_TRIANGLE_COUNT_SIZE)

                # Read all triangle records: 50 bytes each
                total_bytes = triangle_count * self.BINARY_TRIANGLE_SIZE
                self._update_progress(15.0, "Reading triangle data...", progress_callback)

                data = file.read(total_bytes)
                if len(data) != total_bytes:
                    raise STLParseError(f"Failed to read triangle block ({len(data)} of {total_bytes} bytes)")

                self._update_progress(25.0, "Decoding triangle floats...", progress_callback)

                # Convert to NumPy array and extract floats
                u8 = np.frombuffer(data, dtype=np.uint8).reshape(triangle_count, self.BINARY_TRIANGLE_SIZE)  # type: ignore

                # Process float decoding in chunks for progress reporting
                chunk_size = min(50000, max(10000, triangle_count // 20))
                floats = np.empty((triangle_count, 12), dtype=np.float32)

                for start_idx in range(0, triangle_count, chunk_size):
                    end_idx = min(start_idx + chunk_size, triangle_count)
                    chunk_data = u8[start_idx:end_idx, :48].copy().view('<f4').reshape(end_idx - start_idx, 12)
                    floats[start_idx:end_idx] = chunk_data

                    # Report progress during float decoding
                    decode_progress = 25.0 + 15.0 * (end_idx / triangle_count)
                    self._update_progress(decode_progress, f"Decoding floats: {end_idx:,}/{triangle_count:,}", progress_callback)

                    self._check_cancellation()

                # Compute bounds via vectorized operations
                verts = floats[:, 3:12].reshape(triangle_count, 3, 3)
                min_xyz = verts.reshape(-1, 3).min(axis=0)
                max_xyz = verts.reshape(-1, 3).max(axis=0)

                self._update_progress(45.0, "Building triangles (multi-core)...", progress_callback)

                # Build Triangle dictionaries using multiple processes
                cpu_cnt = max(2, (os.cpu_count() or 2))
                max_workers = min(cpu_cnt, 8)

                # Split into roughly equal chunks per worker
                splits = max_workers
                indices = np.linspace(0, triangle_count, splits + 1, dtype=np.int64)  # type: ignore
                chunks = [(int(indices[i]), int(indices[i + 1])) for i in range(splits) if int(indices[i]) < int(indices[i + 1])]

                triangles = []
                built_total = 0
                with ProcessPoolExecutor(max_workers=max_workers) as pool:
                    futures = []
                    for start_idx, end_idx in chunks:
                        futures.append(pool.submit(_build_triangles_from_floats_chunk, floats[start_idx:end_idx].copy()))
                    
                    for fut in as_completed(futures):
                        part = fut.result()
                        triangles.extend(part)
                        built_total += len(part)
                        
                        pct = 45.0 + 50.0 * (built_total / triangle_count)
                        self._update_progress(pct, f"Built {built_total:,}/{triangle_count:,} triangles", progress_callback)
                        self._check_cancellation()

                # Force garbage collection
                gc.collect()

                # Create result dictionary
                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size

                result = {
                    'header': 'Binary STL Model',
                    'triangles': triangles,
                    'format': ModelFormat.STL,
                    'stats': {
                        'vertex_count': triangle_count * 3,
                        'triangle_count': triangle_count,
                        'min_bounds': [float(min_xyz[0]), float(min_xyz[1]), float(min_xyz[2])],
                        'max_bounds': [float(max_xyz[0]), float(max_xyz[1]), float(max_xyz[2])],
                        'file_size_bytes': file_size,
                        'parsing_time_seconds': parsing_time
                    }
                }

                self._update_progress(100.0, "Binary STL parsing completed", progress_callback)

                self.logging_service.log_info(
                    f"Successfully parsed binary STL (vectorized): {triangle_count} triangles, "
                    f"bounds: [{min_xyz[0]:.3f}, {min_xyz[1]:.3f}, {min_xyz[2]:.3f}] to "
                    f"[{max_xyz[0]:.3f}, {max_xyz[1]:.3f}, {max_xyz[2]:.3f}], "
                    f"time: {parsing_time:.2f}s",
                    operation="parse_binary_stl_vectorized",
                    triangle_count=triangle_count,
                    parsing_time_seconds=parsing_time,
                    success=True
                )

                return result

        except Exception as e:
            error_context = {
                "operation": "parse_binary_stl_vectorized",
                "file_path": str(file_path)
            }
            self.logging_service.log_error(e, error_context)
            raise STLParseError(f"Failed to parse binary STL (vectorized): {str(e)}")

    def _parse_binary_stl_pure_python(self, file_path: Path, triangle_count: int, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Pure Python parsing for binary STL (fallback for smaller files).

        Args:
            file_path: Path to the STL file
            triangle_count: Number of triangles to parse
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data
        """
        start_time = time.time()
        triangles = []

        try:
            with open(file_path, 'rb') as file:
                # Skip header
                file.seek(self.BINARY_HEADER_SIZE + self.BINARY_TRIANGLE_COUNT_SIZE)

                min_x = min_y = min_z = float('inf')
                max_x = max_y = max_z = float('-inf')

                for i in range(triangle_count):
                    self._check_cancellation()

                    # Read triangle data (50 bytes)
                    triangle_data = file.read(self.BINARY_TRIANGLE_SIZE)
                    if len(triangle_data) != self.BINARY_TRIANGLE_SIZE:
                        raise STLParseError(f"Failed to read triangle {i}: incomplete data")

                    values = struct.unpack('<ffffffffffffH', triangle_data)

                    triangle = {
                        'normal': [values[0], values[1], values[2]],
                        'vertices': [
                            [values[3], values[4], values[5]],
                            [values[6], values[7], values[8]],
                            [values[9], values[10], values[11]]
                        ],
                        'attribute_byte_count': values[12]
                    }
                    triangles.append(triangle)

                    # Update bounds
                    for vertex in triangle['vertices']:
                        min_x = min(min_x, vertex[0])
                        min_y = min(min_y, vertex[1])
                        min_z = min(min_z, vertex[2])
                        max_x = max(max_x, vertex[0])
                        max_y = max(max_y, vertex[1])
                        max_z = max(max_z, vertex[2])

                    # Report progress
                    if progress_callback and i % 1000 == 0:
                        progress = (i / triangle_count) * 100
                        self._update_progress(progress, f"Parsed {i:,}/{triangle_count:,} triangles", progress_callback)

                    # Periodic garbage collection
                    if i % 10000 == 0 and i > 0:
                        gc.collect()

                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size

                result = {
                    'header': 'Binary STL Model',
                    'triangles': triangles,
                    'format': ModelFormat.STL,
                    'stats': {
                        'vertex_count': triangle_count * 3,
                        'triangle_count': triangle_count,
                        'min_bounds': [min_x, min_y, min_z],
                        'max_bounds': [max_x, max_y, max_z],
                        'file_size_bytes': file_size,
                        'parsing_time_seconds': parsing_time
                    }
                }

                self._update_progress(100.0, "Binary STL parsing completed", progress_callback)

                self.logger.info(
                    f"Successfully parsed binary STL: {triangle_count} triangles, "
                    f"bounds: [{min_x:.3f}, {min_y:.3f}, {min_z:.3f}] to "
                    f"[{max_x:.3f}, {max_y:.3f}, {max_z:.3f}], "
                    f"time: {parsing_time:.2f}s"
                )

                return result

        except Exception as e:
            self.logger.error(f"Error in pure Python binary STL parse: {str(e)}")
            raise STLParseError(f"Failed to parse binary STL (pure Python): {str(e)}")

    def _parse_binary_stl_arrays(self, file_path: Path, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Array-based fast path for binary STL parsing (returns arrays instead of objects).

        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data with arrays
        """
        if np is None:
            raise STLParseError("NumPy is required for array-based STL parsing")

        start_time = time.time()

        try:
            with open(file_path, 'rb') as file:
                # Header
                header_bytes = file.read(self.BINARY_HEADER_SIZE)
                header = header_bytes.decode('utf-8', errors='ignore').strip()

                # Triangle count
                count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                    raise STLParseError("Invalid binary STL: cannot read triangle count")

                triangle_count = struct.unpack('<I', count_bytes)[0]
                self.logger.info(f"Parsing binary STL with {triangle_count} triangles [array path]")

                if triangle_count <= 0:
                    raise STLParseError("Invalid triangle count in STL")

                # Read all triangle records
                total_bytes = triangle_count * self.BINARY_TRIANGLE_SIZE
                self._update_progress(8.0, "Reading triangle block...", progress_callback)

                data = file.read(total_bytes)
                if len(data) != total_bytes:
                    raise STLParseError(f"Failed to read triangle block ({len(data)} of {total_bytes} bytes)")

                self._update_progress(22.0, "Decoding floats...", progress_callback)

                # Decode first 48 bytes of each 50-byte record as 12 float32s
                u8 = np.frombuffer(data, dtype=np.uint8).reshape(triangle_count, self.BINARY_TRIANGLE_SIZE)  # type: ignore

                # Process in chunks for progress reporting
                chunk_size = min(50000, max(10000, triangle_count // 20))
                floats = np.empty((triangle_count, 12), dtype=np.float32)

                for start_idx in range(0, triangle_count, chunk_size):
                    end_idx = min(start_idx + chunk_size, triangle_count)
                    chunk_floats = u8[start_idx:end_idx, :48].view('<f4').reshape(end_idx - start_idx, 12)
                    floats[start_idx:end_idx] = chunk_floats

                    # Report progress during array decoding
                    decode_progress = 22.0 + 13.0 * (end_idx / triangle_count)
                    self._update_progress(decode_progress, f"Decoding arrays: {end_idx:,}/{triangle_count:,}", progress_callback)
                    self._check_cancellation()

                # Release reference to raw data buffer
                del u8

                # Prepare arrays
                self._update_progress(35.0, "Preparing arrays...", progress_callback)

                # normals: cols 0..2, vertices: cols 3..11 reshaped to (N,3,3)
                verts = floats[:, 3:12].reshape(triangle_count, 3, 3)
                vertex_array = verts.reshape(triangle_count * 3, 3).astype('float32', copy=False)

                # Repeat each normal 3 times, one per vertex
                normal_array = np.repeat(floats[:, 0:3], 3, axis=0).astype('float32', copy=False)

                # Bounds
                flat = verts.reshape(-1, 3)
                min_xyz = flat.min(axis=0)
                max_xyz = flat.max(axis=0)

                # Free large temps early
                del verts
                del flat
                del floats

                # Force garbage collection
                gc.collect()

                # Create result dictionary
                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size

                result = {
                    'header': header,
                    'triangles': [],  # Empty for array-based models
                    'format': ModelFormat.STL,
                    'stats': {
                        'vertex_count': triangle_count * 3,
                        'triangle_count': triangle_count,
                        'min_bounds': [float(min_xyz[0]), float(min_xyz[1]), float(min_xyz[2])],
                        'max_bounds': [float(max_xyz[0]), float(max_xyz[1]), float(max_xyz[2])],
                        'file_size_bytes': file_size,
                        'parsing_time_seconds': parsing_time
                    },
                    'vertex_array': vertex_array,
                    'normal_array': normal_array,
                    'loading_state': 'ARRAY_GEOMETRY'
                }

                self._update_progress(100.0, "Array-based STL parsing completed", progress_callback)

                self.logger.info(
                    f"Successfully parsed binary STL (array path): {triangle_count} triangles, "
                    f"time: {parsing_time:.2f}s"
                )

                return result

        except Exception as e:
            self.logger.error(f"Error in array-based binary STL parse: {str(e)}")
            raise STLParseError(f"Failed to parse binary STL (array): {str(e)}")

    def _parse_ascii_stl(self, file_path: Path, progress_callback: Optional[StreamingProgressCallback] = None) -> Dict[str, Any]:
        """
        Parse ASCII STL file format.

        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing parsed model data

        Raises:
            STLParseError: If parsing fails
        """
        start_time = time.time()
        triangles = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()

                if not lines:
                    raise STLParseError("Empty STL file")

                # Extract header from first line
                header = lines[0].strip()
                if not header.lower().startswith('solid'):
                    raise STLParseError("Invalid ASCII STL: must start with 'solid'")

                # Initialize bounds for statistics
                min_x = min_y = min_z = float('inf')
                max_x = max_y = max_z = float('-inf')

                # Parse triangles
                i = 1  # Start from second line (after header)
                line_count = len(lines)
                triangle_count = 0

                while i < line_count:
                    self._check_cancellation()

                    line = lines[i].strip().lower()

                    # Look for "facet normal" to start a triangle
                    if line.startswith('facet normal'):
                        try:
                            # Parse normal vector
                            normal_parts = line.split()
                            if len(normal_parts) != 5:
                                raise STLParseError(f"Invalid facet normal line: {line}")

                            normal = [
                                float(normal_parts[2]),
                                float(normal_parts[3]),
                                float(normal_parts[4])
                            ]

                            # Expect "outer loop" on next line
                            i += 1
                            if i >= line_count or not lines[i].strip().lower() == 'outer loop':
                                raise STLParseError("Expected 'outer loop' after facet normal")

                            # Parse three vertices
                            vertices = []
                            for j in range(3):
                                i += 1
                                if i >= line_count:
                                    raise STLParseError("Unexpected end of file while parsing vertices")

                                vertex_line = lines[i].strip().lower()
                                if not vertex_line.startswith('vertex'):
                                    raise STLParseError(f"Expected 'vertex', got: {vertex_line}")

                                vertex_parts = vertex_line.split()
                                if len(vertex_parts) != 4:
                                    raise STLParseError(f"Invalid vertex line: {vertex_line}")

                                vertex = [
                                    float(vertex_parts[1]),
                                    float(vertex_parts[2]),
                                    float(vertex_parts[3])
                                ]
                                vertices.append(vertex)

                                # Update bounds
                                min_x = min(min_x, vertex[0])
                                min_y = min(min_y, vertex[1])
                                min_z = min(min_z, vertex[2])
                                max_x = max(max_x, vertex[0])
                                max_y = max(max_y, vertex[1])
                                max_z = max(max_z, vertex[2])

                            # Expect "endloop"
                            i += 1
                            if i >= line_count or not lines[i].strip().lower() == 'endloop':
                                raise STLParseError("Expected 'endloop' after vertices")

                            # Expect "endfacet"
                            i += 1
                            if i >= line_count or not lines[i].strip().lower() == 'endfacet':
                                raise STLParseError("Expected 'endfacet' after endloop")

                            # Create triangle
                            triangle = {
                                'normal': normal,
                                'vertices': vertices,
                                'attribute_byte_count': 0
                            }
                            triangles.append(triangle)
                            triangle_count += 1

                            # Report progress
                            if progress_callback and triangle_count % 100 == 0:
                                progress = (i / line_count) * 100
                                self._update_progress(progress, f"Parsed {triangle_count} triangles", progress_callback)

                            # Periodic garbage collection for large files
                            if triangle_count % 1000 == 0 and triangle_count > 0:
                                gc.collect()

                        except ValueError as e:
                            raise STLParseError(f"Invalid numeric value in triangle {triangle_count}: {str(e)}")

                    i += 1

                if triangle_count == 0:
                    raise STLParseError("No triangles found in ASCII STL file")

                # Create result dictionary
                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size

                result = {
                    'header': header,
                    'triangles': triangles,
                    'format': ModelFormat.STL,
                    'stats': {
                        'vertex_count': triangle_count * 3,
                        'triangle_count': triangle_count,
                        'min_bounds': [min_x, min_y, min_z],
                        'max_bounds': [max_x, max_y, max_z],
                        'file_size_bytes': file_size,
                        'parsing_time_seconds': parsing_time
                    }
                }

                self._update_progress(100.0, "ASCII STL parsing completed", progress_callback)

                self.logger.info(
                    f"Successfully parsed ASCII STL: {triangle_count} triangles, "
                    f"bounds: [{min_x:.3f}, {min_y:.3f}, {min_z:.3f}] to "
                    f"[{max_x:.3f}, {max_y:.3f}, {max_z:.3f}], "
                    f"time: {parsing_time:.2f}s"
                )

                return result

        except Exception as e:
            self.logger.error(f"Error parsing ASCII STL: {str(e)}")
            raise STLParseError(f"Failed to parse ASCII STL: {str(e)}")

    def _get_model_info_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method to get model information.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing model information
        """
        try:
            # Get basic file info
            file_size = file_path.stat().st_size

            # Detect format and get triangle count
            format_type = self._detect_format(file_path)
            
            if format_type == STLFormat.BINARY:
                triangle_count = self._get_binary_triangle_count(file_path)
            elif format_type == STLFormat.ASCII:
                triangle_count = self._get_ascii_triangle_count(file_path)
            else:
                raise STLParseError("Unable to determine STL format")

            # Create basic stats (approximate bounds)
            vertex_count = triangle_count * 3

            return {
                'vertex_count': vertex_count,
                'face_count': triangle_count,
                'has_materials': False,
                'has_textures': False,
                'bounding_box': [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],  # Default unit cube
                'format_type': format_type.value,
                'triangle_count': triangle_count
            }

        except Exception as e:
            self.logger.error(f"Failed to get STL model info: {str(e)}")
            raise ParseError(f"Failed to get model info: {str(e)}")

    def _validate_file_internal(self, file_path: Path) -> bool:
        """
        Internal method to validate file format.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid, False otherwise
        """
        try:
            # Check file exists and is not empty
            if not file_path.exists() or file_path.stat().st_size == 0:
                return False

            # Detect format
            format_type = self._detect_format(file_path)
            if format_type == STLFormat.UNKNOWN:
                return False

            # Basic format validation
            if format_type == STLFormat.BINARY:
                with open(file_path, 'rb') as file:
                    file.seek(self.BINARY_HEADER_SIZE)
                    count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                    if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                        return False

                    triangle_count = struct.unpack('<I', count_bytes)[0]
                    if triangle_count == 0:
                        return False

                    # Check if file size matches expected
                    file.seek(0, 2)
                    file_size = file.tell()
                    expected_size = (
                        self.BINARY_HEADER_SIZE +
                        self.BINARY_TRIANGLE_COUNT_SIZE +
                        (triangle_count * self.BINARY_TRIANGLE_SIZE)
                    )

                    return file_size == expected_size

            elif format_type == STLFormat.ASCII:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    first_line = file.readline().strip().lower()
                    if not first_line.startswith('solid'):
                        return False

                    # Check for at least one triangle
                    content = file.read(1000).lower()
                    return 'facet normal' in content and 'vertex' in content

            return False

        except Exception as e:
            self.logger.warning(f"STL validation error for {file_path}: {str(e)}")
            return False

    def _parse_stream_internal(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Internal method for streaming parsing.

        Args:
            file_path: Path to the model file

        Returns:
            Iterator yielding parsed chunks
        """
        try:
            format_type = self._detect_format(file_path)
            
            if format_type == STLFormat.BINARY:
                yield from self._stream_binary_stl(file_path)
            elif format_type == STLFormat.ASCII:
                yield from self._stream_ascii_stl(file_path)
            else:
                raise STLParseError("Unable to determine STL format for streaming")

        except Exception as e:
            self.logger.error(f"Error in STL streaming: {str(e)}")
            raise ParseError(f"Streaming failed: {str(e)}")

    def _stream_binary_stl(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Stream binary STL file in chunks.

        Args:
            file_path: Path to the binary STL file

        Yields:
            Dictionary containing triangle chunk data
        """
        try:
            with open(file_path, 'rb') as file:
                # Skip header
                file.seek(self.BINARY_HEADER_SIZE + self.BINARY_TRIANGLE_COUNT_SIZE)

                # Get triangle count
                file.seek(self.BINARY_HEADER_SIZE)
                count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                triangle_count = struct.unpack('<I', count_bytes)[0]

                # Stream in chunks
                chunk_size = 1000  # Triangles per chunk
                triangles_processed = 0

                while triangles_processed < triangle_count:
                    self._check_cancellation()

                    end_triangle = min(triangles_processed + chunk_size, triangle_count)
                    triangles_in_chunk = end_triangle - triangles_processed

                    # Read chunk data
                    chunk_bytes = triangles_in_chunk * self.BINARY_TRIANGLE_SIZE
                    data = file.read(chunk_bytes)

                    if len(data) != chunk_bytes:
                        break

                    # Parse chunk
                    if np is not None:
                        # Use NumPy for faster parsing
                        u8 = np.frombuffer(data, dtype=np.uint8).reshape(triangles_in_chunk, self.BINARY_TRIANGLE_SIZE)  # type: ignore
                        floats = u8[:, :48].view('<f4').reshape(triangles_in_chunk, 12)
                        
                        chunk_triangles = []
                        for i in range(triangles_in_chunk):
                            triangle = {
                                'normal': floats[i, 0:3].tolist(),
                                'vertices': [
                                    floats[i, 3:6].tolist(),
                                    floats[i, 6:9].tolist(),
                                    floats[i, 9:12].tolist()
                                ],
                                'attribute_byte_count': 0
                            }
                            chunk_triangles.append(triangle)
                    else:
                        # Pure Python fallback
                        chunk_triangles = []
                        for i in range(triangles_in_chunk):
                            offset = i * self.BINARY_TRIANGLE_SIZE
                            triangle_data = data[offset:offset + self.BINARY_TRIANGLE_SIZE]
                            values = struct.unpack('<ffffffffffffH', triangle_data)
                            
                            triangle = {
                                'normal': [values[0], values[1], values[2]],
                                'vertices': [
                                    [values[3], values[4], values[5]],
                                    [values[6], values[7], values[8]],
                                    [values[9], values[10], values[11]]
                                ],
                                'attribute_byte_count': values[12]
                            }
                            chunk_triangles.append(triangle)

                    # Yield chunk
                    yield {
                        'triangles': chunk_triangles,
                        'chunk_index': triangles_processed // chunk_size,
                        'triangles_in_chunk': triangles_in_chunk,
                        'total_triangles': triangle_count,
                        'progress': triangles_processed / triangle_count
                    }

                    triangles_processed = end_triangle

                    # Update progress
                    self._current_progress = triangles_processed / triangle_count

        except Exception as e:
            self.logger.error(f"Error streaming binary STL: {str(e)}")
            raise ParseError(f"Binary STL streaming failed: {str(e)}")

    def _stream_ascii_stl(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """
        Stream ASCII STL file line by line.

        Args:
            file_path: Path to the ASCII STL file

        Yields:
            Dictionary containing parsed triangle data
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                
                # Skip header
                if lines and lines[0].strip().lower().startswith('solid'):
                    header = lines[0].strip()
                else:
                    raise STLParseError("Invalid ASCII STL: must start with 'solid'")

                # Parse triangles
                i = 1
                line_count = len(lines)
                triangle_count = 0
                chunk_triangles = []
                chunk_size = 100  # Triangles per chunk

                while i < line_count:
                    self._check_cancellation()

                    line = lines[i].strip().lower()

                    if line.startswith('facet normal'):
                        try:
                            # Parse normal vector
                            normal_parts = line.split()
                            if len(normal_parts) != 5:
                                continue

                            normal = [
                                float(normal_parts[2]),
                                float(normal_parts[3]),
                                float(normal_parts[4])
                            ]

                            # Skip to vertices
                            i += 1  # outer loop
                            i += 1  # first vertex
                            vertex_line1 = lines[i].strip().lower()
                            v1_parts = vertex_line1.split()
                            v1 = [float(v1_parts[1]), float(v1_parts[2]), float(v1_parts[3])]

                            i += 1  # second vertex
                            vertex_line2 = lines[i].strip().lower()
                            v2_parts = vertex_line2.split()
                            v2 = [float(v2_parts[1]), float(v2_parts[2]), float(v2_parts[3])]

                            i += 1  # third vertex
                            vertex_line3 = lines[i].strip().lower()
                            v3_parts = vertex_line3.split()
                            v3 = [float(v3_parts[1]), float(v3_parts[2]), float(v3_parts[3])]

                            # Skip to endfacet
                            i += 2  # endloop, endfacet

                            # Create triangle
                            triangle = {
                                'normal': normal,
                                'vertices': [v1, v2, v3],
                                'attribute_byte_count': 0
                            }
                            chunk_triangles.append(triangle)
                            triangle_count += 1

                            # Yield chunk when full
                            if len(chunk_triangles) >= chunk_size:
                                yield {
                                    'triangles': chunk_triangles,
                                    'chunk_index': triangle_count // chunk_size,
                                    'triangles_in_chunk': len(chunk_triangles),
                                    'total_triangles': triangle_count,  # Approximate
                                    'progress': i / line_count
                                }
                                chunk_triangles = []

                        except (ValueError, IndexError):
                            continue  # Skip invalid triangles

                    i += 1

                # Yield remaining triangles
                if chunk_triangles:
                    yield {
                        'triangles': chunk_triangles,
                        'chunk_index': triangle_count // chunk_size,
                        'triangles_in_chunk': len(chunk_triangles),
                        'total_triangles': triangle_count,
                        'progress': 1.0
                    }

        except Exception as e:
            self.logger.error(f"Error streaming ASCII STL: {str(e)}")
            raise ParseError(f"ASCII STL streaming failed: {str(e)}")

    def _validate_geometry_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry validation.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing validation results
        """
        try:
            # Basic validation first
            if not self._validate_file_internal(file_path):
                return {
                    'is_valid': False,
                    'issues': ['File format validation failed'],
                    'statistics': {}
                }

            # Parse a small sample to check geometry
            format_type = self._detect_format(file_path)
            
            issues = []
            stats = {}

            if format_type == STLFormat.BINARY:
                # Sample first few triangles
                with open(file_path, 'rb') as file:
                    file.seek(self.BINARY_HEADER_SIZE + self.BINARY_TRIANGLE_COUNT_SIZE)
                    
                    # Read first triangle
                    triangle_data = file.read(self.BINARY_TRIANGLE_SIZE)
                    if len(triangle_data) == self.BINARY_TRIANGLE_SIZE:
                        values = struct.unpack('<ffffffffffffH', triangle_data)
                        
                        # Check for degenerate triangles
                        v1 = [values[3], values[4], values[5]]
                        v2 = [values[6], values[7], values[8]]
                        v3 = [values[9], values[10], values[11]]
                        
                        # Simple degeneracy check (area near zero)
                        import math
                        area = 0.5 * math.sqrt(
                            ((v2[0] - v1[0]) * (v3[1] - v1[1]) - (v3[0] - v1[0]) * (v2[1] - v1[1]))**2 +
                            ((v2[1] - v1[1]) * (v3[2] - v1[2]) - (v3[1] - v1[1]) * (v2[2] - v1[2]))**2 +
                            ((v2[2] - v1[2]) * (v3[0] - v1[0]) - (v3[2] - v1[2]) * (v2[0] - v1[0]))**2
                        )
                        
                        if area < 1e-10:
                            issues.append('Degenerate triangles detected')
                        
                        stats['sample_triangle_area'] = area

            elif format_type == STLFormat.ASCII:
                # Sample first few lines
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    first_line = file.readline().strip().lower()
                    if not first_line.startswith('solid'):
                        issues.append('Invalid ASCII STL header')
                    
                    # Check for basic triangle structure
                    content = file.read(500).lower()
                    if 'facet normal' not in content or 'vertex' not in content:
                        issues.append('No valid triangle data found')

            return {
                'is_valid': len(issues) == 0,
                'issues': issues,
                'statistics': stats
            }

        except Exception as e:
            self.logger.error(f"Error validating STL geometry: {str(e)}")
            return {
                'is_valid': False,
                'issues': [f'Validation error: {str(e)}'],
                'statistics': {}
            }

    def _get_geometry_stats_internal(self, file_path: Path) -> Dict[str, Any]:
        """
        Internal method for geometry statistics.

        Args:
            file_path: Path to the model file

        Returns:
            Dictionary containing geometric statistics
        """
        try:
            # Parse a sample to get statistics
            format_type = self._detect_format(file_path)
            
            if format_type == STLFormat.BINARY:
                triangle_count = self._get_binary_triangle_count(file_path)
            elif format_type == STLFormat.ASCII:
                triangle_count = self._get_ascii_triangle_count(file_path)
            else:
                raise STLParseError("Unable to determine STL format")

            # Basic statistics
            stats = {
                'vertex_count': triangle_count * 3,
                'face_count': triangle_count,
                'edge_count': triangle_count * 3,  # Approximation
                'component_count': 1,  # Assume single component for now
                'degeneracy_count': 0,  # Would need full parse to determine
                'manifold': True  # Assume manifold for STL files
            }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting STL geometry stats: {str(e)}")
            raise ParseError(f"Failed to get geometry stats: {str(e)}")

    def _get_binary_triangle_count(self, file_path: Path) -> int:
        """
        Get triangle count from binary STL without loading full geometry.

        Args:
            file_path: Path to the binary STL file

        Returns:
            Triangle count
        """
        with open(file_path, 'rb') as file:
            # Skip header
            file.seek(self.BINARY_HEADER_SIZE)

            # Read triangle count
            count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
            if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                raise STLParseError("Invalid binary STL: cannot read triangle count")

            triangle_count = struct.unpack('<I', count_bytes)[0]
            return triangle_count

    def _get_ascii_triangle_count(self, file_path: Path) -> int:
        """
        Get triangle count from ASCII STL without loading full geometry.

        Args:
            file_path: Path to the ASCII STL file

        Returns:
            Triangle count
        """
        triangle_count = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if line.strip().lower().startswith('facet normal'):
                    triangle_count += 1

        return triangle_count

    def get_parser_info(self) -> Dict[str, str]:
        """
        Get information about the parser implementation.

        Returns:
            Dictionary containing parser information
        """
        return {
            'name': 'Refactored STL Parser',
            'version': '2.0.0',
            'author': 'Candy-Cadence Development Team',
            'description': 'Enhanced STL parser with streaming support, GPU acceleration, and improved error handling'
        }


# Alias for backward compatibility
STLParser = RefactoredSTLParser