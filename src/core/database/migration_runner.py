"""
Migration runner scaffold.

Provides a single entry point for applying schema migrations. This isolates
migration orchestration from db_operations so it can be expanded with
versioned migrations and dry-run support.
"""

from __future__ import annotations

import sqlite3
from typing import Callable

MigrationFunc = Callable[[sqlite3.Cursor], None]


def apply_migrations(cursor: sqlite3.Cursor, migration_fn: MigrationFunc) -> None:
    """Apply migrations using the provided callable."""
    migration_fn(cursor)
