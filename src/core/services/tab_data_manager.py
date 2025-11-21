"""
Tab Data Manager - Handles saving and loading tab data to/from projects.

This module provides utilities for saving data from tabs (Cut List Optimizer,
Feed and Speed, Cost Estimator) as JSON files linked to projects.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TabDataManager:
    """Manager for saving and loading tab data to/from projects."""

    def __init__(self, db_manager=None) -> None:
        """
        Initialize tab data manager.

        Args:
            db_manager: Database manager for project operations
        """
        self.db_manager = db_manager
        self.logger = logger

    def save_tab_data_to_project(
        self,
        project_id: str,
        tab_name: str,
        data: Dict[str, Any],
        filename: str,
        category: str = None,
    ) -> Tuple[bool, str]:
        """
        Save tab data as JSON file and link to project.

        Args:
            project_id: Project UUID
            tab_name: Name of the tab (e.g., "Cut List Optimizer")
            data: Data dictionary to save
            filename: Filename for the JSON file (e.g., "cut_list.json")
            category: Category for file organization (defaults to tab_name)

        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.db_manager:
                return False, "Database manager not initialized"

            # Get project
            project = self.db_manager.get_project(project_id)
            if not project:
                return False, f"Project {project_id} not found"

            project_dir = Path(project["base_path"])

            # Create subdirectory for tab data
            tab_dir = project_dir / tab_name.lower().replace(" ", "_")
            tab_dir.mkdir(parents=True, exist_ok=True)

            # Add timestamp and metadata to data
            data_with_timestamp = {
                **data,
                "saved_at": datetime.now().isoformat(),
                "tab_name": tab_name,
            }
            if category:
                data_with_timestamp["category"] = category

            # Save JSON file
            file_path = tab_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_with_timestamp, f, indent=2)

            self.logger.info("Saved %s data to %s", tab_name, file_path)

            # Link file to project for tracking.
            try:
                try:
                    file_size = file_path.stat().st_size
                except (OSError, IOError):
                    file_size = None

                self.db_manager.add_file(
                    project_id=project_id,
                    file_path=str(file_path),
                    file_name=filename,
                    file_size=file_size,
                    status="imported",
                )
                self.logger.info("Linked %s to project %s", filename, project_id)
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                self.logger.warning("Could not link file to project: %s", e)
                # File was saved successfully, so don't fail

            return True, f"Data saved to {filename}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to save tab data: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def export_tab_data_to_pdf(
        self,
        project_id: str,
        tab_name: str,
        destination: Optional[Path] = None,
        **kwargs: Any,
    ) -> tuple[bool, str]:
        """
        Placeholder export hook to satisfy callers expecting PDF output.

        Currently writes the tab data JSON (if present) next to the requested
        destination with a .json suffix and returns a clear message.
        """
        try:
            success, tab_data, msg = self.load_tab_data_from_project(
                project_id, f"{tab_name.lower().replace(' ', '_')}.json"
            )
            if not success or tab_data is None:
                return False, msg or "No tab data available for export"

            target = destination or Path.cwd() / f"{tab_name}.pdf"
            backup_path = target.with_suffix(".json")
            with open(backup_path, "w", encoding="utf-8") as handle:
                json.dump(tab_data, handle, indent=2)
            return False, "PDF export not implemented; tab data saved as JSON backup"
        except Exception as exc:
            return False, f"Failed to prepare export: {exc}"

    def load_tab_data_from_project(
        self, project_id: str, filename: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Load tab data from project.

        Args:
            project_id: Project UUID
            filename: Filename to load (e.g., "cut_list.json")

        Returns:
            Tuple of (success, data, message)
        """
        try:
            if not self.db_manager:
                return False, None, "Database manager not initialized"

            # Get project
            project = self.db_manager.get_project(project_id)
            if not project:
                return False, None, f"Project {project_id} not found"

            project_dir = Path(project["base_path"])

            # Find file in project
            file_path = None
            for root, _, files in os.walk(project_dir):
                if filename in files:
                    file_path = Path(root) / filename
                    break

            if not file_path or not file_path.exists():
                return False, None, f"File {filename} not found in project"

            # Load JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.logger.info("Loaded %s from %s", filename, file_path)
            return True, data, f"Data loaded from {filename}"

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {filename}: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to load tab data: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, None, error_msg

    def get_tab_data_file_path(self, project_id: str, filename: str) -> Optional[Path]:
        """
        Get the full path to a tab data file.

        Args:
            project_id: Project UUID
            filename: Filename to find

        Returns:
            Path to file or None if not found
        """
        try:
            if not self.db_manager:
                return None

            project = self.db_manager.get_project(project_id)
            if not project:
                return None

            project_dir = Path(project["base_path"])

            # Find file in project
            for root, _, files in os.walk(project_dir):
                if filename in files:
                    return Path(root) / filename

            return None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting file path: %s", e)
            return None

    def list_tab_data_files(
        self, project_id: str, tab_name: str = None
    ) -> Tuple[bool, list, str]:
        """
        List all tab data files in a project.

        Args:
            project_id: Project UUID
            tab_name: Optional tab name to filter by

        Returns:
            Tuple of (success, files_list, message)
        """
        try:
            if not self.db_manager:
                return False, [], "Database manager not initialized"

            project = self.db_manager.get_project(project_id)
            if not project:
                return False, [], f"Project {project_id} not found"

            project_dir = Path(project["base_path"])
            files = []

            # Find all JSON files
            for root, _, filenames in os.walk(project_dir):
                for filename in filenames:
                    if filename.endswith(".json"):
                        file_path = Path(root) / filename

                        # Filter by tab name if provided
                        if tab_name:
                            if (
                                tab_name.lower().replace(" ", "_")
                                not in str(file_path).lower()
                            ):
                                continue

                        files.append(
                            {
                                "filename": filename,
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "modified": datetime.fromtimestamp(
                                    file_path.stat().st_mtime
                                ).isoformat(),
                            }
                        )

            return True, files, f"Found {len(files)} tab data files"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to list tab data files: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, [], error_msg

    def delete_tab_data_file(self, project_id: str, filename: str) -> Tuple[bool, str]:
        """
        Delete a tab data file from project.

        Args:
            project_id: Project UUID
            filename: Filename to delete

        Returns:
            Tuple of (success, message)
        """
        try:
            file_path = self.get_tab_data_file_path(project_id, filename)
            if not file_path:
                return False, f"File {filename} not found"

            file_path.unlink()
            self.logger.info("Deleted %s", filename)
            return True, f"Deleted {filename}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to delete tab data file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
