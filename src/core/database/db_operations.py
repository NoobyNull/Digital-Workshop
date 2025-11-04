"""
Database operations module for connection management and schema initialization.

Handles SQLite connection creation, configuration, and database schema setup.
"""

import sqlite3
from pathlib import Path

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class DatabaseOperations:
    """Handles database connection and schema operations."""

    def __init__(self, db_path: str):
        """
        Initialize database operations.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @log_function_call(logger)
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper settings.

        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0,  # 30 second timeout
            )

            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Set WAL mode for better performance
            conn.execute("PRAGMA journal_mode = WAL")

            # Optimize for performance
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")

            return conn

        except sqlite3.Error as e:
            logger.error(f"Failed to create database connection: {str(e)}")
            raise

    @log_function_call(logger)
    def initialize_schema(self) -> None:
        """
        Initialize the database with the required schema.

        Creates tables for models, model_metadata, and categories if they don't exist.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create models table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        format TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash TEXT,
                        thumbnail_path TEXT,
                        date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create model_metadata table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS model_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id INTEGER REFERENCES models(id),
                        title TEXT,
                        description TEXT,
                        keywords TEXT,
                        category TEXT,
                        source TEXT,
                        rating INTEGER CHECK(rating >= 0 AND rating <= 5),
                        view_count INTEGER DEFAULT 0,
                        last_viewed DATETIME DEFAULT CURRENT_TIMESTAMP,
                        camera_position_x REAL,
                        camera_position_y REAL,
                        camera_position_z REAL,
                        camera_focal_x REAL,
                        camera_focal_y REAL,
                        camera_focal_z REAL,
                        camera_view_up_x REAL,
                        camera_view_up_y REAL,
                        camera_view_up_z REAL,
                        UNIQUE(model_id)
                    )
                """
                )

                # Create categories table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        color TEXT,
                        icon TEXT,
                        sort_order INTEGER DEFAULT 0
                    )
                """
                )

                # Create projects table for project management
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
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create files table for file tracking
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

                # Create indexes
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_filename ON models(filename)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_format ON models(format)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_file_hash ON models(file_hash)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_models_thumbnail_path ON models(thumbnail_path)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_metadata_category ON model_metadata(category)"
                )

                # Create indexes for projects and files
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_import_tag ON projects(import_tag)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)"
                )

                # Run migrations
                self.migrate_schema(cursor)

                # Seed default categories
                default_categories = [
                    ("Characters", "Character models", "#FF6B6B", 0),
                    ("Buildings", "Architecture and structures", "#4ECDC4", 1),
                    ("Vehicles", "Cars, planes, ships", "#45B7D1", 2),
                    ("Nature", "Plants, animals, landscapes", "#96CEB4", 3),
                    ("Objects", "Miscellaneous objects", "#FFEAA7", 4),
                ]

                for name, desc, color, sort_order in default_categories:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO categories (name, description, color, sort_order)
                        VALUES (?, ?, ?, ?)
                    """,
                        (name, desc, color, sort_order),
                    )

                conn.commit()
                logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {str(e)}")
            raise

    @log_function_call(logger)
    def migrate_schema(self, cursor: sqlite3.Cursor) -> None:
        """
        Migrate database schema to newer versions if needed.

        Args:
            cursor: SQLite cursor object
        """
        try:
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
            has_thumbnail_path = any(
                col[1] == "thumbnail_path" for col in model_columns
            )

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
                cursor.execute(
                    "ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0"
                )
                logger.info("sort_order column added successfully")

            # Migration 4: Add linked_model_id for deduplication tracking
            has_linked_model_id = any(
                col[1] == "linked_model_id" for col in model_columns
            )

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
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_projects_import_tag ON projects(import_tag)"
                )
                logger.info("projects table created successfully")

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
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_files_file_hash ON files(file_hash)"
                )
                logger.info("files table created successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to migrate database schema: {str(e)}")
            raise
