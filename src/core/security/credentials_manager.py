"""
Secure credentials management.

Handles API keys and credentials without storing them in plain text.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class CredentialsManager:
    """Manages credentials securely using environment variables."""

    # Supported credential types
    SUPPORTED_TYPES = {"api_key", "database_url", "auth_token"}

    def __init__(self):
        """Initialize credentials manager."""
        self.security_logger = None

    def get_credential(self, credential_name: str) -> Optional[str]:
        """Get credential from environment variables.
        
        Args:
            credential_name: Name of the credential
            
        Returns:
            Credential value or None if not found
        """
        # Convert to environment variable format
        env_var = f"DW_{credential_name.upper()}"
        
        credential = os.environ.get(env_var)
        
        if credential:
            logger.debug("Retrieved credential: %s", credential_name)
            if self.security_logger:
                self.security_logger.log_credential_access(credential_name, True)
        else:
            logger.warning("Credential not found: %s", credential_name)
            if self.security_logger:
                self.security_logger.log_credential_access(credential_name, False)
        
        return credential

    def set_credential(self, credential_name: str, value: str) -> bool:
        """Set credential in environment variables.
        
        Args:
            credential_name: Name of the credential
            value: Credential value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            env_var = f"DW_{credential_name.upper()}"
            os.environ[env_var] = value
            logger.info("Credential set: %s", credential_name)
            return True
        except (OSError, ValueError) as e:
            logger.error("Failed to set credential %s: %s", credential_name, e)
            return False

    def load_credentials_from_env_file(self, env_file_path: str) -> bool:
        """Load credentials from .env file.
        
        Args:
            env_file_path: Path to .env file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            env_path = Path(env_file_path)
            if not env_path.exists():
                logger.warning("Environment file not found: %s", env_file_path)
                return False
            
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
            
            logger.info("Loaded credentials from: %s", env_file_path)
            return True
            
        except (OSError, IOError) as e:
            logger.error("Failed to load credentials from %s: %s", env_file_path, e)
            return False

    def validate_credentials(self, required_credentials: list) -> bool:
        """Validate that all required credentials are available.
        
        Args:
            required_credentials: List of required credential names
            
        Returns:
            True if all credentials are available, False otherwise
        """
        missing = []
        for cred_name in required_credentials:
            if not self.get_credential(cred_name):
                missing.append(cred_name)
        
        if missing:
            logger.error("Missing required credentials: %s", missing)
            return False
        
        logger.info("All required credentials are available")
        return True

    @staticmethod
    def mask_credential(credential: str, visible_chars: int = 4) -> str:
        """Mask credential for logging.
        
        Args:
            credential: Credential to mask
            visible_chars: Number of characters to show
            
        Returns:
            Masked credential string
        """
        if len(credential) <= visible_chars:
            return "*" * len(credential)
        
        return credential[:visible_chars] + "*" * (len(credential) - visible_chars)

