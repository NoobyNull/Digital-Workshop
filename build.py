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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Build configuration
BUILD_CONFIG = {
    "app_name": "Digital Workshop",
    "version": "1.0.1",
    "main_script": "src/main.py",
    "spec_file": "pyinstaller.spec",
    "installer_script": "installer/inno_setup.iss",
    "dist_dir": "dist",
    "build_dir": "build",
    "installer_dir": "installer",
    "assets_dir": "installer/assets"
}

class BuildManager:
    """Manages the build and packaging process for Digital Workshop."""
    
    def __init__(self, config=None):
        """Initialize the build manager with configuration."""
        self.config = config or BUILD_CONFIG
        self.project_root = Path.cwd()
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
        logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version < (3, 8):
            raise RuntimeError("Python 3.8 or higher is required for building Digital Workshop")
        
        # Check PyInstaller
        try:
            result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"PyInstaller version: {result.stdout.strip()}")
            else:
                raise RuntimeError("PyInstaller not found")
        except Exception as e:
            logger.error("PyInstaller not found. Please install it with: pip install pyinstaller")
            raise
        
        # Check Inno Setup (optional warning)
        try:
            result = subprocess.run(["iscc", "/?"], capture_output=True)
            if result.returncode == 0:
                logger.info("Inno Setup compiler found")
            else:
                logger.warning("Inno Setup compiler not found. Installer creation will be skipped.")
        except FileNotFoundError:
            logger.warning("Inno Setup compiler not found. Installer creation will be skipped.")
            logger.warning("Please install Inno Setup from https://jrsoftware.org/isinfo.php")
    
    def create_app_icon(self):
        """Create a placeholder application icon if it doesn't exist."""
        icon_path = self.project_root / "resources" / "icons" / "app_icon.ico"
        
        if not icon_path.exists():
            logger.info("Creating placeholder application icon...")
            icon_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a simple placeholder icon using PIL if available
            try:
                from PIL import Image, ImageDraw
                
                # Create a simple 256x256 icon
                img = Image.new('RGBA', (256, 256), (0, 123, 255, 255))
                draw = ImageDraw.Draw(img)
                
                # Draw a simple 3D cube shape
                draw.rectangle([50, 50, 206, 206], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                draw.polygon([(50, 50), (20, 20), (176, 20), (206, 50)], fill=(200, 200, 200, 255), outline=(0, 0, 0, 255))
                draw.polygon([(206, 50), (176, 20), (176, 176), (206, 206)], fill=(150, 150, 150, 255), outline=(0, 0, 0, 255))
                
                # Save as ICO with multiple sizes
                img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                logger.info(f"Created placeholder icon: {icon_path}")
            except ImportError:
                logger.warning("PIL not available. Skipping icon creation.")
                logger.warning("Please create app_icon.ico manually in resources/icons/")
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
        
        required_assets = [
            "license.txt",
            "readme.txt"
        ]
        
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
        try:
            result = subprocess.run(["iscc", "/?"], capture_output=True)
            if result.returncode != 0:
                logger.warning("Inno Setup compiler not available. Skipping installer creation.")
                return False
        except FileNotFoundError:
            logger.warning("Inno Setup compiler not found. Skipping installer creation.")
            return False
        
        # Check installer assets
        if not self.check_installer_assets():
            logger.warning("Installer assets missing. Skipping installer creation.")
            return False
        
        installer_script = self.project_root / self.config["installer_script"]
        if not installer_script.exists():
            logger.warning(f"Installer script not found: {installer_script}")
            return False
        
        cmd = ["iscc", str(installer_script)]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode != 0:
            logger.error("Inno Setup installer creation failed")
            return False
        
        logger.info("Inno Setup installer created successfully")
        return True
    
    def run_tests(self):
        """Run the test suite to ensure quality."""
        logger.info("Running test suite...")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            
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
            "success": True
        }
        
        # Check if executable was created
        exe_path = self.project_root / self.config["dist_dir"] / f"{self.config['app_name']}.exe"
        report["executable_created"] = exe_path.exists()
        
        if exe_path.exists():
            exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            report["executable_size_mb"] = round(exe_size, 2)
        
        # Check if installer was created
        installer_path = self.project_root / self.config["dist_dir"] / f"{self.config['app_name']}-Setup-{self.config['version']}.exe"
        report["installer_created"] = installer_path.exists()
        
        if installer_path.exists():
            installer_size = installer_path.stat().st_size / (1024 * 1024)  # Size in MB
            report["installer_size_mb"] = round(installer_size, 2)
        
        # Save report
        report_path = self.project_root / self.config["dist_dir"] / "build_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Build report saved to: {report_path}")
        
        # Print summary
        logger.info("=" * 50)
        logger.info("BUILD SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Application: {report['app_name']} v{report['version']}")
        logger.info(f"Build duration: {duration.total_seconds():.2f} seconds")
        logger.info(f"Executable created: {'Yes' if report['executable_created'] else 'No'}")
        if report['executable_created']:
            logger.info(f"Executable size: {report['executable_size_mb']} MB")
        logger.info(f"Installer created: {'Yes' if report['installer_created'] else 'No'}")
        if report['installer_created']:
            logger.info(f"Installer size: {report['installer_size_mb']} MB")
        logger.info("=" * 50)
        
        return report
    
    def build(self, run_tests_flag=False, create_installer_flag=True):
        """Run the complete build process."""
        logger.info(f"Starting build for {self.config['app_name']} v{self.config['version']}")
        
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
                self.create_installer()
            
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
                "error": str(e)
            }
            
            report_path = self.project_root / self.config["dist_dir"] / "build_report.json"
            report_path.parent.mkdir(exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            raise

def main():
    """Main function to run the build script."""
    parser = argparse.ArgumentParser(description="Build Digital Workshop application")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--no-installer", action="store_true", help="Skip creating installer")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build directories")
    parser.add_argument("--config", help="Path to build configuration file")
    
    args = parser.parse_args()
    
    # Load custom configuration if provided
    config = BUILD_CONFIG
    if args.config:
        with open(args.config, 'r') as f:
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
            create_installer_flag=not args.no_installer
        )
    except Exception as e:
        logger.error(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
