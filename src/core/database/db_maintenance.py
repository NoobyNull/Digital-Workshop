"""
Database maintenance module for statistics and maintenance operations.

Handles database statistics, vacuum, analysis, and cleanup operations.
"""

import sqlite3
from typing import Any, Dict

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


class DatabaseMaintenance:
    """Handles database maintenance and statistics operations."""

    def __init__(self, get_connection_func):
        """
        Initialize database maintenance.

        Args:
            get_connection_func: Function to get database connection
        """
        self._get_connection = get_connection_func

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
                cursor.execute(
                    """
                    SELECT mm.category, COUNT(*) as count
                    FROM model_metadata mm
                    WHERE mm.category IS NOT NULL
                    GROUP BY mm.category
                    ORDER BY count DESC
                """
                )
                category_counts = dict(cursor.fetchall())

                # Get format counts
                cursor.execute(
                    """
                    SELECT format, COUNT(*) as count
                    FROM models
                    GROUP BY format
                    ORDER BY count DESC
                """
                )
                format_counts = dict(cursor.fetchall())

                # Get total file size
                cursor.execute("SELECT SUM(file_size) FROM models WHERE file_size IS NOT NULL")
                total_size = cursor.fetchone()[0] or 0

                stats = {
                    "model_count": model_count,
                    "category_counts": category_counts,
                    "format_counts": format_counts,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                }

                logger.debug("Retrieved database stats: %s", stats)
                return stats

        except sqlite3.Error as e:
            logger.error("Failed to get database stats: %s", str(e))
            raise

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
            logger.error("Failed to vacuum database: %s", str(e))
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
            logger.error("Failed to analyze database: %s", str(e))
            raise
