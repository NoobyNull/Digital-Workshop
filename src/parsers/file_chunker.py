"""
File chunking utilities for multi-threaded STL parsing.

This module provides functionality to split large STL files into manageable
chunks for parallel processing while maintaining triangle boundaries.
"""

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum

from src.core.logging_config import get_logger, log_function_call


class ChunkStrategy(Enum):
    """Strategies for chunking files."""
    SEQUENTIAL = "sequential"  # Process chunks one after another
    PARALLEL = "parallel"      # Process chunks in parallel


@dataclass
class FileChunk:
    """Represents a chunk of an STL file for processing."""
    id: str
    file_path: Path
    start_offset: int  # Byte offset in the file
    size: int          # Size of chunk in bytes
    triangle_start: int  # Starting triangle index
    triangle_count: int  # Number of triangles in this chunk
    strategy: ChunkStrategy

    @property
    def end_offset(self) -> int:
        """Get the end offset of this chunk."""
        return self.start_offset + self.size

    def get_memory_estimate(self) -> int:
        """Estimate memory usage for processing this chunk in bytes."""
        # Rough estimate: triangles * 50 bytes + overhead
        return self.triangle_count * 60


class FileChunker:
    """
    Splits large STL files into chunks for parallel processing.

    This class analyzes STL file structure and creates chunks that align
    with triangle boundaries to ensure proper parsing.
    """

    # Binary STL constants
    BINARY_HEADER_SIZE = 80
    BINARY_TRIANGLE_COUNT_SIZE = 4
    BINARY_TRIANGLE_SIZE = 50  # 12 floats (48 bytes) + 2 bytes attribute

    def __init__(self):
        """Initialize the file chunker."""
        self.logger = get_logger(__name__)

    @log_function_call
    def create_chunks(
        self,
        file_path: Path,
        target_chunk_size_mb: int = 50,
        max_chunks: Optional[int] = None
    ) -> List[FileChunk]:
        """
        Create chunks from an STL file.

        Args:
            file_path: Path to the STL file
            target_chunk_size_mb: Target chunk size in MB
            max_chunks: Maximum number of chunks to create

        Returns:
            List of FileChunk objects

        Raises:
            ValueError: If file cannot be chunked
        """
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"File is empty: {file_path}")

        # Convert target size to bytes
        target_chunk_size_bytes = target_chunk_size_mb * 1024 * 1024

        # Determine file format and get triangle count
        format_type, triangle_count = self._analyze_file(file_path)

        if format_type != "binary":
            # For now, only support binary STL chunking
            # ASCII STL files are typically small and don't need chunking
            raise ValueError(f"Chunking not supported for {format_type} STL files")

        # Calculate optimal chunk parameters
        chunk_params = self._calculate_chunk_parameters(
            file_size, triangle_count, target_chunk_size_bytes, max_chunks
        )

        # Create chunks
        chunks = self._create_binary_chunks(
            file_path, triangle_count, chunk_params
        )

        self.logger.info(
            f"Created {len(chunks)} chunks for {file_path.name} "
            f"({file_size / (1024*1024):.1f} MB, {triangle_count} triangles)"
        )

        return chunks

    @log_function_call
    def get_chunk_metadata(self, file_path: Path) -> dict:
        """
        Get metadata about how a file would be chunked.

        Args:
            file_path: Path to the STL file

        Returns:
            Dictionary with chunking metadata
        """
        try:
            format_type, triangle_count = self._analyze_file(file_path)
            file_size = file_path.stat().st_size

            target_chunk_size_bytes = 50 * 1024 * 1024  # 50MB default
            chunk_params = self._calculate_chunk_parameters(
                file_size, triangle_count, target_chunk_size_bytes
            )

            return {
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "format": format_type,
                "triangle_count": triangle_count,
                "chunk_count": chunk_params["count"],
                "chunk_size_mb": chunk_params["size_bytes"] / (1024 * 1024),
                "strategy": chunk_params["strategy"].value,
                "can_chunk": format_type == "binary" and triangle_count > 1000
            }
        except Exception as e:
            self.logger.error(f"Failed to get chunk metadata for {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "error": str(e),
                "can_chunk": False
            }

    def _analyze_file(self, file_path: Path) -> Tuple[str, int]:
        """
        Analyze STL file to determine format and triangle count.

        Args:
            file_path: Path to the STL file

        Returns:
            Tuple of (format_type, triangle_count)

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, 'rb') as file:
            # Read header
            header = file.read(self.BINARY_HEADER_SIZE)
            if len(header) != self.BINARY_HEADER_SIZE:
                raise ValueError("Invalid STL file: header too short")

            # Try to detect format
            header_text = header.decode('utf-8', errors='ignore').lower().strip()

            # Check for ASCII indicators
            if 'solid' in header_text and header_text.count('\x00') < 5:
                # Likely ASCII - count triangles by scanning
                triangle_count = self._count_ascii_triangles(file_path)
                return "ascii", triangle_count

            # Assume binary format
            count_bytes = file.read(self.BINARY_TRIANGLE_COUNT_SIZE)
            if len(count_bytes) != self.BINARY_TRIANGLE_COUNT_SIZE:
                raise ValueError("Invalid binary STL: cannot read triangle count")

            triangle_count = struct.unpack('<I', count_bytes)[0]

            # Validate file size
            expected_size = (
                self.BINARY_HEADER_SIZE +
                self.BINARY_TRIANGLE_COUNT_SIZE +
                (triangle_count * self.BINARY_TRIANGLE_SIZE)
            )

            file.seek(0, 2)  # Seek to end
            actual_size = file.tell()

            if actual_size != expected_size:
                raise ValueError(
                    f"Binary STL size mismatch: expected {expected_size} bytes, "
                    f"got {actual_size} bytes"
                )

            return "binary", triangle_count

    def _count_ascii_triangles(self, file_path: Path) -> int:
        """
        Count triangles in ASCII STL file.

        Args:
            file_path: Path to the ASCII STL file

        Returns:
            Number of triangles
        """
        count = 0
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if line.strip().lower().startswith('facet normal'):
                    count += 1
        return count

    def _calculate_chunk_parameters(
        self,
        file_size: int,
        triangle_count: int,
        target_chunk_size_bytes: int,
        max_chunks: Optional[int] = None
    ) -> dict:
        """
        Calculate optimal chunking parameters.

        Args:
            file_size: Total file size in bytes
            triangle_count: Total number of triangles
            target_chunk_size_bytes: Target chunk size in bytes
            max_chunks: Maximum number of chunks

        Returns:
            Dictionary with chunk parameters
        """
        # Calculate triangles per chunk based on target size
        bytes_per_triangle = file_size / triangle_count if triangle_count > 0 else 0
        triangles_per_chunk = max(1, int(target_chunk_size_bytes / bytes_per_triangle))

        # Calculate number of chunks
        chunk_count = max(1, (triangle_count + triangles_per_chunk - 1) // triangles_per_chunk)

        # Apply max_chunks limit
        if max_chunks and chunk_count > max_chunks:
            chunk_count = max_chunks
            triangles_per_chunk = max(1, triangle_count // chunk_count)

        # Recalculate chunk size in bytes
        chunk_size_bytes = triangles_per_chunk * bytes_per_triangle

        # Determine strategy
        strategy = ChunkStrategy.PARALLEL if chunk_count > 1 else ChunkStrategy.SEQUENTIAL

        # Ensure reasonable limits
        chunk_count = min(chunk_count, 16)  # Max 16 chunks
        chunk_size_bytes = min(chunk_size_bytes, 200 * 1024 * 1024)  # Max 200MB per chunk

        return {
            "count": chunk_count,
            "size_bytes": int(chunk_size_bytes),
            "triangles_per_chunk": triangles_per_chunk,
            "strategy": strategy
        }

    def _create_binary_chunks(
        self,
        file_path: Path,
        triangle_count: int,
        chunk_params: dict
    ) -> List[FileChunk]:
        """
        Create chunks for binary STL file.

        Args:
            file_path: Path to the binary STL file
            triangle_count: Total number of triangles
            chunk_params: Chunk parameters from _calculate_chunk_parameters

        Returns:
            List of FileChunk objects
        """
        chunks = []
        chunk_count = chunk_params["count"]
        triangles_per_chunk = chunk_params["triangles_per_chunk"]
        strategy = chunk_params["strategy"]

        # Data starts after header + triangle count (84 bytes)
        data_start_offset = self.BINARY_HEADER_SIZE + self.BINARY_TRIANGLE_COUNT_SIZE

        for i in range(chunk_count):
            triangle_start = i * triangles_per_chunk
            triangle_end = min((i + 1) * triangles_per_chunk, triangle_count)
            chunk_triangle_count = triangle_end - triangle_start

            # Calculate byte offsets
            start_offset = data_start_offset + (triangle_start * self.BINARY_TRIANGLE_SIZE)
            size = chunk_triangle_count * self.BINARY_TRIANGLE_SIZE

            chunk = FileChunk(
                id=f"chunk_{i:03d}",
                file_path=file_path,
                start_offset=start_offset,
                size=size,
                triangle_start=triangle_start,
                triangle_count=chunk_triangle_count,
                strategy=strategy
            )

            chunks.append(chunk)

        return chunks