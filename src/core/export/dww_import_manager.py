"""
PJCT (Project File) Import Manager

Handles importing projects from PJCT archive format with integrity verification.
"""

import json
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class PJCTImportManager:
    """Manager for importing projects from PJCT format."""

    def __init__(self, db_manager=None) -> None:
        """
        Initialize PJCT import manager.

        Args:
            db_manager: Optional database manager for storing imported project data
        """
        self.db_manager = db_manager
        self.logger = logger

    def import_project(
        self,
        pjct_path: str,
        import_dir: str,
        verify_integrity: bool = True,
        import_thumbnails: bool = True,
        progress_callback=None,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Import a project from PJCT format.

        Args:
            pjct_path: Path to PJCT file to import
            import_dir: Directory where files will be extracted
            verify_integrity: Whether to verify file integrity before import
            import_thumbnails: Whether to extract and import thumbnails
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, message, project_data)
        """
        try:
            pjct_file = Path(pjct_path)
            if not pjct_file.exists():
                return False, f"PJCT file not found: {pjct_path}", None

            # Verify integrity if requested
            if verify_integrity:
                is_valid, verify_msg = self._verify_pjct_file(pjct_path)
                if not is_valid:
                    return False, f"Integrity verification failed: {verify_msg}", None

            # Extract PJCT archive
            import_path = Path(import_dir)
            import_path.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(pjct_file, "r") as pjct_archive:
                # Read manifest
                manifest_json = pjct_archive.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_json)

                # Extract files
                file_list = pjct_archive.namelist()
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
                        with pjct_archive.open(file_info) as source:
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
                            with pjct_archive.open(file_info) as source:
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
                    metadata_json = pjct_archive.read(
                        "metadata/files_metadata.json"
                    ).decode("utf-8")
                    metadata = json.loads(metadata_json)
                    manifest["metadata"] = metadata
                except KeyError:
                    self.logger.debug("No metadata found in PJCT file")

                # Extract hero tab metadata if available
                try:
                    hero_json = pjct_archive.read("metadata/hero_tabs.json").decode(
                        "utf-8"
                    )
                    hero_tabs = json.loads(hero_json)
                    manifest["hero_tabs"] = hero_tabs
                except KeyError:
                    self.logger.debug("No hero tab metadata found in PJCT file")
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    self.logger.warning("Invalid hero tab metadata in PJCT file: %s", e)

            self.logger.info("Successfully imported project from PJCT: %s", pjct_path)
            return True, "Project imported successfully", manifest

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Failed to import project from PJCT: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None

    def get_pjct_info(self, pjct_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        Get information about a PJCT file without extracting it.

        Args:
            pjct_path: Path to PJCT file

        Returns:
            Tuple of (success, manifest_data)
        """
        try:
            with zipfile.ZipFile(pjct_path, "r") as pjct_archive:
                manifest_json = pjct_archive.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_json)
                return True, manifest

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to read PJCT info: %s", str(e))
            return False, None

    def _verify_pjct_file(self, pjct_path: str) -> Tuple[bool, str]:
        """
        Verify integrity of a PJCT file.

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

                calculated_hash = hashlib.sha256(
                    (combined_data + salt).encode()
                ).hexdigest()

                if calculated_hash == stored_hash:
                    return True, "Integrity verified"
                return False, "Integrity check failed - file may be corrupted"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to verify PJCT file: {str(e)}"

    def list_pjct_files(self, pjct_path: str) -> Tuple[bool, Optional[list]]:
        """
        List all files in a PJCT archive.

        Args:
            pjct_path: Path to PJCT file

        Returns:
            Tuple of (success, file_list)
        """
        try:
            with zipfile.ZipFile(pjct_path, "r") as pjct_archive:
                files = [f for f in pjct_archive.namelist() if f.startswith("files/")]
                return True, files

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to list PJCT files: %s", str(e))
            return False, None
