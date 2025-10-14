"""
SQLite database manager for 3D-MM application.

This module provides database operations for managing 3D models, metadata,
and categories with proper error handling and logging integration.
"""

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .logging_config import get_logger, log_function_call

# Initialize logger
logger = get_logger(__name__)


class DatabaseManager:
    """
    Database manager for 3D-MM application.
    
    Handles all SQLite database operations including schema creation,
    CRUD operations, and connection management with proper logging.
    """
    
    def __init__(self, db_path: str = "data/3dmm.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
        self._lock = threading.Lock()
        
        logger.info(f"Initializing database manager with path: {self.db_path}")
        
        # Initialize database schema
        self._initialize_database()
    
    @log_function_call(logger)
    def _initialize_database(self) -> None:
        """
        Initialize the database with the required schema.
        
        Creates tables for models, model_metadata, and categories if they don't exist.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create models table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        format TEXT NOT NULL,           -- 'stl', 'mf3', 'obj', 'step'
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create model_metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id INTEGER REFERENCES models(id),
                        title TEXT,                     -- Custom model name
                        description TEXT,               -- User description
                        keywords TEXT,                  -- Comma-separated keywords
                        category TEXT,                  -- Category like "Characters", "Buildings"
                        source TEXT,                    -- Where model came from
                        rating INTEGER CHECK(rating >= 0 AND rating <= 5),
                        view_count INTEGER DEFAULT 0,
                        last_viewed DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(model_id)
                    )
                """)
                
                # Create categories table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        color TEXT DEFAULT '#CCCCCC',
                        sort_order INTEGER DEFAULT 0
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_filename ON models(filename)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_format ON models(format)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_metadata_model_id ON model_metadata(model_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_metadata_category ON model_metadata(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)")
                
                # Insert default categories if they don't exist
                self._insert_default_categories(cursor)
                
                # Migrate database schema if needed
                self._migrate_database_schema(cursor)
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {str(e)}")
            raise
    
    @log_function_call(logger)
    def _insert_default_categories(self, cursor: sqlite3.Cursor) -> None:
        """
        Insert default categories into the database.
        
        Args:
            cursor: SQLite cursor object
        """
        default_categories = [
            ("Characters", "#FF6B6B", 1),
            ("Buildings", "#4ECDC4", 2),
            ("Vehicles", "#45B7D1", 3),
            ("Nature", "#96CEB4", 4),
            ("Objects", "#FECA57", 5),
            ("Abstract", "#DDA0DD", 6),
            ("Other", "#CCCCCC", 7)
        ]
        
        for name, color, sort_order in default_categories:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, color, sort_order) VALUES (?, ?, ?)",
                    (name, color, sort_order)
                )
            except sqlite3.Error as e:
                logger.warning(f"Failed to insert default category '{name}': {str(e)}")
    
    @log_function_call(logger)
    def _migrate_database_schema(self, cursor: sqlite3.Cursor) -> None:
        """
        Migrate database schema to newer versions if needed.
        
        Args:
            cursor: SQLite cursor object
        """
        try:
            # Check if we need to migrate the rating constraint
            cursor.execute("PRAGMA table_info(model_metadata)")
            columns = cursor.fetchall()
            
            # Find the rating column definition
            rating_column = None
            for column in columns:
                if column[1] == 'rating':  # column[1] is the column name
                    rating_column = column
                    break
            
            if rating_column:
                # Check if the constraint needs updating (old version had CHECK(rating >= 1 AND rating <= 5))
                # SQLite doesn't support altering column constraints directly, so we need to recreate the table
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='model_metadata'")
                table_sql = cursor.fetchone()[0]
                
                if "CHECK(rating >= 1 AND rating <= 5)" in table_sql:
                    logger.info("Migrating database schema to allow rating = 0")
                    
                    # Create backup table
                    cursor.execute("ALTER TABLE model_metadata RENAME TO model_metadata_old")
                    
                    # Create new table with updated constraint
                    cursor.execute("""
                        CREATE TABLE model_metadata (
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
                            UNIQUE(model_id)
                        )
                    """)
                    
                    # Copy data from old table
                    cursor.execute("""
                        INSERT INTO model_metadata (
                            id, model_id, title, description, keywords, category,
                            source, rating, view_count, last_viewed
                        )
                        SELECT id, model_id, title, description, keywords, category,
                               source,
                               CASE WHEN rating < 0 THEN 0 ELSE rating END,
                               view_count, last_viewed
                        FROM model_metadata_old
                    """)
                    
                    # Drop old table
                    cursor.execute("DROP TABLE model_metadata_old")
                    
                    # Recreate indexes
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_metadata_model_id ON model_metadata(model_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_metadata_category ON model_metadata(category)")
                    
                    logger.info("Database schema migration completed successfully")
                    
        except sqlite3.Error as e:
            logger.warning(f"Database schema migration failed: {str(e)}")
    
    @log_function_call(logger)
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper settings.
        
        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0  # 30 second timeout
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
    
    # Models table operations
    
    @log_function_call(logger)
    def add_model(self, filename: str, format: str, file_path: str, 
                  file_size: Optional[int] = None) -> int:
        """
        Add a new model to the database.
        
        Args:
            filename: Model filename
            format: Model format ('stl', 'mf3', 'obj', 'step')
            file_path: Full path to the model file
            file_size: File size in bytes
            
        Returns:
            ID of the inserted model
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO models (filename, format, file_path, file_size, last_modified)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (filename, format, file_path, file_size))
                
                model_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added model '{filename}' with ID: {model_id}")
                return model_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add model '{filename}': {str(e)}")
            raise
    
    @log_function_call(logger)
    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        Get model information by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model information dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE m.id = ?
                """, (model_id,))
                
                row = cursor.fetchone()
                if row:
                    model = dict(row)
                    logger.debug(f"Retrieved model with ID: {model_id}")
                    return model
                
                logger.warning(f"Model with ID {model_id} not found")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get model {model_id}: {str(e)}")
            raise
    
    @log_function_call(logger)
    def get_all_models(self, limit: Optional[int] = None, 
                       offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all models from the database.
        
        Args:
            limit: Maximum number of models to return
            offset: Number of models to skip
            
        Returns:
            List of model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    ORDER BY m.date_added DESC
                """
                
                params = []
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                models = [dict(row) for row in rows]
                logger.debug(f"Retrieved {len(models)} models")
                return models
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get all models: {str(e)}")
            raise
    
    @log_function_call(logger)
    def update_model(self, model_id: int, **kwargs) -> bool:
        """
        Update model information.
        
        Args:
            model_id: Model ID
            **kwargs: Fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not kwargs:
            logger.warning("No fields provided for update")
            return False
        
        # Filter valid fields for models table
        valid_fields = {'filename', 'format', 'file_path', 'file_size'}
        model_updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not model_updates:
            logger.warning("No valid model fields provided for update")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Add last_modified timestamp
                model_updates['last_modified'] = 'CURRENT_TIMESTAMP'
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in model_updates.keys()])
                values = list(model_updates.values())
                values.append(model_id)
                
                cursor.execute(f"""
                    UPDATE models 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"Updated model {model_id}: {list(model_updates.keys())}")
                else:
                    logger.warning(f"Model {model_id} not found for update")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update model {model_id}: {str(e)}")
            raise
    
    @log_function_call(logger)
    def delete_model(self, model_id: int) -> bool:
        """
        Delete a model from the database.
        
        Args:
            model_id: Model ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First delete associated metadata to avoid foreign key constraint
                cursor.execute("DELETE FROM model_metadata WHERE model_id = ?", (model_id,))
                
                # Then delete the model
                cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"Deleted model with ID: {model_id}")
                else:
                    logger.warning(f"Model with ID {model_id} not found for deletion")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete model {model_id}: {str(e)}")
            raise
    
    # Model metadata operations
    
    @log_function_call(logger)
    def add_model_metadata(self, model_id: int, title: Optional[str] = None,
                          description: Optional[str] = None, keywords: Optional[str] = None,
                          category: Optional[str] = None, source: Optional[str] = None,
                          rating: Optional[int] = None) -> int:
        """
        Add metadata for a model.
        
        Args:
            model_id: Model ID
            title: Custom model name
            description: User description
            keywords: Comma-separated keywords
            category: Category name
            source: Where model came from
            rating: Rating from 1-5
            
        Returns:
            ID of the inserted metadata
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO model_metadata 
                    (model_id, title, description, keywords, category, source, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model_id, title, description, keywords, category, source, rating))
                
                metadata_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added metadata for model {model_id} with ID: {metadata_id}")
                return metadata_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add metadata for model {model_id}: {str(e)}")
            raise
    
    @log_function_call(logger)
    def update_model_metadata(self, model_id: int, **kwargs) -> bool:
        """
        Update model metadata.
        
        Args:
            model_id: Model ID
            **kwargs: Fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not kwargs:
            logger.warning("No fields provided for metadata update")
            return False
        
        # Filter valid fields for model_metadata table
        valid_fields = {'title', 'description', 'keywords', 'category', 'source', 'rating'}
        metadata_updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not metadata_updates:
            logger.warning("No valid metadata fields provided for update")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in metadata_updates.keys()])
                values = list(metadata_updates.values())
                values.append(model_id)
                
                cursor.execute(f"""
                    UPDATE model_metadata 
                    SET {set_clause}
                    WHERE model_id = ?
                """, values)
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"Updated metadata for model {model_id}: {list(metadata_updates.keys())}")
                else:
                    logger.warning(f"Metadata for model {model_id} not found for update")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update metadata for model {model_id}: {str(e)}")
            raise
    
    @log_function_call(logger)
    def increment_view_count(self, model_id: int) -> bool:
        """
        Increment the view count for a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE model_metadata 
                    SET view_count = view_count + 1, last_viewed = CURRENT_TIMESTAMP
                    WHERE model_id = ?
                """, (model_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.debug(f"Incremented view count for model {model_id}")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to increment view count for model {model_id}: {str(e)}")
            raise
    
    # Categories operations
    
    @log_function_call(logger)
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories from the database.
        
        Returns:
            List of category dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM categories 
                    ORDER BY sort_order ASC, name ASC
                """)
                
                rows = cursor.fetchall()
                categories = [dict(row) for row in rows]
                
                logger.debug(f"Retrieved {len(categories)} categories")
                return categories
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {str(e)}")
            raise
    
    @log_function_call(logger)
    def add_category(self, name: str, color: str = "#CCCCCC", 
                     sort_order: int = 0) -> int:
        """
        Add a new category.
        
        Args:
            name: Category name
            color: Category color hex code
            sort_order: Sort order for display
            
        Returns:
            ID of the inserted category
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO categories (name, color, sort_order)
                    VALUES (?, ?, ?)
                """, (name, color, sort_order))
                
                category_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added category '{name}' with ID: {category_id}")
                return category_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add category '{name}': {str(e)}")
            raise
    
    @log_function_call(logger)
    def update_category(self, category_id: int, **kwargs) -> bool:
        """
        Update a category.
        
        Args:
            category_id: Category ID
            **kwargs: Fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not kwargs:
            logger.warning("No fields provided for category update")
            return False
        
        # Filter valid fields for categories table
        valid_fields = {'name', 'color', 'sort_order'}
        category_updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not category_updates:
            logger.warning("No valid category fields provided for update")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in category_updates.keys()])
                values = list(category_updates.values())
                values.append(category_id)
                
                cursor.execute(f"""
                    UPDATE categories 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"Updated category {category_id}: {list(category_updates.keys())}")
                else:
                    logger.warning(f"Category {category_id} not found for update")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to update category {category_id}: {str(e)}")
            raise
    
    @log_function_call(logger)
    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: Category ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"Deleted category with ID: {category_id}")
                else:
                    logger.warning(f"Category with ID {category_id} not found for deletion")
                
                return success
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete category {category_id}: {str(e)}")
            raise
    
    # Search operations
    
    @log_function_call(logger)
    def search_models(self, query: str, category: Optional[str] = None,
                      format: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for models based on query and filters.
        
        Args:
            query: Search query string
            category: Filter by category
            format: Filter by model format
            limit: Maximum number of results
            
        Returns:
            List of matching model dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build search query
                search_query = """
                    SELECT m.*, mm.title, mm.description, mm.keywords, mm.category,
                           mm.source, mm.rating, mm.view_count, mm.last_viewed
                    FROM models m
                    LEFT JOIN model_metadata mm ON m.id = mm.model_id
                    WHERE 1=1
                """
                
                params = []
                
                # Add text search condition
                if query:
                    search_query += """
                        AND (m.filename LIKE ? 
                             OR mm.title LIKE ? 
                             OR mm.description LIKE ? 
                             OR mm.keywords LIKE ?)
                    """
                    search_term = f"%{query}%"
                    params.extend([search_term, search_term, search_term, search_term])
                
                # Add category filter
                if category:
                    search_query += " AND mm.category = ?"
                    params.append(category)
                
                # Add format filter
                if format:
                    search_query += " AND m.format = ?"
                    params.append(format)
                
                # Add ordering and limit
                search_query += " ORDER BY mm.last_viewed DESC"
                
                if limit:
                    search_query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(search_query, params)
                rows = cursor.fetchall()
                
                models = [dict(row) for row in rows]
                logger.debug(f"Search for '{query}' returned {len(models)} results")
                return models
                
        except sqlite3.Error as e:
            logger.error(f"Failed to search models: {str(e)}")
            raise
    
    # Statistics operations
    
    @log_function_call(logger)
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get model count
                cursor.execute("SELECT COUNT(*) FROM models")
                model_count = cursor.fetchone()[0]
                
                # Get category counts
                cursor.execute("""
                    SELECT mm.category, COUNT(*) as count
                    FROM model_metadata mm
                    WHERE mm.category IS NOT NULL
                    GROUP BY mm.category
                    ORDER BY count DESC
                """)
                category_counts = dict(cursor.fetchall())
                
                # Get format counts
                cursor.execute("""
                    SELECT format, COUNT(*) as count
                    FROM models
                    GROUP BY format
                    ORDER BY count DESC
                """)
                format_counts = dict(cursor.fetchall())
                
                # Get total file size
                cursor.execute("SELECT SUM(file_size) FROM models WHERE file_size IS NOT NULL")
                total_size = cursor.fetchone()[0] or 0
                
                stats = {
                    "model_count": model_count,
                    "category_counts": category_counts,
                    "format_counts": format_counts,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
                
                logger.debug(f"Retrieved database stats: {stats}")
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            raise
    
    # Database maintenance operations
    
    @log_function_call(logger)
    def vacuum_database(self) -> None:
        """
        Vacuum the database to reclaim unused space.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuum completed successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {str(e)}")
            raise
    
    @log_function_call(logger)
    def analyze_database(self) -> None:
        """
        Analyze the database to update query planner statistics.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("ANALYZE")
                logger.info("Database analysis completed successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to analyze database: {str(e)}")
            raise
    
    @log_function_call(logger)
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")


# Singleton instance for application-wide use
_database_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_database_manager(db_path: str = "data/3dmm.db") -> DatabaseManager:
    """
    Get the singleton database manager instance.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        DatabaseManager instance
    """
    global _database_manager
    
    with _db_lock:
        if _database_manager is None:
            _database_manager = DatabaseManager(db_path)
        
        return _database_manager


def close_database_manager() -> None:
    """
    Close the database manager instance.
    """
    global _database_manager
    
    with _db_lock:
        if _database_manager:
            _database_manager.close()
            _database_manager = None