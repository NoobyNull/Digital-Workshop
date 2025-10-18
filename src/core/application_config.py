#!/usr/bin/env python3
"""
Application Configuration Module

This module contains the ApplicationConfig class that centralizes
application metadata, version information, and organization details.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ApplicationConfig:
    """Centralized application configuration and metadata."""

    # Application Identity
    name: str = "3D-MM"
    display_name: str = "3D Model Manager"
    version: str = "1.0.0"
    build_number: Optional[str] = None

    # Organization Information
    organization_name: str = "3D-MM Development Team"
    organization_domain: str = "3dmm.local"

    # Application Paths and Settings
    app_data_subdir: str = "3D-MM"

    # Feature Flags
    enable_hardware_acceleration: bool = True
    enable_high_dpi: bool = True
    enable_performance_monitoring: bool = True

    # Resource Limits
    max_memory_usage_mb: int = 2048
    model_cache_size_mb: Optional[int] = None  # None for adaptive

    # UI Configuration
    default_window_width: int = 1200
    default_window_height: int = 800
    minimum_window_width: int = 800
    minimum_window_height: int = 600

    # Logging Configuration
    log_level: str = "DEBUG"
    enable_file_logging: bool = True
    log_retention_days: int = 30

    # Thumbnail Generation Configuration
    thumbnail_bg_color: str = "#F5F5F5"  # Light gray default background
    thumbnail_bg_image: Optional[str] = None  # Path to custom background image
    thumbnail_material: Optional[str] = None  # Wood species name for thumbnail material (e.g., 'Oak', 'Walnut')

    @classmethod
    def get_default(cls) -> "ApplicationConfig":
        """Get the default application configuration."""
        return cls()

    def get_full_version_string(self) -> str:
        """Get the full version string including build number if available."""
        if self.build_number:
            return f"{self.version} (Build {self.build_number})"
        return self.version

    def get_app_identifier(self) -> str:
        """Get the unique application identifier."""
        return f"{self.organization_domain}.{self.name.lower()}"
