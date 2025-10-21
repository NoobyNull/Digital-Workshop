#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It uses the new modular Application class for initialization and execution.
"""

import argparse
import sys
import os

# Add the parent directory to the Python path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.core.application import Application
from src.core.application_config import ApplicationConfig
from src.core.exception_handler import ExceptionHandler


def parse_arguments():
    """Parse command line arguments for the application.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="3D-MM (3D Model Manager) - Manage and view 3D models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start with INFO logging (default)
  python main.py --debug            # Start with DEBUG logging
  python main.py --log-level DEBUG  # Start with DEBUG logging
  python main.py --log-level INFO   # Start with INFO logging
  python main.py --log-level WARNING # Start with WARNING logging
        """
    )
    
    # Log level arguments
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--debug",
        action="store_const",
        const="DEBUG",
        dest="log_level",
        help="Enable DEBUG level logging (verbose output)"
    )
    log_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser.parse_args()


def main():
    """Main function to start the 3D-MM application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle None case (when no arguments are provided in mutually exclusive group)
    log_level = args.log_level if args.log_level is not None else "INFO"
    
    # Create application configuration with overridden log level
    config = ApplicationConfig.get_default()
    
    # Since ApplicationConfig is frozen, we need to create a new instance
    # with all the original fields but with the log level overridden
    config = ApplicationConfig(
        # Application Identity
        name=config.name,
        display_name=config.display_name,
        version=config.version,
        build_number=config.build_number,
        
        # Organization Information
        organization_name=config.organization_name,
        organization_domain=config.organization_domain,
        
        # Application Paths and Settings
        app_data_subdir=config.app_data_subdir,
        
        # Feature Flags
        enable_hardware_acceleration=config.enable_hardware_acceleration,
        enable_high_dpi=config.enable_high_dpi,
        enable_performance_monitoring=config.enable_performance_monitoring,
        
        # Resource Limits
        max_memory_usage_mb=config.max_memory_usage_mb,
        model_cache_size_mb=config.model_cache_size_mb,
        
        # Memory Override Settings
        use_manual_memory_override=config.use_manual_memory_override,
        manual_memory_override_mb=config.manual_memory_override_mb,
        min_memory_specification_mb=config.min_memory_specification_mb,
        system_memory_reserve_percent=config.system_memory_reserve_percent,
        
        # UI Configuration
        default_window_width=config.default_window_width,
        default_window_height=config.default_window_height,
        minimum_window_width=config.minimum_window_width,
        minimum_window_height=config.minimum_window_height,
        maximize_on_startup=config.maximize_on_startup,
        remember_window_size=config.remember_window_size,
        
        # 3D Viewer - Grid Settings
        grid_visible=config.grid_visible,
        grid_color=config.grid_color,
        grid_size=config.grid_size,
        
        # 3D Viewer - Ground Plane Settings
        ground_visible=config.ground_visible,
        ground_color=config.ground_color,
        ground_offset=config.ground_offset,
        
        # Camera & Interaction Settings
        mouse_sensitivity=config.mouse_sensitivity,
        fps_limit=config.fps_limit,
        zoom_speed=config.zoom_speed,
        pan_speed=config.pan_speed,
        auto_fit_on_load=config.auto_fit_on_load,
        
        # Lighting Settings
        default_light_position_x=config.default_light_position_x,
        default_light_position_y=config.default_light_position_y,
        default_light_position_z=config.default_light_position_z,
        default_light_color_r=config.default_light_color_r,
        default_light_color_g=config.default_light_color_g,
        default_light_color_b=config.default_light_color_b,
        default_light_intensity=config.default_light_intensity,
        default_light_cone_angle=config.default_light_cone_angle,
        enable_fill_light=config.enable_fill_light,
        fill_light_intensity=config.fill_light_intensity,
        
        # Logging Configuration (overridden)
        log_level=log_level,
        enable_file_logging=config.enable_file_logging,
        log_retention_days=config.log_retention_days,
        
        # Thumbnail Generation Configuration
        thumbnail_bg_color=config.thumbnail_bg_color,
        thumbnail_bg_image=config.thumbnail_bg_image,
        thumbnail_material=config.thumbnail_material,
    )
    

    # Create exception handler for startup errors
    exception_handler = ExceptionHandler()

    try:
        # Create and initialize application
        app = Application(config)

        if not app.initialize():
            print("Failed to initialize application")
            return 1

        # Run the application
        exit_code = app.run()
        return exit_code

    except RuntimeError as e:
        # Handle any exceptions during startup
        exception_handler.handle_startup_error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
