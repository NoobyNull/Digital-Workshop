"""PJCT (Project File) Export Manager

Handles exporting projects to PJCT archive format with JSON metadata and integrity verification.
PJCT files are ZIP archives containing:
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
from src.core.services.file_type_registry import get_tree_category_for_extension

logger = get_logger(__name__)


class PJCTExportManager:
    """Manager for exporting projects to PJCT format."""

    # PJCT format version
    PJCT_VERSION = "1.0"

    # Salt length for hash verification (32 bytes = 256 bits)
    SALT_LENGTH = 32

    def __init__(self, db_manager=None) -> None:
        """
        Initialize PJCT export manager.

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
        Export a project to PJCT format.

        Args:
            project_id: ID of the project to export
            output_path: Path where PJCT file will be saved
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

            # Create PJCT archive
            with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as pjct_archive:
                # Create manifest
                manifest = self._create_manifest(project, files)
                manifest_json = json.dumps(manifest, indent=2)
                pjct_archive.writestr("manifest.json", manifest_json)

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
                        pjct_archive.write(file_path, arcname=arcname)

                        # Add thumbnail if available
                        if include_thumbnails:
                            thumbnail_path = file_info.get("thumbnail_path")
                            if thumbnail_path and Path(thumbnail_path).exists():
                                try:
                                    thumb_arcname = f"thumbnails/{file_name}.thumb.png"
                                    pjct_archive.write(thumbnail_path, arcname=thumb_arcname)
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
                        self.logger.error("Failed to add file to archive %s: %s", file_path, e)
                        continue

                # Add metadata if requested
                if include_metadata:
                    self._add_metadata_to_archive(pjct_archive, project_id, files)

                # Create integrity verification
                integrity_data = self._create_integrity_data(manifest, file_hashes)
                integrity_json = json.dumps(integrity_data, indent=2)
                pjct_archive.writestr("integrity.json", integrity_json)

            self.logger.info("Successfully exported project to PJCT: %s", output_path)
            return True, f"Project exported successfully to {output_file.name}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to export project to PJCT: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _add_metadata_to_archive(
        self, archive: zipfile.ZipFile, project_id: str, files: List[Dict]
    ) -> None:
        """Add metadata files to the archive.

        This includes both per-file metadata and a compact summary section
        describing the state of the main hero tabs. The additional hero tab
        summary is intentionally lightweight and derived only from filenames
        and extensions so that export remains robust even when some files are
        missing on disk.
        """
        try:
            # Create metadata directory structure
            metadata: Dict[str, object] = {
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

            # Write per-file metadata to archive
            metadata_json = json.dumps(metadata, indent=2)
            archive.writestr("metadata/files_metadata.json", metadata_json)

            # Build and write hero tab summary metadata
            try:
                hero_tabs = self._build_hero_tabs_metadata(project_id, files)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
                self.logger.warning("Failed to build hero tab metadata: %s", exc)
            else:
                try:
                    hero_tabs_json = json.dumps(hero_tabs, indent=2)
                    archive.writestr("metadata/hero_tabs.json", hero_tabs_json)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    self.logger.warning("Failed to add hero tab metadata to archive: %s", exc)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to add metadata to archive: %s", e)

    def _build_hero_tabs_metadata(self, project_id: str, files: List[Dict]) -> Dict:
        """Build summary metadata for the main hero tabs.

        The goal here is not to duplicate the full tab JSON payloads (those
        are already exported as regular project files via TabDataManager) but
        to provide a compact, easy-to-inspect summary that callers can use to
        quickly understand which parts of the project are populated.
        """
        model_files: List[str] = []
        gcode_files: List[str] = []
        has_cut_list = False
        has_feeds_and_speeds = False
        has_cost_estimate = False
        has_model_view = False
        has_gcode_timing = False

        for file_info in files:
            file_name = file_info.get("file_name") or ""
            file_path = file_info.get("file_path") or ""

            if not file_name and file_path:
                file_name = Path(file_path).name

            ext = Path(file_name).suffix.lower()
            tree_category = None
            if ext:
                try:
                    tree_category = get_tree_category_for_extension(ext)
                except Exception:
                    tree_category = None

            if tree_category == "Models":
                if file_name not in model_files:
                    model_files.append(file_name)
            elif tree_category == "Gcode":
                if file_name not in gcode_files:
                    gcode_files.append(file_name)

            lower_name = file_name.lower()
            if lower_name == "cut_list.json":
                has_cut_list = True
            elif lower_name == "feeds_and_speeds.json":
                has_feeds_and_speeds = True
            elif lower_name == "cost_estimate.json":
                has_cost_estimate = True
            elif lower_name == "model_view.json":
                has_model_view = True
            elif lower_name == "gcode_timing.json":
                has_gcode_timing = True

        return {
            "project_id": project_id,
            "model_previewer": {
                "model_files": model_files,
                "has_view_state": has_model_view,
            },
            "gcode_previewer": {
                "gcode_files": gcode_files,
                "has_timing_data": has_gcode_timing,
            },
            "cut_list_optimizer": {
                "has_tab_data": has_cut_list,
                "filename": "cut_list.json" if has_cut_list else None,
            },
            "feeds_and_speeds": {
                "has_tab_data": has_feeds_and_speeds,
                "filename": "feeds_and_speeds.json" if has_feeds_and_speeds else None,
            },
            "project_cost_estimator": {
                "has_tab_data": has_cost_estimate,
                "filename": "cost_estimate.json" if has_cost_estimate else None,
            },
        }

    def _create_manifest(self, project: Dict, files: List[Dict]) -> Dict:
        """Create project manifest."""
        return {
            "version": self.PJCT_VERSION,
            "format": "PJCT",
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
            "version": self.PJCT_VERSION,
            "salt": salt,
            "hash": salted_hash,
            "algorithm": "SHA256",
            "file_hashes": file_hashes,
        }

    def verify_pjct_file(self, pjct_path: str) -> Tuple[bool, str]:
        """Verify integrity of a PJCT file.

        Args:
            pjct_path: Path to PJCT file to verify

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            with zipfile.ZipFile(pjct_path, "r") as pjct_archive:
                # Read manifest and integrity data
                manifest_json = pjct_archive.read("manifest.json").decode("utf-8")
                integrity_json = pjct_archive.read("integrity.json").decode("utf-8")

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
                    return True, "PJCT file integrity verified successfully"

                return (
                    False,
                    "PJCT file integrity check failed - file may be corrupted",
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to verify PJCT file: {str(e)}"
