"""
Database schema migrations.

Contains the existing migration logic extracted from db_operations for clarity.
"""

from __future__ import annotations

import sqlite3

from ..logging_config import get_logger

logger = get_logger(__name__)


def migrate_schema(cursor: sqlite3.Cursor) -> None:
    """Migrate database schema to newer versions if needed."""
    # Migration 1: Add file_hash column if it doesn't exist
    cursor.execute("PRAGMA table_info(models)")
    model_columns = cursor.fetchall()
    has_file_hash = any(col[1] == "file_hash" for col in model_columns)

    if not has_file_hash:
        logger.info("Adding file_hash column to models table")
        cursor.execute("ALTER TABLE models ADD COLUMN file_hash TEXT")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_file_hash ON models(file_hash)"
        )
        logger.info("file_hash column added successfully")

    # Migration 2: Add thumbnail_path column if it doesn't exist
    has_thumbnail_path = any(col[1] == "thumbnail_path" for col in model_columns)

    if not has_thumbnail_path:
        logger.info("Adding thumbnail_path column to models table")
        cursor.execute("ALTER TABLE models ADD COLUMN thumbnail_path TEXT")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_thumbnail_path ON models(thumbnail_path)"
        )
        logger.info("thumbnail_path column added successfully")

    # Migration 3: Add missing columns to categories table
    cursor.execute("PRAGMA table_info(categories)")
    category_columns = cursor.fetchall()
    category_col_names = [col[1] for col in category_columns]

    if "description" not in category_col_names:
        logger.info("Adding description column to categories table")
        cursor.execute("ALTER TABLE categories ADD COLUMN description TEXT")
        logger.info("description column added successfully")

    if "sort_order" not in category_col_names:
        logger.info("Adding sort_order column to categories table")
        cursor.execute("ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0")
        logger.info("sort_order column added successfully")

    # Migration 4: Add linked_model_id for deduplication tracking
    has_linked_model_id = any(col[1] == "linked_model_id" for col in model_columns)

    if not has_linked_model_id:
        logger.info("Adding linked_model_id column to models table")
        cursor.execute(
            "ALTER TABLE models ADD COLUMN linked_model_id INTEGER REFERENCES models(id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_models_linked_model_id ON models(linked_model_id)"
        )
        logger.info("linked_model_id column added successfully")

    # Migration 5: Ensure projects table exists (for project management)
    cursor.execute("PRAGMA table_info(projects)")
    projects_columns = cursor.fetchall()

    if not projects_columns:
        logger.info("Creating projects table")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                base_path TEXT,
                import_tag TEXT,
                original_path TEXT,
                structure_type TEXT,
                import_date DATETIME,
                active_machine_id INTEGER,
                feed_override_pct REAL DEFAULT 100.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_projects_import_tag ON projects(import_tag)"
        )
        logger.info("projects table created successfully")

        # Refresh project columns after potential creation
        cursor.execute("PRAGMA table_info(projects)")
        projects_columns = cursor.fetchall()

    project_col_names = [col[1] for col in projects_columns]

    if "active_machine_id" not in project_col_names:
        logger.info("Adding active_machine_id column to projects table")
        cursor.execute("ALTER TABLE projects ADD COLUMN active_machine_id INTEGER")
        logger.info("active_machine_id column added successfully")

    if "feed_override_pct" not in project_col_names:
        logger.info("Adding feed_override_pct column to projects table")
        cursor.execute(
            "ALTER TABLE projects ADD COLUMN feed_override_pct REAL DEFAULT 100.0"
        )
        logger.info("feed_override_pct column added successfully")

    if "material_name" not in project_col_names:
        logger.info("Adding material_name column to projects table")
        cursor.execute("ALTER TABLE projects ADD COLUMN material_name TEXT")
        logger.info("material_name column added successfully")

    if "material_tag" not in project_col_names:
        logger.info("Adding material_tag column to projects table")
        cursor.execute("ALTER TABLE projects ADD COLUMN material_tag TEXT")
        logger.info("material_tag column added successfully")

    # Migration 6: Ensure files table exists (for file tracking)
    cursor.execute("PRAGMA table_info(files)")
    files_columns = cursor.fetchall()

    if not files_columns:
        logger.info("Creating files table")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                status TEXT DEFAULT 'pending',
                link_type TEXT,
                original_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)"
        )
        logger.info("files table created successfully")

        # Refresh files columns after potential creation
        cursor.execute("PRAGMA table_info(files)")
        files_columns = cursor.fetchall()

    files_col_names = [col[1] for col in files_columns]

    if "link_type" not in files_col_names:
        logger.info("Adding link_type column to files table")
        cursor.execute("ALTER TABLE files ADD COLUMN link_type TEXT")
        logger.info("link_type column added successfully")

    if "original_path" not in files_col_names:
        logger.info("Adding original_path column to files table")
        cursor.execute("ALTER TABLE files ADD COLUMN original_path TEXT")
        logger.info("original_path column added successfully")

    # Migration 7: Add feed_override_pct to gcode_metrics if missing
    cursor.execute("PRAGMA table_info(gcode_metrics)")
    metrics_columns = cursor.fetchall()
    metrics_col_names = [col[1] for col in metrics_columns]
    if metrics_columns:
        if "feed_override_pct" not in metrics_col_names:
            logger.info("Adding feed_override_pct column to gcode_metrics table")
            cursor.execute(
                "ALTER TABLE gcode_metrics ADD COLUMN feed_override_pct REAL"
            )

    # Migration 8: Add spindle capability columns to machines
    cursor.execute("PRAGMA table_info(machines)")
    machine_columns = cursor.fetchall()
    machine_col_names = [col[1] for col in machine_columns]
    if machine_columns:
        if "max_spindle_rpm" not in machine_col_names:
            logger.info("Adding max_spindle_rpm column to machines table")
            cursor.execute("ALTER TABLE machines ADD COLUMN max_spindle_rpm REAL")
        if "max_bit_diameter_mm" not in machine_col_names:
            logger.info("Adding max_bit_diameter_mm column to machines table")
            cursor.execute("ALTER TABLE machines ADD COLUMN max_bit_diameter_mm REAL")
        if "spindle_power_w" not in machine_col_names:
            logger.info("Adding spindle_power_w column to machines table")
            cursor.execute("ALTER TABLE machines ADD COLUMN spindle_power_w REAL")
        if "drive_type" not in machine_col_names:
            logger.info("Adding drive_type column to machines table")
            cursor.execute(
                "ALTER TABLE machines ADD COLUMN drive_type TEXT DEFAULT 'ball_screw'"
            )
