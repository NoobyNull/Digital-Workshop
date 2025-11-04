"""
DWW (Digital Wood Works) Import Manager

Handles importing projects from DWW archive format with integrity verification.
"""

import json
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DWWImportManager:
    """Manager for importing projects from DWW format."""

    def __init__(self, db_manager=None):
        """
        Initialize DWW import manager.

        Args:
            db_manager: Optional database manager for storing imported project data
        """
        self.db_manager = db_manager
        self.logger = logger

    def import_project(
        self,
        dww_path: str,
        import_dir: str,
        verify_integrity: bool = True,
        import_thumbnails: bool = True,
        progress_callback=None,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Import a project from DWW format.

        Args:
            dww_path: Path to DWW file to import
            import_dir: Directory where files will be extracted
            verify_integrity: Whether to verify file integrity before import
            import_thumbnails: Whether to extract and import thumbnails
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, message, project_data)
        """
        try:
            dww_file = Path(dww_path)
            if not dww_file.exists():
                return False, f"DWW file not found: {dww_path}", None

            # Verify integrity if requested
            if verify_integrity:
                is_valid, verify_msg = self._verify_dww_file(dww_path)
                if not is_valid:
                    return False, f"Integrity verification failed: {verify_msg}", None

            # Extract DWW archive
            import_path = Path(import_dir)
            import_path.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(dww_file, "r") as dww_archive:
                # Read manifest
                manifest_json = dww_archive.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_json)

                # Extract files
                file_list = dww_archive.namelist()
                file_count = len([f for f in file_list if f.startswith("files/")])
                total_items = file_count

                # Add thumbnails to count if importing them
                if import_thumbnails:
                    total_items += len(
                        [f for f in file_list if f.startswith("thumbnails/")]
                    )

                current_item = 0

                # Extract main files
                for file_info in file_list:
                    if file_info.startswith("files/"):
                        # Extract file
                        extracted_path = import_path / Path(file_info).name
                        with dww_archive.open(file_info) as source:
                            with open(extracted_path, "wb") as target:
                                target.write(source.read())

                        current_item += 1
                        if progress_callback:
                            progress = (
                                current_item / total_items if total_items > 0 else 1.0
                            )
                            progress_callback(
                                progress, f"Imported {current_item}/{total_items} items"
                            )

                # Extract thumbnails if requested
                if import_thumbnails:
                    thumbnails_dir = import_path / "thumbnails"
                    thumbnails_dir.mkdir(exist_ok=True)

                    for file_info in file_list:
                        if file_info.startswith("thumbnails/"):
                            # Extract thumbnail
                            thumb_name = Path(file_info).name
                            extracted_thumb = thumbnails_dir / thumb_name
                            with dww_archive.open(file_info) as source:
                                with open(extracted_thumb, "wb") as target:
                                    target.write(source.read())

                            current_item += 1
                            if progress_callback:
                                progress = (
                                    current_item / total_items
                                    if total_items > 0
                                    else 1.0
                                )
                                progress_callback(
                                    progress,
                                    f"Imported {current_item}/{total_items} items",
                                )

                # Extract metadata if available
                try:
                    metadata_json = dww_archive.read(
                        "metadata/files_metadata.json"
                    ).decode("utf-8")
                    metadata = json.loads(metadata_json)
                    manifest["metadata"] = metadata
                except KeyError:
                    self.logger.debug("No metadata found in DWW file")

            self.logger.info(f"Successfully imported project from DWW: {dww_path}")
            return True, "Project imported successfully", manifest

        except Exception as e:
            error_msg = f"Failed to import project from DWW: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None

    def get_dww_info(self, dww_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        Get information about a DWW file without extracting it.

        Args:
            dww_path: Path to DWW file

        Returns:
            Tuple of (success, manifest_data)
        """
        try:
            with zipfile.ZipFile(dww_path, "r") as dww_archive:
                manifest_json = dww_archive.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_json)
                return True, manifest

        except Exception as e:
            self.logger.error(f"Failed to read DWW info: {str(e)}")
            return False, None

    def _verify_dww_file(self, dww_path: str) -> Tuple[bool, str]:
        """
        Verify integrity of a DWW file.

        Args:
            dww_path: Path to DWW file to verify

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            with zipfile.ZipFile(dww_path, "r") as dww_archive:
                # Read manifest and integrity data
                manifest_json = dww_archive.read("manifest.json").decode("utf-8")
                integrity_json = dww_archive.read("integrity.json").decode("utf-8")

                manifest = json.loads(manifest_json)
                integrity_data = json.loads(integrity_json)

                # Verify hash
                salt = integrity_data.get("salt")
                stored_hash = integrity_data.get("hash")

                combined_data = json.dumps(
                    {
                        "manifest": manifest,
                        "file_hashes": integrity_data.get("file_hashes", {}),
                        "salt": salt,
                    },
                    sort_keys=True,
                )

                calculated_hash = hashlib.sha256(
                    (combined_data + salt).encode()
                ).hexdigest()

                if calculated_hash == stored_hash:
                    return True, "Integrity verified"
                else:
                    return False, "Integrity check failed - file may be corrupted"

        except Exception as e:
            return False, f"Failed to verify DWW file: {str(e)}"

    def list_dww_files(self, dww_path: str) -> Tuple[bool, Optional[list]]:
        """
        List all files in a DWW archive.

        Args:
            dww_path: Path to DWW file

        Returns:
            Tuple of (success, file_list)
        """
        try:
            with zipfile.ZipFile(dww_path, "r") as dww_archive:
                files = [f for f in dww_archive.namelist() if f.startswith("files/")]
                return True, files

        except Exception as e:
            self.logger.error(f"Failed to list DWW files: {str(e)}")
            return False, None
