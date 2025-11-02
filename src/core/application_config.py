"""
Application Configuration Module

This module contains the ApplicationConfig class that centralizes
application metadata, version information, and organization details.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ApplicationConfig:
    """Centralized application configuration and metadata."""

    # Application Identity - these will be populated dynamically
    name: str = "Digital Workshop"
    display_name: str = "Digital Workshop"
    version: str = "1.0.0"
    build_number: Optional[str] = None

    # Organization Information - these will be populated dynamically
    organization_name: str = "Digital Workshop Development Team"
    organization_domain: str = "digitalworkshop.local"

    # Application Paths and Settings
    app_data_subdir: str = "Digital Workshop"

    # Feature Flags
    enable_hardware_acceleration: bool = True
    enable_high_dpi: bool = True
    enable_performance_monitoring: bool = True

    # Resource Limits
    max_memory_usage_mb: int = 2048
    model_cache_size_mb: Optional[int] = None  # None for adaptive

    # Memory Override Settings
    use_manual_memory_override: bool = False
    manual_cache_limit_percent: int = 80  # Allow cache to use up to 80% of total system RAM
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
    grid_color: str = "theme"  # Use theme grid color, fallback to "#CCCCCC"
    grid_size: float = 10.0

    # 3D Viewer - Ground Plane Settings
    ground_visible: bool = True
    ground_color: str = "theme"  # Use theme ground color, fallback to "#999999"
    ground_offset: float = 0.5
    
    # 3D Viewer - Background Gradient Settings
    gradient_top_color: str = "#4A6FA5"  # Light sky blue
    gradient_bottom_color: str = "#1E3A5F"  # Dark ground blue
    enable_gradient: bool = True

    # Camera & Interaction Settings
    mouse_sensitivity: float = 1.0
    fps_limit: int = 0  # 0 = unlimited
    zoom_speed: float = 1.0
    pan_speed: float = 1.0
    auto_fit_on_load: bool = True

    # Lighting Settings
    default_light_position_x: float = 90.0
    default_light_position_y: float = 90.0
    default_light_position_z: float = 180.0
    default_light_color_r: float = 1.0
    default_light_color_g: float = 1.0
    default_light_color_b: float = 1.0
    default_light_intensity: float = 1.2
    default_light_cone_angle: float = 90.0
    enable_fill_light: bool = True
    fill_light_intensity: float = 0.3

    # Logging Configuration
    log_level: str = "INFO"
    enable_file_logging: bool = True
    enable_console_logging: bool = False  # Console logging disabled by default
    log_retention_days: int = 30

    # Thumbnail Generation Configuration
    thumbnail_bg_color: str = "theme"  # Use theme thumbnail background, fallback to "#F5F5F5"
    thumbnail_bg_image: Optional[str] = None  # Path to custom background image
    thumbnail_material: Optional[str] = None  # Wood species name for thumbnail material (e.g., 'Oak', 'Walnut')

    def get_effective_memory_limit_mb(
        self,
        available_memory_mb: Optional[int] = None,
        total_system_memory_mb: Optional[int] = None,
    ) -> int:
        """
        Calculate effective memory limit using smart algorithm.

        Algorithm: For systems with >32GB RAM, use adaptive scaling.
        For smaller systems, use conservative approach.

        This ensures:
        - App always has minimum needed to run
        - High-memory systems can utilize more resources
        - Low-memory systems remain conservative
        - Scales intelligently with system resources

        Args:
            available_memory_mb: Available system memory (if None, uses max_memory_usage_mb)
            total_system_memory_mb: Total system memory (if None, uses available_memory_mb)

        Returns:
            Effective memory limit in MB
        """
        # If manual override is enabled, use it
        if self.use_manual_memory_override:
            # Calculate cache limit as percentage of total system RAM
            if total_system_memory_mb is not None:
                return int(total_system_memory_mb * (self.manual_cache_limit_percent / 100))

        # Use provided values or defaults
        if available_memory_mb is None:
            available_memory_mb = self.max_memory_usage_mb
        if total_system_memory_mb is None:
            total_system_memory_mb = available_memory_mb

        # Convert to GB for easier calculation
        total_memory_gb = total_system_memory_mb / 1024.0

        # Adaptive memory calculation based on system size
        if total_memory_gb >= 64:
            # High-memory systems: Use up to 60% of available memory, max 16GB
            calculated_limit = min(
                int(available_memory_mb * 0.6),
                16384  # 16GB max for app
            )
        elif total_memory_gb >= 32:
            # Medium-high memory systems: Use up to 50% of available memory, max 8GB
            calculated_limit = min(
                int(available_memory_mb * 0.5),
                8192   # 8GB max for app
            )
        elif total_memory_gb >= 16:
            # Medium memory systems: Use up to 40% of available memory, max 4GB
            calculated_limit = min(
                int(available_memory_mb * 0.4),
                4096   # 4GB max for app
            )
        else:
            # Low memory systems: Use conservative approach
            fifty_percent_mb = available_memory_mb // 2
            hard_max_mb = int(
                total_system_memory_mb * (100 - self.system_memory_reserve_percent) / 100
            )
            calculated_limit = max(
                self.min_memory_specification_mb,
                min(fifty_percent_mb, hard_max_mb)
            )

        return calculated_limit

    @classmethod
    def get_default(cls) -> "ApplicationConfig":
        """Get the default application configuration."""
        config = cls()
        
        # Populate with dynamic version information
        try:
            from .version_manager import get_display_version, get_organization_name, get_app_name
            config.version = get_display_version()
            config.organization_name = get_organization_name()
            config.name = get_app_name()
            config.display_name = get_app_name()
        except ImportError:
            # Fallback to defaults if version manager not available
            pass
            
        return config

    def get_full_version_string(self) -> str:
        """Get the full version string including build number if available."""
        if self.build_number:
            return f"{self.version} (Build {self.build_number})"
        return self.version

    def get_app_identifier(self) -> str:
        """Get the unique application identifier."""
        return f"{self.organization_domain}.{self.name.lower()}"
