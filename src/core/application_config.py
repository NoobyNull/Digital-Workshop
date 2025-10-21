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

    # Memory Override Settings
    use_manual_memory_override: bool = False
    manual_memory_override_mb: Optional[int] = None
    min_memory_specification_mb: int = 512
    system_memory_reserve_percent: int = 20

    # UI Configuration
    default_window_width: int = 1200
    default_window_height: int = 800
    minimum_window_width: int = 800
    minimum_window_height: int = 600
    maximize_on_startup: bool = False
    remember_window_size: bool = True

    # 3D Viewer - Grid Settings
    grid_visible: bool = True
    grid_color: str = "#CCCCCC"
    grid_size: float = 10.0

    # 3D Viewer - Ground Plane Settings
    ground_visible: bool = True
    ground_color: str = "#999999"
    ground_offset: float = 0.5

    # Camera & Interaction Settings
    mouse_sensitivity: float = 1.0
    fps_limit: int = 0  # 0 = unlimited
    zoom_speed: float = 1.0
    pan_speed: float = 1.0
    auto_fit_on_load: bool = True

    # Lighting Settings
    default_light_position_x: float = 100.0
    default_light_position_y: float = 100.0
    default_light_position_z: float = 100.0
    default_light_color_r: float = 1.0
    default_light_color_g: float = 1.0
    default_light_color_b: float = 1.0
    default_light_intensity: float = 0.8
    default_light_cone_angle: float = 30.0
    enable_fill_light: bool = True
    fill_light_intensity: float = 0.3

    # Logging Configuration
    log_level: str = "INFO"
    enable_file_logging: bool = True
    log_retention_days: int = 30

    # Thumbnail Generation Configuration
    thumbnail_bg_color: str = "#F5F5F5"  # Light gray default background
    thumbnail_bg_image: Optional[str] = None  # Path to custom background image
    thumbnail_material: Optional[str] = None  # Wood species name for thumbnail material (e.g., 'Oak', 'Walnut')

    def get_effective_memory_limit_mb(
        self,
        available_memory_mb: Optional[int] = None,
        total_system_memory_mb: Optional[int] = None,
    ) -> int:
        """
        Calculate effective memory limit using smart algorithm.

        Algorithm: min(doubled_minimum, 50% available, total - 20%)

        Args:
            available_memory_mb: Available system memory (if None, uses max_memory_usage_mb)
            total_system_memory_mb: Total system memory (if None, uses available_memory_mb)

        Returns:
            Effective memory limit in MB
        """
        # If manual override is enabled, use it
        if self.use_manual_memory_override and self.manual_memory_override_mb is not None:
            return self.manual_memory_override_mb

        # Use provided values or defaults
        if available_memory_mb is None:
            available_memory_mb = self.max_memory_usage_mb
        if total_system_memory_mb is None:
            total_system_memory_mb = available_memory_mb

        # Calculate three candidates
        minimum_doubled_mb = self.min_memory_specification_mb * 2
        fifty_percent_mb = available_memory_mb // 2
        hard_max_mb = int(
            total_system_memory_mb * (100 - self.system_memory_reserve_percent) / 100
        )

        # Take minimum of all three
        calculated_limit = min(minimum_doubled_mb, fifty_percent_mb, hard_max_mb)

        # Ensure we don't go below minimum
        calculated_limit = max(calculated_limit, self.min_memory_specification_mb)

        return calculated_limit

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
