#!/usr/bin/env python3
"""
Digital Workshop (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It uses the new modular Application class for initialization and execution.
"""

import argparse
import dataclasses
import sys
import os

# Add the parent directory to the Python path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.core.application import Application
from src.core.application_config import ApplicationConfig
from src.core.exception_handler import ExceptionHandler
from src.core.logging_config import get_logger


def parse_arguments():
    """Parse command line arguments for the application.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Digital Workshop (3D Model Manager) - Manage and view 3D models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Start with INFO logging (default)
  python main.py --debug                   # Start with DEBUG logging
  python main.py --log-level DEBUG         # Start with DEBUG logging
  python main.py --log-level INFO          # Start with INFO logging
  python main.py --log-level WARNING       # Start with WARNING logging
  python main.py --log-console             # Enable console logging (default: file only)
  python main.py --log-human               # Use human-readable log format (default: JSON)
  python main.py --debug --log-console     # DEBUG logging to both file and console
  python main.py --debug --log-human       # DEBUG logging with human-readable format
  python main.py --mem-only                # Development only: Run entire database in memory
        """,
    )

    # Log level arguments
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "--debug",
        action="store_const",
        const="DEBUG",
        dest="log_level",
        help="Enable DEBUG level logging (verbose output)",
    )
    log_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    # Console logging argument
    parser.add_argument(
        "--log-console",
        action="store_true",
        help="Enable console logging (default: logs go to file only, activities always shown)",
    )

    # Human-readable logging argument
    parser.add_argument(
        "--log-human",
        action="store_true",
        help="Use human-readable log format instead of JSON (default: JSON format)",
    )

    # Development-only: In-memory database
    parser.add_argument(
        "--mem-only",
        action="store_true",
        help="[DEVELOPMENT ONLY] Run entire database in memory (data not persisted)",
    )

    return parser.parse_args()


def main():
    """Main function to start the Digital Workshop application."""
    logger = get_logger(__name__)
    logger.info("Digital Workshop application starting")

    args = parse_arguments()
    log_level = args.log_level if args.log_level is not None else "INFO"
    logger.info(f"Log level set to: {log_level}")

    # Set environment variable for in-memory database if --mem-only flag is used
    if args.mem_only:
        os.environ["USE_MEMORY_DB"] = "true"
        logger.warning(
            "⚠️  DEVELOPMENT MODE: Running with in-memory database only - data will NOT be persisted!"
        )

    config = ApplicationConfig.get_default()
    config = dataclasses.replace(
        config,
        log_level=log_level,
        enable_console_logging=args.log_console,
        log_human_readable=args.log_human,
    )

    exception_handler = ExceptionHandler()
    app = None

    try:
        # Create and initialize application
        app = Application(config)

        if not app.initialize():
            logger.error("Application initialization failed")
            # Cleanup on initialization failure
            if app:
                app.cleanup()
            return 1

        # Run the application
        logger.info("Application initialized successfully, starting main loop")
        exit_code = app.run()
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130  # Standard Unix exit code for Ctrl+C

    except (OSError, IOError) as e:
        logger.error(f"File system error: {str(e)}")
        exception_handler.handle_startup_error(e)
        return 1

    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        exception_handler.handle_startup_error(e)
        return 1

    except Exception as e:
        # Catch all other exceptions
        logger.error(f"Application startup failed: {str(e)}", exc_info=True)
        exception_handler.handle_startup_error(e)
        return 1

    finally:
        # Ensure cleanup happens
        if app:
            try:
                app.cleanup()
            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")


if __name__ == "__main__":
    sys.exit(main())
