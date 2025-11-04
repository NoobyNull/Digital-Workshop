"""
Snap Configuration Module

This module provides configurable snap settings and parameters for the widget snapping system.
It manages all snap-related configuration including snap zones, magnetism, visual feedback,
and performance settings.

Classes:
    SnapConfiguration: Manages all snap configuration settings
    SnapZone: Represents a snap zone configuration
    VisualSettings: Manages visual feedback settings
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from PySide6.QtCore import QRect

from src.core.logging_config import get_logger


@dataclass
class SnapZone:
    """
    Configuration for a snap zone area.

    Defines the geometry and behavior of a snap zone where widgets can snap to.

    Attributes:
        name: Unique identifier for the snap zone
        area: Rectangular area in unified coordinates
        magnetism: Strength of the magnetic attraction (0.0 to 1.0)
        snap_threshold: Distance threshold for snapping activation (pixels)
        priority: Priority level for overlapping zones (higher = more priority)
        enabled: Whether this snap zone is active
    """

    name: str
    area: QRect
    magnetism: float = 0.8
    snap_threshold: int = 56
    priority: int = 1
    enabled: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 0.0 <= self.magnetism <= 1.0:
            raise ValueError(
                f"Magnetism must be between 0.0 and 1.0, got {self.magnetism}"
            )
        if self.snap_threshold < 0:
            raise ValueError(
                f"Snap threshold must be non-negative, got {self.snap_threshold}"
            )
        if self.priority < 0:
            raise ValueError(f"Priority must be non-negative, got {self.priority}")


@dataclass
class VisualSettings:
    """
    Visual feedback settings for snap guides.

    Controls the appearance and behavior of visual snap indicators.

    Attributes:
        show_guides: Whether to show snap guide lines
        guide_color: Color for snap guides (RGBA tuple)
        guide_width: Width of guide lines (pixels)
        guide_style: Style of guide lines ('solid', 'dashed', 'dotted')
        highlight_color: Color for active snap zones (RGBA tuple)
        highlight_opacity: Opacity for zone highlighting (0.0 to 1.0)
        animation_duration: Duration of snap animations (milliseconds)
        fade_in_duration: Duration of fade-in effect (milliseconds)
        fade_out_duration: Duration of fade-out effect (milliseconds)
    """

    show_guides: bool = True
    guide_color: Tuple[int, int, int, int] = (
        0,
        120,
        212,
        180,
    )  # Default blue with alpha
    guide_width: int = 2
    guide_style: str = "dashed"
    highlight_color: Tuple[int, int, int, int] = (
        0,
        120,
        212,
        100,
    )  # Lighter blue with alpha
    highlight_opacity: float = 0.3
    animation_duration: int = 150
    fade_in_duration: int = 100
    fade_out_duration: int = 200

    def __post_init__(self):
        """Validate visual settings after initialization."""
        if not 0.0 <= self.highlight_opacity <= 1.0:
            raise ValueError(
                f"Highlight opacity must be between 0.0 and 1.0, got {self.highlight_opacity}"
            )
        if self.guide_width < 1:
            raise ValueError(f"Guide width must be at least 1, got {self.guide_width}")
        if self.guide_style not in ["solid", "dashed", "dotted"]:
            raise ValueError(
                f"Invalid guide style '{self.guide_style}', must be 'solid', 'dashed', or 'dotted'"
            )
        if self.animation_duration < 0:
            raise ValueError(
                f"Animation duration must be non-negative, got {self.animation_duration}"
            )


@dataclass
class PerformanceSettings:
    """
    Performance optimization settings for the snapping system.

    Controls performance-related aspects to maintain 30+ FPS during interaction.

    Attributes:
        max_snap_calculations_per_frame: Maximum snap calculations per frame
        spatial_index_enabled: Whether to use spatial indexing for performance
        cache_size: Size of coordinate transformation cache
        hysteresis_threshold: Minimum movement before recalculating snap (pixels)
        update_debounce_ms: Debounce time for snap updates (milliseconds)
        enable_hardware_acceleration: Whether to use hardware acceleration for rendering
        max_memory_usage_mb: Maximum memory usage for snap system (MB)
    """

    max_snap_calculations_per_frame: int = 100
    spatial_index_enabled: bool = True
    cache_size: int = 1000
    hysteresis_threshold: int = 2
    update_debounce_ms: int = 16  # ~60 FPS
    enable_hardware_acceleration: bool = True
    max_memory_usage_mb: int = 50

    def __post_init__(self):
        """Validate performance settings after initialization."""
        if self.max_snap_calculations_per_frame < 1:
            raise ValueError(
                f"Max snap calculations must be at least 1, got {self.max_snap_calculations_per_frame}"
            )
        if self.cache_size < 1:
            raise ValueError(f"Cache size must be at least 1, got {self.cache_size}")
        if self.hysteresis_threshold < 0:
            raise ValueError(
                f"Hysteresis threshold must be non-negative, got {self.hysteresis_threshold}"
            )
        if self.update_debounce_ms < 1:
            raise ValueError(
                f"Update debounce must be at least 1ms, got {self.update_debounce_ms}"
            )
        if self.max_memory_usage_mb < 1:
            raise ValueError(
                f"Max memory usage must be at least 1MB, got {self.max_memory_usage_mb}"
            )


class SnapConfiguration:
    """
    Manages all snap configuration settings for the widget snapping system.

    This class provides a centralized configuration system for all snapping behavior,
    including snap zones, visual feedback, performance settings, and persistence.

    The configuration supports loading from and saving to JSON files, with validation
    and sensible defaults for all settings.

    Attributes:
        snap_zones: Dictionary of snap zone configurations by name
        visual: Visual feedback settings
        performance: Performance optimization settings
        enabled: Whether the entire snapping system is enabled
        logger: Logger instance for debugging and monitoring
    """

    DEFAULT_CONFIG_FILE = "snap_configuration.json"

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the snap configuration system.

        Args:
            config_file: Optional path to configuration file. If None, uses default location.
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing snap configuration system")

        # Core settings
        self.enabled: bool = True
        self.config_file: Optional[Path] = Path(config_file) if config_file else None

        # Component configurations
        self.snap_zones: Dict[str, SnapZone] = {}
        self.visual: VisualSettings = VisualSettings()
        self.performance: PerformanceSettings = PerformanceSettings()

        # Initialize with default snap zones
        self._initialize_default_zones()

        # Load configuration if file exists
        if self.config_file and self.config_file.exists():
            try:
                self.load_from_file()
                self.logger.info(f"Loaded snap configuration from {self.config_file}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to load configuration file, using defaults: {e}"
                )
        else:
            self.logger.info("Using default snap configuration")

    def _initialize_default_zones(self) -> None:
        """
        Initialize default snap zones for standard window edges.

        Creates snap zones for the four main window edges with sensible defaults.
        """
        try:
            # Default snap zones for main window edges
            default_zones = [
                SnapZone(
                    "left_edge", QRect(0, 0, 48, 1000), magnetism=0.8, snap_threshold=56
                ),
                SnapZone(
                    "right_edge",
                    QRect(1000, 0, 48, 1000),
                    magnetism=0.8,
                    snap_threshold=56,
                ),
                SnapZone(
                    "top_edge", QRect(0, 0, 1000, 48), magnetism=0.8, snap_threshold=56
                ),
                SnapZone(
                    "bottom_edge",
                    QRect(0, 1000, 1000, 48),
                    magnetism=0.8,
                    snap_threshold=56,
                ),
            ]

            for zone in default_zones:
                self.snap_zones[zone.name] = zone

            self.logger.debug(f"Initialized {len(default_zones)} default snap zones")
        except Exception as e:
            self.logger.error(f"Failed to initialize default snap zones: {e}")
            raise

    def add_snap_zone(self, zone: SnapZone) -> None:
        """
        Add a new snap zone to the configuration.

        Args:
            zone: Snap zone configuration to add

        Raises:
            ValueError: If zone name already exists or configuration is invalid
        """
        try:
            if zone.name in self.snap_zones:
                raise ValueError(f"Snap zone '{zone.name}' already exists")

            # Validate the zone configuration
            zone.__post_init__()

            self.snap_zones[zone.name] = zone
            self.logger.info(
                f"Added snap zone '{zone.name}' with threshold {zone.snap_threshold}px"
            )
        except Exception as e:
            self.logger.error(f"Failed to add snap zone '{zone.name}': {e}")
            raise

    def remove_snap_zone(self, zone_name: str) -> bool:
        """
        Remove a snap zone from the configuration.

        Args:
            zone_name: Name of the snap zone to remove

        Returns:
            True if zone was removed, False if not found
        """
        try:
            if zone_name not in self.snap_zones:
                self.logger.warning(f"Snap zone '{zone_name}' not found")
                return False

            del self.snap_zones[zone_name]
            self.logger.info(f"Removed snap zone '{zone_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove snap zone '{zone_name}': {e}")
            return False

    def get_snap_zone(self, zone_name: str) -> Optional[SnapZone]:
        """
        Get a snap zone configuration by name.

        Args:
            zone_name: Name of the snap zone

        Returns:
            Snap zone configuration or None if not found
        """
        return self.snap_zones.get(zone_name)

    def update_snap_zone(self, zone_name: str, **kwargs) -> bool:
        """
        Update properties of an existing snap zone.

        Args:
            zone_name: Name of the snap zone to update
            **kwargs: Properties to update (magnetism, snap_threshold, priority, enabled, area)

        Returns:
            True if update was successful, False if zone not found
        """
        try:
            if zone_name not in self.snap_zones:
                self.logger.warning(f"Snap zone '{zone_name}' not found for update")
                return False

            zone = self.snap_zones[zone_name]

            # Update allowed properties
            for key, value in kwargs.items():
                if hasattr(zone, key):
                    setattr(zone, key, value)
                else:
                    self.logger.warning(f"Unknown snap zone property '{key}'")

            # Re-validate the zone
            zone.__post_init__()

            self.logger.debug(f"Updated snap zone '{zone_name}': {kwargs}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update snap zone '{zone_name}': {e}")
            return False

    def get_active_snap_zones(self) -> List[SnapZone]:
        """
        Get all currently active (enabled) snap zones.

        Returns:
            List of active snap zones sorted by priority (highest first)
        """
        try:
            active_zones = [zone for zone in self.snap_zones.values() if zone.enabled]
            active_zones.sort(key=lambda z: z.priority, reverse=True)
            return active_zones
        except Exception as e:
            self.logger.error(f"Failed to get active snap zones: {e}")
            return []

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the entire snapping system.

        Args:
            enabled: Whether snapping should be enabled
        """
        try:
            old_state = self.enabled
            self.enabled = enabled
            self.logger.info(f"Snapping system {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set snapping enabled state: {e}")
            self.enabled = old_state  # Restore previous state

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format for serialization.

        Returns:
            Dictionary representation of the configuration
        """
        try:
            zones_data = {}
            for name, zone in self.snap_zones.items():
                zones_data[name] = {
                    "name": zone.name,
                    "area": {
                        "x": zone.area.x(),
                        "y": zone.area.y(),
                        "width": zone.area.width(),
                        "height": zone.area.height(),
                    },
                    "magnetism": zone.magnetism,
                    "snap_threshold": zone.snap_threshold,
                    "priority": zone.priority,
                    "enabled": zone.enabled,
                }

            return {
                "enabled": self.enabled,
                "visual": {
                    "show_guides": self.visual.show_guides,
                    "guide_color": self.visual.guide_color,
                    "guide_width": self.visual.guide_width,
                    "guide_style": self.visual.guide_style,
                    "highlight_color": self.visual.highlight_color,
                    "highlight_opacity": self.visual.highlight_opacity,
                    "animation_duration": self.visual.animation_duration,
                    "fade_in_duration": self.visual.fade_in_duration,
                    "fade_out_duration": self.visual.fade_out_duration,
                },
                "performance": {
                    "max_snap_calculations_per_frame": self.performance.max_snap_calculations_per_frame,
                    "spatial_index_enabled": self.performance.spatial_index_enabled,
                    "cache_size": self.performance.cache_size,
                    "hysteresis_threshold": self.performance.hysteresis_threshold,
                    "update_debounce_ms": self.performance.update_debounce_ms,
                    "enable_hardware_acceleration": self.performance.enable_hardware_acceleration,
                    "max_memory_usage_mb": self.performance.max_memory_usage_mb,
                },
                "snap_zones": zones_data,
            }
        except Exception as e:
            self.logger.error(f"Failed to convert configuration to dictionary: {e}")
            return {}

    def from_dict(self, data: Dict[str, Any]) -> bool:
        """
        Load configuration from dictionary format.

        Args:
            data: Dictionary containing configuration data

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Load core settings
            self.enabled = data.get("enabled", True)

            # Load visual settings
            if "visual" in data:
                visual_data = data["visual"]
                self.visual = VisualSettings(
                    show_guides=visual_data.get("show_guides", True),
                    guide_color=tuple(
                        visual_data.get("guide_color", (0, 120, 212, 180))
                    ),
                    guide_width=visual_data.get("guide_width", 2),
                    guide_style=visual_data.get("guide_style", "dashed"),
                    highlight_color=tuple(
                        visual_data.get("highlight_color", (0, 120, 212, 100))
                    ),
                    highlight_opacity=visual_data.get("highlight_opacity", 0.3),
                    animation_duration=visual_data.get("animation_duration", 150),
                    fade_in_duration=visual_data.get("fade_in_duration", 100),
                    fade_out_duration=visual_data.get("fade_out_duration", 200),
                )

            # Load performance settings
            if "performance" in data:
                perf_data = data["performance"]
                self.performance = PerformanceSettings(
                    max_snap_calculations_per_frame=perf_data.get(
                        "max_snap_calculations_per_frame", 100
                    ),
                    spatial_index_enabled=perf_data.get("spatial_index_enabled", True),
                    cache_size=perf_data.get("cache_size", 1000),
                    hysteresis_threshold=perf_data.get("hysteresis_threshold", 2),
                    update_debounce_ms=perf_data.get("update_debounce_ms", 16),
                    enable_hardware_acceleration=perf_data.get(
                        "enable_hardware_acceleration", True
                    ),
                    max_memory_usage_mb=perf_data.get("max_memory_usage_mb", 50),
                )

            # Load snap zones
            self.snap_zones.clear()
            if "snap_zones" in data:
                for name, zone_data in data["snap_zones"].items():
                    try:
                        area_data = zone_data["area"]
                        area = QRect(
                            area_data["x"],
                            area_data["y"],
                            area_data["width"],
                            area_data["height"],
                        )
                        zone = SnapZone(
                            name=zone_data["name"],
                            area=area,
                            magnetism=zone_data.get("magnetism", 0.8),
                            snap_threshold=zone_data.get("snap_threshold", 56),
                            priority=zone_data.get("priority", 1),
                            enabled=zone_data.get("enabled", True),
                        )
                        self.snap_zones[name] = zone
                    except Exception as e:
                        self.logger.warning(f"Failed to load snap zone '{name}': {e}")
                        continue

            self.logger.info(
                f"Loaded configuration from dictionary with {len(self.snap_zones)} snap zones"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to load configuration from dictionary: {e}")
            return False

    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            file_path: Path to save file. If None, uses the configured file path.

        Returns:
            True if saving was successful, False otherwise
        """
        try:
            save_path = Path(file_path) if file_path else self.config_file
            if not save_path:
                save_path = Path(self.DEFAULT_CONFIG_FILE)

            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and save
            config_dict = self.to_dict()

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved snap configuration to {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration to file: {e}")
            return False

    def load_from_file(self, file_path: Optional[str] = None) -> bool:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to load file. If None, uses the configured file path.

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            load_path = Path(file_path) if file_path else self.config_file
            if not load_path:
                load_path = Path(self.DEFAULT_CONFIG_FILE)

            if not load_path.exists():
                self.logger.warning(f"Configuration file does not exist: {load_path}")
                return False

            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            success = self.from_dict(data)
            if success:
                self.logger.info(f"Loaded snap configuration from {load_path}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to load configuration from file: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """
        Reset all configuration settings to their default values.

        This will clear all custom snap zones and restore default settings.
        """
        try:
            self.enabled = True
            self.visual = VisualSettings()
            self.performance = PerformanceSettings()
            self.snap_zones.clear()
            self._initialize_default_zones()

            self.logger.info("Reset snap configuration to defaults")
        except Exception as e:
            self.logger.error(f"Failed to reset configuration to defaults: {e}")
            raise

    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration and return any issues.

        Returns:
            List of validation error messages. Empty list if configuration is valid.
        """
        errors = []

        try:
            # Validate core settings
            if not isinstance(self.enabled, bool):
                errors.append("Enabled flag must be boolean")

            # Validate visual settings
            if not isinstance(self.visual, VisualSettings):
                errors.append("Visual settings must be VisualSettings instance")
            else:
                try:
                    self.visual.__post_init__()
                except ValueError as e:
                    errors.append(f"Visual settings validation error: {e}")

            # Validate performance settings
            if not isinstance(self.performance, PerformanceSettings):
                errors.append(
                    "Performance settings must be PerformanceSettings instance"
                )
            else:
                try:
                    self.performance.__post_init__()
                except ValueError as e:
                    errors.append(f"Performance settings validation error: {e}")

            # Validate snap zones
            for name, zone in self.snap_zones.items():
                if not isinstance(zone, SnapZone):
                    errors.append(f"Snap zone '{name}' must be SnapZone instance")
                    continue
                try:
                    zone.__post_init__()
                except ValueError as e:
                    errors.append(f"Snap zone '{name}' validation error: {e}")

            return errors
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return [f"Validation error: {e}"]

    def get_memory_usage(self) -> int:
        """
        Estimate memory usage of the configuration in bytes.

        Returns:
            Estimated memory usage in bytes
        """
        try:
            # Base configuration memory
            memory = 1024  # Base overhead

            # Snap zones memory (approximate)
            for _ in self.snap_zones.values():
                memory += 256  # Approximate per zone

            # Visual settings memory
            memory += 128

            # Performance settings memory
            memory += 64

            return memory
        except Exception as e:
            self.logger.error(f"Failed to calculate memory usage: {e}")
            return 0
