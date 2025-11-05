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
        logger.debug(f"Calculating checksum for: {file_path}")
        
        try:
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(ChecksumUtils.CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            checksum = hasher.hexdigest()
            logger.debug(f"Checksum calculated: {file_path} = {checksum}")
            
            return checksum
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
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
        logger.debug(f"Calculating directory checksum: {directory}")
        
        try:
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
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
            logger.debug(f"Directory checksum calculated: {directory} = {checksum}")
            
            return checksum
            
        except Exception as e:
            logger.error(f"Failed to calculate directory checksum: {e}")
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
        logger.debug(f"Verifying checksum for: {file_path}")
        
        try:
            calculated_checksum = ChecksumUtils.calculate_file_checksum(file_path)
            
            if calculated_checksum is None:
                logger.error(f"Failed to calculate checksum: {file_path}")
                return False
            
            if calculated_checksum == expected_checksum:
                logger.debug(f"Checksum verified: {file_path}")
                return True
            else:
                logger.error(f"Checksum mismatch: {file_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Got:      {calculated_checksum}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify checksum: {e}")
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
        logger.info(f"Creating checksum manifest: {directory}")
        
        try:
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
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
            
            logger.info(f"Checksum manifest created: {len(manifest)} files")
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to create checksum manifest: {e}")
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
        logger.info(f"Verifying checksum manifest: {directory}")
        
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
            logger.error(f"Failed to verify checksum manifest: {e}")
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
        logger.debug(f"Saving checksum manifest: {manifest_file}")
        
        try:
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.debug(f"Checksum manifest saved: {manifest_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checksum manifest: {e}")
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
        logger.debug(f"Loading checksum manifest: {manifest_file}")
        
        try:
            if not manifest_file.exists():
                logger.error(f"Manifest file not found: {manifest_file}")
                return None
            
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            logger.debug(f"Checksum manifest loaded: {len(manifest)} files")
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to load checksum manifest: {e}")
            return None

