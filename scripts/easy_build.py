#!/usr/bin/env python3
"""
Easy build script for Digital Workshop
Simplifies the build process and provides helpful shortcuts
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse


def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def check_dependencies():
    """Check if all required dependencies are available."""
    print("🔍 Checking dependencies...")

    # Check Python version
    version = sys.version_info
    if version.major < 3 or version.minor < 8:
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")

    # Check key modules
    required_modules = ["PySide6", "vtk", "numpy"]
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            print(f"❌ {module} not found - run: pip install -r requirements.txt")
            return False

    return True


def quick_build():
    """Quick build without tests."""
    print("🚀 Quick Build Mode")

    if not check_dependencies():
        return False

    # Clean previous builds
    if not run_command("python build_system/build_exe.py", "Cleaning and building"):
        return False

    # Verify build
    exe_path = Path("dist") / "Digital Workshop" / "Digital Workshop.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 / 1024)
        print(f"✅ Build successful! EXE size: {size_mb:.1f} MB")
        print(f"📍 Location: {exe_path.absolute()}")
        return True
    else:
        print("❌ Build failed - EXE not found")
        return False


def full_build():
    """Full build with tests."""
    print("🔬 Full Build Mode (with tests)")

    if not check_dependencies():
        return False

    # Run tests first
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️ Tests failed, but continuing with build...")

    # Build
    if not run_command("python build_system/build_exe.py", "Building application"):
        return False

    # Verify build
    exe_path = Path("dist") / "Digital Workshop" / "Digital Workshop.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 / 1024)
        print(f"✅ Full build successful! EXE size: {size_mb:.1f} MB")
        print(f"📍 Location: {exe_path.absolute()}")
        return True
    else:
        print("❌ Build failed - EXE not found")
        return False


def setup_development():
    """Setup development environment."""
    print("🛠️ Setting up development environment")

    # Install dependencies
    if not run_command(
        "pip install -r requirements.txt -r requirements-dev.txt",
        "Installing dependencies",
    ):
        return False

    # Setup pre-commit hooks (if available)
    if Path(".pre-commit-config.yaml").exists():
        run_command("pre-commit install", "Setting up pre-commit hooks")

    print("✅ Development environment ready!")
    return True


def clean_all():
    """Clean all build artifacts."""
    print("🧹 Cleaning all artifacts")

    dirs_to_clean = ["build", "dist", "__pycache__", ".pytest_cache"]
    files_to_clean = ["*.pyc", "*.spec.cache"]

    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            run_command(f"rmdir /s /q {dir_name}", f"Removing {dir_name}")

    for pattern in files_to_clean:
        run_command(f"del /s /q {pattern}", f"Removing {pattern}")

    print("✅ Clean completed!")
    return True


def show_build_info():
    """Show current build information."""
    print("📊 Build Information")
    print("=" * 40)

    # Check if EXE exists
    exe_path = Path("dist") / "Digital Workshop" / "Digital Workshop.exe"
    if exe_path.exists():
        stat = exe_path.stat()
        size_mb = stat.st_size / (1024 / 1024)
        print(f"EXE Size: {size_mb:.1f} MB")
        print(f"Last Modified: {stat.st_mtime}")
        print(f"Location: {exe_path.absolute()}")
    else:
        print("No built EXE found")

    # Check git status
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
        )
        branch = result.stdout.strip()
        print(f"Current Branch: {branch}")

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
        )
        commit = result.stdout.strip()
        print(f"Current Commit: {commit}")
    except:
        print("Git information not available")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Easy build helper for Digital Workshop"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Quick build
    subparsers.add_parser("quick", help="Quick build without tests")

    # Full build
    subparsers.add_parser("full", help="Full build with tests")

    # Setup
    subparsers.add_parser("setup", help="Setup development environment")

    # Clean
    subparsers.add_parser("clean", help="Clean all build artifacts")

    # Info
    subparsers.add_parser("info", help="Show build information")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print("Digital Workshop - Easy Build Helper")
    print("=" * 40)

    if args.command == "quick":
        success = quick_build()
    elif args.command == "full":
        success = full_build()
    elif args.command == "setup":
        success = setup_development()
    elif args.command == "clean":
        success = clean_all()
    elif args.command == "info":
        success = show_build_info()
        return  # Info doesn't need success message
    else:
        print(f"Unknown command: {args.command}")
        success = False

    if success:
        print("\n✅ Command completed successfully!")
    else:
        print("\n❌ Command failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
