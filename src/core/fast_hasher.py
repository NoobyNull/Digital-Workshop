"""
Fast non-cryptographic hashing system for 3D model import process.

Uses xxHash128 for optimal performance in:
- Fast duplicate detection during import
- Hash-based thumbnail naming
- File identification in the database

Performance targets:
- Files under 100MB: hash in < 1 second
- Files 100-500MB: hash in < 3 seconds
- Files over 500MB: hash in < 5 seconds
"""

import xxhash
import json
import time
from pathlib import Path
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass

from src.core.logging_config import get_logger
from src.core.cancellation_token import CancellationToken


@dataclass
class HashResult:
    """Result of a file hashing operation."""

    file_path: str
    hash_value: Optional[str]
    file_size: int
    hash_time: float
    success: bool
    error: Optional[str] = None


class FastHasher:
    """
    Fast non-cryptographic file hasher using xxHash128.

    Designed for optimal performance with 3D model files, providing:
    - Stream-based hashing to minimize memory usage
    - Progress callbacks for long operations
    - Cancellation support for user control
    - Adaptive chunk sizing based on file size
    - Comprehensive JSON logging

    Performance characteristics:
    - xxHash128 is 10-20x faster than MD5
    - Stream-based processing uses constant memory
    - Minimal overhead for progress reporting
    - Efficient for files of all sizes
    """

    # Adaptive chunk sizes based on file size for optimal performance
    CHUNK_SIZE_SMALL = 64 * 1024  # 64KB for files < 10MB
    CHUNK_SIZE_MEDIUM = 256 * 1024  # 256KB for files 10-100MB
    CHUNK_SIZE_LARGE = 1024 * 1024  # 1MB for files > 100MB

    # File size thresholds in bytes
    SMALL_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
    MEDIUM_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        """Initialize the fast hasher with logging."""
        self.logger = get_logger(__name__)
        self._log_json(
            "hasher_initialized",
            {
                "algorithm": "xxHash128",
                "chunk_sizes": {
                    "small": self.CHUNK_SIZE_SMALL,
                    "medium": self.CHUNK_SIZE_MEDIUM,
                    "large": self.CHUNK_SIZE_LARGE,
                },
            },
        )

    def _log_json(self, event: str, data: dict) -> None:
        """Log event in JSON format as required by quality standards."""
        log_entry = {"event": event, "timestamp": time.time(), **data}
        self.logger.debug(json.dumps(log_entry))

    def _get_optimal_chunk_size(self, file_size: int) -> int:
        """
        Determine optimal chunk size based on file size.

        Args:
            file_size: Size of file in bytes

        Returns:
            Optimal chunk size in bytes
        """
        if file_size < self.SMALL_FILE_THRESHOLD:
            return self.CHUNK_SIZE_SMALL
        elif file_size < self.MEDIUM_FILE_THRESHOLD:
            return self.CHUNK_SIZE_MEDIUM
        else:
            return self.CHUNK_SIZE_LARGE

    def hash_file(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> HashResult:
        """
        Calculate xxHash128 hash of a file with progress reporting and cancellation support.

        Args:
            file_path: Path to file to hash
            progress_callback: Optional callback(progress_percent, message)
            cancellation_token: Optional token to check for cancellation

        Returns:
            HashResult with hash value and metadata

        Example:
            >>> hasher = FastHasher()
            >>> result = hasher.hash_file("model.stl", lambda p, m: print(f"{p}% - {m}"))
            >>> if result.success:
            ...     print(f"Hash: {result.hash_value}")
        """
        start_time = time.time()
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.warning(error_msg)
            return HashResult(
                file_path=file_path,
                hash_value=None,
                file_size=0,
                hash_time=0.0,
                success=False,
                error=error_msg,
            )

        try:
            file_size = path.stat().st_size
            chunk_size = self._get_optimal_chunk_size(file_size)

            self._log_json(
                "hash_started",
                {
                    "file": path.name,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "chunk_size": chunk_size,
                },
            )

            # Initialize xxHash128
            hasher = xxhash.xxh128()
            bytes_processed = 0
            last_progress_report = 0.0

            # Report initial progress
            if progress_callback:
                progress_callback(0.0, f"Starting hash: {path.name}")

            # Stream file in chunks
            with path.open("rb") as f:
                while True:
                    # Check for cancellation
                    if cancellation_token and cancellation_token.is_cancelled():
                        self._log_json(
                            "hash_cancelled",
                            {
                                "file": path.name,
                                "bytes_processed": bytes_processed,
                                "percent_complete": round((bytes_processed / file_size) * 100, 1),
                            },
                        )
                        return HashResult(
                            file_path=file_path,
                            hash_value=None,
                            file_size=file_size,
                            hash_time=time.time() - start_time,
                            success=False,
                            error="Operation cancelled",
                        )

                    # Read chunk
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # Update hash
                    hasher.update(chunk)
                    bytes_processed += len(chunk)

                    # Report progress (every 5% to avoid overhead)
                    if progress_callback and file_size > 0:
                        current_progress = (bytes_processed / file_size) * 100
                        if current_progress - last_progress_report >= 5.0:
                            progress_callback(
                                current_progress,
                                f"Hashing {path.name}: {round(current_progress)}%",
                            )
                            last_progress_report = current_progress

            # Finalize hash
            hash_value = hasher.hexdigest()
            hash_time = time.time() - start_time

            # Report completion
            if progress_callback:
                progress_callback(100.0, f"Hash complete: {path.name}")

            self._log_json(
                "hash_completed",
                {
                    "file": path.name,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "hash": hash_value[:16] + "...",  # Log first 16 chars only
                    "time_seconds": round(hash_time, 3),
                    "throughput_mbps": (
                        round((file_size / (1024 * 1024)) / hash_time, 2) if hash_time > 0 else 0
                    ),
                },
            )

            return HashResult(
                file_path=file_path,
                hash_value=hash_value,
                file_size=file_size,
                hash_time=hash_time,
                success=True,
            )

        except PermissionError as e:
            error_msg = f"Permission denied: {file_path}"
            self.logger.error("%s: {e}", error_msg)
            return HashResult(
                file_path=file_path,
                hash_value=None,
                file_size=0,
                hash_time=time.time() - start_time,
                success=False,
                error=error_msg,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to hash file: {e}"
            self.logger.error("Error hashing %s: {e}", file_path, exc_info=True)
            return HashResult(
                file_path=file_path,
                hash_value=None,
                file_size=0,
                hash_time=time.time() - start_time,
                success=False,
                error=error_msg,
            )

    def hash_chunk(self, data: bytes, hasher: Optional[xxhash.xxh128] = None) -> xxhash.xxh128:
        """
        Hash a chunk of data, optionally continuing from previous hasher state.

        Useful for streaming scenarios where data comes in chunks.

        Args:
            data: Bytes to hash
            hasher: Optional existing hasher to continue from

        Returns:
            xxhash hasher object (can be reused for additional chunks)

        Example:
            >>> hasher = FastHasher()
            >>> h = hasher.hash_chunk(b"chunk1")
            >>> h = hasher.hash_chunk(b"chunk2", h)
            >>> final_hash = h.hexdigest()
        """
        if hasher is None:
            hasher = xxhash.xxh128()

        hasher.update(data)
        return hasher

    def hash_files_batch(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> List[HashResult]:
        """
        Hash multiple files with batch progress reporting.

        Args:
            file_paths: List of file paths to hash
            progress_callback: Optional callback(completed, total, current_file)
            cancellation_token: Optional token to check for cancellation

        Returns:
            List of HashResult objects for each file

        Example:
            >>> hasher = FastHasher()
            >>> files = ["model1.stl", "model2.stl", "model3.stl"]
            >>> results = hasher.hash_files_batch(files, lambda c, t, f: print(f"{c}/{t}: {f}"))
        """
        start_time = time.time()
        results = []
        total_files = len(file_paths)

        self._log_json(
            "batch_hash_started",
            {"total_files": total_files, "files": [Path(p).name for p in file_paths]},
        )

        for idx, file_path in enumerate(file_paths):
            # Check for cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                self._log_json(
                    "batch_hash_cancelled",
                    {
                        "completed": idx,
                        "total": total_files,
                        "percent_complete": round((idx / total_files) * 100, 1),
                    },
                )
                break

            # Report batch progress
            if progress_callback:
                progress_callback(idx, total_files, Path(file_path).name)

            # Hash individual file
            result = self.hash_file(file_path, cancellation_token=cancellation_token)
            results.append(result)

        # Final progress report
        if progress_callback:
            progress_callback(len(results), total_files, "Batch complete")

        batch_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)

        self._log_json(
            "batch_hash_completed",
            {
                "total_files": total_files,
                "successful": successful,
                "failed": total_files - successful,
                "time_seconds": round(batch_time, 3),
                "avg_time_per_file": (round(batch_time / total_files, 3) if total_files > 0 else 0),
            },
        )

        return results

    def verify_hash(
        self,
        file_path: str,
        expected_hash: str,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> bool:
        """
        Verify file hash matches expected value.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            cancellation_token: Optional token to check for cancellation

        Returns:
            True if hash matches, False otherwise
        """
        result = self.hash_file(file_path, cancellation_token=cancellation_token)

        if not result.success:
            return False

        matches = result.hash_value == expected_hash

        self._log_json(
            "hash_verification",
            {
                "file": Path(file_path).name,
                "matches": matches,
                "expected": expected_hash[:16] + "...",
                "actual": result.hash_value[:16] + "..." if result.hash_value else None,
            },
        )

        return matches

    def get_performance_stats(self, results: List[HashResult]) -> Dict[str, any]:
        """
        Calculate performance statistics from hash results.

        Args:
            results: List of HashResult objects

        Returns:
            Dictionary with performance metrics
        """
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {
                "total_files": len(results),
                "successful": 0,
                "failed": len(results),
                "total_size_mb": 0,
                "total_time_seconds": 0,
                "avg_throughput_mbps": 0,
            }

        total_size = sum(r.file_size for r in successful_results)
        total_time = sum(r.hash_time for r in successful_results)

        stats = {
            "total_files": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_time_seconds": round(total_time, 3),
            "avg_time_per_file": round(total_time / len(successful_results), 3),
            "avg_throughput_mbps": (
                round((total_size / (1024 * 1024)) / total_time, 2) if total_time > 0 else 0
            ),
            "min_time": round(min(r.hash_time for r in successful_results), 3),
            "max_time": round(max(r.hash_time for r in successful_results), 3),
        }

        self._log_json("performance_stats", stats)
        return stats
