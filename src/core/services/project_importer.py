"""
Project Importer for executing library imports with tagging and reporting.

Handles the actual import process including file linking/copying, database updates,
and import reporting.
"""

import os
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from .file_type_filter import FileTypeFilter
from ..database.database_manager import DatabaseManager
from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class ImportReport:
    """Report of import operation."""

    project_id: str
    project_name: str
    import_date: str
    total_files_processed: int
    files_imported: int
    files_failed: int
    files_blocked: int
    total_size_bytes: int
    import_duration_seconds: float
    errors: List[str]
    success: bool


class ProjectImporter:
    """Executes library import with tagging and reporting."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize project importer.

        Args:
            db_manager: DatabaseManager instance
        """
        self.logger = logger
        self.db_manager = db_manager
        self.file_filter = FileTypeFilter()

    @log_function_call(logger)
    def import_project(
        self,
        folder_path: str,
        project_name: str,
        structure_type: str = "nested",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ImportReport:
        """
        Import a project from folder.

        Args:
            folder_path: Path to folder to import
            project_name: Name for the project
            structure_type: Type of structure (flat, nested, balanced)
            progress_callback: Optional callback for progress (current, total)

        Returns:
            ImportReport with import results
        """
        start_time = datetime.now()
        errors = []
        files_imported = 0
        files_failed = 0
        files_blocked = 0
        total_size = 0

        try:
            folder_path = str(Path(folder_path).resolve())

            if not os.path.isdir(folder_path):
                raise ValueError(f"Folder not found: {folder_path}")

            # Create project
            try:
                project_id = self.db_manager.create_project(
                    name=project_name,
                    base_path=folder_path,
                    import_tag="imported_project",
                    original_path=folder_path,
                    structure_type=structure_type,
                )
                logger.info(f"Created project: {project_name} ({project_id})")
            except ValueError as e:
                raise ValueError(f"Failed to create project: {str(e)}")

            # Collect all files
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

            total_files = len(all_files)

            # Process files
            for idx, file_path in enumerate(all_files):
                if progress_callback:
                    progress_callback(idx + 1, total_files)

                try:
                    # Filter file
                    filter_result = self.file_filter.filter_file(file_path)

                    if not filter_result.is_allowed:
                        files_blocked += 1
                        logger.debug(
                            f"Blocked file: {file_path} ({filter_result.reason})"
                        )
                        continue

                    # Get file info
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size

                    # Add file to database
                    file_id = self.db_manager.add_file(
                        project_id=project_id,
                        file_path=file_path,
                        file_name=file_name,
                        file_size=file_size,
                        status="imported",
                        link_type="original",
                        original_path=file_path,
                    )

                    files_imported += 1
                    logger.debug(f"Imported file: {file_name}")

                except Exception as e:
                    files_failed += 1
                    error_msg = f"Failed to import {file_path}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Create report
            report = ImportReport(
                project_id=project_id,
                project_name=project_name,
                import_date=datetime.now().isoformat(),
                total_files_processed=total_files,
                files_imported=files_imported,
                files_failed=files_failed,
                files_blocked=files_blocked,
                total_size_bytes=total_size,
                import_duration_seconds=duration,
                errors=errors,
                success=files_imported > 0 and files_failed == 0,
            )

            logger.info(
                f"Import complete: {project_name} ({files_imported} files, {duration:.1f}s)"
            )
            return report

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            error_msg = f"Import failed: {str(e)}"
            errors.append(error_msg)

            duration = (datetime.now() - start_time).total_seconds()
            return ImportReport(
                project_id="",
                project_name=project_name,
                import_date=datetime.now().isoformat(),
                total_files_processed=0,
                files_imported=0,
                files_failed=0,
                files_blocked=0,
                total_size_bytes=0,
                import_duration_seconds=duration,
                errors=errors,
                success=False,
            )

    def get_import_summary(self, report: ImportReport) -> str:
        """Get human-readable import summary."""
        summary = f"""
Import Summary: {report.project_name}
{'=' * 50}
Date: {report.import_date}
Duration: {report.import_duration_seconds:.1f} seconds
Total Files: {report.total_files_processed}
  - Imported: {report.files_imported}
  - Blocked: {report.files_blocked}
  - Failed: {report.files_failed}
Total Size: {report.total_size_bytes / (1024*1024):.2f} MB
Status: {'✓ Success' if report.success else '✗ Failed'}
"""
        if report.errors:
            summary += f"\nErrors ({len(report.errors)}):\n"
            for error in report.errors[:5]:  # Show first 5 errors
                summary += f"  - {error}\n"
            if len(report.errors) > 5:
                summary += f"  ... and {len(report.errors) - 5} more errors\n"

        return summary
