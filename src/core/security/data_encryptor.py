"""
Data encryption utilities for protecting sensitive information.

Provides encryption/decryption for sensitive project data.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DataEncryptor:
    """Encrypts and decrypts sensitive data."""

    def __init__(self):
        """Initialize data encryptor."""
        self._check_cryptography_available()

    @staticmethod
    def _check_cryptography_available() -> None:
        """Check if cryptography library is available."""
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logger.warning(
                "cryptography library not available. "
                "Install with: pip install cryptography"
            )

    def generate_key(self) -> str:
        """Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            return key.decode("utf-8")
        except ImportError:
            logger.error("cryptography library not available")
            return ""

    def encrypt_data(self, data: str, key: str) -> Optional[str]:
        """Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            
        Returns:
            Encrypted data (base64-encoded) or None if error
        """
        try:
            from cryptography.fernet import Fernet
            
            cipher = Fernet(key.encode("utf-8"))
            encrypted = cipher.encrypt(data.encode("utf-8"))
            return encrypted.decode("utf-8")
            
        except (ImportError, ValueError) as e:
            logger.error("Encryption failed: %s", e)
            return None

    def decrypt_data(self, encrypted_data: str, key: str) -> Optional[str]:
        """Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data: Encrypted data (base64-encoded)
            key: Encryption key
            
        Returns:
            Decrypted data or None if error
        """
        try:
            from cryptography.fernet import Fernet
            
            cipher = Fernet(key.encode("utf-8"))
            decrypted = cipher.decrypt(encrypted_data.encode("utf-8"))
            return decrypted.decode("utf-8")
            
        except (ImportError, ValueError) as e:
            logger.error("Decryption failed: %s", e)
            return None

    def encrypt_file(self, file_path: str, key: str) -> bool:
        """Encrypt a file in place.
        
        Args:
            file_path: Path to file to encrypt
            key: Encryption key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error("File not found: %s", file_path)
                return False
            
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            
            encrypted = self.encrypt_data(data, key)
            if encrypted is None:
                return False
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(encrypted)
            
            logger.info("File encrypted: %s", file_path)
            return True
            
        except (OSError, IOError) as e:
            logger.error("Failed to encrypt file %s: %s", file_path, e)
            return False

    def decrypt_file(self, file_path: str, key: str) -> bool:
        """Decrypt a file in place.
        
        Args:
            file_path: Path to file to decrypt
            key: Encryption key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error("File not found: %s", file_path)
                return False
            
            with open(path, "r", encoding="utf-8") as f:
                encrypted_data = f.read()
            
            decrypted = self.decrypt_data(encrypted_data, key)
            if decrypted is None:
                return False
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(decrypted)
            
            logger.info("File decrypted: %s", file_path)
            return True
            
        except (OSError, IOError) as e:
            logger.error("Failed to decrypt file %s: %s", file_path, e)
            return False

