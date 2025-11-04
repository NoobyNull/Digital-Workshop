"""
Thread pool coordinator for multi-threaded STL parsing.

This module coordinates worker threads for parsing STL file chunks,
managing ProcessPoolExecutor instances and aggregating results.
"""

import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable
from enum import Enum

from src.core.logging_config import get_logger, log_function_call
from src.parsers.file_chunker import FileChunk
from src.parsers.base_parser import Model, Triangle, Vector3D, ModelStats, ModelFormat
from src.core.cancellation_token import CancellationToken


class WorkerState(Enum):
    """States for worker threads."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkerResult:
    """Result from a worker thread."""

    chunk_id: str
    triangles: List[Triangle]
    processing_time: float
    error: Optional[Exception] = None


class ThreadPoolCoordinator:
    """
    Coordinates multi-threaded parsing of STL file chunks.

    This class manages ProcessPoolExecutor instances, distributes chunks
    to worker processes, and aggregates results from parallel parsing.
    """

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """
        Initialize the thread pool coordinator.

        Args:
            max_workers: Maximum number of worker processes (default: CPU count)
        """
        self.logger = get_logger(__name__)
        self.max_workers = max_workers
        self._lock = threading.RLock()

    @log_function_call
    def coordinate_parsing(
        self,
        chunks: List[FileChunk],
        cancellation_token: CancellationToken,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Model:
        """
        Coordinate parsing of file chunks using a thread pool.

        Args:
            chunks: List of file chunks to process
            cancellation_token: Token for cancellation support
            progress_callback: Callback for progress updates

        Returns:
            Complete parsed model

        Raises:
            Exception: If parsing fails or is cancelled
        """
        if not chunks:
            raise ValueError("No chunks provided for parsing")

        start_time = time.time()
        self.logger.info("Starting coordinated parsing of %s chunks", len(chunks))

        # Submit all chunks to the thread pool
        futures = {}
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            for chunk in chunks:
                if cancellation_token.is_cancelled():
                    self.logger.info("Parsing cancelled before submitting all chunks")
                    break

                future = executor.submit(self._process_chunk_worker, chunk, cancellation_token)
                futures[future] = chunk

            # Collect results as they complete
            results = []
            completed_count = 0

            try:
                for future in as_completed(futures):
                    if cancellation_token.is_cancelled():
                        self.logger.info("Parsing cancelled during result collection")
                        break

                    chunk = futures[future]
                    try:
                        result = future.result(timeout=30)  # 30 second timeout per chunk
                        results.append(result)
                        completed_count += 1

                        # Update progress
                        if progress_callback:
                            progress = (completed_count / len(chunks)) * 100
                            progress_callback(
                                progress,
                                f"Processed chunk {completed_count}/{len(chunks)}",
                            )

                        self.logger.debug(
                            f"Completed chunk {chunk.id}: {result.processing_time:.2f}s"
                        )

                    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                        self.logger.error("Failed to process chunk %s: {e}", chunk.id)
                        # Continue with other chunks but mark this as failed
                        error_result = WorkerResult(
                            chunk_id=chunk.id,
                            triangles=[],
                            processing_time=0.0,
                            error=e,
                        )
                        results.append(error_result)

            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Error during result collection: %s", e)
                raise

        # Check for cancellation
        if cancellation_token.is_cancelled():
            raise Exception("Parsing was cancelled by user")

        # Aggregate results
        return self._aggregate_results(chunks[0].file_path, results, start_time)

    @staticmethod
    def _process_chunk_worker(
        chunk: FileChunk, cancellation_token: CancellationToken
    ) -> WorkerResult:
        """
        Worker function to process a single chunk.

        This runs in a separate process.

        Args:
            chunk: The file chunk to process
            cancellation_token: Cancellation token

        Returns:
            WorkerResult with parsed triangles
        """
        start_time = time.time()

        try:
            # Direct chunk processing - no parser instance needed

            # Process the chunk
            triangles = ThreadPoolCoordinator._parse_chunk_data_static(chunk, cancellation_token)

            processing_time = time.time() - start_time

            return WorkerResult(
                chunk_id=chunk.id, triangles=triangles, processing_time=processing_time
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            processing_time = time.time() - start_time
            # Note: Can't log here as logger is not serializable
            return WorkerResult(
                chunk_id=chunk.id,
                triangles=[],
                processing_time=processing_time,
                error=e,
            )

    @staticmethod
    def _parse_chunk_data_static(
        chunk: FileChunk, cancellation_token: CancellationToken
    ) -> List[Triangle]:
        """
        Parse triangle data from a file chunk.

        Args:
            chunk: The file chunk to parse
            cancellation_token: Cancellation token

        Returns:
            List of parsed triangles
        """
        triangles = []

        try:
            with open(chunk.file_path, "rb") as file:
                # Seek to chunk start
                file.seek(chunk.start_offset)

                # Read chunk data
                data = file.read(chunk.size)
                if len(data) != chunk.size:
                    raise ValueError(
                        f"Incomplete chunk read: expected {chunk.size}, got {len(data)}"
                    )

                # Parse triangles from the data
                triangles = ThreadPoolCoordinator._parse_triangle_data_static(
                    data, chunk.triangle_count, cancellation_token
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            # Can't log here as logger is not serializable
            raise

        return triangles

    @staticmethod
    def _parse_triangle_data_static(
        data: bytes, expected_count: int, cancellation_token: CancellationToken
    ) -> List[Triangle]:
        """
        Parse triangle data from raw bytes.

        Args:
            data: Raw triangle data bytes
            expected_count: Expected number of triangles
            cancellation_token: Cancellation token

        Returns:
            List of parsed triangles
        """
        import struct
        from src.parsers.base_parser import Triangle, Vector3D

        triangles = []
        TRIANGLE_SIZE = 50  # bytes per triangle

        if len(data) % TRIANGLE_SIZE != 0:
            raise ValueError(f"Invalid triangle data size: {len(data)} bytes")

        actual_count = len(data) // TRIANGLE_SIZE
        if actual_count != expected_count:
            # Can't log here as logger is not serializable
            pass

        for i in range(actual_count):
            if cancellation_token.is_cancelled():
                break

            offset = i * TRIANGLE_SIZE

            # Unpack triangle data (little-endian)
            # Format: 3 floats (normal) + 9 floats (3 vertices) + 1 uint16 (attribute)
            try:
                values = struct.unpack("<12fH", data[offset : offset + TRIANGLE_SIZE])

                normal = Vector3D(values[0], values[1], values[2])
                v1 = Vector3D(values[3], values[4], values[5])
                v2 = Vector3D(values[6], values[7], values[8])
                v3 = Vector3D(values[9], values[10], values[11])
                attribute = values[12]

                triangle = Triangle(normal, v1, v2, v3, attribute)
                triangles.append(triangle)

            except struct.error as e:
                raise ValueError(f"Failed to unpack triangle {i}: {e}")

        return triangles

    def _aggregate_results(
        self, file_path: Path, results: List[WorkerResult], start_time: float
    ) -> Model:
        """
        Aggregate results from all worker threads.

        Args:
            file_path: Original file path
            results: List of worker results
            start_time: Overall parsing start time

        Returns:
            Complete parsed model
        """
        # Collect all triangles in order
        all_triangles = []
        total_processing_time = 0.0
        errors = []

        # Sort results by chunk ID to maintain triangle order
        results.sort(key=lambda r: r.chunk_id)

        for result in results:
            if result.error:
                errors.append(f"Chunk {result.chunk_id}: {result.error}")
            else:
                all_triangles.extend(result.triangles)
                total_processing_time += result.processing_time

        # Check for errors
        if errors:
            error_msg = f"Parsing failed with {len(errors)} errors: {'; '.join(errors)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Calculate bounds
        if all_triangles:
            min_x = min_y = min_z = float("inf")
            max_x = max_y = max_z = float("-inf")

            for triangle in all_triangles:
                for vertex in triangle.get_vertices():
                    min_x = min(min_x, vertex.x)
                    min_y = min(min_y, vertex.y)
                    min_z = min(min_z, vertex.z)
                    max_x = max(max_x, vertex.x)
                    max_y = max(max_y, vertex.y)
                    max_z = max(max_z, vertex.z)

            min_bounds = Vector3D(min_x, min_y, min_z)
            max_bounds = Vector3D(max_x, max_y, max_z)
        else:
            min_bounds = Vector3D(0, 0, 0)
            max_bounds = Vector3D(0, 0, 0)

        # Create model statistics
        file_size = file_path.stat().st_size
        parsing_time = time.time() - start_time

        stats = ModelStats(
            vertex_count=len(all_triangles) * 3,
            triangle_count=len(all_triangles),
            min_bounds=min_bounds,
            max_bounds=max_bounds,
            file_size_bytes=file_size,
            format_type=ModelFormat.STL,
            parsing_time_seconds=parsing_time,
        )

        # Create model
        model = Model(
            header=f"Multi-threaded STL: {file_path.name}",
            triangles=all_triangles,
            stats=stats,
            format_type=ModelFormat.STL,
        )

        self.logger.info(
            f"Successfully aggregated {len(results)} chunks: "
            f"{len(all_triangles)} triangles in {parsing_time:.2f}s"
        )

        return model
