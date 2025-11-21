#!/usr/bin/env python3
"""
Digital Workshop (3D Model Manager) - Quick Start Script

This script helps users quickly set up and run the Digital Workshop application
with automatic dependency checking and circular import fixes.
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version < (3, 8):
        print(
            f"Error: Python 3.8 or higher is required. You have Python {version.major}.{version.minor}.{version.micro}"
        )
        return False
    elif (version.major, version.minor) >= (3, 13):
        print(
            f"Warning: Python {version.major}.{version.minor}.{version.micro} detected. Digital Workshop is tested with Python 3.8-3.12"
        )
        try:
            response = input("Continue anyway? (y/n): ")
            if response.lower() != "y":
                return False
        except EOFError:
            # Handle non-interactive environments
            print(
                "Non-interactive environment detected. Continuing with Python 3.13+..."
            )

    print(f"[OK] Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        ("PySide6", "PySide6>=6.0.0"),
        ("vtk", "VTK>=9.2.0"),
        ("sqlite3", "SQLite (built-in)"),
    ]

    optional_packages = [
        ("numpy", "NumPy 1.24.0+ (for geometry processing)"),
        ("lxml", "lxml 4.6.0+ (for advanced format parsing)"),
    ]

    missing_required = []
    missing_optional = []

    print("Checking dependencies...")

    for package_name, description in required_packages:
        if package_name == "sqlite3":
            # sqlite3 is built-in with Python
            print(f"[OK] {description}")
            continue

        spec = importlib.util.find_spec(package_name)
        if spec is None:
            missing_required.append(description)
        else:
            print(f"[OK] {description}")

    for package_name, description in optional_packages:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            missing_optional.append(description)
            print(f"○ {description} (optional)")
        else:
            print(f"[OK] {description}")

    if missing_required:
        print("\nMissing required dependencies:")
        for package in missing_required:
            print(f"  - {package}")

        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")

        try:
            install = input("\nInstall missing dependencies now? (y/n): ")
            if install.lower() == "y":
                try:
                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-r",
                            "requirements.txt",
                        ],
                        check=True,
                    )
                    print("Dependencies installed successfully!")
                    return True
                except subprocess.CalledProcessError:
                    print(
                        "Failed to install dependencies. Please install them manually."
                    )
                    return False
            else:
                return False
        except EOFError:
            # Handle non-interactive environments
            print(
                "\nNon-interactive environment detected. Please install missing dependencies manually:"
            )
            print("  pip install -r requirements.txt")
            return False

    if missing_optional:
        print("\nSome optional dependencies are missing:")
        for package in missing_optional:
            print(f"  - {package}")
        print("These are not required for basic functionality.")

    return True


def fix_circular_imports():
    """Check and fix circular import issues."""
    base_parser_path = Path("src/parsers/base_parser.py")

    if not base_parser_path.exists():
        print("Error: src/parsers/base_parser.py not found")
        return False

    with open(base_parser_path, "r") as f:
        content = f.read()

    if "from core.model_cache import get_model_cache, CacheLevel" in content:
        print("Circular import issue detected in base_parser.py")

        try:
            fix = input("Fix circular imports automatically? (y/n): ")
            if fix.lower() == "y":
                try:
                    subprocess.run(
                        [sys.executable, "fix_circular_imports.py"], check=True
                    )
                    print("Circular imports fixed successfully!")
                    return True
                except subprocess.CalledProcessError:
                    print("Failed to fix circular imports automatically.")
                    return False
            else:
                print(
                    "Please fix circular imports manually before running the application."
                )
                return False
        except EOFError:
            # Handle non-interactive environments
            print(
                "\nNon-interactive environment detected. Please fix circular imports manually before running the application."
            )
            return False

    print("[OK] No circular import issues detected")
    return True


def print_startup_summary() -> None:
    """Print a brief, dynamic startup summary before launching the Qt application.

    This includes key paths, database status, and log rotation settings so the
    quick-start output reflects the actual runtime environment instead of only
    static checks.
    """
    try:
        # Ensure src is on sys.path so we can import application modules
        src_dir = Path("src")
        if not src_dir.exists():
            return

        src_path = str(src_dir.resolve())
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from src.core.path_manager import (
            get_cache_directory,
            get_log_directory,
            get_data_directory,
            get_database_file,
            ensure_directories_exist,
        )
        from src.core.version_manager import get_display_version
        from src.core.installation_detector import get_installation_type
        from src.core.database_manager import get_database_manager
        from src.core.logging_config import LoggingProfile

        ensure_directories_exist()

        version = get_display_version()
        installation_type = get_installation_type().value

        print("\nEnvironment summary:")
        print(f"[INFO] Version: {version} ({installation_type})")

        cache_dir = get_cache_directory()
        log_dir = get_log_directory()
        data_dir = get_data_directory()
        db_path = get_database_file()

        print(f"[PATH] Cache directory : {cache_dir}")
        print(f"[PATH] Log directory   : {log_dir}")
        print(f"[PATH] Data directory  : {data_dir}")

        if db_path.exists():
            size_bytes = db_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
            print(f"[DB] {db_path.name} : exists ({size_mb:.2f} MB)")
        else:
            print(f"[DB] {db_path.name} : not found (will be created on first use)")

        # Touch database to ensure schema is initialized and gather basic stats
        try:
            db_manager = get_database_manager()
            stats = db_manager.get_database_stats()
            model_count = stats.get("model_count", 0)
            total_mb = stats.get("total_size_mb", 0)
            print(f"[DB] Models: {model_count} | Total size: {total_mb} MB")
        except Exception as db_exc:  # pragma: no cover - best-effort diagnostics
            print(f"[DB] Could not retrieve database stats: {db_exc}")

        profile = LoggingProfile()
        max_mb = profile.max_bytes / (1024 * 1024)
        print(
            f"[LOG] Rotation: up to {max_mb:.0f} MB per file, keep last {profile.backup_count} files"
        )

    except Exception as exc:  # pragma: no cover - defensive only
        print(f"[WARN] Failed to collect environment summary: {exc}")


def run_application():
    """Run the Digital Workshop application."""
    print("\nStarting Digital Workshop application...")

    try:
        # Add src directory to Python path so imports work
        src_dir = Path("src")

        if not src_dir.exists():
            print("Error: src directory not found")
            return False

        # Add src to path if not already there
        src_path = str(src_dir.resolve())
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Print dynamic startup/runtime information before Qt takes over
        print_startup_summary()

        # Import and run main() from src.main
        # This directly calls the main function instead of using subprocess
        from src.main import main as app_main

        # Run the application - main() returns an exit code
        exit_code = app_main()

        # Exit with the same code as the application
        sys.exit(exit_code if exit_code is not None else 0)

    except ImportError as e:
        print(f"Failed to import application: {e}")
        print("Make sure all dependencies are installed.")
        return False
    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        print(f"Failed to run application: {e}")
        return False


def main():
    """Main function to check and run the application."""
    print("Digital Workshop (3D Model Manager) - Quick Start")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print(
            "Error: src directory not found. Please run this script from the project root."
        )
        sys.exit(1)

    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 2: Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Step 3: Fix circular imports
    if not fix_circular_imports():
        sys.exit(1)

    # Step 4: Run the application
    if not run_application():
        sys.exit(1)


if __name__ == "__main__":
    main()
