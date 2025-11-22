#!/usr/bin/env python3
"""
Build script for Digital Workshop EXE wrapper
Converts run.py into a standalone Windows executable using PyInstaller
"""

import sys
import subprocess
import shutil
import argparse
from pathlib import Path

BUILD_SYSTEM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BUILD_SYSTEM_DIR.parent
SPEC_PATH = BUILD_SYSTEM_DIR / "build_exe.spec"

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
    
    dirs_to_remove = [PROJECT_ROOT / 'build', PROJECT_ROOT / 'dist']
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            print(f"[INFO] Removing {dir_path.relative_to(PROJECT_ROOT)}")
            shutil.rmtree(dir_path)
    
    # Remove .spec file cache
    spec_cache = SPEC_PATH.with_suffix('.spec.cache')
    if spec_cache.exists():
        spec_cache.unlink()
    
    print("[OK] Build artifacts cleaned")

def build_exe(spec_path: Path, dist_path: Path, work_path: Path):
    """Build the EXE using PyInstaller."""
    print("\n[INFO] Building Digital Workshop EXE...")
    print("[INFO] This may take a few minutes...")
    
    try:
        result = subprocess.run(
            [
                sys.executable, '-m', 'PyInstaller',
                str(spec_path),
                '--distpath', str(dist_path),
                '--workpath', str(work_path),
            ],
            check=True,
            cwd=PROJECT_ROOT
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller build failed with code {e.returncode}")
        return False

def verify_build(dist_path: Path, onefile: bool = False):
    """Verify the EXE was created successfully."""
    if onefile:
        exe_path = dist_path / 'Digital Workshop.exe'
    else:
        exe_path = dist_path / 'Digital Workshop' / 'Digital Workshop.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] EXE created successfully!")
        print(f"[OK] Location: {exe_path.resolve()}")
        print(f"[OK] Size: {size_mb:.1f} MB")
        # Clean up any stray top-level EXE that PyInstaller may leave alongside the onedir output
        stray = dist_path / 'Digital Workshop.exe'
        if not onefile and stray.exists():
            try:
                stray.unlink()
                print(f"[INFO] Removed stray EXE: {stray}")
            except Exception:
                print(f"[WARN] Could not remove stray EXE: {stray}")
        try:
            latest_dir = dist_path / "Latest"
            active_dir = dist_path / "Active"
            latest_dir.mkdir(parents=True, exist_ok=True)
            active_dir.mkdir(parents=True, exist_ok=True)
            if onefile:
                target = latest_dir / "Digital Workshop.exe"
                shutil.copy2(exe_path, target)
                shutil.copy2(exe_path, active_dir / "Digital Workshop.exe")
                print(f"[OK] Copied onefile EXE to Latest/ and Active/")
            else:
                # Copy the entire onedir folder
                def copytree(src: Path, dst: Path):
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                copytree(dist_path / "Digital Workshop", latest_dir / "Digital Workshop")
                copytree(dist_path / "Digital Workshop", active_dir / "Digital Workshop")
                print(f"[OK] Copied onedir build to Latest/ and Active/")
        except Exception as copy_exc:
            print(f"[WARN] Failed to copy build to Latest/Active: {copy_exc}")
        return True
    else:
        print(f"\n[ERROR] EXE not found at {exe_path}")
        return False

def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description="Digital Workshop EXE builder")
    parser.add_argument(
        "--mode",
        choices=["onedir", "onefile", "both"],
        help="Build mode (default: onedir in non-interactive environments; prompt in interactive shells)",
    )
    args = parser.parse_args()

    print("Digital Workshop - EXE Builder")
    print("=" * 50)

    mode = args.mode or os.getenv("DW_BUILD_MODE")
    if mode is None and sys.stdin and sys.stdin.isatty():
        choice = input("Select build type: [1] onedir (multi-file)  [2] onefile (single-file)  [3] both: ").strip()
        choice_map = {"1": "onedir", "2": "onefile", "3": "both"}
        mode = choice_map.get(choice)
    if mode is None:
        mode = "onedir"  # sensible default for CI

    if mode not in {"onedir", "onefile", "both"}:
        print("Invalid build mode. Use --mode onedir|onefile|both or set DW_BUILD_MODE.")
        sys.exit(1)

    build_onedir = mode in {"onedir", "both"}
    build_onefile = mode in {"onefile", "both"}

    # Step 1: Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)
    
    # Step 2: Clean previous builds
    clean_build_artifacts()
    
    # Step 3: Build EXE(s)
    dist_path = PROJECT_ROOT / 'dist'
    work_path = PROJECT_ROOT / 'build'

    if build_onedir:
        if not build_exe(SPEC_PATH, dist_path, work_path / "onedir"):
            sys.exit(1)
        if not verify_build(dist_path, onefile=False):
            sys.exit(1)

    if build_onefile:
        onefile_spec = BUILD_SYSTEM_DIR / "pyinstaller_onefile.spec"
        if not build_exe(onefile_spec, dist_path, work_path / "onefile"):
            sys.exit(1)
        if not verify_build(dist_path, onefile=True):
            sys.exit(1)

    print("\n[OK] Build completed successfully!")
    if build_onedir:
        print(" - Onedir: dist/Digital Workshop/Digital Workshop.exe")
    if build_onefile:
        print(" - Onefile: dist/Digital Workshop.exe")

if __name__ == "__main__":
    main()

