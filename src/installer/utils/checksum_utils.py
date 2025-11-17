"""
Checksum Utilities - Calculate and verify file checksums

Provides SHA256 checksum calculation and verification for:
- Module integrity verification
- Backup integrity verification
- File corruption detection
"""

import hashlib
import logging
import json
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ChecksumUtils:
    """Utilities for checksum calculation and verification."""

    ALGORITHM = "sha256"
    CHUNK_SIZE = 8192  # 8KB chunks for memory efficiency

    @staticmethod
    def calculate_file_checksum(file_path: Path) -> Optional[str]:
        """
        Calculate SHA256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of checksum or None if failed
        """
        logger.debug("Calculating checksum for: %s", file_path)

        try:
            if not file_path.exists():
                logger.error("File not found: %s", file_path)
                return None

            hasher = hashlib.sha256()

            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(ChecksumUtils.CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)

            checksum = hasher.hexdigest()
            logger.debug("Checksum calculated: %s = {checksum}", file_path)

            return checksum

        except Exception as e:
            logger.error("Failed to calculate checksum: %s", e)
            return None

    @staticmethod
    def calculate_directory_checksum(directory: Path) -> Optional[str]:
        """
        Calculate combined checksum of all files in directory.

        Args:
            directory: Path to directory

        Returns:
            Hex digest of combined checksum or None if failed
        """
        logger.debug("Calculating directory checksum: %s", directory)

        try:
            if not directory.exists():
                logger.error("Directory not found: %s", directory)
                return None

            hasher = hashlib.sha256()

            # Get all files in directory recursively
            files = sorted(directory.rglob("*"))

            for file_path in files:
                if file_path.is_file():
                    file_checksum = ChecksumUtils.calculate_file_checksum(file_path)
                    if file_checksum:
                        hasher.update(file_checksum.encode())

            checksum = hasher.hexdigest()
            logger.debug("Directory checksum calculated: %s = {checksum}", directory)

            return checksum

        except Exception as e:
            logger.error("Failed to calculate directory checksum: %s", e)
            return None

    @staticmethod
    def verify_file_checksum(file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file checksum.

        Args:
            file_path: Path to file
            expected_checksum: Expected checksum value

        Returns:
            True if checksum matches, False otherwise
        """
        logger.debug("Verifying checksum for: %s", file_path)

        try:
            calculated_checksum = ChecksumUtils.calculate_file_checksum(file_path)

            if calculated_checksum is None:
                logger.error("Failed to calculate checksum: %s", file_path)
                return False

            if calculated_checksum == expected_checksum:
                logger.debug("Checksum verified: %s", file_path)
                return True
            else:
                logger.error("Checksum mismatch: %s", file_path)
                logger.error("  Expected: %s", expected_checksum)
                logger.error("  Got:      %s", calculated_checksum)
                return False

        except Exception as e:
            logger.error("Failed to verify checksum: %s", e)
            return False

    @staticmethod
    def create_checksum_manifest(directory: Path) -> Optional[Dict[str, str]]:
        """
        Create checksum manifest for all files in directory.

        Args:
            directory: Path to directory

        Returns:
            Dict mapping file paths to checksums or None if failed
        """
        logger.info("Creating checksum manifest: %s", directory)

        try:
            if not directory.exists():
                logger.error("Directory not found: %s", directory)
                return None

            manifest = {}

            # Get all files in directory recursively
            files = sorted(directory.rglob("*"))

            for file_path in files:
                if file_path.is_file():
                    relative_path = file_path.relative_to(directory)
                    checksum = ChecksumUtils.calculate_file_checksum(file_path)

                    if checksum:
                        manifest[str(relative_path)] = checksum

            logger.info("Checksum manifest created: %s files", len(manifest))
            return manifest

        except Exception as e:
            logger.error("Failed to create checksum manifest: %s", e)
            return None

    @staticmethod
    def verify_checksum_manifest(directory: Path, manifest: Dict[str, str]) -> bool:
        """
        Verify all files against checksum manifest.

        Args:
            directory: Path to directory
            manifest: Dict mapping file paths to checksums

        Returns:
            True if all files match, False otherwise
        """
        logger.info("Verifying checksum manifest: %s", directory)

        try:
            all_valid = True

            for relative_path, expected_checksum in manifest.items():
                file_path = directory / relative_path

                if not ChecksumUtils.verify_file_checksum(file_path, expected_checksum):
                    all_valid = False

            if all_valid:
                logger.info("Checksum manifest verified")
            else:
                logger.error("Checksum manifest verification failed")

            return all_valid

        except Exception as e:
            logger.error("Failed to verify checksum manifest: %s", e)
            return False

    @staticmethod
    def save_checksum_manifest(manifest: Dict[str, str], manifest_file: Path) -> bool:
        """
        Save checksum manifest to file.

        Args:
            manifest: Dict mapping file paths to checksums
            manifest_file: Path to save manifest

        Returns:
            True if successful, False otherwise
        """
        logger.debug("Saving checksum manifest: %s", manifest_file)

        try:
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)

            logger.debug("Checksum manifest saved: %s", manifest_file)
            return True

        except Exception as e:
            logger.error("Failed to save checksum manifest: %s", e)
            return False

    @staticmethod
    def load_checksum_manifest(manifest_file: Path) -> Optional[Dict[str, str]]:
        """
        Load checksum manifest from file.

        Args:
            manifest_file: Path to manifest file

        Returns:
            Dict mapping file paths to checksums or None if failed
        """
        logger.debug("Loading checksum manifest: %s", manifest_file)

        try:
            if not manifest_file.exists():
                logger.error("Manifest file not found: %s", manifest_file)
                return None

            with open(manifest_file, "r") as f:
                manifest = json.load(f)

            logger.debug("Checksum manifest loaded: %s files", len(manifest))
            return manifest

        except Exception as e:
            logger.error("Failed to load checksum manifest: %s", e)
            return None
