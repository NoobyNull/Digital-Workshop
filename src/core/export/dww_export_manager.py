"""
DWW (Digital Wood Works) Export Manager

Handles exporting projects to DWW archive format with JSON metadata and integrity verification.
DWW files are ZIP archives containing:
- manifest.json: Project metadata and file listing
- files/: Directory containing all project files
- integrity.json: Hash verification data
"""

import json
import hashlib
import secrets
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DWWExportManager:
    """Manager for exporting projects to DWW format."""

    # DWW format version
    DWW_VERSION = "1.0"

    # Salt length for hash verification (32 bytes = 256 bits)
    SALT_LENGTH = 32

    def __init__(self, db_manager=None) -> None:
        """
        Initialize DWW export manager.

        Args:
            db_manager: Optional database manager for retrieving project data
        """
        self.db_manager = db_manager
        self.logger = logger

    def export_project(
        self,
        project_id: str,
        output_path: str,
        include_metadata: bool = True,
        include_thumbnails: bool = True,
        include_renderings: bool = True,
        progress_callback=None,
    ) -> Tuple[bool, str]:
        """
        Export a project to DWW format.

        Args:
            project_id: ID of the project to export
            output_path: Path where DWW file will be saved
            include_metadata: Whether to include project metadata
            include_thumbnails: Whether to include model thumbnails
            include_renderings: Whether to include rendered images
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, message)
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Get project data from database
            if not self.db_manager:
                return False, "Database manager not available"

            project = self.db_manager.get_project(project_id)
            if not project:
                return False, f"Project not found: {project_id}"

            files = self.db_manager.get_files_by_project(project_id)
            if not files:
                return False, "Project has no files to export"

            # Create DWW archive
            with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as dww_archive:
                # Create manifest
                manifest = self._create_manifest(project, files)
                manifest_json = json.dumps(manifest, indent=2)
                dww_archive.writestr("manifest.json", manifest_json)

                # Add project files
                file_hashes = {}
                total_items = len(files)

                for i, file_info in enumerate(files):
                    file_path = file_info.get("file_path")
                    if not file_path or not Path(file_path).exists():
                        self.logger.warning("File not found: %s", file_path)
                        continue

                    try:
                        # Calculate file hash
                        file_hash = self._calculate_file_hash(file_path)
                        file_name = file_info.get("file_name", Path(file_path).name)
                        file_hashes[file_name] = file_hash

                        # Add file to archive
                        arcname = f"files/{file_name}"
                        dww_archive.write(file_path, arcname=arcname)

                        # Add thumbnail if available
                        if include_thumbnails:
                            thumbnail_path = file_info.get("thumbnail_path")
                            if thumbnail_path and Path(thumbnail_path).exists():
                                try:
                                    thumb_arcname = f"thumbnails/{file_name}.thumb.png"
                                    dww_archive.write(thumbnail_path, arcname=thumb_arcname)
                                except (
                                    OSError,
                                    IOError,
                                    ValueError,
                                    TypeError,
                                    KeyError,
                                    AttributeError,
                                ) as e:
                                    self.logger.debug("Failed to add thumbnail: %s", e)

                        if progress_callback:
                            progress = (i + 1) / total_items
                            progress_callback(progress, f"Exported {i + 1}/{total_items} files")

                    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                        self.logger.error("Failed to add file to archive: %s: {e}", file_path)
                        continue

                # Add metadata if requested
                if include_metadata:
                    self._add_metadata_to_archive(dww_archive, project_id, files)

                # Create integrity verification
                integrity_data = self._create_integrity_data(manifest, file_hashes)
                integrity_json = json.dumps(integrity_data, indent=2)
                dww_archive.writestr("integrity.json", integrity_json)

            self.logger.info("Successfully exported project to DWW: %s", output_path)
            return True, f"Project exported successfully to {output_file.name}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to export project to DWW: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _add_metadata_to_archive(
        self, dww_archive: zipfile.ZipFile, project_id: str, files: List[Dict]
    ) -> None:
        """Add metadata files to the archive."""
        try:
            # Create metadata directory structure
            metadata = {
                "project_id": project_id,
                "export_date": datetime.now().isoformat(),
                "files_metadata": [],
            }

            # Collect metadata for each file
            for file_info in files:
                file_metadata = {
                    "file_name": file_info.get("file_name"),
                    "file_path": file_info.get("file_path"),
                    "file_size": file_info.get("file_size"),
                    "file_hash": file_info.get("file_hash"),
                    "thumbnail_path": file_info.get("thumbnail_path"),
                    "created_at": file_info.get("created_at"),
                    "updated_at": file_info.get("updated_at"),
                }
                metadata["files_metadata"].append(file_metadata)

            # Write metadata to archive
            metadata_json = json.dumps(metadata, indent=2)
            dww_archive.writestr("metadata/files_metadata.json", metadata_json)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to add metadata to archive: %s", e)

    def _create_manifest(self, project: Dict, files: List[Dict]) -> Dict:
        """Create project manifest."""
        return {
            "version": self.DWW_VERSION,
            "format": "Digital Wood Works",
            "created_at": datetime.now().isoformat(),
            "project": {
                "id": project.get("id"),
                "name": project.get("name"),
                "description": project.get("description", ""),
                "created_at": project.get("created_at"),
                "updated_at": project.get("updated_at"),
            },
            "files": [
                {
                    "name": f.get("file_name"),
                    "path": f.get("file_path"),
                    "size": (
                        Path(f.get("file_path")).stat().st_size
                        if Path(f.get("file_path")).exists()
                        else 0
                    ),
                    "type": (Path(f.get("file_path")).suffix.lower() if f.get("file_path") else ""),
                    "thumbnail": f.get("thumbnail_path") is not None,
                }
                for f in files
                if f.get("file_path") and Path(f.get("file_path")).exists()
            ],
            "file_count": len(
                [f for f in files if f.get("file_path") and Path(f.get("file_path")).exists()]
            ),
        }

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _create_integrity_data(self, manifest: Dict, file_hashes: Dict) -> Dict:
        """Create integrity verification data with salted hash."""
        # Generate random salt
        salt = secrets.token_hex(self.SALT_LENGTH)

        # Create combined data for hashing
        combined_data = json.dumps(
            {
                "manifest": manifest,
                "file_hashes": file_hashes,
                "salt": salt,
            },
            sort_keys=True,
        )

        # Calculate salted hash
        salted_hash = hashlib.sha256((combined_data + salt).encode()).hexdigest()

        return {
            "version": self.DWW_VERSION,
            "salt": salt,
            "hash": salted_hash,
            "algorithm": "SHA256",
            "file_hashes": file_hashes,
        }

    def verify_dww_file(self, dww_path: str) -> Tuple[bool, str]:
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

                calculated_hash = hashlib.sha256((combined_data + salt).encode()).hexdigest()

                if calculated_hash == stored_hash:
                    return True, "DWW file integrity verified successfully"
                else:
                    return (
                        False,
                        "DWW file integrity check failed - file may be corrupted",
                    )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to verify DWW file: {str(e)}"
