"""
Adaptive file chunking system for multi-threaded 3D model parsing.

This module provides intelligent file chunking that adapts to file size,
format characteristics, and system resources for optimal parallel processing.
"""

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from src.core.logging_config import get_logger, log_function_call
from src.core.memory_manager import get_memory_manager, MemoryStats
from src.core.performance_profiler import get_performance_profiler, PerformanceMetric
from src.parsers.file_chunker import FileChunk, ChunkStrategy


class FileFormat(Enum):
    """Supported 3D file formats."""
    STL_BINARY = "stl_binary"
    STL_ASCII = "stl_ascii"
    OBJ = "obj"
    STEP = "step"
    THREE_MF = "3mf"


class ChunkingStrategy(Enum):
    """Adaptive chunking strategies."""
    FIXED_SIZE = "fixed_size"          # Fixed chunk sizes
    ADAPTIVE_SIZE = "adaptive_size"    # Size adapts to memory/CPU
    FORMAT_AWARE = "format_aware"      # Format-specific boundaries
    MEMORY_CONSTRAINED = "memory_constrained"  # Small chunks for low memory


@dataclass
class ChunkingParameters:
    """Parameters for adaptive chunking."""
    strategy: ChunkingStrategy
    base_chunk_size_mb: float
    max_concurrent_chunks: int
    format_specific_boundaries: bool
    memory_adaptive: bool
    performance_target_ms: float  # Target processing time per chunk


@dataclass
class FileAnalysis:
    """Analysis results for a file."""
    format: FileFormat
    file_size_bytes: int
    estimated_triangles: int
    format_complexity: float  # 0.0-1.0, higher = more complex parsing
    has_variable_structure: bool  # True for formats with variable record sizes
    recommended_strategy: ChunkingStrategy


class AdaptiveChunker:
    """
    Intelligent file chunking system that adapts to file characteristics
    and system resources for optimal parallel processing performance.
    """

    # Format-specific constants
    FORMAT_CONSTANTS = {
        FileFormat.STL_BINARY: {
            "bytes_per_triangle": 50,  # 12 floats + 2 bytes
            "boundary_alignment": 50,  # Must align to triangle boundaries
            "complexity": 0.2,  # Simple binary format
            "variable_structure": False
        },
        FileFormat.STL_ASCII: {
            "bytes_per_triangle": 200,  # Rough estimate for ASCII
            "boundary_alignment": 1,  # Line-based, no strict alignment
            "complexity": 0.4,  # Text parsing overhead
            "variable_structure": True
        },
        FileFormat.OBJ: {
            "bytes_per_triangle": 150,  # Variable due to materials/textures
            "boundary_alignment": 1,  # Line-based
            "complexity": 0.6,  # Material and texture handling
            "variable_structure": True
        },
        FileFormat.STEP: {
            "bytes_per_triangle": 300,  # Complex geometric entities
            "boundary_alignment": 1,  # Entity-based
            "complexity": 0.8,  # Complex parsing logic
            "variable_structure": True
        },
        FileFormat.THREE_MF: {
            "bytes_per_triangle": 250,  # XML + binary data
            "boundary_alignment": 1,  # XML structure
            "complexity": 0.7,  # XML parsing + binary data
            "variable_structure": True
        }
    }

    def __init__(self):
        """Initialize the adaptive chunker."""
        self.logger = get_logger(__name__)
        self.memory_manager = get_memory_manager()
        self.profiler = get_performance_profiler()

        # Adaptive parameters based on system
        self.system_memory_gb = self._detect_system_memory()
        self.cpu_count = os.cpu_count() or 4

        self.logger.info(
            f"AdaptiveChunker initialized: {self.system_memory_gb:.1f}GB RAM, "
            f"{self.cpu_count} CPUs"
        )

    def _detect_system_memory(self) -> float:
        """Detect available system memory."""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            # Fallback estimation
            return 8.0  # Assume 8GB

    @log_function_call
    def create_adaptive_chunks(
        self,
        file_path: Path,
        target_chunk_count: Optional[int] = None,
        max_memory_usage_gb: Optional[float] = None
    ) -> List[FileChunk]:
        """
        Create adaptive chunks for a file based on analysis and system resources.

        Args:
            file_path: Path to the file to chunk
            target_chunk_count: Target number of chunks (None for auto)
            max_memory_usage_gb: Maximum memory to use for chunking

        Returns:
            List of adaptive FileChunk objects
        """
        # Analyze the file
        analysis = self._analyze_file(file_path)

        # Determine chunking parameters
        params = self._calculate_chunking_parameters(
            analysis, target_chunk_count, max_memory_usage_gb
        )

        # Create chunks based on strategy
        with self.profiler.time_operation("adaptive_chunking", PerformanceMetric.CHUNK_TIME):
            if params.strategy == ChunkingStrategy.FORMAT_AWARE:
                chunks = self._create_format_aware_chunks(file_path, analysis, params)
            elif params.strategy == ChunkingStrategy.MEMORY_CONSTRAINED:
                chunks = self._create_memory_constrained_chunks(file_path, analysis, params)
            elif params.strategy == ChunkingStrategy.ADAPTIVE_SIZE:
                chunks = self._create_adaptive_size_chunks(file_path, analysis, params)
            else:  # FIXED_SIZE
                chunks = self._create_fixed_size_chunks(file_path, analysis, params)

        # Validate chunks
        self._validate_chunks(chunks, analysis)

        self.logger.info(
            f"Created {len(chunks)} adaptive chunks for {file_path.name} "
            f"using {params.strategy.value} strategy"
        )

        return chunks

    def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Analyze file to determine format and characteristics.

        Args:
            file_path: Path to the file

        Returns:
            FileAnalysis with format and characteristics
        """
        file_size = file_path.stat().st_size

        # Detect format (simplified - would use existing format detector)
        format_type = self._detect_format(file_path)

        # Estimate triangles based on format
        constants = self.FORMAT_CONSTANTS[format_type]
        estimated_triangles = max(1, file_size // constants["bytes_per_triangle"])

        # Determine recommended strategy
        recommended_strategy = self._determine_optimal_strategy(
            format_type, file_size, estimated_triangles
        )

        return FileAnalysis(
            format=format_type,
            file_size_bytes=file_size,
            estimated_triangles=estimated_triangles,
            format_complexity=constants["complexity"],
            has_variable_structure=constants["variable_structure"],
            recommended_strategy=recommended_strategy
        )

    def _detect_format(self, file_path: Path) -> FileFormat:
        """
        Detect the file format (simplified implementation).

        Args:
            file_path: Path to the file

        Returns:
            Detected FileFormat
        """
        # Read first few bytes to detect format
        with open(file_path, 'rb') as f:
            header = f.read(100)

        # Simple format detection
        header_str = header.decode('utf-8', errors='ignore').lower()

        if header_str.startswith('solid'):
            return FileFormat.STL_ASCII
        elif b'3mf' in header or b'<?xml' in header:
            return FileFormat.THREE_MF
        elif b'ISO-10303-21' in header:
            return FileFormat.STEP
        elif len(header) >= 80 and header[0:5].decode('utf-8', errors='ignore').strip():
            # Likely STL binary (has header text)
            return FileFormat.STL_BINARY
        else:
            # Default to OBJ for text-based files
            return FileFormat.OBJ

    def _determine_optimal_strategy(
        self,
        format_type: FileFormat,
        file_size: int,
        triangle_count: int
    ) -> ChunkingStrategy:
        """
        Determine the optimal chunking strategy based on file characteristics.

        Args:
            format_type: File format
            file_size: File size in bytes
            triangle_count: Estimated triangle count

        Returns:
            Recommended ChunkingStrategy
        """
        file_size_gb = file_size / (1024**3)

        # Memory-constrained systems get smaller chunks
        if self.system_memory_gb < 8:
            return ChunkingStrategy.MEMORY_CONSTRAINED

        # Very large files (>1GB) need careful chunking
        if file_size_gb > 1.0:
            return ChunkingStrategy.ADAPTIVE_SIZE

        # Format-aware for complex or variable formats
        constants = self.FORMAT_CONSTANTS[format_type]
        if constants["variable_structure"] or constants["complexity"] > 0.5:
            return ChunkingStrategy.FORMAT_AWARE

        # Default to adaptive sizing
        return ChunkingStrategy.ADAPTIVE_SIZE

    def _calculate_chunking_parameters(
        self,
        analysis: FileAnalysis,
        target_chunk_count: Optional[int],
        max_memory_usage_gb: Optional[float]
    ) -> ChunkingParameters:
        """
        Calculate optimal chunking parameters.

        Args:
            analysis: File analysis results
            target_chunk_count: Target number of chunks
            max_memory_usage_gb: Maximum memory usage

        Returns:
            ChunkingParameters for the operation
        """
        # Base calculations
        memory_limit = max_memory_usage_gb or (self.system_memory_gb * 0.5)  # Use 50% of RAM
        available_memory_per_chunk = memory_limit / max(target_chunk_count or 4, 1)

        # Adjust for format complexity
        complexity_factor = 1.0 + analysis.format_complexity

        # Calculate base chunk size
        if analysis.recommended_strategy == ChunkingStrategy.MEMORY_CONSTRAINED:
            base_chunk_size_mb = 32  # Small chunks for low memory
        elif analysis.file_size_bytes > 1024**3:  # >1GB
            base_chunk_size_mb = 128  # Larger chunks for big files
        else:
            base_chunk_size_mb = 64  # Default

        # Adjust for available memory
        memory_based_size_mb = available_memory_per_chunk * 1024  # Convert GB to MB
        base_chunk_size_mb = min(base_chunk_size_mb, memory_based_size_mb)

        # Calculate target chunk count
        if target_chunk_count is None:
            estimated_chunk_count = max(1, analysis.file_size_bytes // (base_chunk_size_mb * 1024 * 1024))
            # Limit based on CPU cores
            target_chunk_count = min(estimated_chunk_count, self.cpu_count * 2)

        return ChunkingParameters(
            strategy=analysis.recommended_strategy,
            base_chunk_size_mb=base_chunk_size_mb,
            max_concurrent_chunks=min(target_chunk_count, self.cpu_count),
            format_specific_boundaries=analysis.has_variable_structure,
            memory_adaptive=True,
            performance_target_ms=5000  # 5 second target per chunk
        )

    def _create_format_aware_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create chunks with format-specific boundary alignment.

        Args:
            file_path: File to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of format-aware chunks
        """
        # For format-aware chunking, delegate to specialized chunkers
        if analysis.format == FileFormat.STL_BINARY:
            return self._create_stl_binary_chunks(file_path, analysis, params)
        elif analysis.format == FileFormat.STL_ASCII:
            return self._create_text_based_chunks(file_path, analysis, params)
        else:
            # Generic format-aware chunking
            return self._create_generic_format_chunks(file_path, analysis, params)

    def _create_stl_binary_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create chunks for STL binary files with triangle boundary alignment.

        Args:
            file_path: STL binary file
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of aligned chunks
        """
        chunks = []
        file_size = analysis.file_size_bytes
        triangle_size = 50  # bytes per triangle
        data_start = 84  # Header + triangle count

        # Calculate triangles per chunk
        chunk_size_bytes = int(params.base_chunk_size_mb * 1024 * 1024)
        triangles_per_chunk = chunk_size_bytes // triangle_size
        triangles_per_chunk = max(1, triangles_per_chunk)

        total_chunks = max(1, analysis.estimated_triangles // triangles_per_chunk)

        for i in range(total_chunks):
            start_triangle = i * triangles_per_chunk
            end_triangle = min((i + 1) * triangles_per_chunk, analysis.estimated_triangles)
            chunk_triangles = end_triangle - start_triangle

            start_offset = data_start + (start_triangle * triangle_size)
            chunk_size = chunk_triangles * triangle_size

            # Ensure we don't exceed file size
            if start_offset + chunk_size > file_size:
                chunk_size = file_size - start_offset

            chunk = FileChunk(
                id=f"chunk_{i:03d}",
                file_path=file_path,
                start_offset=start_offset,
                size=chunk_size,
                triangle_start=start_triangle,
                triangle_count=chunk_triangles,
                strategy=ChunkStrategy.PARALLEL
            )
            chunks.append(chunk)

        return chunks

    def _create_text_based_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create chunks for text-based formats (line-aware).

        Args:
            file_path: Text file to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of line-aligned chunks
        """
        # For text files, create chunks at line boundaries
        chunks = []
        chunk_size_bytes = int(params.base_chunk_size_mb * 1024 * 1024)

        with open(file_path, 'rb') as f:
            file_size = f.seek(0, 2)  # Seek to end
            f.seek(0)  # Back to start

            offset = 0
            chunk_index = 0

            while offset < file_size:
                # Find chunk boundary (try to align near target size)
                target_end = min(offset + chunk_size_bytes, file_size)

                # For text files, find nearest line end
                if target_end < file_size:
                    f.seek(target_end)
                    # Read forward to find newline
                    while f.read(1) != b'\n' and f.tell() < file_size:
                        pass
                    actual_end = f.tell()
                else:
                    actual_end = file_size

                chunk_size = actual_end - offset

                # Create chunk (triangle info not applicable for text formats)
                chunk = FileChunk(
                    id=f"chunk_{chunk_index:03d}",
                    file_path=file_path,
                    start_offset=offset,
                    size=chunk_size,
                    triangle_start=0,  # Not applicable
                    triangle_count=0,  # Not applicable
                    strategy=ChunkStrategy.PARALLEL
                )
                chunks.append(chunk)

                offset = actual_end
                chunk_index += 1

        return chunks

    def _create_generic_format_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create generic format-aware chunks.

        Args:
            file_path: File to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of chunks
        """
        # Fallback to adaptive sizing for unknown formats
        return self._create_adaptive_size_chunks(file_path, analysis, params)

    def _create_memory_constrained_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create small chunks for memory-constrained systems.

        Args:
            file_path: File to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of small chunks
        """
        # Use smaller chunk sizes for memory-constrained systems
        small_chunk_size_mb = min(params.base_chunk_size_mb, 16)  # Max 16MB chunks
        return self._create_fixed_size_chunks(
            file_path, analysis,
            params._replace(base_chunk_size_mb=small_chunk_size_mb)
        )

    def _create_adaptive_size_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create chunks with adaptive sizing based on system resources.

        Args:
            file_path: File to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of adaptively-sized chunks
        """
        # Get current memory stats
        memory_stats = self.memory_manager.get_memory_stats()

        # Adjust chunk size based on available memory
        if memory_stats.is_memory_constrained:
            # Reduce chunk size when memory is constrained
            adjusted_size_mb = params.base_chunk_size_mb * 0.5
        elif memory_stats.pressure_level.name == 'LOW':
            # Can use larger chunks when memory is plentiful
            adjusted_size_mb = params.base_chunk_size_mb * 1.5
        else:
            adjusted_size_mb = params.base_chunk_size_mb

        # Ensure reasonable bounds
        adjusted_size_mb = max(8, min(adjusted_size_mb, 256))  # 8MB to 256MB

        return self._create_fixed_size_chunks(
            file_path, analysis,
            params._replace(base_chunk_size_mb=adjusted_size_mb)
        )

    def _create_fixed_size_chunks(
        self,
        file_path: Path,
        analysis: FileAnalysis,
        params: ChunkingParameters
    ) -> List[FileChunk]:
        """
        Create chunks of fixed size.

        Args:
            file_path: File to chunk
            analysis: File analysis
            params: Chunking parameters

        Returns:
            List of fixed-size chunks
        """
        chunks = []
        file_size = analysis.file_size_bytes
        chunk_size_bytes = int(params.base_chunk_size_mb * 1024 * 1024)

        offset = 0
        chunk_index = 0

        while offset < file_size:
            remaining = file_size - offset
            current_chunk_size = min(chunk_size_bytes, remaining)

            chunk = FileChunk(
                id=f"chunk_{chunk_index:03d}",
                file_path=file_path,
                start_offset=offset,
                size=current_chunk_size,
                triangle_start=0,  # Not calculated for fixed size
                triangle_count=0,  # Not calculated for fixed size
                strategy=ChunkStrategy.PARALLEL
            )
            chunks.append(chunk)

            offset += current_chunk_size
            chunk_index += 1

        return chunks

    def _validate_chunks(self, chunks: List[FileChunk], analysis: FileAnalysis) -> None:
        """
        Validate that chunks are properly formed.

        Args:
            chunks: List of chunks to validate
            analysis: Original file analysis

        Raises:
            ValueError: If chunks are invalid
        """
        if not chunks:
            raise ValueError("No chunks created")

        total_size = sum(chunk.size for chunk in chunks)
        if total_size != analysis.file_size_bytes:
            self.logger.warning(
                f"Chunk total size mismatch: {total_size} != {analysis.file_size_bytes}"
            )

        # Check for overlaps or gaps
        sorted_chunks = sorted(chunks, key=lambda c: c.start_offset)
        for i in range(len(sorted_chunks) - 1):
            current_end = sorted_chunks[i].end_offset
            next_start = sorted_chunks[i + 1].start_offset
            if current_end != next_start:
                self.logger.warning(
                    f"Chunk boundary issue: chunk {i} ends at {current_end}, "
                    f"chunk {i+1} starts at {next_start}"
                )

    @log_function_call
    def get_chunking_recommendation(self, file_path: Path) -> Dict[str, Any]:
        """
        Get chunking recommendations for a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with chunking recommendations
        """
        analysis = self._analyze_file(file_path)

        return {
            "file_path": str(file_path),
            "format": analysis.format.value,
            "file_size_mb": analysis.file_size_bytes / (1024 * 1024),
            "estimated_triangles": analysis.estimated_triangles,
            "recommended_strategy": analysis.recommended_strategy.value,
            "format_complexity": analysis.format_complexity,
            "variable_structure": analysis.has_variable_structure,
            "system_memory_gb": self.system_memory_gb,
            "cpu_count": self.cpu_count
        }