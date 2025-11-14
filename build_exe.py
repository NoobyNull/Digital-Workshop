#!/usr/bin/env python3
"""
Build script for Digital Workshop EXE wrapper
Converts run.py into a standalone Windows executable using PyInstaller
"""

import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} is installed")
        return True
    except ImportError:
        print("[ERROR] PyInstaller is not installed")
        print("Install it with: pip install -r requirements-dev.txt")
        return False

def clean_build_artifacts():
    """Remove previous build artifacts."""
    print("\n[INFO] Cleaning previous build artifacts...")
    
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"[INFO] Removing {dir_name}/")
            shutil.rmtree(dir_path)
    
    # Remove .spec file cache
    spec_cache = Path('build_exe.spec.cache')
    if spec_cache.exists():
        spec_cache.unlink()
    
    print("[OK] Build artifacts cleaned")

def build_exe():
    """Build the EXE using PyInstaller."""
    print("\n[INFO] Building Digital Workshop EXE...")
    print("[INFO] This may take a few minutes...")
    
    try:
        result = subprocess.run(
            [
                sys.executable, '-m', 'PyInstaller',
                'build_exe.spec',
                '--distpath', 'dist',
                '--workpath', 'build',
            ],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller build failed with code {e.returncode}")
        return False

def verify_build():
    """Verify the EXE was created successfully."""
    exe_path = Path('dist') / 'Digital Workshop.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] EXE created successfully!")
        print(f"[OK] Location: {exe_path.resolve()}")
        print(f"[OK] Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"\n[ERROR] EXE not found at {exe_path}")
        return False

def main():
    """Main build process."""
    print("Digital Workshop - EXE Builder")
    print("=" * 50)
    
    # Step 1: Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)
    
    # Step 2: Clean previous builds
    clean_build_artifacts()
    
    # Step 3: Build EXE
    if not build_exe():
        sys.exit(1)
    
    # Step 4: Verify build
    if not verify_build():
        sys.exit(1)
    
    print("\n[OK] Build completed successfully!")
    print("\nYou can now run: dist/Digital Workshop.exe")

if __name__ == "__main__":
    main()

