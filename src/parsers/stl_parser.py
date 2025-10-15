"""
STL file parser for 3D-MM application.

This module provides parsing functionality for both binary and ASCII STL file formats.
It includes memory-efficient processing, progress reporting, and comprehensive error handling.
"""

import struct
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union, BinaryIO, Iterator
import gc
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

# Optional accelerated path
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # Fallback to pure-Python parsing when NumPy is not available

def _build_triangles_from_floats_chunk(chunk: "np.ndarray") -> List["Triangle"]:  # type: ignore
    """
    Worker function to convert a chunk of float rows (shape: N x 12) into Triangle objects.
    Executed in a separate process to leverage multiple CPU cores.
    """
    res: List["Triangle"] = []
    # Import inside to ensure pickling works even if module-level imports change
    from .base_parser import Triangle, Vector3D  # type: ignore
    for row in chunk:
        normal = Vector3D(float(row[0]), float(row[1]), float(row[2]))
        v1 = Vector3D(float(row[3]), float(row[4]), float(row[5]))
        v2 = Vector3D(float(row[6]), float(row[7]), float(row[8]))
        v3 = Vector3D(float(row[9]), float(row[10]), float(row[11]))
        res.append(Triangle(normal, v1, v2, v3, 0))
    return res

from .base_parser import (
    BaseParser, Model, ModelFormat, Triangle, Vector3D,
    ModelStats, ParseError, ProgressCallback, LoadingState
)
from core.logging_config import get_logger, log_function_call


class STLFormat(Enum):
    """STL file format types."""
    BINARY = "binary"
    ASCII = "ascii"
    UNKNOWN = "unknown"


@dataclass
class STLModel:
    """Complete 3D model representation with geometry and statistics."""
    header: str
    triangles: List[Triangle]
    stats: ModelStats
    
    def get_vertices(self) -> List[Vector3D]:
        """Get all unique vertices from all triangles."""
        vertices = []
        for triangle in self.triangles:
            vertices.extend(triangle.get_vertices())
        return vertices
    
    def get_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        return (
            len(self.header.encode('utf-8')) +
            len(self.triangles) * (50 + 4 * 9) +  # Rough estimate
            100  # Stats and other data
        )


class STLParseError(ParseError):
    """Custom exception for STL parsing errors."""
    pass


class STLProgressCallback(ProgressCallback):
    """Callback interface for progress reporting during parsing."""
    pass


class STLParser(BaseParser):
    """
    STL file parser supporting both binary and ASCII formats.
    
    Features:
    - Memory-efficient parsing for large files
    - Progress reporting for long operations
    - Comprehensive error handling and validation
    - Integration with JSON logging system
    - Performance optimization for different file sizes
    """
    
    # Binary STL format constants
    BINARY_HEADER_SIZE = 80
    BINARY_TRIANGLE_COUNT_SIZE = 4
    BINARY_TRIANGLE_SIZE = 50  # 12 bytes for normal + 36 bytes for vertices + 2 bytes for attribute
    
    def __init__(self):
        """Initialize the STL parser."""
        super().__init__()
    
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
            self.logger.error(f"Error detecting STL format: {str(e)}")
            raise STLParseError(f"Failed to detect STL format: {str(e)}")
    
    def _parse_binary_stl(
        self,
        file_path: Path,
        progress_callback: Optional[STLProgressCallback] = None
    ) -> STLModel:
        """
        Parse binary STL file format.

        Optimized path:
        - Uses NumPy to decode triangle data in bulk
        - Computes bounds using vectorized operations
        - Builds Triangle objects efficiently in chunks
        Falls back to pure-Python parsing if NumPy is not available.

        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback

        Returns:
            Parsed STL model

        Raises:
            STLParseError: If parsing fails
        """
        start_time = time.time()
        triangles: List[Triangle] = []

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
                self.logger.info(f"Parsing binary STL with {triangle_count} triangles")

                # Validate triangle count is reasonable
                if triangle_count > 100000000:  # 100 million triangles is unreasonable
                    raise STLParseError(f"Invalid triangle count: {triangle_count}")

                # Decide path: vectorized if NumPy available, else original loop
                use_vectorized = (np is not None) and (triangle_count >= 20000)

                if use_vectorized:
                    # Report progress
                    if progress_callback:
                        progress_callback.report(5.0, "Reading binary triangle block...")

                    # Read all triangle records: 50 bytes each
                    total_bytes = triangle_count * self.BINARY_TRIANGLE_SIZE
                    data = file.read(total_bytes)
                    if len(data) != total_bytes:
                        raise STLParseError(f"Failed to read triangle block ({len(data)} of {total_bytes} bytes)")

                    if progress_callback:
                        progress_callback.report(20.0, "Decoding triangle floats...")

                    # Convert to NumPy array and extract floats
                    # Layout per triangle: 48 bytes (12 float32) + 2 bytes (uint16 attribute)
                    # View first 48 bytes as float32 (little-endian)
                    u8 = np.frombuffer(data, dtype=np.uint8).reshape(triangle_count, self.BINARY_TRIANGLE_SIZE)  # type: ignore
                    floats = u8[:, :48].copy().view('<f4').reshape(triangle_count, 12)  # shape: (N, 12)

                    # normals: cols 0:3, vertices: cols 3:12 as 3x3
                    verts = floats[:, 3:12].reshape(triangle_count, 3, 3)

                    # Compute bounds via vectorized operations
                    min_xyz = verts.reshape(-1, 3).min(axis=0)
                    max_xyz = verts.reshape(-1, 3).max(axis=0)

                    # Build Triangle dataclasses using multiple processes for large datasets
                    if progress_callback:
                        progress_callback.report(40.0, "Building triangles from decoded floats (multi-core)...")

                    cpu_cnt = max(2, (os.cpu_count() or 2))
                    # Cap workers to avoid excessive memory duplication
                    max_workers = min(cpu_cnt, 8)

                    # Split into roughly equal chunks per worker
                    splits = max_workers
                    indices = np.linspace(0, triangle_count, splits + 1, dtype=np.int64)  # type: ignore
                    chunks = [(int(indices[i]), int(indices[i + 1])) for i in range(splits) if int(indices[i]) < int(indices[i + 1])]

                    built_total = 0
                    with ProcessPoolExecutor(max_workers=max_workers) as pool:
                        futures = []
                        for start_idx, end_idx in chunks:
                            # Note: sending subarrays incurs copy overhead but unlocks multi-core construction
                            futures.append(pool.submit(_build_triangles_from_floats_chunk, floats[start_idx:end_idx].copy()))
                        for fut in as_completed(futures):
                            part = fut.result()
                            triangles.extend(part)
                            built_total += len(part)
                            if progress_callback:
                                pct = 40.0 + 55.0 * (built_total / triangle_count)
                                progress_callback.report(pct, f"Built {built_total}/{triangle_count} triangles")

                    # Final GC to release worker-side memory sooner
                    gc.collect()

                    # Stats
                    parsing_time = time.time() - start_time
                    file_size = file_path.stat().st_size
                    stats = ModelStats(
                        vertex_count=triangle_count * 3,
                        triangle_count=triangle_count,
                        min_bounds=Vector3D(float(min_xyz[0]), float(min_xyz[1]), float(min_xyz[2])),
                        max_bounds=Vector3D(float(max_xyz[0]), float(max_xyz[1]), float(max_xyz[2])),
                        file_size_bytes=file_size,
                        format_type=STLFormat.BINARY,
                        parsing_time_seconds=parsing_time
                    )

                    if progress_callback:
                        progress_callback.report(100.0, "Binary STL parsing completed")

                    self.logger.info(
                        f"Successfully parsed binary STL (vectorized): {triangle_count} triangles, "
                        f"bounds: [{min_xyz[0]:.3f}, {min_xyz[1]:.3f}, {min_xyz[2]:.3f}] to "
                        f"[{max_xyz[0]:.3f}, {max_xyz[1]:.3f}, {max_xyz[2]:.3f}], "
                        f"time: {parsing_time:.2f}s"
                    )
                    return Model(header=header, triangles=triangles, stats=stats, format_type=ModelFormat.STL)

                # ---- Fallback: original pure-Python loop (smaller files or NumPy unavailable) ----
                min_x = min_y = min_z = float('inf')
                max_x = max_y = max_z = float('-inf')

                for i in range(triangle_count):
                    if self._cancel_parsing:
                        raise STLParseError("Parsing was cancelled")

                    # Read triangle data (50 bytes)
                    triangle_data = file.read(self.BINARY_TRIANGLE_SIZE)
                    if len(triangle_data) != self.BINARY_TRIANGLE_SIZE:
                        raise STLParseError(f"Failed to read triangle {i}: incomplete data")

                    values = struct.unpack('<ffffffffffffH', triangle_data)

                    normal = Vector3D(values[0], values[1], values[2])
                    v1 = Vector3D(values[3], values[4], values[5])
                    v2 = Vector3D(values[6], values[7], values[8])
                    v3 = Vector3D(values[9], values[10], values[11])
                    attribute_byte_count = values[12]

                    triangles.append(Triangle(normal, v1, v2, v3, attribute_byte_count))

                    # Update bounds
                    for vertex in (v1, v2, v3):
                        min_x = min(min_x, vertex.x)
                        min_y = min(min_y, vertex.y)
                        min_z = min(min_z, vertex.z)
                        max_x = max(max_x, vertex.x)
                        max_y = max(max_y, vertex.y)
                        max_z = max(max_z, vertex.z)

                    # Report progress
                    if progress_callback and i % 1000 == 0:
                        progress = (i / triangle_count) * 100
                        progress_callback.report(progress, f"Parsed {i}/{triangle_count} triangles")

                    if i % 10000 == 0 and i > 0:
                        gc.collect()

                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size
                stats = ModelStats(
                    vertex_count=triangle_count * 3,
                    triangle_count=triangle_count,
                    min_bounds=Vector3D(min_x, min_y, min_z),
                    max_bounds=Vector3D(max_x, max_y, max_z),
                    file_size_bytes=file_size,
                    format_type=STLFormat.BINARY,
                    parsing_time_seconds=parsing_time
                )

                self.logger.info(
                    f"Successfully parsed binary STL: {triangle_count} triangles, "
                    f"bounds: [{stats.min_bounds.x:.3f}, {stats.min_bounds.y:.3f}, {stats.min_bounds.z:.3f}] to "
                    f"[{stats.max_bounds.x:.3f}, {stats.max_bounds.y:.3f}, {stats.max_bounds.z:.3f}], "
                    f"time: {parsing_time:.2f}s"
                )

                return Model(header=header, triangles=triangles, stats=stats, format_type=ModelFormat.STL)

        except Exception as e:
            self.logger.error(f"Error parsing binary STL: {str(e)}")
            raise STLParseError(f"Failed to parse binary STL: {str(e)}")
    
    def _parse_ascii_stl(
        self,
        file_path: Path,
        progress_callback: Optional[STLProgressCallback] = None
    ) -> STLModel:
        """
        Parse ASCII STL file format.
        
        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback
            
        Returns:
            Parsed STL model
            
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
                    if self._cancel_parsing:
                        raise STLParseError("Parsing was cancelled")
                    
                    line = lines[i].strip().lower()
                    
                    # Look for "facet normal" to start a triangle
                    if line.startswith('facet normal'):
                        try:
                            # Parse normal vector
                            normal_parts = line.split()
                            if len(normal_parts) != 5:
                                raise STLParseError(f"Invalid facet normal line: {line}")
                            
                            normal = Vector3D(
                                float(normal_parts[2]),
                                float(normal_parts[3]),
                                float(normal_parts[4])
                            )
                            
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
                                
                                vertex = Vector3D(
                                    float(vertex_parts[1]),
                                    float(vertex_parts[2]),
                                    float(vertex_parts[3])
                                )
                                vertices.append(vertex)
                                
                                # Update bounds
                                min_x = min(min_x, vertex.x)
                                min_y = min(min_y, vertex.y)
                                min_z = min(min_z, vertex.z)
                                max_x = max(max_x, vertex.x)
                                max_y = max(max_y, vertex.y)
                                max_z = max(max_z, vertex.z)
                            
                            # Expect "endloop"
                            i += 1
                            if i >= line_count or not lines[i].strip().lower() == 'endloop':
                                raise STLParseError("Expected 'endloop' after vertices")
                            
                            # Expect "endfacet"
                            i += 1
                            if i >= line_count or not lines[i].strip().lower() == 'endfacet':
                                raise STLParseError("Expected 'endfacet' after endloop")
                            
                            # Create triangle
                            triangle = Triangle(normal, vertices[0], vertices[1], vertices[2])
                            triangles.append(triangle)
                            triangle_count += 1
                            
                            # Report progress
                            if progress_callback and triangle_count % 100 == 0:
                                progress = (i / line_count) * 100
                                progress_callback.report(progress, f"Parsed {triangle_count} triangles")
                            
                            # Periodic garbage collection for large files
                            if triangle_count % 1000 == 0 and triangle_count > 0:
                                gc.collect()
                            
                        except ValueError as e:
                            raise STLParseError(f"Invalid numeric value in triangle {triangle_count}: {str(e)}")
                    
                    i += 1
                
                if triangle_count == 0:
                    raise STLParseError("No triangles found in ASCII STL file")
                
                # Create model statistics
                parsing_time = time.time() - start_time
                file_size = file_path.stat().st_size
                
                min_bounds = Vector3D(min_x, min_y, min_z)
                max_bounds = Vector3D(max_x, max_y, max_z)
                
                stats = ModelStats(
                    vertex_count=triangle_count * 3,
                    triangle_count=triangle_count,
                    min_bounds=min_bounds,
                    max_bounds=max_bounds,
                    file_size_bytes=file_size,
                    format_type=STLFormat.ASCII,
                    parsing_time_seconds=parsing_time
                )
                
                self.logger.info(
                    f"Successfully parsed ASCII STL: {triangle_count} triangles, "
                    f"bounds: [{min_x:.3f}, {min_y:.3f}, {min_z:.3f}] to "
                    f"[{max_x:.3f}, {max_y:.3f}, {max_z:.3f}], "
                    f"time: {parsing_time:.2f}s"
                )
                
                return Model(header=header, triangles=triangles, stats=stats, format_type=ModelFormat.STL)
                
        except Exception as e:
            self.logger.error(f"Error parsing ASCII STL: {str(e)}")
            raise STLParseError(f"Failed to parse ASCII STL: {str(e)}")
    
    def _parse_file_internal(
        self,
        file_path: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Model:
        """
        Internal method to parse an STL file (auto-detecting format).
        
        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback
            
        Returns:
            Parsed STL model
            
        Raises:
            STLParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        # Convert to Path object
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"STL file not found: {file_path}")
        
        # Validate file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise STLParseError("STL file is empty")
        
        self.logger.info(f"Starting STL parsing: {file_path} ({file_size} bytes)")
        
        try:
            # Detect format
            format_type = self._detect_format(file_path)
            if format_type == STLFormat.UNKNOWN:
                raise STLParseError("Unable to determine STL format (invalid or corrupted file)")
            
            # Parse based on format
            if format_type == STLFormat.BINARY:
                return self._parse_binary_stl(file_path, progress_callback)
            elif format_type == STLFormat.ASCII:
                return self._parse_ascii_stl(file_path, progress_callback)
            else:
                raise STLParseError(f"Unsupported STL format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to parse STL file {file_path}: {str(e)}")
            raise
    
    def _parse_metadata_only_internal(self, file_path: str) -> Model:
        """
        Parse only metadata from an STL file.
        
        Args:
            file_path: Path to the STL file
            
        Returns:
            Model with metadata only
        """
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"STL file not found: {file_path}")
        
        file_size = file_path.stat().st_size
        start_time = time.time()
        
        try:
            # Detect format
            format_type = self._detect_format(file_path)
            if format_type == STLFormat.UNKNOWN:
                raise STLParseError("Unable to determine STL format")
            
            # Get triangle count without loading full geometry
            if format_type == STLFormat.BINARY:
                triangle_count = self._get_binary_triangle_count(file_path)
            else:
                triangle_count = self._get_ascii_triangle_count(file_path)
            
            # Create minimal stats (approximate bounds)
            min_bounds = Vector3D(0, 0, 0)
            max_bounds = Vector3D(1, 1, 1)  # Default unit cube
            
            stats = ModelStats(
                vertex_count=triangle_count * 3,
                triangle_count=triangle_count,
                min_bounds=min_bounds,
                max_bounds=max_bounds,
                file_size_bytes=file_size,
                format_type=ModelFormat.STL,
                parsing_time_seconds=time.time() - start_time
            )
            
            # Create metadata-only model
            model = Model(
                header=f"STL Model: {file_path.name}",
                triangles=[],  # Empty geometry
                stats=stats,
                format_type=ModelFormat.STL,
                loading_state=LoadingState.METADATA_ONLY,
                file_path=str(file_path)
            )
            
            self.logger.info(f"Parsed STL metadata: {file_path} ({triangle_count} triangles)")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to parse STL metadata: {str(e)}")
            raise STLParseError(f"Failed to parse STL metadata: {str(e)}")
    
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
    
    def _load_low_res_geometry(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> Model:
        """
        Load low-resolution geometry for progressive loading.
        
        Args:
            file_path: Path to the STL file
            progress_callback: Optional progress callback
            
        Returns:
            Model with low-resolution geometry
        """
        file_path = Path(file_path)
        
        # Get full model first
        full_model = self._parse_file_internal(str(file_path), progress_callback)
        
        # Determine sampling rate based on triangle count
        triangle_count = len(full_model.triangles)
        
        # Performance profile determines sampling rate
        perf_profile = self.performance_monitor.get_performance_profile()
        max_triangles = perf_profile.max_triangles_for_full_quality
        
        if triangle_count <= max_triangles:
            # Small model, no need to reduce
            sample_rate = 1
        else:
            # Calculate sampling rate to get to target triangle count
            sample_rate = max(1, triangle_count // max_triangles)
        
        # Sample triangles
        sampled_triangles = full_model.triangles[::sample_rate]
        
        # Update stats
        sampled_stats = ModelStats(
            vertex_count=len(sampled_triangles) * 3,
            triangle_count=len(sampled_triangles),
            min_bounds=full_model.stats.min_bounds,
            max_bounds=full_model.stats.max_bounds,
            file_size_bytes=full_model.stats.file_size_bytes,
            format_type=full_model.stats.format_type,
            parsing_time_seconds=full_model.stats.parsing_time_seconds
        )
        
        # Create low-res model
        low_res_model = Model(
            header=full_model.header,
            triangles=sampled_triangles,
            stats=sampled_stats,
            format_type=full_model.format_type,
            loading_state=LoadingState.LOW_RES_GEOMETRY,
            file_path=str(file_path)
        )
        
        self.logger.info(f"Created low-res model: {len(sampled_triangles)} triangles (sample rate: 1/{sample_rate})")
        return low_res_model
    
    
    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate an STL file without fully parsing it.
        
        Args:
            file_path: Path to the STL file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_path = Path(file_path)
            
            # Check file exists and is not empty
            if not file_path.exists():
                return False, "File does not exist"
            
            if file_path.stat().st_size == 0:
                return False, "File is empty"
            
            # Detect format
            format_type = self._detect_format(file_path)
            if format_type == STLFormat.UNKNOWN:
                return False, "Unable to determine STL format"
            
            # Basic format validation
            if format_type == STLFormat.BINARY:
                with open(file_path, 'rb') as file:
                    file.seek(self.BINARY_HEADER_SIZE)
                    count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
                    if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                        return False, "Invalid binary STL format"
                    
                    triangle_count = struct.unpack('<I', count_bytes)[0]
                    if triangle_count == 0:
                        return False, "No triangles in file"
                    
                    # Check if file size matches expected
                    file.seek(0, 2)
                    file_size = file.tell()
                    expected_size = (
                        self.BINARY_HEADER_SIZE +
                        self.BINARY_TRIANGLE_COUNT_SIZE +
                        (triangle_count * self.BINARY_TRIANGLE_SIZE)
                    )
                    
                    if file_size != expected_size:
                        return False, "File size doesn't match expected binary STL format"
            
            elif format_type == STLFormat.ASCII:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    first_line = file.readline().strip().lower()
                    if not first_line.startswith('solid'):
                        return False, "Invalid ASCII STL format (must start with 'solid')"
                    
                    # Check for at least one triangle
                    content = file.read(1000).lower()
                    if 'facet normal' not in content or 'vertex' not in content:
                        return False, "No triangle data found in ASCII STL"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return ['.stl']