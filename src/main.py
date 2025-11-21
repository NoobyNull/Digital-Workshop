#!/usr/bin/env python3
"""
Digital Workshop (3D Model Manager) - Main Entry Point

This is the main entry point for the 3D Model Manager application.
It uses the new modular Application class for initialization and execution.
"""

import argparse
import dataclasses
import os
import sys
import time

try:  # Windows-only, used for CLI nuclear reset countdown
    import msvcrt  # type: ignore[import]
except ImportError:  # pragma: no cover - non-Windows platforms
    msvcrt = None  # type: ignore[assignment]

from src.core.application import Application
from src.core.application_config import ApplicationConfig
from src.core.exception_handler import ExceptionHandler
from src.core.logging_config import LoggingProfile, get_logger, setup_logging
from src.core.nuclear_reset import NuclearReset


def parse_arguments() -> None:
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
        help="Use human-readable log format instead of JSON (default: JSON format, implies --log-console)",
    )

    # Development-only: In-memory database
    parser.add_argument(
        "--mem-only",
        action="store_true",
        help="[DEVELOPMENT ONLY] Run entire database in memory (data not persisted)",
    )

    # Nuclear reset (CLI shortcut)
    parser.add_argument(
        "--nuke",
        action="store_true",
        help="NUCLEAR RESET: destroy ALL application data after a 5 second cancel window",
    )
    parser.add_argument(
        "--nuke-no-backup",
        action="store_true",
        help=(
            "NUKE: do NOT create a final backup before deletion "
            "(maximum risk, faster)"
        ),
    )
    parser.add_argument(
        "--nuke-exec",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    # Settings import/export
    parser.add_argument(
        "--export-settings",
        metavar="OUTFILE",
        help="Export all QSettings values to the specified JSON file and exit",
    )
    parser.add_argument(
        "--import-settings",
        metavar="INFILE",
        help="Import QSettings values from the specified JSON file and exit (no UI launch)",
    )

    return parser.parse_args()


def _build_logging_profile(args, base_level: str) -> LoggingProfile:
    """Construct the runtime logging profile from CLI arguments."""
    enable_console = args.log_console or args.log_human
    return LoggingProfile(
        log_level=base_level,
        enable_console=enable_console,
        human_readable=args.log_human,
    )


def _confirm_nuclear_reset_with_timeout(timeout_seconds: int = 5) -> bool:
    """Display a warning for nuclear reset and allow cancellation via any key.

    Returns:
        True if the reset should proceed, False if it was cancelled.
    """
    print("=" * 80)
    print("⚠️  NUCLEAR RESET REQUESTED ⚠️")
    print("=" * 80)
    print(
        "This will permanently delete ALL Digital Workshop application data, including:"
    )
    print("  • Databases")
    print("  • Settings / registry entries")
    print("  • Cache, logs, thumbnails, and temp files")
    print("  • All AppData directories used by the application")
    print()
    print(f"Press ANY KEY within {timeout_seconds} seconds to CANCEL.")
    print("If no key is pressed, the nuclear reset will proceed...", flush=True)

    end_time = time.time() + timeout_seconds

    if msvcrt is not None:
        while time.time() < end_time:
            if msvcrt.kbhit():
                msvcrt.getch()
                print("\nNuclear reset cancelled by user.")
                return False
            time.sleep(0.1)
    else:
        # Non-Windows fallback: simple timed delay without key detection
        time.sleep(timeout_seconds)

    print("\nProceeding with nuclear reset...")
    return True


def _init_qsettings_for_cli(config: ApplicationConfig):
    """Initialize QSettings for CLI-only operations (no UI launch)."""
    from pathlib import Path
    from PySide6.QtCore import QCoreApplication, QSettings

    if QCoreApplication.instance() is None:
        QCoreApplication([])
    QCoreApplication.setOrganizationName(config.organization_name)
    QCoreApplication.setApplicationName(config.name)
    if getattr(config, "organization_domain", None):
        QCoreApplication.setOrganizationDomain(config.organization_domain)

    if os.getenv("USE_MEMORY_DB", "false").lower() == "true":
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "digital_workshop_dev"
        temp_dir.mkdir(parents=True, exist_ok=True)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(temp_dir))
        QSettings.setDefaultFormat(QSettings.IniFormat)

    return QSettings()


def _export_settings(config: ApplicationConfig, outfile: str) -> int:
    """Export all QSettings keys to a JSON file."""
    import json
    from pathlib import Path

    try:
        settings = _init_qsettings_for_cli(config)
        data = {key: settings.value(key) for key in settings.allKeys()}
        Path(outfile).parent.mkdir(parents=True, exist_ok=True)
        Path(outfile).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Wrote {len(data)} settings to {outfile}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to export settings: {exc}")
        return 1


def _import_settings(config: ApplicationConfig, infile: str) -> int:
    """Import QSettings keys from a JSON file."""
    import json
    from pathlib import Path

    try:
        payload = json.loads(Path(infile).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to read settings file: {exc}")
        return 1

    try:
        settings = _init_qsettings_for_cli(config)
        for key, value in payload.items():
            settings.setValue(key, value)
        settings.sync()
        print(f"Imported {len(payload)} settings from {infile}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to import settings: {exc}")
        return 1


def main() -> None:
    """Main function to start the Digital Workshop application."""
    args = parse_arguments()
    log_level = args.log_level if args.log_level is not None else "INFO"

    # Special case: background nuclear reset executor
    if getattr(args, "nuke_exec", False):
        # Use a minimal logging profile that avoids locking application data directories
        from tempfile import gettempdir

        temp_log_dir = os.path.join(gettempdir(), "DigitalWorkshop_NukeLogs")
        nuke_profile = LoggingProfile(
            log_level=log_level,
            enable_console=True,
            human_readable=True,
            log_dir=temp_log_dir,
        )
        setup_logging(profile=nuke_profile)
        logger = get_logger(__name__)

        create_backup = not getattr(args, "nuke_no_backup", False)
        logger.warning(
            "Executing nuclear reset in background worker (backup %s)",
            "DISABLED" if not create_backup else "ENABLED",
        )

        # Small delay so any launching process can fully exit before deletion begins
        time.sleep(2.0)

        reset_handler = NuclearReset()
        results = reset_handler.execute_nuclear_reset(create_backup=create_backup)

        if results.get("success"):
            logger.warning(
                "Nuclear reset completed successfully. Directories deleted: %s, files deleted: %s",
                results.get("directories_deleted", 0),
                results.get("files_deleted", 0),
            )
            backup_info = "YES" if results.get("backup_created") else "NO"
            logger.warning("Nuclear reset backup created: %s", backup_info)
            if results.get("backup_path"):
                logger.warning("Nuclear reset backup path: %s", results["backup_path"])
            return 0

        errors = results.get("errors") or []
        if errors:
            logger.error("Nuclear reset failed with errors: %s", "; ".join(errors))
        else:
            logger.error("Nuclear reset failed for unknown reasons.")
        return 1

    # Normal application startup logging
    profile = _build_logging_profile(args, log_level)
    setup_logging(profile=profile)

    logger = get_logger(__name__)
    logger.info("Digital Workshop application starting")
    logger.info("Log level set to: %s", log_level)

    # Handle nuclear reset shortcut before starting the application
    if getattr(args, "nuke", False) or getattr(args, "nuke_no_backup", False):
        create_backup = not getattr(args, "nuke_no_backup", False)

        if not _confirm_nuclear_reset_with_timeout(5):
            logger.warning("Nuclear reset requested but cancelled by user.")
            return 0

        logger.warning(
            "Executing nuclear reset directly (backup %s); application will not launch.",
            "DISABLED" if not create_backup else "ENABLED",
        )

        reset_handler = NuclearReset()
        results = reset_handler.execute_nuclear_reset(create_backup=create_backup)

        if results.get("success"):
            logger.warning(
                "Nuclear reset completed successfully. Directories deleted: %s, files deleted: %s",
                results.get("directories_deleted", 0),
                results.get("files_deleted", 0),
            )
            backup_info = "YES" if results.get("backup_created") else "NO"
            logger.warning("Nuclear reset backup created: %s", backup_info)
            if results.get("backup_path"):
                logger.warning("Nuclear reset backup path: %s", results["backup_path"])
            return 0

        errors = results.get("errors") or []
        if errors:
            logger.error("Nuclear reset failed with errors: %s", "; ".join(errors))
        else:
            logger.error("Nuclear reset failed for unknown reasons.")
        return 1

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
        enable_console_logging=profile.enable_console,
        log_human_readable=args.log_human,
        logging_profile=profile,
    )

    # Handle settings import/export before launching the UI
    if args.export_settings:
        return _export_settings(config, args.export_settings)
    if args.import_settings:
        return _import_settings(config, args.import_settings)

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
        logger.info("Application exited with code: %s", exit_code)
        return exit_code

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130  # Standard Unix exit code for Ctrl+C

    except (OSError, IOError) as e:
        logger.error("File system error: %s", str(e))
        exception_handler.handle_startup_error(e)
        return 1

    except ImportError as e:
        logger.error("Missing dependency: %s", str(e))
        exception_handler.handle_startup_error(e)
        return 1

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Catch all other exceptions
        logger.error("Application startup failed: %s", str(e), exc_info=True)
        exception_handler.handle_startup_error(e)
        return 1

    finally:
        # Ensure cleanup happens
        if app:
            try:
                app.cleanup()
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                logger.error("Cleanup failed: %s", str(e))


if __name__ == "__main__":
    sys.exit(main())
