"""
SQLite connection factory.

Creates a configured sqlite3 connection with the same pragmas used across the app.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def create_connection(db_path: Path) -> sqlite3.Connection:
    """Create a configured SQLite connection."""
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        timeout=30.0,  # 30 second timeout
    )

    # Return rows as dictionary-like objects for convenient access
    conn.row_factory = sqlite3.Row

    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Set WAL mode for better performance
    conn.execute("PRAGMA journal_mode = WAL")

    # Optimize for performance
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 10000")
    conn.execute("PRAGMA temp_store = MEMORY")

    return conn
