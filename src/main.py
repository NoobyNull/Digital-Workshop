#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It uses the new modular Application class for initialization and execution.
"""

import sys
import os
import argparse

# Add the parent directory to the Python path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.core.application import Application
from src.core.application_config import ApplicationConfig
from src.core.exception_handler import ExceptionHandler


def parse_arguments():
    """Parse command-line arguments for the application.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="3D-MM (3D Model Manager) - Professional 3D Model Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                    # Run with default INFO logging
  python src/main.py --debug            # Run with DEBUG logging (verbose)
  python src/main.py --quiet            # Run with WARNING logging only
  python src/main.py --silent           # Run with ERROR logging only
        """
    )

    # Logging level arguments (mutually exclusive)
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging (verbose output)"
    )
    log_group.add_argument(
        "--quiet",
        action="store_true",
        help="Enable WARNING logging only (less verbose)"
    )
    log_group.add_argument(
        "--silent",
        action="store_true",
        help="Enable ERROR logging only (minimal output)"
    )

    return parser.parse_args()


def get_log_level_from_args(args) -> str:
    """Determine log level from command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR)
    """
    if args.debug:
        return "DEBUG"
    elif args.quiet:
        return "WARNING"
    elif args.silent:
        return "ERROR"
    else:
        return "INFO"  # Default to INFO


def main():
    """Main function to start the 3D-MM application."""
    # Parse command-line arguments
    args = parse_arguments()

    # Get log level from arguments
    log_level = get_log_level_from_args(args)

    # Create application configuration with the determined log level
    config = ApplicationConfig.get_default()
    # Override log level from command-line arguments
    config = ApplicationConfig(
        name=config.name,
        display_name=config.display_name,
        version=config.version,
        build_number=config.build_number,
        organization_name=config.organization_name,
        organization_domain=config.organization_domain,
        app_data_subdir=config.app_data_subdir,
        enable_hardware_acceleration=config.enable_hardware_acceleration,
        enable_high_dpi=config.enable_high_dpi,
        enable_performance_monitoring=config.enable_performance_monitoring,
        max_memory_usage_mb=config.max_memory_usage_mb,
        model_cache_size_mb=config.model_cache_size_mb,
        use_manual_memory_override=config.use_manual_memory_override,
        manual_memory_override_mb=config.manual_memory_override_mb,
        min_memory_specification_mb=config.min_memory_specification_mb,
        system_memory_reserve_percent=config.system_memory_reserve_percent,
        default_window_width=config.default_window_width,
        default_window_height=config.default_window_height,
        minimum_window_width=config.minimum_window_width,
        minimum_window_height=config.minimum_window_height,
        log_level=log_level,
        enable_file_logging=config.enable_file_logging,
        log_retention_days=config.log_retention_days,
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
