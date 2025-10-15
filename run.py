#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Quick Start Script

This script helps users quickly set up and run the 3D-MM application
with automatic dependency checking and circular import fixes.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version < (3, 8):
        print(f"Error: Python 3.8 or higher is required. You have Python {version.major}.{version.minor}.{version.micro}")
        return False
    elif (version.major, version.minor) >= (3, 13):
        print(f"Warning: Python {version.major}.{version.minor}.{version.micro} detected. 3D-MM is tested with Python 3.8-3.12")
        try:
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        except EOFError:
            # Handle non-interactive environments
            print("Non-interactive environment detected. Continuing with Python 3.13+...")
    
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
            if install.lower() == 'y':
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
                    print("Dependencies installed successfully!")
                    return True
                except subprocess.CalledProcessError:
                    print("Failed to install dependencies. Please install them manually.")
                    return False
            else:
                return False
        except EOFError:
            # Handle non-interactive environments
            print("\nNon-interactive environment detected. Please install missing dependencies manually:")
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
    
    with open(base_parser_path, 'r') as f:
        content = f.read()
    
    if "from core.model_cache import get_model_cache, CacheLevel" in content:
        print("Circular import issue detected in base_parser.py")
        
        try:
            fix = input("Fix circular imports automatically? (y/n): ")
            if fix.lower() == 'y':
                try:
                    subprocess.run([sys.executable, "fix_circular_imports.py"], check=True)
                    print("Circular imports fixed successfully!")
                    return True
                except subprocess.CalledProcessError:
                    print("Failed to fix circular imports automatically.")
                    return False
            else:
                print("Please fix circular imports manually before running the application.")
                return False
        except EOFError:
            # Handle non-interactive environments
            print("\nNon-interactive environment detected. Please fix circular imports manually before running the application.")
            return False
    
    print("[OK] No circular import issues detected")
    return True

def run_application():
    """Run the 3D-MM application."""
    print("\nStarting 3D-MM application...")
    
    try:
        # Change to src directory temporarily
        original_dir = os.getcwd()
        src_dir = Path("src")
        
        if not src_dir.exists():
            print("Error: src directory not found")
            return False
        
        os.chdir(src_dir)
        
        # Run the application
        subprocess.run([sys.executable, "main.py"], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to run application: {e}")
        return False
    finally:
        # Restore original directory
        os.chdir(original_dir)

def main():
    """Main function to check and run the application."""
    print("3D-MM (3D Model Manager) - Quick Start")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Error: src directory not found. Please run this script from the project root.")
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