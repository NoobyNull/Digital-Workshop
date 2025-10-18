"""
File hashing utilities for duplicate detection and file recovery.

Uses xxHash128 for fast, non-cryptographic hashing of model files.
xxHash provides excellent collision resistance and performance for file identification.
"""

import xxhash
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)


def calculate_file_hash(file_path: str, chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate xxHash128 hash of a file.

    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (default 8KB for memory efficiency)

    Returns:
        Hex string of hash (32 characters), or None if calculation fails
    """
    try:
        hasher = xxhash.xxh128()
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found for hashing: {file_path}")
            return None

        with path.open('rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)

        hash_value = hasher.hexdigest()
        logger.debug(f"Calculated hash for {path.name}: {hash_value[:16]}...")
        return hash_value

    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return None


def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Verify file hash matches expected value.

    Args:
        file_path: Path to file
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = calculate_file_hash(file_path)
        return actual_hash == expected_hash if actual_hash else False
    except Exception as e:
        logger.error(f"Failed to verify hash: {e}")
        return False
