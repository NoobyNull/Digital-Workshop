"""
File hashing utilities for duplicate detection and file recovery.

Uses xxHash128 for fast, non-cryptographic hashing of model files.
xxHash provides excellent collision resistance and performance for file identification.

This module now wraps the FastHasher class for backward compatibility.
"""

from typing import Optional

from src.core.logging_config import get_logger
from src.core.fast_hasher import FastHasher

logger = get_logger(__name__)

# Global hasher instance for backward compatibility
_global_hasher = FastHasher()


def calculate_file_hash(file_path: str, chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate xxHash128 hash of a file.

    Note: This is a backward-compatible wrapper around FastHasher.
    The chunk_size parameter is ignored in favor of FastHasher's adaptive sizing.

    Args:
        file_path: Path to file
        chunk_size: (Deprecated) Size of chunks to read - now handled by FastHasher

    Returns:
        Hex string of hash (32 characters), or None if calculation fails
    """
    try:
        result = _global_hasher.hash_file(file_path)
        return result.hash_value if result.success else None
    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error("Failed to calculate hash for %s: {e}", file_path)
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
        return _global_hasher.verify_hash(file_path, expected_hash)
    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error("Failed to verify hash: %s", e)
        return False
