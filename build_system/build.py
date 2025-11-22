#!/usr/bin/env python3
"""
Digital Workshop - Automated Build Script

This script automates the entire build and packaging process for the Digital Workshop application,
including PyInstaller packaging and Inno Setup installer creation.
"""

import os
import sys
import shutil
import subprocess
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            SCRIPT_DIR / f'build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Build configuration
BUILD_CONFIG = {
    "app_name": "Digital Workshop",
    "version": "0.1.5",
    "main_script": "src/main.py",
    "spec_file": "build_system/pyinstaller.spec",
    "installer_script": "config/installer.iss",
    "dist_dir": "dist",
    "build_dir": "build",
    "installer_dir": "config",
    "assets_dir": "resources",
}


class ModularBuildManager:
    """Manages modular per-module compilation for Digital Workshop."""

    MODULES = ["core", "pyside6", "vtk", "opencv", "numpy"]

    def __init__(self, config=None):
        """Initialize the modular build manager."""
        self.config = config or BUILD_CONFIG
        self.project_root = PROJECT_ROOT
        self.start_time = datetime.now()
        self.modules_dir = self.project_root / "dist" / "modules"

    def compile_module(self, module_name: str) -> bool:
        """
        Compile a single module.

        Args:
            module_name: Name of the module to compile

        Returns:
            True if successful, False otherwise
        """
        logger.info("Compiling module: %s", module_name)

        spec_file = self.project_root / "config" / f"pyinstaller-{module_name}.spec"
        if not spec_file.exists():
            logger.error("Spec file not found: %s", spec_file)
            return False

        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]

        logger.info("Running command: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=self.project_root, check=False)

        if result.returncode != 0:
            logger.error("PyInstaller build failed for module: %s", module_name)
            return False

        logger.info("Module compiled successfully: %s", module_name)
        return True

    def compile_all_modules(self) -> bool:
        """
        Compile all modules.

        Returns:
            True if all successful, False otherwise
        """
        logger.info("Compiling all modules...")

        all_success = True
        for module in self.MODULES:
            if not self.compile_module(module):
                all_success = False
                logger.error("Failed to compile module: %s", module)

        return all_success

    def generate_manifest(self) -> bool:
        """
        Generate manifest file with module information.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Generating manifest...")

        try:
            manifest = {
                "app_name": self.config["app_name"],
                "version": self.config["version"],
                "build_date": datetime.now().isoformat(),
                "modules": {},
            }

            # Collect module information
            for module in self.MODULES:
                module_dir = self.modules_dir / module

                if module_dir.exists():
                    # Calculate module size
                    total_size = 0
                    for file_path in module_dir.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size

                    manifest["modules"][module] = {
                        "version": self.config["version"],
                        "size_bytes": total_size,
                        "size_mb": round(total_size / (1024 * 1024), 2),
                        "path": str(module_dir.relative_to(self.project_root)),
                    }

            # Save manifest
            manifest_file = self.modules_dir / "manifest.json"
            manifest_file.parent.mkdir(parents=True, exist_ok=True)

            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)

            logger.info("Manifest generated: %s", manifest_file)
            return True

        except Exception as e:
            logger.error("Failed to generate manifest: %s", e)
            return False

    def generate_checksums(self) -> bool:
        """
        Generate checksums for all modules.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Generating checksums...")

        try:
            import hashlib

            checksums = {}

            for module in self.MODULES:
                module_dir = self.modules_dir / module

                if module_dir.exists():
                    hasher = hashlib.sha256()

                    # Hash all files in module
                    for file_path in sorted(module_dir.rglob("*")):
                        if file_path.is_file():
                            with open(file_path, "rb") as f:
                                hasher.update(f.read())

                    checksums[module] = hasher.hexdigest()

            # Save checksums
            checksums_file = self.modules_dir / "checksums.json"
            with open(checksums_file, "w") as f:
                json.dump(checksums, f, indent=2)

            logger.info("Checksums generated: %s", checksums_file)
            return True

        except Exception as e:
            logger.error("Failed to generate checksums: %s", e)
            return False


class BuildManager:
    """Manages the build and packaging process for Digital Workshop."""

    def __init__(self, config=None):
        """Initialize the build manager with configuration."""
        self.config = config or BUILD_CONFIG
        self.project_root = PROJECT_ROOT
        self.start_time = datetime.now()

    def clean_build_dirs(self):
        """Clean previous build directories."""
        logger.info("Cleaning previous build directories...")

        dirs_to_clean = [
            self.project_root / self.config["build_dir"],
            self.project_root / self.config["dist_dir"],
        ]

        for dir_path in dirs_to_clean:
            if dir_path.exists():
                logger.info(f"Removing directory: {dir_path}")
                shutil.rmtree(dir_path)

    def check_dependencies(self):
        """Check if required build tools are available."""
        logger.info("Checking build dependencies...")

        # Check Python
        python_version = sys.version_info
        logger.info(
            f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )

        if python_version < (3, 8):
            raise RuntimeError(
                "Python 3.8 or higher is required for building Digital Workshop"
            )

        # Check PyInstaller
        try:
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info(f"PyInstaller version: {result.stdout.strip()}")
            else:
                raise RuntimeError("PyInstaller not found")
        except Exception as e:
            logger.error(
                "PyInstaller not found. Please install it with: pip install pyinstaller"
            )
            raise

        # Check NSIS (optional warning)
        try:
            result = subprocess.run(["makensis", "/VERSION"], capture_output=True)
            if result.returncode == 0:
                logger.info("NSIS compiler found")
            else:
                logger.warning(
                    "NSIS compiler not found. Installer creation will be skipped."
                )
        except FileNotFoundError:
            logger.warning(
                "NSIS compiler not found. Installer creation will be skipped."
            )
            logger.warning("Please install NSIS from https://nsis.sourceforge.io/")

    def create_app_icon(self):
        """Create a placeholder application icon if it doesn't exist.

        The placeholder uses a CNC/toolpath-inspired design that matches the
        Digital Workshop branding so Start menu and desktop shortcuts look
        consistent out of the box.
        """
        icon_path = self.project_root / "resources" / "icons" / "app_icon.ico"

        if not icon_path.exists():
            logger.info("Creating placeholder application icon...")
            icon_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a simple CNC-themed icon using PIL if available
            try:
                from PIL import Image, ImageDraw, ImageFont

                size = 256
                img = Image.new("RGBA", (size, size), (2, 6, 23, 255))
                draw = ImageDraw.Draw(img)

                # Inner panel to suggest a machine control enclosure
                panel_margin = 32
                draw.rectangle(
                    [
                        panel_margin,
                        panel_margin,
                        size - panel_margin,
                        size - panel_margin,
                    ],
                    fill=(15, 23, 42, 255),
                )

                # Toolpath polyline across the work area
                path_points = [
                    (52, 196),
                    (112, 120),
                    (168, 140),
                    (210, 84),
                ]
                draw.line(path_points, fill=(34, 211, 238, 255), width=6)

                # Spindle/tool block at the end of the path
                draw.rectangle([203, 74, 222, 98], fill=(34, 211, 238, 255))

                # DW monogram for "Digital Workshop" in the lower-left
                text_color = (226, 232, 240, 255)
                try:
                    font = ImageFont.truetype("arial.ttf", 80)
                except Exception:
                    font = ImageFont.load_default()

                draw.text((70, 72), "D", font=font, fill=text_color)
                draw.text((108, 136), "W", font=font, fill=text_color)

                # Save as ICO with multiple sizes
                img.save(
                    icon_path,
                    format="ICO",
                    sizes=[
                        (256, 256),
                        (128, 128),
                        (64, 64),
                        (48, 48),
                        (32, 32),
                        (16, 16),
                    ],
                )
                logger.info(f"Created placeholder icon: {icon_path}")
            except ImportError:
                logger.warning("PIL not available. Skipping icon creation.")
                logger.warning(
                    "Please create app_icon.ico manually in resources/icons/"
                )
            except Exception as e:
                logger.error(f"Failed to create icon: {e}")

    def run_pyinstaller(self):
        """Run PyInstaller to create the executable."""
        logger.info("Running PyInstaller...")

        spec_file = self.project_root / self.config["spec_file"]
        if not spec_file.exists():
            raise RuntimeError(f"PyInstaller spec file not found: {spec_file}")

        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            raise RuntimeError("PyInstaller build failed")

        logger.info("PyInstaller build completed successfully")

    def check_installer_assets(self):
        """Check if required installer assets exist."""
        logger.info("Checking installer assets...")

        required_assets = ["license.txt", "readme.txt"]

        missing_assets = []
        for asset in required_assets:
            asset_path = self.project_root / self.config["assets_dir"] / asset
            if not asset_path.exists():
                missing_assets.append(asset)

        if missing_assets:
            logger.warning(f"Missing installer assets: {missing_assets}")
            logger.warning("Please create these files in installer/assets/ directory")
            return False

        return True

    def create_installer(self):
        """Create the Inno Setup installer."""
        logger.info("Creating Inno Setup installer...")

        # Check if Inno Setup is available
        inno_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
        ]

        iscc_exe = None
        for path in inno_paths:
            if Path(path).exists():
                iscc_exe = path
                break

        if not iscc_exe:
            try:
                result = subprocess.run(
                    ["where", "ISCC.exe"], capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    iscc_exe = result.stdout.strip().split("\n")[0]
            except Exception:
                pass

        if not iscc_exe:
            logger.error(
                "Inno Setup compiler (ISCC.exe) not found. Cannot create installer."
            )
            logger.info(
                "Please install Inno Setup from: https://jrsoftware.org/isdl.php"
            )
            return False

        # Check installer assets
        if not self.check_installer_assets():
            logger.error("Installer assets missing. Cannot create installer.")
            return False

        installer_script = self.project_root / self.config["installer_script"]
        if not installer_script.exists():
            logger.error(f"Installer script not found: {installer_script}")
            return False

        cmd = [iscc_exe, str(installer_script)]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.error("Inno Setup installer creation failed")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        # Inno Setup outputs to Output directory by default
        output_dir = self.project_root / "Output"
        if output_dir.exists():
            for installer in output_dir.glob("*.exe"):
                dest = self.project_root / self.config["dist_dir"] / installer.name
                shutil.move(str(installer), str(dest))
                logger.info(f"Moved installer to {dest}")
            # Clean up Output directory
            shutil.rmtree(output_dir)
        else:
            logger.warning("Output directory not found after Inno Setup compilation")
            return False

        logger.info("NSIS installer created successfully")
        return True

    def run_tests(self):
        """Run the test suite to ensure quality."""
        logger.info("Running test suite...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("All tests passed")
                return True
            else:
                logger.warning("Some tests failed")
                logger.warning(result.stdout)
                logger.warning(result.stderr)
                return False
        except Exception as e:
            logger.warning(f"Failed to run tests: {e}")
            return False

    def create_build_report(self):
        """Create a build report with summary information."""
        logger.info("Creating build report...")

        end_time = datetime.now()
        duration = end_time - self.start_time

        report = {
            "build_date": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "app_name": self.config["app_name"],
            "version": self.config["version"],
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "success": True,
        }

        # Check if executable was created
        exe_path = (
            self.project_root
            / self.config["dist_dir"]
            / self.config["app_name"]
            / f"{self.config['app_name']}.exe"
        )
        report["executable_created"] = exe_path.exists()

        if exe_path.exists():
            exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            report["executable_size_mb"] = round(exe_size, 2)

        # Check if installer was created
        installer_path = (
            self.project_root
            / self.config["dist_dir"]
            / f"{self.config['app_name']}-Setup-{self.config['version']}.exe"
        )
        report["installer_created"] = installer_path.exists()

        if installer_path.exists():
            installer_size = installer_path.stat().st_size / (1024 * 1024)  # Size in MB
            report["installer_size_mb"] = round(installer_size, 2)

        # Save report
        report_path = self.project_root / self.config["dist_dir"] / "build_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Build report saved to: {report_path}")

        # Print summary
        logger.info("=" * 50)
        logger.info("BUILD SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Application: {report['app_name']} v{report['version']}")
        logger.info(f"Build duration: {duration.total_seconds():.2f} seconds")
        logger.info(
            f"Executable created: {'Yes' if report['executable_created'] else 'No'}"
        )
        if report["executable_created"]:
            logger.info(f"Executable size: {report['executable_size_mb']} MB")
        logger.info(
            f"Installer created: {'Yes' if report['installer_created'] else 'No'}"
        )
        if report["installer_created"]:
            logger.info(f"Installer size: {report['installer_size_mb']} MB")
        logger.info("=" * 50)

        return report

    def build(self, run_tests_flag=False, create_installer_flag=True):
        """Run the complete build process."""
        logger.info(
            f"Starting build for {self.config['app_name']} v{self.config['version']}"
        )

        try:
            # Clean previous builds
            self.clean_build_dirs()

            # Check dependencies
            self.check_dependencies()

            # Run tests if requested
            if run_tests_flag:
                if not self.run_tests():
                    logger.warning("Tests failed but continuing with build")

            # Create app icon if needed
            self.create_app_icon()

            # Run PyInstaller
            self.run_pyinstaller()

            # Create installer if requested
            if create_installer_flag:
                installer_success = self.create_installer()
                if not installer_success:
                    logger.error(
                        "Installer creation failed - build will continue but installer will not be available"
                    )

            # Create build report
            report = self.create_build_report()

            logger.info("Build completed successfully!")
            return report

        except Exception as e:
            logger.error(f"Build failed: {e}")
            # Create failure report
            report = {
                "build_date": datetime.now().isoformat(),
                "app_name": self.config["app_name"],
                "version": self.config["version"],
                "success": False,
                "error": str(e),
            }

            report_path = (
                self.project_root / self.config["dist_dir"] / "build_report.json"
            )
            report_path.parent.mkdir(exist_ok=True)
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            raise


def main():
    """Main function to run the build script."""
    parser = argparse.ArgumentParser(description="Build Digital Workshop application")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument(
        "--no-installer", action="store_true", help="Skip creating installer"
    )
    parser.add_argument(
        "--clean-only", action="store_true", help="Only clean build directories"
    )
    parser.add_argument("--config", help="Path to build configuration file")

    args = parser.parse_args()

    # Load custom configuration if provided
    config = BUILD_CONFIG
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)

    # Initialize build manager
    build_manager = BuildManager(config)

    # Handle clean-only option
    if args.clean_only:
        build_manager.clean_build_dirs()
        logger.info("Build directories cleaned")
        return

    # Run the build process
    try:
        build_manager.build(
            run_tests_flag=not args.no_tests,
            create_installer_flag=not args.no_installer,
        )
    except Exception as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
